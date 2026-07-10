"""Regression: others witnesses must not activate higher-priority guards."""

from __future__ import annotations

import json
from pathlib import Path

from src.formal.checker import run_formal_check
from src.formal.fsf_eval import eval_predicate, generate_concrete_cases


def test_others_witnesses_respect_first_match() -> None:
    tasks = json.loads(Path("benchmarks/tasks.json").read_text(encoding="utf-8"))
    task = next(t for t in tasks if t["taskId"].endswith("HardCase001"))
    cases = generate_concrete_cases(task["fsfScenarios"], task["signature"], max_cases=64)
    others = [c for c in cases if c.kind == "others" or c.test_expr == "others"]
    assert others, "expected at least one others witness"
    for case in others:
        for sc in task["fsfScenarios"]:
            if sc.get("kind") == "others":
                continue
            assert not eval_predicate(sc["test"], case.inputs), (
                f"others witness {case.inputs} activates guard {sc['test']}"
            )


def test_reference_code_full_conformance() -> None:
    tasks = json.loads(Path("benchmarks/tasks.json").read_text(encoding="utf-8"))
    task = next(t for t in tasks if t["taskId"].endswith("HardCase001"))
    result = run_formal_check(task["referenceCode"], task, max_cases=64)
    assert result.passed
    assert result.conformance_rate == 1.0
