"""Notation-agnostic Specification Intermediate Representation (SpecIR).

SpecIR is the canonical internal representation of any formal specification
consumed by the SgDP framework. Language-specific adapters produce SpecIR;
instantiation-specific lowerers (e.g. FSFLowerer for HSP-Agile) produce the
platform format from SpecIR. The pipeline itself depends only on SpecIR.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class Param:
    name: str
    type: str   # "nat", "int", "bool", "string"

@dataclass
class GuardAtom:
    """A single relational atom in a guard: var op threshold.
    
    op is one of: "eq", "ne", "lt", "le", "gt", "ge", "others"
    threshold is a literal value or None for the "others" sentinel.
    """
    var: str
    op: str
    threshold: int | float | str | None = None

@dataclass
class GuardedCase:
    """One ordered case in the spec: (guard, postcondition).
    
    guard is a list of GuardAtom (AND-connected) or [GuardAtom(var='', op='others')]
    for the default/else case.
    postcondition maps output variable names to their expected values.
    """
    index: int
    guard: list[GuardAtom]
    postcondition: dict[str, Any]
    guard_text: str = ""      # original surface text for prompting
    post_text: str = ""       # original surface text for prompting

@dataclass
class SpecIR:
    """Notation-agnostic Specification Intermediate Representation.
    
    An adapter Adapt_L : Text_L -> SpecIR translates any formal spec language L
    into this canonical form. A lowerer Lower_FSF : SpecIR -> TaskSpec_FSF
    then produces the FSF-shaped dict required by the HSP-Agile pipeline.
    """
    task_id: str
    notation: str           # "sofl", "mini_z", "mini_statemachine", "real_derived"
    name: str
    inputs: list[Param]
    outputs: list[Param]
    cases: list[GuardedCase]  # ordered first-match semantics
    surface_prompt: str       # human-readable spec text for LLM prompting
    metadata: dict[str, Any] = field(default_factory=dict)
    # metadata may include: states, transitions (for SM), source_id, provenance, ext_vars

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "task_id": self.task_id,
            "notation": self.notation,
            "name": self.name,
            "inputs": [{"name": p.name, "type": p.type} for p in self.inputs],
            "outputs": [{"name": p.name, "type": p.type} for p in self.outputs],
            "cases": [
                {
                    "index": c.index,
                    "guard": [{"var": a.var, "op": a.op, "threshold": a.threshold} for a in c.guard],
                    "postcondition": c.postcondition,
                    "guard_text": c.guard_text,
                    "post_text": c.post_text,
                }
                for c in self.cases
            ],
            "surface_prompt": self.surface_prompt,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SpecIR":
        """Deserialize from JSON-compatible dict."""
        return cls(
            task_id=d["task_id"],
            notation=d["notation"],
            name=d["name"],
            inputs=[Param(p["name"], p["type"]) for p in d["inputs"]],
            outputs=[Param(p["name"], p["type"]) for p in d["outputs"]],
            cases=[
                GuardedCase(
                    index=c["index"],
                    guard=[GuardAtom(a["var"], a["op"], a.get("threshold")) for a in c["guard"]],
                    postcondition=c["postcondition"],
                    guard_text=c.get("guard_text", ""),
                    post_text=c.get("post_text", ""),
                )
                for c in d["cases"]
            ],
            surface_prompt=d["surface_prompt"],
            metadata=d.get("metadata", {}),
        )

    @property
    def has_others_case(self) -> bool:
        return any(c.guard and c.guard[0].op == "others" for c in self.cases)

    @property  
    def scenario_count(self) -> int:
        return len(self.cases)
