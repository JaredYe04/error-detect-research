"""Generate difficult synthetic tasks for Agile-SOFL error-prevention studies."""

from __future__ import annotations

import random
from typing import Any

from src.benchmarks.reference_gen import generate_reference_code


def _mk_signature() -> dict[str, Any]:
    return {
        "inputs": [
            {"name": "a", "type": "nat"},
            {"name": "b", "type": "nat"},
            {"name": "c", "type": "nat"},
            {"name": "d", "type": "nat"},
            {"name": "e", "type": "nat"},
        ],
        "outputs": [
            {"name": "risk", "type": "nat"},
            {"name": "action", "type": "nat"},
            {"name": "score", "type": "nat"},
        ],
    }


def _render_prompt(task_name: str, scenarios: list[dict[str, Any]]) -> str:
    lines = [f"Process {task_name}(a,b,c,d,e) -> (risk,action,score)", "", "FSF specification:"]
    for sc in scenarios:
        if sc["kind"] == "others":
            lines.append(f"others => {sc['def']}")
        else:
            lines.append(f"if ({sc['test']}) => {sc['def']}")
    lines.append("")
    lines.append("Important: evaluate conditions in listed order (top-down precedence).")
    return "\n".join(lines)


def _mk_scenarios(rng: random.Random, *, scenarios_per_task: int) -> list[dict[str, Any]]:
    t1 = rng.randint(2, 8)
    t2 = rng.randint(3, 10)
    t3 = rng.randint(2, 7)
    t4 = rng.randint(1, 6)
    t5 = rng.randint(4, 12)
    t6 = rng.randint(2, 8)
    t7 = rng.randint(3, 9)

    candidates: list[tuple[str, str]] = [
        (
            f"a gt {t1} && b gt {t2} && c gt {t3}",
            "risk eq 3 && action eq 4 && score eq a",
        ),
        (
            f"a gt {t1} && b gt {t2} && c le {t3}",
            "risk eq 2 && action eq 3 && score eq b",
        ),
        (
            f"a gt {t1} && b le {t2} && d gt {t4}",
            "risk eq 2 && action eq 2 && score eq d",
        ),
        (
            f"a le {t1} && e gt {t5} && c gt {t3}",
            "risk eq 1 && action eq 2 && score eq e",
        ),
        (
            f"b gt {t2} && d gt {t4} && e le {t5}",
            "risk eq 1 && action eq 1 && score eq b",
        ),
        (
            f"c gt {t6} && d gt {t7}",
            "risk eq 2 && action eq 1 && score eq c",
        ),
        (
            f"a eq 0 && b eq 0",
            "risk eq 0 && action eq 5 && score eq 0",
        ),
        (
            f"e gt {t5} && d le {t4}",
            "risk eq 1 && action eq 3 && score eq e",
        ),
        (
            f"c le {t3} && b le {t2}",
            "risk eq 0 && action eq 2 && score eq c",
        ),
    ]
    rng.shuffle(candidates)
    chosen = candidates[: max(2, min(scenarios_per_task - 1, len(candidates)))]
    scenarios: list[dict[str, Any]] = []
    for idx, (test, definition) in enumerate(chosen, start=1):
        scenarios.append({"index": idx, "kind": "scenario", "test": test, "def": definition})
    scenarios.append(
        {
            "index": len(scenarios) + 1,
            "kind": "others",
            "test": "others",
            "def": "risk eq 0 && action eq 0 && score eq 0",
        }
    )
    return scenarios


def generate_hard_tasks(
    *,
    n_tasks: int = 160,
    scenarios_per_task: int = 8,
    seed: int = 42,
) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    tasks: list[dict[str, Any]] = []
    for i in range(1, n_tasks + 1):
        name = f"HardCase{i:03d}"
        task_id = f"HardSynthetic.{name}"
        scenarios = _mk_scenarios(rng, scenarios_per_task=scenarios_per_task)
        task: dict[str, Any] = {
            "taskId": task_id,
            "kind": "process",
            "sourceFile": "synthetic://hard-generator",
            "module": "HardSynthetic",
            "name": name,
            "signature": _mk_signature(),
            "fsfScenarios": scenarios,
            "ext": [],
            "promptSpec": _render_prompt(name, scenarios),
            "sourceBasename": "synthetic-hard",
        }
        task["referenceCode"] = generate_reference_code(task)
        tasks.append(task)
    return tasks

