#!/usr/bin/env python3
"""Run defect-prevention evaluation on spec mutants."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.benchmarks import load_benchmark
from src.evaluation.prevention import PreventionRecord
from src.evaluation.prevention import evaluate_prevention, save_prevention_report
from src.llm.ecnu_client import ECNUClient


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--modes", nargs="+", default=["B1", "B2", "M", "A1", "A2", "A3"])
    parser.add_argument("--task-limit", type=int, default=None)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts" / "prevention_eval")
    parser.add_argument("--run-name", type=str, default="prevention_full_v1")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    tasks = load_benchmark()
    if args.task_limit:
        tasks = tasks[: args.task_limit]
    out_dir = args.output / args.run_name
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / "prevention_eval.jsonl"

    existing: list[PreventionRecord] = []
    done_keys: set[str] = set()
    if jsonl_path.exists():
        for line in jsonl_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            rec = PreventionRecord(**row)
            existing.append(rec)
            done_keys.add(f"{rec.mode}|{rec.mutant_id}|{rec.eval_type}")

    llm = ECNUClient(log_dir=out_dir / "llm_logs")
    new_records = evaluate_prevention(tasks, args.modes, llm, seed=args.seed, done_keys=done_keys)
    all_records = existing + new_records
    path = save_prevention_report(all_records, out_dir)
    print(f"Prevention evaluation saved to {path}")


if __name__ == "__main__":
    main()
