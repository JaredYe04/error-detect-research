"""Specification and implementation mutation operators for benchmark evaluation."""

from __future__ import annotations

import copy
import random
import re
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class Mutant:
    mutant_id: str
    operator: str
    layer: str  # spec | impl
    task_id: str
    description: str
    payload: dict[str, Any]


SPEC_OPERATORS = [
    ("SNO", "negate_predicate", "Negate FSF test predicate"),
    ("ORO", "swap_relational_op", "Swap relational operator in FSF"),
    ("MCO", "drop_scenario", "Drop one FSF scenario"),
    ("BCO", "weaken_boundary", "Change gt to ge boundary"),
]

IMPL_OPERATORS = [
    ("ICO", "invert_condition", "Invert if condition in implementation"),
    ("WRO", "wrong_return", "Return wrong constant for primary output"),
    ("MBO", "off_by_one", "Off-by-one in comparison"),
    ("DRO", "drop_else", "Remove else branch"),
]


def mutate_spec_scenario(scenarios: list[dict[str, Any]], op: str, rng: random.Random) -> list[dict[str, Any]]:
    scenarios = copy.deepcopy(scenarios)
    if not scenarios:
        return scenarios
    idx = rng.randrange(len(scenarios))
    sc = scenarios[idx]
    test = sc.get("test", "")

    if op == "negate_predicate" and sc.get("kind") != "others":
        sc["test"] = f"not ({test})" if "not" not in test else test.replace("not ", "")
    elif op == "swap_relational_op":
        for a, b in [("gt", "lt"), ("eq", "ne")]:
            if f" {a} " in test:
                sc["test"] = test.replace(f" {a} ", f" {b} ")
                break
    elif op == "drop_scenario":
        scenarios.pop(idx)
        return scenarios
    elif op == "weaken_boundary":
        sc["test"] = test.replace(" gt ", " ge ")
    scenarios[idx] = sc
    return scenarios


def mutate_impl_code(code: str, op: str, task: dict[str, Any], rng: random.Random) -> str:
    outputs = [p["name"] for p in task.get("signature", {}).get("outputs", [])]
    primary = outputs[0] if outputs else "result"

    if op == "invert_condition":
        return re.sub(r"if\s+(.+?):", r"if not (\1):", code, count=1)
    if op == "wrong_return":
        return re.sub(rf"['\"]?{primary}['\"]?\s*:\s*\d+", f"'{primary}': 99", code, count=1)
    if op == "off_by_one":
        return code.replace("> 0", ">= 1", 1)
    if op == "drop_else":
        return re.sub(r"\nelse:.*?(?=\n(?:def |$))", "", code, flags=re.DOTALL)
    return code


def generate_mutants(
    task: dict[str, Any],
    reference_code: str,
    *,
    seed: int = 42,
    spec_ops: bool = True,
    impl_ops: bool = True,
) -> list[Mutant]:
    rng = random.Random(seed)
    mutants: list[Mutant] = []

    if spec_ops:
        for op_id, op_fn, desc in SPEC_OPERATORS:
            mutated = mutate_spec_scenario(task.get("fsfScenarios", []), op_fn, rng)
            mutants.append(
                Mutant(
                    mutant_id=f"{task['taskId']}_spec_{op_id}",
                    operator=op_id,
                    layer="spec",
                    task_id=task["taskId"],
                    description=desc,
                    payload={"fsfScenarios": mutated},
                )
            )

    if impl_ops and reference_code:
        for op_id, op_fn, desc in IMPL_OPERATORS:
            mutated_code = mutate_impl_code(reference_code, op_fn, task, rng)
            mutants.append(
                Mutant(
                    mutant_id=f"{task['taskId']}_impl_{op_id}",
                    operator=op_id,
                    layer="impl",
                    task_id=task["taskId"],
                    description=desc,
                    payload={"code": mutated_code},
                )
            )
    return mutants


def apply_mutant_to_task(task: dict[str, Any], mutant: Mutant) -> dict[str, Any]:
    t = copy.deepcopy(task)
    if mutant.layer == "spec":
        t["fsfScenarios"] = mutant.payload["fsfScenarios"]
    return t
