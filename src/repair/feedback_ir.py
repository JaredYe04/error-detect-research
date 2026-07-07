"""Scenario-aware Semantic Feedback IR for counterexample-guided repair.

This module implements Contribution C2 of the SgDP framework:
a typed eight-field intermediate representation that decomposes a conformance
failure at the specification level rather than the test-case level.

The IR enables controlled ablation (E6) by selectively rendering subsets of fields:
  - Variant A (test_only):     inputs + observed
  - Variant B (test_expected): inputs + observed + expected
  - Variant C (semantic_ir):   all eight fields (default for mode M)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# Violation types in order of semantic severity (highest priority first)
VIOLATION_TYPES = ("ordering", "boundary", "arithmetic", "output", "unknown")

_ORDERING_KEYWORDS = ("scenario", "order", "preceden", "priority", "guard")
_BOUNDARY_KEYWORDS = ("boundary", "border", "edge", "adjacent", "overlap")
_ARITHMETIC_KEYWORDS = ("arith", "sum", "mul", "div", "overflow", "underflow")


@dataclass
class SemanticFeedback:
    """One specification-level violation record.

    Fields map directly to the IR defined in the paper (Section 3.4):
      violation_type  : classification of the defect
      scenario_index  : the violated FSF scenario (1-indexed)
      constraint_text : the guard predicate as human-readable text
      inputs          : concrete witness inputs that expose the fault
      expected        : oracle output for those inputs
      observed        : candidate's actual output
      reason          : inferred natural-language root cause
      priority        : numeric severity (1 = highest)
      suggested_fix   : structural code change category (may be None)
    """
    violation_type: str
    scenario_index: int
    constraint_text: str
    inputs: dict[str, int]
    expected: dict[str, int]
    observed: dict[str, int]
    reason: str
    priority: int
    suggested_fix: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "violation_type": self.violation_type,
            "scenario_index": self.scenario_index,
            "constraint_text": self.constraint_text,
            "inputs": self.inputs,
            "expected": self.expected,
            "observed": self.observed,
            "reason": self.reason,
            "priority": self.priority,
            "suggested_fix": self.suggested_fix,
        }

    def render_test_only(self) -> str:
        """Variant A: inputs + observed only."""
        return (
            f"Scenario {self.scenario_index} failed. "
            f"Inputs: {self.inputs}. "
            f"Your output: {self.observed}."
        )

    def render_test_expected(self) -> str:
        """Variant B: inputs + observed + expected."""
        return (
            f"Scenario {self.scenario_index} failed. "
            f"Inputs: {self.inputs}. "
            f"Expected: {self.expected}. "
            f"Your output: {self.observed}."
        )

    def render_semantic_ir(self) -> str:
        """Variant C: full Semantic Feedback IR."""
        lines = [
            f"[{self.violation_type.upper()} VIOLATION] Scenario {self.scenario_index} "
            f"(priority rank: {self.priority})",
            f"  Guard condition: {self.constraint_text}",
            f"  Witness inputs:  {self.inputs}",
            f"  Expected output: {self.expected}",
            f"  Observed output: {self.observed}",
            f"  Root cause:      {self.reason}",
        ]
        if self.suggested_fix:
            lines.append(f"  Suggested fix:   {self.suggested_fix}")
        return "\n".join(lines)


def _classify_violation(
    scenario_index: int,
    guard_text: str,
    inputs: dict[str, int],
    expected: dict[str, int],
    observed: dict[str, int],
    all_scenarios: list[dict[str, Any]],
) -> tuple[str, str, str | None]:
    """Infer violation type, reason, and suggested fix from counterexample context.

    Returns (violation_type, reason, suggested_fix).
    """
    # Check if this looks like an ordering violation: another scenario's output matched
    obs_vals = set(observed.values()) if observed else set()
    for i, sc in enumerate(all_scenarios):
        if i == scenario_index - 1 or sc.get("kind") == "others":
            continue
        # If observed output matches what another scenario would produce, likely ordering
        def_str = sc.get("def", "")
        for out_key, out_val in expected.items():
            if str(out_val) in def_str and obs_vals:
                pass  # inconclusive without executing

    # Heuristic: if guard text contains overlapping conditions likely ordering issue
    g = guard_text.lower()
    if any(kw in g for kw in _ORDERING_KEYWORDS):
        vtype = "ordering"
        reason = (
            f"The implementation evaluated scenario {scenario_index}'s guard in the wrong "
            f"order. Under FSF first-match semantics, higher-priority scenarios must be "
            f"evaluated before scenario {scenario_index}."
        )
        fix = "Ensure all higher-priority scenario guards are checked before this scenario's guard."
        return vtype, reason, fix

    # Check if it could be a boundary issue (observed differs by small amount from expected)
    if expected and observed:
        for k in expected:
            if k in observed:
                diff = abs(expected[k] - observed.get(k, 0))
                if 0 < diff <= 2:
                    vtype = "boundary"
                    reason = (
                        f"Output '{k}' is off by {diff} from expected. "
                        f"This suggests a boundary condition error in the guard for scenario {scenario_index}."
                    )
                    fix = f"Check the boundary condition in scenario {scenario_index}'s guard predicate."
                    return vtype, reason, fix

    # Check arithmetic pattern
    any_arith = any(op in guard_text for op in ("+", "-", "*", "/", "%"))
    if any_arith:
        vtype = "arithmetic"
        reason = (
            f"Arithmetic in scenario {scenario_index}'s guard may be evaluated incorrectly. "
            f"Check integer division, overflow, or operator precedence."
        )
        fix = "Verify arithmetic expressions in guard match the FSF specification precisely."
        return vtype, reason, fix

    # Default: output mismatch
    vtype = "output"
    reason = (
        f"Scenario {scenario_index} postcondition not satisfied: "
        f"expected {expected} but got {observed}."
    )
    fix = "Review the output assignment logic for this scenario."
    return vtype, reason, fix


class SemanticFeedbackIR:
    """Constructs Semantic Feedback IR records from formal checker counterexamples.

    Usage:
        ir = SemanticFeedbackIR(task)
        prompt_text = ir.render(counterexamples)  # uses full semantic_ir variant
        prompt_text = ir.render(counterexamples, variant="test_expected")
    """

    def __init__(self, task: dict[str, Any]) -> None:
        self.task = task
        self._scenarios = task.get("fsfScenarios", [])
        self._scenario_map = {
            sc["index"]: sc for sc in self._scenarios if sc.get("kind") != "others"
        }

    def _get_guard_text(self, scenario_index: int) -> str:
        sc = self._scenario_map.get(scenario_index)
        if sc:
            return sc.get("test", f"scenario_{scenario_index}_guard")
        return f"scenario_{scenario_index}_guard"

    def _get_priority(self, violation_type: str) -> int:
        """Higher priority (lower number) for more semantically severe violations."""
        return VIOLATION_TYPES.index(violation_type) + 1

    def build(self, counterexamples: list[Any]) -> list[SemanticFeedback]:
        """Convert raw Counterexample objects or dicts to SemanticFeedback records."""
        records: list[SemanticFeedback] = []
        for cx in counterexamples[:5]:  # limit to top 5
            if isinstance(cx, dict):
                idx = cx.get("scenario_index", 0)
                inputs = cx.get("inputs", {})
                expected = cx.get("expected", {})
                observed = cx.get("actual", {})
            else:
                idx = getattr(cx, "scenario_index", 0)
                inputs = getattr(cx, "inputs", {})
                expected = getattr(cx, "expected", {})
                observed = getattr(cx, "actual", {})

            guard_text = self._get_guard_text(idx)
            vtype, reason, fix = _classify_violation(
                idx, guard_text, inputs, expected, observed, self._scenarios
            )
            records.append(SemanticFeedback(
                violation_type=vtype,
                scenario_index=idx,
                constraint_text=guard_text,
                inputs=inputs,
                expected=expected,
                observed=observed,
                reason=reason,
                priority=self._get_priority(vtype),
                suggested_fix=fix,
            ))
        # Sort by priority (ordering errors first)
        records.sort(key=lambda r: r.priority)
        return records

    def render(
        self,
        counterexamples: list[Any],
        variant: str = "semantic_ir",
    ) -> str:
        """Render counterexamples as a repair prompt string.

        variant: "test_only" | "test_expected" | "semantic_ir"
        """
        if not counterexamples:
            return "Implementation incorrect. Retry with attention to all FSF scenarios."

        records = self.build(counterexamples)
        if not records:
            return "Implementation incorrect. Retry."

        header_map = {
            "test_only": "The following inputs caused incorrect output:",
            "test_expected": "The following counterexamples were found:",
            "semantic_ir": (
                "Specification-level violations detected. "
                "Fix the implementation to respect FSF first-match ordering:"
            ),
        }
        header = header_map.get(variant, header_map["semantic_ir"])
        lines = [header, ""]

        for rec in records:
            if variant == "test_only":
                lines.append(rec.render_test_only())
            elif variant == "test_expected":
                lines.append(rec.render_test_expected())
            else:
                lines.append(rec.render_semantic_ir())
            lines.append("")

        lines.append(
            "Remember: FSF scenarios must be evaluated in listed order. "
            "Scenario guards are mutually exclusive through priority ordering — "
            "a scenario is active only when all higher-priority guards have failed."
        )
        return "\n".join(lines)
