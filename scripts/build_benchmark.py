#!/usr/bin/env python3
"""Build benchmark tasks from Agile-SOFL examples."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.benchmarks import HARD_BENCHMARK_PATH, save_benchmark, save_hard_benchmark


def main() -> None:
    parser = argparse.ArgumentParser(description="Build base + hard benchmark suites")
    parser.add_argument("--hard-only", action="store_true")
    parser.add_argument("--hard-size", type=int, default=160)
    parser.add_argument("--hard-scenarios", type=int, default=8)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    hard_path = save_hard_benchmark(
        path=HARD_BENCHMARK_PATH,
        n_tasks=args.hard_size,
        scenarios_per_task=args.hard_scenarios,
        seed=args.seed,
    )
    print(f"Hard benchmark saved to {hard_path}")
    if args.hard_only:
        return
    path = save_benchmark(include_hard=True)
    print(f"Combined benchmark saved to {path}")


if __name__ == "__main__":
    main()
