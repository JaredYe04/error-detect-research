"""SMT domain scalability ablation (no LLM required).

Times Z3 witness generation under widening integer boxes and a Real
encoding probe. Writes JSON + a simple CSV for paper figures.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import time
from pathlib import Path
from typing import Any

from z3 import And, BoolVal, Int, Not, Or, Real, Solver, sat

from src.formal.fsf_eval import (
    DEFAULT_INT_HI,
    DEFAULT_INT_LO,
    collect_variables,
    generate_concrete_cases,
    predicate_to_z3,
)

ROOT = Path(__file__).resolve().parents[1]


def _load_tasks(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else list(data.get("tasks") or [])


def _time_int_domain(task: dict[str, Any], lo: int, hi: int, max_cases: int = 12) -> dict[str, Any]:
    scenarios = task.get("fsfScenarios", [])
    signature = task.get("signature", {})
    t0 = time.perf_counter()
    err = None
    n_cases = 0
    try:
        cases = generate_concrete_cases(
            scenarios, signature, max_cases=max_cases, int_lo=lo, int_hi=hi
        )
        n_cases = len(cases)
    except Exception as exc:  # noqa: BLE001
        err = str(exc)
    ms = (time.perf_counter() - t0) * 1000.0
    return {
        "taskId": task.get("taskId"),
        "encoding": "int",
        "lo": lo,
        "hi": hi,
        "ms": round(ms, 3),
        "n_cases": n_cases,
        "ok": err is None and n_cases > 0,
        "error": err,
    }


def _time_real_encoding(task: dict[str, Any], lo: float, hi: float, max_cases: int = 12) -> dict[str, Any]:
    """Probe: same FSF guards encoded over Z3 Reals (timing only)."""
    scenarios = task.get("fsfScenarios", [])
    signature = task.get("signature", {})
    var_names = collect_variables(scenarios, signature)
    sym = {n: Real(n) for n in var_names}
    t0 = time.perf_counter()
    n_sat = 0
    err = None
    try:
        for sc in scenarios:
            if sc.get("kind") == "others":
                prior = [
                    predicate_to_z3(s["test"], sym)
                    for s in scenarios
                    if s.get("kind") != "others" and s.get("test")
                ]
                test_z3 = Not(Or(*prior)) if prior else BoolVal(True)
            else:
                test_z3 = predicate_to_z3(sc["test"], sym)
                prior = []
                for s in scenarios:
                    if s.get("kind") == "others":
                        break
                    if s is sc:
                        break
                    prior.append(predicate_to_z3(s["test"], sym))
                if prior:
                    test_z3 = And(test_z3, Not(Or(*prior)))
            solver = Solver()
            solver.set("timeout", 5000)  # ms
            solver.add(test_z3)
            for n in var_names:
                solver.add(sym[n] >= lo)
                solver.add(sym[n] <= hi)
            attempts = 0
            while solver.check() == sat and attempts < 3 and n_sat < max_cases:
                model = solver.model()
                block = []
                for n in var_names:
                    v = model.eval(sym[n], model_completion=True)
                    block.append(sym[n] != v)
                if block:
                    solver.add(Or(*block))
                n_sat += 1
                attempts += 1
    except Exception as exc:  # noqa: BLE001
        err = str(exc)
    ms = (time.perf_counter() - t0) * 1000.0
    return {
        "taskId": task.get("taskId"),
        "encoding": "real",
        "lo": lo,
        "hi": hi,
        "ms": round(ms, 3),
        "n_cases": n_sat,
        "ok": err is None,
        "error": err,
    }


def run_ablation(
    tasks: list[dict[str, Any]],
    *,
    domains: list[tuple[int, int]],
    include_real: bool = True,
    repeats: int = 3,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for task in tasks:
        for lo, hi in domains:
            samples = [_time_int_domain(task, lo, hi) for _ in range(repeats)]
            ms_vals = [r["ms"] for r in samples]
            rows.append(
                {
                    **samples[0],
                    "ms_mean": round(statistics.mean(ms_vals), 3),
                    "ms_stdev": round(statistics.pstdev(ms_vals), 3) if len(ms_vals) > 1 else 0.0,
                    "repeats": repeats,
                }
            )
        if include_real:
            # Map compact tasks into a float box; wide tasks keep numeric scale.
            lo_r, hi_r = -100.0, 100.0
            samples = [_time_real_encoding(task, lo_r, hi_r) for _ in range(repeats)]
            ms_vals = [r["ms"] for r in samples]
            rows.append(
                {
                    **samples[0],
                    "ms_mean": round(statistics.mean(ms_vals), 3),
                    "ms_stdev": round(statistics.pstdev(ms_vals), 3) if len(ms_vals) > 1 else 0.0,
                    "repeats": repeats,
                }
            )

    # Aggregate by domain label
    by_domain: dict[str, list[float]] = {}
    for r in rows:
        if r["encoding"] == "int":
            key = f"int[{r['lo']},{r['hi']}]"
        else:
            key = f"real[{r['lo']},{r['hi']}]"
        by_domain.setdefault(key, []).append(float(r["ms_mean"]))

    summary = {
        "n_tasks": len(tasks),
        "default_domain": [DEFAULT_INT_LO, DEFAULT_INT_HI],
        "domains": {
            k: {
                "mean_ms": round(statistics.mean(v), 3),
                "p50_ms": round(statistics.median(v), 3),
                "p95_ms": round(sorted(v)[max(0, int(0.95 * (len(v) - 1)))], 3),
                "max_ms": round(max(v), 3),
                "n": len(v),
            }
            for k, v in by_domain.items()
        },
        "rows": rows,
    }
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--benchmark-path",
        type=Path,
        default=ROOT / "benchmarks" / "real_priority_micro_v1.json",
    )
    ap.add_argument("--task-limit", type=int, default=0)
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "paper" / "hsp-agile" / "artifacts" / "smt_scalability_v1",
    )
    args = ap.parse_args()

    tasks = _load_tasks(args.benchmark_path)
    if args.task_limit > 0:
        tasks = tasks[: args.task_limit]

    domains = [(-5, 20), (-20, 50), (-100, 100), (-1000, 1000)]
    summary = run_ablation(tasks, domains=domains, include_real=True, repeats=args.repeats)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "summary.json").write_text(
        json.dumps({k: v for k, v in summary.items() if k != "rows"}, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.out_dir / "rows.json").write_text(
        json.dumps(summary["rows"], indent=2) + "\n", encoding="utf-8"
    )

    # CSV for plotting: domain -> mean_ms across tasks
    csv_path = args.out_dir / "domain_latency.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["domain", "mean_ms", "p50_ms", "p95_ms", "max_ms", "n"])
        for k, stats in summary["domains"].items():
            w.writerow(
                [k, stats["mean_ms"], stats["p50_ms"], stats["p95_ms"], stats["max_ms"], stats["n"]]
            )

    print(json.dumps(summary["domains"], indent=2))
    print(f"wrote {args.out_dir}")


if __name__ == "__main__":
    main()
