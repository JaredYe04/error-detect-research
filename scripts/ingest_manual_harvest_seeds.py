#!/usr/bin/env python3
"""Ingest manual decision-table JSON seeds into github_harvest corpus.

Use when live GitHub yield is low: drop schema-shaped tables under
artifacts/github_harvest/manual_seed/*.json then run this script.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.benchmarks.complexity import annotate_tasks_complexity
from src.harvest.to_fsf import decision_table_to_task, fsm_to_task, validate_task


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--seed-dir",
        type=Path,
        default=ROOT / "artifacts" / "github_harvest" / "manual_seed",
    )
    ap.add_argument(
        "--merge-into",
        type=Path,
        default=ROOT / "benchmarks" / "github_harvest_v1.json",
    )
    args = ap.parse_args()
    args.seed_dir.mkdir(parents=True, exist_ok=True)

    existing = []
    if args.merge_into.exists():
        existing = json.loads(args.merge_into.read_text(encoding="utf-8"))
    by_id = {t.get("taskId"): t for t in existing}

    added = 0
    for path in sorted(args.seed_dir.glob("*.json")):
        obj = json.loads(path.read_text(encoding="utf-8-sig"))
        prov = {"repo": "manual/seed", "path": path.name, "query_id": "manual_seed"}
        if "transitions" in obj:
            task = fsm_to_task(obj, provenance=prov)
        else:
            task = decision_table_to_task(obj, provenance=prov)
        st = validate_task(task)
        if not st.get("ok"):
            print(f"SKIP {path.name}: {st}")
            continue
        by_id[task["taskId"]] = task
        added += 1
        print(f"OK {task['taskId']}")

    tasks = list(by_id.values())
    annotate_tasks_complexity(tasks)
    args.merge_into.parent.mkdir(parents=True, exist_ok=True)
    args.merge_into.write_text(json.dumps(tasks, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"merged n={len(tasks)} (added/updated this pass ~{added}) -> {args.merge_into}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
