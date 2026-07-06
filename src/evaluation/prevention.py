"""Defect prevention evaluation against spec/impl mutants."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from src.formal.checker import run_formal_check
from src.mutation.injectors import apply_mutant_to_task, generate_mutants
from src.patterns.matcher import PatternGuard
from src.pipeline.runner import ErrorPreventionPipeline, config_for_mode
from src.llm.ecnu_client import ECNUClient


@dataclass
class PreventionRecord:
    task_id: str
    mode: str
    mutant_id: str
    operator: str
    layer: str
    accepted: bool
    detected: bool
    strict_conformance: float
    description: str
    eval_type: str


def _accept_candidate_code(mode: str, code: str, task: dict[str, Any]) -> tuple[bool, float]:
    """Mode-specific gate for accepting a pre-existing implementation candidate."""
    cfg = config_for_mode(mode)
    # Baseline B1 accepts code without formal/pattern checks.
    if mode == "B1":
        return True, 0.0
    max_cases = cfg.formal_max_cases
    fr = run_formal_check(code, task, max_cases=max_cases)
    accepted = fr.passed
    if cfg.enable_patterns:
        guard = PatternGuard()
        high = sum(1 for m in guard.check(code, task) if m.severity in {"high", "critical"})
        accepted = accepted and high <= cfg.pattern_max_high
    strict = run_formal_check(code, task, max_cases=max(cfg.strict_eval_cases, 64))
    return accepted, strict.conformance_rate


def evaluate_prevention(
    tasks: list[dict[str, Any]],
    modes: list[str],
    llm: ECNUClient,
    *,
    seed: int = 42,
    done_keys: set[str] | None = None,
) -> list[PreventionRecord]:
    """Measure both spec-confusion and candidate-defect prevention performance."""
    records: list[PreventionRecord] = []
    done_keys = done_keys or set()
    for task in tasks:
        ref = task.get("referenceCode", "")
        mutants = generate_mutants(task, ref, seed=seed, impl_ops=True, spec_ops=True)
        for mode in modes:
            if mode == "B0":
                continue
            pending: list[tuple[Any, str]] = []
            for mut in mutants:
                eval_type = "spec_confusion" if mut.layer == "spec" else "impl_screening"
                key = f"{mode}|{mut.mutant_id}|{eval_type}"
                if key not in done_keys:
                    pending.append((mut, eval_type))
            if not pending:
                continue
            cfg = config_for_mode(mode)
            pipeline = ErrorPreventionPipeline(config=cfg, llm=llm)
            # Generate one baseline candidate per (task, mode), then evaluate against mutants.
            base_result = pipeline.run_task(task)
            base_code = base_result.code
            base_orig_check = run_formal_check(base_code, task, max_cases=max(cfg.strict_eval_cases, 64))
            for mut, eval_type in pending:
                if eval_type == "spec_confusion":
                    mut_task = apply_mutant_to_task(task, mut)
                    mut_check = run_formal_check(base_code, mut_task, max_cases=max(cfg.strict_eval_cases, 64))
                    detected = not mut_check.passed
                    records.append(
                        PreventionRecord(
                            task_id=task["taskId"],
                            mode=mode,
                            mutant_id=mut.mutant_id,
                            operator=mut.operator,
                            layer=mut.layer,
                            accepted=base_result.success,
                            detected=detected,
                            strict_conformance=base_orig_check.conformance_rate,
                            description=mut.description,
                            eval_type=eval_type,
                        )
                    )
                else:
                    candidate = mut.payload["code"]
                    accepted, strict_conf = _accept_candidate_code(mode, candidate, task)
                    detected = not accepted
                    records.append(
                        PreventionRecord(
                            task_id=task["taskId"],
                            mode=mode,
                            mutant_id=mut.mutant_id,
                            operator=mut.operator,
                            layer=mut.layer,
                            accepted=accepted,
                            detected=detected,
                            strict_conformance=strict_conf,
                            description=mut.description,
                            eval_type=eval_type,
                        )
                    )
                done_keys.add(f"{mode}|{mut.mutant_id}|{eval_type}")
    return records


def save_prevention_report(records: list[PreventionRecord], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "prevention_eval.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")

    by_mode: dict[str, list[PreventionRecord]] = {}
    by_mode_eval: dict[str, dict[str, list[PreventionRecord]]] = {}
    for r in records:
        by_mode.setdefault(r.mode, []).append(r)
        by_mode_eval.setdefault(r.mode, {}).setdefault(r.eval_type, []).append(r)

    summary = {
        mode: {
            "detection_rate": sum(1 for x in rs if x.detected) / len(rs),
            "false_accept_rate": sum(1 for x in rs if x.accepted and not x.detected) / len(rs),
            "strict_conformance": sum(x.strict_conformance for x in rs) / len(rs),
            "n": len(rs),
        }
        for mode, rs in by_mode.items()
    }
    summary["by_eval_type"] = {
        mode: {
            eval_type: {
                "detection_rate": sum(1 for x in rs if x.detected) / len(rs),
                "false_accept_rate": sum(1 for x in rs if x.accepted and not x.detected) / len(rs),
                "strict_conformance": sum(x.strict_conformance for x in rs) / len(rs),
                "n": len(rs),
            }
            for eval_type, rs in eval_groups.items()
        }
        for mode, eval_groups in by_mode_eval.items()
    }
    (out_dir / "prevention_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return path
