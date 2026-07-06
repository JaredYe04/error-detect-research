"""
Publication-quality matplotlib figure generator for HSP-Agile paper.
Reads processed CSVs and writes PDF + PNG figures to paper/hsp-agile/figures/.
No Plotly/Kaleido dependency — 100% matplotlib + seaborn.
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

PAPER_ROOT = Path(__file__).resolve().parents[2]
PROC_DIR = PAPER_ROOT / "data" / "processed"
FIG_DIR = PAPER_ROOT / "figures"

# Colorblind-safe palette (Paul Tol's "muted")
MODE_ORDER = ["B0", "B1", "B2", "M", "A1", "A2", "A3"]
PALETTE = {
    "B0": "#CC6677",
    "B1": "#332288",
    "B2": "#88CCEE",
    "M":  "#117733",
    "A1": "#DDCC77",
    "A2": "#AA4499",
    "A3": "#44AA99",
}
HATCH = {"B0": "//", "B1": None, "B2": "\\\\", "M": None, "A1": "..", "A2": "xx", "A3": "oo"}

FONT_TITLE = 10
FONT_LABEL = 9
FONT_TICK  = 8
FONT_ANNOT = 7.5

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": FONT_LABEL,
    "axes.titlesize": FONT_TITLE,
    "axes.labelsize": FONT_LABEL,
    "xtick.labelsize": FONT_TICK,
    "ytick.labelsize": FONT_TICK,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linewidth": 0.5,
    "legend.fontsize": FONT_ANNOT,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.04,
    "pdf.fonttype": 42,   # embed fonts in PDF
    "ps.fonttype": 42,
})


def _save(fig: plt.Figure, stem: str, formats: list[str], dpi: int) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    for fmt in formats:
        out = FIG_DIR / f"{stem}.{fmt}"
        if fmt == "pdf":
            with PdfPages(str(out)) as pdf:
                pdf.savefig(fig, dpi=dpi, bbox_inches="tight")
        else:
            fig.savefig(str(out), dpi=dpi, format=fmt, bbox_inches="tight")
    print(f"  saved: {stem} ({', '.join(formats)})")


def _ordered_modes(modes: pd.Series | list) -> list[str]:
    present = set(modes)
    return [m for m in MODE_ORDER if m in present]


# ─────────────────────────────────────────────────────────────────────────────
# Figure 1: strict conformance distribution (box + strip) by mode
# ─────────────────────────────────────────────────────────────────────────────
def plot_mode_distribution_conformance(formats: list[str], dpi: int) -> None:
    csv = PROC_DIR / "distribution_by_mode.csv"
    if not csv.exists():
        print("  [skip] distribution_by_mode.csv not found")
        return

    df = pd.read_csv(csv)
    if "strict_conformance" not in df.columns or df.empty:
        print("  [skip] strict_conformance column missing")
        return

    modes = _ordered_modes(df["mode"])
    groups = [df[df["mode"] == m]["strict_conformance"].dropna().values for m in modes]
    counts = [len(g) for g in groups]

    fig, ax = plt.subplots(figsize=(6.5, 3.2))
    positions = np.arange(len(modes))

    vp = ax.violinplot(groups, positions=positions, showmedians=True,
                       showextrema=True, widths=0.7)
    for i, (body, mode) in enumerate(zip(vp["bodies"], modes)):
        body.set_facecolor(PALETTE.get(mode, "#888888"))
        body.set_edgecolor("white")
        body.set_alpha(0.78)
    for part in ["cmedians", "cmins", "cmaxes", "cbars"]:
        vp[part].set_linewidth(1.2)
        vp[part].set_color("#333333")

    # Overlay box
    bp = ax.boxplot(groups, positions=positions, widths=0.18, patch_artist=True,
                    medianprops={"color": "white", "linewidth": 1.5},
                    boxprops={"facecolor": "none", "edgecolor": "#333333", "linewidth": 0.8},
                    whiskerprops={"linewidth": 0.8},
                    capprops={"linewidth": 0.8},
                    flierprops={"marker": "o", "markersize": 2.5, "alpha": 0.4,
                                "markerfacecolor": "#888888", "markeredgewidth": 0},
                    showfliers=True)

    ax.set_xticks(positions)
    ax.set_xticklabels([f"{m}\n(n={c})" for m, c in zip(modes, counts)], fontsize=FONT_TICK)
    ax.set_ylim(-0.05, 1.10)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.set_xlabel("Mode")
    ax.set_ylabel("Strict Conformance")
    ax.set_title("Strict Conformance Distribution by Mode")
    ax.axhline(1.0, ls="--", lw=0.7, color="#999999", label="Perfect conformance")
    ax.legend(framealpha=0.7, loc="lower right")
    fig.tight_layout()
    _save(fig, "mode_distribution_strict_conformance", formats, dpi)
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Figure 2: latency distribution (log-scale box+strip) by mode
# ─────────────────────────────────────────────────────────────────────────────
def plot_mode_distribution_latency(formats: list[str], dpi: int) -> None:
    csv = PROC_DIR / "distribution_by_mode.csv"
    if not csv.exists():
        return
    df = pd.read_csv(csv)
    if "latency_ms" not in df.columns or df.empty:
        return

    modes = _ordered_modes(df["mode"])
    groups = [np.clip(df[df["mode"] == m]["latency_ms"].dropna().values, 1e-3, None)
              for m in modes]
    counts = [len(g) for g in groups]

    fig, ax = plt.subplots(figsize=(6.5, 3.2))
    positions = np.arange(len(modes))

    bp = ax.boxplot(groups, positions=positions, patch_artist=True,
                    widths=0.55,
                    medianprops={"color": "white", "linewidth": 1.8},
                    boxprops={"linewidth": 0.8},
                    whiskerprops={"linewidth": 0.8},
                    capprops={"linewidth": 0.8},
                    flierprops={"marker": "o", "markersize": 2.5, "alpha": 0.35,
                                "markeredgewidth": 0},
                    showfliers=True)

    for patch, mode in zip(bp["boxes"], modes):
        patch.set_facecolor(PALETTE.get(mode, "#888888"))
        patch.set_alpha(0.82)

    # Jitter strip
    rng = np.random.default_rng(7)
    for i, (grp, mode) in enumerate(zip(groups, modes)):
        jitter = rng.uniform(-0.18, 0.18, size=len(grp))
        ax.scatter(positions[i] + jitter, grp, s=3.0, alpha=0.22,
                   color=PALETTE.get(mode, "#888888"), zorder=3)

    ax.set_xticks(positions)
    ax.set_xticklabels([f"{m}\n(n={c})" for m, c in zip(modes, counts)], fontsize=FONT_TICK)
    ax.set_yscale("log")
    ax.set_ylabel("Latency (ms, log scale)")
    ax.set_xlabel("Mode")
    ax.set_title("Latency Distribution by Mode (log scale)")
    fig.tight_layout()
    _save(fig, "mode_distribution_latency", formats, dpi)
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Figure 3: ablation contribution bar chart with 95% CI
# ─────────────────────────────────────────────────────────────────────────────
def plot_ablation_contribution(formats: list[str], dpi: int) -> None:
    csv = PROC_DIR / "ablation_contribution.csv"
    if not csv.exists():
        return
    df = pd.read_csv(csv)
    if df.empty:
        return

    modes = df["mode"].tolist()
    deltas = df["delta_vs_baseline"].values
    ci_lo = df["ci_low"].values
    ci_hi = df["ci_high"].values
    err_lo = deltas - ci_lo
    err_hi = ci_hi - deltas
    baseline_mode = df["baseline_mode"].iloc[0] if "baseline_mode" in df.columns else "M"

    fig, ax = plt.subplots(figsize=(4.5, 3.2))
    x = np.arange(len(modes))
    colors = [PALETTE.get(m, "#888888") for m in modes]

    bars = ax.bar(x, deltas, color=colors, alpha=0.85, width=0.55,
                  yerr=[err_lo, err_hi], error_kw={"elinewidth": 1.4, "capsize": 4,
                                                   "capthick": 1.2, "ecolor": "#333333"})
    ax.axhline(0, color="black", linewidth=0.9, linestyle="--")

    # Label bars
    for bar, d in zip(bars, deltas):
        va = "bottom" if d >= 0 else "top"
        offset = 0.005 if d >= 0 else -0.005
        ax.text(bar.get_x() + bar.get_width() / 2, d + offset,
                f"{d:+.1%}", ha="center", va=va, fontsize=FONT_ANNOT, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(modes, fontsize=FONT_TICK)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:+.0%}"))
    ax.set_xlabel("Ablation Mode")
    ax.set_ylabel(f"Δ Strict Success vs {baseline_mode}")
    ax.set_title(f"Ablation Contribution (95% CI, vs {baseline_mode})")
    ax.margins(y=0.20)

    # Legend patches
    patches = [mpatches.Patch(facecolor=PALETTE.get(m, "#888888"), alpha=0.85, label=m)
               for m in modes]
    ax.legend(handles=patches, fontsize=FONT_ANNOT, loc="upper right", framealpha=0.7)
    fig.tight_layout()
    _save(fig, "ablation_contribution_ci", formats, dpi)
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Figure 4: prevention heatmap (detection rate + false accept rate)
# ─────────────────────────────────────────────────────────────────────────────
def plot_prevention_heatmap(formats: list[str], dpi: int) -> None:
    csv = PROC_DIR / "prevention_heatmap.csv"
    if not csv.exists():
        return
    df = pd.read_csv(csv)
    if df.empty or "detection_rate" not in df.columns:
        # Create placeholder figure
        fig, ax = plt.subplots(figsize=(5.5, 2.5))
        ax.text(0.5, 0.5, "Prevention evaluation pending\n(run experiments/run_prevention.py)",
                ha="center", va="center", transform=ax.transAxes,
                fontsize=FONT_LABEL, color="gray", style="italic")
        ax.set_axis_off()
        ax.set_title("Prevention Heatmap (Placeholder)")
        _save(fig, "prevention_heatmap_by_mode_eval", formats, dpi)
        plt.close(fig)
        return

    modes = _ordered_modes(df["mode"])
    eval_types = sorted(df["eval_type"].unique())

    detection = (df.pivot(index="eval_type", columns="mode", values="detection_rate")
                   .reindex(index=eval_types, columns=modes).fillna(0.0))
    far = (df.pivot(index="eval_type", columns="mode", values="false_accept_rate")
             .reindex(index=eval_types, columns=modes).fillna(0.0))

    fig, axes = plt.subplots(1, 2, figsize=(9.0, 2.5 + 0.5 * len(eval_types)))
    for ax, mat, cmap, title, invert in [
        (axes[0], detection, "YlGn",   "Detection Rate (↑)",     False),
        (axes[1], far,       "YlOrRd", "False Accept Rate (↓)",  True),
    ]:
        vmin, vmax = (1.0, 0.0) if invert else (0.0, 1.0)
        im = ax.imshow(mat.values, aspect="auto", cmap=cmap,
                       vmin=min(vmin, vmax), vmax=max(vmin, vmax), interpolation="nearest")
        ax.set_xticks(range(len(modes)))
        ax.set_xticklabels(modes, fontsize=FONT_TICK)
        ax.set_yticks(range(len(eval_types)))
        ax.set_yticklabels(eval_types, fontsize=FONT_TICK)
        ax.set_title(title, fontsize=FONT_TITLE)
        ax.set_xlabel("Mode", fontsize=FONT_LABEL)
        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04, format="%.2f")
        # Annotate cells
        for i in range(len(eval_types)):
            for j in range(len(modes)):
                v = mat.values[i, j]
                ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                        fontsize=FONT_ANNOT, color="black" if v < 0.7 else "white")

    fig.suptitle("Prevention Heatmap by Mode × Eval Type", fontsize=FONT_TITLE, y=1.01)
    fig.tight_layout()
    _save(fig, "prevention_heatmap_by_mode_eval", formats, dpi)
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Figure 5: Pareto chart — quality vs latency
# ─────────────────────────────────────────────────────────────────────────────
def plot_pareto(formats: list[str], dpi: int) -> None:
    csv = PROC_DIR / "pareto_by_mode.csv"
    if not csv.exists():
        return
    df = pd.read_csv(csv)
    if df.empty:
        return

    modes = _ordered_modes(df["mode"])
    df_plot = df.set_index("mode").loc[[m for m in modes if m in df["mode"].values]]

    fig, ax = plt.subplots(figsize=(5.5, 4.0))

    # Scatter with size proportional to n
    n_max = df_plot["n"].max() if "n" in df_plot.columns else 1
    for mode in modes:
        if mode not in df_plot.index:
            continue
        row = df_plot.loc[mode]
        n = row.get("n", 120)
        size = 80 + 200 * (n / n_max)
        ax.scatter(row["latency_ms"], row["quality"],
                   s=size,
                   color=PALETTE.get(mode, "#888888"),
                   edgecolors="white", linewidths=0.8,
                   zorder=5, label=mode, alpha=0.9)
        ax.annotate(mode, (row["latency_ms"], row["quality"]),
                    textcoords="offset points", xytext=(6, 4),
                    fontsize=FONT_ANNOT, fontweight="bold")

    # Pareto frontier
    sorted_df = df_plot.sort_values("latency_ms")
    frontier_x, frontier_y = [], []
    best_q = -np.inf
    for _, row in sorted_df.iterrows():
        if row["quality"] >= best_q:
            frontier_x.append(row["latency_ms"])
            frontier_y.append(row["quality"])
            best_q = row["quality"]
    if len(frontier_x) > 1:
        ax.plot(frontier_x, frontier_y, ls="--", lw=1.4, color="#444444",
                marker="D", markersize=4.5, zorder=4, label="Pareto frontier")

    ax.set_xscale("log")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.set_xlabel("Latency (ms, log scale)")
    ax.set_ylabel("Strict Conformance")
    ax.set_title("Pareto: Quality vs Latency")
    ax.legend(fontsize=FONT_ANNOT, loc="lower right", framealpha=0.8)
    fig.tight_layout()
    _save(fig, "pareto_quality_vs_latency", formats, dpi)
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Figure 6: Summary bar chart — key metrics across modes
# ─────────────────────────────────────────────────────────────────────────────
def plot_summary_bar(formats: list[str], dpi: int) -> None:
    csv = PROC_DIR / "summary_by_mode.csv"
    if not csv.exists():
        return
    df = pd.read_csv(csv)
    if df.empty:
        return

    modes = _ordered_modes(df["mode"])
    df_plot = df.set_index("mode").loc[[m for m in modes if m in df["mode"].values]]

    metrics = ["success_rate", "strict_conformance", "mutation_kill_rate"]
    labels  = ["Strict Success Rate", "Strict Conformance", "Mutation Kill Rate"]
    avail   = [m for m in metrics if m in df_plot.columns]
    labels  = [labels[metrics.index(m)] for m in avail]

    x = np.arange(len(modes))
    width = 0.25
    offsets = np.linspace(-(len(avail)-1)*width/2, (len(avail)-1)*width/2, len(avail))

    fig, ax = plt.subplots(figsize=(7.5, 3.5))
    linestyles = ["-", "--", ":"]
    hatches_metric = [None, "//", "\\\\"]
    for i, (metric, label, ls, ht) in enumerate(zip(avail, labels, linestyles, hatches_metric)):
        vals = [df_plot.loc[m, metric] if m in df_plot.index else 0.0 for m in modes]
        bars = ax.bar(x + offsets[i], vals, width, label=label,
                      alpha=0.80, hatch=ht,
                      color=[PALETTE.get(m, "#888888") for m in modes],
                      edgecolor="white", linewidth=0.5)

    ax.set_xticks(x)
    ax.set_xticklabels(modes, fontsize=FONT_TICK)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.set_xlabel("Mode")
    ax.set_ylabel("Rate")
    ax.set_title("Key Metrics Summary by Mode")
    ax.set_ylim(0, 1.15)
    ax.legend(fontsize=FONT_ANNOT, loc="upper right", framealpha=0.8)
    fig.tight_layout()
    _save(fig, "summary_metrics_by_mode", formats, dpi)
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--formats", nargs="+", default=["pdf", "png"],
                        choices=["pdf", "png"])
    parser.add_argument("--dpi", type=int, default=300)
    args = parser.parse_args()

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Generating figures → {FIG_DIR}")

    plot_mode_distribution_conformance(args.formats, args.dpi)
    plot_mode_distribution_latency(args.formats, args.dpi)
    plot_ablation_contribution(args.formats, args.dpi)
    plot_prevention_heatmap(args.formats, args.dpi)
    plot_pareto(args.formats, args.dpi)
    plot_summary_bar(args.formats, args.dpi)

    print("Done.")


if __name__ == "__main__":
    main()
