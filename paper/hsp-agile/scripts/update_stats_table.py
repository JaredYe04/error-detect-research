"""Generate LaTeX stats table from paper results_raw.csv."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
PAPER_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from experiments.analyze import (  # noqa: E402
    all_pairwise_latency_with_holm,
    all_pairwise_tests_with_holm,
    latency_comparison,
    pairwise_tests,
)

CSV_PATH = PAPER_ROOT / "data" / "raw" / "results_raw.csv"
TABLE_PATH = PAPER_ROOT / "tables" / "stats_summary.tex"
SIG_JSON_PATH = PAPER_ROOT / "data" / "processed" / "significance_tests.json"
E1_MODES = ["B0", "B1", "B2", "M", "A1", "A2", "A3"]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--csv",
        type=Path,
        default=CSV_PATH,
        help="Path to results_raw.csv (default: paper data/raw/results_raw.csv).",
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=None,
        help="Optional experiment run dir; if set, also reads analysis/significance_tests.json "
        "instead of recomputing (legacy). Omit to compute from CSV.",
    )
    return parser.parse_args()


def _load_e1_frame(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    if "repeat" in df.columns:
        df = df[df["repeat"] == 0]
    df = df[df["mode"].isin(E1_MODES)].copy()
    success_col = "strict_formal_passed" if "strict_formal_passed" in df.columns else "success"
    df["strict_success"] = df[success_col].astype(int)
    return df


def _conf_col(df: pd.DataFrame) -> str:
    if "strict_formal_conformance" in df.columns:
        return "strict_formal_conformance"
    return "formal_conformance"


def _fmt_p(val: float | None, *, holm: bool = False) -> str:
    if val is None:
        return "TBD"
    if val < 1e-3:
        return "<0.001" if not holm else "$<$0.001"
    return f"{val:.4f}"


def _sig_flag(v: bool | None) -> str:
    if v is None:
        return "TBD"
    return "Yes" if v else "No"


def _fmt_delta(val: float | None) -> str:
    if val is None:
        return "TBD"
    return f"{val:+.4f}"


def _pair_label(method: str, baseline: str) -> str:
    return rf"\texttt{{{method}}} vs \texttt{{{baseline}}}"


def compute_significance(df: pd.DataFrame) -> dict:
    conf = _conf_col(df)
    modes = [m for m in E1_MODES if m in df["mode"].unique()]
    pairwise_strict = all_pairwise_tests_with_holm(df, modes=modes, metric="strict_success")
    pairwise_conf = all_pairwise_tests_with_holm(df, modes=modes, metric=conf)
    pairwise_latency = all_pairwise_latency_with_holm(df, modes=modes)
    lat_m_b2 = latency_comparison(df)

    tests: dict = {
        "pairwise_strict_success_holm": pairwise_strict,
        "pairwise_conformance_holm": pairwise_conf,
        "pairwise_latency_holm": pairwise_latency,
        "latency_M_vs_B2": lat_m_b2,
        "M_vs_B1": pairwise_tests(df, "B1", "M", metric="strict_success"),
        "M_vs_B2": pairwise_tests(df, "B2", "M", metric="strict_success"),
        "M_vs_B1_conf": pairwise_tests(df, "B1", "M", metric=conf),
        "M_vs_B2_conf": pairwise_tests(df, "B2", "M", metric=conf),
    }
    for key, holm_key in [("M_vs_B1", "M_vs_B1"), ("M_vs_B2", "M_vs_B2")]:
        if holm_key in pairwise_strict:
            tests[key]["p_value_holm"] = pairwise_strict[holm_key]["p_value_holm"]
            tests[key]["significant_holm_0.05"] = pairwise_strict[holm_key]["significant_holm_0.05"]
    for key, holm_key in [("M_vs_B1_conf", "M_vs_B1"), ("M_vs_B2_conf", "M_vs_B2")]:
        if holm_key in pairwise_conf:
            tests[key]["p_value_holm"] = pairwise_conf[holm_key]["p_value_holm"]
            tests[key]["significant_holm_0.05"] = pairwise_conf[holm_key]["significant_holm_0.05"]
    return tests


def _headline_rows(data: dict) -> list[str]:
    rows: list[str] = []
    lat = data["latency_M_vs_B2"]
    headline = [
        ("M_vs_B1", "strict success", data["M_vs_B1"], None),
        ("M_vs_B2", "strict success", data["M_vs_B2"], None),
        ("M_vs_B1_conf", "conformance", data["M_vs_B1_conf"], None),
        ("M_vs_B2_conf", "conformance", data["M_vs_B2_conf"], None),
    ]
    for _key, metric_label, r, extra in headline:
        rows.append(
            rf"{_pair_label(r['method'], r['baseline'])} ({metric_label}) "
            rf"& {_fmt_p(r.get('p_value_holm', r.get('p_value')))} "
            rf"& {_sig_flag(r.get('significant_holm_0.05', r.get('significant_0.05')))} "
            rf"& {_fmt_delta(r.get('cliffs_delta'))} \\"
        )
    ratio = lat.get("latency_ratio")
    ratio_str = f"{ratio:.2f}$\\times$" if isinstance(ratio, (int, float)) else "TBD"
    rows.append(
        rf"\texttt{{M}} vs \texttt{{B2}} (latency) "
        rf"& {_fmt_p(lat.get('mannwhitney_p'))} "
        rf"& {_sig_flag(lat.get('significant_0.05'))} "
        rf"& {ratio_str} \\"
    )
    return rows


def _pairwise_block(
    pairwise: dict,
    *,
    metric_label: str,
    p_key: str = "p_value_holm",
    sig_key: str = "significant_holm_0.05",
) -> list[str]:
    rows: list[str] = []
    for key in sorted(pairwise):
        r = pairwise[key]
        rows.append(
            rf"{_pair_label(r['method'], r['baseline'])} ({metric_label}) "
            rf"& {_fmt_p(r.get(p_key))} "
            rf"& {_sig_flag(r.get(sig_key))} "
            rf"& {_fmt_delta(r.get('cliffs_delta'))} \\"
        )
    return rows


def render_table(data: dict) -> str:
    lines = [
        r"\begin{table}[t]",
        r"\caption{Statistical test summary for E1 (120-task hard benchmark, repeat~0). "
        r"Wilcoxon signed-rank for per-task strict success and conformance; "
        r"Mann--Whitney~U for latency. Holm--Bonferroni correction within each metric family. "
        r"Cliff's $\delta$: positive favours the first mode in each pair.}",
        r"\label{tab:stats}",
        r"\centering",
        r"\small",
        r"\begin{tabular}{lccc}",
        r"\toprule",
        r"Comparison & $p$ (Holm) & Significant ($\alpha{=}0.05$) & Cliff's $\delta$ / ratio \\",
        r"\midrule",
        r"\multicolumn{4}{l}{\textit{Primary comparisons}} \\",
        r"\addlinespace",
    ]
    lines.extend(_headline_rows(data))
    lines.extend(
        [
            r"\addlinespace",
            r"\multicolumn{4}{l}{\textit{All pairwise conformance (Holm-corrected)}} \\",
            r"\addlinespace",
        ]
    )
    lines.extend(_pairwise_block(data["pairwise_conformance_holm"], metric_label="Conf"))
    lines.extend(
        [
            r"\addlinespace",
            r"\multicolumn{4}{l}{\textit{All pairwise strict success (Holm-corrected)}} \\",
            r"\addlinespace",
        ]
    )
    lines.extend(_pairwise_block(data["pairwise_strict_success_holm"], metric_label="strict"))
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    return "\n".join(lines) + "\n"


def main() -> None:
    args = _parse_args()
    if args.run_dir is not None:
        sig_path = args.run_dir.resolve() / "analysis" / "significance_tests.json"
        if not sig_path.exists():
            raise FileNotFoundError(f"Missing significance file: {sig_path}")
        data = json.loads(sig_path.read_text(encoding="utf-8"))
        print(f"Loaded legacy JSON from {sig_path}")
    else:
        csv_path = args.csv.resolve()
        if not csv_path.exists():
            raise FileNotFoundError(f"Missing results CSV: {csv_path}")
        df = _load_e1_frame(csv_path)
        data = compute_significance(df)
        SIG_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
        SIG_JSON_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"Computed significance from {csv_path} ({len(df)} rows)")

    TABLE_PATH.write_text(render_table(data), encoding="utf-8")
    print(f"Updated {TABLE_PATH}")


if __name__ == "__main__":
    main()
