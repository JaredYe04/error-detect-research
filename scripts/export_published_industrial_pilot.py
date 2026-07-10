#!/usr/bin/env python3
"""Export published-industrial pilot corpus + optional vendor .asfl import.

Usage:
  python scripts/export_published_industrial_pilot.py
  python scripts/export_published_industrial_pilot.py --vendor-dir vendor/agile-sofl-toolchain/examples
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--vendor-dir",
        type=Path,
        default=None,
        help="Optional directory of *.asfl from agile-sofl-toolchain",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "benchmarks" / "published_industrial_pilot.json",
    )
    args = ap.parse_args()

    from src.benchmarks.published_industrial_pilot import load_published_industrial_pilot_tasks
    from src.benchmarks.complexity import annotate_tasks_complexity

    tasks = load_published_industrial_pilot_tasks()
    annotate_tasks_complexity(tasks)

    vendor_n = 0
    if args.vendor_dir and args.vendor_dir.exists():
        from src.asfl_bridge import collect_tasks_from_examples

        vendor_tasks = collect_tasks_from_examples(args.vendor_dir)
        for vt in vendor_tasks:
            vt.setdefault("externalProvenance", {})
            vt["externalProvenance"].update(
                {
                    "source": "vendor_agile_sofl_toolchain",
                    "generator": "asfl_bridge",
                    "corpus": "vendor_asfl",
                }
            )
            vt["sourceFile"] = f"vendor://{vt.get('sourceBasename', 'unknown')}"
        tasks.extend(vendor_tasks)
        vendor_n = len(vendor_tasks)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(tasks, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {args.out} n={len(tasks)} (published={len(tasks)-vendor_n}, vendor_asfl={vendor_n})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
