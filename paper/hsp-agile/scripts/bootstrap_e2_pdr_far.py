#!/usr/bin/env python3
"""Bootstrap 95% CIs for E2 impl-screening PDR/FAR (M vs B2).

Reads artifacts/prevention_eval/prevention_full_v1/prevention_eval.jsonl
and writes paper/hsp-agile/data/processed/e2_pdr_far_bootstrap.json.
"""

from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
JSONL = ROOT / "artifacts" / "prevention_eval" / "prevention_full_v1" / "prevention_eval.jsonl"
OUT = ROOT / "paper" / "hsp-agile" / "data" / "processed" / "e2_pdr_far_bootstrap.json"
N_BOOT = 5000
SEED = 42
MODES = ("B1", "B2", "M")
EVAL = "impl_screening"


def _rates(rows: list[dict]) -> tuple[float, float]:
    n = len(rows)
    if n == 0:
        return float("nan"), float("nan")
    pdr = sum(1 for r in rows if r.get("detected")) / n
    # FAR: accepted while faulty (detected==False means slipped through Accept)
    far = sum(1 for r in rows if r.get("accepted") and not r.get("detected")) / n
    return pdr, far


def main() -> None:
    by_mode: dict[str, list[dict]] = defaultdict(list)
    with JSONL.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("eval_type") != EVAL:
                continue
            mode = row.get("mode")
            if mode in MODES:
                by_mode[mode].append(row)

    rng = random.Random(SEED)
    summary: dict = {"eval_type": EVAL, "n_boot": N_BOOT, "seed": SEED, "modes": {}}

    for mode in MODES:
        rows = by_mode[mode]
        pdr, far = _rates(rows)
        pdr_s: list[float] = []
        far_s: list[float] = []
        n = len(rows)
        for _ in range(N_BOOT):
            sample = [rows[rng.randrange(n)] for _ in range(n)]
            bp, bf = _rates(sample)
            pdr_s.append(bp)
            far_s.append(bf)
        pdr_s.sort()
        far_s.sort()
        lo = int(0.025 * (N_BOOT - 1))
        hi = int(0.975 * (N_BOOT - 1))
        summary["modes"][mode] = {
            "n": n,
            "pdr": round(pdr, 6),
            "far": round(far, 6),
            "pdr_ci95": [round(pdr_s[lo], 6), round(pdr_s[hi], 6)],
            "far_ci95": [round(far_s[lo], 6), round(far_s[hi], 6)],
        }

    # Paired bootstrap on Δ(M−B2) if same mutant ids exist
    b2 = {r["mutant_id"]: r for r in by_mode["B2"]}
    m = {r["mutant_id"]: r for r in by_mode["M"]}
    common = sorted(set(b2) & set(m))
    deltas_pdr: list[float] = []
    deltas_far: list[float] = []
    for _ in range(N_BOOT):
        ids = [common[rng.randrange(len(common))] for _ in range(len(common))]
        b2_rows = [b2[i] for i in ids]
        m_rows = [m[i] for i in ids]
        bp2, bf2 = _rates(b2_rows)
        bpm, bfm = _rates(m_rows)
        deltas_pdr.append(bpm - bp2)
        deltas_far.append(bfm - bf2)
    deltas_pdr.sort()
    deltas_far.sort()
    lo = int(0.025 * (N_BOOT - 1))
    hi = int(0.975 * (N_BOOT - 1))
    summary["delta_M_minus_B2"] = {
        "n_paired": len(common),
        "pdr_pp": round((summary["modes"]["M"]["pdr"] - summary["modes"]["B2"]["pdr"]) * 100, 3),
        "far_pp": round((summary["modes"]["M"]["far"] - summary["modes"]["B2"]["far"]) * 100, 3),
        "pdr_delta_ci95": [round(deltas_pdr[lo], 6), round(deltas_pdr[hi], 6)],
        "far_delta_ci95": [round(deltas_far[lo], 6), round(deltas_far[hi], 6)],
        "pdr_ci_excludes_0": not (deltas_pdr[lo] <= 0 <= deltas_pdr[hi]),
        "far_ci_excludes_0": not (deltas_far[lo] <= 0 <= deltas_far[hi]),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
