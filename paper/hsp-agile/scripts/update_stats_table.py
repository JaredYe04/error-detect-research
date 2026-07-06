"""Update LaTeX stats table from analysis/significance JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PAPER_ROOT = Path(__file__).resolve().parents[1]
TABLE_PATH = PAPER_ROOT / "tables" / "stats_summary.tex"


def _latest_analysis_json() -> Path:
    runs = sorted((ROOT / "artifacts").glob("run_*"))
    for run in reversed(runs):
        p = run / "analysis" / "significance_tests.json"
        if p.exists():
            return p
    raise FileNotFoundError("No significance_tests.json found under artifacts/run_*/analysis/")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=None,
        help="Explicit experiment run directory containing analysis/significance_tests.json.",
    )
    return parser.parse_args()


def _fmt_p(val: float | None) -> str:
    if val is None:
        return "TBD"
    if val < 1e-3:
        return "<0.001"
    return f"{val:.4f}"


def _sig_flag(v: bool | None) -> str:
    if v is None:
        return "TBD"
    return "Yes" if v else "No"


def main() -> None:
    args = _parse_args()
    sig_path = (
        (args.run_dir.resolve() / "analysis" / "significance_tests.json")
        if args.run_dir is not None
        else _latest_analysis_json()
    )
    if not sig_path.exists():
        raise FileNotFoundError(f"Missing significance file: {sig_path}")
    data = json.loads(sig_path.read_text(encoding="utf-8"))

    m_b1 = data.get("M_vs_B1", {})
    m_b2 = data.get("M_vs_B2", {})
    lat = data.get("latency_M_vs_B2", {})

    lines = [
        r"\begin{table}[t]",
        r"\caption{Statistical Test Summary (auto-filled from analysis artifacts)}",
        r"\label{tab:stats}",
        r"\centering",
        r"\begin{tabular}{lccc}",
        r"\toprule",
        r"Comparison & p-value & Significant (\(\alpha=0.05\)) & Effect/Speedup \\",
        r"\midrule",
        rf"\texttt{{M}} vs \texttt{{B1}} (strict) & {_fmt_p(m_b1.get('p_value'))} & {_sig_flag(m_b1.get('significant_0.05'))} & {m_b1.get('effect_size_rank_biserial', 'TBD'):.4f} \\"
        if isinstance(m_b1.get("effect_size_rank_biserial"), (int, float))
        else rf"\texttt{{M}} vs \texttt{{B1}} (strict) & {_fmt_p(m_b1.get('p_value'))} & {_sig_flag(m_b1.get('significant_0.05'))} & TBD \\",
        rf"\texttt{{M}} vs \texttt{{B2}} (strict) & {_fmt_p(m_b2.get('p_value'))} & {_sig_flag(m_b2.get('significant_0.05'))} & {m_b2.get('effect_size_rank_biserial', 'TBD'):.4f} \\"
        if isinstance(m_b2.get("effect_size_rank_biserial"), (int, float))
        else rf"\texttt{{M}} vs \texttt{{B2}} (strict) & {_fmt_p(m_b2.get('p_value'))} & {_sig_flag(m_b2.get('significant_0.05'))} & TBD \\",
        rf"\texttt{{M}} vs \texttt{{B2}} (latency) & {_fmt_p(lat.get('mannwhitney_p'))} & {_sig_flag(lat.get('significant_0.05'))} & {lat.get('speedup', 0):.2f}x \\"
        if isinstance(lat.get("speedup"), (int, float))
        else rf"\texttt{{M}} vs \texttt{{B2}} (latency) & {_fmt_p(lat.get('mannwhitney_p'))} & {_sig_flag(lat.get('significant_0.05'))} & TBD \\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ]
    TABLE_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Updated table from {sig_path}")


if __name__ == "__main__":
    main()
