#!/usr/bin/env python3
"""Build E11 held-out / external SOFL benchmark JSON files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.benchmarks.complexity import annotate_tasks_complexity
from src.benchmarks.external_sofl_corpus import load_external_sofl_tasks


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--external-out", type=Path, default=ROOT / "benchmarks" / "external_sofl.json")
    p.add_argument("--manual-out", type=Path, default=ROOT / "benchmarks" / "manual_heldout.json")
    p.add_argument("--annotate", action="store_true")
    args = p.parse_args()

    external = load_external_sofl_tasks()
    if args.annotate:
        external = annotate_tasks_complexity(external)
    args.external_out.parent.mkdir(parents=True, exist_ok=True)
    args.external_out.write_text(json.dumps(external, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(external)} external tasks -> {args.external_out}")

    # Manual held-out: same external corpus, excluding any ID in hard_tasks.json
    hard_ids = set()
    hard_path = ROOT / "benchmarks" / "hard_tasks.json"
    if hard_path.exists():
        hard_ids = {t["taskId"] for t in json.loads(hard_path.read_text(encoding="utf-8"))}
    manual = [t for t in external if t["taskId"] not in hard_ids]
    if args.annotate and manual is external:
        pass
    elif args.annotate:
        manual = annotate_tasks_complexity(manual)
    args.manual_out.write_text(json.dumps(manual, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(manual)} held-out tasks (zero overlap with hard set) -> {args.manual_out}")


if __name__ == "__main__":
    main()
