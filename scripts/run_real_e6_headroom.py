#!/usr/bin/env python3
"""E6 feedback ablation on real/headroom FSF (serves C2, not aggregate Conf ties).

Runs test_only / test_expected / semantic_ir under mode M, equal K=3, on a
custom benchmark JSON (default: real_headroom_e6.json).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--benchmark",
        type=Path,
        default=ROOT / "benchmarks" / "real_headroom_e6.json",
    )
    ap.add_argument("--run-name", default="run_real_e6_headroom_v1")
    ap.add_argument("--model", default="ecnu-plus")
    ap.add_argument("--parallelism", type=int, default=4)
    ap.add_argument(
        "--variants",
        nargs="+",
        default=["test_only", "test_expected", "semantic_ir"],
    )
    args = ap.parse_args()

    tasks = json.loads(args.benchmark.read_text(encoding="utf-8"))
    print(f"E6 real/headroom: n={len(tasks)} model={args.model} variants={args.variants}")

    from experiments.run_sweep import run_feedback_variant_experiment

    label = {"test_only": "A", "test_expected": "B", "semantic_ir": "C"}
    variants = [(v, label.get(v, v[:1].upper())) for v in args.variants]
    out = ROOT / "artifacts" / args.run_name / "feedback_variants"
    run_feedback_variant_experiment(
        tasks,
        out,
        parallelism=args.parallelism,
        model=args.model,
        variants=variants,
    )
    print(f"Done -> {out}")


if __name__ == "__main__":
    main()
