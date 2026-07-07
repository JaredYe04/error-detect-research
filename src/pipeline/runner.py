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
    mode: str = "M"  # B0, B1, B2, B3, B4, M, A1, A2, A3
    max_attempts: int = 3
    # Per-phase temperature split (thesis: 0.7 gen / 0.0 repair)
    gen_temperature: float = 0.7
    repair_temperature: float = 0.0
    top_p: float = 0.95
    model: str = "ecnu-plus"
    thinking: bool = False
    enable_formal: bool = True
    enable_patterns: bool = True
    enable_repair: bool = True
    # Feedback variant for E6: "test_only" | "test_expected" | "semantic_ir"
    feedback_variant: str = "semantic_ir"
    pattern_max_high: int = 0
    formal_max_cases: int = 16
    strict_eval_cases: int = 64


@dataclass
class AttemptRecord:
    """Per-iteration log entry for repair dynamics analysis (E5)."""
    attempt: int
    conf: float
    cex_count: int
    pattern_count: int
    feedback_variant: str


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
    # Per-attempt trajectory for E5 repair dynamics analysis
    attempt_history: list[dict[str, Any]] = field(default_factory=list)
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
        cfg.feedback_variant = "test_expected"
        cfg.max_attempts = 3
        cfg.formal_max_cases = 8
    elif mode == "B3":
        # Self-Refine: LLM critiques its own output, no external checker
        cfg.enable_formal = False
        cfg.enable_patterns = False
        cfg.enable_repair = True
        cfg.feedback_variant = "self_refine"
        cfg.max_attempts = 3
    elif mode == "B4":
        # Self-Debug: execution trace feedback from reference tests
        cfg.enable_formal = False
        cfg.enable_patterns = False
        cfg.enable_repair = True
        cfg.feedback_variant = "test_only"
        cfg.max_attempts = 3
        cfg.formal_max_cases = 8
    elif mode == "B5":
        # Reflexion-lite (Shinn et al. 2023): verbal RL via accumulated reflection memory
        # Key difference from B3 (Self-Refine): maintains a rolling reflection log across
        # iterations so each repair prompt includes ALL prior reflections, not just the last.
        cfg.enable_formal = False
        cfg.enable_patterns = False
        cfg.enable_repair = True
        cfg.feedback_variant = "reflexion_lite"
        cfg.max_attempts = 3
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
        cfg.feedback_variant = "semantic_ir"
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


def _build_repair_feedback(
    test_result: Any,
    pattern_matches: list,
    variant: str,
    task: dict[str, Any],
    attempt: int,
    reflection_memory: list[str] | None = None,
) -> str:
    """Build repair feedback string according to the requested feedback variant.

    Variants (controlled in E6):
      test_only      — counterexample inputs + observed only
      test_expected  — counterexample inputs + observed + expected (B2-style)
      semantic_ir    — full Semantic Feedback IR with scenario context (M-style)
      self_refine    — ask LLM to critique its own output (B3-style)
      reflexion_lite — verbal reflection accumulated across attempts (B5-style)
    """
    if variant == "self_refine":
        return (
            f"Your attempt {attempt} may be incorrect. "
            "Review the FSF specification carefully. Identify any logical errors, "
            "especially around scenario ordering and guard conditions, then produce a corrected implementation."
        )

    if variant == "reflexion_lite":
        reflection = (
            f"Reflect on attempt {attempt}: review the FSF specification carefully. "
            "Identify exactly what logical error caused the failure — focus on scenario "
            "guard ordering, boundary conditions, and 'others' case coverage."
        )
        parts: list[str] = []
        if reflection_memory:
            mem_lines = "\n".join(f"  [{i+1}] {r}" for i, r in enumerate(reflection_memory))
            parts.append(f"Previous reflections:\n{mem_lines}")
        parts.append(reflection)
        parts.append("Using the above reflections as memory, produce a corrected implementation.")
        return "\n\n".join(parts)

    cxs = test_result.counterexamples if test_result else []
    parts: list[str] = []

    if cxs:
        if variant == "test_only":
            lines = ["The following inputs caused incorrect output:"]
            for i, cx in enumerate(cxs[:5], 1):
                lines.append(f"{i}. inputs={cx.inputs} observed={cx.actual}")
            lines.append("Fix the implementation.")
            parts.append("\n".join(lines))

        elif variant == "test_expected":
            parts.append(format_counterexamples_for_repair(cxs))

        else:  # semantic_ir (default for M)
            from src.repair.feedback_ir import SemanticFeedbackIR
            ir = SemanticFeedbackIR(task)
            parts.append(ir.render(cxs))

    if pattern_matches:
        parts.append(
            "Requirement pattern violations: "
            + "; ".join(f"{m.pattern_id}:{m.name}" for m in pattern_matches[:5])
        )

    return "\n".join(parts) if parts else "Implementation incorrect. Retry."


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
        attempt_history: list[dict[str, Any]] = []
        # B5 Reflexion-lite: rolling verbal memory (last 3 reflections max)
        reflection_memory: list[str] = []

        for attempt in range(1, cfg.max_attempts + 1):
            # Use gen_temperature on first attempt, repair_temperature on subsequent
            temperature = cfg.gen_temperature if attempt == 1 else cfg.repair_temperature
            messages = build_prompt(task, feedback)
            resp = self.llm.chat(
                messages,
                temperature=temperature,
                top_p=cfg.top_p,
                thinking=cfg.thinking,
                model=cfg.model,
                metadata={"task_id": task["taskId"], "mode": cfg.mode, "attempt": attempt},
            )
            llm_calls += 1
            code = extract_python_code(resp.content)

            # All modes run the formal check for evaluation; only M/A1/A2/A3 use it for gating
            test_result = run_formal_check(code, task, max_cases=cfg.formal_max_cases)
            last_formal = test_result if cfg.enable_formal else last_formal

            formal_ok = True if not cfg.enable_formal else test_result.passed
            if cfg.mode in ("B2", "B4"):
                formal_ok = test_result.passed

            pattern_ok = True
            if cfg.enable_patterns:
                last_patterns = self.pattern_guard.check(code, task)
                high = sum(1 for m in last_patterns if m.severity in {"high", "critical"})
                pattern_ok = high <= cfg.pattern_max_high
            else:
                last_patterns = []
                high = 0

            # Log per-attempt trajectory for repair dynamics analysis (E5)
            attempt_history.append({
                "attempt": attempt,
                "conf": test_result.conformance_rate,
                "cex_count": len(test_result.counterexamples),
                "pattern_count": high,
                "feedback_variant": cfg.feedback_variant,
            })

            if formal_ok and pattern_ok:
                break

            if not cfg.enable_repair and cfg.mode not in ("B2", "B3", "B4", "B5"):
                break
            if cfg.mode in ("B2", "B3", "B4", "B5") and attempt >= cfg.max_attempts:
                break

            feedback = _build_repair_feedback(
                test_result, last_patterns, cfg.feedback_variant, task, attempt,
                reflection_memory=reflection_memory if cfg.feedback_variant == "reflexion_lite" else None,
            )
            # B5 Reflexion-lite: accumulate this reflection into rolling memory (cap at 3)
            if cfg.feedback_variant == "reflexion_lite":
                new_reflection = (
                    f"Attempt {attempt} failed "
                    f"(conformance={test_result.conformance_rate:.2f}, "
                    f"failures={len(test_result.counterexamples)}). "
                    "Review scenario guards and boundary conditions."
                )
                reflection_memory.append(new_reflection)
                reflection_memory = reflection_memory[-3:]

        formal_result = last_formal or run_formal_check(code, task, max_cases=cfg.formal_max_cases)
        if cfg.mode in ("B2", "B4"):
            formal_result = run_formal_check(code, task, max_cases=cfg.formal_max_cases)
        pattern_matches = last_patterns if last_patterns else (
            self.pattern_guard.check(code, task) if cfg.enable_patterns else []
        )
        high_violations = sum(1 for m in pattern_matches if m.severity in {"high", "critical"})

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
            attempt_history=attempt_history,
            error=formal_result.error,
        )


def save_result(result: PipelineResult, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{result.task_id.replace('.', '_')}_{result.mode}.json"
    path.write_text(json.dumps(result.__dict__, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
