"""Failure taxonomy and pattern P/R/F1 analysis runner.

Reads completed experiment JSONL output and produces:
  - failure_taxonomy.json  — breakdown of failure categories for M mode
  - repair_dynamics/       — Conf(k) trajectory data (E5)
  - pattern_prf1.json      — per-pattern Precision/Recall/F1 (E7)

Usage:
    python experiments/run_failure_analysis.py \\
        --run artifacts/run_ccf_b_main_v1 \\
        --analysis all

    python experiments/run_failure_analysis.py \\
        --run artifacts/run_ccf_b_main_v1 \\
        --analysis failure_taxonomy repair_dynamics

    python experiments/run_failure_analysis.py \\
        --analysis pattern_precision_recall \\
        --prevention-run artifacts/prevention_ccf_b_v1
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

ARTIFACTS = ROOT / "artifacts"

# Ordered list of failure categories (earlier = higher priority match)
FAILURE_CATEGORIES = [
    "OrderingError",
    "BoundaryError",
    "ArithmeticError",
    "Hallucination",
    "APIMisuse",
    "MissingConstraint",
    "OutputDependency",
    "SyntaxError",
    "Other",
]

# Operator → primary failure category
OPERATOR_CATEGORY = {
    "ICO": "OrderingError",
    "WRO": "OrderingError",
    "MBO": "MissingConstraint",
    "DRO": "OutputDependency",
    "SNO": "OrderingError",
    "ORO": "OrderingError",
    "MCO": "MissingConstraint",
    "BCO": "BoundaryError",
}


def _classify_failure(result: dict) -> str:
    """Classify a pipeline failure result into a taxonomy category."""
    error = result.get("error", "") or ""
    cexs = result.get("counterexamples", [])
    patterns = result.get("pattern_matches", [])

    if "syntax" in error.lower() or "compile_error" in error.lower():
        return "SyntaxError"

    pattern_ids = {m.get("pattern_id", "") if isinstance(m, dict) else "" for m in patterns}
    if "RF07" in pattern_ids:
        return "APIMisuse"
    if "RF02" in pattern_ids or "RF01" in pattern_ids:
        return "APIMisuse"

    # Classify from counterexample signals
    for cx in cexs[:3]:
        if isinstance(cx, dict):
            scenario_idx = cx.get("scenario_index", 0)
            msg = cx.get("message", "").lower()
            inputs = cx.get("inputs", {})
            expected = cx.get("expected", {})
            actual = cx.get("actual", {})
            if "order" in msg or scenario_idx > 1:
                return "OrderingError"
            if expected and actual:
                for k in expected:
                    if k in actual:
                        diff = abs(expected[k] - actual.get(k, expected[k] + 99))
                        if 0 < diff <= 2:
                            return "BoundaryError"
                        if diff > 100:
                            return "ArithmeticError"

    if cexs:
        return "OutputDependency"

    if not cexs and not patterns and not error:
        return "Hallucination"

    return "Other"


def analyze_failure_taxonomy(
    run_dir: Path,
    out_dir: Path,
    *,
    modes: list[str] | None = None,
) -> dict:
    """Build failure taxonomy from results.jsonl."""
    modes = modes or ["M", "B1", "B2"]
    results_path = run_dir / "results.jsonl"
    if not results_path.exists():
        print(f"[failure] No results.jsonl at {results_path}", file=sys.stderr)
        return {}

    records = []
    with results_path.open(encoding="utf-8") as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    taxonomy: dict = {}
    for mode in modes:
        mode_records = [r for r in records if r.get("mode") == mode]
        failed = [r for r in mode_records if not r.get("success", False)]
        if not failed:
            taxonomy[mode] = {"total_failed": 0, "categories": {}}
            continue
        cats = Counter(_classify_failure(r) for r in failed)
        taxonomy[mode] = {
            "total_failed": len(failed),
            "total_records": len(mode_records),
            "failure_rate": round(len(failed) / max(len(mode_records), 1), 4),
            "categories": {cat: {"count": cats.get(cat, 0),
                                  "fraction": round(cats.get(cat, 0) / len(failed), 4)}
                           for cat in FAILURE_CATEGORIES},
        }

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "failure_taxonomy.json").write_text(
        json.dumps(taxonomy, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[failure] Failure taxonomy → {out_dir / 'failure_taxonomy.json'}")
    return taxonomy


def analyze_repair_dynamics(
    run_dir: Path,
    out_dir: Path,
    *,
    modes: list[str] | None = None,
) -> dict:
    """Extract Conf(k) trajectory from attempt_history."""
    modes = modes or ["M", "B2"]
    results_path = run_dir / "results.jsonl"
    if not results_path.exists():
        print(f"[repair] No results.jsonl at {results_path}", file=sys.stderr)
        return {}

    trajectory: dict = {mode: defaultdict(list) for mode in modes}
    with results_path.open(encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            mode = rec.get("mode")
            if mode not in modes:
                continue
            for entry in rec.get("attempt_history", []):
                k = entry.get("attempt")
                conf = entry.get("conf", 0.0)
                if k:
                    trajectory[mode][k].append(conf)

    summary: dict = {}
    for mode in modes:
        summary[mode] = {}
        for k in sorted(trajectory[mode].keys()):
            vals = trajectory[mode][k]
            if vals:
                import statistics
                mean_c = statistics.mean(vals)
                try:
                    ci = 1.96 * statistics.stdev(vals) / (len(vals) ** 0.5)
                except statistics.StatisticsError:
                    ci = 0.0
                summary[mode][k] = {
                    "n": len(vals),
                    "mean_conf": round(mean_c, 4),
                    "ci_95": round(ci, 4),
                }

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "repair_dynamics.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[repair] Repair dynamics → {out_dir / 'repair_dynamics.json'}")
    return summary


def analyze_pattern_prf1(
    prevention_run_dir: Path,
    out_dir: Path,
) -> dict:
    """Compute per-pattern P/R/F1 from prevention eval JSONL."""
    eval_path = prevention_run_dir / "prevention_eval.jsonl"
    if not eval_path.exists():
        # Try to run the compute function directly on tasks
        print(f"[pattern] No prevention_eval.jsonl at {eval_path}. "
              "Loading tasks and computing from scratch...", file=sys.stderr)
        try:
            from src.benchmarks import load_benchmark
            from src.evaluation.prevention import compute_pattern_guard_prf1
            tasks = load_benchmark()
            tasks = [t for t in tasks if "HardSynthetic" in t.get("taskId", "")][:40]
            results = compute_pattern_guard_prf1(tasks)
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "pattern_prf1.json").write_text(
                json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            print(f"[pattern] Pattern P/R/F1 → {out_dir / 'pattern_prf1.json'}")
            return results
        except Exception as e:
            print(f"[pattern] Failed: {e}", file=sys.stderr)
            return {}

    # Parse prevention records and compute per-pattern stats
    records = []
    with eval_path.open(encoding="utf-8") as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    # Aggregate by operator category
    operator_category = {
        "ICO": "Ordering", "WRO": "Ordering", "MBO": "MissingPrecond",
        "DRO": "OutputDep", "SNO": "GuardInversion", "ORO": "Ordering",
        "MCO": "MissingConstraint", "BCO": "Boundary",
    }
    # For P/R/F1 we need to run the pattern guard on the mutant code, which isn't
    # stored in the prevention JSONL. Delegate to the full compute function.
    print("[pattern] Prevention JSONL found but code payloads not stored; "
          "recompute via compute_pattern_guard_prf1.", file=sys.stderr)
    return {}


def main() -> None:
    parser = argparse.ArgumentParser(description="Failure and pattern analysis runner")
    parser.add_argument("--run", type=Path, default=None, help="Main experiment run directory")
    parser.add_argument(
        "--analysis",
        nargs="+",
        choices=["failure_taxonomy", "repair_dynamics", "pattern_precision_recall", "all"],
        default=["all"],
    )
    parser.add_argument(
        "--prevention-run",
        type=Path,
        default=None,
        help="Prevention experiment run directory (for pattern P/R/F1)",
    )
    parser.add_argument("--modes", nargs="+", default=None)
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory (default: <run>/analysis)",
    )
    args = parser.parse_args()

    run_dir = args.run or (ARTIFACTS / "run_ccf_b_main_v1")
    out_dir = args.out or (run_dir / "analysis")

    analyses = args.analysis
    if "all" in analyses:
        analyses = ["failure_taxonomy", "repair_dynamics", "pattern_precision_recall"]

    if "failure_taxonomy" in analyses:
        analyze_failure_taxonomy(run_dir, out_dir / "failure", modes=args.modes)

    if "repair_dynamics" in analyses:
        analyze_repair_dynamics(run_dir, out_dir / "repair_dynamics", modes=args.modes)

    if "pattern_precision_recall" in analyses:
        prevention_dir = args.prevention_run or (ARTIFACTS / "prevention_ccf_b_v1")
        analyze_pattern_prf1(prevention_dir, out_dir / "pattern_prf1")

    print(f"\n[analysis] All analyses complete. Output: {out_dir}")


if __name__ == "__main__":
    main()
