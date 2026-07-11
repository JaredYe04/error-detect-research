"""Parameter sweep runner for mechanism analysis experiments (E3–E6).

Usage:
    python experiments/run_sweep.py --experiment complexity --run-name run_complexity_v1
    python experiments/run_sweep.py --experiment boundary_density --run-name run_boundary_v1
    python experiments/run_sweep.py --experiment feedback_variants --run-name run_feedback_v1
    python experiments/run_sweep.py --experiment repair_dynamics --run-name run_repair_v1
    python experiments/run_sweep.py --experiment all --run-name run_mechanism_v1

Each experiment writes its results to:
    artifacts/<run-name>/<experiment>/results.jsonl
    artifacts/<run-name>/<experiment>/summary.json
    artifacts/<run-name>/<experiment>/progress.json   (LLM experiments)
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
from src.benchmarks.complexity import annotate_tasks_complexity
from src.formal.checker import run_formal_check
from src.pipeline.runner import ErrorPreventionPipeline, PipelineConfig, config_for_mode

ARTIFACTS = ROOT / "artifacts"


def _write_progress(
    path: Path,
    *,
    status: str,
    completed: int,
    total: int,
    started_at: float,
    experiment: str = "",
    running_jobs: int = 0,
    completed_start: int = 0,
    last_message: str | None = None,
) -> None:
    elapsed = max(0.0, time.time() - started_at)
    done_this_session = max(completed - completed_start, 0)
    rate = (done_this_session / elapsed) if elapsed > 0 and done_this_session > 0 else 0.0
    remaining = max(total - completed, 0)
    eta_sec = (remaining / rate) if rate > 1e-9 else None
    payload = {
        "status": status,
        "experiment": experiment,
        "completed": completed,
        "total": total,
        "percent": (completed / total * 100.0) if total else 100.0,
        "elapsed_sec": round(elapsed, 1),
        "rate_per_sec": round(rate, 4),
        "eta_sec": round(eta_sec, 1) if eta_sec is not None else None,
        "running_jobs": running_jobs,
        "last_message": last_message or "",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _print_progress(completed: int, total: int, progress_path: Path, msg: str, *, running: int = 0) -> None:
    pct = (completed / total * 100.0) if total else 100.0
    try:
        prog = json.loads(progress_path.read_text(encoding="utf-8"))
        eta = prog.get("eta_sec")
    except Exception:
        eta = None
    eta_str = "?" if eta is None else f"{eta / 60:.1f}m"
    run_str = f" active={running}" if running else ""
    print(f"[progress] {completed}/{total} ({pct:.1f}%) ETA={eta_str}{run_str} | {msg}")
    sys.stdout.flush()


# ---------------------------------------------------------------------------
# Parallel job workers (module-level for ProcessPoolExecutor on Windows)
# ---------------------------------------------------------------------------

def _run_feedback_job(job: dict, *, run_dir_str: str) -> tuple[str, dict, str]:
    """Single E6 job: one task × one feedback variant."""
    from src.llm.ecnu_client import ECNUClient

    task = job["task"]
    variant_key = job["variant_key"]
    variant_label = job["variant_label"]
    task_id = task["taskId"]
    job_key = job["job_key"]
    ref_code = task.get("referenceCode", "")
    model = job.get("model")

    cfg = config_for_mode("M")
    cfg.feedback_variant = variant_key
    if model:
        cfg.model = model
    cfg = copy.deepcopy(cfg)
    safe_id = task_id.replace(".", "_").replace("/", "_")
    safe_model = (model or "default").replace("/", "_").replace(":", "_")
    llm = ECNUClient(
        log_dir=Path(run_dir_str) / "llm_logs" / f"proc-{safe_id}-{variant_key}-{safe_model}"
    )
    pipeline = ErrorPreventionPipeline(config=cfg, llm=llm)
    try:
        result = pipeline.run_task(task, reference_code=ref_code)
        rec = asdict(result) if hasattr(result, "__dataclass_fields__") else result.__dict__.copy()
    except Exception as e:  # noqa: BLE001
        rec = {"task_id": task_id, "error": str(e), "formal_conformance": 0.0, "attempt_history": []}
    rec["feedback_variant"] = variant_key
    rec["feedback_variant_label"] = variant_label
    if model:
        rec["model"] = model
    msg = f"[E6] {task_id} variant={variant_label} model={model or 'default'} conf={rec.get('formal_conformance', 0):.3f}"
    return job_key, rec, msg


def _run_complexity_job(job: dict, *, run_dir_str: str) -> tuple[str, dict, str]:
    """Single E3 job: one task × one mode."""
    from src.llm.ecnu_client import ECNUClient

    task = job["task"]
    mode = job["mode"]
    task_id = task["taskId"]
    job_key = job["job_key"]
    ref_code = task.get("referenceCode", "")

    cfg = copy.deepcopy(config_for_mode(mode))
    safe_id = task_id.replace(".", "_").replace("/", "_")
    llm = ECNUClient(log_dir=Path(run_dir_str) / "llm_logs" / f"proc-{safe_id}-{mode}") if mode != "B0" else None
    pipeline = ErrorPreventionPipeline(config=cfg, llm=llm)
    try:
        result = pipeline.run_task(task, reference_code=ref_code)
        rec = asdict(result) if hasattr(result, "__dataclass_fields__") else result.__dict__.copy()
    except Exception as e:  # noqa: BLE001
        rec = {"task_id": task_id, "mode": mode, "error": str(e), "formal_conformance": 0.0}
    rec["complexity"] = task.get("complexity", {})
    msg = f"[E3] {task_id} {mode} conf={rec.get('formal_conformance', 0):.3f}"
    return job_key, rec, msg


def _run_jobs_parallel(
    *,
    pending: list[dict],
    total: int,
    completed_start: int,
    results_path: Path,
    progress_path: Path,
    started_at: float,
    experiment: str,
    run_dir: Path,
    worker_fn,
    parallelism: int,
) -> list[dict]:
    """Execute pending jobs with ProcessPoolExecutor; append results incrementally."""
    results = _load_jsonl(results_path)
    completed = completed_start
    llm_log_root = run_dir / "llm_logs"
    llm_log_root.mkdir(parents=True, exist_ok=True)

    _write_progress(
        progress_path, status="running", completed=completed, total=total,
        started_at=started_at, experiment=experiment, running_jobs=0,
        completed_start=completed_start,
        last_message=f"parallelism={parallelism}, pending={len(pending)}",
    )

    writer = results_path.open("a", encoding="utf-8")
    try:
        if parallelism <= 1:
            for job in pending:
                _job_key, rec, msg = worker_fn(job, run_dir_str=str(run_dir))
                writer.write(json.dumps(rec, ensure_ascii=False) + "\n")
                writer.flush()
                results.append(rec)
                completed += 1
                print(msg)
                _write_progress(
                    progress_path, status="running", completed=completed, total=total,
                    started_at=started_at, experiment=experiment, running_jobs=0,
                    completed_start=completed_start, last_message=msg,
                )
                _print_progress(completed, total, progress_path, msg)
        else:
            max_workers = max(1, parallelism)
            with ProcessPoolExecutor(max_workers=max_workers) as ex:
                futures = {
                    ex.submit(worker_fn, job, run_dir_str=str(run_dir)): job
                    for job in pending
                }
                session_done = 0
                for fut in as_completed(futures):
                    _job_key, rec, msg = fut.result()
                    writer.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    writer.flush()
                    results.append(rec)
                    completed += 1
                    session_done += 1
                    running = sum(1 for f in futures if not f.done())
                    print(msg)
                    _write_progress(
                        progress_path, status="running", completed=completed, total=total,
                        started_at=started_at, experiment=experiment,
                        running_jobs=max(0, running),
                        completed_start=completed_start, last_message=msg,
                    )
                    _print_progress(completed, total, progress_path, msg, running=max(0, running))
    finally:
        writer.close()

    return results


def _append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
        f.flush()


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


def _load_completed_keys(path: Path, key_fields: tuple[str, ...]) -> set[tuple]:
    return {tuple(r.get(f) for f in key_fields) for r in _load_jsonl(path)}


def _load_annotated_tasks() -> list[dict]:
    """Load tasks with complexity metadata, annotating on-the-fly if needed."""
    annotated_path = ROOT / "benchmarks" / "hard_tasks_annotated.json"
    if annotated_path.exists():
        tasks = json.loads(annotated_path.read_text(encoding="utf-8"))
        print(f"[sweep] Loaded {len(tasks)} annotated tasks from {annotated_path.name}")
        return tasks
    hard_path = ROOT / "benchmarks" / "hard_tasks.json"
    if hard_path.exists():
        tasks = json.loads(hard_path.read_text(encoding="utf-8"))
    else:
        tasks = load_benchmark()
        tasks = [t for t in tasks if "HardSynthetic" in t.get("taskId", "")]
    print(f"[sweep] Annotating {len(tasks)} tasks (Z3 overlap analysis, may take 2–5 min)...")
    sys.stdout.flush()
    tasks = annotate_tasks_complexity(tasks)
    annotated_path.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[sweep] Saved annotated benchmark to {annotated_path}")
    return tasks


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _write_summary(path: Path, summary: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# E3 — Specification Complexity Analysis
# ---------------------------------------------------------------------------

def run_complexity_experiment(
    tasks: list[dict],
    out_dir: Path,
    *,
    modes: list[str] | None = None,
    llm_client=None,
    parallelism: int = 1,
) -> None:
    """Run E3: stratify Conf by overlap_density_tier and guard_complexity."""
    modes = modes or ["B1", "B2", "M"]
    out_dir.mkdir(parents=True, exist_ok=True)
    results_path = out_dir / "results.jsonl"
    progress_path = out_dir / "progress.json"
    started_at = time.time()

    done = _load_completed_keys(results_path, ("task_id", "mode"))
    pending: list[dict] = []
    for task in tasks:
        if not task.get("complexity"):
            continue
        task_id = task["taskId"]
        for mode in modes:
            if (task_id, mode) in done:
                continue
            pending.append({
                "task": task,
                "mode": mode,
                "job_key": f"{task_id}|{mode}",
            })

    total = len([1 for task in tasks if task.get("complexity") for mode in modes])
    completed_start = len(done)

    if parallelism > 1 or llm_client is None:
        results = _run_jobs_parallel(
            pending=pending,
            total=total,
            completed_start=completed_start,
            results_path=results_path,
            progress_path=progress_path,
            started_at=started_at,
            experiment="complexity",
            run_dir=out_dir,
            worker_fn=_run_complexity_job,
            parallelism=parallelism,
        )
    else:
        # Serial with shared client (legacy path)
        results = _load_jsonl(results_path)
        completed = completed_start
        for job in pending:
            task, mode = job["task"], job["mode"]
            task_id = task["taskId"]
            ref_code = task.get("referenceCode", "")
            cfg = config_for_mode(mode)
            pipeline = ErrorPreventionPipeline(config=cfg, llm=llm_client)
            try:
                result = pipeline.run_task(task, reference_code=ref_code)
                rec = asdict(result) if hasattr(result, "__dataclass_fields__") else result.__dict__.copy()
            except Exception as e:  # noqa: BLE001
                rec = {"task_id": task_id, "mode": mode, "error": str(e), "formal_conformance": 0.0}
            rec["complexity"] = task.get("complexity", {})
            _append_jsonl(results_path, rec)
            results.append(rec)
            completed += 1

    # Aggregate by (tier, guard_complexity, mode)
    summary: dict = {"by_tier": {}, "by_guard_complexity": {}}
    for mode in modes:
        mode_results = [r for r in results if r.get("mode") == mode]
        for tier in ("low", "medium", "high"):
            tier_results = [r for r in mode_results if r.get("complexity", {}).get("overlap_density_tier") == tier]
            if tier_results:
                avg_conf = sum(r.get("formal_conformance", 0) for r in tier_results) / len(tier_results)
                summary["by_tier"].setdefault(tier, {})[mode] = {
                    "n": len(tier_results),
                    "mean_conf": round(avg_conf, 4),
                }

    _write_summary(out_dir / "summary.json", summary)
    _write_progress(
        progress_path, status="completed", completed=total, total=total,
        started_at=started_at, experiment="complexity", completed_start=completed_start,
        last_message="completed",
    )
    print(f"[E3] Complete. Results in {out_dir}")


# ---------------------------------------------------------------------------
# E4 — Boundary Density Analysis
# ---------------------------------------------------------------------------

def run_boundary_density_experiment(
    tasks: list[dict],
    out_dir: Path,
) -> None:
    """Run E4: compare SMT witness vs random sampling across case budgets and density tiers."""
    from src.formal.fsf_eval import generate_concrete_cases
    import random

    out_dir.mkdir(parents=True, exist_ok=True)
    case_budgets = [4, 8, 16, 32, 64]
    results = []

    for task in tasks:
        complexity = task.get("complexity", {})
        tier = complexity.get("overlap_density_tier", "unknown")
        scenarios = task.get("fsfScenarios", [])
        signature = task.get("signature", {})
        task_id = task["taskId"]
        ref_code = task.get("referenceCode", "")

        if not ref_code or not scenarios:
            continue

        for budget in case_budgets:
            # SMT witnesses (Z3-guided)
            try:
                smt_cases = generate_concrete_cases(scenarios, signature, max_cases=budget)
                smt_coverage = len(set(c.scenario_index for c in smt_cases)) / max(
                    len([sc for sc in scenarios if sc.get("kind") != "others"]), 1
                )
            except Exception:
                smt_coverage = 0.0

            # Random sampling (sample inputs uniformly and check coverage)
            rng = random.Random(42)
            input_vars = [p["name"] for p in signature.get("inputs", signature.get("params", []))]
            random_covered = set()
            for _ in range(budget):
                rand_inputs = {v: rng.randint(-5, 20) for v in input_vars}
                for sc in scenarios:
                    if sc.get("kind") == "others":
                        continue
                    try:
                        from src.formal.fsf_eval import eval_predicate
                        if eval_predicate(sc.get("test", ""), rand_inputs):
                            random_covered.add(sc["index"])
                            break
                    except Exception:
                        pass
            n_non_others = max(len([sc for sc in scenarios if sc.get("kind") != "others"]), 1)
            random_coverage = len(random_covered) / n_non_others

            results.append({
                "task_id": task_id,
                "density_tier": tier,
                "budget": budget,
                "smt_coverage": round(smt_coverage, 4),
                "random_coverage": round(random_coverage, 4),
            })

    _write_jsonl(out_dir / "results.jsonl", results)

    # Aggregate by (tier, budget, method)
    summary: dict = {}
    for tier in ("low", "medium", "high"):
        summary[tier] = {}
        for budget in case_budgets:
            tier_budget = [r for r in results if r["density_tier"] == tier and r["budget"] == budget]
            if tier_budget:
                summary[tier][budget] = {
                    "n": len(tier_budget),
                    "mean_smt_coverage": round(sum(r["smt_coverage"] for r in tier_budget) / len(tier_budget), 4),
                    "mean_random_coverage": round(sum(r["random_coverage"] for r in tier_budget) / len(tier_budget), 4),
                }
    _write_summary(out_dir / "summary.json", summary)
    print(f"[E4] Complete. Results in {out_dir}")


# ---------------------------------------------------------------------------
# E5 — Repair Dynamics (uses attempt_history from main E1 run)
# ---------------------------------------------------------------------------

def run_repair_dynamics_analysis(
    main_run_dir: Path,
    out_dir: Path,
    *,
    modes: list[str] | None = None,
) -> None:
    """Extract E5 repair trajectory data from an existing main run's attempt_history."""
    modes = modes or ["M", "B2"]
    out_dir.mkdir(parents=True, exist_ok=True)

    results_path = main_run_dir / "results.jsonl"
    if not results_path.exists():
        print(f"[E5] No results.jsonl at {results_path}. Run E1 first.", file=sys.stderr)
        return

    trajectory_data = []
    with results_path.open(encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            mode = rec.get("mode")
            if mode not in modes:
                continue
            history = rec.get("attempt_history", [])
            for entry in history:
                trajectory_data.append({
                    "task_id": rec.get("task_id"),
                    "mode": mode,
                    "attempt": entry.get("attempt"),
                    "conf": entry.get("conf", 0.0),
                    "cex_count": entry.get("cex_count", 0),
                    "pattern_count": entry.get("pattern_count", 0),
                })

    _write_jsonl(out_dir / "trajectory.jsonl", trajectory_data)

    # Aggregate Conf(k) per mode
    summary: dict = {}
    for mode in modes:
        mode_data = [r for r in trajectory_data if r["mode"] == mode]
        summary[mode] = {}
        for k in (1, 2, 3):
            k_data = [r for r in mode_data if r["attempt"] == k]
            if k_data:
                mean_conf = sum(r["conf"] for r in k_data) / len(k_data)
                summary[mode][k] = {"n": len(k_data), "mean_conf": round(mean_conf, 4)}

    _write_summary(out_dir / "summary.json", summary)
    print(f"[E5] Repair dynamics extracted. Results in {out_dir}")


# ---------------------------------------------------------------------------
# E6 — Feedback Variant Comparison
# ---------------------------------------------------------------------------

def run_feedback_variant_experiment(
    tasks: list[dict],
    out_dir: Path,
    *,
    llm_client=None,
    parallelism: int = 6,
    model: str | None = None,
    variants: list[tuple[str, str]] | None = None,
) -> None:
    """Run E6: compare feedback variants under the same M pipeline.

    ``variants`` is a list of (variant_key, variant_label). Default is classic
    A/B/C. Agent B field ablations pass an extended list.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    results_path = out_dir / "results.jsonl"
    progress_path = out_dir / "progress.json"
    started_at = time.time()

    if variants is None:
        variants = [
            ("test_only", "A"),
            ("test_expected", "B"),
            ("semantic_ir", "C"),
        ]
    done = _load_completed_keys(results_path, ("task_id", "feedback_variant"))
    pending: list[dict] = []
    for task in tasks:
        task_id = task["taskId"]
        for variant_key, variant_label in variants:
            if (task_id, variant_key) in done:
                continue
            pending.append({
                "task": task,
                "variant_key": variant_key,
                "variant_label": variant_label,
                "job_key": f"{task_id}|{variant_key}",
                "model": model,
            })

    total = len(tasks) * len(variants)
    completed_start = len(done)

    if done:
        print(f"[E6] Resuming: {completed_start}/{total} jobs already in {results_path}")
    print(f"[E6] model={model or 'default'} Parallelism={parallelism}, pending={len(pending)} jobs")

    if parallelism > 1:
        results = _run_jobs_parallel(
            pending=pending,
            total=total,
            completed_start=completed_start,
            results_path=results_path,
            progress_path=progress_path,
            started_at=started_at,
            experiment="feedback_variants",
            run_dir=out_dir,
            worker_fn=_run_feedback_job,
            parallelism=parallelism,
        )
    else:
        results = _load_jsonl(results_path)
        completed = completed_start
        for job in pending:
            task = job["task"]
            variant_key, variant_label = job["variant_key"], job["variant_label"]
            task_id = task["taskId"]
            ref_code = task.get("referenceCode", "")
            cfg = config_for_mode("M")
            cfg.feedback_variant = variant_key
            if model:
                cfg.model = model
            pipeline = ErrorPreventionPipeline(config=cfg, llm=llm_client)
            try:
                result = pipeline.run_task(task, reference_code=ref_code)
                rec = asdict(result) if hasattr(result, "__dataclass_fields__") else result.__dict__.copy()
            except Exception as e:  # noqa: BLE001
                rec = {"task_id": task_id, "error": str(e), "formal_conformance": 0.0, "attempt_history": []}
            rec["feedback_variant"] = variant_key
            rec["feedback_variant_label"] = variant_label
            if model:
                rec["model"] = model
            _append_jsonl(results_path, rec)
            results.append(rec)
            completed += 1
            msg = f"[E6] {task_id} variant={variant_label} conf={rec.get('formal_conformance', 0):.3f}"
            print(msg)
            _write_progress(
                progress_path, status="running", completed=completed, total=total,
                started_at=started_at, experiment="feedback_variants",
                completed_start=completed_start, last_message=msg,
            )
            _print_progress(completed, total, progress_path, msg)

    summary: dict = {}
    for variant_key, variant_label in variants:
        var_results = [r for r in results if r.get("feedback_variant") == variant_key]
        if var_results:
            mean_conf = sum(r.get("formal_conformance", 0) for r in var_results) / len(var_results)
            # mean iterations to convergence (length of attempt_history)
            mean_iters = sum(len(r.get("attempt_history", [])) for r in var_results) / len(var_results)
            summary[variant_label] = {
                "variant": variant_key,
                "n": len(var_results),
                "mean_conf": round(mean_conf, 4),
                "mean_iterations": round(mean_iters, 2),
            }
    if model:
        summary["model"] = model
    _write_summary(out_dir / "summary.json", summary)
    _write_progress(
        progress_path, status="completed", completed=total, total=total,
        started_at=started_at, experiment="feedback_variants",
        completed_start=completed_start, last_message="completed",
    )
    print(f"[E6] Complete. Results in {out_dir}")
    print(f"[E6] Summary: {json.dumps(summary, indent=2)}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    # Line-buffer stdout so background runs show progress immediately
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(line_buffering=True)
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Mechanism analysis sweep runner")
    parser.add_argument(
        "--experiment",
        choices=[
            "complexity",
            "boundary_density",
            "feedback_variants",
            "ir_field_ablation",
            "repair_dynamics",
            "all",
        ],
        required=True,
    )
    parser.add_argument("--run-name", default=f"run_sweep_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    parser.add_argument("--task-limit", type=int, default=None, help="Limit tasks for quick testing")
    parser.add_argument(
        "--main-run",
        type=Path,
        default=None,
        help="Path to main E1 run dir (for repair_dynamics extraction)",
    )
    parser.add_argument("--modes", nargs="+", default=None)
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Override LLM model id for E6/E3 (e.g. ecnu-max, gpt-4o, claude-sonnet-4-6)",
    )
    parser.add_argument(
        "--task-subset",
        type=Path,
        default=None,
        help="JSON list of taskIds or task objects (e.g. benchmarks/e12_stratified_30.json)",
    )
    parser.add_argument(
        "--parallelism",
        type=int,
        default=10,
        help="Parallel workers for LLM experiments (E3/E6). Default: 6.",
    )
    args = parser.parse_args()

    run_dir = ARTIFACTS / args.run_name
    run_dir.mkdir(parents=True, exist_ok=True)

    tasks = _load_annotated_tasks()
    # Paper-aligned: only HardSynthetic tasks (120-task hard suite)
    tasks = [t for t in tasks if "HardSynthetic" in t.get("taskId", "")]
    if args.task_subset:
        raw = json.loads(Path(args.task_subset).read_text(encoding="utf-8"))
        if raw and isinstance(raw[0], dict):
            want = {t.get("taskId") or t.get("task_id") for t in raw}
        else:
            want = set(raw)
        tasks = [t for t in tasks if t.get("taskId") in want]
        print(f"[sweep] Filtered to task-subset {args.task_subset}: {len(tasks)} tasks")
    if args.task_limit:
        tasks = tasks[: args.task_limit]
    print(f"[sweep] Loaded {len(tasks)} tasks. model={args.model or 'default'} Parallelism={args.parallelism}")

    llm = None
    if args.parallelism <= 1:
        try:
            from src.llm.ecnu_client import ECNUClient
            llm = ECNUClient()
        except Exception:
            print("[sweep] No LLM client available; runs requiring LLM will error.", file=sys.stderr)

    exp = args.experiment
    if exp in ("complexity", "all"):
        run_complexity_experiment(
            tasks, run_dir / "complexity", modes=args.modes, llm_client=llm,
            parallelism=args.parallelism,
        )
    if exp in ("boundary_density", "all"):
        run_boundary_density_experiment(tasks, run_dir / "boundary_density")
    if exp in ("feedback_variants", "all"):
        out = run_dir / "feedback_variants"
        print(f"[sweep] E6 progress file: {out / 'progress.json'}")
        print(f"[sweep] E6 results (incremental): {out / 'results.jsonl'}")
        run_feedback_variant_experiment(
            tasks, out, llm_client=llm, parallelism=args.parallelism, model=args.model,
        )
    if exp == "ir_field_ablation":
        out = run_dir / "ir_field_ablation"
        field_variants = [
            ("test_only", "A"),
            ("semantic_ir", "FULL"),
            ("ir_no_scenario_id", "NO_SID"),
            ("ir_no_expected", "NO_EXP"),
            ("ir_no_constraint", "NO_CON"),
            ("ir_no_reason", "NO_REA"),
            ("ir_no_suggested_fix", "NO_FIX"),
            ("ir_nl_only", "NL"),
        ]
        print(f"[sweep] IR field ablation → {out}")
        run_feedback_variant_experiment(
            tasks,
            out,
            llm_client=llm,
            parallelism=args.parallelism,
            model=args.model,
            variants=field_variants,
        )
    if exp in ("repair_dynamics", "all"):
        main_run = args.main_run or (ARTIFACTS / "run_ccf_b_main_v1")
        run_repair_dynamics_analysis(main_run, run_dir / "repair_dynamics", modes=args.modes)

    print(f"\n[sweep] All experiments complete. Output: {run_dir}")


if __name__ == "__main__":
    main()
