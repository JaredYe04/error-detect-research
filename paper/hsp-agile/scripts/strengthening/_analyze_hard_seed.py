# -*- coding: utf-8 -*-
import json
from collections import Counter, defaultdict
from pathlib import Path

p = Path("artifacts/run_ir_hard_seed_ablation_ecnu_plus_v1/results.jsonl")
rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
print("n_rows", len(rows))
print("seed types", Counter(r.get("seed_type") for r in rows))
print("tasks", len({r["task_id"] for r in rows}))
print("expected_full", 14 * 3 * 9)

means = defaultdict(list)
by = defaultdict(dict)
for r in rows:
    k = f"{r.get('seed_type')}|{r['feedback_variant']}"
    means[k].append(float(r["formal_conformance"]))
    by[(r["task_id"], r.get("seed_type"))][r["feedback_variant"]] = float(r["formal_conformance"])

print("--- means ---")
for k in sorted(means):
    print(k, round(sum(means[k]) / len(means[k]), 4), "n", len(means[k]))

print("--- paired FULL vs test_only by seed ---")
for st in ["swap_bodies", "invert_order", "wrong_relop"]:
    w = l = t = 0
    ds = []
    for (tid, sst), s in by.items():
        if sst != st or "semantic_ir" not in s or "test_only" not in s:
            continue
        d = s["semantic_ir"] - s["test_only"]
        ds.append(d)
        if d > 1e-12:
            w += 1
        elif d < -1e-12:
            l += 1
        else:
            t += 1
    print(st, "W/L/T", w, l, t, "mean_d_pp", round(100 * sum(ds) / max(len(ds), 1), 2))

for variant in ["ir_no_expected", "ir_no_scenario_id", "ir_no_constraint", "ir_nl_only"]:
    print(f"--- paired FULL vs {variant} (wrong_relop) ---")
    w = l = t = 0
    for (tid, sst), s in by.items():
        if sst != "wrong_relop" or "semantic_ir" not in s or variant not in s:
            continue
        d = s["semantic_ir"] - s[variant]
        if d > 1e-12:
            w += 1
        elif d < -1e-12:
            l += 1
        else:
            t += 1
    print("W/L/T", w, l, t)
