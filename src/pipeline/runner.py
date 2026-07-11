"""Integrated Spec→LLM→FormalCheck→PatternGuard pipeline."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.formal.checker import Counterexample, extract_python_code, run_formal_check
from src.ir.spec_ir import SpecIR
from src.llm.ecnu_client import ECNUClient
from src.patterns.matcher import PatternGuard
from src.pipeline.task_input import normalize_task
from src.repair.feedback_ir import FeedbackRenderer, SemanticFeedbackIR


SYSTEM_PROMPT = """You are an expert in Agile-SOFL formal specification-based programming.
Generate a single Python function that implements the given process/function specification.
Rules:
- Return a dict mapping output variable names to int values.
- Handle all FSF scenarios including 'others'.
- Evaluate scenario guards in the exact first-match order given by the specification;
  never reorder overlapping guards.
- When repairing, preserve previously correct branches; fix only the reported failure.
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
    pattern_guard_mode: str = "hard"  # hard | advisory (RF07/critical only blocks)
    formal_max_cases: int = 16
    strict_eval_cases: int = 64
    feedback_variant: str = ""  # test_only | test_expected | semantic_ir (E6)


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
    semantic_feedback: list[dict[str, Any]] = field(default_factory=list)
    attempt_history: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None


def resolve_feedback_variant(cfg: PipelineConfig) -> str:
    """Map mode / explicit override to E6 feedback projection variant."""
    if cfg.feedback_variant in FeedbackRenderer.VARIANTS:
        return cfg.feedback_variant
    if cfg.mode == "B2":
        return "test_only"
    if cfg.mode in {"B4M", "M", "M_adv"}:
        return "execution_trace_matched"
    if cfg.enable_formal:
        return "semantic_ir"
    return "test_expected"


def build_repair_feedback(
    task: dict[str, Any],
    counterexamples: list[Counterexample],
    *,
    variant: str,
    pattern_matches: list[Any] | None = None,
    reflexion_memory: list[str] | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    """Construct repair prompt via Semantic Feedback IR (JSON then render)."""
    ir = SemanticFeedbackIR.from_counterexamples(counterexamples, task=task)
    feedback_json = ir.to_json_list()
    if variant == "reflexion":
        rendered = FeedbackRenderer._render_reflexion(ir.records, memory=reflexion_memory)
    else:
        rendered = FeedbackRenderer.render(ir.records, variant=variant)
    parts = [rendered]
    # For structured M-style variants, append failing-scenario postconditions.
    # Field-level IR ablations (ir_*) intentionally skip this appendix so the only
    # changing channel is FeedbackRenderer.render (Agent B causal hygiene).
    if variant in {"semantic_ir", "execution_trace_matched", "verifier_loop"}:
        scenario_note = _scenario_postcondition_hint(task, ir.records)
        if scenario_note:
            parts.append(scenario_note)
    if pattern_matches:
        parts.append(
            "Pattern violations: "
            + "; ".join(f"{m.pattern_id}:{m.name}" for m in pattern_matches[:5])
        )
    return "\n".join(parts), feedback_json


def _scenario_postcondition_hint(task: dict[str, Any], records: list) -> str:
    """Append oracle postconditions for failing scenarios (helps others/arithmetic)."""
    scenarios = task.get("fsfScenarios") or task.get("scenarios") or []
    if not scenarios or not records:
        return ""
    lines = ["Specification postconditions for failing scenarios:"]
    seen: set[int] = set()
    for r in records:
        idx = int(getattr(r, "scenario_index", 0) or 0)
        if idx in seen or not (1 <= idx <= len(scenarios)):
            continue
        seen.add(idx)
        sc = scenarios[idx - 1]
        guard = sc.get("test") or sc.get("guard") or ""
        post = sc.get("def") or sc.get("postcondition") or sc.get("body") or ""
        lines.append(f"  S{idx}: if ({guard}) then assign {post}")
        lines.append(f"       oracle on witness must equal {getattr(r, 'expected', {})}")
    return "\n".join(lines) if len(lines) > 1 else ""


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
        cfg.feedback_variant = "test_only"
    elif mode == "B3":
        cfg.enable_formal = False
        cfg.enable_patterns = False
        cfg.enable_repair = True
        cfg.max_attempts = 3
        cfg.formal_max_cases = 8
        cfg.feedback_variant = "self_critique"
    elif mode == "B4":
        cfg.enable_formal = False
        cfg.enable_patterns = False
        cfg.enable_repair = True
        cfg.max_attempts = 3
        cfg.formal_max_cases = 8
        cfg.feedback_variant = "execution_trace"
    elif mode == "B5":
        cfg.enable_formal = False
        cfg.enable_patterns = False
        cfg.enable_repair = True
        cfg.max_attempts = 3
        cfg.formal_max_cases = 8
        cfg.feedback_variant = "reflexion"
    elif mode == "B6":
        cfg.enable_formal = True
        cfg.enable_patterns = False
        cfg.enable_repair = True
        cfg.max_attempts = 3
        cfg.formal_max_cases = 24
        cfg.feedback_variant = "verifier_loop"
    elif mode == "A1":
        # Ablation of strengthened M: no formal checker; keep repair+patterns.
        cfg.enable_formal = False
        cfg.enable_patterns = True
        cfg.enable_repair = True
        cfg.max_attempts = 5
        cfg.formal_max_cases = 32
        cfg.thinking = False
        cfg.model = "ecnu-plus"
        cfg.feedback_variant = "execution_trace_matched"
        cfg.pattern_guard_mode = "advisory"
        cfg.temperature = 0.2
    elif mode == "A2":
        # Ablation of strengthened M: no pattern guard; keep formal+repair.
        cfg.enable_formal = True
        cfg.enable_patterns = False
        cfg.enable_repair = True
        cfg.max_attempts = 5
        cfg.formal_max_cases = 32
        cfg.thinking = False
        cfg.model = "ecnu-plus"
        cfg.feedback_variant = "execution_trace_matched"
        cfg.temperature = 0.2
    elif mode == "A3":
        # Ablation of strengthened M: no repair loop (single attempt).
        cfg.enable_formal = True
        cfg.enable_patterns = True
        cfg.enable_repair = False
        cfg.max_attempts = 1
        cfg.formal_max_cases = 32
        cfg.thinking = False
        cfg.model = "ecnu-plus"
        cfg.feedback_variant = "execution_trace_matched"
        cfg.pattern_guard_mode = "advisory"
        cfg.temperature = 0.2
    elif mode == "M":
        cfg.enable_formal = True
        cfg.enable_patterns = True
        cfg.enable_repair = True
        # Extra repair budget vs B2 (K=3): others/arithmetic residues need more turns.
        cfg.max_attempts = 5
        cfg.formal_max_cases = 32
        cfg.thinking = False
        cfg.model = "ecnu-plus"
        # E14: length-matched execution_trace beats bare semantic_ir under M.
        cfg.feedback_variant = "execution_trace_matched"
        # Hard-block only critical (RF07); high-severity patterns stay advisory
        # for repair telemetry but do not force Conf-regressing over-repair.
        cfg.pattern_guard_mode = "advisory"
        cfg.temperature = 0.2  # attempt 1; repair attempts force 0.0 in run_task
    elif mode == "M_adv":
        cfg.enable_formal = True
        cfg.enable_patterns = True
        cfg.enable_repair = True
        cfg.max_attempts = 5
        cfg.formal_max_cases = 32
        cfg.thinking = False
        cfg.model = "ecnu-plus"
        cfg.feedback_variant = "execution_trace_matched"
        cfg.pattern_guard_mode = "advisory"
        cfg.temperature = 0.2
    elif mode == "M_hard":
        # Legacy hard pattern gate + semantic_ir (ablation / prevention track).
        cfg.enable_formal = True
        cfg.enable_patterns = True
        cfg.enable_repair = True
        cfg.max_attempts = 3
        cfg.formal_max_cases = 24
        cfg.thinking = False
        cfg.model = "ecnu-plus"
        cfg.feedback_variant = "semantic_ir"
        cfg.pattern_guard_mode = "hard"
    elif mode == "B4M":
        cfg.enable_formal = False
        cfg.enable_patterns = False
        cfg.enable_repair = True
        cfg.max_attempts = 3
        cfg.formal_max_cases = 8
        cfg.feedback_variant = "execution_trace_matched"
    elif mode == "M_lite":
        # Witness-guided repair + Semantic IR, no pattern guard (P1 reviewer ask)
        cfg.enable_formal = True
        cfg.enable_patterns = False
        cfg.enable_repair = True
        cfg.max_attempts = 3
        cfg.formal_max_cases = 24
        cfg.feedback_variant = "semantic_ir"
    elif mode == "M_eq":
        # Equal-K hygiene vs B2: K=3, semantic_ir, advisory gate, fixed-oracle friendly.
        # Use for Conf ranking claims; do not conflate with strengthened M (K=5 bundle).
        cfg.enable_formal = True
        cfg.enable_patterns = True
        cfg.enable_repair = True
        cfg.max_attempts = 3
        cfg.formal_max_cases = 32
        cfg.thinking = False
        cfg.model = "ecnu-plus"
        cfg.feedback_variant = "semantic_ir"
        cfg.pattern_guard_mode = "advisory"
        cfg.temperature = 0.2
    return cfg


def _blocking_pattern_violations(matches: list, cfg: PipelineConfig) -> int:
    """Count pattern hits that block acceptance under the configured guard mode."""
    if cfg.pattern_guard_mode == "advisory":
        return sum(1 for m in matches if m.severity == "critical")
    return sum(1 for m in matches if m.severity in {"high", "critical"})


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
        task: SpecIR | dict[str, Any],
        *,
        reference_code: str | None = None,
    ) -> PipelineResult:
        start = time.perf_counter()
        cfg = self.config
        task = normalize_task(task)

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
        last_feedback_json: list[dict[str, Any]] = []
        feedback_variant = resolve_feedback_variant(cfg)
        reflexion_memory: list[str] = []
        # Best-effort tracking (Algorithm 1): never return a Conf-regressed last attempt.
        best_code = ""
        best_conf = -1.0
        best_formal = None
        best_patterns: list = []
        best_attempt = 0
        best_formal_ok = False
        best_pattern_ok = False
        best_blocking = 0

        for attempt in range(1, cfg.max_attempts + 1):
            messages = build_prompt(task, feedback)
            # Paper protocol: T_gen for first attempt, T_repair=0.0 thereafter.
            call_temperature = cfg.temperature if attempt == 1 else 0.0
            resp = self.llm.chat(
                messages,
                temperature=call_temperature,
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
            if cfg.mode in {"B2", "B3", "B4", "B4M", "B5", "B6"}:
                formal_ok = test_result.passed

            pattern_ok = True
            blocking = 0
            if cfg.enable_patterns:
                last_patterns = self.pattern_guard.check(code, task)
                blocking = _blocking_pattern_violations(last_patterns, cfg)
                pattern_ok = blocking <= cfg.pattern_max_high
            else:
                last_patterns = []

            conf = float(test_result.conformance_rate)
            # Lexicographic: higher Conf, then formal pass, then fewer blocking patterns.
            rank = (conf, 1 if formal_ok else 0, -blocking)
            best_rank = (best_conf, 1 if best_formal_ok else 0, -best_blocking)
            if rank > best_rank or not best_code:
                best_code = code
                best_conf = conf
                best_formal = test_result
                best_patterns = list(last_patterns)
                best_attempt = attempt
                best_formal_ok = formal_ok
                best_pattern_ok = pattern_ok
                best_blocking = blocking

            attempt_entry: dict[str, Any] = {
                "attempt": attempt,
                "formal_conformance": test_result.conformance_rate,
                "formal_passed": test_result.passed,
                "pattern_violations": blocking if cfg.enable_patterns else 0,
                "feedback_variant": feedback_variant,
                "is_best_so_far": code == best_code,
            }

            if formal_ok and pattern_ok:
                attempt_history.append(attempt_entry)
                break

            # Formal already clear: do not burn remaining budget on pattern-only
            # LLM repairs that often regress Conf; keep best formal candidate.
            if formal_ok and cfg.enable_patterns and not pattern_ok:
                attempt_history.append(attempt_entry)
                break

            if not cfg.enable_repair and cfg.mode not in {"B2", "B3", "B4", "B5", "B6"}:
                attempt_history.append(attempt_entry)
                break
            if cfg.mode in {"B2", "B3", "B4", "B4M", "B5", "B6"} and attempt >= cfg.max_attempts:
                attempt_history.append(attempt_entry)
                break

            if cfg.mode == "B3" and test_result.counterexamples:
                feedback, last_feedback_json = build_repair_feedback(
                    task,
                    test_result.counterexamples,
                    variant=feedback_variant,
                    pattern_matches=last_patterns,
                )
                feedback = (
                    "Self-critique: identify logical errors in your previous implementation before revising.\n"
                    + feedback
                )
                attempt_entry["semantic_feedback"] = last_feedback_json
            elif test_result.counterexamples:
                feedback, last_feedback_json = build_repair_feedback(
                    task,
                    test_result.counterexamples,
                    variant=feedback_variant,
                    pattern_matches=last_patterns,
                    reflexion_memory=reflexion_memory if cfg.mode == "B5" else None,
                )
                attempt_entry["semantic_feedback"] = last_feedback_json
                if cfg.mode == "B5":
                    reflexion_memory.append(
                        f"attempt {attempt}: scenario "
                        f"{test_result.counterexamples[0].scenario_index} failed"
                    )
            elif last_patterns:
                feedback = (
                    "Pattern violations: "
                    + "; ".join(f"{m.pattern_id}:{m.name}" for m in last_patterns[:5])
                )
                last_feedback_json = []
            else:
                feedback = "Implementation incorrect. Retry."
                last_feedback_json = []
            attempt_history.append(attempt_entry)

        # Return best-effort candidate (not necessarily the last attempt).
        code = best_code or code
        formal_result = best_formal or last_formal or run_formal_check(
            code, task, max_cases=cfg.formal_max_cases
        )
        if cfg.mode in {"B2", "B3", "B4", "B4M", "B5", "B6"}:
            formal_result = run_formal_check(code, task, max_cases=cfg.formal_max_cases)
        pattern_matches = best_patterns if best_patterns else (
            last_patterns if last_patterns else (
                self.pattern_guard.check(code, task) if cfg.enable_patterns else []
            )
        )
        high_violations = _blocking_pattern_violations(pattern_matches, cfg)

        success = formal_result.passed
        if cfg.mode in {"B2", "B3", "B4", "B4M", "B5", "B6"}:
            success = formal_result.passed
        if cfg.enable_patterns:
            success = success and high_violations <= cfg.pattern_max_high

        return PipelineResult(
            task_id=task["taskId"],
            mode=cfg.mode,
            success=success,
            code=code,
            attempts=best_attempt or attempt,
            formal_passed=formal_result.passed,
            formal_conformance=formal_result.conformance_rate,
            pattern_violations=high_violations,
            llm_calls=llm_calls,
            latency_ms=(time.perf_counter() - start) * 1000,
            counterexamples=[cx.__dict__ for cx in formal_result.counterexamples],
            pattern_matches=[m.__dict__ for m in pattern_matches],
            semantic_feedback=last_feedback_json,
            attempt_history=attempt_history,
            error=formal_result.error,
        )


def save_result(result: PipelineResult, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{result.task_id.replace('.', '_')}_{result.mode}.json"
    path.write_text(json.dumps(result.__dict__, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
