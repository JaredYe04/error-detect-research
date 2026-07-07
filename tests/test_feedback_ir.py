"""Tests for Semantic Feedback IR and FeedbackRenderer."""

from __future__ import annotations

from src.formal.checker import Counterexample
from src.pipeline.runner import build_repair_feedback, resolve_feedback_variant, PipelineConfig
from src.repair.feedback_ir import FeedbackRenderer, SemanticFeedback, SemanticFeedbackIR


def test_semantic_feedback_json_round_trip():
    rec = SemanticFeedback(
        violation_type="ordering",
        scenario_index=1,
        constraint_text="a gt 5",
        inputs={"a": 6},
        expected={"out": 1},
        observed={"out": 2},
        reason="first-match violation",
        priority=1,
        suggested_fix="reorder",
    )
    restored = SemanticFeedback.from_json(rec.to_json())
    assert restored.violation_type == "ordering"
    assert restored.constraint_text == "a gt 5"
    assert restored.suggested_fix == "reorder"


def test_feedback_renderer_variants_differ():
    records = [
        SemanticFeedback(
            violation_type="output",
            scenario_index=2,
            constraint_text="b le 3",
            inputs={"b": 2},
            expected={"y": 10},
            observed={"y": 9},
            reason="output mismatch",
            priority=1,
        )
    ]
    a = FeedbackRenderer.render(records, variant="test_only")
    b = FeedbackRenderer.render(records, variant="test_expected")
    c = FeedbackRenderer.render(records, variant="semantic_ir")
    assert "expected" not in a
    assert "expected" in b
    assert "Scenario 2" in c
    assert a != c


def test_from_counterexamples_uses_task_guard():
    task = {
        "fsfScenarios": [
            {"index": 1, "test": "a gt 5", "def": "out eq 1"},
        ]
    }
    cx = Counterexample(
        scenario_index=1,
        inputs={"a": 6},
        expected={"out": 1},
        actual={"out": 2},
        message="FSF scenario 1 violated",
    )
    ir = SemanticFeedbackIR.from_counterexamples([cx], task=task)
    assert ir.records[0].constraint_text == "a gt 5"
    assert ir.records[0].violation_type in {"output", "unknown", "ordering"}


def test_build_repair_feedback_returns_json_then_prompt():
    task = {"fsfScenarios": [{"index": 1, "test": "a gt 5", "def": "out eq 1"}]}
    cx = Counterexample(
        scenario_index=1,
        inputs={"a": 6},
        expected={"out": 1},
        actual={"out": 2},
        message="FSF scenario 1 violated",
    )
    prompt, feedback_json = build_repair_feedback(task, [cx], variant="semantic_ir")
    assert len(feedback_json) == 1
    assert feedback_json[0]["scenario_index"] == 1
    assert "Semantic Feedback IR" in prompt


def test_resolve_feedback_variant_by_mode():
    assert resolve_feedback_variant(PipelineConfig(mode="B2")) == "test_only"
    assert resolve_feedback_variant(PipelineConfig(mode="M")) == "semantic_ir"
    cfg = PipelineConfig(mode="M", feedback_variant="test_only")
    assert resolve_feedback_variant(cfg) == "test_only"
