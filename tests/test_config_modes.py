"""Unit tests for pipeline mode configuration (REV-0)."""

from __future__ import annotations

from src.pipeline.runner import config_for_mode


def test_b3_differs_from_m() -> None:
    b3 = config_for_mode("B3")
    m = config_for_mode("M")
    assert b3.enable_formal is False
    assert b3.enable_patterns is False
    assert b3.feedback_variant == "self_critique"
    assert m.enable_formal is True
    assert m.enable_patterns is True
    assert m.feedback_variant == "execution_trace_matched"


def test_b4_execution_trace() -> None:
    b4 = config_for_mode("B4")
    b2 = config_for_mode("B2")
    assert b4.feedback_variant == "execution_trace"
    assert b2.feedback_variant == "test_only"
    assert b4.enable_formal is False


def test_b5_reflexion_budget() -> None:
    b5 = config_for_mode("B5")
    m = config_for_mode("M")
    assert b5.feedback_variant == "reflexion"
    assert b5.max_attempts == 3
    assert m.max_attempts == 5
    assert b5.enable_formal is False
    assert b5.enable_patterns is False


def test_b6_verifier_loop_fsf() -> None:
    b6 = config_for_mode("B6")
    m = config_for_mode("M")
    a2 = config_for_mode("A2")
    b2 = config_for_mode("B2")
    assert b6.enable_formal is True
    assert b6.enable_patterns is False
    assert b6.enable_repair is True
    assert b6.feedback_variant == "verifier_loop"
    assert b6.max_attempts == 3
    assert m.max_attempts == 5
    assert b6.formal_max_cases == 24
    assert m.formal_max_cases == 32
    assert a2.enable_formal is True and a2.enable_patterns is False
    assert a2.feedback_variant != "verifier_loop"
    assert b2.enable_formal is False
    assert b2.feedback_variant == "test_only"


def test_m_adv_advisory_pattern_guard() -> None:
    adv = config_for_mode("M_adv")
    m = config_for_mode("M")
    hard = config_for_mode("M_hard")
    assert adv.pattern_guard_mode == "advisory"
    assert m.pattern_guard_mode == "advisory"
    assert hard.pattern_guard_mode == "hard"
    assert m.feedback_variant == "execution_trace_matched"
    assert hard.feedback_variant == "semantic_ir"


def test_b4m_execution_trace_matched() -> None:
    b4m = config_for_mode("B4M")
    b4 = config_for_mode("B4")
    assert b4m.feedback_variant == "execution_trace_matched"
    assert b4.feedback_variant == "execution_trace"
    assert "execution_trace_matched" in __import__(
        "src.repair.feedback_ir", fromlist=["FeedbackRenderer"]
    ).FeedbackRenderer.VARIANTS


def test_m_lite_witness_plus_semantic_ir() -> None:
    lite = config_for_mode("M_lite")
    b6 = config_for_mode("B6")
    m = config_for_mode("M")
    assert lite.enable_formal is True
    assert lite.enable_patterns is False
    assert lite.feedback_variant == "semantic_ir"
    assert b6.feedback_variant == "verifier_loop"
    assert m.enable_patterns is True
    assert m.feedback_variant == "execution_trace_matched"


def test_m_eq_equal_k_hygiene() -> None:
    """M_eq matches B2 budget (K=3) for Conf ranking claims."""
    meq = config_for_mode("M_eq")
    b2 = config_for_mode("B2")
    m = config_for_mode("M")
    assert meq.max_attempts == b2.max_attempts == 3
    assert meq.enable_formal is True
    assert meq.feedback_variant == "semantic_ir"
    assert meq.pattern_guard_mode == "advisory"
    assert m.max_attempts == 5


def test_a1_a2_a3_ablate_strengthened_m() -> None:
    """Fixed-oracle ablations share M's budget/feedback except the removed knob."""
    m = config_for_mode("M")
    a1 = config_for_mode("A1")
    a2 = config_for_mode("A2")
    a3 = config_for_mode("A3")
    assert a1.enable_formal is False and a1.enable_patterns and a1.enable_repair
    assert a2.enable_formal and a2.enable_patterns is False and a2.enable_repair
    assert a3.enable_formal and a3.enable_patterns and a3.enable_repair is False
    assert a1.max_attempts == m.max_attempts == 5
    assert a2.max_attempts == 5
    assert a3.max_attempts == 1
    assert a1.formal_max_cases == a2.formal_max_cases == a3.formal_max_cases == 32
    assert a1.feedback_variant == a2.feedback_variant == m.feedback_variant
    assert a3.pattern_guard_mode == "advisory"
