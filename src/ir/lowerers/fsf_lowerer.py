"""FSF Lowerer: SpecIR → TaskSpec dict (HSP-Agile instantiation).

The FSF Lowering is the HSP-Agile-specific translation from the notation-agnostic
SpecIR to the FSF-shaped TaskSpec dict consumed by the shared pipeline.
"""
from __future__ import annotations
from typing import Any
from src.ir.spec_ir import GuardAtom, GuardedCase, SpecIR


_OP_MAP = {
    "eq": "eq", "ne": "ne", "lt": "lt", "le": "le", "gt": "gt", "ge": "ge",
}

def _atom_to_fsf(atom: GuardAtom) -> str:
    if atom.op == "others":
        return "others"
    op = _OP_MAP.get(atom.op, atom.op)
    return f"{atom.var} {op} {atom.threshold}"

def _guard_to_fsf(guard: list[GuardAtom]) -> str:
    if not guard:
        return "others"
    if guard[0].op == "others":
        return "others"
    return " && ".join(_atom_to_fsf(a) for a in guard)

def _post_to_fsf(postcondition: dict[str, Any]) -> str:
    parts = []
    for k, v in postcondition.items():
        if isinstance(v, str):
            parts.append(f"{k} eq {v}")
        else:
            parts.append(f"{k} eq {v}")
    return " && ".join(parts)

def _case_to_fsf_scenario(case: GuardedCase) -> dict:
    is_others = case.guard and case.guard[0].op == "others"
    return {
        "index": case.index,
        "kind": "others" if is_others else "scenario",
        "test": "others" if is_others else (case.guard_text or _guard_to_fsf(case.guard)),
        "def": case.post_text or _post_to_fsf(case.postcondition),
    }


class FSFLowerer:
    """Lowers a SpecIR to the TaskSpec dict format for HSP-Agile/FSF pipeline."""

    @staticmethod
    def lower(spec: SpecIR) -> dict[str, Any]:
        """Produce a TaskSpec-compatible dict from SpecIR."""
        scenarios = [_case_to_fsf_scenario(c) for c in spec.cases]
        sig_inputs = [{"name": p.name, "type": p.type} for p in spec.inputs]
        sig_outputs = [{"name": p.name, "type": p.type} for p in spec.outputs]

        return {
            "taskId": spec.task_id,
            "kind": "process",
            "sourceFile": f"{spec.notation}://spec-ir",
            "module": spec.metadata.get("module", spec.notation.upper()),
            "name": spec.name,
            "signature": {
                "inputs": sig_inputs,
                "outputs": sig_outputs,
            },
            "fsfScenarios": scenarios,
            "ext": spec.metadata.get("ext_vars", []),
            "promptSpec": spec.surface_prompt,
            "sourceBasename": spec.metadata.get("source_basename", f"{spec.notation}-derived"),
            "referenceCode": spec.metadata.get("reference_code"),
            # Carry SpecIR notation tag for downstream use
            "notation": spec.notation,
            "_spec_ir": spec.to_dict(),  # embed canonical form for traceability
        }
