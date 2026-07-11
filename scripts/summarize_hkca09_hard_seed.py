#!/usr/bin/env python3
"""Bootstrap paired CI for HKCA09 hard-seed FULL vs test_only."""

from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    paths = [
        ROOT / "artifacts" / "run_hkca09_hard_seed_e6_v1" / "results.jsonl",
        ROOT / "artifacts" / "run_hkca09_hard_seed_e6_v2" / "results.jsonl",
    ]
    rows = []
    for p in paths:
        if p.exists():
            rows.extend(json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip())

    by: dict[tuple[str, str], dict[str, float]] = defaultdict(dict)
    for r in rows:
        by[(r["task_id"], r["seed_type"])][r["feedback_variant"]] = float(r["formal_conformance"])

    out = {"by_seed": {}, "pooled_wrong_family": None}
    rng = random.Random(42)
    for seed in sorted({k[1] for k in by}):
        deltas = []
        for (tid, st), scores in by.items():
            if st != seed or "semantic_ir" not in scores or "test_only" not in scores:
                continue
            deltas.append(scores["semantic_ir"] - scores["test_only"])
        if not deltas:
            continue
        means = []
        n = len(deltas)
        for _ in range(5000):
            sample = [deltas[rng.randrange(n)] for _ in range(n)]
            means.append(sum(sample) / n)
        means.sort()
        w = sum(1 for d in deltas if d > 1e-12)
        l = sum(1 for d in deltas if d < -1e-12)
        t = n - w - l
        lo, hi = means[int(0.025 * 5000)], means[int(0.975 * 5000)]
        out["by_seed"][seed] = {
            "n": n,
            "mean_delta": round(sum(deltas) / n, 4),
            "mean_ir": round(
                sum(by[(tid, seed)]["semantic_ir"] for tid, st in by if st == seed and "semantic_ir" in by[(tid, st)])
                / max(1, sum(1 for tid, st in by if st == seed and "semantic_ir" in by[(tid, st)])),
                4,
            ),
            "mean_test_only": round(
                sum(by[(tid, seed)]["test_only"] for tid, st in by if st == seed and "test_only" in by[(tid, st)])
                / max(1, sum(1 for tid, st in by if st == seed and "test_only" in by[(tid, st)])),
                4,
            ),
            "wlt": [w, l, t],
            "ci95": [round(lo, 4), round(hi, 4)],
            "excl0": bool(lo > 0 or hi < 0),
        }

    dest = (
        ROOT
        / "paper"
        / "hsp-agile"
        / "artifacts"
        / "strengthening_sprint"
        / "agent_d_industrial"
        / "HKCA09_HARD_SEED_PAIRED.json"
    )
    dest.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    print("->", dest)


if __name__ == "__main__":
    main()
