"""Unit tests for Semantic Feedback IR field-ablation render variants."""

from __future__ import annotations

from src.repair.feedback_ir import FeedbackRenderer, SemanticFeedback


def _rec() -> SemanticFeedback:
    return SemanticFeedback(
        violation_type="ordering",
        scenario_index=1,
        constraint_text="level < 0",
        inputs={"level": -3, "threshold": -10},
        expected={"alert": "Error"},
        observed={"alert": "Critical"},
        reason="Scenario 1 violated under first-match guard precedence.",
        priority=1,
        suggested_fix="reorder guard evaluation",
    )


def test_field_ablation_variants_registered() -> None:
    for v in (
        "ir_no_scenario_id",
        "ir_no_expected",
        "ir_no_constraint",
        "ir_no_reason",
        "ir_no_suggested_fix",
        "ir_nl_only",
    ):
        assert v in FeedbackRenderer.VARIANTS


def test_ir_no_scenario_id_hides_index() -> None:
    text = FeedbackRenderer.render([_rec()], "ir_no_scenario_id")
    assert "Scenario 1" not in text
    assert "level < 0" in text


def test_ir_no_expected_omits_expected() -> None:
    text = FeedbackRenderer.render([_rec()], "ir_no_expected")
    assert "expected=" not in text
    assert "observed=" in text


def test_ir_no_constraint_omits_guard() -> None:
    text = FeedbackRenderer.render([_rec()], "ir_no_constraint")
    assert "level < 0" not in text
    assert "Scenario 1" in text


def test_ir_nl_only_is_prose() -> None:
    text = FeedbackRenderer.render([_rec()], "ir_nl_only")
    assert "fix hint:" not in text
    assert "Error" in text and "Critical" in text
