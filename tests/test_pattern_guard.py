"""Unit tests for PatternGuard fixes: RF05, RF06, RF11, and CFG utilities."""

from __future__ import annotations

import pytest

from src.patterns.cfg import (
    all_paths_define_outputs,
    build_cfg,
    has_empty_branch_bodies,
    has_unreachable_returns,
)
from src.patterns.guard_extract import (
    detect_missing_guards,
    detect_off_by_one,
    detect_swapped_comparisons,
    extract_code_conditions,
    extract_fsf_guards,
)
from src.patterns.matcher import PatternGuard


# ---------------------------------------------------------------------------
# Shared task fixtures
# ---------------------------------------------------------------------------

_TASK_WITH_ZERO_BOUNDARY = {
    "name": "CheckAge",
    "signature": {
        "inputs": [{"name": "age", "type": "nat"}],
        "outputs": [{"name": "valid", "type": "nat"}],
    },
    "fsfScenarios": [
        {"index": 1, "kind": "scenario", "test": "age gt 0", "def": "valid eq 1"},
        {"index": 2, "kind": "scenario", "test": "age eq 0", "def": "valid eq 0"},
        {"index": 3, "kind": "others", "test": "others", "def": "valid eq 0"},
    ],
    "ext": [],
}

_TASK_GE_BOUNDARY = {
    "name": "IsAdult",
    "signature": {
        "inputs": [{"name": "age", "type": "nat"}],
        "outputs": [{"name": "adult", "type": "nat"}],
    },
    "fsfScenarios": [
        {"index": 1, "kind": "scenario", "test": "age ge 18", "def": "adult eq 1"},
        {"index": 2, "kind": "others", "test": "others", "def": "adult eq 0"},
    ],
    "ext": [],
}

_TASK_GT_BOUNDARY = {
    "name": "IsPositive",
    "signature": {
        "inputs": [{"name": "x", "type": "int"}],
        "outputs": [{"name": "result", "type": "nat"}],
    },
    "fsfScenarios": [
        {"index": 1, "kind": "scenario", "test": "x gt 0", "def": "result eq 1"},
        {"index": 2, "kind": "others", "test": "others", "def": "result eq 0"},
    ],
    "ext": [],
}


# ===========================================================================
# guard_extract unit tests
# ===========================================================================

class TestExtractFsfGuards:
    def test_keyword_gt(self):
        scenarios = [{"kind": "scenario", "test": "age gt 0", "def": "valid eq 1"}]
        guards = extract_fsf_guards(scenarios)
        assert ("age", ">", "0") in guards

    def test_keyword_ge(self):
        scenarios = [{"kind": "scenario", "test": "age ge 18", "def": "adult eq 1"}]
        guards = extract_fsf_guards(scenarios)
        assert ("age", ">=", "18") in guards

    def test_keyword_eq(self):
        scenarios = [{"kind": "scenario", "test": "x eq 0", "def": "r eq 0"}]
        guards = extract_fsf_guards(scenarios)
        assert ("x", "==", "0") in guards

    def test_symbol_syntax(self):
        scenarios = [{"kind": "scenario", "test": "x > 5", "def": "r eq 1"}]
        guards = extract_fsf_guards(scenarios)
        assert ("x", ">", "5") in guards

    def test_others_skipped(self):
        scenarios = [{"kind": "others", "test": "others", "def": "r eq 0"}]
        guards = extract_fsf_guards(scenarios)
        assert guards == []

    def test_conjunct_split(self):
        scenarios = [{"kind": "scenario", "test": "x gt 0 && y le 10", "def": "r eq 1"}]
        guards = extract_fsf_guards(scenarios)
        assert ("x", ">", "0") in guards
        assert ("y", "<=", "10") in guards

    def test_multiple_scenarios(self):
        scenarios = [
            {"kind": "scenario", "test": "a gt 0", "def": "r eq 1"},
            {"kind": "scenario", "test": "a eq 0", "def": "r eq 0"},
        ]
        guards = extract_fsf_guards(scenarios)
        assert len(guards) == 2


class TestExtractCodeConditions:
    def test_simple_gt(self):
        code = "def f(x):\n    if x > 0:\n        return 1\n    return 0\n"
        conds = extract_code_conditions(code)
        assert ("x", ">", "0") in conds

    def test_simple_ge(self):
        code = "def f(age):\n    if age >= 18:\n        return 1\n    return 0\n"
        conds = extract_code_conditions(code)
        assert ("age", ">=", "18") in conds

    def test_eq_zero(self):
        code = "def f(x):\n    if x == 0:\n        return 0\n    return 1\n"
        conds = extract_code_conditions(code)
        assert ("x", "==", "0") in conds

    def test_lt_condition(self):
        code = "def f(x):\n    if x < 0:\n        return -1\n    return 0\n"
        conds = extract_code_conditions(code)
        assert ("x", "<", "0") in conds

    def test_no_conditions(self):
        code = "def f(x):\n    return x + 1\n"
        conds = extract_code_conditions(code)
        assert conds == []

    def test_multiple_ifs(self):
        code = (
            "def f(x, y):\n"
            "    if x > 0:\n"
            "        return 1\n"
            "    if y == 0:\n"
            "        return 0\n"
            "    return -1\n"
        )
        conds = extract_code_conditions(code)
        assert ("x", ">", "0") in conds
        assert ("y", "==", "0") in conds


class TestDetectSwappedComparisons:
    def test_gt_swapped_to_lt(self):
        fsf_guards = [("x", ">", "0")]
        code_conds = [("x", "<", "0")]
        violations = detect_swapped_comparisons(fsf_guards, code_conds)
        assert len(violations) == 1
        assert "x" in violations[0]
        assert "<" in violations[0]

    def test_ge_swapped_to_le(self):
        fsf_guards = [("age", ">=", "18")]
        code_conds = [("age", "<=", "18")]
        violations = detect_swapped_comparisons(fsf_guards, code_conds)
        assert len(violations) == 1

    def test_no_swap_correct(self):
        fsf_guards = [("x", ">", "0")]
        code_conds = [("x", ">", "0")]
        violations = detect_swapped_comparisons(fsf_guards, code_conds)
        assert violations == []

    def test_different_var_no_violation(self):
        fsf_guards = [("x", ">", "0")]
        code_conds = [("y", "<", "0")]
        violations = detect_swapped_comparisons(fsf_guards, code_conds)
        assert violations == []

    def test_different_threshold_no_violation(self):
        fsf_guards = [("x", ">", "0")]
        code_conds = [("x", "<", "1")]
        violations = detect_swapped_comparisons(fsf_guards, code_conds)
        assert violations == []


class TestDetectOffByOne:
    def test_ge_vs_gt(self):
        """FSF: age >= 18, code: age > 18 — off-by-one."""
        fsf_guards = [("age", ">=", "18")]
        code_conds = [("age", ">", "18")]
        violations = detect_off_by_one(fsf_guards, code_conds)
        assert len(violations) == 1
        assert "age" in violations[0]
        assert ">" in violations[0]

    def test_gt_vs_ge(self):
        """FSF: x > 0, code: x >= 0 — off-by-one (includes zero)."""
        fsf_guards = [("x", ">", "0")]
        code_conds = [("x", ">=", "0")]
        violations = detect_off_by_one(fsf_guards, code_conds)
        assert len(violations) == 1

    def test_le_vs_lt(self):
        fsf_guards = [("n", "<=", "100")]
        code_conds = [("n", "<", "100")]
        violations = detect_off_by_one(fsf_guards, code_conds)
        assert len(violations) == 1

    def test_correct_ge_no_violation(self):
        fsf_guards = [("age", ">=", "18")]
        code_conds = [("age", ">=", "18")]
        violations = detect_off_by_one(fsf_guards, code_conds)
        assert violations == []

    def test_eq_not_off_by_one(self):
        """== has no strict/non-strict variant — should not flag."""
        fsf_guards = [("x", "==", "0")]
        code_conds = [("x", ">", "0")]
        violations = detect_off_by_one(fsf_guards, code_conds)
        assert violations == []


class TestDetectMissingGuards:
    def test_missing_guard(self):
        fsf_guards = [("x", ">", "0"), ("y", "==", "0")]
        code_conds = [("x", ">", "0")]
        violations = detect_missing_guards(fsf_guards, code_conds)
        assert len(violations) == 1
        assert "y" in violations[0]

    def test_all_present(self):
        fsf_guards = [("x", ">", "0")]
        code_conds = [("x", ">", "0")]
        violations = detect_missing_guards(fsf_guards, code_conds)
        assert violations == []


# ===========================================================================
# cfg.py unit tests
# ===========================================================================

class TestBuildCfg:
    def test_simple_function(self):
        code = "def f(x):\n    return x\n"
        cfg = build_cfg(code)
        assert "nodes" in cfg
        assert "edges" in cfg
        assert len(cfg["nodes"]) >= 2  # entry + return block

    def test_branching_function(self):
        code = (
            "def f(x):\n"
            "    if x > 0:\n"
            "        return 1\n"
            "    return 0\n"
        )
        cfg = build_cfg(code)
        assert len(cfg["exits"]) >= 1
        assert len(cfg["nodes"]) >= 3

    def test_no_function_returns_empty(self):
        cfg = build_cfg("x = 1\n")
        assert cfg["nodes"] == []

    def test_syntax_error_returns_empty(self):
        cfg = build_cfg("def f(:\n    pass\n")
        assert cfg["nodes"] == []


class TestHasUnreachableReturns:
    def test_reachable_return(self):
        code = "def f(x):\n    return x + 1\n"
        cfg = build_cfg(code)
        assert not has_unreachable_returns(cfg)

    def test_empty_cfg(self):
        cfg = {"nodes": [], "edges": [], "entry": 0, "exits": []}
        assert not has_unreachable_returns(cfg)

    def test_all_reachable_branching(self):
        code = (
            "def f(x):\n"
            "    if x > 0:\n"
            "        return 1\n"
            "    return 0\n"
        )
        cfg = build_cfg(code)
        assert not has_unreachable_returns(cfg)


class TestHasEmptyBranchBodies:
    def test_empty_else_pass(self):
        code = (
            "def f(x):\n"
            "    if x > 0:\n"
            "        return 1\n"
            "    else:\n"
            "        pass\n"
        )
        assert has_empty_branch_bodies(code)

    def test_no_empty_branch(self):
        code = (
            "def f(x):\n"
            "    if x > 0:\n"
            "        return 1\n"
            "    else:\n"
            "        return 0\n"
        )
        assert not has_empty_branch_bodies(code)

    def test_no_else(self):
        code = "def f(x):\n    if x > 0:\n        return 1\n"
        assert not has_empty_branch_bodies(code)

    def test_syntax_error(self):
        assert not has_empty_branch_bodies("def f(:\n    pass\n")


class TestAllPathsDefineOutputs:
    def test_all_paths_ok(self):
        code = (
            "def f(x):\n"
            "    if x > 0:\n"
            '        return {"result": 1}\n'
            '    return {"result": 0}\n'
        )
        assert all_paths_define_outputs(code, ["result"])

    def test_missing_key_on_one_path(self):
        code = (
            "def f(x):\n"
            "    if x > 0:\n"
            '        return {"result": 1}\n'
            '    return {"success": 0}\n'
        )
        assert not all_paths_define_outputs(code, ["result"])

    def test_no_output_keys(self):
        code = "def f(x):\n    return {}\n"
        assert all_paths_define_outputs(code, [])

    def test_syntax_error(self):
        assert not all_paths_define_outputs("def f(:\n    pass\n", ["result"])


# ===========================================================================
# PatternGuard integration tests
# ===========================================================================

class TestPatternGuardRF05:
    """RF05: swapped comparison operator."""

    def test_swapped_gt_to_lt_detected(self):
        code = (
            "def IsPositive(x: int) -> dict:\n"
            "    if x < 0:\n"  # FSF says x > 0, code has x < 0
            '        return {"result": 1}\n'
            '    return {"result": 0}\n'
        )
        guard = PatternGuard()
        matches = guard.check(code, _TASK_GT_BOUNDARY)
        ids = [m.pattern_id for m in matches]
        assert "RF05" in ids, f"Expected RF05 in {ids}"

    def test_correct_gt_not_flagged(self):
        code = (
            "def IsPositive(x: int) -> dict:\n"
            "    if x > 0:\n"
            '        return {"result": 1}\n'
            '    return {"result": 0}\n'
        )
        guard = PatternGuard()
        matches = guard.check(code, _TASK_GT_BOUNDARY)
        ids = [m.pattern_id for m in matches]
        assert "RF05" not in ids, f"RF05 should not fire; got {ids}"


class TestPatternGuardRF06:
    """RF06: no guard for zero input when FSF requires one."""

    def test_missing_zero_guard_detected(self):
        code = (
            "def CheckAge(age: int) -> dict:\n"
            "    if age > 0:\n"  # handles gt 0 but not eq 0
            '        return {"valid": 1}\n'
            '    return {"valid": 0}\n'
        )
        guard = PatternGuard()
        matches = guard.check(code, _TASK_WITH_ZERO_BOUNDARY)
        ids = [m.pattern_id for m in matches]
        assert "RF06" in ids, f"Expected RF06 in {ids}"

    def test_zero_guard_present_not_flagged(self):
        code = (
            "def CheckAge(age: int) -> dict:\n"
            "    if age > 0:\n"
            '        return {"valid": 1}\n'
            "    if age == 0:\n"
            '        return {"valid": 0}\n'
            '    return {"valid": 0}\n'
        )
        guard = PatternGuard()
        matches = guard.check(code, _TASK_WITH_ZERO_BOUNDARY)
        ids = [m.pattern_id for m in matches]
        assert "RF06" not in ids, f"RF06 should not fire; got {ids}"

    def test_no_zero_in_fsf_not_flagged(self):
        """When FSF has no zero-boundary, RF06 should not fire."""
        code = (
            "def IsAdult(age: int) -> dict:\n"
            "    if age >= 18:\n"
            '        return {"adult": 1}\n'
            '    return {"adult": 0}\n'
        )
        guard = PatternGuard()
        matches = guard.check(code, _TASK_GE_BOUNDARY)
        ids = [m.pattern_id for m in matches]
        assert "RF06" not in ids, f"RF06 should not fire; got {ids}"


class TestPatternGuardRF11:
    """RF11: off-by-one boundary error."""

    def test_off_by_one_ge_to_gt_detected(self):
        """FSF says age >= 18 but code uses age > 18."""
        code = (
            "def IsAdult(age: int) -> dict:\n"
            "    if age > 18:\n"  # off-by-one: should be >=
            '        return {"adult": 1}\n'
            '    return {"adult": 0}\n'
        )
        guard = PatternGuard()
        matches = guard.check(code, _TASK_GE_BOUNDARY)
        ids = [m.pattern_id for m in matches]
        assert "RF11" in ids, f"Expected RF11 in {ids}"

    def test_correct_ge_not_flagged(self):
        code = (
            "def IsAdult(age: int) -> dict:\n"
            "    if age >= 18:\n"
            '        return {"adult": 1}\n'
            '    return {"adult": 0}\n'
        )
        guard = PatternGuard()
        matches = guard.check(code, _TASK_GE_BOUNDARY)
        ids = [m.pattern_id for m in matches]
        assert "RF11" not in ids, f"RF11 should not fire; got {ids}"

    def test_off_by_one_gt_to_ge_detected(self):
        """FSF says x > 0 but code uses x >= 0 (includes zero when it shouldn't)."""
        code = (
            "def IsPositive(x: int) -> dict:\n"
            "    if x >= 0:\n"  # off-by-one: should be >
            '        return {"result": 1}\n'
            '    return {"result": 0}\n'
        )
        guard = PatternGuard()
        matches = guard.check(code, _TASK_GT_BOUNDARY)
        ids = [m.pattern_id for m in matches]
        assert "RF11" in ids, f"Expected RF11 in {ids}"


class TestPatternGuardRF13:
    """RF13: empty else/pass branch."""

    def test_empty_else_detected(self):
        code = (
            "def CheckAge(age: int) -> dict:\n"
            "    if age > 0:\n"
            '        return {"valid": 1}\n'
            "    else:\n"
            "        pass\n"
        )
        guard = PatternGuard()
        matches = guard.check(code, _TASK_WITH_ZERO_BOUNDARY)
        ids = [m.pattern_id for m in matches]
        assert "RF13" in ids, f"Expected RF13 in {ids}"

    def test_non_empty_else_not_flagged(self):
        code = (
            "def CheckAge(age: int) -> dict:\n"
            "    if age > 0:\n"
            '        return {"valid": 1}\n'
            "    else:\n"
            '        return {"valid": 0}\n'
        )
        guard = PatternGuard()
        matches = guard.check(code, _TASK_WITH_ZERO_BOUNDARY)
        ids = [m.pattern_id for m in matches]
        assert "RF13" not in ids, f"RF13 should not fire; got {ids}"


_TASK_SUCCESS_OUTPUT = {
    "name": "DoAction",
    "signature": {
        "inputs": [{"name": "x", "type": "nat"}],
        "outputs": [{"name": "success", "type": "nat"}],
    },
    "fsfScenarios": [
        {"index": 1, "kind": "scenario", "test": "x gt 0", "def": "success eq 1"},
        {"index": 2, "kind": "others", "test": "others", "def": "success eq 0"},
    ],
    "ext": [],
}


class TestPatternGuardRF07:
    """RF07: unconditional success / unreachable return."""

    def test_unconditional_success_detected(self):
        """Code that always returns success=1 without any conditions."""
        code = (
            "def DoAction(x: int) -> dict:\n"
            '    return {"success": 1}\n'
        )
        guard = PatternGuard()
        matches = guard.check(code, _TASK_SUCCESS_OUTPUT)
        ids = [m.pattern_id for m in matches]
        assert "RF07" in ids, f"Expected RF07 in {ids}"


class TestPatternGuardPassed:
    """Smoke test for the passed() helper."""

    def test_good_code_passes(self):
        code = (
            "def IsAdult(age: int) -> dict:\n"
            '    """Reference implementation auto-generated from FSF."""\n'
            "    if age >= 18:\n"
            '        return {"adult": 1}\n'
            "    else:\n"
            '        return {"adult": 0}\n'
        )
        guard = PatternGuard()
        assert guard.passed(code, _TASK_GE_BOUNDARY, max_high=2)

    def test_bad_code_fails(self):
        code = (
            "def IsAdult(age: int) -> dict:\n"
            '    return {"adult": 1}\n'
        )
        guard = PatternGuard()
        assert not guard.passed(code, _TASK_GE_BOUNDARY, max_high=0)
