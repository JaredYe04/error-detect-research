#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Paired stats + bootstrap CI for hard-seed IR ablation results."""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path


def _load(path: Path) -> list[dict]:
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    # dedupe: keep last row per (task, seed, variant, model)
    keyed: dict[tuple, dict] = {}
    for r in rows:
        k = (r["task_id"], r.get("seed_type"), r["feedback_variant"], r.get("model"))
        keyed[k] = r
    return list(keyed.values())


def _paired(rows: list[dict], seed: str, a: str, b: str) -> dict:
    by_task: dict[str, dict[str, float]] = defaultdict(dict)
    for r in rows:
        if r.get("seed_type") != seed:
            continue
        by_task[r["task_id"]][r["feedback_variant"]] = float(r["formal_conformance"])
    deltas = []
    w = l = t = 0
    for scores in by_task.values():
        if a not in scores or b not in scores:
            continue
        d = scores[a] - scores[b]
        deltas.append(d)
        if d > 1e-12:
            w += 1
        elif d < -1e-12:
            l += 1
        else:
            t += 1
    if not deltas:
        return {"n": 0}
    mean = sum(deltas) / len(deltas)
    # bootstrap CI
    rng = random.Random(0)
    boots = []
    for _ in range(2000):
        sample = [deltas[rng.randrange(len(deltas))] for _ in range(len(deltas))]
        boots.append(sum(sample) / len(sample))
    boots.sort()
    lo = boots[int(0.025 * len(boots))]
    hi = boots[int(0.975 * len(boots)) - 1]
    return {
        "n": len(deltas),
        "wins": w,
        "losses": l,
        "ties": t,
        "mean_delta": round(mean, 6),
        "mean_delta_pp": round(100 * mean, 2),
        "ci95": [round(lo, 6), round(hi, 6)],
        "ci95_pp": [round(100 * lo, 2), round(100 * hi, 2)],
        "ci_excludes_0": not (lo <= 0 <= hi),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("results", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    rows = _load(args.results)
    seeds = sorted({r.get("seed_type") for r in rows if r.get("seed_type")})
    models = sorted({r.get("model") for r in rows if r.get("model")})
    variants = sorted({r["feedback_variant"] for r in rows})
    report: dict = {"n_rows_deduped": len(rows), "models": models, "seeds": seeds, "paired": {}}
    for seed in seeds:
        for v in variants:
            if v == "semantic_ir":
                continue
            key = f"{seed}|FULL_vs_{v}"
            report["paired"][key] = _paired(rows, seed, "semantic_ir", v)
    # means
    means: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        means[f"{r.get('seed_type')}|{r['feedback_variant']}"].append(float(r["formal_conformance"]))
    report["mean_conf"] = {k: round(sum(v) / len(v), 4) for k, v in sorted(means.items())}
    text = json.dumps(report, indent=2)
    print(text)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
