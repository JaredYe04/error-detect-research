"""E12 multi-seed stability analysis for B2 vs M."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import friedmanchisquare, wilcoxon

PAPER_ROOT = Path(__file__).resolve().parents[1]
PROC = PAPER_ROOT / "data" / "processed"


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--jsonl", type=Path, required=True, help="E12 results.jsonl path")
    p.add_argument("--out", type=Path, default=PROC / "e12_stability_summary.json")
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    rows = [json.loads(line) for line in args.jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
    df = pd.DataFrame(rows)
    conf_col = "strict_formal_conformance" if "strict_formal_conformance" in df.columns else "formal_conformance"

    summary: dict[str, object] = {"modes": {}, "pairwise": {}}
    for mode in sorted(df["mode"].unique()):
        sub = df[df["mode"] == mode]
        per_seed = sub.groupby("repeat")[conf_col].mean()
        summary["modes"][mode] = {
            "mean_conf": float(sub[conf_col].mean()),
            "std_conf": float(sub[conf_col].std()),
            "seed_means": {int(k): float(v) for k, v in per_seed.items()},
        }

    pivot = df.pivot_table(
        index=["task_id", "repeat"],
        columns="mode",
        values=conf_col,
        aggfunc="first",
    ).reset_index()
    if {"B2", "M"}.issubset(pivot.columns):
        wins = int((pivot.groupby("task_id").apply(lambda g: g["M"].mean() > g["B2"].mean()).sum()))
        n_tasks = pivot["task_id"].nunique()
        summary["pairwise"] = {
            "m_wins": wins,
            "n_tasks": n_tasks,
            "win_rate": wins / n_tasks if n_tasks else 0.0,
        }
        seed_rank = []
        for rep in sorted(df["repeat"].unique()):
            rep_df = df[df["repeat"] == rep]
            m_mean = rep_df[rep_df["mode"] == "M"][conf_col].mean()
            b2_mean = rep_df[rep_df["mode"] == "B2"][conf_col].mean()
            seed_rank.append("M" if m_mean > b2_mean else ("B2" if b2_mean > m_mean else "tie"))
        summary["ranking_by_seed"] = seed_rank
        summary["ranking_stable"] = len(set(seed_rank)) == 1

    if {"B2", "M"}.issubset(df["mode"].unique()):
        friedman_data = []
        for task_id, grp in df.groupby("task_id"):
            b2 = grp[grp["mode"] == "B2"].sort_values("repeat")[conf_col].tolist()
            m = grp[grp["mode"] == "M"].sort_values("repeat")[conf_col].tolist()
            if len(b2) == len(m) and len(b2) >= 2:
                friedman_data.append((b2, m))
        if friedman_data and len(friedman_data[0][0]) >= 2:
            n_seeds = len(friedman_data[0][0])
            arrays = [
                np.array([pair[0][i] for pair in friedman_data])
                for i in range(n_seeds)
            ] + [
                np.array([pair[1][i] for pair in friedman_data])
                for i in range(n_seeds)
            ]
            try:
                stat, p = friedmanchisquare(*arrays)
                summary["friedman"] = {"statistic": float(stat), "p": float(p)}
            except ValueError:
                pass

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
