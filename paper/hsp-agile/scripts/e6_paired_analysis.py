#!/usr/bin/env python3
"""E6 paired win/loss/tie + bootstrap CI: semantic_ir vs test_only / test_expected.

Default input:
  artifacts/run_feedback_v2/feedback_variants/results.jsonl

Outputs under paper/hsp-agile/data/processed/:
  e6_paired_summary.json
  e6_paired_summary.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PAPER_PROC = Path(__file__).resolve().parents[1] / "data" / "processed"
DEFAULT_RUN = ROOT / "artifacts" / "run_feedback_v2" / "feedback_variants"

FOCAL = "semantic_ir"
COMPARATORS = ("test_only", "test_expected")
# Map E6 labels A/B/C if present
LABEL_TO_VARIANT = {
    "A": "test_only",
    "B": "test_expected",
    "C": "semantic_ir",
    "test_only": "test_only",
    "test_expected": "test_expected",
    "semantic_ir": "semantic_ir",
    "full_semantic_ir": "semantic_ir",
}
EPS = 1e-12


def load_rows(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _variant(row: dict) -> str | None:
    raw = row.get("feedback_variant") or row.get("variant") or row.get("variant_label")
    if raw is None:
        return None
    key = str(raw).strip()
    return LABEL_TO_VARIANT.get(key, LABEL_TO_VARIANT.get(key.lower(), key))


def _conf(row: dict) -> float:
    if "strict_formal_conformance" in row:
        return float(row["strict_formal_conformance"])
    if "formal_conformance" in row:
        return float(row["formal_conformance"])
    if "mean_conf" in row:
        return float(row["mean_conf"])
    raise KeyError("missing conformance field")


def paired_counts(by_task: dict[str, dict[str, float]], a: str, b: str) -> dict:
    wins = losses = ties = 0
    deltas: list[float] = []
    paired_tasks: list[str] = []
    for tid, scores in by_task.items():
        if a not in scores or b not in scores:
            continue
        delta = scores[a] - scores[b]
        deltas.append(delta)
        paired_tasks.append(tid)
        if delta > EPS:
            wins += 1
        elif delta < -EPS:
            losses += 1
        else:
            ties += 1
    n = wins + losses + ties
    mean_a = (
        sum(by_task[t][a] for t in paired_tasks) / n if n else 0.0
    )
    mean_b = (
        sum(by_task[t][b] for t in paired_tasks) / n if n else 0.0
    )
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
        "deltas": deltas,
    }


def bootstrap_ci(deltas: list[float], b: int = 5000, seed: int = 42) -> dict:
    if not deltas:
        return {"ci_low_pp": None, "ci_high_pp": None, "mean_delta_pp": None}
    rng = random.Random(seed)
    n = len(deltas)
    means = []
    for _ in range(b):
        sample = [deltas[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo = means[int(0.025 * b)]
    hi = means[min(b - 1, int(0.975 * b))]
    return {
        "mean_delta_pp": 100.0 * (sum(deltas) / n),
        "ci_low_pp": 100.0 * lo,
        "ci_high_pp": 100.0 * hi,
        "B": b,
        "seed": seed,
    }


def wilcoxon_p(deltas: list[float]) -> float | None:
    nonzero = [d for d in deltas if abs(d) > EPS]
    if len(nonzero) < 5:
        return None
    try:
        from scipy.stats import wilcoxon

        stat = wilcoxon(nonzero, alternative="two-sided")
        return float(stat.pvalue)
    except Exception:
        return None


def analyse(rows: list[dict]) -> dict:
    by_task: dict[str, dict[str, float]] = defaultdict(dict)
    variant_conf: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        tid = r.get("task_id") or r.get("taskId")
        variant = _variant(r)
        if not tid or not variant:
            continue
        c = _conf(r)
        by_task[tid][variant] = c
        variant_conf[variant].append(c)

    means = {
        v: {"n": len(vals), "mean_conf": sum(vals) / len(vals) if vals else 0.0}
        for v, vals in sorted(variant_conf.items())
    }

    comparisons = []
    for comp in COMPARATORS:
        rec = paired_counts(by_task, FOCAL, comp)
        deltas = rec.pop("deltas")
        ci = bootstrap_ci(deltas)
        rec.update(ci)
        rec["wilcoxon_p"] = wilcoxon_p(deltas)
        comparisons.append(rec)

    return {
        "source": None,
        "n_rows": len(rows),
        "n_tasks": len(by_task),
        "variant_means": means,
        "comparisons": comparisons,
        "note": (
            "Paired per task_id. Wins = semantic_ir > comparator. "
            "Bootstrap 95% CI on mean paired delta (B=5000, seed=42)."
        ),
    }


def write_outputs(summary: dict, out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "e6_paired_summary.json"
    csv_path = out_dir / "e6_paired_summary.csv"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    fields = [
        "focal",
        "comparator",
        "n_paired",
        "wins",
        "losses",
        "ties",
        "mean_focal",
        "mean_comparator",
        "delta_pp",
        "ci_low_pp",
        "ci_high_pp",
        "wilcoxon_p",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for row in summary["comparisons"]:
            w.writerow(row)
    return json_path, csv_path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    ap.add_argument("--out-dir", type=Path, default=PAPER_PROC)
    args = ap.parse_args()
    jsonl = args.run_dir / "results.jsonl"
    if not jsonl.exists():
        print(f"missing {jsonl}", file=sys.stderr)
        return 1
    rows = load_rows(jsonl)
    summary = analyse(rows)
    summary["source"] = str(jsonl.resolve())
    json_path, csv_path = write_outputs(summary, args.out_dir)
    print(f"source={summary['source']} n_rows={summary['n_rows']} n_tasks={summary['n_tasks']}")
    for v, m in summary["variant_means"].items():
        print(f"  {v}: n={m['n']} mean_Conf={100 * m['mean_conf']:.1f}%")
    for c in summary["comparisons"]:
        print(
            f"  vs {c['comparator']}: W/L/T={c['wins']}/{c['losses']}/{c['ties']} "
            f"delta={c['delta_pp']:+.1f} pp "
            f"CI=[{c['ci_low_pp']:.1f}, {c['ci_high_pp']:.1f}] "
            f"wilcoxon_p={c['wilcoxon_p']}"
        )
    print(f"Wrote {json_path}")
    print(f"Wrote {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
