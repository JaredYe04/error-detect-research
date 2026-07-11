#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hard-seed IR field ablation — strengthen C2 uniqueness evidence.

Seed types (deterministic mutations of referenceCode):
  - swap_bodies: swap return bodies of the first two guarded branches
  - invert_order: reverse if/elif branch order (ordering bug)
  - wrong_relop: flip first <= to >= (or > to <) in a guard
  - others_const: legacy easy seed (last int +7) for baseline comparison

Protocol: freeze buggy code -> render SAME SemanticFeedback under each IR
variant -> one T=0 repair -> score Conf. Supports --model for weaker endpoints.
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

from src.formal.checker import run_formal_check
from src.repair.feedback_ir import SemanticFeedbackIR

OUT_DEFAULT = ROOT / "artifacts" / "run_ir_hard_seed_ablation_v1"
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

BRANCH_RE = re.compile(
    r"(?P<header>^[ \t]*(?:if|elif)[^\n]+:)\n(?P<body>(?:^[ \t]+.*\n)+)",
    re.M,
)


def inject_others_const(code: str) -> str:
    matches = list(re.finditer(r"\b(\d+)\b", code))
    if not matches:
        return code
    m = matches[-1]
    return code[: m.start()] + str(int(m.group(1)) + 7) + code[m.end() :]


def inject_wrong_relop(code: str) -> str:
    """Flip the first relational operator in a guard condition."""
    for a, b in (("<=", ">="), (">=", "<="), ("<", ">"), (">", "<"), ("==", "!="), ("!=", "==")):
        if a in code:
            return code.replace(a, b, 1)
    return code


def _branch_spans(code: str) -> list[re.Match[str]]:
    return list(BRANCH_RE.finditer(code))


def inject_swap_bodies(code: str) -> str:
    """Swap the indented bodies of the first two if/elif branches."""
    branches = _branch_spans(code)
    if len(branches) < 2:
        return inject_others_const(code)
    b0, b1 = branches[0], branches[1]
    # rebuild: ... header0 + body1 + header1 + body0 ...
    return (
        code[: b0.start()]
        + b0.group("header")
        + "\n"
        + b1.group("body")
        + b1.group("header")
        + "\n"
        + b0.group("body")
        + code[b1.end() :]
    )


def inject_invert_order(code: str) -> str:
    """Reverse order of if/elif branches (keep final else if present)."""
    branches = _branch_spans(code)
    if len(branches) < 2:
        return inject_swap_bodies(code)
    else_m = re.search(r"(^[ \t]*else:\n(?:^[ \t]+.*\n)*)", code[branches[-1].end() :], re.M)
    else_block = ""
    end = branches[-1].end()
    if else_m and else_m.start() == 0:
        else_block = else_m.group(1)
        end = branches[-1].end() + else_m.end()
    # Convert first elif -> if and first if in reversed list accordingly
    chunks = []
    rev = list(reversed(branches))
    for i, b in enumerate(rev):
        header = b.group("header")
        if i == 0:
            header = re.sub(r"\belif\b", "if", header, count=1)
        else:
            header = re.sub(r"^[ \t]*if\b", lambda m: m.group(0).replace("if", "elif", 1), header, count=1)
            if "elif" not in header and header.lstrip().startswith("if"):
                # already if from original first branch now later — force elif
                header = re.sub(r"(\bif\b)", "elif", header, count=1)
        chunks.append(header + "\n" + b.group("body"))
    return code[: branches[0].start()] + "".join(chunks) + else_block + code[end:]


def inject_combo_swap_relop(code: str) -> str:
    """Harder seed: swap first two bodies, then flip a relational op."""
    return inject_wrong_relop(inject_swap_bodies(code))


def inject_combo_invert_relop(code: str) -> str:
    """Harder seed: invert branch order, then flip a relational op."""
    return inject_wrong_relop(inject_invert_order(code))


def inject_drop_first_guard(code: str) -> str:
    """Delete the first guarded branch (force fall-through / wrong routing)."""
    branches = _branch_spans(code)
    if len(branches) < 2:
        return inject_combo_swap_relop(code)
    b0 = branches[0]
    return code[: b0.start()] + code[b0.end() :]


INJECTORS = {
    "others_const": inject_others_const,
    "wrong_relop": inject_wrong_relop,
    "swap_bodies": inject_swap_bodies,
    "invert_order": inject_invert_order,
    "combo_swap_relop": inject_combo_swap_relop,
    "combo_invert_relop": inject_combo_invert_relop,
    "drop_first_guard": inject_drop_first_guard,
}


def _cex_records(task: dict, code: str) -> tuple[float, list[dict]]:
    fr = run_formal_check(code, task, max_cases=32)
    ir = SemanticFeedbackIR.from_counterexamples(fr.counterexamples, task=task)
    return fr.conformance_rate, [r.to_json() for r in ir.records]


def _job_worker(payload: dict) -> dict:
    from src.formal.checker import extract_python_code, run_formal_check
    from src.llm.ecnu_client import ECNUClient
    from src.pipeline.runner import build_prompt
    from src.repair.feedback_ir import FeedbackRenderer, SemanticFeedback

    task = payload["task"]
    records = [SemanticFeedback.from_json(d) for d in payload["records"]]
    feedback = FeedbackRenderer.render(records, variant=payload["variant"])
    feedback_block = f"Current code:\n```python\n{payload['frozen_code']}\n```\n\n{feedback}"
    messages = build_prompt(task, feedback_block)
    llm = ECNUClient(log_dir=Path(payload["log_dir"]), model=payload.get("model") or "ecnu-plus")
    resp = llm.chat(messages, temperature=0.0, top_p=0.9, model=payload.get("model"))
    code = extract_python_code(resp.content) or payload["frozen_code"]
    fr = run_formal_check(code, task, max_cases=32)
    return {
        "task_id": payload["task_id"],
        "seed_type": payload["seed_type"],
        "model": payload.get("model") or "ecnu-plus",
        "feedback_variant": payload["variant"],
        "feedback_variant_label": payload["label"],
        "frozen_conf": payload["frozen_conf"],
        "formal_conformance": fr.conformance_rate,
        "delta_vs_frozen": fr.conformance_rate - payload["frozen_conf"],
        "formal_passed": fr.passed,
    }


def build_seeds(
    tasks: dict[str, dict],
    task_ids: list[str],
    seed_types: list[str],
) -> list[dict]:
    seeds: list[dict] = []
    for tid in task_ids:
        task = tasks.get(tid)
        if not task:
            continue
        ref = (task.get("referenceCode") or "").strip()
        if not ref:
            continue
        for st in seed_types:
            inj = INJECTORS[st]
            buggy = inj(ref)
            if buggy == ref:
                continue
            conf, records = _cex_records(task, buggy)
            if conf >= 1.0 - 1e-12 or not records:
                continue
            seeds.append(
                {
                    "task_id": tid,
                    "task": task,
                    "seed_type": st,
                    "frozen_code": buggy,
                    "frozen_conf": conf,
                    "records": records,
                }
            )
    return seeds


def summarize(results_path: Path) -> dict:
    from collections import defaultdict

    rows = [json.loads(l) for l in results_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    by_key: dict[tuple[str, str], list[float]] = defaultdict(list)
    paired: dict[str, dict] = {}
    for r in rows:
        key = (r.get("seed_type", "?"), r["feedback_variant"])
        by_key[key].append(float(r["formal_conformance"]))

    # paired FULL vs others within seed_type
    by_task_seed: dict[tuple[str, str], dict[str, float]] = defaultdict(dict)
    for r in rows:
        by_task_seed[(r["task_id"], r.get("seed_type", "?"))][r["feedback_variant"]] = float(
            r["formal_conformance"]
        )
    for st in {k[1] for k in by_task_seed}:
        for variant in {r["feedback_variant"] for r in rows}:
            if variant == "semantic_ir":
                continue
            w = l = t = 0
            for (tid, sst), scores in by_task_seed.items():
                if sst != st or "semantic_ir" not in scores or variant not in scores:
                    continue
                d = scores["semantic_ir"] - scores[variant]
                if d > 1e-12:
                    w += 1
                elif d < -1e-12:
                    l += 1
                else:
                    t += 1
            paired[f"{st}|FULL_vs_{variant}"] = {"wins": w, "losses": l, "ties": t}

    return {
        "n_rows": len(rows),
        "mean_conf_by_seed_variant": {
            f"{s}|{v}": round(sum(xs) / len(xs), 4) for (s, v), xs in sorted(by_key.items())
        },
        "paired_full_vs_ablation": paired,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tasks", type=Path, default=ROOT / "benchmarks" / "hard_tasks_annotated.json")
    ap.add_argument(
        "--task-ids",
        type=Path,
        default=ROOT
        / "paper"
        / "hsp-agile"
        / "artifacts"
        / "strengthening_sprint"
        / "agent_a_evidence"
        / "e6_win_tasks.json",
        help="JSON list of taskIds OR e6_win_tasks.json with semantic_ir_wins",
    )
    ap.add_argument(
        "--seed-types",
        nargs="+",
        default=["swap_bodies", "invert_order", "wrong_relop"],
        choices=list(INJECTORS),
    )
    ap.add_argument("--model", type=str, default="ecnu-plus")
    ap.add_argument("--out-dir", type=Path, default=OUT_DEFAULT)
    ap.add_argument("--parallelism", type=int, default=4)
    ap.add_argument("--task-limit", type=int, default=None)
    ap.add_argument(
        "--variants",
        nargs="+",
        default=None,
        help="Subset of feedback variants (default: full field ablation list)",
    )
    args = ap.parse_args()

    global VARIANTS
    if args.variants:
        label = {
            "test_only": "A",
            "test_expected": "B",
            "semantic_ir": "FULL",
            "ir_no_scenario_id": "NO_SID",
            "ir_no_expected": "NO_EXP",
            "ir_no_constraint": "NO_CON",
            "ir_no_reason": "NO_REA",
            "ir_no_suggested_fix": "NO_FIX",
            "ir_nl_only": "NL",
        }
        VARIANTS = [(v, label.get(v, v[:8].upper())) for v in args.variants]

    raw = json.loads(args.task_ids.read_text(encoding="utf-8"))
    if isinstance(raw, dict) and "semantic_ir_wins" in raw:
        task_ids = list(raw["semantic_ir_wins"])
    elif isinstance(raw, list):
        task_ids = [x if isinstance(x, str) else x.get("taskId") for x in raw]
    else:
        raise SystemExit(f"Unrecognized task-ids file: {args.task_ids}")
    if args.task_limit:
        task_ids = task_ids[: args.task_limit]

    tasks = {t["taskId"]: t for t in json.loads(args.tasks.read_text(encoding="utf-8"))}
    args.out_dir.mkdir(parents=True, exist_ok=True)
    results_path = args.out_dir / "results.jsonl"

    seeds = build_seeds(tasks, task_ids, args.seed_types)
    (args.out_dir / "seed_meta.json").write_text(
        json.dumps(
            [
                {
                    "task_id": s["task_id"],
                    "seed_type": s["seed_type"],
                    "frozen_conf": s["frozen_conf"],
                    "n_records": len(s["records"]),
                }
                for s in seeds
            ],
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[hard-seed] seeds={len(seeds)} types={args.seed_types} model={args.model}")

    done = set()
    if results_path.exists():
        for line in results_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                done.add((r["task_id"], r.get("seed_type"), r["feedback_variant"], r.get("model")))

    pending = []
    log_dir = str(args.out_dir / "llm_logs")
    for s in seeds:
        for variant, label in VARIANTS:
            key = (s["task_id"], s["seed_type"], variant, args.model)
            if key in done:
                continue
            pending.append(
                {
                    "task_id": s["task_id"],
                    "task": s["task"],
                    "seed_type": s["seed_type"],
                    "frozen_code": s["frozen_code"],
                    "frozen_conf": s["frozen_conf"],
                    "records": s["records"],
                    "variant": variant,
                    "label": label,
                    "model": args.model,
                    "log_dir": log_dir,
                }
            )
    print(f"[hard-seed] pending={len(pending)}")

    with results_path.open("a", encoding="utf-8") as w:
        if args.parallelism <= 1:
            for p in pending:
                rec = _job_worker(p)
                w.write(json.dumps(rec, ensure_ascii=False) + "\n")
                w.flush()
                print(
                    f"[{rec['seed_type']}] {rec['task_id']} {rec['feedback_variant_label']} "
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
                        f"[{rec['seed_type']}] {rec['task_id']} {rec['feedback_variant_label']} "
                        f"{rec['frozen_conf']:.3f}->{rec['formal_conformance']:.3f}"
                    )

    summary = summarize(results_path)
    summary["model"] = args.model
    summary["seed_types"] = args.seed_types
    (args.out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    report = (
        ROOT
        / "paper"
        / "hsp-agile"
        / "artifacts"
        / "strengthening_sprint"
        / "agent_b_ir_ablation"
        / f"hard_seed_summary_{args.model.replace('/', '_')}.json"
    )
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
