"""Prepare paper-ready datasets from experiment artifacts."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
PAPER_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PAPER_ROOT / "data" / "raw"
PROC_DIR = PAPER_ROOT / "data" / "processed"
DEFAULT_RUN = ROOT / "artifacts" / "run_hard_full_parallel_v1"
DEFAULT_PREVENTION = ROOT / "artifacts" / "prevention_eval" / "prevention_full_v1" / "prevention_summary.json"


def _latest_run_dir() -> Path:
    runs = sorted(
        p
        for p in (ROOT / "artifacts").glob("run_*")
        if p.is_dir() and (p / "results.jsonl").exists()
    )
    if not runs:
        raise FileNotFoundError("No run_* directories with results.jsonl found in artifacts/")
    return runs[-1]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=DEFAULT_RUN,
        help="Experiment run directory (default: artifacts/run_hard_full_parallel_v1).",
    )
    parser.add_argument(
        "--prevention-summary",
        type=Path,
        default=DEFAULT_PREVENTION,
        help="Prevention summary JSON (default: prevention_full_v1/prevention_summary.json).",
    )
    parser.add_argument(
        "--extended-run-dir",
        type=Path,
        default=None,
        help="Optional run directory whose results are merged (e.g. B3--B5 extended baselines).",
    )
    parser.add_argument(
        "--extended-repeat",
        type=int,
        default=0,
        help="Repeat index to merge from --extended-run-dir (default 0, matches E1 single-repeat).",
    )
    parser.add_argument(
        "--e10-run-dir",
        type=Path,
        default=None,
        help="E10 random-benchmark run directory → e10_random_summary.csv",
    )
    parser.add_argument(
        "--e11-run-dir",
        type=Path,
        default=None,
        help="E11 external SOFL run directory → e11_external_summary.csv",
    )
    parser.add_argument(
        "--b6-run-dir",
        type=Path,
        default=None,
        help="B6 VerifierLoop-FSF full run → b6_verifierloop_summary.csv",
    )
    parser.add_argument(
        "--b6-stratified-run-dir",
        type=Path,
        default=None,
        help="B6/B2/M stratified run → b6_stratified_summary.csv",
    )
    return parser.parse_args()


def _win_rate_m_vs_b2(df: pd.DataFrame, conf_col: str) -> dict[str, float | int]:
    e1 = df[df["repeat"] == 0] if "repeat" in df.columns else df
    e1 = e1[e1["mode"].isin(["M", "B2"])]
    m = e1[e1["mode"] == "M"].set_index("task_id")[conf_col]
    b2 = e1[e1["mode"] == "B2"].set_index("task_id")[conf_col]
    common = m.index.intersection(b2.index)
    wins = int((m.loc[common] > b2.loc[common]).sum())
    n = len(common)
    rate = wins / n if n else 0.0
    se = math.sqrt(rate * (1 - rate) / n) if n else 0.0
    return {
        "wins": wins,
        "n": n,
        "win_rate": rate,
        "ci_low": max(0.0, rate - 1.96 * se),
        "ci_high": min(1.0, rate + 1.96 * se),
    }


def main() -> None:
    args = _parse_args()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROC_DIR.mkdir(parents=True, exist_ok=True)

    run_dir = args.run_dir.resolve()
    results_path = run_dir / "results.jsonl"
    if not results_path.exists():
        raise FileNotFoundError(f"Missing {results_path}")

    rows = [json.loads(line) for line in results_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.extended_run_dir is not None:
        ext_path = args.extended_run_dir.resolve() / "results.jsonl"
        if not ext_path.exists():
            raise FileNotFoundError(f"Missing {ext_path}")
        ext_rows = [
            json.loads(line)
            for line in ext_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        ext_rows = [r for r in ext_rows if int(r.get("repeat", 0)) == args.extended_repeat]
        rows.extend(ext_rows)
    df = pd.DataFrame(rows)
    df.to_csv(RAW_DIR / "results_raw.csv", index=False)

    success_col = "strict_formal_passed" if "strict_formal_passed" in df.columns else "success"
    conf_col = "strict_formal_conformance" if "strict_formal_conformance" in df.columns else "formal_conformance"

    summary = (
        df.groupby("mode")
        .agg(
            n=(success_col, "count"),
            success_rate=(success_col, "mean"),
            strict_conformance=(conf_col, "mean"),
            mutation_kill_rate=("mutation_kill_rate", "mean"),
            latency_ms=("latency_ms", "mean"),
            strict_failures=("strict_failures", "mean") if "strict_failures" in df.columns else (success_col, "sum"),
        )
        .reset_index()
    )
    summary.to_csv(PROC_DIR / "summary_by_mode.csv", index=False)

    distribution_cols = ["mode", "latency_ms", conf_col]
    distributions = (
        df[distribution_cols]
        .rename(columns={conf_col: "strict_conformance"})
        .dropna(subset=["mode", "latency_ms", "strict_conformance"])
        .reset_index(drop=True)
    )
    distributions.to_csv(PROC_DIR / "distribution_by_mode.csv", index=False)

    ablation_rows: list[dict[str, float | str | int]] = []
    if "M" in set(summary["mode"]):
        m_row = summary.loc[summary["mode"] == "M"].iloc[0]
        p_m = float(m_row["success_rate"])
        n_m = int(m_row["n"])
        for mode in ["A1", "A2", "A3"]:
            mode_rows = summary.loc[summary["mode"] == mode]
            if mode_rows.empty:
                continue
            row = mode_rows.iloc[0]
            p_mode = float(row["success_rate"])
            n_mode = int(row["n"])
            delta = p_mode - p_m
            se = math.sqrt(
                (p_mode * (1.0 - p_mode) / n_mode if n_mode > 0 else 0.0)
                + (p_m * (1.0 - p_m) / n_m if n_m > 0 else 0.0)
            )
            ci_half_width = 1.96 * se
            ablation_rows.append(
                {
                    "mode": mode,
                    "n": n_mode,
                    "success_rate": p_mode,
                    "baseline_mode": "M",
                    "baseline_n": n_m,
                    "baseline_success_rate": p_m,
                    "delta_vs_baseline": delta,
                    "ci_low": max(-1.0, delta - ci_half_width),
                    "ci_high": min(1.0, delta + ci_half_width),
                    "ci_method": "normal_approx_diff_proportions_95",
                }
            )
    pd.DataFrame(
        ablation_rows,
        columns=[
            "mode",
            "n",
            "success_rate",
            "baseline_mode",
            "baseline_n",
            "baseline_success_rate",
            "delta_vs_baseline",
            "ci_low",
            "ci_high",
            "ci_method",
        ],
    ).to_csv(PROC_DIR / "ablation_contribution.csv", index=False)

    pareto = summary.copy()
    pareto["quality"] = pareto["strict_conformance"]
    pareto["latency_ms"] = pareto["latency_ms"]
    pareto["n"] = pareto["n"].astype(int)
    pareto = pareto[["mode", "n", "quality", "latency_ms", "success_rate", "strict_failures"]]
    pareto.to_csv(PROC_DIR / "pareto_by_mode.csv", index=False)

    analysis_dir = run_dir / "analysis"
    if analysis_dir.exists():
        skip_summary = args.extended_run_dir is not None
        for fname in ["ablation.csv", "sensitivity.csv", "significance_tests.json", "summary_by_mode.csv"]:
            if skip_summary and fname == "summary_by_mode.csv":
                continue
            p = analysis_dir / fname
            if p.exists():
                target = PROC_DIR / fname
                target.write_bytes(p.read_bytes())

    prevention = (
        args.prevention_summary.resolve()
        if args.prevention_summary is not None
        else ROOT / "artifacts" / "prevention_eval" / "prevention_summary.json"
    )
    prevention_rows: list[dict[str, float | str | int]] = []
    if prevention.exists():
        prevention_data = json.loads(prevention.read_text(encoding="utf-8"))
        (PROC_DIR / "prevention_summary.json").write_text(
            json.dumps(prevention_data, indent=2), encoding="utf-8"
        )

        by_eval = prevention_data.get("by_eval_type", {})
        for mode, eval_group in by_eval.items():
            for eval_type, metrics in eval_group.items():
                prevention_rows.append(
                    {
                        "mode": mode,
                        "eval_type": eval_type,
                        "detection_rate": metrics.get("detection_rate", 0.0),
                        "false_accept_rate": metrics.get("false_accept_rate", 0.0),
                        "strict_conformance": metrics.get("strict_conformance", 0.0),
                        "n": metrics.get("n", 0),
                    }
                )
    pd.DataFrame(
            prevention_rows,
            columns=["mode", "eval_type", "detection_rate", "false_accept_rate", "strict_conformance", "n"],
        ).to_csv(PROC_DIR / "prevention_by_eval.csv", index=False)
    prevention_heatmap = pd.DataFrame(
        prevention_rows,
        columns=["mode", "eval_type", "detection_rate", "false_accept_rate", "strict_conformance", "n"],
    )
    prevention_heatmap.to_csv(PROC_DIR / "prevention_heatmap.csv", index=False)

    win_rate = _win_rate_m_vs_b2(df, conf_col)
    (PROC_DIR / "win_rate_m_vs_b2.json").write_text(json.dumps(win_rate, indent=2), encoding="utf-8")

    if args.e10_run_dir is not None:
        e10_path = args.e10_run_dir.resolve() / "results.jsonl"
        if e10_path.exists():
            e10_rows = [
                json.loads(line) for line in e10_path.read_text(encoding="utf-8").splitlines() if line.strip()
            ]
            e10_df = pd.DataFrame(e10_rows)
            e10_summary = (
                e10_df.groupby("mode")
                .agg(
                    n=(success_col, "count"),
                    success_rate=(success_col, "mean"),
                    strict_conformance=(conf_col, "mean"),
                    latency_ms=("latency_ms", "mean"),
                )
                .reset_index()
            )
            e10_summary.to_csv(PROC_DIR / "e10_random_summary.csv", index=False)

    if args.e11_run_dir is not None:
        e11_path = args.e11_run_dir.resolve() / "results.jsonl"
        if e11_path.exists():
            e11_rows = [
                json.loads(line) for line in e11_path.read_text(encoding="utf-8").splitlines() if line.strip()
            ]
            e11_df = pd.DataFrame(e11_rows)
            if "repeat" in e11_df.columns:
                e11_df = e11_df[e11_df["repeat"] == 0]
            e11_summary = (
                e11_df.groupby("mode")
                .agg(
                    n=(success_col, "count"),
                    success_rate=(success_col, "mean"),
                    strict_conformance=(conf_col, "mean"),
                    latency_ms=("latency_ms", "mean"),
                )
                .reset_index()
            )
            e11_summary.to_csv(PROC_DIR / "e11_external_summary.csv", index=False)

    if args.b6_run_dir is not None:
        b6_path = args.b6_run_dir.resolve() / "results.jsonl"
        if b6_path.exists():
            b6_rows = [
                json.loads(line) for line in b6_path.read_text(encoding="utf-8").splitlines() if line.strip()
            ]
            b6_df = pd.DataFrame(b6_rows)
            if "repeat" in b6_df.columns:
                b6_df = b6_df[b6_df["repeat"] == 0]
            b6_summary = (
                b6_df.groupby("mode")
                .agg(
                    n=(success_col, "count"),
                    success_rate=(success_col, "mean"),
                    strict_conformance=(conf_col, "mean"),
                    latency_ms=("latency_ms", "mean"),
                )
                .reset_index()
            )
            b6_summary.to_csv(PROC_DIR / "b6_verifierloop_summary.csv", index=False)

    if args.b6_stratified_run_dir is not None:
        strat_path = args.b6_stratified_run_dir.resolve() / "results.jsonl"
        if strat_path.exists():
            strat_rows = [
                json.loads(line) for line in strat_path.read_text(encoding="utf-8").splitlines() if line.strip()
            ]
            strat_df = pd.DataFrame(strat_rows)
            if "repeat" in strat_df.columns:
                strat_df = strat_df[strat_df["repeat"] == 0]
            strat_summary = (
                strat_df.groupby("mode")
                .agg(
                    n=(success_col, "count"),
                    success_rate=(success_col, "mean"),
                    strict_conformance=(conf_col, "mean"),
                    latency_ms=("latency_ms", "mean"),
                )
                .reset_index()
            )
            strat_summary.to_csv(PROC_DIR / "b6_stratified_summary.csv", index=False)

    print(f"Prepared paper data from {run_dir}")
    print(f"Raw dir: {RAW_DIR}")
    print(f"Processed dir: {PROC_DIR}")


if __name__ == "__main__":
    main()
