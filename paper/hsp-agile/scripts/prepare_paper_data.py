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
        default=None,
        help="Explicit experiment run directory (defaults to latest artifacts/run_* with results.jsonl).",
    )
    parser.add_argument(
        "--prevention-summary",
        type=Path,
        default=None,
        help="Explicit prevention_summary.json path (defaults to artifacts/prevention_eval/prevention_summary.json).",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROC_DIR.mkdir(parents=True, exist_ok=True)

    run_dir = args.run_dir.resolve() if args.run_dir is not None else _latest_run_dir()
    results_path = run_dir / "results.jsonl"
    if not results_path.exists():
        raise FileNotFoundError(f"Missing {results_path}")

    rows = [json.loads(line) for line in results_path.read_text(encoding="utf-8").splitlines() if line.strip()]
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
        for fname in ["ablation.csv", "sensitivity.csv", "significance_tests.json", "summary_by_mode.csv"]:
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

    print(f"Prepared paper data from {run_dir}")
    print(f"Raw dir: {RAW_DIR}")
    print(f"Processed dir: {PROC_DIR}")


if __name__ == "__main__":
    main()
