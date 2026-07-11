#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6-style feedback variants on RealSpec tasks where B1 failed (data strengthening)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--realspec-run",
        type=Path,
        default=ROOT / "artifacts" / "run_realspec_v1_b1b2m" / "results.jsonl",
    )
    ap.add_argument(
        "--benchmark",
        type=Path,
        default=ROOT / "benchmarks" / "realspec" / "realspec_v1.json",
    )
    ap.add_argument("--out-subset", type=Path, default=ROOT / "benchmarks" / "realspec_b1_fail.json")
    ap.add_argument("--run-name", default="run_realspec_e6_b1fail_v1")
    ap.add_argument("--model", default="ecnu-plus")
    ap.add_argument("--parallelism", type=int, default=4)
    ap.add_argument("--dry-build-only", action="store_true")
    args = ap.parse_args()

    rows = [json.loads(l) for l in args.realspec_run.read_text(encoding="utf-8").splitlines() if l.strip()]
    fail_ids = sorted(
        {
            r["task_id"]
            for r in rows
            if r.get("mode") == "B1" and float(r.get("formal_conformance") or 0) < 1.0 - 1e-12
        }
    )
    tasks = json.loads(args.benchmark.read_text(encoding="utf-8"))
    subset = [t for t in tasks if t.get("taskId") in set(fail_ids)]
    args.out_subset.write_text(json.dumps(subset, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"RealSpec B1-fail subset: {len(subset)} -> {args.out_subset}")

    if args.dry_build_only:
        return

    # Reuse sweep runner with task-subset of IDs
    id_list = ROOT / "benchmarks" / "realspec_b1_fail_ids.json"
    id_list.write_text(json.dumps(fail_ids, indent=2), encoding="utf-8")

    import subprocess

    cmd = [
        sys.executable,
        str(ROOT / "experiments" / "run_sweep.py"),
        "--experiment",
        "feedback_variants",
        "--run-name",
        args.run_name,
        "--task-subset",
        str(id_list),
        "--parallelism",
        str(args.parallelism),
        "--model",
        args.model,
    ]
    # run_sweep loads hard_tasks by default — need to patch: write a combined approach
    # Instead call run_feedback directly via a thin wrapper below.
    print("NOTE: launching via dedicated runner that loads RealSpec benchmark...")
    from experiments.run_sweep import run_feedback_variant_experiment

    out = ROOT / "artifacts" / args.run_name / "feedback_variants"
    run_feedback_variant_experiment(
        subset,
        out,
        parallelism=args.parallelism,
        model=args.model,
    )
    print(f"Done -> {out}")


if __name__ == "__main__":
    main()
