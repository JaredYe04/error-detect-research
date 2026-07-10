#!/usr/bin/env python3
"""E14 paired win/loss/tie: semantic_ir vs execution_trace_matched / test_only.

Expected input (from experiments/run_e14_sweep.py):
  artifacts/run_e14_sweep_v1/results.jsonl
  each row: task_id, feedback_variant, strict_formal_conformance
  variants: test_only, test_expected, semantic_ir, execution_trace_matched

Outputs under paper/hsp-agile/data/processed/:
  e14_paired_summary.json
  e14_paired_summary.csv

Usage:
  python paper/hsp-agile/scripts/e14_paired_analysis.py
  python paper/hsp-agile/scripts/e14_paired_analysis.py --run-dir artifacts/run_e14_sweep_v1
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PAPER_PROC = Path(__file__).resolve().parents[1] / "data" / "processed"
DEFAULT_RUN = ROOT / "artifacts" / "run_e14_sweep_v1"

FOCAL = "semantic_ir"
COMPARATORS = ("execution_trace_matched", "test_only")
EPS = 1e-12


def load_rows(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _conf(row: dict) -> float:
    if "strict_formal_conformance" in row:
        return float(row["strict_formal_conformance"])
    if "formal_conformance" in row:
        return float(row["formal_conformance"])
    raise KeyError("missing conformance field")


def _strict(row: dict) -> float:
    """Binary strict success in {0.0, 1.0}."""
    if "strict_formal_passed" in row:
        return 1.0 if row["strict_formal_passed"] else 0.0
    return 1.0 if _conf(row) >= 1.0 - EPS else 0.0


def paired_counts(
    by_task: dict[str, dict[str, float]],
    a: str,
    b: str,
) -> dict[str, float | int]:
    wins = losses = ties = 0
    deltas: list[float] = []
    for scores in by_task.values():
        if a not in scores or b not in scores:
            continue
        delta = scores[a] - scores[b]
        deltas.append(delta)
        if delta > EPS:
            wins += 1
        elif delta < -EPS:
            losses += 1
        else:
            ties += 1
    n = wins + losses + ties
    mean_a = sum(by_task[t][a] for t in by_task if a in by_task[t] and b in by_task[t]) / n if n else 0.0
    mean_b = sum(by_task[t][b] for t in by_task if a in by_task[t] and b in by_task[t]) / n if n else 0.0
    return {
        "focal": a,
        "comparator": b,
        "n_paired": n,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "mean_focal": mean_a,
        "mean_comparator": mean_b,
        "delta_pp": 100.0 * (mean_a - mean_b),
        "mean_delta": sum(deltas) / n if n else 0.0,
    }


def analyse(rows: list[dict]) -> dict:
    by_task_conf: dict[str, dict[str, float]] = defaultdict(dict)
    by_task_strict: dict[str, dict[str, float]] = defaultdict(dict)
    variant_conf: dict[str, list[float]] = defaultdict(list)
    variant_strict: dict[str, list[float]] = defaultdict(list)

    for r in rows:
        tid = r.get("task_id") or r.get("taskId")
        variant = r.get("feedback_variant")
        if not tid or not variant:
            continue
        c = _conf(r)
        s = _strict(r)
        by_task_conf[tid][variant] = c
        by_task_strict[tid][variant] = s
        variant_conf[variant].append(c)
        variant_strict[variant].append(s)

    means = {
        v: {
            "n": len(vals),
            "mean_conf": sum(vals) / len(vals) if vals else 0.0,
            "mean_strict": (
                sum(variant_strict[v]) / len(variant_strict[v]) if variant_strict[v] else 0.0
            ),
        }
        for v, vals in sorted(variant_conf.items())
    }

    comparisons: list[dict] = []
    for metric_name, by_task in (("mean_conf", by_task_conf), ("strict_conf", by_task_strict)):
        for comp in COMPARATORS:
            rec = paired_counts(by_task, FOCAL, comp)
            rec["metric"] = metric_name
            comparisons.append(rec)

    return {
        "source": None,  # filled by main
        "n_rows": len(rows),
        "n_tasks": len(by_task_conf),
        "variant_means": means,
        "comparisons": comparisons,
        "note": (
            "Paired per task_id. Wins = semantic_ir > comparator on the metric. "
            "Aggregate means in e14_feedback_summary.csv remain the table source; "
            "this file adds paired W/L/T only."
        ),
    }


def write_outputs(summary: dict, out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "e14_paired_summary.json"
    csv_path = out_dir / "e14_paired_summary.csv"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    fieldnames = [
        "metric",
        "focal",
        "comparator",
        "n_paired",
        "wins",
        "losses",
        "ties",
        "mean_focal",
        "mean_comparator",
        "delta_pp",
        "mean_delta",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in summary["comparisons"]:
            w.writerow(row)
    return json_path, csv_path


def print_report(summary: dict) -> None:
    print(f"source={summary['source']} n_rows={summary['n_rows']} n_tasks={summary['n_tasks']}")
    print("\nVariant means (strict_formal_conformance / strict success rate):")
    for v, m in summary["variant_means"].items():
        print(
            f"  {v}: n={m['n']} "
            f"mean_Conf={100 * m['mean_conf']:.1f}% "
            f"strict={100 * m['mean_strict']:.1f}%"
        )
    print(f"\nPaired {FOCAL} vs comparators:")
    for c in summary["comparisons"]:
        print(
            f"  [{c['metric']}] vs {c['comparator']}: "
            f"wins={c['wins']} losses={c['losses']} ties={c['ties']} "
            f"(n={c['n_paired']}); "
            f"means {100 * c['mean_focal']:.1f}% vs {100 * c['mean_comparator']:.1f}% "
            f"({c['delta_pp']:+.1f} pp)"
        )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--run-dir",
        type=Path,
        default=DEFAULT_RUN,
        help="Directory containing results.jsonl (default: artifacts/run_e14_sweep_v1)",
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=PAPER_PROC,
        help="Output directory for JSON/CSV",
    )
    args = ap.parse_args()

    jsonl = args.run_dir / "results.jsonl"
    if not jsonl.exists():
        schema = {
            "expected_path": str(jsonl),
            "expected_schema": {
                "task_id": "str",
                "feedback_variant": (
                    "test_only | test_expected | semantic_ir | execution_trace_matched"
                ),
                "strict_formal_conformance": "float in [0,1]",
                "strict_formal_passed": "bool (optional; derived from conf if absent)",
            },
            "how_to_produce": (
                "python experiments/run_e14_sweep.py --run-name run_e14_sweep_v1"
            ),
            "status": "no-op: per-task results missing; paired win counts not invented",
        }
        args.out_dir.mkdir(parents=True, exist_ok=True)
        stub = args.out_dir / "e14_paired_summary.json"
        stub.write_text(json.dumps(schema, indent=2), encoding="utf-8")
        print(
            f"E14 paired analysis: no-op — missing {jsonl}\n"
            f"Wrote schema stub to {stub}\n"
            "Do not invent paired win counts. Aggregate means may still exist in "
            "e14_feedback_summary.csv.",
            file=sys.stderr,
        )
        return 1

    rows = load_rows(jsonl)
    summary = analyse(rows)
    summary["source"] = str(jsonl.resolve())
    json_path, csv_path = write_outputs(summary, args.out_dir)
    print_report(summary)
    print(f"\nWrote {json_path}")
    print(f"Wrote {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
