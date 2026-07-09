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


def _cliffs_delta(x: np.ndarray, y: np.ndarray) -> float:
    """Compute Cliff's delta (non-parametric effect size) between arrays x and y."""
    n_x, n_y = len(x), len(y)
    if n_x == 0 or n_y == 0:
        return 0.0
    concordant = sum(1 for xi in x for yi in y if xi > yi)
    discordant = sum(1 for xi in x for yi in y if xi < yi)
    return (concordant - discordant) / (n_x * n_y)


def _bootstrap_ci(
    x: np.ndarray,
    y: np.ndarray,
    *,
    n_boot: int = 1000,
    ci: float = 0.95,
    seed: int = 42,
) -> tuple[float, float]:
    """Bootstrap confidence interval for the mean difference (y - x)."""
    rng = np.random.default_rng(seed)
    diffs = []
    for _ in range(n_boot):
        xi = rng.choice(x, size=len(x), replace=True)
        yi = rng.choice(y, size=len(y), replace=True)
        diffs.append(float(np.mean(yi) - np.mean(xi)))
    alpha = 1 - ci
    lo = float(np.percentile(diffs, 100 * alpha / 2))
    hi = float(np.percentile(diffs, 100 * (1 - alpha / 2)))
    return lo, hi


def holm_bonferroni(p_values: list[float]) -> list[float]:
    """Apply Holm-Bonferroni correction to a list of p-values.

    Returns corrected p-values in the same order as the input.
    """
    n = len(p_values)
    if n == 0:
        return []
    indexed = sorted(enumerate(p_values), key=lambda t: t[1])
    adjusted = [0.0] * n
    prev_corrected = 0.0
    for rank, (orig_idx, p) in enumerate(indexed):
        corrected = min(1.0, max(prev_corrected, p * (n - rank)))
        adjusted[orig_idx] = corrected
        prev_corrected = corrected
    return adjusted


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
            "cliffs_delta": 0.0,
            "bootstrap_ci_95": [0.0, 0.0],
            "significant_0.05": False,
            "note": "all_differences_zero",
        }
    try:
        stat, p = stats.wilcoxon(t, b, alternative="greater")
    except ValueError:
        stat, p = float("nan"), 1.0
    # Cliff's delta: positive when method > baseline
    cd = _cliffs_delta(t, b)
    # Bootstrap 95% CI on mean difference
    lo, hi = _bootstrap_ci(b, t, n_boot=1000, ci=0.95)
    # rank-biserial correlation (legacy)
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
        "wilcoxon_stat": float(stat) if not np.isnan(stat) else None,
        "p_value": float(p),
        "cliffs_delta": float(cd),
        "effect_size_rank_biserial": float(rbc),
        "bootstrap_ci_95": [lo, hi],
        "significant_0.05": bool(p < 0.05),
    }


def all_pairwise_tests_with_holm(
    df: pd.DataFrame,
    modes: list[str] | None = None,
    metric: str = "success",
) -> dict:
    """Run all pairwise comparisons and apply Holm-Bonferroni correction."""
    modes = modes or ["B1", "B2", "M", "A1", "A2", "A3"]
    modes = [m for m in modes if m in df["mode"].unique()]
    pairs = [(a, b) for i, a in enumerate(modes) for b in modes[i + 1:]]

    raw_results = {}
    p_values = []
    pair_keys = []
    for baseline, method in pairs:
        key = f"{method}_vs_{baseline}"
        r = pairwise_tests(df, baseline, method, metric)
        raw_results[key] = r
        p_values.append(r.get("p_value", 1.0))
        pair_keys.append(key)

    corrected = holm_bonferroni(p_values)
    for key, adj_p in zip(pair_keys, corrected):
        raw_results[key]["p_value_holm"] = adj_p
        raw_results[key]["significant_holm_0.05"] = adj_p < 0.05

    return raw_results


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


def latency_comparison(df: pd.DataFrame, baseline: str = "B2", method: str = "M") -> dict:
    m = df[df["mode"] == method]["latency_ms"]
    b = df[df["mode"] == baseline]["latency_ms"]
    if len(m) < 3 or len(b) < 3:
        return {"error": "insufficient samples"}
    stat, p = stats.mannwhitneyu(m, b, alternative="greater")
    return {
        "comparison": f"{method}_latency_vs_{baseline}",
        "baseline": baseline,
        "method": method,
        f"{method}_mean_ms": float(m.mean()),
        f"{baseline}_mean_ms": float(b.mean()),
        "latency_ratio": float(m.mean() / b.mean()) if b.mean() else 0,
        "mannwhitney_p": float(p),
        "cliffs_delta": float(_cliffs_delta(m.values, b.values)),
        "significant_0.05": bool(p < 0.05),
    }


def all_pairwise_latency_with_holm(
    df: pd.DataFrame,
    modes: list[str] | None = None,
) -> dict:
    """Mann-Whitney U for latency across all mode pairs (separate Holm family)."""
    modes = modes or ["B0", "B1", "B2", "M", "A1", "A2", "A3"]
    modes = [m for m in modes if m in df["mode"].unique()]
    pairs = [(a, b) for i, a in enumerate(modes) for b in modes[i + 1:]]

    raw_results: dict = {}
    p_values: list[float] = []
    pair_keys: list[str] = []
    for baseline, method in pairs:
        key = f"{method}_vs_{baseline}"
        m_lat = df[df["mode"] == method]["latency_ms"].values
        b_lat = df[df["mode"] == baseline]["latency_ms"].values
        if len(m_lat) < 3 or len(b_lat) < 3:
            continue
        try:
            _, p = stats.mannwhitneyu(m_lat, b_lat, alternative="two-sided")
        except ValueError:
            p = 1.0
        raw_results[key] = {
            "baseline": baseline,
            "method": method,
            "metric": "latency_ms",
            "n_method": int(len(m_lat)),
            "n_baseline": int(len(b_lat)),
            "method_mean": float(np.mean(m_lat)),
            "baseline_mean": float(np.mean(b_lat)),
            "latency_ratio": float(np.mean(m_lat) / np.mean(b_lat)) if np.mean(b_lat) else 0,
            "mannwhitney_p": float(p),
            "cliffs_delta": float(_cliffs_delta(m_lat, b_lat)),
        }
        p_values.append(float(p))
        pair_keys.append(key)

    corrected = holm_bonferroni(p_values)
    for key, adj_p in zip(pair_keys, corrected):
        raw_results[key]["p_value_holm"] = adj_p
        raw_results[key]["significant_holm_0.05"] = adj_p < 0.05

    return raw_results


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


def compute_far_bound_validation(
    results_path: Path,
    prevention_path: Path | None = None,
    *,
    epsilon: float = 0.05,
    out_dir: Path | None = None,
) -> pd.DataFrame:
    """Compute empirical FAR vs. theoretical (1-ε)^n bound (C5 validation).

    For each mode, the theoretical bound is (1 - epsilon)^n_witnesses, where
    n_witnesses = average number of formal test cases (witnesses) exercised and
    epsilon = 0.05 (conservative per-witness fault-activation probability).

    Args:
        results_path: Path to results.jsonl (main E1 run or prevention run).
        prevention_path: Optional path to a separate prevention results.jsonl.
            If None, uses results_path for both empirical FAR and witness count.
        epsilon: Per-witness fault-activation probability (default 0.05).
        out_dir: Directory to write far_bound_validation.csv. Defaults to
            the parent of results_path / "analysis".

    Returns:
        DataFrame with columns: mode, empirical_far, theoretical_bound, n_witnesses.
    """
    rows_main = [
        json.loads(line)
        for line in results_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    df_main = pd.DataFrame(rows_main)

    if prevention_path is not None and prevention_path.exists():
        rows_prev = [
            json.loads(line)
            for line in prevention_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        df_prev = pd.DataFrame(rows_prev)
    else:
        df_prev = df_main.copy()

    records = []
    for mode in sorted(df_main["mode"].unique()):
        mode_main = df_main[df_main["mode"] == mode]
        mode_prev = df_prev[df_prev["mode"] == mode] if "mode" in df_prev.columns else df_prev

        # Empirical FAR: fraction of clean implementations that still have formal failures
        # (i.e., strict_formal_passed == False) — proxy for false-acceptance rate
        if "strict_formal_passed" in mode_prev.columns:
            passed_col = "strict_formal_passed"
        elif "formal_passed" in mode_prev.columns:
            passed_col = "formal_passed"
        else:
            passed_col = "success"
        empirical_far = float(1.0 - mode_prev[passed_col].mean()) if not mode_prev.empty else float("nan")

        # Average witness count: use strict_failures (= counterexample count at eval) as proxy
        # for how many witnesses the checker produced during strict evaluation
        if "strict_failures" in mode_main.columns:
            n_witnesses = float(mode_main["strict_failures"].mean())
        elif "counterexamples" in mode_main.columns:
            n_witnesses = float(
                mode_main["counterexamples"].apply(
                    lambda v: len(v) if isinstance(v, list) else 0
                ).mean()
            )
        else:
            n_witnesses = float("nan")

        # Theoretical FAR upper bound: (1 - ε)^n  (probability all n witnesses miss the fault)
        if not np.isnan(n_witnesses) and n_witnesses >= 0:
            theoretical_bound = float((1.0 - epsilon) ** n_witnesses)
        else:
            theoretical_bound = float("nan")

        records.append(
            {
                "mode": mode,
                "empirical_far": round(empirical_far, 4),
                "theoretical_bound": round(theoretical_bound, 4) if not np.isnan(theoretical_bound) else None,
                "n_witnesses": round(n_witnesses, 2) if not np.isnan(n_witnesses) else None,
                "epsilon": epsilon,
            }
        )

    result_df = pd.DataFrame(records)

    save_dir = out_dir or (results_path.parent / "analysis")
    save_dir.mkdir(parents=True, exist_ok=True)
    csv_path = save_dir / "far_bound_validation.csv"
    result_df.to_csv(csv_path, index=False)
    print(f"[FAR] Bound validation written to {csv_path}")
    return result_df


def analyze(run_dir: Path) -> Path:
    df = load_results(run_dir)
    if "strict_formal_passed" in df.columns:
        df["strict_success"] = df["strict_formal_passed"].astype(int)
    else:
        df["strict_success"] = df["success"].astype(int)
    conf_col = (
        "strict_formal_conformance"
        if "strict_formal_conformance" in df.columns
        else "formal_conformance"
    )
    report_dir = run_dir / "analysis"
    report_dir.mkdir(parents=True, exist_ok=True)

    summary = aggregate_by_mode(df)
    summary.to_csv(report_dir / "summary_by_mode.csv", index=False)

    # Upgraded stats: all pairwise with Holm correction + Cliff's delta + bootstrap CI
    e1_modes = [m for m in ["B0", "B1", "B2", "M", "A1", "A2", "A3"] if m in df["mode"].unique()]
    pairwise_strict = all_pairwise_tests_with_holm(df, modes=e1_modes, metric="strict_success")
    pairwise_conf = all_pairwise_tests_with_holm(df, modes=e1_modes, metric=conf_col)
    pairwise_latency = all_pairwise_latency_with_holm(df, modes=e1_modes)
    lat_m_b2 = latency_comparison(df)
    tests = {
        "pairwise_strict_success_holm": pairwise_strict,
        "pairwise_conformance_holm": pairwise_conf,
        "pairwise_latency_holm": pairwise_latency,
        "latency_M_vs_B2": lat_m_b2,
        # Keep primary comparisons at top level for backward compatibility
        "M_vs_B1": pairwise_tests(df, "B1", "M", metric="strict_success"),
        "M_vs_B2": pairwise_tests(df, "B2", "M", metric="strict_success"),
        "M_vs_B1_conf": pairwise_tests(df, "B1", "M", metric=conf_col),
        "M_vs_B2_conf": pairwise_tests(df, "B2", "M", metric=conf_col),
    }
    for key, holm_key in [("M_vs_B1", "M_vs_B1"), ("M_vs_B2", "M_vs_B2")]:
        if holm_key in pairwise_strict:
            tests[key]["p_value_holm"] = pairwise_strict[holm_key]["p_value_holm"]
            tests[key]["significant_holm_0.05"] = pairwise_strict[holm_key]["significant_holm_0.05"]
    for key, holm_key in [("M_vs_B1_conf", "M_vs_B1"), ("M_vs_B2_conf", "M_vs_B2")]:
        if holm_key in pairwise_conf:
            tests[key]["p_value_holm"] = pairwise_conf[holm_key]["p_value_holm"]
            tests[key]["significant_holm_0.05"] = pairwise_conf[holm_key]["significant_holm_0.05"]
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
