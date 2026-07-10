#!/usr/bin/env python3
"""E14: length-matched feedback variant sweep (fairness vs E6).

Runs mode M with feedback variants:
  test_only, test_expected, semantic_ir, execution_trace_matched

Usage:
  python experiments/run_e14_sweep.py --run-name run_e14_sweep_v1 --task-limit 10
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from experiments.run_all import run_experiment  # noqa: E402
from src.benchmarks import load_benchmark  # noqa: E402
from src.formal.checker import run_formal_check  # noqa: E402
from src.llm.ecnu_client import ECNUClient  # noqa: E402
from src.pipeline.runner import ErrorPreventionPipeline, config_for_mode  # noqa: E402

VARIANTS = ["test_only", "test_expected", "semantic_ir", "execution_trace_matched"]


def _run_variant(
    variant: str,
    tasks: list[dict],
    *,
    run_dir: Path,
    model: str | None,
) -> list[dict]:
    records: list[dict] = []
    for i, task in enumerate(tasks, start=1):
        cfg = config_for_mode("M")
        cfg.feedback_variant = variant
        if model:
            cfg.model = model
        llm = ECNUClient(log_dir=run_dir / "llm_logs" / variant / task["taskId"])
        pipeline = ErrorPreventionPipeline(config=cfg, llm=llm)
        result = pipeline.run_task(task)
        strict = run_formal_check(result.code, task, max_cases=cfg.strict_eval_cases)
        records.append(
            {
                **asdict(result),
                "feedback_variant": variant,
                "strict_formal_passed": strict.passed,
                "strict_formal_conformance": strict.conformance_rate,
                "timestamp": time.time(),
            }
        )
        if i % 10 == 0 or i == len(tasks):
            print(f"[E14] {variant} {i}/{len(tasks)}", flush=True)
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-name", default="run_e14_sweep_v1")
    parser.add_argument("--task-limit", type=int, default=None)
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--parallelism", type=int, default=1, help="Reserved; E14 runs sequentially per variant")
    args = parser.parse_args()

    tasks = load_benchmark()
    if args.task_limit:
        tasks = tasks[: args.task_limit]

    run_dir = ROOT / "artifacts" / args.run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    out_path = run_dir / "results.jsonl"

    all_records: list[dict] = []
    for variant in VARIANTS:
        print(f"[E14] variant={variant} n={len(tasks)}")
        batch = _run_variant(variant, tasks, run_dir=run_dir, model=args.model)
        all_records.extend(batch)

    with out_path.open("w", encoding="utf-8") as f:
        for rec in all_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    summary: dict[str, float] = {}
    for variant in VARIANTS:
        sub = [r for r in all_records if r.get("feedback_variant") == variant]
        if sub:
            summary[variant] = sum(r["strict_formal_conformance"] for r in sub) / len(sub)

    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"E14 complete -> {out_path}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
