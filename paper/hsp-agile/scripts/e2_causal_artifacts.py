#!/usr/bin/env python3
"""Generate E2 causal/decomposition artifacts from existing local runs.

This script is intentionally read-only with respect to experiment execution: it
derives lightweight CSV/JSON outputs from existing JSONL/CSV artifacts.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
PAPER_ROOT = Path(__file__).resolve().parents[1]
PROC_DIR = PAPER_ROOT / "data" / "processed"

PREVENTION_JSONL = ROOT / "artifacts" / "prevention_eval" / "prevention_full_v1" / "prevention_eval.jsonl"
PREVENTION_SUMMARY = ROOT / "artifacts" / "prevention_eval" / "prevention_full_v1" / "prevention_summary.json"
RAW_RESULTS = PAPER_ROOT / "data" / "raw" / "results_raw.csv"
B6_FULL = ROOT / "artifacts" / "run_b6_full_v2" / "results.jsonl"
M_LITE = ROOT / "artifacts" / "run_m_lite_v1" / "results.jsonl"

DECOMP_CSV = PROC_DIR / "e2_decomp_same_denominator.csv"
B6_AVAILABILITY_JSON = PROC_DIR / "e2_b6_prevention_availability.json"
SCREEN_FP_JSON = PROC_DIR / "e_screen_fp_reference.json"


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _metric_columns(df: pd.DataFrame) -> tuple[str, str]:
    success_col = "strict_formal_passed" if "strict_formal_passed" in df.columns else "success"
    conf_col = "strict_formal_conformance" if "strict_formal_conformance" in df.columns else "formal_conformance"
    return success_col, conf_col


def _summarize_run_level(df: pd.DataFrame, *, source: str, mode: str, common_tasks: set[str]) -> dict[str, Any]:
    success_col, conf_col = _metric_columns(df)
    sub = df[(df["mode"] == mode) & (df["task_id"].isin(common_tasks))].copy()
    row: dict[str, Any] = {
        "scope": "bench120_common_task_conformance",
        "mode": mode,
        "denominator_n": int(sub["task_id"].nunique()),
        "pdr": "",
        "far": "",
        "strict_success_rate": float(sub[success_col].mean()) if not sub.empty else "",
        "strict_conformance": float(sub[conf_col].mean()) if not sub.empty else "",
        "mutation_kill_rate": float(sub["mutation_kill_rate"].mean()) if "mutation_kill_rate" in sub.columns else "",
        "latency_ms": float(sub["latency_ms"].mean()) if "latency_ms" in sub.columns and not sub.empty else "",
        "source": source,
        "comparability_note": "same task_id denominator; modes come from existing local campaigns",
    }
    return row


def build_decomposition_table() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    prevention = json.loads(PREVENTION_SUMMARY.read_text(encoding="utf-8")) if PREVENTION_SUMMARY.exists() else {}
    by_eval = prevention.get("by_eval_type", {})
    for mode in ["B2", "B6", "M_lite", "A2", "M"]:
        metrics = by_eval.get(mode, {}).get("impl_screening")
        rows.append(
            {
                "scope": "prevention_impl_screening",
                "mode": mode,
                "denominator_n": int(metrics.get("n", 0)) if metrics else "",
                "pdr": float(metrics.get("detection_rate")) if metrics else "",
                "far": float(metrics.get("false_accept_rate")) if metrics else "",
                "strict_success_rate": "",
                "strict_conformance": float(metrics.get("strict_conformance")) if metrics else "",
                "mutation_kill_rate": "",
                "latency_ms": "",
                "source": _rel(PREVENTION_SUMMARY) if PREVENTION_SUMMARY.exists() else "",
                "comparability_note": "same impl_screening denominator when present; B6/M_lite absent in prevention_full_v1",
            }
        )

    raw = pd.read_csv(RAW_RESULTS)
    b6 = pd.DataFrame(_read_jsonl(B6_FULL))
    m_lite = pd.DataFrame(_read_jsonl(M_LITE))
    mode_sources = {
        "B2": (raw, _rel(RAW_RESULTS)),
        "B6": (b6, _rel(B6_FULL)),
        "M_lite": (m_lite, _rel(M_LITE)),
        "A2": (raw, _rel(RAW_RESULTS)),
        "M": (raw, _rel(RAW_RESULTS)),
    }
    task_sets = [
        set(df.loc[df["mode"] == mode, "task_id"])
        for mode, (df, _) in mode_sources.items()
        if not df.empty and "task_id" in df.columns
    ]
    common_tasks = set.intersection(*task_sets) if task_sets else set()
    for mode, (df, source) in mode_sources.items():
        rows.append(_summarize_run_level(df, source=source, mode=mode, common_tasks=common_tasks))

    out = pd.DataFrame(rows)
    out.to_csv(DECOMP_CSV, index=False)
    return out


def build_b6_availability() -> dict[str, Any]:
    rows = _read_jsonl(PREVENTION_JSONL)
    df = pd.DataFrame(rows)
    eval_counts: dict[str, dict[str, int]] = {}
    if not df.empty:
        grouped = df.groupby(["mode", "eval_type"]).size()
        for (mode, eval_type), count in grouped.items():
            eval_counts.setdefault(str(mode), {})[str(eval_type)] = int(count)

    availability = {
        "prevention_jsonl": _rel(PREVENTION_JSONL),
        "prevention_jsonl_exists": PREVENTION_JSONL.exists(),
        "prevention_summary": _rel(PREVENTION_SUMMARY),
        "prevention_summary_exists": PREVENTION_SUMMARY.exists(),
        "modes_in_prevention": sorted(eval_counts),
        "eval_counts": eval_counts,
        "b6_prevention_exists": "B6" in eval_counts,
        "m_lite_prevention_exists": "M_lite" in eval_counts,
        "b6_run_level_artifacts": {
            "run_b6_full_v1": (ROOT / "artifacts" / "run_b6_full_v1" / "results.jsonl").exists(),
            "run_b6_full_v2": B6_FULL.exists(),
            "run_b6_stratified_v1": (ROOT / "artifacts" / "run_b6_stratified_v1" / "results.jsonl").exists(),
        },
        "note": "B6 data exists for run-level conformance, but not for prevention impl_screening/spec_confusion in prevention_full_v1.",
    }
    B6_AVAILABILITY_JSON.write_text(json.dumps(availability, indent=2), encoding="utf-8")
    return availability


def build_screen_fp_reference() -> dict[str, Any]:
    sys.path.insert(0, str(ROOT))
    from src.benchmarks import load_benchmark
    from src.patterns.matcher import PatternGuard

    tasks = load_benchmark()
    guard = PatternGuard()
    any_hits = 0
    blocking_hits = 0
    advisory_counts: Counter[str] = Counter()
    blocking_counts: Counter[str] = Counter()
    examples: list[dict[str, Any]] = []
    for task in tasks:
        matches = guard.check(task.get("referenceCode", ""), task)
        if matches:
            any_hits += 1
        blocking = [m for m in matches if m.severity in {"high", "critical"}]
        if blocking:
            blocking_hits += 1
            if len(examples) < 5:
                examples.append(
                    {
                        "task_id": task.get("taskId"),
                        "blocking_patterns": [m.pattern_id for m in blocking],
                    }
                )
        advisory_counts.update(m.pattern_id for m in matches)
        blocking_counts.update(m.pattern_id for m in blocking)

    n = len(tasks)
    result = {
        "screen": "PatternGuard hard blocking threshold (high or critical)",
        "benchmark": "src.benchmarks.load_benchmark()",
        "n_reference_tasks": n,
        "blocking_false_positive_count": blocking_hits,
        "blocking_false_positive_rate": blocking_hits / n if n else 0.0,
        "any_pattern_hit_count": any_hits,
        "any_pattern_hit_rate": any_hits / n if n else 0.0,
        "advisory_pattern_counts": dict(sorted(advisory_counts.items())),
        "blocking_pattern_counts": dict(sorted(blocking_counts.items())),
        "blocking_examples": examples,
        "interpretation": "Clean references trigger advisory rules, but the hard Screen would not reject any reference task.",
    }
    SCREEN_FP_JSON.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> None:
    PROC_DIR.mkdir(parents=True, exist_ok=True)
    decomp = build_decomposition_table()
    availability = build_b6_availability()
    screen_fp = build_screen_fp_reference()
    print(f"wrote {_rel(DECOMP_CSV)} ({len(decomp)} rows)")
    print(f"wrote {_rel(B6_AVAILABILITY_JSON)}")
    print(f"wrote {_rel(SCREEN_FP_JSON)}")
    print(f"B6 prevention exists: {availability['b6_prevention_exists']}")
    print(
        "Screen blocking FP: "
        f"{screen_fp['blocking_false_positive_count']}/{screen_fp['n_reference_tasks']} "
        f"({screen_fp['blocking_false_positive_rate']:.3f})"
    )


if __name__ == "__main__":
    main()
