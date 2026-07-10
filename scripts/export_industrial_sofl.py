#!/usr/bin/env python3
"""Export industrial SOFL/FSF corpus to benchmarks/industrial_sofl.json.

Validates each task by:
  1. Z3 first-match witness generation per non-others scenario
  2. Formal checker against auto-generated referenceCode
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.benchmarks.complexity import annotate_tasks_complexity
from src.benchmarks.industrial_sofl_corpus import load_industrial_sofl_tasks
from src.benchmarks.reference_gen import validate_reference
from src.formal.fsf_eval import generate_concrete_cases


def _validate_task(task: dict) -> dict:
    scenarios = task.get("fsfScenarios", [])
    signature = task.get("signature", {})
    non_others = [s for s in scenarios if s.get("kind") != "others"]

    cases = generate_concrete_cases(scenarios, signature, max_cases=max(12, 3 * len(non_others)))
    covered = {c.scenario_index for c in cases if c.kind != "others"}
    missing = [s["index"] for s in non_others if s["index"] not in covered]

    ref_ok = False
    formal_error = None
    try:
        ref_ok = validate_reference(task, task["referenceCode"])
    except Exception as exc:  # noqa: BLE001
        formal_error = str(exc)

    return {
        "taskId": task["taskId"],
        "scenarios": len(non_others),
        "witness_cases": len(cases),
        "scenarios_with_witness": len(covered),
        "missing_witness_scenarios": missing,
        "formal_passed": bool(ref_ok),
        "formal_error": formal_error,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--out",
        type=Path,
        default=ROOT / "benchmarks" / "industrial_sofl.json",
    )
    p.add_argument("--annotate", action="store_true", default=True)
    p.add_argument("--no-annotate", action="store_false", dest="annotate")
    p.add_argument("--skip-validate", action="store_true")
    p.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Optional JSON validation report path",
    )
    args = p.parse_args()

    tasks = load_industrial_sofl_tasks()
    if args.annotate:
        tasks = annotate_tasks_complexity(tasks)

    report: list[dict] = []
    if not args.skip_validate:
        failures = 0
        for task in tasks:
            row = _validate_task(task)
            report.append(row)
            miss = row["missing_witness_scenarios"]
            ok = row["formal_passed"] and not miss
            status = "OK" if ok else "WARN" if row["formal_passed"] else "FAIL"
            if status != "OK":
                failures += 0 if status == "WARN" else 1
            print(
                f"[{status}] {row['taskId']}: "
                f"witnesses={row['witness_cases']} "
                f"covered={row['scenarios_with_witness']}/{row['scenarios']} "
                f"formal={row['formal_passed']}"
                + (f" missing={miss}" if miss else "")
                + (f" err={row['formal_error']}" if row["formal_error"] else "")
            )
        print(
            f"\nValidated {len(tasks)} tasks; "
            f"formal failures={sum(1 for r in report if not r['formal_passed'])}; "
            f"partial witness coverage={sum(1 for r in report if r['missing_witness_scenarios'])}"
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(tasks)} industrial tasks -> {args.out}")

    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote validation report -> {args.report}")


if __name__ == "__main__":
    main()
