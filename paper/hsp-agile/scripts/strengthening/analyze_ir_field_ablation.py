#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analyze IR field-ablation results (Agent B).

Consumes results.jsonl with feedback_variant in
{test_only, semantic_ir, ir_no_*, ir_nl_only}.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT_DEFAULT = (
    ROOT
    / "paper"
    / "hsp-agile"
    / "artifacts"
    / "strengthening_sprint"
    / "agent_b_ir_ablation"
)
FOCAL = "semantic_ir"
EPS = 1e-12


def _conf(row: dict) -> float:
    for k in ("strict_formal_conformance", "formal_conformance"):
        if row.get(k) is not None:
            return float(row[k])
    return 0.0


def paired(by_task: dict[str, dict[str, float]], a: str, b: str) -> dict:
    wins = losses = ties = 0
    deltas: list[float] = []
    for scores in by_task.values():
        if a not in scores or b not in scores:
            continue
        d = scores[a] - scores[b]
        deltas.append(d)
        if d > EPS:
            wins += 1
        elif d < -EPS:
            losses += 1
        else:
            ties += 1
    mean = sum(deltas) / len(deltas) if deltas else 0.0
    return {
        "a": a,
        "b": b,
        "n": len(deltas),
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "mean_delta_pp": round(mean * 100, 3),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--results",
        type=Path,
        default=ROOT / "artifacts" / "run_ir_field_ablation_v1" / "ir_field_ablation" / "results.jsonl",
    )
    ap.add_argument("--out-dir", type=Path, default=OUT_DEFAULT)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    if not args.results.exists():
        (args.out_dir / "STATUS.md").write_text(
            f"# Agent B analysis\n\nWAITING for results at `{args.results}`.\n"
            "Run smoke/full campaign first (see PROTOCOL.md).\n",
            encoding="utf-8",
        )
        print(f"No results yet: {args.results}")
        return

    rows = [json.loads(l) for l in args.results.read_text(encoding="utf-8").splitlines() if l.strip()]
    by_task: dict[str, dict[str, float]] = defaultdict(dict)
    means: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        tid = r.get("task_id")
        var = r.get("feedback_variant")
        if not tid or not var:
            continue
        c = _conf(r)
        by_task[str(tid)][str(var)] = c
        means[str(var)].append(c)

    summary = {
        "n_rows": len(rows),
        "n_tasks": len(by_task),
        "mean_conf": {v: round(sum(xs) / len(xs), 4) for v, xs in sorted(means.items())},
        "paired_vs_full_ir": [
            paired(by_task, FOCAL, v)
            for v in sorted(means)
            if v != FOCAL
        ],
        "paired_vs_test_only": [
            paired(by_task, v, "test_only")
            for v in sorted(means)
            if v != "test_only"
        ],
    }
    (args.out_dir / "ir_field_ablation_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    # Critical fields = largest drop when removed vs full IR
    drops = []
    for p in summary["paired_vs_full_ir"]:
        if str(p["b"]).startswith("ir_") or p["b"] == "test_only":
            drops.append((p["b"], p["mean_delta_pp"], p["wins"], p["losses"], p["ties"]))
    drops.sort(key=lambda t: t[1])  # most negative first = biggest harm when using ablated vs full

    lines = [
        "# IR Field Ablation Summary",
        "",
        f"Rows={summary['n_rows']} tasks={summary['n_tasks']}",
        "",
        "## Mean Conf by variant",
        "```json",
        json.dumps(summary["mean_conf"], indent=2),
        "```",
        "",
        "## Paired: full semantic_ir ???variant (negative ???field mattered)",
        "```json",
        json.dumps(summary["paired_vs_full_ir"], indent=2),
        "```",
        "",
        "## Ranked harm when removing a field (lower mean_delta_pp = more critical)",
    ]
    for name, dpp, w, l, t in drops:
        lines.append(f"- `{name}`: ??={dpp} pp (W/L/T {w}/{l}/{t})")
    (args.out_dir / "ir_field_ablation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
