"""Experiment configuration and batch runner."""

from __future__ import annotations

import hashlib
import argparse
import copy
import json
import math
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
from src.llm.ecnu_client import ECNUClient
from src.mutation.injectors import apply_mutant_to_task, generate_mutants
from src.pipeline.runner import ErrorPreventionPipeline, config_for_mode

MODES = ["B0", "B1", "B2", "B3", "B4", "B4M", "B5", "B6", "M", "M_lite", "M_adv", "A1", "A2", "A3"]
SENSITIVITY_GRID = [
    {"temperature": 0.0, "max_attempts": 1},
    {"temperature": 0.2, "max_attempts": 3},
    {"temperature": 0.5, "max_attempts": 3},
    {"temperature": 0.8, "max_attempts": 5},
]


def _write_progress(
    path: Path,
    *,
    status: str,
    completed: int,
    total: int,
    started_at: float,
    running_jobs: int = 0,
    last_message: str | None = None,
) -> None:
    elapsed = max(0.0, time.time() - started_at)
    rate = (completed / elapsed) if elapsed > 0 else 0.0
    remaining = max(total - completed, 0)
    eta_sec = (remaining / rate) if rate > 1e-9 else None
    payload = {
        "status": status,
        "completed": completed,
        "total": total,
        "percent": (completed / total * 100.0) if total else 100.0,
        "elapsed_sec": elapsed,
        "rate_per_sec": rate,
        "eta_sec": eta_sec,
        "running_jobs": running_jobs,
        "last_message": last_message or "",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _build_task_grid(
    *,
    modes: list[str],
    repeats: int,
    tasks: list[dict],
    grid: list[dict],
) -> list[dict]:
    items: list[dict] = []
    for mode in modes:
        for grid_idx, params in enumerate(grid):
            for rep in range(repeats):
                for task in tasks:
                    items.append(
                        {
                            "mode": mode,
                            "grid_idx": grid_idx,
                            "params": params,
                            "rep": rep,
                            "task": task,
                            "task_key": f"{mode}|{rep}|{grid_idx}|{task['taskId']}",
                        }
                    )
    return items


def _run_one_job(
    job: dict,
    *,
    run_dir_str: str,
    use_llm: bool,
    mutation_eval: bool,
    seed: int,
    model: str | None = None,
) -> tuple[str, dict, str]:
    mode = job["mode"]
    rep = job["rep"]
    grid_idx = job["grid_idx"]
    params = job["params"]
    task = job["task"]
    task_key = job["task_key"]

    cfg = config_for_mode(mode)
    cfg.temperature = params["temperature"]
    cfg.max_attempts = params["max_attempts"]
    if model:
        cfg.model = model
    cfg = copy.deepcopy(cfg)
    llm = ECNUClient(log_dir=Path(run_dir_str) / "llm_logs" / f"proc-{mode}-{rep}-{grid_idx}") if use_llm else None
    pipeline = ErrorPreventionPipeline(config=cfg, llm=llm)

    ref = task.get("referenceCode")
    result = pipeline.run_task(task, reference_code=ref)
    strict_check = run_formal_check(result.code, task, max_cases=cfg.strict_eval_cases)

    mutant_kill = 0
    mutant_total = 0
    if mutation_eval and ref:
        mutants = generate_mutants(task, ref, seed=seed + rep)
        for mut in mutants:
            mutant_total += 1
            if mut.layer == "spec":
                mut_task = apply_mutant_to_task(task, mut)
                check = run_formal_check(result.code, mut_task)
                if not check.passed:
                    mutant_kill += 1
            else:
                check = run_formal_check(mut.payload["code"], task)
                if not check.passed:
                    mutant_kill += 1

    record = {
        **asdict(result),
        "strict_formal_passed": strict_check.passed,
        "strict_formal_conformance": strict_check.conformance_rate,
        "strict_failures": len(strict_check.counterexamples),
        "repeat": rep,
        "seed": seed + rep,
        "grid_idx": grid_idx,
        "temperature": params["temperature"],
        "max_attempts": params["max_attempts"],
        "mutation_kill_rate": mutant_kill / mutant_total if mutant_total else 0.0,
        "mutation_killed": mutant_kill,
        "mutation_total": mutant_total,
        "timestamp": time.time(),
    }
    msg = (
        f"[{mode}] rep={rep} task={task['taskId']} "
        f"success={result.success} formal={result.formal_conformance:.2f} "
        f"strict={strict_check.conformance_rate:.2f} "
        f"mut_kill={record['mutation_kill_rate']:.2f}"
    )
    return task_key, record, msg


def run_experiment(
    *,
    modes: list[str],
    repeats: int,
    output_dir: Path,
    use_llm: bool = True,
    task_limit: int | None = None,
    sensitivity: bool = False,
    mutation_eval: bool = True,
    seed: int = 42,
    benchmark_path: Path | None = None,
    task_subset_path: Path | None = None,
    run_name: str | None = None,
    parallelism: int = 1,
    model: str | None = None,
) -> Path:
    tasks = load_benchmark(benchmark_path, include_hard=False) if benchmark_path else load_benchmark()
    if task_subset_path:
        subset_raw = json.loads(task_subset_path.read_text(encoding="utf-8"))
        if isinstance(subset_raw, list) and subset_raw and isinstance(subset_raw[0], dict):
            subset_ids = {t.get("taskId") for t in subset_raw}
        elif isinstance(subset_raw, dict) and "taskIds" in subset_raw:
            subset_ids = set(subset_raw["taskIds"])
        else:
            subset_ids = set(subset_raw)
        tasks = [t for t in tasks if t.get("taskId") in subset_ids]
        order = {tid: i for i, tid in enumerate(subset_ids)}
        tasks.sort(key=lambda t: order.get(t.get("taskId"), 10**9))
    if task_limit:
        tasks = tasks[:task_limit]

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = output_dir / (run_name if run_name else f"run_{ts}")
    run_dir.mkdir(parents=True, exist_ok=True)

    llm_log_root = run_dir / "llm_logs"
    llm_log_root.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []
    out_path = run_dir / "results.jsonl"
    progress_path = run_dir / "progress.json"
    done_keys: set[str] = set()
    if out_path.exists():
        for line in out_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            done_keys.add(f"{row['mode']}|{row['repeat']}|{row['grid_idx']}|{row['task_id']}")

    grid = SENSITIVITY_GRID if sensitivity else [{"temperature": 0.2, "max_attempts": 3}]
    all_jobs = _build_task_grid(modes=modes, repeats=repeats, tasks=tasks, grid=grid)
    pending = [job for job in all_jobs if job["task_key"] not in done_keys]
    total = len(all_jobs)
    completed = total - len(pending)
    started_at = time.time()

    _write_progress(
        progress_path,
        status="running",
        completed=completed,
        total=total,
        started_at=started_at,
        running_jobs=0,
        last_message="initialized",
    )

    writer = out_path.open("a", encoding="utf-8")
    try:
        if parallelism <= 1:
            for job in pending:
                task_key, record, msg = _run_one_job(
                    job,
                    run_dir_str=str(run_dir),
                    use_llm=use_llm,
                    mutation_eval=mutation_eval,
                    seed=seed,
                    model=model,
                )
                records.append(record)
                writer.write(json.dumps(record, ensure_ascii=False) + "\n")
                writer.flush()
                done_keys.add(task_key)
                completed_local = len(done_keys)
                print(msg)
                _write_progress(
                    progress_path,
                    status="running",
                    completed=completed_local,
                    total=total,
                    started_at=started_at,
                    running_jobs=0,
                    last_message=msg,
                )
                eta = json.loads(progress_path.read_text(encoding="utf-8")).get("eta_sec")
                eta_str = "?" if eta is None else f"{eta/60:.1f}m"
                print(f"[progress] {completed_local}/{total} ({completed_local/total*100:.2f}%) ETA={eta_str}")
        else:
            max_workers = max(1, parallelism)
            with ProcessPoolExecutor(max_workers=max_workers) as ex:
                futures = [
                    ex.submit(
                        _run_one_job,
                        job,
                        run_dir_str=str(run_dir),
                        use_llm=use_llm,
                        mutation_eval=mutation_eval,
                        seed=seed,
                        model=model,
                    )
                    for job in pending
                ]
                for fut in as_completed(futures):
                    task_key, record, msg = fut.result()
                    records.append(record)
                    writer.write(json.dumps(record, ensure_ascii=False) + "\n")
                    writer.flush()
                    done_keys.add(task_key)
                    completed_local = len(done_keys)
                    print(msg)
                    _write_progress(
                        progress_path,
                        status="running",
                        completed=completed_local,
                        total=total,
                        started_at=started_at,
                        running_jobs=max(0, len(futures) - completed_local),
                        last_message=msg,
                    )
                    eta = json.loads(progress_path.read_text(encoding="utf-8")).get("eta_sec")
                    eta_str = "?" if eta is None else f"{eta/60:.1f}m"
                    print(f"[progress] {completed_local}/{total} ({completed_local/total*100:.2f}%) ETA={eta_str}")
    finally:
        writer.close()

    task_ids = sorted(t.get("taskId") or t.get("task_id", "") for t in tasks)
    benchmark_fingerprint = hashlib.sha256(
        json.dumps(task_ids, separators=(",", ":")).encode()
    ).hexdigest()[:16]

    meta = {
        "modes": modes,
        "repeats": repeats,
        "tasks": len(tasks),
        "sensitivity": sensitivity,
        "llm_usage": {"calls": sum(int(r.get("llm_calls", 0)) for r in records)} if use_llm else {},
        "parallelism": parallelism,
        "benchmark_path": str(benchmark_path) if benchmark_path else None,
        "task_subset_path": str(task_subset_path) if task_subset_path else None,
        "benchmark_fingerprint": benchmark_fingerprint,
        "seed": seed,
        "model": model,
        "completed": len(done_keys),
        "total": total,
    }
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    _write_progress(
        progress_path,
        status="completed",
        completed=len(done_keys),
        total=total,
        started_at=started_at,
        running_jobs=0,
        last_message="completed",
    )
    return run_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Agile-SOFL error prevention experiments")
    parser.add_argument("--modes", nargs="+", default=["B0", "B1", "B2", "B3", "B4", "B5", "M", "A1", "A2", "A3"])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--task-limit", type=int, default=None)
    parser.add_argument("--benchmark-path", type=Path, default=None, help="Benchmark JSON (default: benchmarks/tasks.json)")
    parser.add_argument("--task-subset", type=Path, default=None, help="JSON list of taskIds or task objects for stratified runs")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts")
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM calls (B0 only)")
    parser.add_argument("--sensitivity", action="store_true")
    parser.add_argument("--quick", action="store_true", help="Fast smoke: B0,B1,M only, 1 repeat")
    parser.add_argument("--run-name", type=str, default=None, help="Reuse/append named run directory")
    parser.add_argument("--parallelism", type=int, default=10, help="Number of parallel workers")
    parser.add_argument("--seed", type=int, default=42, help="Base RNG seed for mutation eval and run metadata")
    parser.add_argument("--model", type=str, default=None, help="Override LLM model id (e.g. ecnu-plus, ecnu-max)")
    args = parser.parse_args()

    modes = args.modes
    repeats = args.repeats
    if args.quick:
        modes = ["B0", "B1", "M"]
        repeats = 1

    run_dir = run_experiment(
        modes=modes,
        repeats=repeats,
        output_dir=args.output,
        use_llm=not args.no_llm,
        task_limit=args.task_limit,
        benchmark_path=args.benchmark_path,
        task_subset_path=args.task_subset,
        sensitivity=args.sensitivity,
        run_name=args.run_name,
        parallelism=args.parallelism,
        seed=args.seed,
        model=args.model,
    )
    print(f"Results written to {run_dir}")


if __name__ == "__main__":
    main()
