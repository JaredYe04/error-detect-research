#!/usr/bin/env python3
"""Re-validate / merge GitHub harvest tasks into benchmarks + RealSpec."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.benchmarks.complexity import annotate_tasks_complexity
from src.harvest.to_fsf import validate_task


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-run", type=str, default=None, help="artifacts/github_harvest/<run>")
    ap.add_argument(
        "--tasks",
        type=Path,
        default=ROOT / "benchmarks" / "github_harvest_v1.json",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "benchmarks" / "github_harvest_v1.json",
    )
    ap.add_argument("--rebuild-realspec", action="store_true")
    args = ap.parse_args()

    if args.from_run:
        src = ROOT / "artifacts" / "github_harvest" / args.from_run / "05_converted_tasks.json"
        if not src.exists():
            print(f"missing {src}", file=sys.stderr)
            return 2
        tasks = json.loads(src.read_text(encoding="utf-8"))
    else:
        if not args.tasks.exists():
            print(f"missing {args.tasks}", file=sys.stderr)
            return 2
        tasks = json.loads(args.tasks.read_text(encoding="utf-8"))

    kept = []
    rejected = []
    for t in tasks:
        st = validate_task(t)
        if st.get("ok"):
            kept.append(t)
        else:
            rejected.append({"taskId": t.get("taskId"), "status": st})

    annotate_tasks_complexity(kept)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(kept, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    rej_path = args.out.with_name(args.out.stem + "_rejected.json")
    rej_path.write_text(json.dumps(rejected, indent=2), encoding="utf-8")
    print(f"kept={len(kept)} rejected={len(rejected)} -> {args.out}")

    if args.rebuild_realspec:
        from paper.hsp_agile.scripts.strengthening.build_realspec_corpus import main as rebuild

        # call via subprocess-equivalent import path may fail; use runpy
        import runpy

        runpy.run_path(
            str(ROOT / "paper" / "hsp-agile" / "scripts" / "strengthening" / "build_realspec_corpus.py"),
            run_name="__main__",
        )
    return 0 if kept else 1


if __name__ == "__main__":
    raise SystemExit(main())
