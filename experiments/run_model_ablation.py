"""Model ablation runner — evaluate B1 (one-shot) and M (full pipeline) on a given model.

Usage:
    python experiments/run_model_ablation.py --model ecnu-plus
    python experiments/run_model_ablation.py --model ecnu-thinking --tasks 30
    python experiments/run_model_ablation.py --model gpt-4o --modes B1 M --tasks 120

Output:
    artifacts/run_model_ablation_<model_name>/results.jsonl
    artifacts/run_model_ablation_<model_name>/meta.json
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.benchmarks import load_benchmark
from src.formal.checker import run_formal_check
from src.pipeline.runner import ErrorPreventionPipeline, config_for_mode

ARTIFACTS = ROOT / "artifacts"
DEFAULT_MODES = ["B1", "M"]
DEFAULT_TASKS = 120


def _run_ablation_job(
    job: dict,
    *,
    run_dir_str: str,
    model: str,
) -> tuple[str, dict, str]:
    """Single ablation job: one task × one mode with the specified model."""
    from src.llm.ecnu_client import ECNUClient

    task = job["task"]
    mode = job["mode"]
    task_id = task["taskId"]
    job_key = job["job_key"]
    ref_code = task.get("referenceCode", "")

    cfg = copy.deepcopy(config_for_mode(mode))
    cfg.model = model

    safe_id = task_id.replace(".", "_").replace("/", "_")
    safe_model = model.replace("/", "_").replace(":", "_")
    llm = ECNUClient(
        log_dir=Path(run_dir_str) / "llm_logs" / f"proc-{safe_id}-{mode}-{safe_model}"
    )
    pipeline = ErrorPreventionPipeline(config=cfg, llm=llm)

    try:
        result = pipeline.run_task(task, reference_code=ref_code)
        rec = asdict(result) if hasattr(result, "__dataclass_fields__") else result.__dict__.copy()
        strict_check = run_formal_check(result.code, task, max_cases=cfg.strict_eval_cases)
        rec["strict_formal_passed"] = strict_check.passed
        rec["strict_formal_conformance"] = strict_check.conformance_rate
        rec["strict_failures"] = len(strict_check.counterexamples)
    except Exception as e:  # noqa: BLE001
        rec = {
            "task_id": task_id,
            "mode": mode,
            "error": str(e),
            "formal_conformance": 0.0,
            "strict_formal_passed": False,
            "strict_formal_conformance": 0.0,
            "strict_failures": 0,
        }

    rec["model"] = model
    rec["timestamp"] = time.time()
    msg = (
        f"[ablation] model={model} mode={mode} task={task_id} "
        f"conf={rec.get('formal_conformance', 0):.3f} "
        f"strict={rec.get('strict_formal_conformance', 0):.3f}"
    )
    return job_key, rec, msg


def run_model_ablation(
    *,
    model: str,
    modes: list[str],
    task_limit: int,
    output_dir: Path,
    run_name: str | None = None,
    parallelism: int = 1,
) -> Path:
    tasks = load_benchmark()
    if task_limit:
        tasks = tasks[:task_limit]

    safe_model = model.replace("/", "_").replace(":", "_").replace(" ", "_")
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = output_dir / (run_name or f"run_model_ablation_{safe_model}_{ts}")
    run_dir.mkdir(parents=True, exist_ok=True)

    out_path = run_dir / "results.jsonl"
    done_keys: set[str] = set()
    if out_path.exists():
        for line in out_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            done_keys.add(f"{row.get('mode')}|{row.get('task_id')}")

    all_jobs = [
        {
            "mode": mode,
            "task": task,
            "job_key": f"{mode}|{task['taskId']}",
        }
        for mode in modes
        for task in tasks
    ]
    pending = [j for j in all_jobs if j["job_key"] not in done_keys]
    total = len(all_jobs)
    completed = total - len(pending)

    print(f"[ablation] model={model} modes={modes} tasks={len(tasks)}")
    print(f"[ablation] total={total} pending={len(pending)} already_done={completed}")
    print(f"[ablation] output={run_dir}")

    started_at = time.time()
    records: list[dict] = []

    with out_path.open("a", encoding="utf-8") as writer:
        if parallelism <= 1:
            for job in pending:
                _, record, msg = _run_ablation_job(
                    job,
                    run_dir_str=str(run_dir),
                    model=model,
                )
                records.append(record)
                writer.write(json.dumps(record, ensure_ascii=False) + "\n")
                writer.flush()
                done_keys.add(job["job_key"])
                pct = len(done_keys) / total * 100
                elapsed = time.time() - started_at
                rate = (len(records) / elapsed) if elapsed > 0 else 0
                eta = ((total - len(done_keys)) / rate) if rate > 0 else None
                eta_str = "?" if eta is None else f"{eta / 60:.1f}m"
                print(f"{msg}")
                print(f"[progress] {len(done_keys)}/{total} ({pct:.1f}%) ETA={eta_str}")
        else:
            with ProcessPoolExecutor(max_workers=max(1, parallelism)) as ex:
                futures = [
                    ex.submit(_run_ablation_job, job, run_dir_str=str(run_dir), model=model)
                    for job in pending
                ]
                for fut in as_completed(futures):
                    _, record, msg = fut.result()
                    records.append(record)
                    writer.write(json.dumps(record, ensure_ascii=False) + "\n")
                    writer.flush()
                    done_keys.add(f"{record.get('mode')}|{record.get('task_id')}")
                    pct = len(done_keys) / total * 100
                    print(f"{msg}")
                    print(f"[progress] {len(done_keys)}/{total} ({pct:.1f}%)")

    elapsed_total = time.time() - started_at
    meta = {
        "model": model,
        "modes": modes,
        "tasks": len(tasks),
        "total_jobs": total,
        "completed_jobs": len(done_keys),
        "parallelism": parallelism,
        "elapsed_sec": round(elapsed_total, 1),
        "run_dir": str(run_dir),
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"\n[ablation] Done. Results: {out_path}")
    print(f"[ablation] Meta: {run_dir / 'meta.json'}")
    return run_dir


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Model ablation: run B1 and M with a specified model endpoint"
    )
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Model identifier to use (e.g. ecnu-plus, ecnu-thinking, gpt-4o)",
    )
    parser.add_argument(
        "--modes",
        nargs="+",
        default=DEFAULT_MODES,
        help=f"Modes to run (default: {DEFAULT_MODES})",
    )
    parser.add_argument(
        "--tasks",
        type=int,
        default=DEFAULT_TASKS,
        help=f"Number of tasks to run (default: {DEFAULT_TASKS})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ARTIFACTS,
        help="Output root directory (default: artifacts/)",
    )
    parser.add_argument(
        "--run-name",
        type=str,
        default=None,
        help="Override run directory name (default: run_model_ablation_<model>_<ts>)",
    )
    parser.add_argument(
        "--parallelism",
        type=int,
        default=1,
        help="Number of parallel workers (default: 1)",
    )
    args = parser.parse_args()

    run_dir = run_model_ablation(
        model=args.model,
        modes=args.modes,
        task_limit=args.tasks,
        output_dir=args.output,
        run_name=args.run_name,
        parallelism=args.parallelism,
    )
    print(f"Results written to {run_dir}")


if __name__ == "__main__":
    main()
