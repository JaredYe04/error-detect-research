"""Guard extraction and comparison utilities for FSF vs code condition analysis."""

from __future__ import annotations

import ast
import re

# Maps each operator to its strict inversion (swap pair)
_SWAP_PAIRS: dict[str, str] = {
    ">": "<",
    "<": ">",
    ">=": "<=",
    "<=": ">=",
    "==": "!=",
    "!=": "==",
}

# Maps each boundary operator to its strict/non-strict counterpart (off-by-one pair)
_STRICT_PAIRS: dict[str, str] = {
    ">=": ">",
    ">": ">=",
    "<=": "<",
    "<": "<=",
}

# FSF keyword-style operators (e.g. "x gt 0")
_OP_WORD_MAP: dict[str, str] = {
    "eq": "==",
    "gt": ">",
    "lt": "<",
    "ge": ">=",
    "le": "<=",
    "ne": "!=",
}

# AST comparison node types to operator strings
_AST_OP_MAP: dict[type, str] = {
    ast.Gt: ">",
    ast.Lt: "<",
    ast.GtE: ">=",
    ast.LtE: "<=",
    ast.Eq: "==",
    ast.NotEq: "!=",
    ast.Is: "is",
    ast.IsNot: "is not",
}


def _parse_atom(atom: str) -> tuple[str, str, str] | None:
    """Parse a single relational atom into (var, op, threshold).

    Supports FSF keyword syntax (x gt 0) and Python symbol syntax (x > 0).
    """
    atom = atom.strip()
    if not atom or atom.lower() in ("others", "true", "false"):
        return None

    # Keyword-style: "x gt 0"
    for word, sym in _OP_WORD_MAP.items():
        m = re.match(rf"^(\w+)\s+{word}\s+(\S+)$", atom, re.IGNORECASE)
        if m:
            return m.group(1), sym, m.group(2)

    # Symbol-style: try longest operators first to avoid partial matches
    for sym in (">=", "<=", "!=", "==", ">", "<"):
        m = re.match(rf"^(\w+)\s*{re.escape(sym)}\s*(\S+)$", atom)
        if m:
            return m.group(1), sym, m.group(2)

    return None


def _split_predicate(text: str) -> list[str]:
    """Split a predicate string into individual atomic clauses."""
    text = re.sub(r"\band\b", "&&", text, flags=re.IGNORECASE)
    text = re.sub(r"\bor\b", "||", text, flags=re.IGNORECASE)
    return re.split(r"\s*(?:&&|\|\|)\s*", text)


def extract_fsf_guards(scenarios: list[dict]) -> list[tuple[str, str, str]]:
    """Extract (var, op, threshold) atoms from FSF scenario guards.

    Returns list of (variable, operator, threshold) for comparison atoms,
    skipping 'others' and boolean-only scenarios.
    """
    guards: list[tuple[str, str, str]] = []
    for sc in scenarios:
        if sc.get("kind") == "others":
            continue
        test = sc.get("test", "")
        for atom in _split_predicate(test):
            parsed = _parse_atom(atom.strip())
            if parsed:
                guards.append(parsed)
    return guards


def extract_code_conditions(code: str) -> list[tuple[str, str, str]]:
    """Extract ordered (var, op, threshold) from If/elif chain using AST.

    Returns them in source order. Handles simple binary comparisons of the
    form ``if var OP threshold`` where threshold is a literal or name.
    """
    conditions: list[tuple[str, str, str]] = []
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return conditions

    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        test = node.test

        # Handle "if x is None" / "if x is not None"
        if isinstance(test, ast.Compare) and len(test.ops) == 1:
            left = test.left
            op_node = test.ops[0]
            right_node = test.comparators[0]
            op_sym = _AST_OP_MAP.get(type(op_node))
            if op_sym is None:
                continue
            if not isinstance(left, ast.Name):
                continue
            var = left.id
            if isinstance(right_node, ast.Constant):
                threshold = str(right_node.value)
            elif isinstance(right_node, ast.Name):
                threshold = right_node.id
            else:
                continue
            conditions.append((var, op_sym, threshold))

        # Handle "if not x" style - treat as x == 0 / x is None
        elif isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
            if isinstance(test.operand, ast.Name):
                conditions.append((test.operand.id, "==", "0"))

    return conditions


def detect_swapped_comparisons(
    fsf_guards: list[tuple[str, str, str]],
    code_conditions: list[tuple[str, str, str]],
) -> list[str]:
    """Return list of violation strings where code operator is the inverse of FSF.

    Example: FSF says ``x > 0`` but code has ``x < 0``.
    """
    violations: list[str] = []
    for var, fsf_op, threshold in fsf_guards:
        inverted = _SWAP_PAIRS.get(fsf_op)
        if inverted is None:
            continue
        for cvar, cop, cthreshold in code_conditions:
            if cvar == var and cthreshold == threshold and cop == inverted:
                violations.append(
                    f"{var}: FSF uses '{fsf_op} {threshold}' but code has '{cop} {cthreshold}'"
                )
    return violations


def detect_off_by_one(
    fsf_guards: list[tuple[str, str, str]],
    code_conditions: list[tuple[str, str, str]],
) -> list[str]:
    """Return list of violations where strict/non-strict boundary is wrong.

    Example: FSF has ``x >= 0`` but code uses ``x > 0`` (off by one at zero).
    """
    violations: list[str] = []
    for var, fsf_op, threshold in fsf_guards:
        strict_alt = _STRICT_PAIRS.get(fsf_op)
        if strict_alt is None:
            continue
        for cvar, cop, cthreshold in code_conditions:
            if cvar == var and cthreshold == threshold and cop == strict_alt:
                violations.append(
                    f"{var}: FSF boundary '{fsf_op} {threshold}' but code uses '{cop} {cthreshold}'"
                )
    return violations


def detect_missing_guards(
    fsf_guards: list[tuple[str, str, str]],
    code_conditions: list[tuple[str, str, str]],
) -> list[str]:
    """Return list of FSF guard atoms not reflected in any code condition."""
    code_set = set(code_conditions)
    violations: list[str] = []
    for var, op, threshold in fsf_guards:
        if (var, op, threshold) not in code_set:
            violations.append(f"{var} {op} {threshold}")
    return violations
