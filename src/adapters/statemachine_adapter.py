"""Mini-StateMachine adapter for the SgDP generalisation study (E8a).

A Mini-StateMachine specification describes a finite-state system with ordered
transition guards.  The ordering semantics are structurally equivalent to FSF:
the first matching transition guard fires, making ordering matter exactly as
in FSF precedence-sensitive tasks.

Spec format (simple text, one transition per line):
    STATE  from_state → to_state  IF  guard_condition  DO  output_assignments

Example:
    INPUTS: level: int, mode: int
    OUTPUTS: status: int, action: int
    STATES: idle, active, error
    INITIAL: idle

    idle → active   IF level gt 5 && mode eq 1   DO status eq 1 && action eq 2
    idle → error    IF level gt 5 && mode ne 1   DO status eq 2 && action eq 0
    active → idle   IF level le 0                DO status eq 0 && action eq 1
    active → active IF level gt 0 && level le 5  DO status eq 1 && action eq 1
    error → idle    IF mode eq 0                 DO status eq 0 && action eq 3
    others                                        DO status eq 0 && action eq 0

The adapter converts this to FSF-style fsfScenarios with ordered guards,
making it directly compatible with the shared formal checker and pipeline.
"""

from __future__ import annotations

import re
from typing import Any

from src.adapters.base import SpecAdapter


class StateMachineAdapter(SpecAdapter):
    """Adapter: Mini-StateMachine → FSF-style TaskSpec."""

    @property
    def notation_name(self) -> str:
        return "mini_statemachine"

    def parse(self, spec_text: str, task_id: str) -> dict[str, Any]:
        lines = [ln.strip() for ln in spec_text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
        inputs: list[dict] = []
        outputs: list[dict] = []
        transitions: list[tuple[str, str, str]] = []  # (from_state, guard, def)
        has_others = False
        others_def = "status eq 0 && action eq 0"
        task_name = task_id.replace("-", "_").replace(".", "_")

        for line in lines:
            if line.upper().startswith("INPUTS:"):
                for var_spec in line.split(":", 1)[1].split(","):
                    m = re.match(r"\s*(\w+)\s*:\s*\w+", var_spec)
                    if m:
                        inputs.append({"name": m.group(1), "type": "nat"})
            elif line.upper().startswith("OUTPUTS:"):
                for var_spec in line.split(":", 1)[1].split(","):
                    m = re.match(r"\s*(\w+)\s*:\s*\w+", var_spec)
                    if m:
                        outputs.append({"name": m.group(1), "type": "nat"})
            elif line.upper().startswith("STATES:") or line.upper().startswith("INITIAL:"):
                pass  # not needed for FSF conversion
            elif re.match(r"others", line, re.IGNORECASE):
                has_others = True
                m_do = re.search(r"DO\s+(.+)", line, re.IGNORECASE)
                if m_do:
                    others_def = m_do.group(1).strip()
            elif "→" in line or "->" in line:
                # transition: from → to IF guard DO def
                line = line.replace("->", "→")
                m = re.match(r"(\w+)\s*→\s*(\w+)\s+IF\s+(.+?)\s+DO\s+(.+)", line, re.IGNORECASE)
                if m:
                    from_state, to_state, guard, definition = m.groups()
                    transitions.append((from_state, guard.strip(), definition.strip()))

        if not inputs:
            inputs = [{"name": "level", "type": "nat"}, {"name": "mode", "type": "nat"}]
        if not outputs:
            outputs = [{"name": "status", "type": "nat"}, {"name": "action", "type": "nat"}]

        # Convert to FSF-style ordered scenarios (order preserved from spec)
        scenarios: list[dict[str, Any]] = []
        for idx, (_, guard, definition) in enumerate(transitions, start=1):
            scenarios.append({
                "index": idx,
                "kind": "scenario",
                "test": guard,
                "def": definition,
            })
        scenarios.append({
            "index": len(scenarios) + 1,
            "kind": "others",
            "test": "others",
            "def": others_def,
        })

        in_str = ", ".join(f"{p['name']}: int" for p in inputs)
        out_names = [p["name"] for p in outputs]
        prompt_lines = [f"Function {task_name}({in_str}) → ({', '.join(out_names)})", "", "Ordered transition rules:"]
        for sc in scenarios:
            if sc["kind"] == "others":
                prompt_lines.append(f"otherwise => {sc['def']}")
            else:
                prompt_lines.append(f"if ({sc['test']}) => {sc['def']}")
        prompt_lines.append("\nIMPORTANT: evaluate conditions in listed order (first match wins).")

        return {
            "taskId": f"MiniSM.{task_id}",
            "kind": "process",
            "sourceFile": f"statemachine://{task_id}",
            "module": "MiniStateMachine",
            "name": task_name,
            "signature": {"inputs": inputs, "outputs": outputs},
            "fsfScenarios": scenarios,
            "ext": [],
            "promptSpec": "\n".join(prompt_lines),
            "sourceBasename": task_id,
            "notation": "mini_statemachine",
        }


# Built-in Mini-StateMachine tasks for E8 evaluation
BUILTIN_STATEMACHINE_TASKS_SPEC = [
    # Task SM001: signal classifier
    """\
INPUTS: level: int, threshold: int
OUTPUTS: status: int, action: int
STATES: normal, warning, critical
INITIAL: normal

normal → critical  IF level gt 10 && threshold gt 5   DO status eq 3 && action eq 2
normal → warning   IF level gt 10 && threshold le 5   DO status eq 2 && action eq 1
normal → warning   IF level gt 5 && level le 10        DO status eq 2 && action eq 0
normal → normal    IF level le 0                        DO status eq 0 && action eq 3
others                                                   DO status eq 1 && action eq 0
""",
    # Task SM002: temperature controller
    """\
INPUTS: temp: int, setpoint: int, override: int
OUTPUTS: heater: int, cooler: int, alarm: int
STATES: idle, heating, cooling, alarm
INITIAL: idle

idle → alarm    IF override eq 1 && temp gt 80          DO heater eq 0 && cooler eq 0 && alarm eq 1
idle → cooling  IF override eq 0 && temp gt setpoint    DO heater eq 0 && cooler eq 1 && alarm eq 0
idle → heating  IF override eq 0 && temp lt setpoint    DO heater eq 1 && cooler eq 0 && alarm eq 0
others                                                    DO heater eq 0 && cooler eq 0 && alarm eq 0
""",
    # Task SM003: access control
    """\
INPUTS: level: int, role: int, time: int
OUTPUTS: access: int, log: int, alert: int
STATES: locked, unlocked, restricted
INITIAL: locked

locked → unlocked    IF role eq 3 && level gt 0             DO access eq 1 && log eq 1 && alert eq 0
locked → restricted  IF role eq 2 && level gt 0 && time le 8 DO access eq 1 && log eq 1 && alert eq 0
locked → locked      IF role eq 1 && level gt 0              DO access eq 0 && log eq 1 && alert eq 1
others                                                         DO access eq 0 && log eq 0 && alert eq 0
""",
    # Task SM004: network packet router
    """\
INPUTS: priority: int, size: int, flags: int
OUTPUTS: queue: int, action: int, drop: int
STATES: normal, congested, blocked
INITIAL: normal

normal → blocked   IF flags eq 1 && priority gt 5            DO queue eq 0 && action eq 3 && drop eq 1
normal → congested IF flags eq 0 && size gt 100 && priority le 3 DO queue eq 2 && action eq 1 && drop eq 0
normal → normal    IF flags eq 0 && priority gt 5             DO queue eq 1 && action eq 2 && drop eq 0
normal → normal    IF size le 50                              DO queue eq 0 && action eq 0 && drop eq 0
others                                                         DO queue eq 1 && action eq 1 && drop eq 0
""",
    # Task SM005: inventory reorder system
    """\
INPUTS: stock: int, demand: int, budget: int
OUTPUTS: order: int, amount: int, status: int
STATES: ok, low, critical
INITIAL: ok

ok → critical IF stock le 5 && demand gt 10                   DO order eq 1 && amount eq 50 && status eq 2
ok → low      IF stock le 20 && stock gt 5 && budget gt 100   DO order eq 1 && amount eq 20 && status eq 1
ok → ok       IF stock gt 20                                   DO order eq 0 && amount eq 0 && status eq 0
others                                                          DO order eq 0 && amount eq 0 && status eq 0
""",
    # Task SM006: elevator controller
    """\
INPUTS: floor: int, target: int, load: int
OUTPUTS: direction: int, speed: int, door: int
STATES: idle, moving, loading
INITIAL: idle

idle → loading  IF load gt 0 && floor eq target   DO direction eq 0 && speed eq 0 && door eq 1
idle → moving   IF target gt floor && load le 8   DO direction eq 1 && speed eq 2 && door eq 0
idle → moving   IF target lt floor && load le 8   DO direction eq 2 && speed eq 2 && door eq 0
idle → idle     IF load gt 8                      DO direction eq 0 && speed eq 0 && door eq 0
others                                             DO direction eq 0 && speed eq 0 && door eq 0
""",
    # Task SM007: battery manager
    """\
INPUTS: charge: int, consumption: int, solar: int
OUTPUTS: mode: int, output: int, warning: int
STATES: normal, low, critical
INITIAL: normal

normal → critical IF charge le 10 && consumption gt solar    DO mode eq 0 && output eq 0 && warning eq 2
normal → low      IF charge le 30 && charge gt 10            DO mode eq 1 && output eq 1 && warning eq 1
normal → normal   IF charge gt 30 && solar ge consumption    DO mode eq 2 && output eq 3 && warning eq 0
others                                                         DO mode eq 1 && output eq 2 && warning eq 0
""",
    # Task SM008: water level controller
    """\
INPUTS: level: int, inflow: int, outflow: int
OUTPUTS: pump: int, valve: int, alarm: int
STATES: normal, fill, drain, emergency
INITIAL: normal

normal → emergency IF level gt 90                              DO pump eq 0 && valve eq 1 && alarm eq 1
normal → drain     IF level gt 70 && level le 90               DO pump eq 0 && valve eq 1 && alarm eq 0
normal → fill      IF level lt 30 && inflow gt 0               DO pump eq 1 && valve eq 0 && alarm eq 0
normal → normal    IF level ge 30 && level le 70               DO pump eq 0 && valve eq 0 && alarm eq 0
others                                                          DO pump eq 0 && valve eq 0 && alarm eq 0
""",
    # Task SM009: loan approval
    """\
INPUTS: score: int, income: int, debt: int
OUTPUTS: approved: int, limit: int, rate: int
STATES: pending, approved, rejected
INITIAL: pending

pending → rejected IF score lt 600                             DO approved eq 0 && limit eq 0 && rate eq 0
pending → approved IF score ge 750 && income gt 50 && debt le 30 DO approved eq 1 && limit eq 100 && rate eq 3
pending → approved IF score ge 600 && income gt 30              DO approved eq 1 && limit eq 50 && rate eq 5
others                                                           DO approved eq 0 && limit eq 0 && rate eq 0
""",
    # Task SM010: traffic light controller
    """\
INPUTS: queue: int, emergency: int, cycle: int
OUTPUTS: green: int, yellow: int, red: int
STATES: green, yellow, red
INITIAL: red

red → green    IF emergency eq 0 && queue gt 5 && cycle ge 30  DO green eq 1 && yellow eq 0 && red eq 0
red → green    IF emergency eq 1                                DO green eq 1 && yellow eq 0 && red eq 0
red → yellow   IF queue le 5 && cycle lt 30                    DO green eq 0 && yellow eq 1 && red eq 0
others                                                          DO green eq 0 && yellow eq 0 && red eq 1
""",
]


def load_builtin_statemachine_tasks() -> list[dict[str, Any]]:
    """Return the 10 built-in Mini-StateMachine tasks as TaskSpec dicts."""
    adapter = StateMachineAdapter()
    tasks = []
    for i, spec_text in enumerate(BUILTIN_STATEMACHINE_TASKS_SPEC, start=1):
        task_id = f"SM{i:03d}"
        try:
            task = adapter.parse(spec_text, task_id)
            # Generate reference code from the FSF scenarios
            from src.benchmarks.reference_gen import generate_reference_code
            task["referenceCode"] = generate_reference_code(task)
            tasks.append(task)
        except Exception as e:
            print(f"[SM] Failed to parse {task_id}: {e}")
    return tasks
