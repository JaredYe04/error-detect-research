"""Export + validate real_priority_micro_v1, then (optionally) run equal-K eval."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.benchmarks.real_priority_micro import export_and_validate  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target-n", type=int, default=30)
    ap.add_argument("--run-eval", action="store_true")
    ap.add_argument("--model", default="ecnu-plus")
    ap.add_argument("--parallelism", type=int, default=4)
    ap.add_argument("--run-name", default="run_real_priority_micro_v1")
    args = ap.parse_args()

    summary = export_and_validate(target_n=args.target_n)
    print(json.dumps({k: v for k, v in summary.items() if k != "failures"}, indent=2))
    if summary["failures"]:
        print("FAILURES:", json.dumps(summary["failures"], indent=2))

    if not args.run_eval:
        return

    bench = Path(summary["path"])
    cmd = [
        sys.executable,
        "-u",
        str(ROOT / "experiments" / "run_all.py"),
        "--modes",
        "B1",
        "B2",
        "M_eq",
        "--repeats",
        "1",
        "--benchmark-path",
        str(bench),
        "--run-name",
        args.run_name,
        "--parallelism",
        str(args.parallelism),
        "--force-max-attempts",
        "3",
        "--model",
        args.model,
        "--seed",
        "42",
    ]
    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd, cwd=str(ROOT))


if __name__ == "__main__":
    main()
