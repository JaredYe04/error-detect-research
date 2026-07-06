"""Error pattern DSL matcher for generated implementations."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class PatternMatch:
    pattern_id: str
    name: str
    category: str
    severity: str
    description: str
    evidence: str


def load_rules(path: str | Path | None = None) -> list[dict[str, Any]]:
    rules_path = Path(path or Path(__file__).with_name("rules.yaml"))
    data = yaml.safe_load(rules_path.read_text(encoding="utf-8"))
    return data.get("patterns", [])


def _count_branches(tree: ast.AST) -> int:
    return sum(1 for node in ast.walk(tree) if isinstance(node, ast.If))


def _has_else_branch(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and node.orelse:
            orelse = node.orelse
            if len(orelse) == 1 and isinstance(orelse[0], ast.If):
                return True
            return True
    return False


def _return_keys(tree: ast.AST) -> set[str]:
    keys: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict):
            for k in node.value.keys:
                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                    keys.add(k.value)
    return keys


def _referenced_names(tree: ast.AST) -> set[str]:
    return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}


def _returns_constant_success(tree: ast.AST, key: str = "success") -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict):
            for k, v in zip(node.value.keys, node.value.values, strict=False):
                if isinstance(k, ast.Constant) and k.value == key:
                    if isinstance(v, ast.Constant) and v.value == 1:
                        if not any(isinstance(n, ast.If) for n in ast.walk(tree)):
                            return True
    return False


class PatternGuard:
    def __init__(self, rules: list[dict[str, Any]] | None = None) -> None:
        self.rules = rules or load_rules()

    def check(self, code: str, task: dict[str, Any]) -> list[PatternMatch]:
        matches: list[PatternMatch] = []
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return [
                PatternMatch(
                    pattern_id="SYNTAX",
                    name="syntax_error",
                    category="implementation",
                    severity="critical",
                    description="Generated code has syntax errors",
                    evidence="SyntaxError on parse",
                )
            ]

        output_names = [p["name"] for p in task.get("signature", {}).get("outputs", [])]
        scenario_count = len([s for s in task.get("fsfScenarios", []) if s.get("kind") != "others"])
        has_others = any(s.get("kind") == "others" for s in task.get("fsfScenarios", []))
        ext_names = [e["name"] for e in task.get("ext", [])]
        ref_names = _referenced_names(tree)
        branch_count = _count_branches(tree)
        return_keys = _return_keys(tree)

        for rule in self.rules:
            rid = rule["id"]
            matched = False
            evidence = ""
            check = rule.get("ast_check")

            if check == "missing_output_key" and output_names and return_keys:
                missing = [n for n in output_names if n not in return_keys]
                if missing:
                    matched = True
                    evidence = f"missing outputs: {missing}"

            elif check == "branch_count_lt_scenarios" and scenario_count > 1:
                needed = scenario_count if has_others else max(1, scenario_count - 1)
                if branch_count < needed:
                    matched = True
                    evidence = f"branches={branch_count} needed>={needed}"

            elif check == "ext_var_unused" and ext_names:
                unused = [n for n in ext_names if n not in ref_names]
                if unused:
                    matched = True
                    evidence = f"unused ext vars: {unused}"

            elif rid == "RF02" and has_others and not _has_else_branch(tree):
                matched = True
                evidence = "no else branch for others scenario"

            elif rid == "RF07" and _returns_constant_success(tree):
                matched = True
                evidence = "unconditional success return"

            elif rid == "RF13" and re.search(r"else:\s*pass\s*$", code, re.MULTILINE):
                matched = True
                evidence = "empty else branch"

            elif "code_regex" in rule and check is None and rid not in {"RF02", "RF05", "RF07", "RF11"}:
                pat = rule["code_regex"]
                ex = rule.get("exclude_regex")
                if re.search(pat, code, re.MULTILINE):
                    if not ex or not re.search(ex, code, re.MULTILINE):
                        matched = True
                        evidence = f"regex:{pat}"

            if matched:
                matches.append(
                    PatternMatch(
                        pattern_id=rid,
                        name=rule["name"],
                        category=rule["category"],
                        severity=rule["severity"],
                        description=rule["description"],
                        evidence=evidence,
                    )
                )
        return matches

    def passed(self, code: str, task: dict[str, Any], *, max_high: int = 0) -> bool:
        matches = self.check(code, task)
        high = sum(1 for m in matches if m.severity in {"high", "critical"})
        return high <= max_high
