"""Unit tests for formal checker and pattern guard."""

from __future__ import annotations

import pytest

from src.formal.checker import run_formal_check
from src.formal.fsf_eval import eval_predicate, generate_concrete_cases
from src.patterns.matcher import PatternGuard


BORROW_TASK = {
    "taskId": "SYSTEM_Library.Borrow",
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


GOOD_CODE = '''
def Borrow(member_id: int, book_id: int) -> dict:
    if member_id > 0:
        return {"success": 1}
    if book_id == 0:
        return {"success": 0}
    return {"success": 0}
'''

BAD_CODE = '''
def Borrow(member_id: int, book_id: int) -> dict:
    return {"success": 1}
'''


def test_eval_predicate():
    assert eval_predicate("member_id gt 0", {"member_id": 1, "book_id": 0})
    assert not eval_predicate("member_id gt 0", {"member_id": 0, "book_id": 0})


def test_generate_cases():
    cases = generate_concrete_cases(BORROW_TASK["fsfScenarios"], BORROW_TASK["signature"])
    assert len(cases) >= 1


def test_formal_check_pass():
    result = run_formal_check(GOOD_CODE, BORROW_TASK)
    assert result.passed
    assert result.conformance_rate == 1.0


def test_formal_check_fail():
    result = run_formal_check(BAD_CODE, BORROW_TASK)
    assert not result.passed
    assert result.counterexamples


def test_pattern_guard_detects_unconditional_success():
    guard = PatternGuard()
    matches = guard.check(BAD_CODE, BORROW_TASK)
    assert any(m.name == "unconditional_success" for m in matches)
