"""Translate FSF predicates to Z3 constraints and concrete test cases."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from z3 import And, BoolVal, Int, Not, Or, Solver, sat

OP_MAP = {
    "eq": "==",
    "gt": ">",
    "lt": "<",
    "ge": ">=",
    "le": "<=",
    "ne": "!=",
}


@dataclass
class ScenarioCase:
    scenario_index: int
    kind: str
    test_expr: str
    def_expr: str
    inputs: dict[str, int]
    expected: dict[str, int]


def _tokenize_predicate(text: str) -> list[str]:
    text = text.replace("&&", " and ").replace("||", " or ")
    text = re.sub(r"\bothers\b", "True", text, flags=re.IGNORECASE)
    return text.split()


def parse_relational_atom(atom: str) -> tuple[str, str, str] | None:
    """Parse 'x gt 0' or 'success eq 1' style atoms."""
    atom = atom.strip()
    for op_name, py_op in OP_MAP.items():
        pat = rf"^(\w+)\s+{op_name}\s+(\w+|\d+)$"
        m = re.match(pat, atom)
        if m:
            return m.group(1), py_op, m.group(2)
    # fallback: x = y
    m = re.match(r"^(\w+)\s*=\s*(\w+|-?\d+)$", atom)
    if m:
        return m.group(1), "==", m.group(2)
    m = re.match(r"^(\w+)\s*>=\s*(\w+|-?\d+)$", atom)
    if m:
        return m.group(1), ">=", m.group(2)
    m = re.match(r"^(\w+)\s*<=\s*(\w+|-?\d+)$", atom)
    if m:
        return m.group(1), "<=", m.group(2)
    m = re.match(r"^(\w+)\s*!=\s*(\w+|-?\d+)$", atom)
    if m:
        return m.group(1), "!=", m.group(2)
    m = re.match(r"^(\w+)\s*>\s*(\w+|-?\d+)$", atom)
    if m:
        return m.group(1), ">", m.group(2)
    m = re.match(r"^(\w+)\s*<\s*(\w+|-?\d+)$", atom)
    if m:
        return m.group(1), "<", m.group(2)
    m = re.match(r"^(\w+)\s+eq\s+(.+)$", atom, re.IGNORECASE)
    if m:
        return m.group(1), "==", m.group(2).strip()
    if atom.lower() == "true":
        return "__true__", "==", "1"
    return None


def eval_atom(atom: str, env: dict[str, Any]) -> bool:
    parsed = parse_relational_atom(atom.strip())
    if not parsed:
        return False
    left, op, right = parsed
    if left == "__true__":
        return True
    lv = env.get(left)
    if lv is None:
        try:
            lv = int(left)
        except ValueError:
            return False
    try:
        rv = int(right)
    except ValueError:
        rv = env.get(right)
    if rv is None:
        return False
    if op == "==":
        return lv == rv
    if op == ">":
        return lv > rv
    if op == "<":
        return lv < rv
    if op == ">=":
        return lv >= rv
    if op == "<=":
        return lv <= rv
    if op == "!=":
        return lv != rv
    return False


def eval_predicate(text: str, env: dict[str, Any]) -> bool:
    """Evaluate simple DNF predicate: conjuncts with && and ||."""
    text = text.strip()
    if not text or text.lower() == "others":
        return True
    text = re.sub(r"\band\b", "&&", text, flags=re.IGNORECASE)
    text = re.sub(r"\bor\b", "||", text, flags=re.IGNORECASE)
    disjuncts = re.split(r"\s*\|\|\s*", text)
    for disj in disjuncts:
        conjuncts = re.split(r"\s*&&\s*", disj.strip())
        if all(eval_atom(c.strip(), env) for c in conjuncts if c.strip()):
            return True
    return False


def parse_def_assignments(def_expr: str) -> dict[str, int | str]:
    """Parse 'success eq 1' or 'count eq 1 && sync_count eq sync_count'."""
    result: dict[str, int | str] = {}
    def_expr = re.sub(r"\band\b", "&&", def_expr, flags=re.IGNORECASE)
    parts = re.split(r"\s*&&\s*", def_expr.strip())
    for part in parts:
        parsed = parse_relational_atom(part.strip())
        if parsed and parsed[1] == "==":
            left, _, right = parsed
            try:
                result[left] = int(right)
            except ValueError:
                result[left] = right
    return result


def resolve_expected(assignments: dict[str, int | str], env: dict[str, Any]) -> dict[str, int]:
    expected: dict[str, int] = {}
    safe_env = {k: int(v) for k, v in env.items()}
    for k, v in assignments.items():
        if isinstance(v, int):
            expected[k] = v
        elif isinstance(v, str) and v in env:
            expected[k] = int(env[v])
        elif isinstance(v, str):
            try:
                expected[k] = int(eval(v, {"__builtins__": {}}, safe_env))  # noqa: S307
            except Exception:
                try:
                    expected[k] = int(v)  # type: ignore[arg-type]
                except (TypeError, ValueError):
                    pass
        else:
            try:
                expected[k] = int(v)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                pass
    return expected


def collect_variables(scenarios: list[dict[str, Any]], signature: dict[str, Any]) -> list[str]:
    names: set[str] = set()
    for group in ("inputs", "outputs", "params"):
        for p in signature.get(group, []):
            names.add(p["name"])
    for sc in scenarios:
        for token in re.findall(r"\b[a-zA-Z_]\w*\b", sc.get("test", "") + " " + sc.get("def", "")):
            if token not in {"others", "true", "and", "or"}:
                names.add(token)
    return sorted(names)


def _z3_var(name: str):
    return Int(name)


def atom_to_z3(atom: str, sym: dict[str, Any]):
    parsed = parse_relational_atom(atom.strip())
    if not parsed:
        return None
    left, op, right = parsed
    if left == "__true__":
        return BoolVal(True)
    lv = sym.get(left, _z3_var(left))
    try:
        rv = int(right)
    except ValueError:
        rv = sym.get(right, _z3_var(right))
    if op == "==":
        return lv == rv
    if op == ">":
        return lv > rv
    if op == "<":
        return lv < rv
    if op == ">=":
        return lv >= rv
    if op == "<=":
        return lv <= rv
    if op == "!=":
        return lv != rv
    return None


def predicate_to_z3(text: str, sym: dict[str, Any]):
    text = text.strip()
    if not text or text.lower() == "others":
        return BoolVal(True)
    text = re.sub(r"\band\b", "&&", text, flags=re.IGNORECASE)
    text = re.sub(r"\bor\b", "||", text, flags=re.IGNORECASE)
    disjuncts = re.split(r"\s*\|\|\s*", text)
    or_terms = []
    for disj in disjuncts:
        conjuncts = re.split(r"\s*&&\s*", disj.strip())
        and_terms = [atom_to_z3(c.strip(), sym) for c in conjuncts if c.strip()]
        and_terms = [t for t in and_terms if t is not None]
        if and_terms:
            or_terms.append(And(*and_terms) if len(and_terms) > 1 else and_terms[0])
    if not or_terms:
        return BoolVal(False)
    return Or(*or_terms) if len(or_terms) > 1 else or_terms[0]


def generate_concrete_cases(
    scenarios: list[dict[str, Any]],
    signature: dict[str, Any],
    *,
    max_cases: int = 12,
) -> list[ScenarioCase]:
    """Use Z3 to generate concrete inputs satisfying each FSF scenario test."""
    var_names = collect_variables(scenarios, signature)
    input_names = [p["name"] for p in signature.get("inputs", signature.get("params", []))]
    output_names = [p["name"] for p in signature.get("outputs", [])]

    cases: list[ScenarioCase] = []
    sym = {n: _z3_var(n) for n in var_names}

    for sc in scenarios:
        if sc.get("kind") == "others":
            test_str = "others"
            prior = [
                predicate_to_z3(s["test"], sym)
                for s in scenarios
                if s.get("kind") != "others" and s.get("test")
            ]
            # First-match others region: ¬(g1 ∨ … ∨ g_{n-1})
            test_z3 = Not(Or(*prior)) if prior else BoolVal(True)
        else:
            test_str = sc["test"]
            test_z3 = predicate_to_z3(test_str, sym)
            prior = []
            for s in scenarios:
                if s.get("kind") == "others":
                    break
                if s is sc:
                    break
                prior.append(predicate_to_z3(s["test"], sym))
            if prior:
                test_z3 = And(test_z3, Not(Or(*prior)))

        solver = Solver()
        solver.add(test_z3)
        # bound integers for termination
        for n in var_names:
            solver.add(sym[n] >= -5)
            solver.add(sym[n] <= 20)

        attempts = 0
        while solver.check() == sat and attempts < 3 and len(cases) < max_cases:
            model = solver.model()
            env = {n: model.eval(sym[n]).as_long() for n in var_names if model.eval(sym[n]) is not None}
            if sc.get("kind") == "others":
                # Reject models that still activate any higher-priority guard.
                if any(
                    eval_predicate(s["test"], env)
                    for s in scenarios
                    if s.get("kind") != "others" and s.get("test")
                ):
                    block = Or(*[sym[n] != env[n] for n in env if n in sym])
                    solver.add(block)
                    attempts += 1
                    continue
            elif not eval_predicate(test_str, env):
                break
            assignments = parse_def_assignments(sc["def"])
            expected = resolve_expected(assignments, env)
            inputs = {k: int(env[k]) for k in input_names if k in env}
            cases.append(
                ScenarioCase(
                    scenario_index=sc.get("index", 0),
                    kind=sc.get("kind", "scenario"),
                    test_expr=test_str,
                    def_expr=sc["def"],
                    inputs=inputs,
                    expected=expected,
                )
            )
            # block this model
            block = Or(*[sym[n] != env[n] for n in env if n in sym])
            solver.add(block)
            attempts += 1

    # ensure at least one case per non-others scenario via hand-crafted fallbacks
    if not cases:
        for sc in scenarios:
            if sc.get("kind") == "others":
                continue
            inputs = {n: 1 for n in input_names}
            env = dict(inputs)
            for out in output_names:
                env.setdefault(out, 0)
            assignments = parse_def_assignments(sc["def"])
            expected = resolve_expected(assignments, env)
            cases.append(
                ScenarioCase(
                    scenario_index=sc.get("index", 0),
                    kind=sc.get("kind", "scenario"),
                    test_expr=sc["test"],
                    def_expr=sc["def"],
                    inputs=inputs,
                    expected=expected,
                )
            )
    return cases[:max_cases]
