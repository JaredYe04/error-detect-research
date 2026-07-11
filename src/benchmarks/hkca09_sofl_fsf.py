"""HKCA09 public SOFL → ordered-guard FSF reconstructions.

Source corpus (public GitHub, maintainability experiment materials)::

    HKCA09/SOFL-Maintainability-Experiment-Dataset
      Experiment II Materials/{ATM SYSTEM,COURSE_REGISTRATION,
        HOSPITAL_REGISTRATION,PUBLIC_TRANSPORT_TICKETING,
        STOCK_TRADING,VENDING_MACHINE}.txt

Honesty
-------
- Original modules use maps/sequences/strings; we **reconstruct** compact
  integer FSF processes that preserve the *decision precedence* (auth /
  capacity / balance / success) so the formal harness can run.
- Guards are intentionally **overlapping** (first-match order matters) to
  create repair headroom for E6 (typed IR vs unstructured test dumps).
- Not proprietary Casco/Mitsubishi dumps; not bit-identical to the SOFL
  postconditions (those are not SMT-encodable as-is).
"""

from __future__ import annotations

from typing import Any

from src.benchmarks.industrial_sofl_corpus import _task

_SRC = "hkca09/SOFL-Maintainability-Experiment-Dataset"


def _hk(
    task_id: str,
    name: str,
    *,
    inputs: list[tuple[str, str]],
    outputs: list[tuple[str, str]],
    scenarios: list[tuple[str, str]],
    module: str,
    section: str,
) -> dict[str, Any]:
    t = _task(
        task_id,
        name,
        inputs=inputs,
        outputs=outputs,
        scenarios=scenarios,
        source=_SRC,
        section=section,
    )
    t["module"] = f"HKCA09.{module}"
    t["sourceFile"] = f"github://{_SRC}/{module}"
    t["externalProvenance"] = {
        "source": _SRC,
        "module": module,
        "section": section,
        "generator": "hkca09_sofl_fsf_reconstruction",
        "corpus": "hkca09_github_sofl",
        "honesty": "desensitized_int_fsf_from_public_sofl_decision_logic",
    }
    return t


# ---------------------------------------------------------------------------
# Curated FSF tasks — overlapping guards, compact int domains
# ---------------------------------------------------------------------------

HKCA09_SOFL_FSF_TASKS: list[dict[str, Any]] = [
    # ===== ATM SYSTEM (Liu-style ATM teaching SOFL; HKCA09 materials) =====
    _hk(
        "HKCA09.Atm.Auth",
        "current_authorization",
        inputs=[("acct_ok", "int"), ("pin_ok", "int"), ("tries", "int"), ("locked", "int")],
        outputs=[("permit", "int"), ("msg", "int")],
        scenarios=[
            # locked / bad account preempts PIN checks
            ("locked gt 0", "permit eq 0 && msg eq 4"),
            ("acct_ok eq 0", "permit eq 0 && msg eq 3"),
            ("tries ge 3", "permit eq 0 && msg eq 4"),
            ("pin_ok eq 0", "permit eq 0 && msg eq 2"),
            ("acct_ok gt 0 && pin_ok gt 0 && tries lt 3 && locked eq 0", "permit eq 1 && msg eq 0"),
        ],
        module="ATM_SYSTEM",
        section="Current_Authorization: account/PIN/tries/lock precedence",
    ),
    _hk(
        "HKCA09.Atm.Deposit",
        "current_deposit",
        inputs=[("auth", "int"), ("amount", "int"), ("max_once", "int"), ("balance", "int")],
        outputs=[("ok", "int"), ("warn", "int")],
        scenarios=[
            ("auth eq 0", "ok eq 0 && warn eq 3"),
            ("amount le 0", "ok eq 0 && warn eq 1"),
            # over once-limit even when amount is positive (overlaps amount>0)
            ("amount gt max_once", "ok eq 0 && warn eq 2"),
            ("auth gt 0 && amount gt 0 && amount le max_once", "ok eq 1 && warn eq 0"),
        ],
        module="ATM_SYSTEM",
        section="Current_Deposit: auth + maximum_deposit_once gate",
    ),
    _hk(
        "HKCA09.Atm.Withdraw",
        "current_withdraw",
        inputs=[
            ("auth", "int"),
            ("amount", "int"),
            ("balance", "int"),
            ("max_once", "int"),
            ("day_remain", "int"),
        ],
        outputs=[("cash", "int"), ("warn", "int")],
        scenarios=[
            ("auth eq 0", "cash eq 0 && warn eq 4"),
            ("amount le 0", "cash eq 0 && warn eq 1"),
            # once-limit / day-remain / balance can all fail — order matters
            ("amount gt max_once", "cash eq 0 && warn eq 2"),
            ("amount gt balance", "cash eq 0 && warn eq 3"),
            ("amount gt day_remain", "cash eq 0 && warn eq 2"),
            (
                "auth gt 0 && amount gt 0 && amount le max_once && amount le balance "
                "&& amount le day_remain",
                "cash eq 1 && warn eq 0",
            ),
        ],
        module="ATM_SYSTEM",
        section="Current_Withdraw: once/day/balance ordered rejects",
    ),
    _hk(
        "HKCA09.Atm.Transfer",
        "manage_transfer",
        inputs=[
            ("auth", "int"),
            ("amount", "int"),
            ("src_bal", "int"),
            ("dst_ok", "int"),
            ("max_xfer", "int"),
        ],
        outputs=[("done", "int"), ("code", "int")],
        scenarios=[
            ("auth eq 0", "done eq 0 && code eq 4"),
            ("dst_ok eq 0", "done eq 0 && code eq 3"),
            ("amount le 0", "done eq 0 && code eq 1"),
            ("amount gt max_xfer", "done eq 0 && code eq 2"),
            ("amount gt src_bal", "done eq 0 && code eq 3"),
            (
                "auth gt 0 && dst_ok gt 0 && amount gt 0 && amount le max_xfer && amount le src_bal",
                "done eq 1 && code eq 0",
            ),
        ],
        module="ATM_SYSTEM",
        section="Manage_Transfer: dest/limit/balance precedence",
    ),
    _hk(
        "HKCA09.Atm.ChangePass",
        "change_password",
        inputs=[("auth", "int"), ("old_ok", "int"), ("new_len", "int"), ("same", "int")],
        outputs=[("changed", "int"), ("err", "int")],
        scenarios=[
            ("auth eq 0", "changed eq 0 && err eq 4"),
            ("old_ok eq 0", "changed eq 0 && err eq 2"),
            ("new_len lt 4", "changed eq 0 && err eq 1"),
            ("same gt 0", "changed eq 0 && err eq 1"),
            ("auth gt 0 && old_ok gt 0 && new_len ge 4 && same eq 0", "changed eq 1 && err eq 0"),
        ],
        module="ATM_SYSTEM",
        section="Change_Password: auth/old/new-policy ordered checks",
    ),
    _hk(
        "HKCA09.Atm.SelectService",
        "select_services",
        inputs=[("deposit", "int"), ("withdraw", "int"), ("balance", "int"), ("print", "int")],
        outputs=[("sel", "int"), ("ok", "int")],
        scenarios=[
            # mutually exclusive ports in SOFL; encode priority order
            ("deposit gt 0", "sel eq 1 && ok eq 1"),
            ("withdraw gt 0", "sel eq 2 && ok eq 1"),
            ("balance gt 0", "sel eq 3 && ok eq 1"),
            ("print gt 0", "sel eq 4 && ok eq 1"),
        ],
        module="ATM_SYSTEM",
        section="Select_Services: bound-port priority encoding",
    ),
    # ===== COURSE_REGISTRATION =====
    _hk(
        "HKCA09.Course.Register",
        "register_course",
        inputs=[
            ("catalog_ok", "int"),
            ("enrolled", "int"),
            ("already", "int"),
            ("credits", "int"),
            ("max_lim", "int"),
        ],
        outputs=[("success", "int"), ("msg", "int")],
        scenarios=[
            ("catalog_ok eq 0", "success eq 0 && msg eq 3"),
            ("already gt 0", "success eq 0 && msg eq 2"),
            # limit exceeded (overlaps enrolled near max)
            ("enrolled ge max_lim", "success eq 0 && msg eq 1"),
            ("credits le 0", "success eq 0 && msg eq 3"),
            (
                "catalog_ok gt 0 && already eq 0 && enrolled lt max_lim && credits gt 0",
                "success eq 1 && msg eq 0",
            ),
        ],
        module="COURSE_REGISTRATION",
        section="Register_Course: catalog/already/max_course_limit",
    ),
    _hk(
        "HKCA09.Course.Drop",
        "drop_course",
        inputs=[("enrolled", "int"), ("in_list", "int"), ("min_lim", "int")],
        outputs=[("success", "int"), ("msg", "int")],
        scenarios=[
            ("in_list eq 0", "success eq 0 && msg eq 2"),
            # dropping would violate min load
            ("enrolled le min_lim", "success eq 0 && msg eq 1"),
            ("in_list gt 0 && enrolled gt min_lim", "success eq 1 && msg eq 0"),
        ],
        module="COURSE_REGISTRATION",
        section="Drop_Course: membership + min_course_limit",
    ),
    _hk(
        "HKCA09.Course.AddNotify",
        "add_notification",
        inputs=[("student_ok", "int"), ("msg_len", "int"), ("quota", "int")],
        outputs=[("ok", "int"), ("code", "int")],
        scenarios=[
            ("student_ok eq 0", "ok eq 0 && code eq 2"),
            ("msg_len le 0", "ok eq 0 && code eq 1"),
            ("quota le 0", "ok eq 0 && code eq 1"),
            ("student_ok gt 0 && msg_len gt 0 && quota gt 0", "ok eq 1 && code eq 0"),
        ],
        module="COURSE_REGISTRATION",
        section="Add_Notification: student/message/quota gates",
    ),
    _hk(
        "HKCA09.Course.ViewNotify",
        "view_notifications",
        inputs=[("student_ok", "int"), ("n_msg", "int")],
        outputs=[("shown", "int"), ("empty", "int")],
        scenarios=[
            ("student_ok eq 0", "shown eq 0 && empty eq 1"),
            ("n_msg eq 0", "shown eq 0 && empty eq 1"),
            ("student_ok gt 0 && n_msg gt 0", "shown eq 1 && empty eq 0"),
        ],
        module="COURSE_REGISTRATION",
        section="View_Notifications: empty vs present",
    ),
    # ===== HOSPITAL_REGISTRATION =====
    _hk(
        "HKCA09.Hosp.RegisterPatient",
        "register_patient",
        inputs=[("exists", "int"), ("info_ok", "int")],
        outputs=[("pid_new", "int"), ("conf", "int")],
        scenarios=[
            ("info_ok eq 0", "pid_new eq 0 && conf eq 0"),
            ("exists gt 0", "pid_new eq 0 && conf eq 1"),
            ("exists eq 0 && info_ok gt 0", "pid_new eq 1 && conf eq 2"),
        ],
        module="HOSPITAL_REGISTRATION",
        section="Register_Patient: duplicate vs new",
    ),
    _hk(
        "HKCA09.Hosp.UpdateSchedule",
        "update_schedule",
        inputs=[("doc_known", "int"), ("slots", "int"), ("conflict", "int")],
        outputs=[("success", "int"), ("msg", "int")],
        scenarios=[
            ("slots le 0", "success eq 0 && msg eq 1"),
            ("conflict gt 0", "success eq 0 && msg eq 2"),
            ("doc_known eq 0 && slots gt 0 && conflict eq 0", "success eq 1 && msg eq 0"),
            ("doc_known gt 0 && slots gt 0 && conflict eq 0", "success eq 1 && msg eq 3"),
        ],
        module="HOSPITAL_REGISTRATION",
        section="Update_Schedule: new doctor vs merge; conflict preempts",
    ),
    _hk(
        "HKCA09.Hosp.PerformReg",
        "perform_registration",
        inputs=[
            ("patient_ok", "int"),
            ("doctor_ok", "int"),
            ("slot_free", "int"),
            ("doc_load", "int"),
            ("max_load", "int"),
        ],
        outputs=[("reg_ok", "int"), ("code", "int")],
        scenarios=[
            ("patient_ok eq 0", "reg_ok eq 0 && code eq 4"),
            ("doctor_ok eq 0", "reg_ok eq 0 && code eq 3"),
            ("slot_free eq 0", "reg_ok eq 0 && code eq 2"),
            # max_patients_per_doctor = 30 → compact scale
            ("doc_load ge max_load", "reg_ok eq 0 && code eq 1"),
            (
                "patient_ok gt 0 && doctor_ok gt 0 && slot_free gt 0 && doc_load lt max_load",
                "reg_ok eq 1 && code eq 0",
            ),
        ],
        module="HOSPITAL_REGISTRATION",
        section="Perform_Registration: patient/doctor/slot/load order",
    ),
    _hk(
        "HKCA09.Hosp.ManageQueue",
        "manage_queue",
        inputs=[("dept_ok", "int"), ("q_len", "int"), ("max_q", "int"), ("prio", "int")],
        outputs=[("enqueued", "int"), ("status", "int")],
        scenarios=[
            ("dept_ok eq 0", "enqueued eq 0 && status eq 3"),
            ("q_len ge max_q", "enqueued eq 0 && status eq 2"),
            ("prio gt 0 && dept_ok gt 0 && q_len lt max_q", "enqueued eq 1 && status eq 1"),
            ("dept_ok gt 0 && q_len lt max_q", "enqueued eq 1 && status eq 0"),
        ],
        module="HOSPITAL_REGISTRATION",
        section="Manage_Queue: capacity + priority enqueue",
    ),
    _hk(
        "HKCA09.Hosp.Stats",
        "generate_statistics",
        inputs=[("n_reg", "int"), ("n_dept", "int")],
        outputs=[("ready", "int"), ("flag", "int")],
        scenarios=[
            ("n_reg le 0", "ready eq 0 && flag eq 1"),
            ("n_dept le 0", "ready eq 0 && flag eq 1"),
            ("n_reg gt 0 && n_dept gt 0", "ready eq 1 && flag eq 0"),
        ],
        module="HOSPITAL_REGISTRATION",
        section="Generate_Statistics: empty-data guard",
    ),
    # ===== VENDING_MACHINE =====
    _hk(
        "HKCA09.Vend.AddItem",
        "add_item",
        inputs=[("qty", "int"), ("price", "int"), ("max_price", "int"), ("cap", "int")],
        outputs=[("ok", "int"), ("code", "int")],
        scenarios=[
            ("qty le 0", "ok eq 0 && code eq 1"),
            ("price gt max_price", "ok eq 0 && code eq 2"),
            ("qty gt cap", "ok eq 0 && code eq 2"),
            ("qty gt 0 && price le max_price && qty le cap", "ok eq 1 && code eq 0"),
        ],
        module="VENDING_MACHINE",
        section="Add_Item: qty/price/capacity preconditions",
    ),
    _hk(
        "HKCA09.Vend.Restock",
        "restock_item",
        inputs=[("found", "int"), ("qty", "int"), ("room", "int")],
        outputs=[("ok", "int"), ("code", "int")],
        scenarios=[
            ("found eq 0", "ok eq 0 && code eq 3"),
            ("qty le 0", "ok eq 0 && code eq 1"),
            ("qty gt room", "ok eq 0 && code eq 2"),
            ("found gt 0 && qty gt 0 && qty le room", "ok eq 1 && code eq 0"),
        ],
        module="VENDING_MACHINE",
        section="Restock_Item: exists + remaining capacity",
    ),
    _hk(
        "HKCA09.Vend.SelectItem",
        "select_item",
        inputs=[
            ("found", "int"),
            ("qty", "int"),
            ("stock", "int"),
            ("cost", "int"),
            ("balance", "int"),
        ],
        outputs=[("vend", "int"), ("code", "int")],
        scenarios=[
            ("found eq 0", "vend eq 0 && code eq 4"),
            ("qty le 0", "vend eq 0 && code eq 1"),
            # stock and balance can both fail — order matters for IR
            ("qty gt stock", "vend eq 0 && code eq 2"),
            ("cost gt balance", "vend eq 0 && code eq 3"),
            (
                "found gt 0 && qty gt 0 && qty le stock && cost le balance",
                "vend eq 1 && code eq 0",
            ),
        ],
        module="VENDING_MACHINE",
        section="Select_Item: stock vs balance ordered rejects",
    ),
    _hk(
        "HKCA09.Vend.InsertMoney",
        "insert_money",
        inputs=[("amount", "int"), ("room", "int")],
        outputs=[("ok", "int"), ("code", "int")],
        scenarios=[
            ("amount le 0", "ok eq 0 && code eq 1"),
            ("amount gt room", "ok eq 0 && code eq 2"),
            ("amount gt 0 && amount le room", "ok eq 1 && code eq 0"),
        ],
        module="VENDING_MACHINE",
        section="Insert_Money: positive amount + balance room",
    ),
    _hk(
        "HKCA09.Vend.CheckBalance",
        "check_balance",
        inputs=[("balance", "int"), ("warn_thr", "int")],
        outputs=[("warn", "int"), ("ok", "int")],
        scenarios=[
            ("balance lt warn_thr", "warn eq 1 && ok eq 0"),
            ("balance ge warn_thr", "warn eq 0 && ok eq 1"),
        ],
        module="VENDING_MACHINE",
        section="Check_Balance: min_balance_warning threshold",
    ),
    _hk(
        "HKCA09.Vend.CheckInv",
        "check_inventory_status",
        inputs=[("min_stock", "int"), ("n_empty", "int")],
        outputs=[("healthy", "int"), ("alert", "int")],
        scenarios=[
            ("n_empty gt 0", "healthy eq 0 && alert eq 2"),
            ("min_stock le 0", "healthy eq 0 && alert eq 1"),
            ("n_empty eq 0 && min_stock gt 0", "healthy eq 1 && alert eq 0"),
        ],
        module="VENDING_MACHINE",
        section="Check_Inventory_Status: empty-item alert",
    ),
    # ===== STOCK_TRADING =====
    _hk(
        "HKCA09.Stock.PlaceOrder",
        "place_order",
        inputs=[
            ("user_ok", "int"),
            ("side", "int"),
            ("qty", "int"),
            ("cost", "int"),
            ("balance", "int"),
            ("holding", "int"),
        ],
        outputs=[("accepted", "int"), ("code", "int")],
        scenarios=[
            ("user_ok eq 0", "accepted eq 0 && code eq 4"),
            ("qty le 0", "accepted eq 0 && code eq 1"),
            ("cost le 0", "accepted eq 0 && code eq 1"),
            # buy: insufficient funds (side>0); sell: insufficient holding (side=0)
            ("side gt 0 && cost gt balance", "accepted eq 0 && code eq 2"),
            ("side eq 0 && qty gt holding", "accepted eq 0 && code eq 3"),
            ("side gt 0 && cost le balance", "accepted eq 1 && code eq 0"),
            ("side eq 0 && qty le holding", "accepted eq 1 && code eq 0"),
        ],
        module="STOCK_TRADING",
        section="Place_Order: buy/sell fund-holding checks",
    ),
    _hk(
        "HKCA09.Stock.CheckRisk",
        "check_account_risk",
        inputs=[("balance", "int"), ("n_hold", "int"), ("conc", "int")],
        outputs=[("alert", "int"), ("level", "int")],
        scenarios=[
            # Overdrawn preempts; then holdings size; then concentration
            ("balance lt 0", "alert eq 1 && level eq 3"),
            ("n_hold gt 10", "alert eq 1 && level eq 2"),
            ("conc gt 7", "alert eq 1 && level eq 1"),
            ("balance ge 0 && n_hold le 10 && conc le 7", "alert eq 0 && level eq 0"),
        ],
        module="STOCK_TRADING",
        section="Check_Account_Risk: overdrawn / holdings / concentration",
    ),
    _hk(
        "HKCA09.Stock.Settle",
        "settle_order",
        inputs=[
            ("valid", "int"),
            ("side", "int"),
            ("qty", "int"),
            ("cost", "int"),
            ("buyer_bal", "int"),
            ("seller_hold", "int"),
        ],
        outputs=[("settled", "int"), ("code", "int")],
        scenarios=[
            ("valid eq 0", "settled eq 0 && code eq 3"),
            ("side gt 0 && cost gt buyer_bal", "settled eq 0 && code eq 2"),
            ("side eq 0 && qty gt seller_hold", "settled eq 0 && code eq 1"),
            ("valid gt 0 && side gt 0 && cost le buyer_bal", "settled eq 1 && code eq 0"),
            ("valid gt 0 && side eq 0 && qty le seller_hold", "settled eq 1 && code eq 0"),
        ],
        module="STOCK_TRADING",
        section="Settle_Order: buyer/seller solvency",
    ),
    _hk(
        "HKCA09.Stock.CancelOrder",
        "cancel_order",
        inputs=[("found", "int"), ("owner", "int"), ("filled", "int")],
        outputs=[("cancelled", "int"), ("code", "int")],
        scenarios=[
            ("found eq 0", "cancelled eq 0 && code eq 3"),
            ("owner eq 0", "cancelled eq 0 && code eq 2"),
            ("filled gt 0", "cancelled eq 0 && code eq 1"),
            ("found gt 0 && owner gt 0 && filled eq 0", "cancelled eq 1 && code eq 0"),
        ],
        module="STOCK_TRADING",
        section="Cancel_Order: found/owner/filled gates",
    ),
    # ===== PUBLIC_TRANSPORT_TICKETING =====
    _hk(
        "HKCA09.Transit.Purchase",
        "purchase_ticket",
        inputs=[
            ("user_ok", "int"),
            ("route_ok", "int"),
            ("balance", "int"),
            ("fare", "int"),
            ("remain", "int"),
            ("min_bal", "int"),
        ],
        outputs=[("ticket", "int"), ("msg", "int")],
        scenarios=[
            ("user_ok eq 0", "ticket eq 0 && msg eq 4"),
            ("route_ok eq 0", "ticket eq 0 && msg eq 3"),
            ("fare le 0", "ticket eq 0 && msg eq 1"),
            ("balance lt fare", "ticket eq 0 && msg eq 2"),
            # post-purchase remain must keep min_balance (overlap with afford)
            ("remain lt min_bal", "ticket eq 0 && msg eq 2"),
            (
                "user_ok gt 0 && route_ok gt 0 && fare gt 0 && balance ge fare "
                "&& remain ge min_bal",
                "ticket eq 1 && msg eq 0",
            ),
        ],
        module="PUBLIC_TRANSPORT_TICKETING",
        section="Purchase_Ticket: user/route/fare/min_balance",
    ),
    _hk(
        "HKCA09.Transit.UpdateBalance",
        "update_balance",
        inputs=[("user_ok", "int"), ("amount", "int")],
        outputs=[("status", "int"), ("msg", "int")],
        scenarios=[
            ("user_ok eq 0", "status eq 0 && msg eq 2"),
            ("amount eq 0", "status eq 0 && msg eq 1"),
            ("user_ok gt 0 && amount ne 0", "status eq 1 && msg eq 0"),
        ],
        module="PUBLIC_TRANSPORT_TICKETING",
        section="Update_Balance: user found + nonzero delta",
    ),
    _hk(
        "HKCA09.Transit.Validate",
        "validate_ticket",
        inputs=[("found", "int"), ("valid", "int"), ("expired", "int")],
        outputs=[("ok", "int"), ("msg", "int")],
        scenarios=[
            ("found eq 0", "ok eq 0 && msg eq 3"),
            ("expired gt 0", "ok eq 0 && msg eq 2"),
            ("valid eq 0", "ok eq 0 && msg eq 1"),
            ("found gt 0 && valid gt 0 && expired eq 0", "ok eq 1 && msg eq 0"),
        ],
        module="PUBLIC_TRANSPORT_TICKETING",
        section="Validate_Ticket: found/valid/expired order",
    ),
    _hk(
        "HKCA09.Transit.MakePayment",
        "make_payment",
        inputs=[("user_ok", "int"), ("amount", "int"), ("balance", "int"), ("method", "int")],
        outputs=[("paid", "int"), ("code", "int")],
        scenarios=[
            ("user_ok eq 0", "paid eq 0 && code eq 4"),
            ("method le 0", "paid eq 0 && code eq 1"),
            ("amount le 0", "paid eq 0 && code eq 1"),
            ("amount gt balance", "paid eq 0 && code eq 2"),
            (
                "user_ok gt 0 && method gt 0 && amount gt 0 && amount le balance",
                "paid eq 1 && code eq 0",
            ),
        ],
        module="PUBLIC_TRANSPORT_TICKETING",
        section="Make_Payment: method + solvency",
    ),
    _hk(
        "HKCA09.Transit.UpdateRoute",
        "update_route",
        inputs=[("exists", "int"), ("n_stations", "int"), ("dist", "int")],
        outputs=[("status", "int"), ("msg", "int")],
        scenarios=[
            ("n_stations lt 2", "status eq 0 && msg eq 1"),
            ("dist le 0", "status eq 0 && msg eq 1"),
            ("exists gt 0", "status eq 0 && msg eq 2"),
            ("exists eq 0 && n_stations ge 2 && dist gt 0", "status eq 1 && msg eq 0"),
        ],
        module="PUBLIC_TRANSPORT_TICKETING",
        section="Update_Route: add-only; reject duplicates",
    ),
    # ===== Extra ATM / cross-cutting headroom tasks =====
    _hk(
        "HKCA09.Atm.WithdrawStrict",
        "current_withdraw_strict",
        inputs=[
            ("auth", "int"),
            ("amount", "int"),
            ("balance", "int"),
            ("max_once", "int"),
            ("app_lim", "int"),
        ],
        outputs=[("cash", "int"), ("warn", "int")],
        scenarios=[
            ("auth eq 0", "cash eq 0 && warn eq 5"),
            ("amount le 0", "cash eq 0 && warn eq 1"),
            ("amount gt max_once", "cash eq 0 && warn eq 2"),
            ("amount gt app_lim", "cash eq 0 && warn eq 2"),
            ("amount gt balance", "cash eq 0 && warn eq 3"),
            # residual: amount equals balance is OK; amount==max_once OK
            (
                "auth gt 0 && amount gt 0 && amount le max_once && amount le app_lim "
                "&& amount le balance",
                "cash eq 1 && warn eq 0",
            ),
        ],
        module="ATM_SYSTEM",
        section="Current_Withdraw strict: once + application + balance overlaps",
    ),
    _hk(
        "HKCA09.Vend.SelectItemStrict",
        "select_item_strict",
        inputs=[
            ("found", "int"),
            ("qty", "int"),
            ("stock", "int"),
            ("cost", "int"),
            ("balance", "int"),
            ("remain", "int"),
            ("warn_thr", "int"),
        ],
        outputs=[("vend", "int"), ("code", "int")],
        scenarios=[
            ("found eq 0", "vend eq 0 && code eq 5"),
            ("qty le 0", "vend eq 0 && code eq 1"),
            ("qty gt stock", "vend eq 0 && code eq 2"),
            ("cost gt balance", "vend eq 0 && code eq 3"),
            # leave machine below warning threshold after vend
            ("remain lt warn_thr", "vend eq 0 && code eq 4"),
            (
                "found gt 0 && qty gt 0 && qty le stock && cost le balance "
                "&& remain ge warn_thr",
                "vend eq 1 && code eq 0",
            ),
        ],
        module="VENDING_MACHINE",
        section="Select_Item + post-vend min_balance_warning",
    ),
    _hk(
        "HKCA09.Hosp.PerformRegStrict",
        "perform_registration_strict",
        inputs=[
            ("patient_ok", "int"),
            ("doctor_ok", "int"),
            ("slot_free", "int"),
            ("doc_load", "int"),
            ("max_load", "int"),
            ("dept_ok", "int"),
        ],
        outputs=[("reg_ok", "int"), ("code", "int")],
        scenarios=[
            ("patient_ok eq 0", "reg_ok eq 0 && code eq 5"),
            ("dept_ok eq 0", "reg_ok eq 0 && code eq 4"),
            ("doctor_ok eq 0", "reg_ok eq 0 && code eq 3"),
            ("slot_free eq 0", "reg_ok eq 0 && code eq 2"),
            ("doc_load ge max_load", "reg_ok eq 0 && code eq 1"),
            (
                "patient_ok gt 0 && dept_ok gt 0 && doctor_ok gt 0 && slot_free gt 0 "
                "&& doc_load lt max_load",
                "reg_ok eq 1 && code eq 0",
            ),
        ],
        module="HOSPITAL_REGISTRATION",
        section="Perform_Registration + department validity",
    ),
    _hk(
        "HKCA09.Course.RegisterStrict",
        "register_course_strict",
        inputs=[
            ("catalog_ok", "int"),
            ("enrolled", "int"),
            ("already", "int"),
            ("credits", "int"),
            ("max_lim", "int"),
            ("prereq", "int"),
        ],
        outputs=[("success", "int"), ("msg", "int")],
        scenarios=[
            ("catalog_ok eq 0", "success eq 0 && msg eq 4"),
            ("prereq eq 0", "success eq 0 && msg eq 3"),
            ("already gt 0", "success eq 0 && msg eq 2"),
            ("enrolled ge max_lim", "success eq 0 && msg eq 1"),
            ("credits le 0", "success eq 0 && msg eq 4"),
            (
                "catalog_ok gt 0 && prereq gt 0 && already eq 0 && enrolled lt max_lim "
                "&& credits gt 0",
                "success eq 1 && msg eq 0",
            ),
        ],
        module="COURSE_REGISTRATION",
        section="Register_Course + prerequisite gate",
    ),
    _hk(
        "HKCA09.Stock.PlaceOrderStrict",
        "place_order_strict",
        inputs=[
            ("user_ok", "int"),
            ("side", "int"),
            ("qty", "int"),
            ("cost", "int"),
            ("balance", "int"),
            ("holding", "int"),
            ("n_hold", "int"),
            ("max_hold", "int"),
        ],
        outputs=[("accepted", "int"), ("code", "int")],
        scenarios=[
            ("user_ok eq 0", "accepted eq 0 && code eq 5"),
            ("qty le 0", "accepted eq 0 && code eq 1"),
            ("cost le 0", "accepted eq 0 && code eq 1"),
            ("side gt 0 && n_hold ge max_hold", "accepted eq 0 && code eq 4"),
            ("side gt 0 && cost gt balance", "accepted eq 0 && code eq 2"),
            ("side eq 0 && qty gt holding", "accepted eq 0 && code eq 3"),
            ("side gt 0 && n_hold lt max_hold && cost le balance", "accepted eq 1 && code eq 0"),
            ("side eq 0 && qty le holding", "accepted eq 1 && code eq 0"),
        ],
        module="STOCK_TRADING",
        section="Place_Order + max holdings risk gate",
    ),
]


def load_hkca09_sofl_fsf_tasks() -> list[dict[str, Any]]:
    import copy

    return copy.deepcopy(HKCA09_SOFL_FSF_TASKS)
