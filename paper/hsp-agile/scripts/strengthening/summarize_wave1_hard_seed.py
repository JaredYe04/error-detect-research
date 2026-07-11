#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cross-run hard-seed summary: FULL vs test_only / key field ablations."""

from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def load_dedup(paths: list[Path]) -> list[dict]:
    keyed: dict[tuple, dict] = {}
    for path in paths:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            k = (r["task_id"], r.get("seed_type"), r["feedback_variant"], r.get("model"))
            keyed[k] = r
    return list(keyed.values())


def paired(rows: list[dict], seed: str, a: str, b: str) -> dict:
    by_task: dict[str, dict[str, float]] = defaultdict(dict)
    for r in rows:
        if r.get("seed_type") != seed:
            continue
        by_task[r["task_id"]][r["feedback_variant"]] = float(r["formal_conformance"])
    deltas = []
    w = l = t = 0
    for scores in by_task.values():
        if a not in scores or b not in scores:
            continue
        d = scores[a] - scores[b]
        deltas.append(d)
        if d > 1e-12:
            w += 1
        elif d < -1e-12:
            l += 1
        else:
            t += 1
    if not deltas:
        return {"n": 0}
    mean = sum(deltas) / len(deltas)
    rng = random.Random(0)
    boots = []
    for _ in range(2000):
        sample = [deltas[rng.randrange(len(deltas))] for _ in range(len(deltas))]
        boots.append(sum(sample) / len(sample))
    boots.sort()
    lo = boots[int(0.025 * len(boots))]
    hi = boots[int(0.975 * len(boots)) - 1]
    return {
        "n": len(deltas),
        "wlt": f"{w}/{l}/{t}",
        "mean_pp": round(100 * mean, 2),
        "ci95_pp": [round(100 * lo, 2), round(100 * hi, 2)],
        "excl0": not (lo <= 0 <= hi),
    }


def mean_conf(rows: list[dict], seed: str, variant: str) -> float | None:
    xs = [
        float(r["formal_conformance"])
        for r in rows
        if r.get("seed_type") == seed and r["feedback_variant"] == variant
    ]
    return round(sum(xs) / len(xs), 4) if xs else None


def summarize(name: str, paths: list[Path], contrasts: list[tuple[str, str]]) -> dict:
    rows = load_dedup(paths)
    seeds = sorted({r.get("seed_type") for r in rows if r.get("seed_type")})
    models = sorted({r.get("model") for r in rows if r.get("model")})
    out: dict = {
        "name": name,
        "n_rows": len(rows),
        "n_tasks": len({r["task_id"] for r in rows}),
        "models": models,
        "seeds": seeds,
        "paired": {},
        "mean_full_a": {},
    }
    for seed in seeds:
        out["mean_full_a"][seed] = {
            "FULL": mean_conf(rows, seed, "semantic_ir"),
            "A": mean_conf(rows, seed, "test_only"),
            "NO_EXP": mean_conf(rows, seed, "ir_no_expected"),
            "NO_SID": mean_conf(rows, seed, "ir_no_scenario_id"),
        }
        for a, b in contrasts:
            out["paired"][f"{seed}|{a}_vs_{b}"] = paired(rows, seed, a, b)
    return out


CONTRASTS = [
    ("semantic_ir", "test_only"),
    ("semantic_ir", "test_expected"),
    ("semantic_ir", "ir_no_expected"),
    ("semantic_ir", "ir_no_scenario_id"),
    ("semantic_ir", "ir_no_constraint"),
    ("semantic_ir", "ir_nl_only"),
]

RUNS = [
    ("H1_ecnu_e6win14", [ROOT / "artifacts/run_ir_hard_seed_ablation_ecnu_plus_v1/results.jsonl"]),
    ("H2_gemini_e6win14", [ROOT / "artifacts/run_ir_hard_seed_ablation_gemini_flash_v1/results.jsonl"]),
    ("H6_gpt4omini_e6win14", [ROOT / "artifacts/run_ir_hard_seed_ablation_gpt4omini_v1/results.jsonl"]),
    (
        "H4_ecnu_hard60",
        [
            ROOT / "artifacts/run_ir_hard_seed_ablation_ecnu_plus_n120_v1/results.jsonl",
            ROOT / "artifacts/run_ir_hard_seed_ablation_ecnu_plus_n120_slice30_60_v1/results.jsonl",
        ],
    ),
    (
        "H5_realspec_gemini",
        [
            ROOT / "artifacts/run_ir_hard_seed_realspec_gemini_v1/results.jsonl",
            ROOT / "artifacts/run_ir_hard_seed_realspec_gemini_n20_40_v1/results.jsonl",
        ],
    ),
    ("H5_realspec_ecnu", [ROOT / "artifacts/run_ir_hard_seed_realspec_ecnu_v1/results.jsonl"]),
    ("H6_realspec_gpt4omini", [ROOT / "artifacts/run_ir_hard_seed_realspec_gpt4omini_v1/results.jsonl"]),
]


def main() -> None:
    report = [summarize(name, paths, CONTRASTS) for name, paths in RUNS]
    out_dir = ROOT / "paper/hsp-agile/artifacts/strengthening_sprint/agent_b_ir_ablation"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "WAVE1_CROSS_RUN_STATS.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = ["# Wave-1 hard-seed cross-run summary", "", "**Narrative still frozen.**", ""]
    for block in report:
        lines.append(f"## {block['name']} (tasks={block['n_tasks']}, rows={block['n_rows']})")
        lines.append("")
        lines.append("| Seed | FULL | A | NO_EXP | FULL-A W/L/T | d_pp | CI95 | excl0 | FULL-NO_EXP |")
        lines.append("|------|-----:|--:|-------:|-------------:|-----:|------|:-----:|------------:|")
        for seed in block["seeds"]:
            m = block["mean_full_a"][seed]
            pa = block["paired"].get(f"{seed}|semantic_ir_vs_test_only", {})
            pe = block["paired"].get(f"{seed}|semantic_ir_vs_ir_no_expected", {})
            lines.append(
                f"| {seed} | {m['FULL']} | {m['A']} | {m['NO_EXP']} | {pa.get('wlt','-')} | "
                f"{pa.get('mean_pp','-')} | {pa.get('ci95_pp','-')} | {pa.get('excl0','-')} | "
                f"{pe.get('wlt','-')} d{pe.get('mean_pp','-')} excl={pe.get('excl0','-')} |"
            )
        lines.append("")
        hits = [k for k, v in block["paired"].items() if v.get("excl0")]
        if hits:
            lines.append("CI excludes 0: " + ", ".join(hits))
        else:
            lines.append("No paired contrast with CI excluding 0.")
        lines.append("")
    text = "\n".join(lines)
    (out_dir / "WAVE1_CROSS_RUN_SUMMARY.md").write_text(text, encoding="utf-8")
    Path(out_dir / "_wave1_print.txt").write_text(text, encoding="utf-8")
    print("wrote WAVE1_CROSS_RUN_SUMMARY.md")


if __name__ == "__main__":
    main()
