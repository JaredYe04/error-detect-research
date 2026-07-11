#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Seeded others-bug IR field ablation (causal, fixed-oracle safe).

Motivation
----------
Original E6 win codes mostly *pass* under the fixed others-witness oracle, so
replaying historical failures is a null experiment. Qualitative analysis showed
E6 wins concentrated on scenario-8 (`others`) arithmetic/output repairs.

This script:
1. Takes referenceCode for each task
2. Injects a deterministic bug in the `others` / final-else branch (wrong constant)
3. Builds SemanticFeedback from the formal checker
4. Runs ONE T=0 repair per feedback variant
5. Reports which fields recover the bug

Default task set: the 14 E6 win tasks (mechanism-relevant).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from src.formal.checker import Counterexample, extract_python_code, run_formal_check
from src.llm.ecnu_client import ECNUClient
from src.pipeline.runner import build_prompt
from src.repair.feedback_ir import FeedbackRenderer, SemanticFeedback, SemanticFeedbackIR

OUT_DEFAULT = ROOT / "artifacts" / "run_ir_seeded_others_ablation_v1"
VARIANTS = [
    ("test_only", "A"),
    ("test_expected", "B"),
    ("semantic_ir", "FULL"),
    ("ir_no_scenario_id", "NO_SID"),
    ("ir_no_expected", "NO_EXP"),
    ("ir_no_constraint", "NO_CON"),
    ("ir_no_reason", "NO_REA"),
    ("ir_no_suggested_fix", "NO_FIX"),
    ("ir_nl_only", "NL"),
]


def inject_others_bug(code: str) -> str:
    """Corrupt the last return/dict in an else/others-like branch.

    Heuristic: flip the last integer literal in the final return dict, or append
    a wrong trailing assignment. Keeps syntax valid for typical hard-task refs.
    """
    # Prefer mutating the last dict literal numbers: change last int to last+7
    matches = list(re.finditer(r"\b(\d+)\b", code))
    if not matches:
        return code + "\n# BUG\n"
    m = matches[-1]
    old = m.group(1)
    new = str(int(old) + 7)
    return code[: m.start()] + new + code[m.end() :]


def _cex_to_feedback(task: dict, code: str) -> list[SemanticFeedback]:
    fr = run_formal_check(code, task, max_cases=32)
    ir = SemanticFeedbackIR.from_counterexamples(fr.counterexamples, task=task)
    return ir.records


def _job_worker(payload: dict) -> dict:
    """Process-safe worker: one task x one variant."""
    from src.formal.checker import extract_python_code, run_formal_check
    from src.llm.ecnu_client import ECNUClient
    from src.pipeline.runner import build_prompt
    from src.repair.feedback_ir import FeedbackRenderer, SemanticFeedback

    task = payload["task"]
    variant = payload["variant"]
    label = payload["label"]
    frozen = payload["frozen_code"]
    records = [SemanticFeedback.from_json(d) for d in payload["records"]]
    feedback = FeedbackRenderer.render(records, variant=variant)
    feedback_block = f"Current code:\n```python\n{frozen}\n```\n\n{feedback}"
    messages = build_prompt(task, feedback_block)
    llm = ECNUClient(log_dir=Path(payload["log_dir"]))
    resp = llm.chat(messages, temperature=0.0, top_p=0.9)
    code = extract_python_code(resp.content) or frozen
    fr = run_formal_check(code, task, max_cases=32)
    return {
        "task_id": payload["task_id"],
        "feedback_variant": variant,
        "feedback_variant_label": label,
        "frozen_conf": payload["frozen_conf"],
        "formal_conformance": fr.conformance_rate,
        "delta_vs_frozen": fr.conformance_rate - payload["frozen_conf"],
        "formal_passed": fr.passed,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--tasks",
        type=Path,
        default=ROOT / "benchmarks" / "hard_tasks_annotated.json",
    )
    ap.add_argument(
        "--win-list",
        type=Path,
        default=ROOT
        / "paper"
        / "hsp-agile"
        / "artifacts"
        / "strengthening_sprint"
        / "agent_a_evidence"
        / "e6_win_tasks.json",
    )
    ap.add_argument("--out-dir", type=Path, default=OUT_DEFAULT)
    ap.add_argument("--parallelism", type=int, default=4)
    ap.add_argument("--task-limit", type=int, default=None)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    results_path = args.out_dir / "results.jsonl"

    all_tasks = {t["taskId"]: t for t in json.loads(args.tasks.read_text(encoding="utf-8"))}
    win_ids = json.loads(args.win_list.read_text(encoding="utf-8"))["semantic_ir_wins"]
    if args.task_limit:
        win_ids = win_ids[: args.task_limit]

    seeds = []
    for tid in win_ids:
        task = all_tasks[tid]
        ref = task.get("referenceCode") or ""
        if not ref.strip():
            continue
        buggy = inject_others_bug(ref)
        fr = run_formal_check(buggy, task, max_cases=32)
        if fr.conformance_rate >= 1.0 - 1e-12:
            # mutation didn't bite; try flipping first int instead
            buggy2 = re.sub(r"\b(\d+)\b", lambda m: str(int(m.group(1)) + 3), ref, count=1)
            fr = run_formal_check(buggy2, task, max_cases=32)
            buggy = buggy2
        if fr.conformance_rate >= 1.0 - 1e-12:
            continue
        records = _cex_to_feedback(task, buggy)
        if not records:
            continue
        seeds.append(
            {
                "task_id": tid,
                "task": task,
                "frozen_code": buggy,
                "frozen_conf": fr.conformance_rate,
                "records": [r.to_json() for r in records],
            }
        )

    (args.out_dir / "seed_meta.json").write_text(
        json.dumps(
            [{"task_id": s["task_id"], "frozen_conf": s["frozen_conf"], "n_records": len(s["records"])} for s in seeds],
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[seeded-others] usable seeds={len(seeds)}")

    done = set()
    if results_path.exists():
        for line in results_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                done.add((r["task_id"], r["feedback_variant"]))

    pending = []
    log_dir = str(args.out_dir / "llm_logs")
    for s in seeds:
        for variant, label in VARIANTS:
            if (s["task_id"], variant) in done:
                continue
            pending.append(
                {
                    "task_id": s["task_id"],
                    "task": s["task"],
                    "frozen_code": s["frozen_code"],
                    "frozen_conf": s["frozen_conf"],
                    "records": s["records"],
                    "variant": variant,
                    "label": label,
                    "log_dir": log_dir,
                }
            )
    print(f"[seeded-others] pending={len(pending)}")

    with results_path.open("a", encoding="utf-8") as w:
        if args.parallelism <= 1:
            for p in pending:
                rec = _job_worker(p)
                w.write(json.dumps(rec, ensure_ascii=False) + "\n")
                w.flush()
                print(
                    f"[seeded] {rec['task_id']} {rec['feedback_variant_label']} "
                    f"{rec['frozen_conf']:.3f}->{rec['formal_conformance']:.3f}"
                )
        else:
            with ProcessPoolExecutor(max_workers=args.parallelism) as ex:
                futs = [ex.submit(_job_worker, p) for p in pending]
                for fut in as_completed(futs):
                    rec = fut.result()
                    w.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    w.flush()
                    print(
                        f"[seeded] {rec['task_id']} {rec['feedback_variant_label']} "
                        f"{rec['frozen_conf']:.3f}->{rec['formal_conformance']:.3f}"
                    )

    # summary
    from collections import defaultdict

    rows = [
        json.loads(l)
        for l in results_path.read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]
    means: dict[str, list[float]] = defaultdict(list)
    deltas: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        means[r["feedback_variant"]].append(float(r["formal_conformance"]))
        deltas[r["feedback_variant"]].append(float(r["delta_vs_frozen"]))
    summary = {
        "n_rows": len(rows),
        "n_seeds": len(seeds),
        "mean_conf": {k: round(sum(v) / len(v), 4) for k, v in sorted(means.items())},
        "mean_delta_vs_frozen": {
            k: round(sum(v) / len(v), 4) for k, v in sorted(deltas.items())
        },
    }
    (args.out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    report_dir = (
        ROOT
        / "paper"
        / "hsp-agile"
        / "artifacts"
        / "strengthening_sprint"
        / "agent_b_ir_ablation"
    )
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "seeded_others_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
