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
    # Task SM011: elevator state machine (floor × direction × request → next_state)
    """\
INPUTS: floor: int, direction: int, request: int
OUTPUTS: next_floor: int, door: int, moving: int
STATES: idle, moving_up, moving_down, door_open
INITIAL: idle

idle → door_open     IF floor eq request && direction eq 0     DO next_floor eq floor && door eq 1 && moving eq 0
idle → moving_up     IF request gt floor                        DO next_floor eq floor + 1 && door eq 0 && moving eq 1
idle → moving_down   IF request lt floor                        DO next_floor eq floor - 1 && door eq 0 && moving eq 1
moving_up → door_open IF floor eq request                       DO next_floor eq floor && door eq 1 && moving eq 0
moving_up → moving_up IF request gt floor                       DO next_floor eq floor + 1 && door eq 0 && moving eq 1
moving_down → door_open IF floor eq request                     DO next_floor eq floor && door eq 1 && moving eq 0
moving_down → moving_down IF request lt floor                   DO next_floor eq floor - 1 && door eq 0 && moving eq 1
others                                                          DO next_floor eq floor && door eq 0 && moving eq 0
""",
    # Task SM012: ATM transaction FSM (card_present × pin_ok × balance × amount → state)
    """\
INPUTS: card_present: int, pin_ok: int, balance: int, amount: int
OUTPUTS: state: int, dispensed: int, error: int
STATES: idle, card_inserted, authenticated, dispensing, error
INITIAL: idle

idle → error         IF card_present eq 0 && amount gt 0       DO state eq 4 && dispensed eq 0 && error eq 1
idle → card_inserted IF card_present eq 1 && pin_ok eq 0        DO state eq 1 && dispensed eq 0 && error eq 0
idle → authenticated IF card_present eq 1 && pin_ok eq 1 && balance ge amount DO state eq 2 && dispensed eq 0 && error eq 0
idle → error         IF card_present eq 1 && pin_ok eq 1 && balance lt amount DO state eq 4 && dispensed eq 0 && error eq 2
authenticated → dispensing IF amount gt 0                        DO state eq 3 && dispensed eq amount && error eq 0
others                                                            DO state eq 0 && dispensed eq 0 && error eq 0
""",
    # Task SM013: document approval workflow (stage × decision → next_stage)
    """\
INPUTS: stage: int, decision: int, priority: int
OUTPUTS: next_stage: int, notify: int, escalate: int
STATES: draft, review, approval, published, rejected
INITIAL: draft

draft → review       IF stage eq 0 && decision eq 1             DO next_stage eq 1 && notify eq 1 && escalate eq 0
review → approval    IF stage eq 1 && decision eq 1             DO next_stage eq 2 && notify eq 1 && escalate eq 0
review → draft       IF stage eq 1 && decision eq 0             DO next_stage eq 0 && notify eq 1 && escalate eq 0
approval → published IF stage eq 2 && decision eq 1             DO next_stage eq 3 && notify eq 1 && escalate eq 0
approval → rejected  IF stage eq 2 && decision eq 2             DO next_stage eq 4 && notify eq 1 && escalate eq 0
review → approval    IF stage eq 1 && priority ge 3             DO next_stage eq 2 && notify eq 1 && escalate eq 1
others                                                           DO next_stage eq 0 && notify eq 0 && escalate eq 0
""",
    # Task SM014: VPN connection FSM (authenticated × tunnel_ok × timeout → conn_state)
    """\
INPUTS: authenticated: int, tunnel_ok: int, timeout: int
OUTPUTS: conn_state: int, reconnect: int, alert: int
STATES: disconnected, connecting, connected, error
INITIAL: disconnected

disconnected → connecting   IF authenticated eq 1 && timeout eq 0 DO conn_state eq 1 && reconnect eq 0 && alert eq 0
connecting → connected      IF tunnel_ok eq 1 && timeout eq 0      DO conn_state eq 2 && reconnect eq 0 && alert eq 0
connecting → error          IF tunnel_ok eq 0 && timeout ge 30     DO conn_state eq 3 && reconnect eq 1 && alert eq 1
connected → disconnected    IF timeout ge 60                        DO conn_state eq 0 && reconnect eq 0 && alert eq 1
connected → connecting      IF tunnel_ok eq 0 && timeout lt 60     DO conn_state eq 1 && reconnect eq 1 && alert eq 0
error → connecting          IF authenticated eq 1 && reconnect eq 1 DO conn_state eq 1 && reconnect eq 0 && alert eq 0
others                                                              DO conn_state eq 0 && reconnect eq 0 && alert eq 0
""",
    # Task SM015: microwave oven FSM (door_closed × time × power → run_state)
    """\
INPUTS: door_closed: int, time: int, power: int
OUTPUTS: run_state: int, lamp: int, turntable: int
STATES: idle, running, paused, done
INITIAL: idle

idle → running    IF door_closed eq 1 && time gt 0 && power gt 0  DO run_state eq 1 && lamp eq 1 && turntable eq 1
idle → idle       IF door_closed eq 0                              DO run_state eq 0 && lamp eq 1 && turntable eq 0
running → paused  IF door_closed eq 0 && time gt 0                DO run_state eq 2 && lamp eq 1 && turntable eq 0
running → done    IF time le 0                                     DO run_state eq 3 && lamp eq 1 && turntable eq 0
paused → running  IF door_closed eq 1 && time gt 0                DO run_state eq 1 && lamp eq 1 && turntable eq 1
paused → idle     IF time le 0                                     DO run_state eq 0 && lamp eq 0 && turntable eq 0
others                                                              DO run_state eq 0 && lamp eq 0 && turntable eq 0
""",
    # Task SM016: payment processing FSM (authorized × captured × settled → status)
    """\
INPUTS: authorized: int, captured: int, settled: int
OUTPUTS: status: int, action: int, refund: int
STATES: pending, authorized, captured, settled, failed
INITIAL: pending

pending → failed     IF authorized eq 0                           DO status eq 4 && action eq 0 && refund eq 0
pending → authorized IF authorized eq 1 && captured eq 0         DO status eq 1 && action eq 1 && refund eq 0
authorized → captured IF captured eq 1 && settled eq 0           DO status eq 2 && action eq 2 && refund eq 0
authorized → failed  IF captured eq 0 && authorized eq 0         DO status eq 4 && action eq 3 && refund eq 1
captured → settled   IF settled eq 1                              DO status eq 3 && action eq 0 && refund eq 0
captured → failed    IF settled eq 0 && captured eq 0            DO status eq 4 && action eq 3 && refund eq 1
others                                                            DO status eq 0 && action eq 0 && refund eq 0
""",
    # Task SM017: battery charging FSM (charge_level × temp × voltage → charge_mode)
    """\
INPUTS: charge_level: int, temp: int, voltage: int
OUTPUTS: charge_mode: int, rate: int, safe: int
STATES: idle, trickle, bulk, absorption, full, fault
INITIAL: idle

idle → fault        IF temp gt 45 || temp lt 0                    DO charge_mode eq 5 && rate eq 0 && safe eq 0
idle → trickle      IF charge_level lt 10 && voltage lt 36        DO charge_mode eq 1 && rate eq 1 && safe eq 1
idle → bulk         IF charge_level lt 80 && voltage ge 36        DO charge_mode eq 2 && rate eq 3 && safe eq 1
bulk → absorption   IF charge_level ge 80 && voltage ge 36        DO charge_mode eq 3 && rate eq 2 && safe eq 1
absorption → full   IF charge_level ge 98                         DO charge_mode eq 4 && rate eq 0 && safe eq 1
full → idle         IF charge_level ge 100                        DO charge_mode eq 0 && rate eq 0 && safe eq 1
others                                                             DO charge_mode eq 2 && rate eq 2 && safe eq 1
""",
    # Task SM018: order fulfillment FSM (paid × picked × shipped × delivered → order_state)
    """\
INPUTS: paid: int, picked: int, shipped: int, delivered: int
OUTPUTS: order_state: int, notify: int, action: int
STATES: placed, processing, shipped, delivered, cancelled
INITIAL: placed

placed → cancelled   IF paid eq 0 && picked eq 0 && shipped eq 0  DO order_state eq 4 && notify eq 1 && action eq 0
placed → processing  IF paid eq 1 && picked eq 0                   DO order_state eq 1 && notify eq 1 && action eq 1
processing → shipped IF picked eq 1 && shipped eq 0                DO order_state eq 2 && notify eq 1 && action eq 2
shipped → delivered  IF shipped eq 1 && delivered eq 1             DO order_state eq 3 && notify eq 1 && action eq 3
shipped → shipped    IF shipped eq 1 && delivered eq 0             DO order_state eq 2 && notify eq 0 && action eq 0
others                                                              DO order_state eq 0 && notify eq 0 && action eq 0
""",
]


def load_builtin_statemachine_tasks() -> list[dict[str, Any]]:
    """Return the 18 built-in Mini-StateMachine tasks as TaskSpec dicts."""
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
