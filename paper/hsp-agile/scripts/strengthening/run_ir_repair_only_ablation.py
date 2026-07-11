#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Repair-only IR field ablation using frozen failing codes from E6.

Why: under the fixed others-witness oracle, one-shot Conf often saturates at 1.0,
so full pipeline re-runs cannot measure field importance. This script:

1. Loads original E6 rows (test_only / semantic_ir) with attempt_history
2. Freezes the first failing candidate code (Conf < 1)
3. Re-renders the SAME SemanticFeedback records under each ablation variant
4. Runs ONE repair call (T=0) per variant
5. Scores formal conformance of the repaired code

This isolates feedback *content* while holding the buggy program fixed.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from src.formal.checker import extract_python_code, run_formal_check
from src.llm.ecnu_client import ECNUClient
from src.pipeline.runner import build_prompt
from src.repair.feedback_ir import FeedbackRenderer, SemanticFeedback

DEFAULT_E6 = ROOT / "artifacts" / "run_feedback_v2" / "feedback_variants" / "results.jsonl"
DEFAULT_TASKS = ROOT / "benchmarks" / "hard_tasks_annotated.json"
OUT_DIR = ROOT / "artifacts" / "run_ir_repair_only_ablation_v1"

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


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _records_from_hist(hist_entry: dict) -> list[SemanticFeedback]:
    out: list[SemanticFeedback] = []
    for d in hist_entry.get("semantic_feedback") or []:
        out.append(SemanticFeedback.from_json(d))
    return out


def build_jobs(e6_path: Path, tasks_path: Path, win_only: bool) -> list[dict]:
    tasks = {t["taskId"]: t for t in json.loads(tasks_path.read_text(encoding="utf-8"))}
    rows = _load_jsonl(e6_path)
    by_task: dict[str, dict[str, dict]] = {}
    for r in rows:
        by_task.setdefault(r["task_id"], {})[r["feedback_variant"]] = r

    win_ids = None
    if win_only:
        win_path = (
            ROOT
            / "paper"
            / "hsp-agile"
            / "artifacts"
            / "strengthening_sprint"
            / "agent_a_evidence"
            / "e6_win_tasks.json"
        )
        win_ids = set(json.loads(win_path.read_text(encoding="utf-8"))["semantic_ir_wins"])

    jobs: list[dict] = []
    for tid, variants in by_task.items():
        if win_only and tid not in win_ids:
            continue
        base = variants.get("test_only")
        ir = variants.get("semantic_ir")
        if not base or not ir:
            continue
        code = (base.get("code") or "").strip()
        if not code:
            continue
        task = tasks.get(tid)
        if not task:
            continue
        fr = run_formal_check(code, task, max_cases=32)
        if fr.conformance_rate >= 1.0 - 1e-12:
            continue
        # Prefer feedback records from first failing IR/test_only attempt
        records: list[SemanticFeedback] = []
        for src in (base, ir):
            for h in src.get("attempt_history") or []:
                if float(h.get("formal_conformance") or 0) < 1.0 - 1e-12:
                    records = _records_from_hist(h)
                    if records:
                        break
            if records:
                break
        if not records:
            continue
        jobs.append(
            {
                "task_id": tid,
                "task": task,
                "frozen_code": code,
                "frozen_conf": fr.conformance_rate,
                "records": [r.to_json() for r in records],
            }
        )
    return jobs


def repair_once(job: dict, variant: str, label: str, llm: ECNUClient) -> dict:
    task = job["task"]
    records = [SemanticFeedback.from_json(d) for d in job["records"]]
    feedback = FeedbackRenderer.render(records, variant=variant)
    feedback_block = (
        f"Current code:\n```python\n{job['frozen_code']}\n```\n\n{feedback}"
    )
    messages = build_prompt(task, feedback_block)
    resp = llm.chat(messages, temperature=0.0, top_p=0.9)
    code = extract_python_code(resp.content) or job["frozen_code"]
    fr = run_formal_check(code, task, max_cases=32)
    return {
        "task_id": job["task_id"],
        "feedback_variant": variant,
        "feedback_variant_label": label,
        "frozen_conf": job["frozen_conf"],
        "formal_conformance": fr.conformance_rate,
        "formal_passed": fr.passed,
        "delta_vs_frozen": fr.conformance_rate - job["frozen_conf"],
        "code": code,
        "prompt_feedback_preview": feedback[:500],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--e6", type=Path, default=DEFAULT_E6)
    ap.add_argument("--tasks", type=Path, default=DEFAULT_TASKS)
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    ap.add_argument("--win-only", action="store_true", default=True)
    ap.add_argument("--all-failing", action="store_true", help="Use all E6 failing tasks, not just wins")
    ap.add_argument("--parallelism", type=int, default=4)
    ap.add_argument("--task-limit", type=int, default=None)
    args = ap.parse_args()
    win_only = not args.all_failing

    args.out_dir.mkdir(parents=True, exist_ok=True)
    results_path = args.out_dir / "results.jsonl"

    print("[repair-only] scanning frozen failing codes under CURRENT oracle...")
    jobs = build_jobs(args.e6, args.tasks, win_only=win_only)
    if args.task_limit:
        jobs = jobs[: args.task_limit]
    print(f"[repair-only] usable frozen-fail jobs: {len(jobs)}")
    (args.out_dir / "frozen_jobs_meta.json").write_text(
        json.dumps(
            [{"task_id": j["task_id"], "frozen_conf": j["frozen_conf"], "n_records": len(j["records"])} for j in jobs],
            indent=2,
        ),
        encoding="utf-8",
    )
    if not jobs:
        print("[repair-only] no jobs — frozen codes no longer fail under fixed oracle.")
        print("             Fall back to synthetic buggy seeds or weaker model.")
        return

    done = set()
    if results_path.exists():
        for r in _load_jsonl(results_path):
            done.add((r["task_id"], r["feedback_variant"]))

    llm = ECNUClient(log_dir=args.out_dir / "llm_logs")
    pending = []
    for j in jobs:
        for variant, label in VARIANTS:
            if (j["task_id"], variant) in done:
                continue
            pending.append((j, variant, label))

    print(f"[repair-only] pending={len(pending)} done={len(done)}")
    with results_path.open("a", encoding="utf-8") as w:
        if args.parallelism <= 1:
            for j, variant, label in pending:
                rec = repair_once(j, variant, label, llm)
                w.write(json.dumps(rec, ensure_ascii=False) + "\n")
                w.flush()
                print(
                    f"[repair-only] {rec['task_id']} {label} "
                    f"frozen={rec['frozen_conf']:.3f} -> {rec['formal_conformance']:.3f}"
                )
        else:
            with ThreadPoolExecutor(max_workers=args.parallelism) as ex:
                futs = {
                    ex.submit(repair_once, j, variant, label, llm): (j["task_id"], label)
                    for j, variant, label in pending
                }
                for fut in as_completed(futs):
                    rec = fut.result()
                    w.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    w.flush()
                    print(
                        f"[repair-only] {rec['task_id']} {rec['feedback_variant_label']} "
                        f"frozen={rec['frozen_conf']:.3f} -> {rec['formal_conformance']:.3f}"
                    )

    # summarize
    rows = _load_jsonl(results_path)
    from collections import defaultdict

    means: dict[str, list[float]] = defaultdict(list)
    deltas: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        means[r["feedback_variant"]].append(float(r["formal_conformance"]))
        deltas[r["feedback_variant"]].append(float(r["delta_vs_frozen"]))
    summary = {
        "n_rows": len(rows),
        "mean_conf": {k: round(sum(v) / len(v), 4) for k, v in sorted(means.items())},
        "mean_delta_vs_frozen": {k: round(sum(v) / len(v), 4) for k, v in sorted(deltas.items())},
    }
    (args.out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
