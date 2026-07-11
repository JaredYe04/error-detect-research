#!/usr/bin/env python3
"""Build overlap-rich / headroom subset from RealSpec + HKCA09 for E6.

Aggregate Conf on easy public ASFL often ties B2/M_eq. This subset keeps
ordered-guard tasks with medium/high overlap (or all HKCA09 reconstructions)
so feedback-content ablation can show typed IR advantage.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.benchmarks.complexity import annotate_tasks_complexity


def _load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "benchmarks" / "real_headroom_e6.json",
    )
    ap.add_argument("--min-overlap", type=float, default=1.2)
    ap.add_argument("--include-all-hkca09", action="store_true", default=True)
    args = ap.parse_args()

    pools = [
        ROOT / "benchmarks" / "hkca09_sofl_fsf.json",
        ROOT / "benchmarks" / "industrial_sofl.json",
        ROOT / "benchmarks" / "published_industrial_pilot.json",
        ROOT / "benchmarks" / "github_harvest_v1.json",
    ]
    seen = set()
    tasks: list[dict] = []
    for p in pools:
        for t in _load(p):
            tid = t.get("taskId")
            if not tid or tid in seen:
                continue
            seen.add(tid)
            tasks.append(t)

    annotate_tasks_complexity(tasks)

    selected = []
    for t in tasks:
        tid = str(t.get("taskId", ""))
        rate = float((t.get("complexity") or {}).get("overlap_rate") or 0)
        tier = (t.get("complexity") or {}).get("overlap_density_tier")
        is_hk = tid.startswith("HKCA09.")
        if args.include_all_hkca09 and is_hk:
            selected.append(t)
        elif rate >= args.min_overlap or tier == "high":
            selected.append(t)

    # de-dup preserve order
    out_tasks, seen2 = [], set()
    for t in selected:
        tid = t["taskId"]
        if tid in seen2:
            continue
        seen2.add(tid)
        out_tasks.append(t)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out_tasks, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ids = ROOT / "benchmarks" / "real_headroom_e6_ids.json"
    ids.write_text(json.dumps([t["taskId"] for t in out_tasks], indent=2) + "\n", encoding="utf-8")

    hk = sum(1 for t in out_tasks if str(t["taskId"]).startswith("HKCA09."))
    print(f"selected={len(out_tasks)} (hkca09={hk}) -> {args.out}")
    by_tier = {}
    for t in out_tasks:
        tr = (t.get("complexity") or {}).get("overlap_density_tier") or "?"
        by_tier[tr] = by_tier.get(tr, 0) + 1
    print("tiers", by_tier)
    return 0 if out_tasks else 1


if __name__ == "__main__":
    raise SystemExit(main())
