"""Auto-generate reference implementations from FSF scenarios."""

from __future__ import annotations

import re
from typing import Any

from src.formal.fsf_eval import eval_predicate, parse_def_assignments, resolve_expected


def _py_condition(test_expr: str) -> str:
    if test_expr.strip().lower() == "others":
        return "True"
    expr = test_expr
    expr = re.sub(r"\bgt\b", ">", expr)
    expr = re.sub(r"\blt\b", "<", expr)
    expr = re.sub(r"\bge\b", ">=", expr)
    expr = re.sub(r"\ble\b", "<=", expr)
    expr = re.sub(r"\bne\b", "!=", expr)
    expr = re.sub(r"\beq\b", "==", expr)
    expr = re.sub(r"\btrue\b", "True", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\bfalse\b", "False", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\band\b", "and", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\bor\b", "or", expr, flags=re.IGNORECASE)
    return expr.strip()


def generate_reference_code(task: dict[str, Any]) -> str:
    """Compile FSF scenarios into a deterministic Python reference function."""
    name = task["name"]
    sig = task.get("signature", {})
    inputs = sig.get("inputs", sig.get("params", []))
    outputs = sig.get("outputs", [])
    in_params = ", ".join(f"{p['name']}: int" for p in inputs)
    out_keys = [p["name"] for p in outputs] or ["result"]

    lines = [f"def {name}({in_params}) -> dict:"]
    lines.append('    """Reference implementation auto-generated from FSF."""')

    scenarios = task.get("fsfScenarios", [])
    has_others = any(s.get("kind") == "others" for s in scenarios)
    regular = [s for s in scenarios if s.get("kind") != "others"]
    others = next((s for s in scenarios if s.get("kind") == "others"), None)

    for i, sc in enumerate(regular):
        cond = _py_condition(sc["test"])
        assignments = parse_def_assignments(sc["def"])
        branch = "if" if i == 0 else "elif"
        lines.append(f"    {branch} {cond}:")
        if assignments:
            ret = ", ".join(f'"{k}": {v}' if isinstance(v, int) else f'"{k}": {k}' for k, v in assignments.items())
            lines.append(f"        return {{{ret}}}")
        else:
            lines.append(f"        return {{{', '.join(f'"{k}": 0' for k in out_keys)}}}")

    if others:
        assignments = parse_def_assignments(others["def"])
        lines.append("    else:")
        if assignments:
            ret = ", ".join(f'"{k}": {v}' if isinstance(v, int) else f'"{k}": {k}' for k, v in assignments.items())
            lines.append(f"        return {{{ret}}}")
        else:
            lines.append(f"        return {{{', '.join(f'"{k}": 0' for k in out_keys)}}}")
    elif not regular:
        lines.append(f"    return {{{', '.join(f'"{k}": 0' for k in out_keys)}}}")
    elif not has_others:
        lines.append("    else:")
        lines.append(f"        return {{{', '.join(f'"{k}": 0' for k in out_keys)}}}")

    return "\n".join(lines) + "\n"


def validate_reference(task: dict[str, Any], code: str) -> bool:
    from src.formal.checker import run_formal_check

    return run_formal_check(code, task).passed
