"""Statistical analysis for experiment results."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def load_results(run_dir: Path) -> pd.DataFrame:
    path = run_dir / "results.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return pd.DataFrame(rows)


def aggregate_by_mode(df: pd.DataFrame) -> pd.DataFrame:
    success_col = "strict_formal_passed" if "strict_formal_passed" in df.columns else "success"
    conf_col = "strict_formal_conformance" if "strict_formal_conformance" in df.columns else "formal_conformance"
    agg_map: dict[str, tuple[str, str]] = {
        "n": (success_col, "count"),
        "success_rate": (success_col, "mean"),
        "formal_conformance": (conf_col, "mean"),
        "pattern_violations": ("pattern_violations", "mean"),
        "mutation_kill_rate": ("mutation_kill_rate", "mean"),
        "llm_calls": ("llm_calls", "mean"),
        "latency_ms": ("latency_ms", "mean"),
    }
    if "strict_failures" in df.columns:
        agg_map["strict_failures"] = ("strict_failures", "mean")
    agg = (
        df.groupby("mode")
        .agg(**agg_map)
        .reset_index()
    )
    return agg


def pairwise_tests(df: pd.DataFrame, baseline: str = "B1", method: str = "M", metric: str = "success") -> dict:
    base = df[df["mode"] == baseline].groupby("task_id")[metric].mean()
    treat = df[df["mode"] == method].groupby("task_id")[metric].mean()
    common = base.index.intersection(treat.index)
    if len(common) < 3:
        return {"error": "insufficient paired tasks"}
    b = base.loc[common].values
    t = treat.loc[common].values
    diff = t - b
    if np.all(diff == 0):
        # All differences are zero: no test can be performed; report trivially
        return {
            "baseline": baseline,
            "method": method,
            "metric": metric,
            "n_pairs": int(len(diff)),
            "baseline_mean": float(np.mean(b)),
            "method_mean": float(np.mean(t)),
            "delta": 0.0,
            "wilcoxon_stat": None,
            "p_value": 1.0,
            "effect_size_rank_biserial": 0.0,
            "significant_0.05": False,
            "note": "all_differences_zero",
        }
    try:
        stat, p = stats.wilcoxon(t, b, alternative="greater")
    except ValueError:
        stat, p = float("nan"), 1.0
    # rank-biserial correlation effect size
    n = len(diff)
    ranks = stats.rankdata(np.abs(diff))
    pos = np.sum(ranks[diff > 0])
    neg = np.sum(ranks[diff < 0])
    rbc = (pos - neg) / (n * (n + 1) / 2) if n else 0.0
    return {
        "baseline": baseline,
        "method": method,
        "metric": metric,
        "n_pairs": int(n),
        "baseline_mean": float(np.mean(b)),
        "method_mean": float(np.mean(t)),
        "delta": float(np.mean(t) - np.mean(b)),
        "wilcoxon_stat": float(stat),
        "p_value": float(p),
        "effect_size_rank_biserial": float(rbc),
        "significant_0.05": bool(p < 0.05),
    }


def ablation_analysis(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    metric = "strict_formal_passed" if "strict_formal_passed" in df.columns else "success"
    full = df[df["mode"] == "M"][metric].mean()
    for mode in ["A1", "A2", "A3"]:
        sub = df[df["mode"] == mode]
        if sub.empty:
            continue
        rate = sub[metric].mean()
        rows.append(
            {
                "ablation": mode,
                "success_rate": rate,
                "delta_vs_M": rate - full,
                "component_removed": {
                    "A1": "formal_check",
                    "A2": "pattern_guard",
                    "A3": "repair_loop",
                }[mode],
            }
        )
    return pd.DataFrame(rows)


def latency_comparison(df: pd.DataFrame) -> dict:
    m = df[df["mode"] == "M"]["latency_ms"]
    b2 = df[df["mode"] == "B2"]["latency_ms"]
    if len(m) < 3 or len(b2) < 3:
        return {"error": "insufficient samples"}
    stat, p = stats.mannwhitneyu(m, b2, alternative="less")
    return {
        "comparison": "M_latency_vs_B2",
        "M_mean_ms": float(m.mean()),
        "B2_mean_ms": float(b2.mean()),
        "speedup": float(b2.mean() / m.mean()) if m.mean() else 0,
        "mannwhitney_p": float(p),
        "significant_0.05": bool(p < 0.05),
    }


def sensitivity_analysis(df: pd.DataFrame) -> pd.DataFrame:
    if "temperature" not in df.columns:
        return pd.DataFrame()
    conf_col = "strict_formal_conformance" if "strict_formal_conformance" in df.columns else "formal_conformance"
    succ_col = "strict_formal_passed" if "strict_formal_passed" in df.columns else "success"
    return (
        df.groupby(["mode", "temperature"])
        .agg(success_rate=(succ_col, "mean"), formal=(conf_col, "mean"))
        .reset_index()
    )


def plot_figures(df: pd.DataFrame, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    agg = aggregate_by_mode(df)
    plt.figure(figsize=(10, 5))
    sns.barplot(data=agg, x="mode", y="success_rate", hue="mode", legend=False, palette="viridis")
    plt.title("Success Rate by Method")
    plt.ylim(0, 1.05)
    plt.ylabel("Success Rate")
    plt.tight_layout()
    plt.savefig(out_dir / "success_rate_by_mode.png", dpi=150)
    plt.close()

    plt.figure(figsize=(10, 5))
    sns.barplot(data=agg, x="mode", y="mutation_kill_rate", hue="mode", legend=False, palette="magma")
    plt.title("Mutation Kill Rate by Method")
    plt.ylim(0, 1.05)
    plt.tight_layout()
    plt.savefig(out_dir / "mutation_kill_rate.png", dpi=150)
    plt.close()

    plt.figure(figsize=(10, 5))
    sns.barplot(data=agg, x="mode", y="latency_ms", hue="mode", legend=False, palette="crest")
    plt.title("Mean Latency by Method (ms)")
    plt.tight_layout()
    plt.savefig(out_dir / "latency_by_mode.png", dpi=150)
    plt.close()

    if "temperature" in df.columns and df["temperature"].nunique() > 1:
        sens = sensitivity_analysis(df)
        plt.figure(figsize=(10, 5))
        sns.lineplot(data=sens, x="temperature", y="success_rate", hue="mode", marker="o")
        plt.title("Sensitivity: Temperature vs Success Rate")
        plt.tight_layout()
        plt.savefig(out_dir / "sensitivity_temperature.png", dpi=150)
        plt.close()


def analyze(run_dir: Path) -> Path:
    df = load_results(run_dir)
    if "strict_formal_passed" in df.columns:
        df["strict_success"] = df["strict_formal_passed"].astype(int)
    else:
        df["strict_success"] = df["success"].astype(int)
    report_dir = run_dir / "analysis"
    report_dir.mkdir(parents=True, exist_ok=True)

    summary = aggregate_by_mode(df)
    summary.to_csv(report_dir / "summary_by_mode.csv", index=False)

    tests = {
        "M_vs_B1": pairwise_tests(df, "B1", "M", metric="strict_success"),
        "M_vs_B2": pairwise_tests(df, "B2", "M", metric="strict_success"),
        "B2_vs_B1": pairwise_tests(df, "B1", "B2", metric="strict_success"),
        "latency_M_vs_B2": latency_comparison(df),
    }
    (report_dir / "significance_tests.json").write_text(
        json.dumps(tests, indent=2), encoding="utf-8"
    )

    ablation = ablation_analysis(df)
    if not ablation.empty:
        ablation.to_csv(report_dir / "ablation.csv", index=False)

    sens = sensitivity_analysis(df)
    if not sens.empty:
        sens.to_csv(report_dir / "sensitivity.csv", index=False)

    plot_figures(df, report_dir)

    report_md = [
        "# Experiment Analysis Report",
        "",
        "## Summary by Mode",
        summary.to_markdown(index=False),
        "",
        "## Significance Tests",
        "```json",
        json.dumps(tests, indent=2),
        "```",
    ]
    if not ablation.empty:
        report_md.extend(["", "## Ablation", ablation.to_markdown(index=False)])
    (report_dir / "REPORT.md").write_text("\n".join(report_md), encoding="utf-8")
    return report_dir


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path, help="Experiment run directory")
    args = parser.parse_args()
    report = analyze(args.run_dir)
    print(f"Analysis written to {report}")


if __name__ == "__main__":
    main()
