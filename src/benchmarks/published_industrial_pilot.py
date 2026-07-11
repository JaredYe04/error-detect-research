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
    # =========================================================================
    # Wave-2 expansion (2026-07): desensitized reconstructions from additional
    # *public* SOFL / interlocking / Agile-SOFL sources. Compact integer scales;
    # no proprietary IDs, station names, or vendor dumps.
    # =========================================================================
    # --- Agile-SOFL ATM informal+formal example (Waseda Agile-SOFL PDF) ---
    _task(
        "PubIndPilot.AtmDeposit",
        "atm_deposit",
        inputs=[("auth", "int"), ("amount", "int"), ("cap", "int")],
        outputs=[("ok", "int"), ("status", "int")],
        scenarios=[
            ("auth eq 0", "ok eq 0 && status eq 2"),
            ("amount le 0", "ok eq 0 && status eq 1"),
            ("amount gt cap", "ok eq 0 && status eq 1"),
            ("auth gt 0 && amount gt 0 && amount le cap", "ok eq 1 && status eq 0"),
        ],
        source="li2022qrs_companion",
        section="Agile-SOFL ATM deposit constraints (public teaching/industrial "
        "example; amount cap mirrors published JPY limits scaled to ints)",
    ),
    _task(
        "PubIndPilot.AtmTransfer",
        "atm_transfer",
        inputs=[("auth", "int"), ("balance", "int"), ("amount", "int"), ("xfer_cap", "int")],
        outputs=[("ok", "int"), ("reason", "int")],
        scenarios=[
            ("auth eq 0", "ok eq 0 && reason eq 4"),
            ("amount le 0", "ok eq 0 && reason eq 1"),
            ("amount gt balance", "ok eq 0 && reason eq 2"),
            ("amount gt xfer_cap", "ok eq 0 && reason eq 3"),
            (
                "auth gt 0 && amount gt 0 && amount le balance && amount le xfer_cap",
                "ok eq 1 && reason eq 0",
            ),
        ],
        source="li2022qrs_companion",
        section="ATM/online transfer under auth/balance/cap (Agile-SOFL ATM "
        "transfer function; desensitized)",
    ),
    _task(
        "PubIndPilot.AtmInquire",
        "atm_inquire",
        inputs=[("auth", "int"), ("account_ok", "int")],
        outputs=[("show", "int"), ("deny", "int")],
        scenarios=[
            ("auth eq 0", "show eq 0 && deny eq 1"),
            ("account_ok eq 0", "show eq 0 && deny eq 1"),
            ("auth gt 0 && account_ok gt 0", "show eq 1 && deny eq 0"),
        ],
        source="li2022qrs_companion",
        section="ATM balance inquire; auth and account validity first",
    ),
    _task(
        "PubIndPilot.DailyWithdrawCap",
        "daily_withdraw_cap",
        inputs=[("auth", "int"), ("amount", "int"), ("remaining", "int")],
        outputs=[("cash", "int"), ("status", "int")],
        scenarios=[
            ("auth eq 0", "cash eq 0 && status eq 2"),
            ("amount le 0", "cash eq 0 && status eq 1"),
            ("amount gt remaining", "cash eq 0 && status eq 3"),
            (
                "auth gt 0 && amount gt 0 && amount le remaining",
                "cash eq 1 && status eq 0",
            ),
        ],
        source="li2022qrs_companion",
        section="Daily withdrawal remaining-cap check (Agile-SOFL constraint "
        "3.1 family; remaining = cap - used, desensitized)",
    ),
    # --- Extra interlocking decision tables (Luo/Casco + public interlocking lit) ---
    _task(
        "PubIndPilot.RouteConflict",
        "route_conflict_check",
        inputs=[("req_a", "int"), ("req_b", "int"), ("share_plat", "int")],
        outputs=[("conflict", "int"), ("allow", "int")],
        scenarios=[
            ("req_a gt 0 && req_b gt 0 && share_plat gt 0", "conflict eq 1 && allow eq 0"),
            ("req_a gt 0 && req_b eq 0", "conflict eq 0 && allow eq 1"),
            ("req_b gt 0 && req_a eq 0", "conflict eq 0 && allow eq 1"),
        ],
        source="luo2017railway",
        section="Conflicting routes sharing platform (industrial interlocking "
        "pattern; cf. published compositional interlocking examples)",
    ),
    _task(
        "PubIndPilot.FlankProtect",
        "flank_protect",
        inputs=[("route_set", "int"), ("flank_clear", "int"), ("override", "int")],
        outputs=[("proceed", "int"), ("block", "int")],
        scenarios=[
            ("override gt 0", "proceed eq 0 && block eq 2"),
            ("route_set eq 0", "proceed eq 0 && block eq 1"),
            ("flank_clear eq 0", "proceed eq 0 && block eq 1"),
            ("route_set gt 0 && flank_clear gt 0 && override eq 0", "proceed eq 1 && block eq 0"),
        ],
        source="luo2017railway",
        section="Flank protection gate before proceed (desensitized from "
        "public interlocking-table literature; SOFL-shaped FSF)",
    ),
    _task(
        "PubIndPilot.ApproachLock",
        "approach_lock",
        inputs=[("train_app", "int"), ("signal_clear", "int"), ("timer", "int")],
        outputs=[("locked", "int"), ("release", "int")],
        scenarios=[
            ("train_app gt 0 && signal_clear gt 0", "locked eq 1 && release eq 0"),
            ("train_app gt 0 && timer lt 3", "locked eq 1 && release eq 0"),
            ("train_app eq 0 && timer ge 3", "locked eq 0 && release eq 1"),
        ],
        source="liu1998railwaycrossing",
        section="Approach locking / timed release (railway crossing + "
        "interlocking public patterns)",
    ),
    _task(
        "PubIndPilot.SignalClear",
        "signal_clear_permit",
        inputs=[("route_ok", "int"), ("track_clear", "int"), ("fault", "int")],
        outputs=[("clear", "int"), ("restrict", "int")],
        scenarios=[
            ("fault gt 0", "clear eq 0 && restrict eq 2"),
            ("route_ok eq 0", "clear eq 0 && restrict eq 1"),
            ("track_clear eq 0", "clear eq 0 && restrict eq 1"),
            ("route_ok gt 0 && track_clear gt 0 && fault eq 0", "clear eq 1 && restrict eq 0"),
        ],
        source="luo2017railway",
        section="Signal clear only when route+track OK and no fault",
    ),
    # --- Liu SOFL book classic industrial teaching cases ---
    _task(
        "PubIndPilot.LibraryBorrow",
        "library_borrow",
        inputs=[("member_ok", "int"), ("copies", "int"), ("overdue", "int")],
        outputs=[("loan", "int"), ("deny", "int")],
        scenarios=[
            ("member_ok eq 0", "loan eq 0 && deny eq 2"),
            ("overdue gt 0", "loan eq 0 && deny eq 1"),
            ("copies le 0", "loan eq 0 && deny eq 1"),
            ("member_ok gt 0 && overdue eq 0 && copies gt 0", "loan eq 1 && deny eq 0"),
        ],
        source="liu2004soflbook",
        section="Library borrow process (SOFL book industrial teaching case)",
    ),
    _task(
        "PubIndPilot.LibraryReturn",
        "library_return",
        inputs=[("loan_active", "int"), ("days_late", "int")],
        outputs=[("closed", "int"), ("fine", "int")],
        scenarios=[
            ("loan_active eq 0", "closed eq 0 && fine eq 0"),
            ("days_late gt 0", "closed eq 1 && fine eq 1"),
            ("loan_active gt 0 && days_late eq 0", "closed eq 1 && fine eq 0"),
        ],
        source="liu2004soflbook",
        section="Library return with late fine priority",
    ),
    _task(
        "PubIndPilot.WaterTank",
        "water_tank_control",
        inputs=[("level", "int"), ("inflow", "int"), ("alarm", "int")],
        outputs=[("valve", "int"), ("pump", "int")],
        scenarios=[
            ("alarm gt 0", "valve eq 0 && pump eq 0"),
            ("level ge 9", "valve eq 0 && pump eq 0"),
            ("level le 2", "valve eq 1 && pump eq 1"),
            ("level gt 2 && level lt 9", "valve eq 1 && pump eq 0"),
        ],
        source="liu2004soflbook",
        section="Water-tank / process-control SOFL example (alarm preempts)",
    ),
    _task(
        "PubIndPilot.HotelCheckout",
        "hotel_checkout",
        inputs=[("occupied", "int"), ("paid", "int"), ("damage", "int")],
        outputs=[("release", "int"), ("bill", "int")],
        scenarios=[
            ("occupied eq 0", "release eq 0 && bill eq 0"),
            ("paid eq 0", "release eq 0 && bill eq 2"),
            ("damage gt 0", "release eq 0 && bill eq 1"),
            ("occupied gt 0 && paid gt 0 && damage eq 0", "release eq 1 && bill eq 0"),
        ],
        source="liu_sofl_hotel",
        section="Hotel checkout release under payment/damage guards",
    ),
    # --- IET fault-prevention / Agile-SOFL industrial modelling patterns ---
    _task(
        "PubIndPilot.AccessBadge",
        "access_badge",
        inputs=[("badge_ok", "int"), ("zone", "int"), ("time_ok", "int")],
        outputs=[("open", "int"), ("alarm", "int")],
        scenarios=[
            ("badge_ok eq 0", "open eq 0 && alarm eq 2"),
            ("time_ok eq 0", "open eq 0 && alarm eq 1"),
            ("zone ge 3 && badge_ok gt 0", "open eq 0 && alarm eq 1"),
            ("badge_ok gt 0 && time_ok gt 0 && zone lt 3", "open eq 1 && alarm eq 0"),
        ],
        source="li2023iet_faultprevention",
        section="Physical access control ordered guards (IET SOFL "
        "fault-prevention industrial modelling style)",
    ),
    _task(
        "PubIndPilot.MedDose",
        "med_dose_check",
        inputs=[("weight", "int"), ("dose", "int"), ("allergy", "int")],
        outputs=[("approve", "int"), ("flag", "int")],
        scenarios=[
            ("allergy gt 0", "approve eq 0 && flag eq 2"),
            ("dose le 0", "approve eq 0 && flag eq 1"),
            ("dose gt weight", "approve eq 0 && flag eq 1"),
            ("allergy eq 0 && dose gt 0 && dose le weight", "approve eq 1 && flag eq 0"),
        ],
        source="li2023iet_faultprevention",
        section="Medication dose safety checks (published SOFL healthcare "
        "modelling pattern; desensitized units)",
    ),
    _task(
        "PubIndPilot.PowerTrip",
        "power_trip_protect",
        inputs=[("current", "int"), ("temp", "int"), ("manual", "int")],
        outputs=[("trip", "int"), ("warn", "int")],
        scenarios=[
            ("manual gt 0", "trip eq 1 && warn eq 2"),
            ("current ge 9", "trip eq 1 && warn eq 2"),
            ("temp ge 8", "trip eq 1 && warn eq 1"),
            ("current lt 9 && temp lt 8", "trip eq 0 && warn eq 0"),
        ],
        source="li2023iet_faultprevention",
        section="Power protection trip priority (industrial control FSF)",
    ),
    _task(
        "PubIndPilot.TrafficPriority",
        "traffic_signal_priority",
        inputs=[("emergency", "int"), ("ped", "int"), ("phase", "int")],
        outputs=[("light", "int"), ("hold", "int")],
        scenarios=[
            ("emergency gt 0", "light eq 0 && hold eq 2"),
            ("ped gt 0 && phase eq 1", "light eq 1 && hold eq 1"),
            ("phase eq 2", "light eq 2 && hold eq 0"),
            ("phase eq 0", "light eq 0 && hold eq 0"),
        ],
        source="liu2004soflbook",
        section="Traffic signal priority with emergency preempt "
        "(SOFL-style ordered scenarios)",
    ),
    _task(
        "PubIndPilot.InsuranceClaim",
        "insurance_claim_triage",
        inputs=[("fraud_score", "int"), ("amount", "int"), ("docs_ok", "int")],
        outputs=[("pay", "int"), ("review", "int")],
        scenarios=[
            ("fraud_score ge 8", "pay eq 0 && review eq 2"),
            ("docs_ok eq 0", "pay eq 0 && review eq 1"),
            ("amount ge 9", "pay eq 0 && review eq 1"),
            ("fraud_score lt 8 && docs_ok gt 0 && amount lt 9", "pay eq 1 && review eq 0"),
        ],
        source="li2023iet_faultprevention",
        section="Insurance claim triage with fraud preempt (IET-style "
        "requirements fault-prevention modelling)",
    ),
    _task(
        "PubIndPilot.InventoryReorder",
        "inventory_reorder",
        inputs=[("stock", "int"), ("reorder_pt", "int"), ("on_order", "int")],
        outputs=[("order", "int"), ("qty", "int")],
        scenarios=[
            ("on_order gt 0", "order eq 0 && qty eq 0"),
            ("stock le reorder_pt", "order eq 1 && qty eq 2"),
            ("stock gt reorder_pt", "order eq 0 && qty eq 0"),
        ],
        source="liu2004soflbook",
        section="Inventory reorder decision (SOFL book / teaching industrial case)",
    ),
]


def load_published_industrial_pilot_tasks() -> list[dict[str, Any]]:
    """Return a copy of the published-industrial pilot task list."""
    import copy

    return copy.deepcopy(PUBLISHED_INDUSTRIAL_PILOT_TASKS)
