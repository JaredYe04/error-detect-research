"""Semantic Feedback Intermediate Representation.

SemanticFeedback is a machine-readable IR for specification-level conformance
violations.  It is constructed once by the formal checker and can be serialised
to/from JSON (schema: schemas/semantic_feedback.schema.json).

Three rendering variants project the IR onto natural-language repair prompts:
  - 'test_only':     inputs + observed output only  (ablation B2)
  - 'test_expected': inputs + observed + expected    (ablation A1/A2)
  - 'semantic_ir':   full 9-field IR                (mode M, default)

FeedbackRenderer is kept separate from SemanticFeedbackIR to prove that the IR
is a genuine machine-readable artifact, not merely a prompt template.
SemanticFeedbackIR.render() delegates to FeedbackRenderer internally so that
existing call sites (e.g. runner.py) continue to work without modification.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Core IR dataclass
# ---------------------------------------------------------------------------

@dataclass
class SemanticFeedback:
    """One specification-level conformance violation.

    Fields correspond 1-to-1 with schemas/semantic_feedback.schema.json.
    """

    violation_type: str          # "ordering" | "boundary" | "arithmetic" | "output" | "unknown"
    scenario_index: int          # 1-indexed FSF scenario
    constraint_text: str         # guard predicate as human-readable text
    inputs: dict[str, Any]       # concrete witness inputs
    expected: dict[str, Any]     # oracle output
    observed: dict[str, Any]     # candidate actual output
    reason: str                  # inferred natural-language root cause
    priority: int                # severity rank (1 = highest)
    suggested_fix: str | None = field(default=None)  # optional structural hint

    # ------------------------------------------------------------------
    # JSON serialisation
    # ------------------------------------------------------------------

    def to_json(self) -> dict[str, Any]:
        """Return a schema-compliant dict (schemas/semantic_feedback.schema.json)."""
        d: dict[str, Any] = {
            "violation_type": self.violation_type,
            "scenario_index": self.scenario_index,
            "constraint_text": self.constraint_text,
            "inputs": self.inputs,
            "expected": self.expected,
            "observed": self.observed,
            "reason": self.reason,
            "priority": self.priority,
        }
        if self.suggested_fix is not None:
            d["suggested_fix"] = self.suggested_fix
        try:
            from src.ir.schema_validate import validate_semantic_feedback
            validate_semantic_feedback(d)
        except ImportError:
            pass
        return d

    @classmethod
    def from_json(cls, d: dict[str, Any]) -> SemanticFeedback:
        """Reconstruct a SemanticFeedback from a schema-compliant dict."""
        return cls(
            violation_type=d["violation_type"],
            scenario_index=d["scenario_index"],
            constraint_text=d["constraint_text"],
            inputs=d["inputs"],
            expected=d["expected"],
            observed=d["observed"],
            reason=d["reason"],
            priority=d["priority"],
            suggested_fix=d.get("suggested_fix"),
        )


# ---------------------------------------------------------------------------
# Renderer (separated from IR — proves IR is machine-readable, not a template)
# ---------------------------------------------------------------------------

class FeedbackRenderer:
    """Renders a list of SemanticFeedback records to a repair prompt string.

    The IR (SemanticFeedback) is constructed once; the renderer projects it onto
    different natural-language surfaces depending on the ablation variant:
      - 'test_only':     inputs + observed output only
      - 'test_expected': inputs + observed + expected
      - 'semantic_ir':   full 9-field IR (default for mode M)

    This separation proves that the Semantic Feedback IR is a machine-readable
    intermediate representation, not merely a prompt template.
    """

    VARIANTS = ("test_only", "test_expected", "semantic_ir")

    @staticmethod
    def render(records: list[SemanticFeedback], variant: str = "semantic_ir") -> str:
        """Render IR records to a repair prompt string."""
        if variant == "test_only":
            return FeedbackRenderer._render_test_only(records)
        elif variant == "test_expected":
            return FeedbackRenderer._render_test_expected(records)
        else:
            return FeedbackRenderer._render_full(records)

    @staticmethod
    def _render_test_only(records: list[SemanticFeedback]) -> str:
        lines = ["Counterexamples:"]
        for r in records:
            lines.append(f"  inputs={r.inputs} → observed={r.observed}")
        return "\n".join(lines)

    @staticmethod
    def _render_test_expected(records: list[SemanticFeedback]) -> str:
        lines = ["Counterexamples:"]
        for r in records:
            lines.append(f"  inputs={r.inputs} → observed={r.observed}, expected={r.expected}")
        return "\n".join(lines)

    @staticmethod
    def _render_full(records: list[SemanticFeedback]) -> str:
        lines = ["Specification-level violations (Semantic Feedback IR):"]
        for r in records:
            lines.append(f"  [{r.violation_type}] Scenario {r.scenario_index}: {r.constraint_text}")
            lines.append(f"    inputs={r.inputs}")
            lines.append(f"    expected={r.expected}, observed={r.observed}")
            lines.append(f"    reason: {r.reason}")
            if r.suggested_fix:
                lines.append(f"    fix hint: {r.suggested_fix}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Aggregate IR container (preserves existing API surface)
# ---------------------------------------------------------------------------

class SemanticFeedbackIR:
    """Container for a list of SemanticFeedback records for one repair iteration.

    Delegates rendering to FeedbackRenderer so that call sites using
    ``ir.render(variant=...)`` continue to work unchanged.
    """

    def __init__(self, records: list[SemanticFeedback]) -> None:
        self.records = records

    # ------------------------------------------------------------------
    # Existing API — kept for backwards compatibility with runner.py
    # ------------------------------------------------------------------

    def render(self, variant: str = "semantic_ir") -> str:
        """Render to repair prompt string (delegates to FeedbackRenderer)."""
        return FeedbackRenderer.render(self.records, variant=variant)

    # ------------------------------------------------------------------
    # Convenience constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_counterexamples(
        cls,
        counterexamples: list[Any],
        *,
        task: dict[str, Any] | None = None,
        violation_type: str | None = None,
        constraint_text: str = "",
        reason: str | None = None,
    ) -> SemanticFeedbackIR:
        """Build a SemanticFeedbackIR from checker Counterexample objects or dicts."""
        records: list[SemanticFeedback] = []
        for idx, cx in enumerate(counterexamples, start=1):
            if hasattr(cx, "scenario_index"):
                scenario_index = cx.scenario_index
                inputs = cx.inputs
                expected = cx.expected
                observed = cx.actual
                message = cx.message
            else:
                scenario_index = cx.get("scenario_index", idx)
                inputs = cx.get("inputs", {})
                expected = cx.get("expected", {})
                observed = cx.get("actual", cx.get("observed", {}))
                message = cx.get("message", "")

            guard_text = constraint_text
            if task and not guard_text:
                scenarios = task.get("fsfScenarios", [])
                if 1 <= scenario_index <= len(scenarios):
                    guard_text = scenarios[scenario_index - 1].get("test", "")

            vtype, inferred_reason, fix = _classify_violation(
                message=message,
                expected=expected,
                observed=observed,
                scenario_index=scenario_index,
            )
            records.append(
                SemanticFeedback(
                    violation_type=violation_type or vtype,
                    scenario_index=scenario_index,
                    constraint_text=guard_text or message,
                    inputs=inputs,
                    expected=expected,
                    observed=observed,
                    reason=reason or inferred_reason,
                    priority=idx,
                    suggested_fix=fix,
                )
            )
        return cls(records)

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    def to_json_list(self) -> list[dict[str, Any]]:
        """Return a list of schema-compliant dicts (one per record)."""
        return [r.to_json() for r in self.records]

    @classmethod
    def from_json_list(cls, data: list[dict[str, Any]]) -> SemanticFeedbackIR:
        """Reconstruct from a list of schema-compliant dicts."""
        return cls([SemanticFeedback.from_json(d) for d in data])


def _classify_violation(
    *,
    message: str,
    expected: dict[str, Any],
    observed: dict[str, Any],
    scenario_index: int,
) -> tuple[str, str, str | None]:
    """Heuristic violation classifier for Semantic Feedback IR records."""
    msg = (message or "").lower()
    if "ordering" in msg or "precedence" in msg or "first-match" in msg:
        return (
            "ordering",
            f"Scenario {scenario_index} violated under first-match guard precedence.",
            "reorder guard evaluation to match specification precedence",
        )
    if "boundary" in msg or "threshold" in msg or "off-by" in msg:
        return (
            "boundary",
            f"Boundary witness for scenario {scenario_index} exposed a threshold mismatch.",
            "adjust boundary comparison to match guard threshold",
        )
    if expected and observed and expected != observed:
        exp_keys = set(expected.keys())
        obs_keys = set(observed.keys())
        if exp_keys != obs_keys:
            return (
                "output",
                f"Scenario {scenario_index}: output field mismatch ({obs_keys} vs {exp_keys}).",
                "return all required output fields for the active scenario",
            )
        numeric_delta = any(
            isinstance(expected.get(k), (int, float))
            and isinstance(observed.get(k), (int, float))
            and abs(float(expected[k]) - float(observed[k])) > 1
            for k in exp_keys
        )
        if numeric_delta:
            return (
                "arithmetic",
                f"Scenario {scenario_index}: arithmetic expression inconsistent with oracle.",
                "correct the output expression for the active scenario",
            )
        return (
            "output",
            f"Scenario {scenario_index}: observed output differs from oracle.",
            "align output assignment with the active scenario postcondition",
        )
    return (
        "unknown",
        "Formal conformance violation detected by SMT-generated witness.",
        None,
    )
