#!/usr/bin/env python3
"""Hard-seed IR ablation on HKCA09 / real headroom FSF (C2 evidence).

One-shot Conf saturates on these public SOFL reconstructions; freeze an
ordering/relop seed bug, then one T=0 repair under test_only vs semantic_ir.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_HS_PATH = ROOT / "paper" / "hsp-agile" / "scripts" / "strengthening" / "run_ir_hard_seed_ablation.py"
_spec = importlib.util.spec_from_file_location("run_ir_hard_seed_ablation", _HS_PATH)
hs = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(hs)

CORE_VARIANTS = [
    ("test_only", "A"),
    ("test_expected", "B"),
    ("semantic_ir", "FULL"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--tasks",
        type=Path,
        default=ROOT / "benchmarks" / "hkca09_sofl_fsf.json",
    )
    ap.add_argument(
        "--task-ids",
        type=Path,
        default=ROOT / "benchmarks" / "hkca09_sofl_fsf.json",
        help="JSON list of tasks or taskId strings",
    )
    ap.add_argument(
        "--seed-types",
        nargs="+",
        default=["invert_order", "wrong_relop", "swap_bodies"],
    )
    ap.add_argument("--model", default="ecnu-plus")
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "artifacts" / "run_hkca09_hard_seed_e6_v1",
    )
    ap.add_argument("--parallelism", type=int, default=4)
    ap.add_argument("--task-limit", type=int, default=None)
    args = ap.parse_args()

    hs.VARIANTS = CORE_VARIANTS

    raw = json.loads(args.task_ids.read_text(encoding="utf-8"))
    if isinstance(raw, list) and raw and isinstance(raw[0], dict):
        task_ids = [t["taskId"] for t in raw]
    elif isinstance(raw, list):
        task_ids = list(raw)
    else:
        raise SystemExit("bad task-ids")
    if args.task_limit:
        task_ids = task_ids[: args.task_limit]

    tasks = {t["taskId"]: t for t in json.loads(args.tasks.read_text(encoding="utf-8"))}
    args.out_dir.mkdir(parents=True, exist_ok=True)
    results_path = args.out_dir / "results.jsonl"

    seeds = hs.build_seeds(tasks, task_ids, args.seed_types)
    (args.out_dir / "seed_meta.json").write_text(
        json.dumps(
            [
                {
                    "task_id": s["task_id"],
                    "seed_type": s["seed_type"],
                    "frozen_conf": s["frozen_conf"],
                    "n_records": len(s["records"]),
                }
                for s in seeds
            ],
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[hkca09-hard-seed] seeds={len(seeds)} types={args.seed_types} model={args.model}")

    done = set()
    if results_path.exists():
        for line in results_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                done.add((r["task_id"], r.get("seed_type"), r["feedback_variant"], r.get("model")))

    pending = []
    log_dir = str(args.out_dir / "llm_logs")
    for s in seeds:
        for variant, label in CORE_VARIANTS:
            key = (s["task_id"], s["seed_type"], variant, args.model)
            if key in done:
                continue
            pending.append(
                {
                    "task_id": s["task_id"],
                    "task": s["task"],
                    "seed_type": s["seed_type"],
                    "frozen_code": s["frozen_code"],
                    "frozen_conf": s["frozen_conf"],
                    "records": s["records"],
                    "variant": variant,
                    "label": label,
                    "model": args.model,
                    "log_dir": log_dir,
                }
            )
    print(f"[hkca09-hard-seed] pending={len(pending)}")

    with results_path.open("a", encoding="utf-8") as w:
        if args.parallelism <= 1:
            for p in pending:
                rec = hs._job_worker(p)
                w.write(json.dumps(rec, ensure_ascii=False) + "\n")
                w.flush()
                print(
                    f"[{rec.get('seed_type')}] {rec['task_id']} {rec['feedback_variant']} "
                    f"conf={rec.get('formal_conformance')}"
                )
        else:
            # Thread pool: hs module is loaded via importlib (not process-picklable).
            with ThreadPoolExecutor(max_workers=args.parallelism) as ex:
                futs = {ex.submit(hs._job_worker, p): p for p in pending}
                for i, fut in enumerate(as_completed(futs), 1):
                    rec = fut.result()
                    w.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    w.flush()
                    if i % 5 == 0 or i == len(pending):
                        print(
                            f"[progress] {i}/{len(pending)} "
                            f"last={rec['task_id']}|{rec['feedback_variant']} "
                            f"conf={rec.get('formal_conformance')}"
                        )

    summary = hs.summarize(results_path)
    (args.out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
