#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.benchmarks.complexity import annotate_tasks_complexity
from src.benchmarks.hkca09_sofl_fsf import load_hkca09_sofl_fsf_tasks
from src.harvest.to_fsf import validate_task


def main() -> int:
    tasks = load_hkca09_sofl_fsf_tasks()
    kept, rejected = [], []
    for t in tasks:
        st = validate_task(t)
        if st.get("ok"):
            kept.append(t)
        else:
            rejected.append({"taskId": t.get("taskId"), "status": st})

    annotate_tasks_complexity(kept)
    out = ROOT / "benchmarks" / "hkca09_sofl_fsf.json"
    out.write_text(json.dumps(kept, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"kept={len(kept)} rejected={len(rejected)} -> {out}")
    for r in rejected:
        print("REJECT", r)

    rates = sorted(t["complexity"]["overlap_rate"] for t in kept)
    tiers = {}
    for t in kept:
        tiers[t["complexity"]["overlap_density_tier"]] = tiers.get(t["complexity"]["overlap_density_tier"], 0) + 1
    print("tiers", tiers)
    print("overlap_rate", rates[0], rates[len(rates) // 2], rates[-1])
    for t in sorted(kept, key=lambda x: -x["complexity"]["overlap_rate"])[:10]:
        c = t["complexity"]
        print(f"  {t['taskId']}: rate={c['overlap_rate']} tier={c['overlap_density_tier']} sc={c['scenario_count']}")
    return 0 if kept and not rejected else 1


if __name__ == "__main__":
    raise SystemExit(main())
