"""SOFL/FSF Specification Adapter.

Wraps the existing ASFL bridge to produce SpecIR from SOFL/FSF specifications,
unifying the ingestion path with Mini-Z and Mini-StateMachine adapters.
"""
from __future__ import annotations
import re
from typing import Any

from src.adapters.base import SpecAdapter
from src.ir.spec_ir import GuardAtom, GuardedCase, Param, SpecIR


class SOFLAdapter(SpecAdapter):
    """Adapter for SOFL/FSF specifications.
    
    Converts FSF-formatted task dicts (from the existing benchmark pipeline)
    into SpecIR, enabling unified processing across notation backends.
    """

    @property
    def notation_name(self) -> str:
        return "sofl"

    def parse(self, spec_text: str, task_id: str) -> SpecIR:
        """Parse SOFL/FSF spec text into SpecIR.
        
        For the existing benchmark, tasks are already in TaskSpec dict format;
        use from_task_spec() for that path.
        """
        raise NotImplementedError(
            "Direct SOFL text parsing requires the ASFL bridge. "
            "Use SOFLAdapter.from_task_spec(task_dict) for pre-parsed tasks."
        )

    @classmethod
    def from_task_spec(cls, task: dict[str, Any]) -> SpecIR:
        """Convert an existing FSF TaskSpec dict to SpecIR."""
        task_id = task.get("taskId", "")
        sig = task.get("signature", {})
        inputs = [Param(p["name"], p.get("type", "nat")) for p in sig.get("inputs", [])]
        outputs = [Param(p["name"], p.get("type", "nat")) for p in sig.get("outputs", [])]

        cases = []
        for s in task.get("fsfScenarios", []):
            idx = s.get("index", len(cases) + 1)
            is_others = s.get("kind") == "others" or s.get("test") == "others"
            guard_text = s.get("test", "")
            post_text = s.get("def", "")

            if is_others:
                guard = [GuardAtom(var="", op="others")]
            else:
                guard = _parse_fsf_guard(guard_text)

            post = _parse_fsf_post(post_text, outputs)
            cases.append(GuardedCase(
                index=idx,
                guard=guard,
                postcondition=post,
                guard_text=guard_text,
                post_text=post_text,
            ))

        return SpecIR(
            task_id=task_id,
            notation="sofl",
            name=task.get("name", task_id),
            inputs=inputs,
            outputs=outputs,
            cases=cases,
            surface_prompt=task.get("promptSpec", ""),
            metadata={
                "module": task.get("module", ""),
                "source_file": task.get("sourceFile", ""),
                "ext_vars": task.get("ext", []),
                "reference_code": task.get("referenceCode"),
                "source_basename": task.get("sourceBasename", ""),
            },
        )


def _parse_fsf_guard(guard_text: str) -> list[GuardAtom]:
    """Best-effort parser for FSF guard atoms like 'a gt 5 && b le 3'."""
    atoms = []
    for part in re.split(r"\s*&&\s*", guard_text.strip()):
        part = part.strip()
        if not part or part == "others":
            continue
        m = re.match(r"^(\w+)\s+(eq|ne|lt|le|gt|ge)\s+(.+)$", part)
        if m:
            var, op, thr = m.groups()
            thr = thr.strip()
            try:
                threshold: int | float | str = int(thr)
            except ValueError:
                try:
                    threshold = float(thr)
                except ValueError:
                    threshold = thr
            atoms.append(GuardAtom(var=var, op=op, threshold=threshold))
        else:
            atoms.append(GuardAtom(var=part, op="eq", threshold=None))
    return atoms or [GuardAtom(var="", op="others")]


def _parse_fsf_post(post_text: str, outputs: list[Param]) -> dict[str, Any]:
    """Parse FSF postcondition 'a eq 1 && b eq 2' into dict."""
    result: dict[str, Any] = {}
    for part in re.split(r"\s*&&\s*", post_text.strip()):
        m = re.match(r"^(\w+)\s+eq\s+(.+)$", part.strip())
        if m:
            var, val = m.groups()
            val = val.strip()
            try:
                result[var] = int(val)
            except ValueError:
                try:
                    result[var] = float(val)
                except ValueError:
                    result[var] = val
    return result
