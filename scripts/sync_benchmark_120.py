#!/usr/bin/env python3
"""Regenerate 120-task hard benchmark and sync to canonical benchmark paths."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    build = ROOT / "scripts" / "build_benchmark.py"
    cmd = [
        sys.executable,
        str(build),
        "--hard-size",
        "180",
        "--hard-limit",
        "120",
        "--annotate",
        "--annotated-path",
        str(ROOT / "benchmarks" / "hard_tasks_annotated.json"),
    ]
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=str(ROOT))

    annotated = ROOT / "benchmarks" / "hard_tasks_annotated.json"
    tasks = json.loads(annotated.read_text(encoding="utf-8"))
    n = len(tasks)
    print(f"Annotated benchmark: {n} tasks")

    for dest_name in ("hard_tasks.json", "tasks.json"):
        dest = ROOT / "benchmarks" / dest_name
        shutil.copy2(annotated, dest)
        print(f"Synced -> {dest}")

    if n != 120:
        print(f"WARNING: expected 120 tasks, got {n}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
