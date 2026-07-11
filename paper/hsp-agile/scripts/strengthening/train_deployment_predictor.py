#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Train a pre-hoc Deployment Predictor (Agent F).

Features: spec-only (overlap, atoms, ...). Label: E6 delta or win.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
A_DIR = (
    ROOT
    / "paper"
    / "hsp-agile"
    / "artifacts"
    / "strengthening_sprint"
    / "agent_a_evidence"
)
OUT = (
    ROOT
    / "paper"
    / "hsp-agile"
    / "artifacts"
    / "strengthening_sprint"
    / "agent_f_deployment"
)

FEATS = [
    "overlap_rate",
    "n_guard_atoms",
    "n_and_ops",
    "n_rel_ops",
    "mean_atoms_per_guard",
    "max_atoms_per_guard",
    "prompt_spec_len",
    "n_outputs",
    "n_inputs",
    "n_scenarios",
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=A_DIR / "task_feature_db.csv")
    ap.add_argument("--out-dir", type=Path, default=OUT)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    if not args.db.exists():
        raise SystemExit(f"Missing feature DB: {args.db} (run build_task_feature_db.py first)")

    df = pd.read_csv(args.db)
    df = df.dropna(subset=["delta_ir_minus_test_only"])
    df["label_win"] = (df["e6_winner"] == "semantic_ir").astype(int)
    df["label_gain"] = (df["delta_ir_minus_test_only"] > 0.05).astype(int)  # >5pp

    X = df[FEATS].astype(float).values
    y_win = df["label_win"].values
    y_gain = df["label_gain"].values
    delta = df["delta_ir_minus_test_only"].values

    from sklearn.linear_model import LogisticRegression, Ridge
    from sklearn.model_selection import cross_val_predict, cross_val_score
    from sklearn.preprocessing import StandardScaler
    from sklearn.tree import DecisionTreeClassifier, export_text
    from sklearn.metrics import f1_score, roc_auc_score

    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    metrics: dict = {"n": int(len(df)), "positive_wins": int(y_win.sum()), "positive_gain5pp": int(y_gain.sum())}

    # Classification: will IR win?
    if y_win.sum() >= 3 and (len(y_win) - y_win.sum()) >= 3:
        clf = LogisticRegression(max_iter=2000, class_weight="balanced")
        acc = cross_val_score(clf, Xs, y_win, cv=5, scoring="accuracy")
        f1 = cross_val_score(clf, Xs, y_win, cv=5, scoring="f1")
        proba = cross_val_predict(clf, Xs, y_win, cv=5, method="predict_proba")[:, 1]
        try:
            auc = float(roc_auc_score(y_win, proba))
        except ValueError:
            auc = None
        clf.fit(Xs, y_win)
        metrics["win_classifier"] = {
            "cv_accuracy_mean": round(float(acc.mean()), 4),
            "cv_accuracy_std": round(float(acc.std()), 4),
            "cv_f1_mean": round(float(f1.mean()), 4),
            "auc": round(auc, 4) if auc is not None else None,
            "coefs": {f: round(float(c), 4) for f, c in zip(FEATS, clf.coef_[0])},
        }
    else:
        metrics["win_classifier"] = {"error": "too few positive/negative wins"}

    # Regression: predict delta
    reg = Ridge(alpha=1.0)
    pred = cross_val_predict(reg, Xs, delta, cv=5)
    metrics["delta_regressor"] = {
        "cv_mae": round(float(np.mean(np.abs(pred - delta))), 4),
        "cv_rmse": round(float(np.sqrt(np.mean((pred - delta) ** 2))), 4),
        "baseline_mae_predict_zero": round(float(np.mean(np.abs(delta))), 4),
    }
    reg.fit(Xs, delta)
    metrics["delta_regressor"]["coefs"] = {f: round(float(c), 4) for f, c in zip(FEATS, reg.coef_)}

    # Interpretable tree rules on gain>5pp
    tree = DecisionTreeClassifier(max_depth=3, min_samples_leaf=8, class_weight="balanced", random_state=42)
    tree.fit(X, y_gain)
    rules_txt = export_text(tree, feature_names=FEATS)
    (args.out_dir / "deployment_tree_rules.txt").write_text(rules_txt, encoding="utf-8")

    # Simple threshold policy from overlap tier (always interpretable)
    # Recommend M if predicted delta > tau
    taus = [0.0, 0.02, 0.05, 0.08]
    policies = []
    # Use CV predictions for honesty
    for tau in taus:
        choose_m = pred > tau
        # oracle regret: if we chose M, get delta; if B2/test_only, get 0 vs IR
        realized = np.where(choose_m, delta, 0.0)
        always_m = delta
        always_b2 = np.zeros_like(delta)
        policies.append(
            {
                "tau": tau,
                "frac_choose_m": round(float(choose_m.mean()), 4),
                "mean_realized_delta": round(float(realized.mean()), 4),
                "mean_always_m": round(float(always_m.mean()), 4),
                "mean_always_b2": round(float(always_b2.mean()), 4),
                "regret_vs_always_m": round(float((always_m - realized).mean()), 4),
            }
        )
    metrics["policies"] = policies

    # Tier rule (no ML)
    tier_rule = []
    for tier, g in df.groupby("overlap_density_tier"):
        tier_rule.append(
            {
                "tier": tier,
                "n": int(len(g)),
                "mean_delta": round(float(g["delta_ir_minus_test_only"].mean()), 4),
                "recommend": "prefer_inspect_M" if g["delta_ir_minus_test_only"].mean() > 0.05 else "default_B2",
            }
        )

    rules = {
        "pre_hoc_features": FEATS,
        "simple_tier_rule": tier_rule,
        "tree_rules_file": "deployment_tree_rules.txt",
        "note": "Pre-hoc only; no attempt_history features. Signal may be weak ???report honestly.",
    }
    (args.out_dir / "deployment_rules.json").write_text(json.dumps(rules, indent=2), encoding="utf-8")
    (args.out_dir / "cv_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (args.out_dir / "feature_importances.json").write_text(
        json.dumps(
            {
                "ridge_delta_coefs": metrics.get("delta_regressor", {}).get("coefs"),
                "logistic_win_coefs": metrics.get("win_classifier", {}).get("coefs"),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    report = f"""# Deployment Predictor Report (Agent F)

## Question

Can we decide **before** running HSP whether typed Semantic Feedback IR is worth enabling?

## Data

- n={metrics['n']} hard tasks with E6 labels
- positive IR wins={metrics['positive_wins']}
- deltas >5pp={metrics['positive_gain5pp']}

## Metrics

```json
{json.dumps(metrics, indent=2)}
```

## Interpretable tier rule

```json
{json.dumps(tier_rule, indent=2)}
```

## Decision sketch

```mermaid
flowchart TD
  S[Spec features: overlap / atoms / outputs] --> P[Predict expected IR gain]
  P -->|gain > tau| M[Enable full HSP / typed IR]
  P -->|gain <= tau| B2[Keep test-feedback B2]
```

## Honest reading

If CV AUC/F1 is near chance, say so: deployment-aware then rests on **release requirements** (Accept/FAR) plus coarse tier rules, not a high-accuracy classifier.
If ridge MAE beats predict-zero, there is usable ranking signal for expected gain.

## Files

- `cv_metrics.json`
- `deployment_rules.json`
- `deployment_tree_rules.txt`
- `feature_importances.json`
"""
    (args.out_dir / "deployment_predictor_report.md").write_text(report, encoding="utf-8")
    (args.out_dir / "STATUS.md").write_text("# Agent F STATUS\n\nDONE: pre-hoc predictor trained on E6 labels.\n", encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
