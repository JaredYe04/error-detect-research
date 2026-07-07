"""Real-derived benchmark runner (Track A / CCF-B upgrade).

Runs the SgDP pipeline on tasks derived from HumanEval and MBPP that have been
converted to FSF format.  Benchmark files:
    benchmarks/real_derived/humaneval_fsf.json  (20 tasks)
    benchmarks/real_derived/mbpp_fsf.json       (20 tasks)

Usage:
    python -u experiments/run_real_derived.py
    python -u experiments/run_real_derived.py --run-name run_real_derived_v1
    python -u experiments/run_real_derived.py --modes B1 M --parallelism 4
    python -u experiments/run_real_derived.py --dry-run

Progress: artifacts/<run-name>/progress.json
Results:  artifacts/<run-name>/results_<source>.jsonl  (incremental append)
Summary:  artifacts/<run-name>/real_derived_summary.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.benchmarks.reference_gen import generate_reference_code
from src.pipeline.runner import ErrorPreventionPipeline, config_for_mode

ARTIFACTS = ROOT / "artifacts"
BENCHMARKS = ROOT / "benchmarks" / "real_derived"

BENCHMARK_FILES = {
    "humaneval": BENCHMARKS / "humaneval_fsf.json",
    "mbpp": BENCHMARKS / "mbpp_fsf.json",
}

DEFAULT_MODES = ["B1", "B2", "M"]
DEFAULT_RUN_NAME = "run_real_derived_v1"


# ---------------------------------------------------------------------------
# Progress / JSONL helpers (matches run_generalisation.py convention)
# ---------------------------------------------------------------------------

def _write_progress(
    path: Path,
    *,
    status: str,
    completed: int,
    total: int,
    started_at: float,
    last_message: str = "",
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
        "elapsed_sec": round(elapsed, 1),
        "rate_per_sec": round(rate, 4),
        "eta_sec": round(eta_sec, 1) if eta_sec is not None else None,
        "last_message": last_message,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
        f.flush()


def _load_completed_keys(path: Path) -> set[tuple]:
    if not path.exists():
        return set()
    keys: set[tuple] = set()
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    r = json.loads(line)
                    keys.add((r.get("task_id"), r.get("mode")))
                except json.JSONDecodeError:
                    pass
    return keys


# ---------------------------------------------------------------------------
# Benchmark loading
# ---------------------------------------------------------------------------

def _load_source_tasks(source: str) -> list[dict]:
    path = BENCHMARK_FILES[source]
    if not path.exists():
        raise FileNotFoundError(
            f"Benchmark file not found: {path}\n"
            "Run: python scripts/convert_humaneval_mbpp.py"
        )
    tasks = json.loads(path.read_text(encoding="utf-8"))
    # Ensure each task has referenceCode; generate from FSF if absent
    for task in tasks:
        if not task.get("referenceCode"):
            try:
                task["referenceCode"] = generate_reference_code(task)
            except Exception:
                task["referenceCode"] = ""
    return tasks


# ---------------------------------------------------------------------------
# Single-job runner (used for both serial and parallel execution)
# ---------------------------------------------------------------------------

def _run_one_job(
    job: dict,
    *,
    run_dir_str: str,
) -> tuple[str, dict, str]:
    """Execute one (task, mode) pair; returns (task_key, record, message)."""
    task = job["task"]
    mode = job["mode"]
    source = job["source"]
    task_key = job["task_key"]
    ref_code = task.get("referenceCode", "")

    cfg = config_for_mode(mode)
    try:
        from src.llm.ecnu_client import ECNUClient
        llm = ECNUClient(log_dir=Path(run_dir_str) / "llm_logs" / f"{source}-{mode}")
    except Exception:
        llm = None

    pipeline = ErrorPreventionPipeline(config=cfg, llm=llm)
    try:
        result = pipeline.run_task(task, reference_code=ref_code)
        rec = asdict(result) if hasattr(result, "__dataclass_fields__") else result.__dict__.copy()
    except Exception as exc:
        rec = {
            "task_id": task["taskId"],
            "mode": mode,
            "error": str(exc),
            "formal_conformance": 0.0,
            "success": False,
        }
    rec["source"] = source
    msg = (
        f"[RD] {source} {task['taskId']} {mode} "
        f"conf={rec.get('formal_conformance', 0.0):.3f} "
        f"success={rec.get('success', False)}"
    )
    return task_key, rec, msg


# ---------------------------------------------------------------------------
# Summary aggregation
# ---------------------------------------------------------------------------

def aggregate_summary(run_dir: Path, modes: list[str]) -> dict:
    summary: dict = {}
    for results_path in sorted(run_dir.glob("results_*.jsonl")):
        source = results_path.stem.replace("results_", "")
        rows = [
            json.loads(line)
            for line in results_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        summary[source] = {}
        for mode in modes:
            mode_results = [r for r in rows if r.get("mode") == mode]
            if mode_results:
                mean_conf = sum(r.get("formal_conformance", 0.0) for r in mode_results) / len(mode_results)
                strict_count = sum(1 for r in mode_results if r.get("success", False))
                summary[source][mode] = {
                    "n": len(mode_results),
                    "mean_conf": round(mean_conf, 4),
                    "strict_success_rate": round(strict_count / len(mode_results), 4),
                }
    return summary


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(line_buffering=True)
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Real-derived benchmark runner (HumanEval/MBPP → FSF)")
    parser.add_argument("--modes", nargs="+", default=DEFAULT_MODES,
                        help="Pipeline modes to evaluate (default: B1 B2 M)")
    parser.add_argument("--sources", nargs="+", choices=list(BENCHMARK_FILES.keys()), default=list(BENCHMARK_FILES.keys()),
                        help="Which benchmark sources to run (default: humaneval mbpp)")
    parser.add_argument("--run-name", default=DEFAULT_RUN_NAME,
                        help="Output subdirectory under artifacts/")
    parser.add_argument("--task-limit", type=int, default=None,
                        help="Cap tasks per source (useful for smoke tests)")
    parser.add_argument("--parallelism", type=int, default=10,
                        help="Number of parallel worker processes")
    parser.add_argument("--dry-run", action="store_true",
                        help="List all tasks that would be run without executing them")
    args = parser.parse_args()

    run_dir = ARTIFACTS / args.run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    progress_path = run_dir / "progress.json"
    started_at = time.time()

    # Load all tasks
    source_tasks: dict[str, list[dict]] = {}
    for source in args.sources:
        tasks = _load_source_tasks(source)
        if args.task_limit:
            tasks = tasks[: args.task_limit]
        source_tasks[source] = tasks

    # Build job list
    all_jobs: list[dict] = []
    for source, tasks in source_tasks.items():
        for task in tasks:
            for mode in args.modes:
                task_key = f"{source}|{task['taskId']}|{mode}"
                all_jobs.append({"source": source, "task": task, "mode": mode, "task_key": task_key})

    # --dry-run: list tasks and exit
    if args.dry_run:
        total_tasks = sum(len(t) for t in source_tasks.values())
        print(f"[dry-run] {total_tasks} tasks × {len(args.modes)} modes = {len(all_jobs)} jobs")
        print(f"[dry-run] Output directory: {run_dir}")
        for source, tasks in source_tasks.items():
            print(f"\n  {source} ({len(tasks)} tasks):")
            for task in tasks:
                print(f"    {task['taskId']}")
        return

    # Filter already-completed jobs
    done_keys: set[tuple] = set()
    for source in args.sources:
        results_path = run_dir / f"results_{source}.jsonl"
        for k in _load_completed_keys(results_path):
            done_keys.add(k)

    pending_jobs = [
        j for j in all_jobs
        if (j["task"]["taskId"], j["mode"]) not in done_keys
    ]
    total = len(all_jobs)
    completed = total - len(pending_jobs)

    print(f"[RD] Run: {run_dir}")
    print(f"[RD] Sources: {list(source_tasks.keys())}")
    print(f"[RD] Modes: {args.modes}")
    print(f"[RD] Total jobs: {total}, already done: {completed}, pending: {len(pending_jobs)}")
    _write_progress(progress_path, status="running", completed=completed,
                    total=total, started_at=started_at, last_message="starting")

    def _write_record(rec: dict) -> None:
        source = rec.get("source", "unknown")
        _append_jsonl(run_dir / f"results_{source}.jsonl", rec)

    if args.parallelism <= 1:
        for job in pending_jobs:
            task_key, rec, msg = _run_one_job(job, run_dir_str=str(run_dir))
            _write_record(rec)
            done_keys.add((rec.get("task_id"), rec.get("mode")))
            completed = len(done_keys)
            print(msg)
            _write_progress(progress_path, status="running", completed=completed,
                            total=total, started_at=started_at, last_message=msg)
            eta = json.loads(progress_path.read_text(encoding="utf-8")).get("eta_sec")
            eta_str = "?" if eta is None else f"{eta / 60:.1f}m"
            print(f"[progress] {completed}/{total} ({completed / total * 100:.1f}%) ETA={eta_str}")
    else:
        max_workers = max(1, args.parallelism)
        with ProcessPoolExecutor(max_workers=max_workers) as ex:
            futures = [
                ex.submit(_run_one_job, job, run_dir_str=str(run_dir))
                for job in pending_jobs
            ]
            for fut in as_completed(futures):
                task_key, rec, msg = fut.result()
                _write_record(rec)
                done_keys.add((rec.get("task_id"), rec.get("mode")))
                completed = len(done_keys)
                print(msg)
                _write_progress(progress_path, status="running", completed=completed,
                                total=total, started_at=started_at, last_message=msg)
                eta = json.loads(progress_path.read_text(encoding="utf-8")).get("eta_sec")
                eta_str = "?" if eta is None else f"{eta / 60:.1f}m"
                print(f"[progress] {completed}/{total} ({completed / total * 100:.1f}%) ETA={eta_str}")

    summary = aggregate_summary(run_dir, args.modes)
    summary_path = run_dir / "real_derived_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_progress(progress_path, status="completed", completed=len(done_keys),
                    total=total, started_at=started_at, last_message="completed")

    print(f"\n[RD] Summary → {summary_path}")
    print("\n=== Real-Derived Results ===")
    for source, mode_data in summary.items():
        print(f"\n  {source}:")
        for mode, stats in mode_data.items():
            print(
                f"    {mode}: conf={stats.get('mean_conf', 0):.4f} "
                f"strict={stats.get('strict_success_rate', 0):.4f} "
                f"n={stats.get('n', 0)}"
            )


if __name__ == "__main__":
    main()
