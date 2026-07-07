"""Specification complexity metadata computation for benchmark tasks.

Computes per-task complexity annotations needed for E3 (complexity stratification):
  - overlap_density:     fraction of input space where >= 2 guards can fire simultaneously
  - scenario_count:      number of non-others scenarios
  - guard_complexity:    Simple / AND / Nested / Arithmetic / Mixed
  - has_external_vars:   whether output vars depend on input vars not in guards
  - overlap_rate:        mean number of simultaneously satisfiable guards per Z3 witness
"""

from __future__ import annotations

import re
from typing import Any

try:
    from z3 import And, Int, Not, Or, Solver, sat, unknown

    Z3_AVAILABLE = True
except ImportError:
    Z3_AVAILABLE = False

from src.formal.fsf_eval import generate_concrete_cases


_ARITHMETIC_OPS = re.compile(r"[+\-*/%]|div|mod", re.IGNORECASE)
_NESTED_KW = re.compile(r"\band\b|\bor\b|&&|\|\|", re.IGNORECASE)
_AND_ONLY = re.compile(r"&&|and", re.IGNORECASE)


def _guard_complexity_label(guard_text: str) -> str:
    """Classify a single guard predicate string."""
    has_arith = bool(_ARITHMETIC_OPS.search(guard_text))
    has_nested = bool(_NESTED_KW.search(guard_text))
    has_and = bool(_AND_ONLY.search(guard_text))

    atoms = [a.strip() for a in re.split(r"&&|and|\|\||or", guard_text, flags=re.IGNORECASE) if a.strip()]
    n_atoms = len(atoms)

    if has_arith and has_nested:
        return "Mixed"
    if has_arith:
        return "Arithmetic"
    if n_atoms >= 3:
        return "Nested"
    if has_and or n_atoms == 2:
        return "AND"
    return "Simple"


def _aggregate_complexity(labels: list[str]) -> str:
    """Aggregate per-scenario guard complexity labels into a single task-level label."""
    priority = ["Mixed", "Arithmetic", "Nested", "AND", "Simple"]
    for p in priority:
        if p in labels:
            return p
    return "Simple"


def _count_overlap_samples(
    scenarios: list[dict[str, Any]],
    signature: dict[str, Any],
    *,
    sample_n: int = 32,
) -> float:
    """Estimate average overlap rate by generating witnesses and counting
    how many guards fire on each witness input.

    Returns mean number of simultaneously satisfiable guards per witness point.
    This is a lightweight approximation; full measure computation would require
    Z3 integration over the full domain.
    """
    if not scenarios:
        return 0.0

    cases = generate_concrete_cases(scenarios, signature, max_cases=sample_n)
    if not cases:
        return 0.0

    # For each case, count how many non-others guards fire
    total_overlap = 0
    from src.formal.fsf_eval import eval_predicate

    for case in cases:
        fire_count = 0
        for sc in scenarios:
            if sc.get("kind") == "others":
                continue
            test_text = sc.get("test", "")
            try:
                if eval_predicate(test_text, case.inputs):
                    fire_count += 1
            except Exception:  # noqa: BLE001
                pass
        total_overlap += fire_count

    return total_overlap / len(cases)


def _has_external_vars(scenarios: list[dict[str, Any]], signature: dict[str, Any]) -> bool:
    """Check whether any output definition references input variables not appearing in guards."""
    inputs = {p["name"] for p in signature.get("inputs", signature.get("params", []))}
    guard_vars: set[str] = set()
    for sc in scenarios:
        if sc.get("kind") == "others":
            continue
        for token in re.findall(r"\b[a-zA-Z_]\w*\b", sc.get("test", "")):
            if token in inputs:
                guard_vars.add(token)

    for sc in scenarios:
        def_text = sc.get("def", "")
        def_vars = set(re.findall(r"\b[a-zA-Z_]\w*\b", def_text))
        referenced_inputs = def_vars & inputs
        if referenced_inputs - guard_vars:
            return True
    return False


def compute_task_complexity(task: dict[str, Any]) -> dict[str, Any]:
    """Compute complexity metadata for a single benchmark task.

    Returns a dict with keys:
      scenario_count, guard_complexity, overlap_rate, has_external_vars,
      overlap_density_tier (low/medium/high, set after batch computation)
    """
    scenarios = task.get("fsfScenarios", [])
    signature = task.get("signature", {})

    non_others = [sc for sc in scenarios if sc.get("kind") != "others"]
    scenario_count = len(non_others)

    labels = [_guard_complexity_label(sc.get("test", "")) for sc in non_others]
    guard_complexity = _aggregate_complexity(labels)

    overlap_rate = _count_overlap_samples(scenarios, signature, sample_n=32)
    ext_vars = _has_external_vars(scenarios, signature)

    return {
        "scenario_count": scenario_count,
        "guard_complexity": guard_complexity,
        "overlap_rate": round(overlap_rate, 3),
        "has_external_vars": ext_vars,
        "overlap_density_tier": None,  # assigned by annotate_tasks_complexity
    }


def annotate_tasks_complexity(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compute complexity metadata for all tasks and assign overlap_density_tier.

    Modifies tasks in-place: adds a 'complexity' field to each task dict.
    Returns the annotated task list.
    """
    for task in tasks:
        task["complexity"] = compute_task_complexity(task)

    # Assign overlap density tertile labels based on the full distribution
    rates = [t["complexity"]["overlap_rate"] for t in tasks]
    if rates:
        rates_sorted = sorted(rates)
        n = len(rates_sorted)
        low_cutoff = rates_sorted[n // 3]
        high_cutoff = rates_sorted[2 * n // 3]
        for task in tasks:
            rate = task["complexity"]["overlap_rate"]
            if rate <= low_cutoff:
                task["complexity"]["overlap_density_tier"] = "low"
            elif rate <= high_cutoff:
                task["complexity"]["overlap_density_tier"] = "medium"
            else:
                task["complexity"]["overlap_density_tier"] = "high"

    return tasks
