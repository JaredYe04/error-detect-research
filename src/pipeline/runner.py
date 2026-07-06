"""Integrated Spec→LLM→FormalCheck→PatternGuard pipeline."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.formal.checker import extract_python_code, format_counterexamples_for_repair, run_formal_check
from src.llm.ecnu_client import ECNUClient
from src.patterns.matcher import PatternGuard


SYSTEM_PROMPT = """You are an expert in Agile-SOFL formal specification-based programming.
Generate a single Python function that implements the given process/function specification.
Rules:
- Return a dict mapping output variable names to int values.
- Handle all FSF scenarios including 'others'.
- Use only integer arithmetic and boolean conditions.
- Output ONLY one Python code block with the function. No explanation outside the code block.
"""


@dataclass
class PipelineConfig:
    mode: str = "M"  # B0, B1, B2, M, A1, A2, A3
    max_attempts: int = 3
    temperature: float = 0.2
    top_p: float = 0.95
    model: str = "ecnu-plus"
    thinking: bool = False
    enable_formal: bool = True
    enable_patterns: bool = True
    enable_repair: bool = True
    pattern_max_high: int = 0
    formal_max_cases: int = 16
    strict_eval_cases: int = 64


@dataclass
class PipelineResult:
    task_id: str
    mode: str
    success: bool
    code: str
    attempts: int
    formal_passed: bool
    formal_conformance: float
    pattern_violations: int
    llm_calls: int
    latency_ms: float
    counterexamples: list[dict[str, Any]] = field(default_factory=list)
    pattern_matches: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None


def config_for_mode(mode: str) -> PipelineConfig:
    cfg = PipelineConfig(mode=mode)
    if mode == "B0":
        cfg.enable_formal = False
        cfg.enable_patterns = False
        cfg.enable_repair = False
        cfg.max_attempts = 1
    elif mode == "B1":
        cfg.enable_formal = False
        cfg.enable_patterns = False
        cfg.enable_repair = False
        cfg.max_attempts = 1
    elif mode == "B2":
        cfg.enable_formal = False
        cfg.enable_patterns = False
        cfg.enable_repair = True
        cfg.max_attempts = 3
        cfg.formal_max_cases = 8
    elif mode == "A1":
        cfg.enable_formal = False
        cfg.enable_patterns = True
        cfg.enable_repair = True
        cfg.formal_max_cases = 10
    elif mode == "A2":
        cfg.enable_formal = True
        cfg.enable_patterns = False
        cfg.enable_repair = True
        cfg.formal_max_cases = 24
    elif mode == "A3":
        cfg.enable_formal = True
        cfg.enable_patterns = True
        cfg.enable_repair = False
        cfg.max_attempts = 1
        cfg.formal_max_cases = 24
    elif mode == "M":
        cfg.enable_formal = True
        cfg.enable_patterns = True
        cfg.enable_repair = True
        cfg.max_attempts = 3
        cfg.formal_max_cases = 24
        cfg.thinking = False
        cfg.model = "ecnu-plus"
    return cfg


def build_prompt(task: dict[str, Any], feedback: str | None = None) -> list[dict[str, str]]:
    sig = task.get("signature", {})
    inputs = sig.get("inputs", sig.get("params", []))
    outputs = sig.get("outputs", [])
    in_str = ", ".join(f"{p['name']}: int" for p in inputs)
    out_names = [p["name"] for p in outputs]
    out_doc = ", ".join(out_names) if out_names else "result"

    user = [
        task.get("promptSpec", ""),
        f"\nFunction signature: def {task['name']}({in_str}) -> dict",
        f"Required output keys: {out_doc}",
    ]
    if feedback:
        user.append(f"\nPrevious attempt failed:\n{feedback}")
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "\n".join(user)},
    ]


class ErrorPreventionPipeline:
    def __init__(
        self,
        config: PipelineConfig | None = None,
        llm: ECNUClient | None = None,
        pattern_guard: PatternGuard | None = None,
    ) -> None:
        self.config = config or PipelineConfig()
        self.llm = llm
        self.pattern_guard = pattern_guard or PatternGuard()

    def run_task(
        self,
        task: dict[str, Any],
        *,
        reference_code: str | None = None,
    ) -> PipelineResult:
        start = time.perf_counter()
        cfg = self.config

        if cfg.mode == "B0" and reference_code:
            formal = run_formal_check(reference_code, task) if True else None
            fr = run_formal_check(reference_code, task)
            return PipelineResult(
                task_id=task["taskId"],
                mode=cfg.mode,
                success=fr.passed,
                code=reference_code,
                attempts=1,
                formal_passed=fr.passed,
                formal_conformance=fr.conformance_rate,
                pattern_violations=0,
                llm_calls=0,
                latency_ms=(time.perf_counter() - start) * 1000,
            )

        if not self.llm:
            raise ValueError("LLM client required for non-B0 modes")

        feedback: str | None = None
        code = ""
        llm_calls = 0
        last_formal = None
        last_patterns: list = []

        for attempt in range(1, cfg.max_attempts + 1):
            messages = build_prompt(task, feedback)
            resp = self.llm.chat(
                messages,
                temperature=cfg.temperature,
                top_p=cfg.top_p,
                thinking=cfg.thinking,
                model=cfg.model,
                metadata={"task_id": task["taskId"], "mode": cfg.mode, "attempt": attempt},
            )
            llm_calls += 1
            code = extract_python_code(resp.content)

            # B2 uses FSF-derived cases as unit-test oracle
            test_result = run_formal_check(code, task, max_cases=cfg.formal_max_cases)
            last_formal = test_result if cfg.enable_formal else last_formal

            formal_ok = True if not cfg.enable_formal else test_result.passed
            if cfg.mode == "B2":
                formal_ok = test_result.passed

            pattern_ok = True
            if cfg.enable_patterns:
                last_patterns = self.pattern_guard.check(code, task)
                high = sum(1 for m in last_patterns if m.severity in {"high", "critical"})
                pattern_ok = high <= cfg.pattern_max_high
            else:
                last_patterns = []

            if formal_ok and pattern_ok:
                break

            if not cfg.enable_repair and cfg.mode != "B2":
                break
            if cfg.mode == "B2" and attempt >= cfg.max_attempts:
                break

            parts = []
            if test_result.counterexamples:
                parts.append(format_counterexamples_for_repair(test_result.counterexamples))
            if last_patterns:
                parts.append(
                    "Pattern violations: "
                    + "; ".join(f"{m.pattern_id}:{m.name}" for m in last_patterns[:5])
                )
            feedback = "\n".join(parts) if parts else "Implementation incorrect. Retry."

        formal_result = last_formal or run_formal_check(code, task, max_cases=cfg.formal_max_cases)
        if cfg.mode == "B2":
            formal_result = run_formal_check(code, task, max_cases=cfg.formal_max_cases)
        pattern_matches = last_patterns if last_patterns else (
            self.pattern_guard.check(code, task) if cfg.enable_patterns else []
        )
        high_violations = sum(1 for m in pattern_matches if m.severity in {"high", "critical"})

        success = formal_result.passed
        if cfg.mode == "B2":
            success = formal_result.passed
        if cfg.enable_patterns:
            success = success and high_violations <= cfg.pattern_max_high

        return PipelineResult(
            task_id=task["taskId"],
            mode=cfg.mode,
            success=success,
            code=code,
            attempts=attempt,
            formal_passed=formal_result.passed,
            formal_conformance=formal_result.conformance_rate,
            pattern_violations=high_violations,
            llm_calls=llm_calls,
            latency_ms=(time.perf_counter() - start) * 1000,
            counterexamples=[cx.__dict__ for cx in formal_result.counterexamples],
            pattern_matches=[m.__dict__ for m in pattern_matches],
            error=formal_result.error,
        )


def save_result(result: PipelineResult, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{result.task_id.replace('.', '_')}_{result.mode}.json"
    path.write_text(json.dumps(result.__dict__, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
