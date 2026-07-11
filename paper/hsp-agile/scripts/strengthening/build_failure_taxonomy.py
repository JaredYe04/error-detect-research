#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build Failure Taxonomy from E6 / equal-K attempt histories (Agent E)."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = (
    ROOT
    / "paper"
    / "hsp-agile"
    / "artifacts"
    / "strengthening_sprint"
    / "agent_e_failure"
)

CATEGORIES = [
    "Ordering",
    "Boundary",
    "MissingGuard",
    "WrongThreshold",
    "Arithmetic",
    "Hallucination",
    "RepairRegression",
    "OverRepair",
    "StateLongRange",
    "Other",
]


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _conf(row: dict) -> float:
    for k in ("formal_conformance", "strict_formal_conformance"):
        if row.get(k) is not None:
            return float(row[k])
    return 0.0


def classify_violation(vtype: str, reason: str, constraint: str) -> str:
    text = f"{vtype} {reason} {constraint}".lower()
    if "order" in text or vtype == "ordering":
        return "Ordering"
    if "bound" in text or "off-by" in text or vtype == "boundary":
        return "Boundary"
    if "missing" in text and "guard" in text:
        return "MissingGuard"
    if "threshold" in text or re.search(r"\b(le|ge|lt|gt)\b", text):
        if "wrong" in text or "swap" in text or "invert" in text:
            return "WrongThreshold"
    if "arith" in text or vtype == "arithmetic":
        return "Arithmetic"
    if "hallucin" in text or "rf07" in text or "api" in text:
        return "Hallucination"
    if "state" in text or "accumul" in text or "long-range" in text:
        return "StateLongRange"
    if vtype in {"output", "unknown", ""}:
        return "Other"
    return {
        "ordering": "Ordering",
        "boundary": "Boundary",
        "arithmetic": "Arithmetic",
        "output": "Other",
    }.get(vtype, "Other")


def analyze_row(row: dict) -> dict:
    hist = row.get("attempt_history") or []
    confs = [float(h.get("formal_conformance") or 0.0) for h in hist]
    regression = any(confs[i] + 1e-12 < confs[i - 1] for i in range(1, len(confs)))

    types_per_attempt: list[set[str]] = []
    all_cats: list[str] = []
    for h in hist:
        cats = set()
        for sf in h.get("semantic_feedback") or []:
            cat = classify_violation(
                str(sf.get("violation_type") or ""),
                str(sf.get("reason") or ""),
                str(sf.get("constraint_text") or ""),
            )
            cats.add(cat)
            all_cats.append(cat)
        types_per_attempt.append(cats)

    over_repair = False
    for i in range(1, len(types_per_attempt)):
        if types_per_attempt[i] - types_per_attempt[i - 1]:
            # new category appeared after a prior attempt
            if confs and i < len(confs):
                over_repair = True
                break

    primary = Counter(all_cats).most_common(1)[0][0] if all_cats else "Other"
    if regression:
        primary = "RepairRegression"
    elif over_repair and primary == "Other":
        primary = "OverRepair"

    return {
        "task_id": row.get("task_id"),
        "feedback_variant": row.get("feedback_variant"),
        "final_conf": _conf(row),
        "success": bool(row.get("success") or row.get("formal_passed")),
        "primary_category": primary,
        "secondary_tags": sorted(set(all_cats)),
        "repair_regression": regression,
        "over_repair": over_repair,
        "n_attempts": len(hist),
        "violation_types_raw": sorted({str(sf.get("violation_type")) for h in hist for sf in (h.get("semantic_feedback") or [])}),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--e6",
        type=Path,
        default=ROOT / "artifacts" / "run_feedback_v2" / "feedback_variants" / "results.jsonl",
    )
    ap.add_argument("--out-dir", type=Path, default=OUT)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    rows = _load_jsonl(args.e6)
    # Focus: semantic_ir rows that did not fully pass, plus mechanism contrast set
    analyses = []
    by_task: dict[str, dict[str, dict]] = defaultdict(dict)
    for r in rows:
        tid = r.get("task_id")
        var = r.get("feedback_variant")
        if tid and var:
            by_task[str(tid)][str(var)] = r

    for tid, variants in by_task.items():
        ir = variants.get("semantic_ir")
        to = variants.get("test_only")
        if ir is None:
            continue
        a = analyze_row(ir)
        a["corpus"] = "run_feedback_v2/E6"
        a["delta_vs_test_only"] = None
        if to is not None:
            a["delta_vs_test_only"] = round(_conf(ir) - _conf(to), 6)
            a["mechanism_role"] = (
                "ir_rescues"
                if _conf(ir) > _conf(to) + 1e-12
                else ("test_only_better" if _conf(to) > _conf(ir) + 1e-12 else "tie")
            )
        else:
            a["mechanism_role"] = "unknown"
        a["ir_failed"] = _conf(ir) < 1.0 - 1e-12
        analyses.append(a)

    (args.out_dir / "failure_taxonomy.json").write_text(json.dumps(analyses, indent=2), encoding="utf-8")

    import csv

    keys = list(analyses[0].keys()) if analyses else []
    with (args.out_dir / "failure_taxonomy.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(analyses)

    failed = [a for a in analyses if a["ir_failed"]]
    rescued = [a for a in analyses if a.get("mechanism_role") == "ir_rescues"]
    still = Counter(a["primary_category"] for a in failed)
    rescue_cats = Counter()
    for a in rescued:
        # category of residual feedback on test_only side if available ???use IR hist primary before success
        rescue_cats[a["primary_category"]] += 1

    md = f"""# Failure Taxonomy (Agent E)

**Corpus:** E6 `run_feedback_v2` (semantic_ir under mode M).  
**Not** the historical pre-fix E9 pie (Strict???%).

## Counts

| Slice | n |
|-------|--:|
| Tasks with semantic_ir row | {len(analyses)} |
| IR not at Conf=1.0 | {len(failed)} |
| IR rescues vs test_only | {len(rescued)} |

## Primary category among IR residuals (Conf < 1)

| Category | n |
|----------|--:|
{chr(10).join(f'| {k} | {v} |' for k, v in still.most_common())}

## Categories on IR-rescue tasks (where typed IR beat test_only)

These are the failure modes typed IR most often *fixes* (primary label from IR attempt history ???often the residual type mid-repair):

| Category | n |
|----------|--:|
{chr(10).join(f'| {k} | {v} |' for k, v in rescue_cats.most_common())}

## Definitions

- **Ordering:** first-match / scenario precedence violations
- **Boundary:** off-by-one / relational edge errors
- **Arithmetic:** wrong output expression under correct branch
- **RepairRegression:** Conf decreases across attempts
- **OverRepair:** new violation categories appear after a repair step
- **Hallucination / MissingGuard / WrongThreshold / StateLongRange:** as named

## Implications for IR design

- If Ordering/Boundary dominate residuals ???strengthen scenario_id + constraint_text fields (Agent B).
- If RepairRegression is common ???early-stopping / argmax Conf selection matters.
- If Arithmetic dominates ???witnesses-on-guards alone are insufficient (known limitation).

## Files

- `failure_taxonomy.json` / `.csv`
"""
    (args.out_dir / "FAILURE_TAXONOMY.md").write_text(md, encoding="utf-8")
    (args.out_dir / "STATUS.md").write_text("# Agent E STATUS\n\nDONE: E6-based failure taxonomy.\n", encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
