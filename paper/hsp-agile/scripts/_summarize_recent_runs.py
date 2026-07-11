#!/usr/bin/env python3
"""Summarize recent strengthening-sprint experiment runs."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

RUNS = [
    "run_ir_hard_seed_ablation_ecnu_plus_n120_v1",
    "run_ir_hard_seed_ablation_ecnu_plus_n120_slice30_60_v1",
    "run_ir_hard_seed_ablation_gpt4omini_v1",
    "run_ir_hard_seed_ablation_gemini_flash_v1",
    "run_ir_hard_seed_ablation_ecnu_plus_v1",
    "run_ir_hard_seed_realspec_wrong_relop_gemini_full_v1",
    "run_ir_hard_seed_realspec_gemini_n20_40_v1",
    "run_ir_hard_seed_realspec_gpt4omini_v1",
    "run_ir_hard_seed_realspec_gemini_v1",
    "run_ir_hard_seed_realspec_ecnu_v1",
    "run_ir_combo_seed_deepseek_v1",
    "run_ir_combo_seed_gemini_v1",
    "run_ir_combo_seed_gpt4omini_v1",
    "run_realspec_v1_b1b2m",
    "run_realspec_e6_b1fail_v1",
    "run_realspec_e6_b1fail_gemini_v1",
    "run_realspec_repair_only_gemini_v1",
    "run_ir_seeded_others_ablation_v1",
    "run_ir_repair_only_ablation_v1",
    "run_ir_field_ablation_headroom34",
    "run_e1_equal_k_v1",
    "run_e1_ablation_fixed_v1",
    "run_pubind_pilot_v1",
]


def summarize(name: str) -> None:
    root = Path("artifacts") / name
    path = root / "results.jsonl"
    if not path.exists():
        print(f"MISSING {name}")
        return
    by: dict[str, list[float]] = defaultdict(list)
    n = 0
    for line in path.open(encoding="utf-8"):
        r = json.loads(line)
        n += 1
        conf = r.get("formal_conformance")
        if conf is None:
            conf = r.get("strict_formal_conformance", 0.0)
        by[str(r.get("mode", "?"))].append(float(conf))
    meta_bits = ""
    meta = root / "meta.json"
    if meta.exists():
        m = json.loads(meta.read_text(encoding="utf-8"))
        keys = ("model", "modes", "n_tasks", "task_limit", "run_name", "benchmark")
        meta_bits = " | " + ", ".join(f"{k}={m.get(k)}" for k in keys if k in m)
    print(f"\n=== {name} rows={n}{meta_bits}")
    for mode, vals in sorted(by.items()):
        mean = 100.0 * sum(vals) / len(vals)
        print(f"  {mode}: n={len(vals)} Conf={mean:.1f}%")


def main() -> None:
    for name in RUNS:
        summarize(name)


if __name__ == "__main__":
    main()
