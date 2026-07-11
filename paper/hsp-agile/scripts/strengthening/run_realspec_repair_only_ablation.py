#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Repair-only feedback ablation on RealSpec B1-failed codes (frozen).

NOTE (2026-07): In run_realspec_v1_b1b2m, B1 failures often have empty LLM
responses (generation failure, not a buggy implementation). Prefer the
hard-seed protocol on RealSpec referenceCode instead:

  python paper/hsp-agile/scripts/strengthening/run_ir_hard_seed_ablation.py \\
    --tasks benchmarks/realspec/realspec_v1.json \\
    --task-ids benchmarks/realspec_all_ids.json \\
    --seed-types swap_bodies invert_order wrong_relop \\
    --model gemini-2.5-flash --task-limit 20 ...

This script still supports the rare case where a non-empty failing B1 code
exists (results.jsonl or recoverable from llm_logs).
"""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from src.formal.checker import run_formal_check
from src.repair.feedback_ir import SemanticFeedbackIR

VARIANTS = [
    ("test_only", "A"),
    ("test_expected", "B"),
    ("semantic_ir", "FULL"),
    ("ir_no_scenario_id", "NO_SID"),
    ("ir_no_expected", "NO_EXP"),
    ("ir_no_constraint", "NO_CON"),
    ("ir_nl_only", "NL"),
]


def _worker(payload: dict) -> dict:
    from src.formal.checker import extract_python_code, run_formal_check
    from src.llm.ecnu_client import ECNUClient
    from src.pipeline.runner import build_prompt
    from src.repair.feedback_ir import FeedbackRenderer, SemanticFeedback

    records = [SemanticFeedback.from_json(d) for d in payload["records"]]
    feedback = FeedbackRenderer.render(records, variant=payload["variant"])
    block = f"Current code:\n```python\n{payload['frozen_code']}\n```\n\n{feedback}"
    messages = build_prompt(payload["task"], block)
    llm = ECNUClient(log_dir=Path(payload["log_dir"]), model=payload["model"])
    resp = llm.chat(messages, temperature=0.0, top_p=0.9, model=payload["model"])
    code = extract_python_code(resp.content) or payload["frozen_code"]
    fr = run_formal_check(code, payload["task"], max_cases=32)
    return {
        "task_id": payload["task_id"],
        "model": payload["model"],
        "feedback_variant": payload["variant"],
        "feedback_variant_label": payload["label"],
        "frozen_conf": payload["frozen_conf"],
        "formal_conformance": fr.conformance_rate,
        "delta_vs_frozen": fr.conformance_rate - payload["frozen_conf"],
    }


def _recover_code_from_logs(run_dir: Path, task_id: str, mode: str = "B1") -> str:
    from src.formal.checker import extract_python_code

    log_root = run_dir / "llm_logs"
    if not log_root.exists():
        return ""
    candidates: list[tuple[str, str]] = []
    for p in log_root.rglob("llm_*.json"):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        md = d.get("metadata") or {}
        if md.get("task_id") != task_id:
            continue
        if mode and md.get("mode") not in (None, mode):
            continue
        content = d.get("response")
        if isinstance(content, dict):
            content = content.get("content")
        code = extract_python_code(content or "") or ""
        if code.strip():
            candidates.append((str(md.get("attempt") or "0"), code))
    if not candidates:
        return ""
    candidates.sort(key=lambda x: int(x[0]) if str(x[0]).isdigit() else 0)
    return candidates[0][1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--realspec-run", type=Path, default=ROOT / "artifacts" / "run_realspec_v1_b1b2m" / "results.jsonl")
    ap.add_argument("--benchmark", type=Path, default=ROOT / "benchmarks" / "realspec" / "realspec_v1.json")
    ap.add_argument("--model", default="gemini-2.5-flash")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "artifacts" / "run_realspec_repair_only_gemini_v1")
    ap.add_argument("--parallelism", type=int, default=4)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    run_dir = args.realspec_run.parent
    tasks = {t["taskId"]: t for t in json.loads(args.benchmark.read_text(encoding="utf-8"))}
    rows = [json.loads(l) for l in args.realspec_run.read_text(encoding="utf-8").splitlines() if l.strip()]
    seeds = []
    for r in rows:
        if r.get("mode") != "B1":
            continue
        tid = r["task_id"]
        task = tasks.get(tid)
        if not task:
            continue
        if float(r.get("formal_conformance") or 0) >= 1.0 - 1e-12:
            continue
        code = (r.get("code") or "").strip() or _recover_code_from_logs(run_dir, tid, "B1")
        if not code:
            print(f"[skip] no code for {tid}")
            continue
        fr = run_formal_check(code, task, max_cases=32)
        if fr.conformance_rate >= 1.0 - 1e-12:
            print(f"[skip] recovered code already passes for {tid}")
            continue
        ir = SemanticFeedbackIR.from_counterexamples(fr.counterexamples, task=task)
        if not ir.records:
            continue
        seeds.append(
            {
                "task_id": tid,
                "task": task,
                "frozen_code": code,
                "frozen_conf": fr.conformance_rate,
                "records": [x.to_json() for x in ir.records],
            }
        )
    print(f"[realspec-repair-only] seeds={len(seeds)} model={args.model}")
    (args.out_dir / "seed_meta.json").write_text(
        json.dumps([{"task_id": s["task_id"], "frozen_conf": s["frozen_conf"]} for s in seeds], indent=2),
        encoding="utf-8",
    )

    results_path = args.out_dir / "results.jsonl"
    done = set()
    if results_path.exists():
        for line in results_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                done.add((r["task_id"], r["feedback_variant"]))

    pending = []
    for s in seeds:
        for v, lab in VARIANTS:
            if (s["task_id"], v) in done:
                continue
            pending.append(
                {
                    **{k: s[k] for k in ("task_id", "task", "frozen_code", "frozen_conf", "records")},
                    "variant": v,
                    "label": lab,
                    "model": args.model,
                    "log_dir": str(args.out_dir / "llm_logs"),
                }
            )
    print(f"[realspec-repair-only] pending={len(pending)}")

    with results_path.open("a", encoding="utf-8") as w:
        with ProcessPoolExecutor(max_workers=max(1, args.parallelism)) as ex:
            futs = [ex.submit(_worker, p) for p in pending]
            for fut in as_completed(futs):
                rec = fut.result()
                w.write(json.dumps(rec, ensure_ascii=False) + "\n")
                w.flush()
                print(
                    f"[ror] {rec['task_id']} {rec['feedback_variant_label']} "
                    f"{rec['frozen_conf']:.3f}->{rec['formal_conformance']:.3f}"
                )

    from collections import defaultdict

    rows2 = [json.loads(l) for l in results_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    means = defaultdict(list)
    for r in rows2:
        means[r["feedback_variant"]].append(float(r["formal_conformance"]))
    summary = {k: round(sum(v) / len(v), 4) for k, v in sorted(means.items())}
    (args.out_dir / "summary.json").write_text(json.dumps({"mean_conf": summary, "n": len(rows2)}, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
