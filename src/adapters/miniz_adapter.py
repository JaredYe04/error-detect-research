"""Mini-Z adapter for the SgDP generalisation study (E8b).

Mini-Z is a simplified subset of Z notation that captures the essential
spec-guided ordering structure relevant to specification-conformance defects:
ordered precondition cases with deterministic output assignments.

This adapter translates Mini-Z schemas into FSF-compatible TaskSpec dicts
so the shared pipeline runs without modification.

Mini-Z spec format (simplified, not full ISO Z):
    SCHEMA  SchemaName
    INPUTS:  x: ℤ, y: ℤ
    OUTPUTS: result: ℤ, flag: ℤ

    CASE  guard_predicate ⟹  output_assignments  (ordered, first match wins)
    ...
    DEFAULT  output_assignments

Since standard Z notation uses Unicode, we accept both Unicode and ASCII
equivalents (e.g. x ≤ 5 or x le 5, x ≠ y or x ne y).
"""

from __future__ import annotations

import re
from typing import Any

from src.adapters.base import SpecAdapter

_UNICODE_MAP = {
    "≤": " le ", "≥": " ge ", "≠": " ne ", "=": " eq ",
    "∧": " && ", "∨": " || ", "¬": "not ",
    "⟹": "=>", "→": "=>",
    "ℤ": "int", "ℕ": "nat",
}


def _normalise(text: str) -> str:
    text = text.replace("=>", "\x00ARROW\x00")
    for uni, asc in _UNICODE_MAP.items():
        if uni == "=":
            continue  # handled after arrow protection
        text = text.replace(uni, asc)
    text = text.replace("=", " eq ")
    text = text.replace("\x00ARROW\x00", "=>")
    return text


class MiniZAdapter(SpecAdapter):
    """Adapter: Mini-Z schema → FSF-style TaskSpec."""

    @property
    def notation_name(self) -> str:
        return "mini_z"

    def parse(self, spec_text: str, task_id: str) -> dict[str, Any]:
        spec_text = _normalise(spec_text)
        lines = [ln.strip() for ln in spec_text.splitlines() if ln.strip() and not ln.strip().startswith("--")]
        inputs: list[dict] = []
        outputs: list[dict] = []
        cases: list[tuple[str, str]] = []  # (guard, def)
        default_def = ""
        schema_name = task_id.replace("-", "_").replace(".", "_")

        i = 0
        while i < len(lines):
            line = lines[i]
            if line.upper().startswith("SCHEMA"):
                schema_name = line.split(None, 1)[1].strip() if " " in line else schema_name
            elif line.upper().startswith("INPUTS:"):
                for var_spec in line.split(":", 1)[1].split(","):
                    m = re.match(r"\s*(\w+)\s*:\s*\w+", var_spec)
                    if m:
                        inputs.append({"name": m.group(1), "type": "nat"})
            elif line.upper().startswith("OUTPUTS:"):
                for var_spec in line.split(":", 1)[1].split(","):
                    m = re.match(r"\s*(\w+)\s*:\s*\w+", var_spec)
                    if m:
                        outputs.append({"name": m.group(1), "type": "nat"})
            elif line.upper().startswith("CASE"):
                rest = line[4:].strip()
                if "=>" in rest:
                    guard, definition = rest.split("=>", 1)
                    cases.append((guard.strip(), definition.strip()))
            elif line.upper().startswith("DEFAULT"):
                rest = line[7:].strip()
                default_def = rest.lstrip("=>").strip()
            i += 1

        if not inputs:
            inputs = [{"name": "x", "type": "nat"}, {"name": "y", "type": "nat"}]
        if not outputs:
            outputs = [{"name": "result", "type": "nat"}]

        scenarios: list[dict[str, Any]] = []
        for idx, (guard, definition) in enumerate(cases, start=1):
            scenarios.append({"index": idx, "kind": "scenario", "test": guard, "def": definition})
        scenarios.append({
            "index": len(scenarios) + 1,
            "kind": "others",
            "test": "others",
            "def": default_def or f"{outputs[0]['name']} eq 0",
        })

        in_str = ", ".join(f"{p['name']}: int" for p in inputs)
        out_names = [p["name"] for p in outputs]
        prompt_lines = [
            f"Process {schema_name}({in_str}) → ({', '.join(out_names)})",
            "",
            "Z-notation ordered cases (first matching case wins):",
        ]
        for sc in scenarios:
            if sc["kind"] == "others":
                prompt_lines.append(f"default: {sc['def']}")
            else:
                prompt_lines.append(f"  CASE ({sc['test']}) ⟹ {sc['def']}")
        prompt_lines.append("\nIMPORTANT: evaluate cases in the listed order.")

        return {
            "taskId": f"MiniZ.{task_id}",
            "kind": "process",
            "sourceFile": f"mini_z://{task_id}",
            "module": "MiniZ",
            "name": schema_name,
            "signature": {"inputs": inputs, "outputs": outputs},
            "fsfScenarios": scenarios,
            "ext": [],
            "promptSpec": "\n".join(prompt_lines),
            "sourceBasename": task_id,
            "notation": "mini_z",
        }


BUILTIN_MINIZ_TASKS_SPEC = [
    # MZ001: discount calculator
    """\
SCHEMA DiscountCalc
INPUTS: price: int, loyalty: int, coupon: int
OUTPUTS: discount: int, final: int

CASE price ge 100 && loyalty ge 5 && coupon ge 1 => discount eq 30 && final eq price - 30
CASE price ge 100 && loyalty ge 5               => discount eq 20 && final eq price - 20
CASE price ge 100 && coupon ge 1                => discount eq 15 && final eq price - 15
CASE price ge 50 && loyalty ge 3                => discount eq 10 && final eq price - 10
CASE price ge 50                                => discount eq 5  && final eq price - 5
DEFAULT discount eq 0 && final eq price
""",
    # MZ002: grade classifier
    """\
SCHEMA GradeClass
INPUTS: score: int, bonus: int, late: int
OUTPUTS: grade: int, gpa: int

CASE late eq 1                                   => grade eq 0 && gpa eq 0
CASE score ge 90 && bonus ge 5                   => grade eq 4 && gpa eq 4
CASE score ge 90                                 => grade eq 4 && gpa eq 4
CASE score ge 80 && bonus ge 3                   => grade eq 3 && gpa eq 4
CASE score ge 80                                 => grade eq 3 && gpa eq 3
CASE score ge 70                                 => grade eq 2 && gpa eq 2
CASE score ge 60                                 => grade eq 1 && gpa eq 1
DEFAULT grade eq 0 && gpa eq 0
""",
    # MZ003: shipping cost
    """\
SCHEMA ShipCost
INPUTS: weight: int, distance: int, express: int
OUTPUTS: cost: int, eta: int

CASE express eq 1 && weight gt 20                => cost eq 50 && eta eq 1
CASE express eq 1                                => cost eq 30 && eta eq 1
CASE weight gt 50 && distance gt 100             => cost eq 40 && eta eq 5
CASE weight gt 20 && distance gt 50              => cost eq 25 && eta eq 4
CASE weight gt 20                                => cost eq 15 && eta eq 3
CASE distance gt 100                             => cost eq 20 && eta eq 4
DEFAULT cost eq 10 && eta eq 2
""",
    # MZ004: insurance premium
    """\
SCHEMA InsurancePremium
INPUTS: age: int, risk: int, history: int
OUTPUTS: premium: int, tier: int

CASE history ge 3                                => premium eq 0 && tier eq 0
CASE age lt 25 && risk ge 3                      => premium eq 80 && tier eq 3
CASE age lt 25                                   => premium eq 50 && tier eq 2
CASE age ge 65 && risk ge 2                      => premium eq 60 && tier eq 3
CASE age ge 65                                   => premium eq 40 && tier eq 2
CASE risk ge 3                                   => premium eq 45 && tier eq 2
DEFAULT premium eq 20 && tier eq 1
""",
    # MZ005: power management
    """\
SCHEMA PowerMgmt
INPUTS: load: int, solar: int, battery: int
OUTPUTS: source: int, export: int, charge: int

CASE load eq 0 && solar gt 0 && battery lt 90    => source eq 2 && export eq 0 && charge eq 1
CASE load eq 0 && solar gt 0                     => source eq 2 && export eq 1 && charge eq 0
CASE load gt 0 && solar ge load                  => source eq 2 && export eq 0 && charge eq 0
CASE load gt 0 && battery ge 20                  => source eq 3 && export eq 0 && charge eq 0
CASE load gt 0 && solar gt 0                     => source eq 1 && export eq 0 && charge eq 0
DEFAULT source eq 0 && export eq 0 && charge eq 0
""",
    # MZ006: request throttler
    """\
SCHEMA ReqThrottle
INPUTS: rate: int, burst: int, priority: int
OUTPUTS: allow: int, delay: int, code: int

CASE priority ge 9                               => allow eq 1 && delay eq 0 && code eq 200
CASE rate gt 1000 && burst gt 50                 => allow eq 0 && delay eq 0 && code eq 429
CASE rate gt 1000                                => allow eq 0 && delay eq 500 && code eq 429
CASE rate gt 500 && priority ge 5                => allow eq 1 && delay eq 100 && code eq 200
CASE rate gt 500                                 => allow eq 1 && delay eq 200 && code eq 200
DEFAULT allow eq 1 && delay eq 0 && code eq 200
""",
    # MZ007: cache policy
    """\
SCHEMA CachePolicy
INPUTS: hits: int, size: int, ttl: int
OUTPUTS: evict: int, refresh: int, priority: int

CASE ttl le 0                                    => evict eq 1 && refresh eq 0 && priority eq 0
CASE hits ge 100 && size le 10                   => evict eq 0 && refresh eq 1 && priority eq 3
CASE hits ge 50 && ttl le 60                     => evict eq 0 && refresh eq 1 && priority eq 2
CASE hits ge 10                                  => evict eq 0 && refresh eq 0 && priority eq 1
CASE size gt 50                                  => evict eq 1 && refresh eq 0 && priority eq 0
DEFAULT evict eq 0 && refresh eq 0 && priority eq 1
""",
    # MZ008: salary calculator
    """\
SCHEMA SalaryCalc
INPUTS: base: int, years: int, performance: int
OUTPUTS: bonus: int, raise: int, total: int

CASE performance ge 5 && years ge 5              => bonus eq 20 && raise eq 10 && total eq base + 30
CASE performance ge 5                            => bonus eq 15 && raise eq 5  && total eq base + 20
CASE performance ge 3 && years ge 10             => bonus eq 10 && raise eq 8  && total eq base + 18
CASE performance ge 3                            => bonus eq 5  && raise eq 3  && total eq base + 8
CASE years ge 15                                 => bonus eq 8  && raise eq 5  && total eq base + 13
DEFAULT bonus eq 0 && raise eq 0 && total eq base
""",
    # MZ009: resource scheduler
    """\
SCHEMA ResourceScheduler
INPUTS: cpu: int, mem: int, deadline: int
OUTPUTS: assigned: int, preempt: int, queue: int

CASE cpu gt 90 && deadline le 1                  => assigned eq 0 && preempt eq 1 && queue eq 0
CASE cpu gt 90 && mem gt 80                      => assigned eq 0 && preempt eq 0 && queue eq 2
CASE cpu gt 90                                   => assigned eq 0 && preempt eq 0 && queue eq 1
CASE deadline le 1                               => assigned eq 1 && preempt eq 0 && queue eq 0
CASE mem gt 80                                   => assigned eq 1 && preempt eq 0 && queue eq 1
DEFAULT assigned eq 1 && preempt eq 0 && queue eq 0
""",
    # MZ010: fraud detection
    """\
SCHEMA FraudDetect
INPUTS: amount: int, velocity: int, country: int
OUTPUTS: block: int, review: int, score: int

CASE country ge 5                                => block eq 1 && review eq 0 && score eq 100
CASE amount gt 500 && velocity gt 10             => block eq 1 && review eq 0 && score eq 90
CASE amount gt 500 && velocity gt 5              => block eq 0 && review eq 1 && score eq 70
CASE velocity gt 10                              => block eq 0 && review eq 1 && score eq 60
CASE amount gt 200                               => block eq 0 && review eq 1 && score eq 40
DEFAULT block eq 0 && review eq 0 && score eq 0
""",
]


def load_builtin_miniz_tasks() -> list[dict[str, Any]]:
    """Return the 10 built-in Mini-Z tasks as TaskSpec dicts."""
    adapter = MiniZAdapter()
    tasks = []
    for i, spec_text in enumerate(BUILTIN_MINIZ_TASKS_SPEC, start=1):
        task_id = f"MZ{i:03d}"
        try:
            task = adapter.parse(spec_text, task_id)
            from src.benchmarks.reference_gen import generate_reference_code
            task["referenceCode"] = generate_reference_code(task)
            tasks.append(task)
        except Exception as e:
            print(f"[MZ] Failed to parse {task_id}: {e}")
    return tasks
