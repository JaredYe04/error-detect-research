"""Published industrial SOFL pilot corpus (vendor-adjacent).

Reconstructed ordered-guard FSF processes from *published* industrial SOFL
case studies (railway crossing / interlocking, ATM, hotel, banking).

Honesty contract
----------------
- These are NOT proprietary Casco / Mitsubishi / Nippon Signal dumps.
- Guards and decision tables are reconstructed from publicly described
  industrial SOFL applications so the evaluation harness can run a
  "published-industrial pilot" without NDA access.
- When ``vendor/agile-sofl-toolchain/examples/*.asfl`` is available, prefer
  ``src.asfl_bridge.collect_tasks_from_examples`` and merge via
  ``scripts/import_vendor_asfl.py``.

Provenance tags use real bibliographic keys (see bib/references.bib).
"""

from __future__ import annotations

from typing import Any

from src.benchmarks.industrial_sofl_corpus import _task


# Compact integer encodings of published industrial decision tables.
PUBLISHED_INDUSTRIAL_PILOT_TASKS: list[dict[str, Any]] = [
    # --- Railway crossing controller (Liu/Asuka/Mitsubishi industrial trial) ---
    _task(
        "PubIndPilot.CrossingApproach",
        "crossing_approach",
        inputs=[("train_dist", "int"), ("gate_pos", "int"), ("fault", "int")],
        outputs=[("cmd", "int"), ("alarm", "int")],
        scenarios=[
            # fault preempts all motion commands
            ("fault gt 0", "cmd eq 0 && alarm eq 2"),
            # train near + gate open -> close / warn
            ("train_dist le 3 && gate_pos ge 2", "cmd eq 2 && alarm eq 1"),
            # train near + gate closing -> hold warn
            ("train_dist le 3 && gate_pos eq 1", "cmd eq 1 && alarm eq 1"),
            # train clear + gate closed -> open
            ("train_dist ge 8 && gate_pos eq 0", "cmd eq 3 && alarm eq 0"),
        ],
        source="liu1998railwaycrossing",
        section="Railway crossing controller industrial trial (Mitsubishi); "
        "FSF reconstruction of approach/clear/fault priority",
    ),
    _task(
        "PubIndPilot.CrossingClear",
        "crossing_clear_check",
        inputs=[("occupancy", "int"), ("gate_pos", "int"), ("timer", "int")],
        outputs=[("permit", "int"), ("status", "int")],
        scenarios=[
            ("occupancy gt 0", "permit eq 0 && status eq 2"),
            ("gate_pos gt 0", "permit eq 0 && status eq 1"),
            ("timer lt 2", "permit eq 0 && status eq 1"),
            ("occupancy eq 0 && gate_pos eq 0 && timer ge 2", "permit eq 1 && status eq 0"),
        ],
        source="liu1998railwaycrossing",
        section="Clearance permit under occupancy/gate/timer constraints",
    ),
    # --- Railway interlocking (Luo/Liu/Casco Signal, SOFL 2017) ---
    _task(
        "PubIndPilot.RouteLock",
        "route_lock",
        inputs=[("route_req", "int"), ("conflict", "int"), ("point_ok", "int")],
        outputs=[("locked", "int"), ("reject", "int")],
        scenarios=[
            ("conflict gt 0", "locked eq 0 && reject eq 2"),
            ("point_ok eq 0", "locked eq 0 && reject eq 1"),
            ("route_req gt 0 && conflict eq 0 && point_ok gt 0", "locked eq 1 && reject eq 0"),
        ],
        source="luo2017railway",
        section="Casco interlocking route-lock decision (published SOFL case); "
        "conflict preempts lock",
    ),
    _task(
        "PubIndPilot.SignalAspect",
        "signal_aspect",
        inputs=[("route_locked", "int"), ("block_clear", "int"), ("override", "int")],
        outputs=[("aspect", "int"), ("restrict", "int")],
        scenarios=[
            ("override gt 0", "aspect eq 0 && restrict eq 1"),
            ("route_locked eq 0", "aspect eq 0 && restrict eq 1"),
            ("route_locked gt 0 && block_clear eq 0", "aspect eq 1 && restrict eq 1"),
            ("route_locked gt 0 && block_clear gt 0", "aspect eq 2 && restrict eq 0"),
        ],
        source="luo2017railway",
        section="Signal aspect selection under lock/block/override priority",
    ),
    _task(
        "PubIndPilot.PointMove",
        "point_move_permit",
        inputs=[("locked", "int"), ("occupied", "int"), ("cmd", "int")],
        outputs=[("move", "int"), ("deny", "int")],
        scenarios=[
            ("locked gt 0", "move eq 0 && deny eq 2"),
            ("occupied gt 0", "move eq 0 && deny eq 1"),
            ("cmd gt 0 && locked eq 0 && occupied eq 0", "move eq 1 && deny eq 0"),
        ],
        source="luo2017railway",
        section="Point (switch) move permit; lock/occupancy preempt command",
    ),
    # --- ATM (Liu SOFL book / industrial teaching cases) ---
    _task(
        "PubIndPilot.AtmAuth",
        "atm_auth",
        inputs=[("pin_ok", "int"), ("card_ok", "int"), ("tries", "int")],
        outputs=[("auth", "int"), ("retain", "int")],
        scenarios=[
            ("card_ok eq 0", "auth eq 0 && retain eq 1"),
            ("tries ge 3", "auth eq 0 && retain eq 1"),
            ("pin_ok eq 0", "auth eq 0 && retain eq 0"),
            ("pin_ok gt 0 && card_ok gt 0 && tries lt 3", "auth eq 1 && retain eq 0"),
        ],
        source="liu2004soflbook",
        section="ATM authentication FSF (book industrial example pattern)",
    ),
    _task(
        "PubIndPilot.AtmWithdraw",
        "atm_withdraw_pilot",
        inputs=[("auth", "int"), ("balance", "int"), ("amount", "int")],
        outputs=[("cash", "int"), ("status", "int")],
        scenarios=[
            ("auth eq 0", "cash eq 0 && status eq 2"),
            ("amount le 0", "cash eq 0 && status eq 1"),
            ("amount gt balance", "cash eq 0 && status eq 1"),
            ("auth gt 0 && amount gt 0 && amount le balance", "cash eq 1 && status eq 0"),
        ],
        source="liu2004soflbook",
        section="ATM withdraw under auth/balance guards",
    ),
    # --- Hotel reservation (published SOFL application) ---
    _task(
        "PubIndPilot.HotelBook",
        "hotel_book",
        inputs=[("rooms", "int"), ("nights", "int"), ("vip", "int")],
        outputs=[("booked", "int"), ("rate", "int")],
        scenarios=[
            ("rooms le 0", "booked eq 0 && rate eq 0"),
            ("nights le 0", "booked eq 0 && rate eq 0"),
            ("vip gt 0 && rooms gt 0 && nights gt 0", "booked eq 1 && rate eq 1"),
            ("rooms gt 0 && nights gt 0", "booked eq 1 && rate eq 2"),
        ],
        source="liu_sofl_hotel",
        section="Hotel reservation SOFL application (Liu research applications list)",
    ),
    # --- Online banking (published SOFL course/industrial modelling) ---
    _task(
        "PubIndPilot.TransferGuard",
        "transfer_guard",
        inputs=[("balance", "int"), ("amount", "int"), ("daily_left", "int")],
        outputs=[("ok", "int"), ("reason", "int")],
        scenarios=[
            ("amount le 0", "ok eq 0 && reason eq 1"),
            ("amount gt balance", "ok eq 0 && reason eq 2"),
            ("amount gt daily_left", "ok eq 0 && reason eq 3"),
            ("amount gt 0 && amount le balance && amount le daily_left", "ok eq 1 && reason eq 0"),
        ],
        source="liu_sofl_online_banking",
        section="Online banking transfer guards (published SOFL modelling case)",
    ),
    _task(
        "PubIndPilot.FraudHold",
        "fraud_hold",
        inputs=[("risk", "int"), ("amount", "int"), ("new_device", "int")],
        outputs=[("hold", "int"), ("challenge", "int")],
        scenarios=[
            ("risk ge 8", "hold eq 1 && challenge eq 2"),
            ("new_device gt 0 && amount ge 5", "hold eq 1 && challenge eq 1"),
            ("risk ge 5 && amount ge 8", "hold eq 1 && challenge eq 1"),
            ("risk lt 5", "hold eq 0 && challenge eq 0"),
        ],
        source="liu_sofl_online_banking",
        section="Fraud hold priority over routine transfer clearance",
    ),
]


def load_published_industrial_pilot_tasks() -> list[dict[str, Any]]:
    """Return a copy of the published-industrial pilot task list."""
    import copy

    return copy.deepcopy(PUBLISHED_INDUSTRIAL_PILOT_TASKS)
