#!/usr/bin/env python3
"""Paired FULL(semantic_ir) vs A(test_only) / B(test_expected) / NO_EXP on IR seed runs."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np


def bootstrap_ci(deltas: list[float], B: int = 5000, seed: int = 42) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    arr = np.asarray(deltas, dtype=float)
    if len(arr) == 0:
        return (float("nan"), float("nan"))
    means = []
    for _ in range(B):
        sample = rng.choice(arr, size=len(arr), replace=True)
        means.append(float(sample.mean()))
    lo, hi = np.percentile(means, [2.5, 97.5])
    return float(lo), float(hi)


def analyze(run_dir: Path, focal: str = "semantic_ir", comps: list[str] | None = None) -> None:
    comps = comps or ["test_only", "test_expected", "ir_no_expected"]
    rows = [json.loads(l) for l in (run_dir / "results.jsonl").open(encoding="utf-8") if l.strip()]
    # key: (task_id, seed_type) -> variant -> conf
    grid: dict[tuple[str, str], dict[str, float]] = defaultdict(dict)
    for r in rows:
        tid = str(r["task_id"])
        seed = str(r.get("seed_type", ""))
        var = str(r["feedback_variant"])
        grid[(tid, seed)][var] = float(r["formal_conformance"])

    print(f"\n=== {run_dir.name} paired cells={len(grid)} ===")
    by_seed: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for k in grid:
        by_seed[k[1]].append(k)

    for seed, keys in sorted(by_seed.items()):
        print(f"\n-- seed={seed} n_tasks={len(keys)} --")
        for comp in comps:
            deltas = []
            wins = losses = ties = 0
            f_vals = []
            c_vals = []
            for k in keys:
                g = grid[k]
                if focal not in g or comp not in g:
                    continue
                fv, cv = g[focal], g[comp]
                f_vals.append(fv)
                c_vals.append(cv)
                d = fv - cv
                deltas.append(d)
                if abs(d) < 1e-12:
                    ties += 1
                elif d > 0:
                    wins += 1
                else:
                    losses += 1
            if not deltas:
                print(f"  {focal} vs {comp}: missing")
                continue
            mean_f = 100 * float(np.mean(f_vals))
            mean_c = 100 * float(np.mean(c_vals))
            d_pp = 100 * float(np.mean(deltas))
            lo, hi = bootstrap_ci(deltas)
            excl = lo > 0 or hi < 0
            print(
                f"  {focal} vs {comp}: FULL={mean_f:.1f}% COMP={mean_c:.1f}% "
                f"d={d_pp:+.1f}pp W/L/T={wins}/{losses}/{ties} "
                f"CI95=[{100*lo:.1f},{100*hi:.1f}] excl0={excl}"
            )


def main() -> None:
    roots = [
        "artifacts/run_ir_combo_seed_gemini_v1",
        "artifacts/run_ir_combo_seed_gpt4omini_v1",
        "artifacts/run_ir_combo_seed_deepseek_v1",
        "artifacts/run_ir_hard_seed_realspec_wrong_relop_gemini_full_v1",
        "artifacts/run_ir_hard_seed_ablation_gemini_flash_v1",
        "artifacts/run_ir_hard_seed_ablation_ecnu_plus_v1",
    ]
    for r in roots:
        p = Path(r)
        if p.exists():
            analyze(p)


if __name__ == "__main__":
    main()
