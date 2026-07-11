"""Real-world ordered-priority micro-benchmark (external validity).

Curates ~30 first-match FSF tasks from practitioner-style ACL / billing /
routing patterns, public GitHub ``.asfl`` harvest slices, HKCA09 SOFL
reconstructions, and a handful of new firewall / role-permission /
tax-bracket adaptations (the ``compute_tax`` running-example family).

Thresholds that need a wider SMT box declare ``smtDomain: {lo, hi}``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.benchmarks.industrial_sofl_corpus import _task
from src.benchmarks.reference_gen import generate_reference_code
from src.harvest.to_fsf import validate_task

ROOT = Path(__file__).resolve().parents[2]

# Prefer overlap-rich / priority-sensitive IDs from existing real corpora.
SELECT_INDUSTRIAL = [
    "IndustrialSOFL.LoanUnderwrite",
    "IndustrialSOFL.WireTransferGate",
    "IndustrialSOFL.CallRoute",
    "IndustrialSOFL.SmsThrottle",
    "IndustrialSOFL.BadgeAccess",
    "IndustrialSOFL.ApiAcl",
    "IndustrialSOFL.DoseAlert",
    "IndustrialSOFL.PickPriority",
    "IndustrialSOFL.FareRule",
    "IndustrialSOFL.ClaimTriage",
    "IndustrialSOFL.BoilerInterlock",
    "IndustrialSOFL.ApiRateLimit",
    "IndustrialSOFL.CardFraud",
    "IndustrialSOFL.OvertimePay",
]

SELECT_GITHUB = [
    "GitHubHarvest.ASFL_AddToCart",
    "GitHubHarvest.ASFL_Checkout",
    "GitHubHarvest.ASFL_Refund",
    "GitHubHarvest.ASFL_Authorize",
    "GitHubHarvest.ASFL_Capture",
    "GitHubHarvest.ASFL_CollectFee",
    "GitHubHarvest.ASFL_RefundFee",
    "GitHubHarvest.ASFL_AdmitUrgent",
    "GitHubHarvest.ManualSeed_TelecomSeverity",
]

SELECT_HKCA09 = [
    "HKCA09.Atm.Auth",
    "HKCA09.Atm.Withdraw",
    "HKCA09.Atm.Deposit",
    "HKCA09.Stock.PlaceOrder",
    "HKCA09.Stock.CheckRisk",
    "HKCA09.Transit.Purchase",
    "HKCA09.Transit.Validate",
]

SELECT_PUB = [
    "PubIndPilot.CrossingApproach",
    "PubIndPilot.RouteLock",
    "PubIndPilot.AtmAuth",
    "PubIndPilot.TransferGuard",
    "PubIndPilot.FraudHold",
    "PubIndPilot.AccessBadge",
    "PubIndPilot.TrafficPriority",
    "PubIndPilot.InsuranceClaim",
]


def _wide(task: dict[str, Any], lo: int = -100, hi: int = 100) -> dict[str, Any]:
    out = dict(task)
    out["smtDomain"] = {"lo": lo, "hi": hi}
    return out


def _new_priority_tasks() -> list[dict[str, Any]]:
    """Hand-adapted firewall / role / billing tasks with realistic scales."""
    tasks = [
        _task(
            "RealPriority.FirewallAcl",
            "firewall_acl",
            inputs=[("src_trust", "int"), ("dst_port", "int"), ("proto", "int")],
            outputs=[("action", "int"), ("log", "int")],
            scenarios=[
                ("src_trust lt 0", "action eq 0 && log eq 1"),
                ("src_trust eq 0 && dst_port eq 22", "action eq 0 && log eq 1"),
                ("src_trust ge 8 && dst_port eq 22", "action eq 1 && log eq 0"),
                ("src_trust ge 5 && dst_port le 1024", "action eq 1 && log eq 1"),
                ("src_trust ge 3 && dst_port gt 1024", "action eq 1 && log eq 0"),
            ],
            source="real_priority:firewall_acl",
            section="Firewall ACL first-match (deny/allow with port preemption)",
        ),
        _task(
            "RealPriority.SolidityRoleGate",
            "role_gated_transfer",
            inputs=[("role", "int"), ("amount", "int"), ("paused", "int")],
            outputs=[("ok", "int"), ("reason", "int")],
            scenarios=[
                ("paused eq 1", "ok eq 0 && reason eq 1"),
                ("role eq 0", "ok eq 0 && reason eq 2"),
                ("role ge 3 && amount ge 50", "ok eq 1 && reason eq 0"),
                ("role ge 2 && amount ge 20", "ok eq 1 && reason eq 0"),
                ("role ge 1 && amount le 10", "ok eq 1 && reason eq 0"),
            ],
            source="real_priority:solidity_role",
            section="Solidity-style Ownable/role transfer gate (ordered privileges)",
        ),
        _task(
            "RealPriority.ComputeTax",
            "compute_tax",
            inputs=[("income", "int"), ("is_foreign", "int")],
            outputs=[("bracket", "int")],
            scenarios=[
                ("income lt 0", "bracket eq 0"),
                ("income ge 80 && is_foreign eq 1", "bracket eq 3"),
                ("income ge 50", "bracket eq 2"),
                ("income ge 20", "bracket eq 1"),
            ],
            source="real_priority:compute_tax",
            section="Running-example tax brackets (foreign-high preempts mid)",
        ),
        _task(
            "RealPriority.BillingTier",
            "bill_subscription",
            inputs=[("usage", "int"), ("plan", "int"), ("overdue", "int")],
            outputs=[("charge", "int"), ("throttle", "int")],
            scenarios=[
                ("overdue eq 1", "charge eq 0 && throttle eq 1"),
                ("plan ge 3 && usage ge 80", "charge eq 15 && throttle eq 0"),
                ("plan ge 2 && usage ge 40", "charge eq 8 && throttle eq 0"),
                ("plan ge 1 && usage ge 10", "charge eq 3 && throttle eq 0"),
            ],
            source="real_priority:billing",
            section="SaaS billing tiers with overdue preemption (open-source billing pattern)",
        ),
        _task(
            "RealPriority.NftRoyalty",
            "split_royalty",
            inputs=[("price", "int"), ("creator_share", "int"), ("platform", "int")],
            outputs=[("creator_pay", "int"), ("plat_pay", "int")],
            scenarios=[
                ("price le 0", "creator_pay eq 0 && plat_pay eq 0"),
                ("platform eq 1 && creator_share ge 15", "creator_pay eq 15 && plat_pay eq 5"),
                ("creator_share ge 10", "creator_pay eq 10 && plat_pay eq 2"),
                ("creator_share ge 5", "creator_pay eq 5 && plat_pay eq 1"),
            ],
            source="real_priority:nft_royalty",
            section="NFT royalty split with platform surcharge preemption",
        ),
        _task(
            "RealPriority.RoutePriority",
            "route_packet",
            inputs=[("priority", "int"), ("congest", "int"), ("acl_deny", "int")],
            outputs=[("fwd", "int"), ("queue", "int")],
            scenarios=[
                ("acl_deny eq 1", "fwd eq 0 && queue eq 0"),
                ("priority ge 9 && congest ge 5", "fwd eq 1 && queue eq 0"),
                ("priority ge 5 && congest ge 7", "fwd eq 1 && queue eq 1"),
                ("priority ge 2", "fwd eq 1 && queue eq 2"),
            ],
            source="real_priority:network_qos",
            section="Packet routing QoS with ACL deny first",
        ),
    ]
    # Wider domain: thresholds up to 1024 need lo/hi beyond [-5,20].
    wide_ids = {
        "RealPriority.FirewallAcl": (-5, 2048),
        "RealPriority.SolidityRoleGate": (-100, 100),
        "RealPriority.ComputeTax": (-100, 100),
        "RealPriority.BillingTier": (-100, 100),
        "RealPriority.NftRoyalty": (-100, 100),
        "RealPriority.RoutePriority": (-100, 100),
    }
    out: list[dict[str, Any]] = []
    for t in tasks:
        lo, hi = wide_ids[t["taskId"]]
        t = _wide(t, lo, hi)
        t["referenceCode"] = generate_reference_code(t)
        out.append(t)
    return out


def _load_json(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    return list(data.get("tasks") or data.get("benchmark") or [])


def _index_by_id(tasks: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(t.get("taskId") or t.get("id")): t for t in tasks}


def build_real_priority_micro(*, target_n: int = 30) -> list[dict[str, Any]]:
    industrial = _index_by_id(_load_json(ROOT / "benchmarks" / "industrial_sofl.json"))
    github = _index_by_id(_load_json(ROOT / "benchmarks" / "github_harvest_v1.json"))
    hkca = _index_by_id(_load_json(ROOT / "benchmarks" / "hkca09_sofl_fsf.json"))
    pub = _index_by_id(_load_json(ROOT / "benchmarks" / "published_industrial_pilot.json"))

    selected: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(task: dict[str, Any] | None, *, widen: bool = False) -> None:
        if task is None:
            return
        tid = str(task.get("taskId"))
        if tid in seen:
            return
        if len(selected) >= target_n:
            return
        seen.add(tid)
        t = dict(task)
        if widen and "smtDomain" not in t:
            t = _wide(t, -100, 100)
        if "referenceCode" not in t:
            t["referenceCode"] = generate_reference_code(t)
        t.setdefault("externalProvenance", {})
        if isinstance(t["externalProvenance"], dict):
            t["externalProvenance"] = {
                **t["externalProvenance"],
                "micro_benchmark": "real_priority_micro_v1",
            }
        selected.append(t)

    # Reserve adapted real-world patterns first (firewall / role / tax / billing).
    for t in _new_priority_tasks():
        add(t)

    for tid in SELECT_INDUSTRIAL:
        add(industrial.get(tid), widen=True)
    for tid in SELECT_GITHUB:
        add(github.get(tid), widen=False)
    for tid in SELECT_HKCA09:
        add(hkca.get(tid), widen=True)
    for tid in SELECT_PUB:
        add(pub.get(tid), widen=True)

    # Fill remaining slots from leftover industrial / github with >=4 scenarios.
    if len(selected) < target_n:
        pool = list(industrial.values()) + list(github.values()) + list(hkca.values())
        pool.sort(
            key=lambda t: (
                -len(t.get("fsfScenarios") or []),
                str(t.get("taskId")),
            )
        )
        for t in pool:
            if len(selected) >= target_n:
                break
            n_scen = len(t.get("fsfScenarios") or [])
            if n_scen < 4:
                continue
            add(t, widen=True)

    return selected[:target_n]


def export_and_validate(
    out_path: Path | None = None,
    *,
    target_n: int = 30,
) -> dict[str, Any]:
    out_path = out_path or (ROOT / "benchmarks" / "real_priority_micro_v1.json")
    tasks = build_real_priority_micro(target_n=target_n)
    reports = []
    ok_tasks: list[dict[str, Any]] = []
    for t in tasks:
        rep = validate_task(t)
        reports.append({"taskId": t.get("taskId"), **rep})
        if rep.get("ok"):
            ok_tasks.append(t)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(ok_tasks, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    summary = {
        "path": str(out_path),
        "n_built": len(tasks),
        "n_ok": len(ok_tasks),
        "n_fail": len(tasks) - len(ok_tasks),
        "failures": [r for r in reports if not r.get("ok")],
        "task_ids": [t["taskId"] for t in ok_tasks],
        "domains": sorted(
            {
                (
                    (t.get("smtDomain") or {}).get("lo", -5),
                    (t.get("smtDomain") or {}).get("hi", 20),
                )
                for t in ok_tasks
            }
        ),
    }
    summary_path = out_path.with_name(out_path.stem + "_validation.json")
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    s = export_and_validate()
    print(json.dumps(s, indent=2))
