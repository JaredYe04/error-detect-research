#!/usr/bin/env python3
"""Offline B2/B6/M_lite/A2/M impl-screening on reconstructed HardSynthetic-180.

The archived prevention_full_v1 corpus had 213 tasks (180 HardSynthetic + 33
industrial examples). Vendor examples are no longer present, so this script
reconstructs the HardSynthetic-180 slice with the original generator seed and
scores mode gates without LLM calls.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from src.benchmarks.hard_gen import generate_hard_tasks
from src.evaluation.prevention import _accept_candidate_code
from src.mutation.injectors import generate_mutants

OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"
MODES = ["B2", "B6", "M_lite", "A2", "M"]


def main() -> int:
    tasks = generate_hard_tasks(n_tasks=180, scenarios_per_task=8, seed=42)
    stats: dict[str, dict[str, Any]] = {
        m: {"detected": 0, "accepted_undetected": 0, "n": 0, "conf_sum": 0.0}
        for m in MODES
    }
    ops: dict[str, dict[str, dict[str, int]]] = {
        m: defaultdict(lambda: {"n": 0, "detected": 0}) for m in MODES
    }

    for ti, task in enumerate(tasks):
        ref = task.get("referenceCode", "")
        if not ref:
            continue
        mutants = generate_mutants(task, ref, seed=42, impl_ops=True, spec_ops=False)
        for mut in mutants:
            candidate = mut.payload.get("code", "")
            if not candidate:
                continue
            for mode in MODES:
                accepted, strict_conf = _accept_candidate_code(mode, candidate, task)
                detected = not accepted
                s = stats[mode]
                s["n"] += 1
                s["detected"] += int(detected)
                s["accepted_undetected"] += int(accepted and not detected)
                s["conf_sum"] += strict_conf
                o = ops[mode][mut.operator]
                o["n"] += 1
                o["detected"] += int(detected)
        if (ti + 1) % 30 == 0:
            print(f"processed {ti + 1}/{len(tasks)} tasks", flush=True)

    rows = []
    for mode in MODES:
        s = stats[mode]
        n = s["n"] or 1
        row = {
            "mode": mode,
            "eval_type": "impl_screening",
            "n": s["n"],
            "detection_rate": s["detected"] / n,
            "false_accept_rate": s["accepted_undetected"] / n,
            "strict_conformance": s["conf_sum"] / n,
            "by_operator": {
                k: {"n": v["n"], "pdr": v["detected"] / v["n"]}
                for k, v in ops[mode].items()
            },
        }
        rows.append(row)
        print(
            f"{mode}: n={row['n']} "
            f"PDR={100 * row['detection_rate']:.2f}% "
            f"FAR={100 * row['false_accept_rate']:.2f}%",
            flush=True,
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "source": "offline_accept_candidate_code",
        "corpus": "HardSynthetic-180 regenerated with hard_gen seed=42",
        "seed": 42,
        "n_tasks": len(tasks),
        "note": (
            "Same-denominator impl-screening on reconstructed HardSynthetic-180. "
            "Does not restore the 33 industrial tasks from prevention_full_v1. "
            "Primary screen delta remains M vs A2 on archived prevention_full_v1 "
            "(n=852)."
        ),
        "rows": rows,
    }
    json_path = OUT_DIR / "e2_b6_mlite_impl_screening.json"
    csv_path = OUT_DIR / "e2_b6_mlite_impl_screening.csv"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "mode",
                "eval_type",
                "n",
                "detection_rate",
                "false_accept_rate",
                "strict_conformance",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in writer.fieldnames})
    print(f"wrote {json_path}")
    print(f"wrote {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
