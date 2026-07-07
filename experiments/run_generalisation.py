"""Generalisation study runner for E8.

Evaluates the SgDP framework (HSP-Agile) on three specification notations:
  1. SOFL/FSF       — 120 hard tasks (existing benchmark)
  2. Mini-StateMachine — 10 built-in tasks (structurally equivalent to FSF)
  3. Mini-Z            — 10 built-in tasks (simplified Z-notation ordered cases)

Usage:
    python -u experiments/run_generalisation.py --run-name run_generalisation_v1
    python -u experiments/run_generalisation.py --notation statemachine miniz --run-name run_gen_test
    python -u experiments/run_generalisation.py --notation statemachine --task-limit 5 --no-llm

Progress: artifacts/<run-name>/progress.json
Results:  artifacts/<run-name>/results_<notation>.jsonl (incremental append)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.adapters.miniz_adapter import load_builtin_miniz_tasks
from src.adapters.statemachine_adapter import load_builtin_statemachine_tasks
from src.benchmarks import load_benchmark
from src.pipeline.runner import ErrorPreventionPipeline, config_for_mode

ARTIFACTS = ROOT / "artifacts"


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
    keys = set()
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    r = json.loads(line)
                    keys.add((r.get("task_id"), r.get("mode")))
                except json.JSONDecodeError:
                    pass
    return keys


def _load_notation_tasks(notation: str, task_limit: int | None) -> list[dict]:
    if notation == "sofl":
        tasks = load_benchmark()
        tasks = [t for t in tasks if "HardSynthetic" in t.get("taskId", "")]
        if task_limit:
            tasks = tasks[:task_limit]
        return tasks
    elif notation == "statemachine":
        tasks = load_builtin_statemachine_tasks()
        if task_limit:
            tasks = tasks[:task_limit]
        return tasks
    elif notation == "miniz":
        tasks = load_builtin_miniz_tasks()
        if task_limit:
            tasks = tasks[:task_limit]
        return tasks
    else:
        raise ValueError(f"Unknown notation: {notation}")


def run_notation(
    notation: str,
    tasks: list[dict],
    modes: list[str],
    out_dir: Path,
    llm_client,
    progress_path: Path,
    started_at: float,
    completed_offset: int,
    total_jobs: int,
    *,
    no_llm: bool = False,
) -> tuple[list[dict], int]:
    out_dir.mkdir(parents=True, exist_ok=True)
    results_path = out_dir / f"results_{notation}.jsonl"
    done = _load_completed_keys(results_path)
    results: list[dict] = []
    completed = completed_offset

    for task in tasks:
        task_id = task["taskId"]
        ref_code = task.get("referenceCode", "")
        for mode in modes:
            if mode == "B0" or (not llm_client and mode != "B0"):
                if no_llm:
                    if (task_id, "B0") in done:
                        continue
                    from src.formal.checker import run_formal_check
                    fr = run_formal_check(ref_code, task, max_cases=16) if ref_code else None
                    rec = {
                        "task_id": task_id,
                        "mode": "B0",
                        "notation": notation,
                        "formal_conformance": fr.conformance_rate if fr else 0.0,
                        "success": fr.passed if fr else False,
                    }
                    _append_jsonl(results_path, rec)
                    results.append(rec)
                    completed += 1
                    msg = f"[E8] {task_id} B0 conf={rec['formal_conformance']:.3f}"
                    print(msg)
                    _write_progress(progress_path, status="running", completed=completed,
                                    total=total_jobs, started_at=started_at, last_message=msg)
                    break
                continue

            if (task_id, mode) in done:
                continue

            cfg = config_for_mode(mode)
            pipeline = ErrorPreventionPipeline(config=cfg, llm=llm_client)
            try:
                result = pipeline.run_task(task, reference_code=ref_code)
                rec = asdict(result) if hasattr(result, "__dataclass_fields__") else result.__dict__.copy()
            except Exception as e:  # noqa: BLE001
                rec = {
                    "task_id": task_id,
                    "mode": mode,
                    "error": str(e),
                    "formal_conformance": 0.0,
                    "success": False,
                }
            rec["notation"] = notation
            _append_jsonl(results_path, rec)
            results.append(rec)
            completed += 1
            msg = f"[E8] {notation} {task_id} {mode} conf={rec.get('formal_conformance', 0):.3f}"
            print(msg)
            eta = json.loads(progress_path.read_text(encoding="utf-8")).get("eta_sec") if progress_path.exists() else None
            eta_str = "?" if eta is None else f"{eta / 60:.1f}m"
            _write_progress(progress_path, status="running", completed=completed,
                            total=total_jobs, started_at=started_at, last_message=msg)
            print(f"[progress] {completed}/{total_jobs} ({completed/total_jobs*100:.1f}%) ETA={eta_str} | {msg}")

    return results, completed


def aggregate_summary(run_dir: Path, modes: list[str]) -> dict:
    summary: dict = {}
    for results_path in sorted(run_dir.glob("results_*.jsonl")):
        notation = results_path.stem.replace("results_", "")
        rows = [json.loads(line) for line in results_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        summary[notation] = {}
        for mode in modes:
            mode_results = [r for r in rows if r.get("mode") == mode]
            if mode_results:
                mean_conf = sum(r.get("formal_conformance", 0) for r in mode_results) / len(mode_results)
                strict_count = sum(1 for r in mode_results if r.get("success", False))
                summary[notation][mode] = {
                    "n": len(mode_results),
                    "mean_conf": round(mean_conf, 4),
                    "strict_success_rate": round(strict_count / len(mode_results), 4),
                }
    return summary


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(line_buffering=True)
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="E8 Generalisation study runner")
    parser.add_argument(
        "--notation",
        nargs="+",
        choices=["sofl", "statemachine", "miniz", "all"],
        default=["all"],
    )
    parser.add_argument("--modes", nargs="+", default=["B1", "B2", "M"])
    parser.add_argument("--run-name", default=f"run_generalisation_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    parser.add_argument("--task-limit", type=int, default=None)
    parser.add_argument("--no-llm", action="store_true", help="Run B0 reference only (no LLM needed)")
    args = parser.parse_args()

    run_dir = ARTIFACTS / args.run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    progress_path = run_dir / "progress.json"
    started_at = time.time()

    notations = args.notation
    if "all" in notations:
        notations = ["sofl", "statemachine", "miniz"]

    # Count total jobs for progress
    total_jobs = 0
    notation_tasks: dict[str, list] = {}
    for notation in notations:
        tasks = _load_notation_tasks(notation, args.task_limit)
        notation_tasks[notation] = tasks
        if args.no_llm:
            total_jobs += len(tasks)
        else:
            total_jobs += len(tasks) * len(args.modes)

    # Count already completed
    completed = 0
    for notation in notations:
        done = _load_completed_keys(run_dir / f"results_{notation}.jsonl")
        completed += len(done)

    print(f"[E8] Total jobs: {total_jobs}, already done: {completed}")
    print(f"[E8] Progress file: {progress_path}")
    _write_progress(progress_path, status="running", completed=completed, total=total_jobs,
                    started_at=started_at, last_message="starting")

    try:
        from src.llm.ecnu_client import ECNUClient
        llm = ECNUClient() if not args.no_llm else None
    except Exception:
        llm = None
        print("[E8] No LLM client available.", file=sys.stderr)

    all_results = []
    for notation in notations:
        tasks = notation_tasks[notation]
        print(f"\n[E8] {len(tasks)} {notation} tasks")
        results, completed = run_notation(
            notation, tasks, args.modes, run_dir, llm, progress_path,
            started_at, completed, total_jobs, no_llm=args.no_llm,
        )
        all_results.extend(results)

    summary = aggregate_summary(run_dir, args.modes)
    summary_path = run_dir / "generalisation_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_progress(progress_path, status="completed", completed=completed, total=total_jobs,
                    started_at=started_at, last_message="completed")
    print(f"\n[E8] Summary → {summary_path}")

    print("\n=== Generalisation Results ===")
    for notation, mode_data in summary.items():
        print(f"\n  {notation}:")
        for mode, stats in mode_data.items():
            print(f"    {mode}: conf={stats.get('mean_conf', 0):.4f} "
                  f"strict={stats.get('strict_success_rate', 0):.4f} "
                  f"n={stats.get('n', 0)}")


if __name__ == "__main__":
    main()
