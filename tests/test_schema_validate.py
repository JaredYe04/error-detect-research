"""JSON Schema validation for SpecIR and Semantic Feedback IR."""

from __future__ import annotations

import pytest

from src.ir.schema_validate import validate_semantic_feedback, validate_spec_ir
from src.ir.spec_ir import GuardAtom, GuardedCase, Param, SpecIR
from src.repair.feedback_ir import SemanticFeedback


def test_validate_spec_ir_round_trip():
    spec = SpecIR(
        task_id="T1",
        notation="mini_z",
        name="f",
        inputs=[Param("x", "nat")],
        outputs=[Param("y", "nat")],
        cases=[
            GuardedCase(1, [GuardAtom("x", "gt", 0)], {"y": 1}),
            GuardedCase(2, [GuardAtom("", "others")], {"y": 0}),
        ],
        surface_prompt="test",
    )
    validate_spec_ir(spec.to_dict())


def test_validate_semantic_feedback_record():
    rec = SemanticFeedback(
        violation_type="ordering",
        scenario_index=1,
        constraint_text="a gt 5",
        inputs={"a": 6},
        expected={"out": 1},
        observed={"out": 2},
        reason="precedence violation",
        priority=1,
        suggested_fix="reorder",
    )
    validate_semantic_feedback(rec.to_json())


def test_validate_semantic_feedback_rejects_invalid_type():
    pytest.importorskip("jsonschema")
    with pytest.raises(Exception):
        validate_semantic_feedback({
            "violation_type": "not_a_type",
            "scenario_index": 1,
            "constraint_text": "x",
            "inputs": {},
            "expected": {},
            "observed": {},
            "reason": "x",
            "priority": 1,
        })
