"""Mini-Z adapter for the SgDP generalisation study (E8b).

Mini-Z is a simplified subset of Z notation that captures the essential
spec-guided ordering structure relevant to specification-conformance defects:
ordered precondition cases with deterministic output assignments.

This adapter translates Mini-Z schemas into SpecIR so the shared pipeline
runs without modification via FSFLowerer.

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
from src.ir.spec_ir import GuardAtom, GuardedCase, Param, SpecIR

# Unicode → ASCII equivalents for normalisation
_UNICODE_MAP: dict[str, str] = {
    "≤": " le ",
    "≥": " ge ",
    "≠": " ne ",
    "=": " eq ",
    "∧": " && ",
    "∨": " || ",
    "¬": "not ",
    "⟹": "=>",
    "→": "=>",
    "ℤ": "int",
    "ℕ": "nat",
}


def _normalise(text: str) -> str:
    """Normalise Unicode Z-notation symbols to ASCII equivalents."""
    # Protect the arrow sentinel before doing '=' substitution
    text = text.replace("=>", "\x00ARROW\x00")
    for uni, asc in _UNICODE_MAP.items():
        if uni == "=":
            continue  # handle standalone '=' last
        text = text.replace(uni, asc)
    text = text.replace("=", " eq ")
    text = text.replace("\x00ARROW\x00", "=>")
    return text


def _parse_guard_atoms(guard_text: str) -> list[GuardAtom]:
    """Parse a guard string like 'price ge 100 && loyalty ge 5' into GuardAtoms."""
    atoms = []
    for part in re.split(r"\s*&&\s*", guard_text.strip()):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^(\w+)\s+(eq|ne|lt|le|gt|ge)\s+(.+)$", part)
        if m:
            var, op, thr = m.groups()
            thr = thr.strip()
            try:
                threshold: int | float | str = int(thr)
            except ValueError:
                try:
                    threshold = float(thr)
                except ValueError:
                    threshold = thr
            atoms.append(GuardAtom(var=var, op=op, threshold=threshold))
        else:
            atoms.append(GuardAtom(var=part, op="eq", threshold=None))
    return atoms or [GuardAtom(var="", op="others")]


def _parse_post_dict(post_text: str) -> dict[str, Any]:
    """Parse postcondition 'a eq 1 && b eq 2' into dict (best-effort, literals only)."""
    result: dict[str, Any] = {}
    for part in re.split(r"\s*&&\s*", post_text.strip()):
        m = re.match(r"^(\w+)\s+eq\s+(.+)$", part.strip())
        if m:
            var, val = m.groups()
            val = val.strip()
            try:
                result[var] = int(val)
            except ValueError:
                try:
                    result[var] = float(val)
                except ValueError:
                    result[var] = val
    return result


class MiniZAdapter(SpecAdapter):
    """Adapter: Mini-Z schema → SpecIR → FSF-style TaskSpec."""

    @property
    def notation_name(self) -> str:
        return "mini_z"

    def parse(self, spec_text: str, task_id: str) -> SpecIR:
        """Parse a Mini-Z SCHEMA spec into SpecIR."""
        spec_text = _normalise(spec_text)
        lines = [
            ln.strip()
            for ln in spec_text.splitlines()
            if ln.strip() and not ln.strip().startswith("--")
        ]

        inputs: list[dict[str, str]] = []
        outputs: list[dict[str, str]] = []
        raw_cases: list[tuple[str, str]] = []  # (guard_text, post_text)
        default_def: str | None = None
        schema_name = task_id.replace("-", "_").replace(".", "_")

        for line in lines:
            up = line.upper()
            if up.startswith("SCHEMA"):
                parts = line.split(None, 1)
                if len(parts) > 1:
                    schema_name = parts[1].strip()
            elif up.startswith("INPUTS:"):
                rest = line[len("INPUTS:"):].strip()
                for var_spec in rest.split(","):
                    m = re.match(r"\s*(\w+)\s*:\s*\w+", var_spec)
                    if m:
                        inputs.append({"name": m.group(1), "type": "nat"})
            elif up.startswith("OUTPUTS:"):
                rest = line[len("OUTPUTS:"):].strip()
                for var_spec in rest.split(","):
                    m = re.match(r"\s*(\w+)\s*:\s*\w+", var_spec)
                    if m:
                        outputs.append({"name": m.group(1), "type": "nat"})
            elif up.startswith("CASE"):
                rest = line[4:].strip()
                if "=>" in rest:
                    guard, definition = rest.split("=>", 1)
                    raw_cases.append((guard.strip(), definition.strip()))
            elif up.startswith("DEFAULT"):
                default_def = line[len("DEFAULT"):].strip()

        # Fallback vars if no signature found
        if not inputs:
            inputs = [{"name": "x", "type": "nat"}, {"name": "y", "type": "nat"}]
        if not outputs:
            outputs = [{"name": "result", "type": "nat"}]

        # Build GuardedCase list
        cases: list[GuardedCase] = []
        for idx, (guard_text, post_text) in enumerate(raw_cases, 1):
            guard_atoms = _parse_guard_atoms(guard_text)
            post_dict = _parse_post_dict(post_text)
            cases.append(GuardedCase(
                index=idx,
                guard=guard_atoms,
                postcondition=post_dict,
                guard_text=guard_text,
                post_text=post_text,
            ))

        # Add DEFAULT as "others" case
        if default_def is not None:
            post_dict = _parse_post_dict(default_def)
            cases.append(GuardedCase(
                index=len(cases) + 1,
                guard=[GuardAtom(var="", op="others")],
                postcondition=post_dict,
                guard_text="others",
                post_text=default_def,
            ))

        # Build surface prompt
        in_str = ", ".join(p["name"] for p in inputs)
        out_names = ", ".join(p["name"] for p in outputs)
        prompt_lines = [
            f"Process {schema_name}({in_str}) \u2192 ({out_names})",
            "Z-notation ordered cases (first matching case wins):",
        ]
        for c in cases:
            if c.guard and c.guard[0].op == "others":
                prompt_lines.append(f"  default: {c.post_text}")
            else:
                prompt_lines.append(f"  CASE ({c.guard_text}) \u27f9 {c.post_text}")
        prompt_lines.append("\nIMPORTANT: evaluate cases in the listed order.")
        surface_prompt = "\n".join(prompt_lines)

        return SpecIR(
            task_id=task_id,
            notation="mini_z",
            name=f"MiniZ.{schema_name}",
            inputs=[Param(p["name"], p["type"]) for p in inputs],
            outputs=[Param(p["name"], p["type"]) for p in outputs],
            cases=cases,
            surface_prompt=surface_prompt,
            metadata={
                "module": "MiniZ",
                "source_basename": "mini_z-derived",
                "source_file": f"mini_z://{schema_name}",
            },
        )


# ── Built-in Mini-Z task corpus (30 schemas) ──────────────────────────────────

_EXTRA_MINIZ_SPECS: list[str] = [
    """\
SCHEMA TaxBracket
INPUTS: income: int, dependents: int, region: int
OUTPUTS: rate: int, credit: int

CASE income le 0                                    => rate eq 0 && credit eq 0
CASE dependents ge 3 && income le 20000             => rate eq 5 && credit eq 30
CASE income le 40000 && region le 1                 => rate eq 10 && credit eq 10
CASE income le 80000                                => rate eq 20 && credit eq 5
DEFAULT rate eq 30 && credit eq 0
""",
    """\
SCHEMA RefundPolicy
INPUTS: days: int, condition: int, price: int
OUTPUTS: refund_pct: int, fee: int

CASE days le 7 && condition eq 1                    => refund_pct eq 100 && fee eq 0
CASE days le 14 && condition eq 1                   => refund_pct eq 80 && fee eq 5
CASE days le 30 && price gt 100                     => refund_pct eq 50 && fee eq 10
DEFAULT refund_pct eq 0 && fee eq 15
""",
    """\
SCHEMA SeatAssign
INPUTS: party: int, vip: int, available: int
OUTPUTS: section: int, priority: int

CASE vip eq 1 && available ge party               => section eq 3 && priority eq 1
CASE party ge 6 && available ge party             => section eq 2 && priority eq 2
CASE available ge party                             => section eq 1 && priority eq 3
DEFAULT section eq 0 && priority eq 0
""",
    """\
SCHEMA LoanTier
INPUTS: score: int, collateral: int, term: int
OUTPUTS: tier: int, apr: int

CASE score lt 550                                   => tier eq 0 && apr eq 0
CASE score ge 750 && collateral ge 50               => tier eq 3 && apr eq 5
CASE score ge 650 && term le 12                     => tier eq 2 && apr eq 8
DEFAULT tier eq 1 && apr eq 12
""",
    """\
SCHEMA AlertLevel
INPUTS: metric: int, baseline: int, spike: int
OUTPUTS: level: int, page: int

CASE metric gt baseline + spike && spike gt 10      => level eq 3 && page eq 1
CASE metric gt baseline + spike                     => level eq 2 && page eq 0
CASE metric gt baseline                             => level eq 1 && page eq 0
DEFAULT level eq 0 && page eq 0
""",
    """\
SCHEMA CouponApply
INPUTS: subtotal: int, coupon: int, member: int
OUTPUTS: discount: int, payable: int

CASE coupon ge 50 && subtotal ge 200                => discount eq 50 && payable eq subtotal - 50
CASE coupon ge 20 && member ge 2                    => discount eq 20 && payable eq subtotal - 20
CASE coupon ge 10                                   => discount eq 10 && payable eq subtotal - 10
DEFAULT discount eq 0 && payable eq subtotal
""",
    """\
SCHEMA ShiftAssign
INPUTS: skill: int, availability: int, demand: int
OUTPUTS: shift: int, overtime: int

CASE skill ge 5 && availability eq 1 && demand ge 3 => shift eq 2 && overtime eq 1
CASE skill ge 3 && availability eq 1                  => shift eq 1 && overtime eq 0
CASE demand ge 5                                    => shift eq 2 && overtime eq 1
DEFAULT shift eq 0 && overtime eq 0
""",
    """\
SCHEMA WarrantyClaim
INPUTS: months: int, defect: int, misuse: int
OUTPUTS: covered: int, payout: int

CASE misuse eq 1                                    => covered eq 0 && payout eq 0
CASE months le 12 && defect eq 1                    => covered eq 1 && payout eq 100
CASE months le 24 && defect eq 1                    => covered eq 1 && payout eq 50
DEFAULT covered eq 0 && payout eq 0
""",
    """\
SCHEMA ParkingFee
INPUTS: minutes: int, zone: int, permit: int
OUTPUTS: fee: int, valid: int

CASE permit eq 1                                    => fee eq 0 && valid eq 1
CASE zone ge 3 && minutes gt 120                    => fee eq 40 && valid eq 1
CASE minutes gt 60                                  => fee eq 20 && valid eq 1
DEFAULT fee eq 5 && valid eq 1
""",
    """\
SCHEMA RiskScore
INPUTS: exposure: int, volatility: int, hedge: int
OUTPUTS: score: int, action: int

CASE exposure gt 80 && hedge lt 20                    => score eq 90 && action eq 2
CASE volatility gt 50 && exposure gt 50           => score eq 70 && action eq 1
CASE exposure gt 30                                   => score eq 40 && action eq 1
DEFAULT score eq 10 && action eq 0
""",
    """\
SCHEMA BatchRelease
INPUTS: passed: int, failed: int, sample: int
OUTPUTS: release: int, rework: int

CASE failed gt 0 && sample lt 10                    => release eq 0 && rework eq 1
CASE passed ge 95 && failed eq 0                    => release eq 1 && rework eq 0
CASE passed ge 80                                   => release eq 1 && rework eq 0
DEFAULT release eq 0 && rework eq 1
""",
    """\
SCHEMA LoyaltyTier
INPUTS: points: int, tenure: int, complaints: int
OUTPUTS: tier: int, bonus: int

CASE complaints ge 3                                => tier eq 0 && bonus eq 0
CASE points ge 1000 && tenure ge 5                  => tier eq 3 && bonus eq 50
CASE points ge 500                                  => tier eq 2 && bonus eq 20
DEFAULT tier eq 1 && bonus eq 5
""",
]

BUILTIN_MINIZ_TASKS_SPEC: list[str] = [
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
    """\
SCHEMA FileAccess
INPUTS: role: int, file_type: int, classification: int
OUTPUTS: permission: int, audit: int, allowed: int

CASE classification ge 3 && role lt 3           => permission eq 0 && audit eq 1 && allowed eq 0
CASE role ge 5 && classification ge 2            => permission eq 3 && audit eq 1 && allowed eq 1
CASE role ge 3 && file_type le 2                 => permission eq 2 && audit eq 1 && allowed eq 1
CASE role ge 3 && file_type gt 2                 => permission eq 1 && audit eq 0 && allowed eq 1
CASE role ge 2 && file_type le 1                 => permission eq 1 && audit eq 0 && allowed eq 1
DEFAULT permission eq 0 && audit eq 0 && allowed eq 0
""",
    """\
SCHEMA PacketRoute
INPUTS: protocol: int, port: int, priority: int
OUTPUTS: route: int, action: int, queue: int

CASE protocol eq 0                               => route eq 0 && action eq 3 && queue eq 0
CASE priority ge 8 && protocol eq 1              => route eq 1 && action eq 2 && queue eq 0
CASE protocol eq 1 && port le 1024               => route eq 2 && action eq 1 && queue eq 1
CASE protocol eq 2 && priority ge 5              => route eq 3 && action eq 1 && queue eq 1
CASE port gt 1024 && priority lt 3               => route eq 4 && action eq 0 && queue eq 2
DEFAULT route eq 2 && action eq 0 && queue eq 1
""",
    """\
SCHEMA InsureRate
INPUTS: age: int, risk_factor: int, claims: int
OUTPUTS: rate: int, surcharge: int, tier: int

CASE claims ge 5                                 => rate eq 0 && surcharge eq 0 && tier eq 0
CASE age lt 25 && risk_factor ge 4               => rate eq 90 && surcharge eq 30 && tier eq 4
CASE age lt 25 && risk_factor ge 2               => rate eq 70 && surcharge eq 15 && tier eq 3
CASE age ge 70 && risk_factor ge 3               => rate eq 75 && surcharge eq 20 && tier eq 3
CASE age ge 70                                   => rate eq 55 && surcharge eq 10 && tier eq 2
CASE risk_factor ge 4                            => rate eq 60 && surcharge eq 15 && tier eq 3
CASE risk_factor ge 2                            => rate eq 40 && surcharge eq 5  && tier eq 2
DEFAULT rate eq 25 && surcharge eq 0 && tier eq 1
""",
    """\
SCHEMA LibraryLoan
INPUTS: membership: int, book_type: int, overdue: int
OUTPUTS: loan_days: int, renewable: int, fee: int

CASE overdue ge 3                                => loan_days eq 0 && renewable eq 0 && fee eq 10
CASE membership ge 3 && book_type le 1           => loan_days eq 28 && renewable eq 1 && fee eq 0
CASE membership ge 3 && book_type eq 2           => loan_days eq 14 && renewable eq 1 && fee eq 0
CASE membership ge 2 && book_type le 1           => loan_days eq 21 && renewable eq 1 && fee eq 0
CASE membership ge 2                             => loan_days eq 14 && renewable eq 0 && fee eq 0
CASE book_type ge 3                              => loan_days eq 7  && renewable eq 0 && fee eq 2
DEFAULT loan_days eq 14 && renewable eq 0 && fee eq 0
""",
    """\
SCHEMA InvReorder
INPUTS: stock: int, demand: int, lead_time: int
OUTPUTS: order_qty: int, urgent: int, status: int

CASE stock le 0 && demand gt 0                   => order_qty eq 100 && urgent eq 1 && status eq 3
CASE stock le 10 && demand ge 50                 => order_qty eq 80  && urgent eq 1 && status eq 2
CASE stock le 10 && lead_time le 2               => order_qty eq 60  && urgent eq 1 && status eq 2
CASE stock le 30 && demand ge 30                 => order_qty eq 40  && urgent eq 0 && status eq 1
CASE stock le 50 && demand ge 20                 => order_qty eq 20  && urgent eq 0 && status eq 1
DEFAULT order_qty eq 0 && urgent eq 0 && status eq 0
""",
    """\
SCHEMA TicketPrice
INPUTS: event_type: int, seat_zone: int, early_bird: int
OUTPUTS: price_tier: int, discount: int, vip: int

CASE event_type ge 3 && seat_zone ge 3 && early_bird eq 1 => price_tier eq 5 && discount eq 20 && vip eq 1
CASE event_type ge 3 && seat_zone ge 3           => price_tier eq 5 && discount eq 0 && vip eq 1
CASE event_type ge 3 && early_bird eq 1          => price_tier eq 4 && discount eq 15 && vip eq 0
CASE event_type ge 2 && seat_zone ge 3           => price_tier eq 3 && discount eq 10 && vip eq 0
CASE event_type ge 2 && early_bird eq 1          => price_tier eq 2 && discount eq 10 && vip eq 0
CASE seat_zone ge 2                              => price_tier eq 2 && discount eq 0 && vip eq 0
DEFAULT price_tier eq 1 && discount eq 0 && vip eq 0
""",
    """\
SCHEMA EnrollEligible
INPUTS: credits: int, gpa: int, status: int
OUTPUTS: eligibility: int, units: int, flag: int

CASE status eq 0                                 => eligibility eq 0 && units eq 0 && flag eq 2
CASE credits ge 90 && gpa ge 35                  => eligibility eq 3 && units eq 18 && flag eq 0
CASE credits ge 60 && gpa ge 30                  => eligibility eq 2 && units eq 15 && flag eq 0
CASE credits ge 30 && gpa ge 25                  => eligibility eq 1 && units eq 12 && flag eq 0
CASE gpa lt 20                                   => eligibility eq 0 && units eq 0 && flag eq 1
DEFAULT eligibility eq 1 && units eq 9 && flag eq 0
""",
    """\
SCHEMA MedDosage
INPUTS: weight: int, age: int, condition: int
OUTPUTS: dose_level: int, frequency: int, warning: int

CASE condition ge 3 && age lt 12                 => dose_level eq 0 && frequency eq 0 && warning eq 2
CASE age lt 12 && weight lt 20                   => dose_level eq 1 && frequency eq 2 && warning eq 1
CASE age lt 12                                   => dose_level eq 2 && frequency eq 3 && warning eq 1
CASE age ge 75 && condition ge 2                 => dose_level eq 2 && frequency eq 2 && warning eq 1
CASE weight ge 100 && condition ge 2             => dose_level eq 4 && frequency eq 3 && warning eq 0
CASE weight ge 70                                => dose_level eq 3 && frequency eq 3 && warning eq 0
DEFAULT dose_level eq 2 && frequency eq 2 && warning eq 0
""",
]


BUILTIN_MINIZ_TASKS_SPEC: list[str] = BUILTIN_MINIZ_TASKS_SPEC + _EXTRA_MINIZ_SPECS  # type: ignore[misc]


def load_builtin_miniz_tasks() -> list[dict[str, Any]]:
    """Return the 30 built-in Mini-Z tasks as TaskSpec dicts."""
    from src.ir.lowerers.fsf_lowerer import FSFLowerer
    adapter = MiniZAdapter()
    tasks = []
    for i, spec_text in enumerate(BUILTIN_MINIZ_TASKS_SPEC, start=1):
        task_id = f"MZ{i:03d}"
        try:
            spec_ir = adapter.parse(spec_text, task_id)
            task = FSFLowerer.lower(spec_ir)
            from src.benchmarks.reference_gen import generate_reference_code
            task["referenceCode"] = generate_reference_code(task)
            tasks.append(task)
        except Exception as e:
            print(f"[MZ] Failed to parse {task_id}: {e}")
    return tasks
