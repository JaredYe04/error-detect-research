#!/usr/bin/env python3
"""Build benchmark tasks from Agile-SOFL examples.

New flags (CCF-B upgrade):
  --hard-limit N   Keep only the first N hard tasks that pass the Z3
                   satisfiability filter (default: 120, matching the thesis).
  --annotate       Compute and embed complexity metadata (overlap_rate, etc.)
                   in each task dict.  Required for E3 complexity analysis.
  --annotated-path PATH
                   Output path for the annotated hard benchmark JSON.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.benchmarks import HARD_BENCHMARK_PATH, save_benchmark, save_hard_benchmark
from src.benchmarks.complexity import annotate_tasks_complexity


def _z3_satisfiability_filter(tasks: list[dict], *, limit: int) -> list[dict]:
    """Filter tasks to those with at least one non-trivially overlapping scenario pair.

    A task passes the filter if the Z3 solver can find an input satisfying the
    priority formula for at least two distinct scenarios (i.e., there exists an
    input where two guards are simultaneously satisfiable, making ordering matter).

    This is the filter described in the thesis §6.2 that reduces 180 → 120 tasks.
    """
    try:
        from src.formal.fsf_eval import generate_concrete_cases, eval_predicate
    except ImportError as e:
        print(f"[warn] Cannot import fsf_eval ({e}); skipping Z3 filter.", file=sys.stderr)
        return tasks[:limit]

    kept = []
    skipped = 0
    for task in tasks:
        if len(kept) >= limit:
            break
        scenarios = task.get("fsfScenarios", [])
        signature = task.get("signature", {})
        non_others = [sc for sc in scenarios if sc.get("kind") != "others"]
        if len(non_others) < 2:
            skipped += 1
            continue

        # Generate witnesses and test for overlapping guards
        try:
            cases = generate_concrete_cases(scenarios, signature, max_cases=len(non_others) * 2)
        except Exception:
            skipped += 1
            continue

        overlap_found = False
        for case in cases:
            fire_count = sum(
                1 for sc in non_others
                if _safe_eval_predicate(sc.get("test", ""), case.inputs)
            )
            if fire_count >= 2:
                overlap_found = True
                break

        if overlap_found:
            kept.append(task)
        else:
            skipped += 1

    print(
        f"[filter] Z3 satisfiability filter: {len(kept)} tasks kept, "
        f"{skipped} skipped (of {len(tasks)} generated). Limit={limit}.",
        file=sys.stderr,
    )
    return kept


def _safe_eval_predicate(test_text: str, inputs: dict) -> bool:
    try:
        from src.formal.fsf_eval import eval_predicate
        return bool(eval_predicate(test_text, inputs))
    except Exception:
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Build base + hard benchmark suites")
    parser.add_argument("--hard-only", action="store_true")
    parser.add_argument(
        "--hard-size",
        type=int,
        default=180,
        help="Number of hard tasks to generate before filtering (default: 180)",
    )
    parser.add_argument(
        "--hard-limit",
        type=int,
        default=120,
        help="Maximum hard tasks to keep after Z3 satisfiability filter (default: 120)",
    )
    parser.add_argument("--hard-scenarios", type=int, default=8)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--annotate",
        action="store_true",
        help="Compute and embed complexity metadata (overlap_rate, guard_complexity, etc.)",
    )
    parser.add_argument(
        "--annotated-path",
        type=Path,
        default=None,
        help="Output path for annotated hard benchmark (default: benchmarks/hard_tasks_annotated.json)",
    )
    parser.add_argument(
        "--no-filter",
        action="store_true",
        help="Skip the Z3 satisfiability filter (use all generated tasks up to --hard-size)",
    )
    args = parser.parse_args()

    from src.benchmarks.hard_gen import generate_hard_tasks

    # Generate raw hard tasks
    raw_tasks = generate_hard_tasks(
        n_tasks=args.hard_size,
        scenarios_per_task=args.hard_scenarios,
        seed=args.seed,
    )
    print(f"[gen] Generated {len(raw_tasks)} raw hard tasks.")

    # Apply Z3 filter (or just take first N)
    if args.no_filter:
        filtered_tasks = raw_tasks[: args.hard_limit]
        print(f"[filter] Skipped (--no-filter). Kept first {len(filtered_tasks)} tasks.")
    else:
        filtered_tasks = _z3_satisfiability_filter(raw_tasks, limit=args.hard_limit)

    # Save filtered hard benchmark
    hard_path = HARD_BENCHMARK_PATH
    hard_path.parent.mkdir(parents=True, exist_ok=True)
    hard_path.write_text(
        json.dumps(filtered_tasks, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[save] Hard benchmark ({len(filtered_tasks)} tasks) → {hard_path}")

    # Optionally annotate with complexity metadata
    if args.annotate:
        annotated = annotate_tasks_complexity(list(filtered_tasks))
        annotated_path = args.annotated_path or (
            hard_path.parent / "hard_tasks_annotated.json"
        )
        annotated_path.write_text(
            json.dumps(annotated, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"[annotate] Complexity-annotated benchmark → {annotated_path}")
        tiers = {"low": 0, "medium": 0, "high": 0}
        for t in annotated:
            tier = t.get("complexity", {}).get("overlap_density_tier")
            if tier in tiers:
                tiers[tier] += 1
        print(f"[annotate] Overlap density tiers: {tiers}")

    if args.hard_only:
        return

    path = save_benchmark(include_hard=True)
    print(f"[save] Combined benchmark → {path}")


if __name__ == "__main__":
    main()
