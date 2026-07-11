#!/usr/bin/env python3
"""Validate published-industrial pilot: Z3 witnesses + reference Conf=1."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.benchmarks.published_industrial_pilot import load_published_industrial_pilot_tasks
from src.benchmarks.reference_gen import validate_reference
from src.formal.fsf_eval import generate_concrete_cases


def main() -> int:
    tasks = load_published_industrial_pilot_tasks()
    rows = []
    fails = 0
    for t in tasks:
        scenarios = t.get("fsfScenarios", [])
        signature = t.get("signature", {})
        non_others = [s for s in scenarios if s.get("kind") != "others"]
        cases = generate_concrete_cases(
            scenarios, signature, max_cases=max(12, 3 * len(non_others))
        )
        covered = {c.scenario_index for c in cases if c.kind != "others"}
        missing = [s["index"] for s in non_others if s["index"] not in covered]
        ref_ok = False
        err = None
        try:
            ref_ok = validate_reference(t, t["referenceCode"])
        except Exception as exc:  # noqa: BLE001
            err = str(exc)
        ok = ref_ok and not missing and len(cases) >= 1
        if not ok:
            fails += 1
        rows.append(
            {
                "taskId": t["taskId"],
                "n_cases": len(cases),
                "missing_scenarios": missing,
                "ref_ok": ref_ok,
                "ok": ok,
                "error": err,
                "source": (t.get("externalProvenance") or {}).get("source"),
            }
        )
        print(
            f"{'OK' if ok else 'FAIL'} {t['taskId']}: "
            f"cases={len(cases)} missing={missing} ref_ok={ref_ok}"
        )

    out = ROOT / "benchmarks" / "published_industrial_pilot_validation.json"
    out.write_text(
        json.dumps({"n": len(rows), "fails": fails, "rows": rows}, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {out} fails={fails}/{len(rows)}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
