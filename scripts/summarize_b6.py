#!/usr/bin/env python3
import json
from pathlib import Path

import pandas as pd

for label, path in [
    ("FULL", "artifacts/run_b6_full_v1/results.jsonl"),
    ("STRAT", "artifacts/run_b6_stratified_v1/results.jsonl"),
]:
    rows = [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]
    df = pd.DataFrame(rows)
    if "repeat" in df.columns:
        df = df[df["repeat"] == 0]
    conf = "strict_formal_conformance" if "strict_formal_conformance" in df.columns else "formal_conformance"
    succ = "strict_formal_passed" if "strict_formal_passed" in df.columns else "success"
    print(f"=== {label} ===")
    for mode in sorted(df["mode"].unique()):
        sub = df[df["mode"] == mode]
        print(
            f"  {mode}: n={len(sub)} strict={sub[succ].mean()*100:.1f}% "
            f"conf={sub[conf].mean()*100:.1f}% kill={sub['mutation_kill_rate'].mean()*100:.1f}% "
            f"lat={sub['latency_ms'].mean():.0f} fail={sub.get('strict_failures', pd.Series([0])).mean():.2f}"
        )
