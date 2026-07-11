#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Winner Feature Analysis: which task features predict E6 semantic_ir wins?

Reads task_feature_db.json produced by build_task_feature_db.py.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
OUT_DIR = (
    ROOT
    / "paper"
    / "hsp-agile"
    / "artifacts"
    / "strengthening_sprint"
    / "agent_a_evidence"
)
EPS = 1e-12


def _stratify(df: pd.DataFrame, col: str) -> pd.DataFrame:
    rows = []
    for key, g in df.groupby(col, dropna=False):
        deltas = g["delta_ir_minus_test_only"].dropna()
        wins = int((g["e6_winner"] == "semantic_ir").sum())
        losses = int((g["e6_winner"] == "test_only").sum())
        ties = int((g["e6_winner"] == "tie").sum())
        rows.append(
            {
                "feature": col,
                "level": str(key),
                "n": len(g),
                "wins": wins,
                "losses": losses,
                "ties": ties,
                "win_rate_among_decisive": round(wins / max(wins + losses, 1), 4),
                "mean_delta_pp": round(float(deltas.mean()) * 100, 3) if len(deltas) else None,
                "median_delta_pp": round(float(deltas.median()) * 100, 3) if len(deltas) else None,
            }
        )
    return pd.DataFrame(rows)


def _point_biserial(df: pd.DataFrame, feature: str) -> dict:
    """Correlate continuous feature with win (1) vs not-win (0) among decisive tasks."""
    sub = df[df["e6_winner"].isin(["semantic_ir", "test_only"])].copy()
    if sub.empty or feature not in sub.columns:
        return {"feature": feature, "n": 0, "corr": None}
    y = (sub["e6_winner"] == "semantic_ir").astype(float).values
    x = pd.to_numeric(sub[feature], errors="coerce").values
    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() < 5 or y[mask].std() < EPS or x[mask].std() < EPS:
        return {"feature": feature, "n": int(mask.sum()), "corr": None}
    corr = float(np.corrcoef(x[mask], y[mask])[0, 1])
    return {"feature": feature, "n": int(mask.sum()), "corr": round(corr, 4)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, default=OUT_DIR / "task_feature_db.json")
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_json(args.db)
    # Derived bins
    df["overlap_bin"] = pd.cut(
        df["overlap_rate"],
        bins=[-0.01, 1.0, 1.25, 1.5, 10],
        labels=["<=1.0", "1.0-1.25", "1.25-1.5", ">1.5"],
    )
    df["atoms_bin"] = pd.cut(
        df["n_guard_atoms"],
        bins=[-1, 12, 16, 20, 100],
        labels=["<=12", "13-16", "17-20", ">20"],
    )

    tier = _stratify(df, "overlap_density_tier")
    overlap_bin = _stratify(df, "overlap_bin")
    atoms_bin = _stratify(df, "atoms_bin")
    multi = _stratify(df, "multi_output")
    by_tier = pd.concat([tier, overlap_bin, atoms_bin, multi], ignore_index=True)
    by_tier.to_csv(args.out_dir / "winner_by_tier.csv", index=False)

    win_tasks = df[df["e6_winner"] == "semantic_ir"]["task_id"].tolist()
    loss_tasks = df[df["e6_winner"] == "test_only"]["task_id"].tolist()
    (args.out_dir / "e6_win_tasks.json").write_text(
        json.dumps(
            {
                "semantic_ir_wins": win_tasks,
                "test_only_wins": loss_tasks,
                "n_wins": len(win_tasks),
                "n_losses": len(loss_tasks),
                "n_ties": int((df["e6_winner"] == "tie").sum()),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    cont_feats = [
        "overlap_rate",
        "n_guard_atoms",
        "n_and_ops",
        "n_rel_ops",
        "mean_atoms_per_guard",
        "max_atoms_per_guard",
        "prompt_spec_len",
        "n_outputs",
        "n_inputs",
    ]
    corrs = [_point_biserial(df, f) for f in cont_feats]
    corrs_sorted = sorted(
        [c for c in corrs if c["corr"] is not None],
        key=lambda d: abs(d["corr"]),
        reverse=True,
    )
    (args.out_dir / "feature_win_correlations.json").write_text(
        json.dumps(corrs_sorted, indent=2), encoding="utf-8"
    )

    # Simple threshold rules: mean delta by high vs low overlap
    high = df[df["overlap_density_tier"] == "high"]
    low = df[df["overlap_density_tier"] == "low"]
    med = df[df["overlap_density_tier"] == "medium"]

    def _summary(g: pd.DataFrame) -> dict:
        d = g["delta_ir_minus_test_only"].dropna()
        return {
            "n": len(g),
            "wins": int((g["e6_winner"] == "semantic_ir").sum()),
            "losses": int((g["e6_winner"] == "test_only").sum()),
            "ties": int((g["e6_winner"] == "tie").sum()),
            "mean_delta_pp": round(float(d.mean()) * 100, 3) if len(d) else None,
        }

    # Compare win vs loss feature means
    wins = df[df["e6_winner"] == "semantic_ir"]
    losses = df[df["e6_winner"] == "test_only"]
    ties = df[df["e6_winner"] == "tie"]
    mean_cmp = {}
    for f in cont_feats:
        mean_cmp[f] = {
            "win_mean": round(float(wins[f].mean()), 4) if len(wins) else None,
            "loss_mean": round(float(losses[f].mean()), 4) if len(losses) else None,
            "tie_mean": round(float(ties[f].mean()), 4) if len(ties) else None,
        }

    # Optional logistic on decisive subset
    logistic = None
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import cross_val_score
        from sklearn.preprocessing import StandardScaler

        sub = df[df["e6_winner"].isin(["semantic_ir", "test_only"])].copy()
        feat_cols = ["overlap_rate", "n_guard_atoms", "n_and_ops", "prompt_spec_len", "n_outputs"]
        X = sub[feat_cols].astype(float).values
        y = (sub["e6_winner"] == "semantic_ir").astype(int).values
        if len(sub) >= 10 and y.sum() >= 3 and (len(y) - y.sum()) >= 2:
            Xs = StandardScaler().fit_transform(X)
            clf = LogisticRegression(max_iter=1000)
            scores = cross_val_score(clf, Xs, y, cv=min(5, len(sub)), scoring="accuracy")
            clf.fit(Xs, y)
            logistic = {
                "features": feat_cols,
                "cv_accuracy_mean": round(float(scores.mean()), 4),
                "cv_accuracy_std": round(float(scores.std()), 4),
                "coefs": {f: round(float(c), 4) for f, c in zip(feat_cols, clf.coef_[0])},
                "n_decisive": int(len(sub)),
                "n_wins": int(y.sum()),
            }
    except Exception as e:  # noqa: BLE001
        logistic = {"error": str(e)}

    report = f"""# Winner Feature Analysis (Agent A)

## Headline (E6: semantic_ir vs test_only)

| Outcome | Count |
|---------|------:|
| semantic_ir wins | {len(win_tasks)} |
| test_only wins | {len(loss_tasks)} |
| ties | {int((df['e6_winner']=='tie').sum())} |
| mean ?? Conf (all tasks) | {round(float(df['delta_ir_minus_test_only'].mean())*100, 3)} pp |

## By overlap density tier

| Tier | n | wins | losses | ties | mean ?? (pp) |
|------|--:|-----:|-------:|-----:|------------:|
| high | {_summary(high)['n']} | {_summary(high)['wins']} | {_summary(high)['losses']} | {_summary(high)['ties']} | {_summary(high)['mean_delta_pp']} |
| medium | {_summary(med)['n']} | {_summary(med)['wins']} | {_summary(med)['losses']} | {_summary(med)['ties']} | {_summary(med)['mean_delta_pp']} |
| low | {_summary(low)['n']} | {_summary(low)['wins']} | {_summary(low)['losses']} | {_summary(low)['ties']} | {_summary(low)['mean_delta_pp']} |

## Feature means: IR-win vs test_only-win tasks

```json
{json.dumps(mean_cmp, indent=2)}
```

## Point-biserial correlations (decisive tasks only)

```json
{json.dumps(corrs_sorted, indent=2)}
```

## Logistic probe (interpretable, small-n)

```json
{json.dumps(logistic, indent=2)}
```

## Reviewer-facing takeaway

Typed Semantic Feedback IR gains are **concentrated**, not uniform:
- Most tasks are **ties**; the +7.7 pp mean is driven by a **small win set** ({len(win_tasks)} tasks).
- Compare tier mean ?? and win counts above to see whether high-overlap / atom-dense specs
  disproportionately host IR wins (this is the pre-hoc deployment signal Agent F consumes).

## Files

- `task_feature_db.csv` / `.json`
- `winner_by_tier.csv`
- `e6_win_tasks.json`
- `feature_win_correlations.json`
"""
    (args.out_dir / "winner_feature_analysis.md").write_text(report, encoding="utf-8")
    (args.out_dir / "STATUS.md").write_text(
        "# Agent A STATUS\n\n- DONE: task feature DB + winner analysis from E6 artifacts.\n"
        "- No new LLM runs.\n",
        encoding="utf-8",
    )
    print(report)
    print(f"Wrote report ???{args.out_dir / 'winner_feature_analysis.md'}")


if __name__ == "__main__":
    main()
