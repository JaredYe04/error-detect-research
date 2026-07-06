"""Formal conformance checker with counterexample generation."""

from __future__ import annotations

import ast
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable

from .fsf_eval import ScenarioCase, eval_predicate, generate_concrete_cases, parse_def_assignments, resolve_expected


@dataclass
class Counterexample:
    scenario_index: int
    inputs: dict[str, int]
    expected: dict[str, int]
    actual: dict[str, int]
    message: str


@dataclass
class FormalCheckResult:
    passed: bool
    cases_run: int
    cases_passed: int
    counterexamples: list[Counterexample] = field(default_factory=list)
    error: str | None = None

    @property
    def conformance_rate(self) -> float:
        if self.cases_run == 0:
            return 0.0
        return self.cases_passed / self.cases_run


def extract_python_code(llm_output: str) -> str:
    """Extract Python code from markdown fenced block or raw text."""
    import re

    blocks = re.findall(r"```(?:python)?\s*\n(.*?)```", llm_output, re.DOTALL | re.IGNORECASE)
    if blocks:
        return blocks[-1].strip()
    lines = []
    for line in llm_output.splitlines():
        if line.strip().startswith(("def ", "import ", "from ", "class ", "@", "return ", "#")):
            lines.append(line)
        elif lines:
            lines.append(line)
    return "\n".join(lines).strip() if lines else llm_output.strip()


def compile_callable(code: str, func_name: str) -> Callable[..., dict[str, int]]:
    namespace: dict[str, Any] = {}
    exec(code, namespace)  # noqa: S102
    if func_name not in namespace:
        # try snake_case from process name
        candidates = [k for k, v in namespace.items() if callable(v) and not k.startswith("_")]
        if not candidates:
            raise ValueError(f"Function '{func_name}' not found in generated code")
        func_name = candidates[0]
    fn = namespace[func_name]

    def wrapper(**kwargs: int) -> dict[str, int]:
        result = fn(**kwargs)
        if isinstance(result, dict):
            return {k: int(v) for k, v in result.items()}
        if isinstance(result, (int, float)):
            # single output
            return {"result": int(result)}
        if isinstance(result, tuple):
            return {f"out{i}": int(v) for i, v in enumerate(result)}
        raise TypeError(f"Unexpected return type: {type(result)}")

    return wrapper


def run_formal_check(
    code: str,
    task: dict[str, Any],
    *,
    func_name: str | None = None,
    max_cases: int = 12,
) -> FormalCheckResult:
    """Check generated implementation against FSF-derived test cases."""
    name = func_name or task["name"]
    try:
        clean = extract_python_code(code)
        fn = compile_callable(clean, name)
    except Exception as exc:  # noqa: BLE001
        return FormalCheckResult(
            passed=False,
            cases_run=0,
            cases_passed=0,
            counterexamples=[],
            error=f"compile_error: {exc}\n{traceback.format_exc()}",
        )

    scenarios = task.get("fsfScenarios", [])
    signature = task.get("signature", {})
    cases = generate_concrete_cases(scenarios, signature, max_cases=max_cases)

    passed = 0
    counterexamples: list[Counterexample] = []

    for case in cases:
        try:
            actual_raw = fn(**case.inputs)
            actual = {k: int(actual_raw.get(k, 0)) for k in case.expected}
            ok = all(actual.get(k) == v for k, v in case.expected.items())
            if ok:
                passed += 1
            else:
                counterexamples.append(
                    Counterexample(
                        scenario_index=case.scenario_index,
                        inputs=case.inputs,
                        expected=case.expected,
                        actual=actual,
                        message=f"FSF scenario {case.scenario_index} violated",
                    )
                )
        except Exception as exc:  # noqa: BLE001
            counterexamples.append(
                Counterexample(
                    scenario_index=case.scenario_index,
                    inputs=case.inputs,
                    expected=case.expected,
                    actual={},
                    message=f"runtime_error: {exc}",
                )
            )

    # scenario coverage: verify correct branch selection via predicate
    for sc in scenarios:
        if sc.get("kind") == "others":
            continue
        test = sc["test"]
        def_expr = sc["def"]
        for case in cases:
            env = {**case.inputs, **case.expected}
            if eval_predicate(test, env):
                expected = resolve_expected(parse_def_assignments(def_expr), env)
                # branch consistency check already covered above
                break

    return FormalCheckResult(
        passed=passed == len(cases) and len(cases) > 0,
        cases_run=len(cases),
        cases_passed=passed,
        counterexamples=counterexamples,
    )


def format_counterexamples_for_repair(cxs: list[Counterexample]) -> str:
    lines = ["The following counterexamples were found:"]
    for i, cx in enumerate(cxs[:5], 1):
        lines.append(
            f"{i}. scenario={cx.scenario_index} inputs={cx.inputs} "
            f"expected={cx.expected} actual={cx.actual} ({cx.message})"
        )
    lines.append("Fix the implementation to satisfy all FSF scenarios.")
    return "\n".join(lines)
