#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Evaluate deployment policies vs always-B2 / always-M (Agent F companion)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
A_DIR = ROOT / "paper" / "hsp-agile" / "artifacts" / "strengthening_sprint" / "agent_a_evidence"
F_DIR = ROOT / "paper" / "hsp-agile" / "artifacts" / "strengthening_sprint" / "agent_f_deployment"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=A_DIR / "task_feature_db.csv")
    ap.add_argument("--out", type=Path, default=F_DIR / "policy_eval.json")
    args = ap.parse_args()
    df = pd.read_csv(args.db).dropna(subset=["delta_ir_minus_test_only"])
    delta = df["delta_ir_minus_test_only"]

    policies = {
        "always_B2": {"mean_delta": 0.0, "frac_m": 0.0},
        "always_M": {"mean_delta": float(delta.mean()), "frac_m": 1.0},
        "tier_high_only": {
            "mean_delta": float(delta[df["overlap_density_tier"] == "high"].sum() / len(df)),
            "frac_m": float((df["overlap_density_tier"] == "high").mean()),
        },
        "overlap_gt_1.25": {
            "mean_delta": float(delta[df["overlap_rate"] > 1.25].sum() / len(df)),
            "frac_m": float((df["overlap_rate"] > 1.25).mean()),
        },
        "atoms_gt_16": {
            "mean_delta": float(delta[df["n_guard_atoms"] > 16].sum() / len(df)),
            "frac_m": float((df["n_guard_atoms"] > 16).mean()),
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(policies, indent=2), encoding="utf-8")
    print(json.dumps(policies, indent=2))


if __name__ == "__main__":
    main()
