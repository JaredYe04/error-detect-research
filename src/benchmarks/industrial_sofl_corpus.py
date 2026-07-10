"""Industrial / practitioner-style SOFL/FSF benchmark tasks (E11 expansion).

Hand-authored ordered-guard FSF processes that resemble domain control logic
(banking, telecom, SCADA, healthcare, etc.). Numeric thresholds are scaled to
small integers so Z3 witness generation (default domain bounds) remains feasible;
semantics mirror industrial decision tables, not HardSynthetic.* generators.
"""

from __future__ import annotations

from typing import Any

from src.benchmarks.reference_gen import generate_reference_code


def _sig(inputs: list[tuple[str, str]], outputs: list[tuple[str, str]]) -> dict[str, Any]:
    return {
        "inputs": [{"name": n, "type": t} for n, t in inputs],
        "outputs": [{"name": n, "type": t} for n, t in outputs],
    }


def _task(
    task_id: str,
    name: str,
    *,
    inputs: list[tuple[str, str]],
    outputs: list[tuple[str, str]],
    scenarios: list[tuple[str, str]],
    source: str,
    section: str = "",
) -> dict[str, Any]:
    fsf: list[dict[str, Any]] = []
    for i, (test, definition) in enumerate(scenarios, start=1):
        fsf.append({"index": i, "kind": "scenario", "test": test, "def": definition})
    fsf.append(
        {
            "index": len(fsf) + 1,
            "kind": "others",
            "test": "others",
            "def": " && ".join(f"{o[0]} eq 0" for o in outputs),
        }
    )
    in_names = ", ".join(n for n, _ in inputs)
    out_names = ", ".join(n for n, _ in outputs)
    prompt_lines = [f"Process {name}({in_names}) -> ({out_names})", "", "FSF specification:"]
    for sc in fsf:
        if sc["kind"] == "others":
            prompt_lines.append(f"others => {sc['def']}")
        else:
            prompt_lines.append(f"if ({sc['test']}) => {sc['def']}")
    task: dict[str, Any] = {
        "taskId": task_id,
        "kind": "process",
        "sourceFile": f"industrial://{source}",
        "module": "IndustrialSOFL",
        "name": name,
        "signature": _sig(inputs, outputs),
        "fsfScenarios": fsf,
        "ext": [],
        "promptSpec": "\n".join(prompt_lines),
        "sourceBasename": source,
        "externalProvenance": {
            "source": source,
            "section": section,
            "generator": "manual_industrial_curation",
            "corpus": "industrial_sofl",
        },
    }
    task["referenceCode"] = generate_reference_code(task)
    return task


# ---------------------------------------------------------------------------
# Curated industrial FSF tasks (ordered first-match; intentional overlaps)
# Thresholds use compact integer scales (typically 0–20) for SMT witnesses.
# ---------------------------------------------------------------------------

INDUSTRIAL_SOFL_TASKS: list[dict[str, Any]] = [
    # --- banking / loan ---
    _task(
        "IndustrialSOFL.LoanUnderwrite",
        "underwrite_loan",
        inputs=[("credit_band", "int"), ("income_k", "int"), ("dti", "int")],
        outputs=[("decision", "int"), ("limit_k", "int")],
        scenarios=[
            ("credit_band lt 3", "decision eq 0 && limit_k eq 0"),
            ("credit_band ge 8 && income_k ge 8 && dti le 3", "decision eq 1 && limit_k eq 15"),
            ("credit_band ge 6 && income_k ge 5", "decision eq 1 && limit_k eq 8"),
            ("credit_band ge 3 && dti le 5", "decision eq 2 && limit_k eq 3"),
        ],
        source="industrial_pattern:banking_loan",
        section="Retail loan underwriting decision table (ordered risk bands)",
    ),
    _task(
        "IndustrialSOFL.AtmWithdraw",
        "atm_withdraw",
        inputs=[("balance", "int"), ("amount", "int"), ("pin_ok", "int")],
        outputs=[("cash", "int"), ("status", "int")],
        scenarios=[
            ("pin_ok eq 0", "cash eq 0 && status eq 2"),
            ("amount gt balance", "cash eq 0 && status eq 3"),
            ("amount gt 10", "cash eq 0 && status eq 4"),
            ("amount gt 0 && amount le balance", "cash eq amount && status eq 1"),
        ],
        source="liu2004soflbook",
        section="ATM withdraw process (Agile-SOFL / textbook banking pattern, scaled)",
    ),
    _task(
        "IndustrialSOFL.WireTransferGate",
        "gate_wire_transfer",
        inputs=[("amount", "int"), ("dest_risk", "int"), ("auth_level", "int")],
        outputs=[("allow", "int"), ("hold", "int")],
        scenarios=[
            ("dest_risk ge 4", "allow eq 0 && hold eq 1"),
            ("amount ge 15 && auth_level lt 3", "allow eq 0 && hold eq 1"),
            ("amount ge 8 && auth_level ge 2", "allow eq 1 && hold eq 1"),
            ("amount lt 8 && auth_level ge 1", "allow eq 1 && hold eq 0"),
        ],
        source="industrial_pattern:banking_loan",
        section="Wire transfer compliance gate with overlapping amount/auth bands",
    ),
    # --- telecom routing ---
    _task(
        "IndustrialSOFL.CallRoute",
        "route_call",
        inputs=[("qos", "int"), ("trunk_load", "int"), ("vip", "int")],
        outputs=[("route", "int"), ("preempt", "int")],
        scenarios=[
            ("vip eq 1 && qos ge 2", "route eq 1 && preempt eq 1"),
            ("trunk_load ge 9", "route eq 0 && preempt eq 0"),
            ("qos ge 4 && trunk_load le 6", "route eq 2 && preempt eq 0"),
            ("qos ge 2", "route eq 3 && preempt eq 0"),
        ],
        source="li2023iet_faultprevention",
        section="RF pattern: telecom call routing / overload policy",
    ),
    _task(
        "IndustrialSOFL.SmsThrottle",
        "throttle_sms",
        inputs=[("rate", "int"), ("spam_score", "int"), ("enterprise", "int")],
        outputs=[("deliver", "int"), ("delay_s", "int")],
        scenarios=[
            ("spam_score ge 8", "deliver eq 0 && delay_s eq 0"),
            ("enterprise eq 1 && rate le 15", "deliver eq 1 && delay_s eq 0"),
            ("rate gt 12 && spam_score ge 4", "deliver eq 0 && delay_s eq 0"),
            ("rate gt 8", "deliver eq 1 && delay_s eq 5"),
        ],
        source="industrial_pattern:telecom_routing",
        section="SMS gateway rate / spam throttle (first-match)",
    ),
    # --- access control ---
    _task(
        "IndustrialSOFL.BadgeAccess",
        "check_badge_access",
        inputs=[("clearance", "int"), ("zone", "int"), ("time_ok", "int")],
        outputs=[("open", "int"), ("alarm", "int")],
        scenarios=[
            ("time_ok eq 0 && zone ge 2", "open eq 0 && alarm eq 1"),
            ("clearance ge 4 && zone le 4", "open eq 1 && alarm eq 0"),
            ("clearance ge 2 && zone le 2", "open eq 1 && alarm eq 0"),
            ("clearance ge 1 && zone eq 1 && time_ok eq 1", "open eq 1 && alarm eq 0"),
        ],
        source="li2023iet_faultprevention",
        section="RF pattern: physical / logical authorization",
    ),
    _task(
        "IndustrialSOFL.ApiAcl",
        "enforce_api_acl",
        inputs=[("role", "int"), ("scope", "int"), ("mfa", "int")],
        outputs=[("permit", "int"), ("step_up", "int")],
        scenarios=[
            ("role eq 0", "permit eq 0 && step_up eq 0"),
            ("scope ge 3 && mfa eq 0", "permit eq 0 && step_up eq 1"),
            ("role ge 3 && scope le 3", "permit eq 1 && step_up eq 0"),
            ("role ge 1 && scope le 1", "permit eq 1 && step_up eq 0"),
        ],
        source="industrial_pattern:access_control",
        section="API ACL with MFA step-up on sensitive scopes",
    ),
    # --- medical dosage alerts ---
    _task(
        "IndustrialSOFL.DoseAlert",
        "dose_alert",
        inputs=[("weight_kg", "int"), ("age", "int"), ("severity", "int")],
        outputs=[("dose_u", "int"), ("alert", "int")],
        scenarios=[
            ("severity ge 4 && age lt 5", "dose_u eq 0 && alert eq 3"),
            ("age lt 5 && weight_kg lt 8", "dose_u eq 1 && alert eq 2"),
            ("age ge 12 && severity ge 3", "dose_u eq 4 && alert eq 1"),
            ("weight_kg ge 10 && severity ge 1", "dose_u eq 2 && alert eq 0"),
        ],
        source="industrial_pattern:medical_dosage",
        section="Pediatric / adult dosage alert decision table (scaled kg/age)",
    ),
    _task(
        "IndustrialSOFL.LabCritical",
        "flag_lab_critical",
        inputs=[("value", "int"), ("low", "int"), ("high", "int")],
        outputs=[("flag", "int"), ("page", "int")],
        scenarios=[
            ("value lt low && value le 0", "flag eq 3 && page eq 1"),
            ("value lt low", "flag eq 2 && page eq 1"),
            ("value gt high", "flag eq 2 && page eq 1"),
            ("value ge low && value le high", "flag eq 0 && page eq 0"),
        ],
        source="industrial_pattern:medical_dosage",
        section="Lab critical-value paging with overlapping low bands",
    ),
    # --- inventory / warehouse ---
    _task(
        "IndustrialSOFL.PickPriority",
        "prioritize_pick",
        inputs=[("sla_h", "int"), ("qty", "int"), ("hazmat", "int")],
        outputs=[("wave", "int"), ("special", "int")],
        scenarios=[
            ("hazmat eq 1", "wave eq 0 && special eq 1"),
            ("sla_h le 2 && qty ge 5", "wave eq 1 && special eq 0"),
            ("sla_h le 4", "wave eq 2 && special eq 0"),
            ("qty ge 10", "wave eq 3 && special eq 0"),
        ],
        source="industrial_pattern:inventory_warehouse",
        section="Warehouse pick-wave prioritization (SLA vs hazmat)",
    ),
    _task(
        "IndustrialSOFL.ReorderPoint",
        "compute_reorder",
        inputs=[("on_hand", "int"), ("forecast", "int"), ("lead", "int")],
        outputs=[("order_qty", "int"), ("expedite", "int")],
        scenarios=[
            ("on_hand le 0 && forecast gt 0", "order_qty eq 12 && expedite eq 1"),
            ("on_hand le 3 && forecast ge 6", "order_qty eq 8 && expedite eq 1"),
            ("on_hand le 6 && lead ge 5", "order_qty eq 5 && expedite eq 0"),
            ("on_hand gt 6", "order_qty eq 0 && expedite eq 0"),
        ],
        source="liu2004soflbook",
        section="Inventory reorder / logistics control (textbook-style, scaled)",
    ),
    # --- power / SCADA ---
    _task(
        "IndustrialSOFL.ScadaTrip",
        "scada_trip",
        inputs=[("amps", "int"), ("temp_c", "int"), ("relay", "int")],
        outputs=[("trip", "int"), ("alarm", "int")],
        scenarios=[
            ("relay eq 1", "trip eq 1 && alarm eq 2"),
            ("amps ge 15 && temp_c ge 12", "trip eq 1 && alarm eq 2"),
            ("amps ge 12 || temp_c ge 14", "trip eq 0 && alarm eq 1"),
            ("amps ge 8", "trip eq 0 && alarm eq 1"),
        ],
        source="industrial_pattern:power_scada",
        section="Feeder overcurrent / temperature trip ladder (ordered)",
    ),
    _task(
        "IndustrialSOFL.GridDispatch",
        "dispatch_grid",
        inputs=[("load", "int"), ("renewable", "int"), ("reserve", "int")],
        outputs=[("source", "int"), ("shed", "int")],
        scenarios=[
            ("load gt renewable && reserve lt 2", "source eq 1 && shed eq 1"),
            ("renewable ge load", "source eq 2 && shed eq 0"),
            ("reserve ge 5", "source eq 3 && shed eq 0"),
            ("load gt 0", "source eq 1 && shed eq 0"),
        ],
        source="industrial_pattern:power_scada",
        section="Microgrid dispatch with overlapping renewable/reserve guards",
    ),
    # --- airline / ticket ---
    _task(
        "IndustrialSOFL.SeatUpgrade",
        "upgrade_seat",
        inputs=[("tier", "int"), ("overbook", "int"), ("hours_to_dep", "int")],
        outputs=[("cabin", "int"), ("voucher", "int")],
        scenarios=[
            ("overbook ge 3 && hours_to_dep le 2", "cabin eq 0 && voucher eq 2"),
            ("tier ge 4 && hours_to_dep le 6", "cabin eq 2 && voucher eq 0"),
            ("tier ge 2 && overbook le 1", "cabin eq 1 && voucher eq 0"),
            ("tier ge 1", "cabin eq 0 && voucher eq 1"),
        ],
        source="industrial_pattern:airline_ticket",
        section="Airline involuntary / elite upgrade decision table",
    ),
    _task(
        "IndustrialSOFL.FareRule",
        "apply_fare_rule",
        inputs=[("advance_d", "int"), ("flex", "int"), ("intl", "int")],
        outputs=[("fare_band", "int"), ("change_fee", "int")],
        scenarios=[
            ("intl eq 1 && advance_d lt 3", "fare_band eq 4 && change_fee eq 3"),
            ("advance_d ge 14 && flex eq 0", "fare_band eq 1 && change_fee eq 2"),
            ("flex eq 1", "fare_band eq 3 && change_fee eq 0"),
            ("advance_d ge 7", "fare_band eq 2 && change_fee eq 1"),
        ],
        source="industrial_pattern:airline_ticket",
        section="Fare family / change-fee rules with overlapping advance-purchase",
    ),
    # --- insurance premium ---
    _task(
        "IndustrialSOFL.AutoPremium",
        "quote_auto_premium",
        inputs=[("age", "int"), ("claims", "int"), ("risk", "int")],
        outputs=[("premium", "int"), ("decline", "int")],
        scenarios=[
            ("claims ge 4", "premium eq 0 && decline eq 1"),
            ("age lt 4 && risk ge 3", "premium eq 12 && decline eq 0"),
            ("age ge 12 && risk ge 2", "premium eq 9 && decline eq 0"),
            ("risk ge 2", "premium eq 6 && decline eq 0"),
        ],
        source="industrial_pattern:insurance_premium",
        section="Auto insurance quote bands (age scaled; claims hard decline)",
    ),
    _task(
        "IndustrialSOFL.ClaimTriage",
        "triage_claim",
        inputs=[("amount", "int"), ("fraud_score", "int"), ("injury", "int")],
        outputs=[("queue", "int"), ("siu", "int")],
        scenarios=[
            ("fraud_score ge 7", "queue eq 0 && siu eq 1"),
            ("injury eq 1 && amount ge 8", "queue eq 1 && siu eq 0"),
            ("amount ge 10", "queue eq 2 && siu eq 0"),
            ("amount ge 3", "queue eq 3 && siu eq 0"),
        ],
        source="li2023iet_faultprevention",
        section="RF pattern: boundary screening applied to claims triage",
    ),
    # --- traffic signal ---
    _task(
        "IndustrialSOFL.IntersectionPhase",
        "select_phase",
        inputs=[("queue_ns", "int"), ("queue_ew", "int"), ("ped", "int")],
        outputs=[("phase", "int"), ("extend", "int")],
        scenarios=[
            ("ped eq 1 && queue_ns le 2", "phase eq 4 && extend eq 0"),
            ("queue_ns ge 8", "phase eq 1 && extend eq 1"),
            ("queue_ew ge 8", "phase eq 2 && extend eq 1"),
            ("queue_ns ge queue_ew", "phase eq 1 && extend eq 0"),
        ],
        source="industrial_pattern:traffic_signal",
        section="Actuated intersection phase selection (pedestrian priority)",
    ),
    _task(
        "IndustrialSOFL.RampMeter",
        "meter_ramp",
        inputs=[("mainline", "int"), ("ramp_q", "int"), ("incident", "int")],
        outputs=[("rate", "int"), ("close", "int")],
        scenarios=[
            ("incident eq 1", "rate eq 0 && close eq 1"),
            ("mainline ge 14 && ramp_q ge 5", "rate eq 1 && close eq 0"),
            ("mainline ge 10", "rate eq 2 && close eq 0"),
            ("ramp_q ge 3", "rate eq 3 && close eq 0"),
        ],
        source="industrial_pattern:traffic_signal",
        section="Freeway ramp metering with incident override",
    ),
    # --- cache / rate-limit ---
    _task(
        "IndustrialSOFL.CdnCache",
        "cdn_cache_policy",
        inputs=[("hit_rate", "int"), ("size_mb", "int"), ("ttl", "int")],
        outputs=[("action", "int"), ("ttl_new", "int")],
        scenarios=[
            ("ttl le 0", "action eq 2 && ttl_new eq 0"),
            ("hit_rate ge 15 && size_mb le 5", "action eq 1 && ttl_new eq 10"),
            ("hit_rate ge 8 && ttl le 5", "action eq 1 && ttl_new eq 8"),
            ("size_mb ge 12", "action eq 2 && ttl_new eq 0"),
        ],
        source="li2023iet_faultprevention",
        section="RF pattern: resource lifecycle (CDN cache)",
    ),
    _task(
        "IndustrialSOFL.ApiRateLimit",
        "limit_api_rate",
        inputs=[("rps", "int"), ("burst", "int"), ("plan", "int")],
        outputs=[("allow", "int"), ("retry_after", "int")],
        scenarios=[
            ("plan ge 3", "allow eq 1 && retry_after eq 0"),
            ("rps gt 15 && burst gt 8", "allow eq 0 && retry_after eq 10"),
            ("rps gt 10 && plan ge 2", "allow eq 1 && retry_after eq 2"),
            ("rps gt 10", "allow eq 0 && retry_after eq 5"),
        ],
        source="industrial_pattern:cache_rate_limit",
        section="API gateway rate limit with plan override",
    ),
    # --- library (SOFL classic) ---
    _task(
        "IndustrialSOFL.LibraryBorrow",
        "library_borrow",
        inputs=[("member_ok", "int"), ("copies", "int"), ("fines", "int")],
        outputs=[("loaned", "int"), ("block", "int")],
        scenarios=[
            ("member_ok eq 0", "loaned eq 0 && block eq 1"),
            ("fines ge 5", "loaned eq 0 && block eq 1"),
            ("copies ge 1 && fines le 2", "loaned eq 1 && block eq 0"),
            ("copies ge 1", "loaned eq 0 && block eq 1"),
        ],
        source="liu2004soflbook",
        section="Classic SOFL library borrow with fine / copy guards",
    ),
    _task(
        "IndustrialSOFL.LibraryRenew",
        "library_renew",
        inputs=[("times_renewed", "int"), ("holds", "int"), ("overdue_d", "int")],
        outputs=[("renewed", "int"), ("due_extend", "int")],
        scenarios=[
            ("holds ge 1", "renewed eq 0 && due_extend eq 0"),
            ("overdue_d ge 3", "renewed eq 0 && due_extend eq 0"),
            ("times_renewed ge 3", "renewed eq 0 && due_extend eq 0"),
            ("times_renewed le 2 && overdue_d eq 0", "renewed eq 1 && due_extend eq 2"),
        ],
        source="liu2004soflbook",
        section="Library renew policy (holds preempt renewals)",
    ),
    # --- water tank / process control ---
    _task(
        "IndustrialSOFL.TankLevel",
        "control_tank_level",
        inputs=[("level", "int"), ("inflow", "int"), ("demand", "int")],
        outputs=[("pump", "int"), ("drain", "int")],
        scenarios=[
            ("level ge 16", "pump eq 0 && drain eq 1"),
            ("level ge 12 && demand lt inflow", "pump eq 0 && drain eq 1"),
            ("level le 4 && inflow gt 0", "pump eq 1 && drain eq 0"),
            ("level ge 5 && level le 11", "pump eq 0 && drain eq 0"),
        ],
        source="liu2004soflbook",
        section="Process-control water tank (monitoring / CDFD style)",
    ),
    _task(
        "IndustrialSOFL.BoilerInterlock",
        "boiler_interlock",
        inputs=[("pressure", "int"), ("flame", "int"), ("water_ok", "int")],
        outputs=[("fuel", "int"), ("lockout", "int")],
        scenarios=[
            ("water_ok eq 0", "fuel eq 0 && lockout eq 1"),
            ("pressure ge 14", "fuel eq 0 && lockout eq 1"),
            ("flame eq 0 && pressure ge 5", "fuel eq 0 && lockout eq 0"),
            ("flame eq 1 && pressure le 12", "fuel eq 1 && lockout eq 0"),
        ],
        source="industrial_pattern:water_tank_process",
        section="Boiler fuel interlock (safety-first ordered guards)",
    ),
    # --- fraud screen ---
    _task(
        "IndustrialSOFL.CardFraud",
        "screen_card_fraud",
        inputs=[("amount", "int"), ("velocity", "int"), ("geo_risk", "int")],
        outputs=[("block", "int"), ("challenge", "int")],
        scenarios=[
            ("geo_risk ge 4", "block eq 1 && challenge eq 0"),
            ("amount ge 12 && velocity ge 6", "block eq 1 && challenge eq 0"),
            ("amount ge 6 && velocity ge 3", "block eq 0 && challenge eq 1"),
            ("amount le 5", "block eq 0 && challenge eq 0"),
        ],
        source="li2023iet_faultprevention",
        section="RF pattern: payment fraud boundary screening",
    ),
    _task(
        "IndustrialSOFL.LoginAnomaly",
        "score_login_anomaly",
        inputs=[("fail_count", "int"), ("new_device", "int"), ("geo_shift", "int")],
        outputs=[("lock", "int"), ("mfa", "int")],
        scenarios=[
            ("fail_count ge 5", "lock eq 1 && mfa eq 0"),
            ("new_device eq 1 && geo_shift eq 1", "lock eq 0 && mfa eq 1"),
            ("fail_count ge 3 || geo_shift eq 1", "lock eq 0 && mfa eq 1"),
            ("new_device eq 1", "lock eq 0 && mfa eq 1"),
        ],
        source="industrial_pattern:fraud_screen",
        section="Identity login anomaly / step-up authentication",
    ),
    # --- enrollment ---
    _task(
        "IndustrialSOFL.CourseEnroll",
        "enroll_course",
        inputs=[("credits", "int"), ("prereq", "int"), ("seats", "int")],
        outputs=[("enrolled", "int"), ("waitlist", "int")],
        scenarios=[
            ("prereq eq 0", "enrolled eq 0 && waitlist eq 0"),
            ("seats le 0 && credits le 15", "enrolled eq 0 && waitlist eq 1"),
            ("credits ge 12 && seats ge 1", "enrolled eq 1 && waitlist eq 0"),
            ("seats ge 1", "enrolled eq 1 && waitlist eq 0"),
        ],
        source="liu2004soflbook",
        section="Academic enrollment / registration workflow",
    ),
    _task(
        "IndustrialSOFL.BenefitEnroll",
        "enroll_benefit",
        inputs=[("tenure_y", "int"), ("hours", "int"), ("open_enroll", "int")],
        outputs=[("eligible", "int"), ("plan", "int")],
        scenarios=[
            ("open_enroll eq 0 && tenure_y lt 1", "eligible eq 0 && plan eq 0"),
            ("hours ge 12 && tenure_y ge 1", "eligible eq 1 && plan eq 2"),
            ("hours ge 8 && open_enroll eq 1", "eligible eq 1 && plan eq 1"),
            ("tenure_y ge 3", "eligible eq 1 && plan eq 1"),
        ],
        source="industrial_pattern:enrollment",
        section="Employee benefits enrollment eligibility ladder",
    ),
    # --- salary / bonus ---
    _task(
        "IndustrialSOFL.BonusAward",
        "award_bonus",
        inputs=[("perf", "int"), ("years", "int"), ("budget_ok", "int")],
        outputs=[("bonus_pct", "int"), ("raise_pct", "int")],
        scenarios=[
            ("budget_ok eq 0", "bonus_pct eq 0 && raise_pct eq 0"),
            ("perf ge 5 && years ge 5", "bonus_pct eq 15 && raise_pct eq 8"),
            ("perf ge 5", "bonus_pct eq 12 && raise_pct eq 5"),
            ("perf ge 3 && years ge 8", "bonus_pct eq 8 && raise_pct eq 6"),
        ],
        source="industrial_pattern:salary_bonus",
        section="HR bonus / raise matrix with budget kill-switch",
    ),
    _task(
        "IndustrialSOFL.OvertimePay",
        "compute_overtime",
        inputs=[("hours", "int"), ("night", "int"), ("holiday", "int")],
        outputs=[("mult_x10", "int"), ("premium", "int")],
        scenarios=[
            ("holiday eq 1", "mult_x10 eq 20 && premium eq 1"),
            ("night eq 1 && hours gt 8", "mult_x10 eq 15 && premium eq 1"),
            ("hours gt 8", "mult_x10 eq 15 && premium eq 0"),
            ("hours le 8 && night eq 1", "mult_x10 eq 12 && premium eq 1"),
        ],
        source="industrial_pattern:salary_bonus",
        section="Payroll overtime / night / holiday multipliers (x10 scale)",
    ),
]


def load_industrial_sofl_tasks() -> list[dict[str, Any]]:
    return list(INDUSTRIAL_SOFL_TASKS)
