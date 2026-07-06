"""Tests for mutation operators and reference generation."""

from __future__ import annotations

from src.benchmarks.reference_gen import generate_reference_code, validate_reference
from src.formal.checker import run_formal_check
from src.mutation.injectors import generate_mutants

TASK = {
    "taskId": "TEST.Borrow",
    "name": "Borrow",
    "signature": {
        "inputs": [{"name": "member_id", "type": "nat"}, {"name": "book_id", "type": "nat"}],
        "outputs": [{"name": "success", "type": "nat"}],
    },
    "fsfScenarios": [
        {"index": 1, "kind": "scenario", "test": "member_id gt 0", "def": "success eq 1"},
        {"index": 2, "kind": "scenario", "test": "book_id eq 0", "def": "success eq 0"},
        {"index": 3, "kind": "others", "test": "others", "def": "success eq 0"},
    ],
    "ext": [],
}


def test_reference_gen_validates():
    code = generate_reference_code(TASK)
    assert validate_reference(TASK, code)


def test_mutants_detectable():
    code = generate_reference_code(TASK)
    mutants = generate_mutants(TASK, code, seed=1)
    assert len(mutants) >= 4
    killed = 0
    for m in mutants:
        if m.layer == "spec":
            from src.mutation.injectors import apply_mutant_to_task
            mt = apply_mutant_to_task(TASK, m)
            if not run_formal_check(code, mt).passed:
                killed += 1
        else:
            if not run_formal_check(m.payload["code"], TASK).passed:
                killed += 1
    assert killed > 0
