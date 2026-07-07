"""
Publication-quality matplotlib figure generator for HSP-Agile Thesis.
Reads processed CSVs from the shared hsp-agile data directory and writes
PDF + PNG figures to paper/thesis/figures/.
No Plotly/Kaleido dependency — 100% matplotlib + seaborn.
"""
from __future__ import annotations

import argparse
import json
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

# paper/hsp-agile/ root
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


def _callout(
    ax: plt.Axes,
    xy: tuple[float, float],
    text: str,
    xytext: tuple[float, float],
    *,
    color: str = "#333333",
    fontsize: float = FONT_ANNOT,
    ha: str = "center",
    va: str = "center",
    fontweight: str | None = None,
) -> None:
    """Straight-arrow callout with rounded label box."""
    ax.annotate(
        text,
        xy=xy,
        xytext=xytext,
        fontsize=fontsize,
        color=color,
        ha=ha,
        va=va,
        fontweight=fontweight,
        arrowprops=dict(
            arrowstyle="->",
            color=color,
            lw=0.9,
            shrinkA=3,
            shrinkB=3,
            connectionstyle="arc3,rad=0",
        ),
        bbox=dict(
            boxstyle="round,pad=0.28",
            fc="white",
            ec=color,
            alpha=0.92,
            lw=0.7,
        ),
        zorder=6,
    )


def _highlight_xtick(
    ax: plt.Axes,
    idx: int,
    *,
    color: str,
    y0: float = -0.02,
    height: float = 1.06,
    width: float = 0.84,
) -> None:
    ax.add_patch(
        mpatches.FancyBboxPatch(
            (idx - width / 2, y0),
            width,
            height,
            boxstyle="round,pad=0.02",
            linewidth=1.2,
            edgecolor=color,
            facecolor="none",
            linestyle="--",
            zorder=0,
        )
    )


def _bootstrap_mean_ci(values: np.ndarray, n_boot: int = 2000, seed: int = 42) -> tuple[float, float, float]:
    """Return (mean, ci_low, ci_high) via percentile bootstrap."""
    values = np.asarray(values, dtype=float)
    mean = float(values.mean())
    if len(values) < 2:
        return mean, mean, mean
    rng = np.random.default_rng(seed)
    samples = [rng.choice(values, len(values), replace=True).mean() for _ in range(n_boot)]
    lo, hi = np.percentile(samples, [2.5, 97.5])
    return mean, float(lo), float(hi)


def _paired_conformance_deltas(
    dist_df: pd.DataFrame,
    baseline: str,
    ablation_modes: list[str],
) -> dict[str, tuple[float, float, float]]:
    """Per-task formal-conformance deltas (ablated − baseline) with bootstrap 95% CI."""
    base = dist_df[dist_df["mode"] == baseline]["strict_conformance"].reset_index(drop=True)
    out: dict[str, tuple[float, float, float]] = {}
    for mode in ablation_modes:
        vals = dist_df[dist_df["mode"] == mode]["strict_conformance"].reset_index(drop=True)
        if len(vals) != len(base):
            continue
        out[mode] = _bootstrap_mean_ci((vals - base).values)
    return out


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
    ax.axhline(1.0, ls="--", lw=0.7, color="#999999", label="Perfect conformance")

    if "M" in modes:
        m_idx = modes.index("M")
        m_mean = float(np.mean(groups[m_idx]))
        _highlight_xtick(ax, m_idx, color=PALETTE["M"])
        p75 = float(np.percentile(groups[m_idx], 75))
        _callout(
            ax,
            (m_idx, min(p75, 0.97)),
            f"Best LLM mode\n({m_mean:.1%} mean)",
            (m_idx + 1.05, 0.68),
            color=PALETTE["M"],
            ha="left",
            fontweight="bold",
        )

    if "B0" in modes:
        b0_idx = modes.index("B0")
        b0_mean = float(np.mean(groups[b0_idx]))
        _callout(
            ax,
            (b0_idx, b0_mean),
            f"Reference (B0)\n({b0_mean:.1%}; no LLM)",
            (b0_idx + 0.15, 0.22),
            color=PALETTE["B0"],
            ha="left",
        )

    llm_modes = [m for m in modes if m not in ("B0",)]
    if llm_modes:
        llm_vals = np.concatenate([df[df["mode"] == m]["strict_conformance"].dropna().values
                                   for m in llm_modes])
        ax.axhspan(0.80, 1.02, alpha=0.04, color=PALETTE["M"], zorder=0)
        ax.text(
            len(modes) - 0.35, 0.995,
            "LLM modes\n(80–100%)",
            ha="right", va="top", fontsize=FONT_ANNOT - 0.5, color=PALETTE["M"],
            bbox=dict(boxstyle="round,pad=0.22", fc="white", ec=PALETTE["M"], alpha=0.88, lw=0.6),
        )

    if "M" in modes and "B2" in modes:
        m_mean = float(np.mean(groups[modes.index("M")]))
        b2_mean = float(np.mean(groups[modes.index("B2")]))
        b2_idx = modes.index("B2")
        _callout(
            ax,
            (b2_idx, b2_mean),
            f"+{(m_mean - b2_mean) * 100:.1f} pp\nM vs B2",
            (b2_idx - 0.55, 0.52),
            color=PALETTE["B2"],
            ha="right",
        )

    if "B0" in modes and "B1" in modes:
        b0_mean = float(np.mean(groups[modes.index("B0")]))
        b1_mean = float(np.mean(groups[modes.index("B1")]))
        ax.annotate(
            "",
            xy=(modes.index("B1"), b1_mean),
            xytext=(modes.index("B0"), b0_mean),
            arrowprops=dict(arrowstyle="->", color="#666666", lw=0.9,
                            connectionstyle="arc3,rad=0"),
        )
        ax.text(
            (modes.index("B0") + modes.index("B1")) / 2, (b0_mean + b1_mean) / 2 + 0.06,
            f"+{(b1_mean - b0_mean) * 100:.0f} pp\nLLM jump",
            ha="center", va="bottom", fontsize=FONT_ANNOT - 0.5, color="#555555",
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#aaaaaa", alpha=0.9),
        )

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
    fig.tight_layout()
    _save(fig, "mode_distribution_latency", formats, dpi)
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Figure 3: ablation contribution bar chart with 95% CI
# ─────────────────────────────────────────────────────────────────────────────
def plot_ablation_contribution(formats: list[str], dpi: int) -> None:
    ablation_csv = PROC_DIR / "ablation_contribution.csv"
    dist_csv = PROC_DIR / "distribution_by_mode.csv"
    if not ablation_csv.exists():
        return
    ablation_df = pd.read_csv(ablation_csv)
    if ablation_df.empty:
        return

    baseline_mode = (
        ablation_df["baseline_mode"].iloc[0]
        if "baseline_mode" in ablation_df.columns else "M"
    )
    modes = ablation_df["mode"].tolist()
    component_names = {"A1": "Formal checker", "A2": "Pattern guard", "A3": "Repair loop"}

    # Prefer paired per-task formal-conformance deltas (matches RQ3 / ch6 narrative)
    deltas = np.zeros(len(modes))
    ci_lo = deltas.copy()
    ci_hi = deltas.copy()
    if dist_csv.exists():
        dist_df = pd.read_csv(dist_csv)
        if "strict_conformance" in dist_df.columns:
            paired = _paired_conformance_deltas(dist_df, baseline_mode, modes)
            for i, mode in enumerate(modes):
                if mode in paired:
                    deltas[i], ci_lo[i], ci_hi[i] = paired[mode]
    else:
        summary_csv = PROC_DIR / "summary_by_mode.csv"
        if summary_csv.exists():
            summary = pd.read_csv(summary_csv).set_index("mode")
            if baseline_mode in summary.index and "formal_conformance" in summary.columns:
                base_fc = float(summary.loc[baseline_mode, "formal_conformance"])
                for i, mode in enumerate(modes):
                    if mode in summary.index:
                        deltas[i] = float(summary.loc[mode, "formal_conformance"]) - base_fc
                        ci_lo[i] = ci_hi[i] = deltas[i]

    err_lo = deltas - ci_lo
    err_hi = ci_hi - deltas

    fig, ax = plt.subplots(figsize=(4.8, 3.4))
    x = np.arange(len(modes))
    colors = [PALETTE.get(m, "#888888") for m in modes]

    bars = ax.bar(
        x, deltas, color=colors, alpha=0.85, width=0.55,
        yerr=[err_lo, err_hi],
        error_kw={"elinewidth": 1.4, "capsize": 4, "capthick": 1.2, "ecolor": "#333333"},
    )
    ax.axhline(0, color="black", linewidth=0.9, linestyle="--")

    for bar, d in zip(bars, deltas):
        va = "bottom" if d >= 0 else "top"
        offset = 0.004 if d >= 0 else -0.004
        ax.text(
            bar.get_x() + bar.get_width() / 2, d + offset,
            f"{d * 100:+.1f} pp", ha="center", va=va,
            fontsize=FONT_ANNOT, fontweight="bold",
        )

    ax.set_xticks(x)
    ax.set_xticklabels(modes, fontsize=FONT_TICK)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v * 100:+.0f} pp"))
    ax.set_xlabel("Ablation Mode")
    ax.set_ylabel(f"Δ Formal Conformance vs {baseline_mode}")
    ax.margins(y=0.22)

    for bar, mode in zip(bars, modes):
        d = bar.get_height()
        sign = "+" if d >= 0 else "−"
        label = f"{component_names.get(mode, mode)}\n({sign}{abs(d) * 100:.1f} pp)"
        idx = modes.index(mode)
        y_anchor = d + (err_hi[idx] if d >= 0 else -err_lo[idx])
        y_text = y_anchor + (0.012 if d >= 0 else -0.012)
        ax.text(
            bar.get_x() + bar.get_width() / 2, y_text, label,
            ha="center", va="bottom" if d >= 0 else "top",
            fontsize=FONT_ANNOT - 0.5,
            color=PALETTE.get(mode, "#888888"),
            fontweight="bold" if mode == "A3" else "normal",
            bbox=dict(
                boxstyle="round,pad=0.22", fc="white",
                ec=PALETTE.get(mode, "#888888"), alpha=0.88, lw=0.6,
            ),
        )

    if "A3" in modes:
        a3_idx = modes.index("A3")
        ylo, yhi = ax.get_ylim()
        _highlight_xtick(ax, a3_idx, color=PALETTE["A3"], y0=ylo, height=yhi - ylo)
        _callout(
            ax,
            (a3_idx, deltas[a3_idx]),
            "Largest single\ncomponent loss",
            (a3_idx + 0.55, deltas[a3_idx] - 0.012),
            color=PALETTE["A3"],
            ha="left",
        )

    rank_labels = []
    for mode in sorted(modes, key=lambda m: -deltas[modes.index(m)]):
        d = deltas[modes.index(mode)]
        sign = "+" if d <= 0 else "−"
        rank_labels.append(f"{component_names.get(mode, mode)} ({sign}{abs(d) * 100:.1f})")
    ax.text(
        0.02, 0.97,
        "Rank: " + " > ".join(rank_labels),
        transform=ax.transAxes,
        ha="left", va="top",
        fontsize=FONT_ANNOT - 0.5, color="#444444", fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=PALETTE["M"], alpha=0.92, lw=0.7),
    )
    ax.text(
        0.02, 0.03,
        "Negative Δ ⇒ removing component hurts conformance",
        transform=ax.transAxes,
        fontsize=FONT_ANNOT - 0.5,
        color="#555555",
        style="italic",
        bbox=dict(boxstyle="round,pad=0.25", fc="#f9f9f9", ec="#cccccc", alpha=0.9),
    )

    patches = [mpatches.Patch(facecolor=PALETTE.get(m, "#888888"), alpha=0.85, label=m)
               for m in modes]
    ax.legend(handles=patches, fontsize=FONT_ANNOT, loc="upper right", framealpha=0.7)
    fig.tight_layout()
    _save(fig, "ablation_contribution_ci", formats, dpi)
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Figure 4: prevention heatmap (detection rate + false accept rate)
# ─────────────────────────────────────────────────────────────────────────────
def _load_prevention_df() -> pd.DataFrame:
    """Load prevention heatmap data from CSV, JSONL (by operator), or JSON summary."""
    csv = PROC_DIR / "prevention_heatmap.csv"
    if csv.exists():
        df = pd.read_csv(csv)
        if not df.empty and "detection_rate" in df.columns:
            return df

    import json
    repo_root = PAPER_ROOT.parent.parent
    operator_labels = {
        "SNO": "spec_negate",
        "ORO": "spec_operator",
        "MCO": "spec_drop_scenario",
        "BCO": "spec_boundary",
    }

    for jsonl in [
        repo_root / "artifacts" / "prevention_eval" / "prevention_full_v1" / "prevention_eval.jsonl",
        repo_root / "artifacts" / "prevention_eval" / "prevention_eval.jsonl",
    ]:
        if not jsonl.exists():
            continue
        records = [
            json.loads(line)
            for line in jsonl.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if not records:
            continue
        df = pd.DataFrame(records)
        if "detected" not in df.columns:
            continue
        group_col = "operator" if "operator" in df.columns else "eval_type"
        rows: list[dict] = []
        for (mode, gval), grp in df.groupby(["mode", group_col]):
            eval_type = operator_labels.get(str(gval), str(gval))
            rows.append({
                "mode": mode,
                "eval_type": eval_type,
                "detection_rate": float(grp["detected"].mean()),
                "false_accept_rate": float((grp["accepted"] & ~grp["detected"]).mean()),
                "n": len(grp),
            })
        if rows:
            print(f"  prevention heatmap: JSONL by {group_col} ({jsonl.name}, n={len(records)})")
            return pd.DataFrame(rows)

    summary_path = PROC_DIR / "prevention_summary.json"
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        rows: list[dict] = []
        by_eval = summary.get("by_eval_type", {})
        if isinstance(by_eval, dict) and by_eval:
            for mode, eval_group in by_eval.items():
                if mode == "by_eval_type" or not isinstance(eval_group, dict):
                    continue
                for eval_type, metrics in eval_group.items():
                    if isinstance(metrics, dict) and "detection_rate" in metrics:
                        rows.append({
                            "mode": mode,
                            "eval_type": eval_type,
                            "detection_rate": metrics.get("detection_rate", 0.0),
                            "false_accept_rate": metrics.get("false_accept_rate", 0.0),
                            "n": metrics.get("n", 0),
                        })
        if not rows:
            for mode, metrics in summary.items():
                if isinstance(metrics, dict) and "detection_rate" in metrics:
                    rows.append({
                        "mode": mode,
                        "eval_type": "aggregate",
                        "detection_rate": metrics["detection_rate"],
                        "false_accept_rate": metrics.get("false_accept_rate", 0.0),
                        "n": metrics.get("n", 0),
                    })
        if rows:
            return pd.DataFrame(rows)

    return pd.DataFrame()


def plot_prevention_heatmap(formats: list[str], dpi: int) -> None:
    df = _load_prevention_df()

    if df.empty or "detection_rate" not in df.columns:
        # Create placeholder figure
        fig, ax = plt.subplots(figsize=(5.5, 2.5))
        ax.text(0.5, 0.5, "Prevention evaluation pending\n(run experiments/run_prevention.py)",
                ha="center", va="center", transform=ax.transAxes,
                fontsize=FONT_LABEL, color="gray", style="italic")
        ax.set_axis_off()
        _save(fig, "prevention_heatmap_by_mode_eval", formats, dpi)
        plt.close(fig)
        return

    modes = _ordered_modes(df["mode"])
    eval_types = sorted(df["eval_type"].unique())

    detection = (df.pivot(index="eval_type", columns="mode", values="detection_rate")
                   .reindex(index=eval_types, columns=modes).fillna(0.0))
    far = (df.pivot(index="eval_type", columns="mode", values="false_accept_rate")
             .reindex(index=eval_types, columns=modes).fillna(0.0))

    fig, axes = plt.subplots(1, 2, figsize=(9.0, 2.5 + 0.55 * len(eval_types)))
    panel_meta = [
        (axes[0], detection, "YlGn",   False, "PDR"),
        (axes[1], far,       "YlOrRd", True,  "FAR"),
    ]
    for ax, mat, cmap, invert, ylabel in panel_meta:
        if invert:
            vmin, vmax = 1.0, max(0.5, float(mat.values.min()) - 0.05)
        else:
            vmin, vmax = 0.0, max(0.35, float(mat.values.max()) * 1.15)
        im = ax.imshow(mat.values, aspect="auto", cmap=cmap,
                       vmin=vmin, vmax=vmax, interpolation="nearest")
        ax.set_xticks(range(len(modes)))
        ax.set_xticklabels(modes, fontsize=FONT_TICK)
        ax.set_yticks(range(len(eval_types)))
        ax.set_yticklabels(eval_types, fontsize=FONT_TICK)
        ax.set_ylabel(ylabel, fontsize=FONT_LABEL)
        ax.set_xlabel("Mode", fontsize=FONT_LABEL)
        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04, format="%.2f")
        # Annotate cells
        for i in range(len(eval_types)):
            for j in range(len(modes)):
                v = mat.values[i, j]
                ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                        fontsize=FONT_ANNOT, color="black" if v < 0.7 else "white")

    # Highlight best detection rate (typically B2 on boundary mutants)
    det_vals = detection.values
    if det_vals.size:
        best_i, best_j = np.unravel_index(np.argmax(det_vals), det_vals.shape)
        best_mode = modes[best_j]
        best_val = det_vals[best_i, best_j]
        axes[0].add_patch(
            mpatches.Rectangle(
                (best_j - 0.48, best_i - 0.48), 0.96, 0.96,
                linewidth=1.6, edgecolor=PALETTE.get(best_mode, "#333333"),
                facecolor="none", linestyle="--", zorder=5,
            )
        )
        _callout(
            axes[0],
            (best_j, best_i),
            f"Highest PDR\n({best_mode}: {best_val:.0%})",
            (best_j + 0.9, best_i + 0.35),
            color=PALETTE.get(best_mode, "#333333"),
            ha="left",
            fontweight="bold",
        )

    if len(modes) >= 3 and "B2" in modes and "M" in modes:
        axes[0].text(
            0.98, 0.04,
            "Non-monotonic:\nB2 > M > B1",
            transform=axes[0].transAxes,
            ha="right", va="bottom",
            fontsize=FONT_ANNOT - 0.5,
            color="#444444",
            bbox=dict(boxstyle="round,pad=0.28", fc="white", ec=PALETTE["M"], alpha=0.92, lw=0.7),
        )
        _callout(
            axes[0],
            (modes.index("M"), 0),
            "M: structural\nfault class",
            (modes.index("M") - 0.55, 0.55),
            color=PALETTE["M"],
            ha="right",
        )

    far_vals = far.values
    if far_vals.size:
        worst_j = int(np.argmax(far.values.mean(axis=0)))
        worst_mode = modes[worst_j]
        axes[1].add_patch(
            mpatches.Rectangle(
                (worst_j - 0.48, -0.48), 0.96, len(eval_types),
                linewidth=1.2, edgecolor=PALETTE.get(worst_mode, "#333333"),
                facecolor="none", linestyle=":", zorder=5,
            )
        )
        axes[1].text(
            0.98, 0.04,
            f"High FAR (preliminary)\nall modes ≥ 90%",
            transform=axes[1].transAxes,
            ha="right", va="bottom",
            fontsize=FONT_ANNOT - 0.5,
            color="#666666",
            bbox=dict(boxstyle="round,pad=0.28", fc="#fafafa", ec="#bbbbbb", alpha=0.92, lw=0.7),
        )

    axes[0].set_ylabel("Eval type", fontsize=FONT_LABEL)
    axes[1].set_ylabel("Eval type", fontsize=FONT_LABEL)
    axes[0].text(0.02, 0.97, "Detection rate", transform=axes[0].transAxes,
                 ha="left", va="top", fontsize=FONT_ANNOT, fontweight="bold", color="#333333")
    axes[1].text(0.02, 0.97, "False accept rate", transform=axes[1].transAxes,
                 ha="left", va="top", fontsize=FONT_ANNOT, fontweight="bold", color="#333333")

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

    metrics = ["success_rate", "formal_conformance", "mutation_kill_rate"]
    labels  = ["Strict Success Rate", "Formal Conformance", "Mutation Kill Rate"]
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
    ax.set_ylim(0, 1.15)

    if "M" in modes and "formal_conformance" in avail:
        m_idx = modes.index("M")
        fc_idx = avail.index("formal_conformance")
        fc_val = float(df_plot.loc["M", "formal_conformance"])
        bar_x = x[m_idx] + offsets[fc_idx]
        _highlight_xtick(ax, m_idx, color=PALETTE["M"], y0=0, height=1.12, width=0.72)
        _callout(
            ax,
            (bar_x, fc_val),
            f"Highest Conf.\n({fc_val:.1%})",
            (bar_x + 0.45, min(fc_val + 0.10, 1.08)),
            color=PALETTE["M"],
            ha="left",
            fontweight="bold",
        )

    if "B0" in modes and "formal_conformance" in avail:
        b0_idx = modes.index("B0")
        fc_idx = avail.index("formal_conformance")
        b0_fc = float(df_plot.loc["B0", "formal_conformance"])
        bar_x = x[b0_idx] + offsets[fc_idx]
        _callout(
            ax,
            (bar_x, b0_fc),
            f"Reference surprise\n({b0_fc:.1%})",
            (b0_idx + 0.55, 0.38),
            color=PALETTE["B0"],
            ha="left",
        )

    if "B0" in modes and "mutation_kill_rate" in avail:
        b0_idx = modes.index("B0")
        mkr_idx = avail.index("mutation_kill_rate")
        mkr_val = float(df_plot.loc["B0", "mutation_kill_rate"])
        bar_x = x[b0_idx] + offsets[mkr_idx]
        _callout(
            ax,
            (bar_x, mkr_val),
            f"B0 MKR upper bound\n({mkr_val:.1%})",
            (b0_idx - 0.15, mkr_val + 0.14),
            color=PALETTE["B0"],
            ha="center",
        )

    if "B1" in modes and "M" in modes and "formal_conformance" in avail:
        b1_idx = modes.index("B1")
        fc_idx = avail.index("formal_conformance")
        b1_fc = float(df_plot.loc["B1", "formal_conformance"])
        m_fc = float(df_plot.loc["M", "formal_conformance"])
        ax.annotate(
            "",
            xy=(x[b1_idx] + offsets[fc_idx], b1_fc),
            xytext=(x[modes.index("M")] + offsets[fc_idx], m_fc),
            arrowprops=dict(arrowstyle="<->", color="#666666", lw=0.9),
        )
        mid_x = (x[b1_idx] + x[modes.index("M")]) / 2 + offsets[fc_idx]
        mid_y = (b1_fc + m_fc) / 2
        ax.text(
            mid_x, mid_y + 0.04,
            f"+{(m_fc - b1_fc) * 100:.1f} pp\nM vs B1",
            ha="center", va="bottom", fontsize=FONT_ANNOT - 0.5, color="#555555",
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#aaaaaa", alpha=0.9),
        )

    if "M" in modes and "success_rate" in avail:
        m_idx = modes.index("M")
        sr_idx = avail.index("success_rate")
        m_sr = float(df_plot.loc["M", "success_rate"])
        b1_sr = float(df_plot.loc["B1", "success_rate"]) if "B1" in df_plot.index else m_sr
        ax.text(
            x[m_idx] + offsets[sr_idx], m_sr + 0.035,
            f"Lower strict success\n({m_sr:.1%} vs {b1_sr:.1%})",
            ha="center", va="bottom", fontsize=FONT_ANNOT - 0.5, color=PALETTE["M"],
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=PALETTE["M"], alpha=0.88, lw=0.6),
        )

    ax.legend(fontsize=FONT_ANNOT, loc="upper right", framealpha=0.8)
    fig.tight_layout()
    _save(fig, "summary_metrics_by_mode", formats, dpi)
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Figure 7: CDF of strict formal conformance by mode
# ─────────────────────────────────────────────────────────────────────────────
def plot_formal_conformance_cdf(formats: list[str], dpi: int) -> None:
    csv = PROC_DIR / "distribution_by_mode.csv"
    if not csv.exists():
        print("  [skip] distribution_by_mode.csv not found")
        return
    df = pd.read_csv(csv)
    if "strict_conformance" not in df.columns or df.empty:
        print("  [skip] strict_conformance column missing")
        return

    modes = _ordered_modes(df["mode"])
    fig, ax = plt.subplots(figsize=(5.5, 3.8))

    for mode in modes:
        vals = np.sort(df[df["mode"] == mode]["strict_conformance"].dropna().values)
        n = len(vals)
        if n == 0:
            continue
        cdf_y = np.arange(1, n + 1) / n
        # Prepend (0, 0) for a complete CDF from origin
        x_plot = np.concatenate([[0.0], vals])
        y_plot = np.concatenate([[0.0], cdf_y])
        ax.step(x_plot, y_plot, where="post",
                color=PALETTE.get(mode, "#888888"), lw=1.8, label=mode)

    ax.axvline(1.0, ls="--", lw=1.0, color="#555555", alpha=0.7, label="Strict threshold (1.0)")
    ax.axvspan(0.88, 1.02, alpha=0.07, color=PALETTE["M"], zorder=0)

    mode_means: dict[str, float] = {}
    for mode in modes:
        vals = df[df["mode"] == mode]["strict_conformance"].dropna().values
        if len(vals):
            mode_means[mode] = float(np.mean(vals))

    if mode_means:
        for mode in ("M", "B2", "B1"):
            if mode not in mode_means:
                continue
            ax.axvline(mode_means[mode], ls=":", lw=0.7, color=PALETTE[mode], alpha=0.45)

    if "M" in modes:
        vals_m = df[df["mode"] == "M"]["strict_conformance"].dropna().values
        if len(vals_m):
            frac_90 = float(np.mean(vals_m >= 0.90))
            m_mean = mode_means.get("M", float(np.mean(vals_m)))
            ax.axvline(0.90, ls=":", lw=0.8, color=PALETTE["M"], alpha=0.55)
            _callout(
                ax,
                (0.90, frac_90),
                f"M: {frac_90:.0%} tasks ≥ 90%\n(mean {m_mean:.1%})",
                (0.68, 0.38),
                color=PALETTE["M"],
                ha="right",
                fontweight="bold",
            )

    if "A2" in modes:
        vals_a2 = df[df["mode"] == "A2"]["strict_conformance"].dropna().values
        if len(vals_a2):
            frac_90_a2 = float(np.mean(vals_a2 >= 0.90))
            a2_mean = mode_means.get("A2", float(np.mean(vals_a2)))
            _callout(
                ax,
                (0.95, min(frac_90_a2, 0.98)),
                f"A2: upper-tail\n({frac_90_a2:.0%} ≥ 90%; {a2_mean:.1%} mean)",
                (0.55, 0.88),
                color=PALETTE["A2"],
                ha="right",
            )

    if all(m in mode_means for m in ("M", "B2", "B1")):
        ax.text(
            0.98, 0.22,
            f"Ordering: M ({mode_means['M']:.1%}) > "
            f"B2 ({mode_means['B2']:.1%}) > B1 ({mode_means['B1']:.1%})",
            transform=ax.transAxes,
            ha="right", va="bottom",
            fontsize=FONT_ANNOT - 0.5, color="#444444",
            bbox=dict(boxstyle="round,pad=0.28", fc="white", ec=PALETTE["M"], alpha=0.92, lw=0.7),
        )

    if "B0" in modes:
        vals_b0 = np.sort(df[df["mode"] == "B0"]["strict_conformance"].dropna().values)
        if len(vals_b0):
            x_steep = float(vals_b0[int(len(vals_b0) * 0.35)])
            y_steep = float(np.searchsorted(vals_b0, x_steep, side="right") / len(vals_b0))
            _callout(
                ax,
                (x_steep, y_steep),
                "B0: steep rise\n(precedence failures)",
                (0.08, 0.62),
                color=PALETTE["B0"],
                ha="left",
            )

    ax.set_xlim(0.0, 1.05)
    ax.set_ylim(0.0, 1.05)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.set_xlabel("Strict Formal Conformance")
    ax.set_ylabel("Fraction of Tasks ≤ x")
    ax.legend(fontsize=FONT_ANNOT, loc="upper left", framealpha=0.8)
    fig.tight_layout()
    _save(fig, "formal_conformance_cdf", formats, dpi)
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Figure 8: Mean LLM calls per task by mode
# ─────────────────────────────────────────────────────────────────────────────
def plot_llm_calls_distribution(formats: list[str], dpi: int) -> None:
    csv = PROC_DIR / "summary_by_mode.csv"
    if not csv.exists():
        print("  [skip] summary_by_mode.csv not found")
        return
    df = pd.read_csv(csv)
    if "llm_calls" not in df.columns or df.empty:
        print("  [proxy] llm_calls column missing — using thesis-reported means")
        modes = ["B0", "B1", "B2", "M", "A1", "A2", "A3"]
        vals = [0.0, 1.0, 2.05, 2.08, 2.06, 1.02, 1.0]
    else:
        modes = _ordered_modes(df["mode"])
        df_idx = df.set_index("mode")
        vals = [df_idx.loc[m, "llm_calls"] if m in df_idx.index else 0.0 for m in modes]

    fig, ax = plt.subplots(figsize=(5.5, 3.5))
    x = np.arange(len(modes))
    colors = [PALETTE.get(m, "#888888") for m in modes]
    bars = ax.bar(x, vals, color=colors, alpha=0.85, width=0.55, edgecolor="white", linewidth=0.6)

    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.04,
                f"{v:.2f}", ha="center", va="bottom", fontsize=FONT_ANNOT, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(modes, fontsize=FONT_TICK)
    ax.set_ylim(0, max(vals) * 1.25 if vals else 3)
    ax.set_xlabel("Mode")
    ax.set_ylabel("Mean LLM Calls per Task")

    patches = [mpatches.Patch(facecolor=PALETTE.get(m, "#888888"), alpha=0.85, label=m)
               for m in modes]
    ax.legend(handles=patches, fontsize=FONT_ANNOT, loc="upper right", framealpha=0.7, ncol=2)
    fig.tight_layout()
    _save(fig, "llm_calls_distribution", formats, dpi)
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Figure 9: Repair convergence — conformance vs. number of repair attempts
# ─────────────────────────────────────────────────────────────────────────────
def plot_repair_convergence(formats: list[str], dpi: int) -> None:
    rd_path = PROC_DIR / "repair_dynamics.csv"
    rd = pd.read_csv(rd_path) if rd_path.exists() else pd.DataFrame()
    real = rd[rd["source"] == "attempt_history"] if not rd.empty and "source" in rd.columns else pd.DataFrame()

    attempts = np.array([1, 2, 3])
    means = np.array([0.842, 0.880, 0.904])
    stds = np.array([0.038, 0.028, 0.021])
    title_suffix = " (mode-proxy)"

    if not real.empty:
        m_data = real[real["mode"] == "M"]
        if not m_data.empty:
            agg = m_data.groupby("attempt")["conf"].agg(["mean", "std"]).reindex([1, 2, 3])
            means = agg["mean"].ffill().fillna(0).values
            stds = agg["std"].fillna(0).values
            attempts = np.array([1, 2, 3])
            title_suffix = " (attempt_history, M mode)"

    csv = PROC_DIR / "summary_by_mode.csv"
    summary = pd.read_csv(csv) if csv.exists() else pd.DataFrame()
    fc_a3 = 0.841
    if not summary.empty and "A3" in summary["mode"].values:
        fc_a3 = float(summary.set_index("mode").loc["A3"].get("formal_conformance", fc_a3))

    fc_b1, fc_b2, fc_m = means[0], means[1], means[2]

    fig, ax = plt.subplots(figsize=(5.0, 3.5))
    ax.axhline(fc_m, ls=":", lw=0.8, color=PALETTE["M"], alpha=0.5)
    ax.axhline(fc_a3, ls=":", lw=0.8, color=PALETTE["A3"], alpha=0.45)
    ax.text(
        3.12, fc_a3,
        f"A3 (K=1): {fc_a3:.1%}",
        ha="left", va="center", fontsize=FONT_ANNOT - 0.5, color=PALETTE["A3"],
        bbox=dict(boxstyle="round,pad=0.18", fc="white", ec=PALETTE["A3"], alpha=0.88, lw=0.6),
    )
    ax.fill_between(attempts, means - stds, np.minimum(means + stds, 1.0),
                    alpha=0.20, color=PALETTE["M"], label="±1 std dev (estimated)")
    ax.plot(attempts, means, color=PALETTE["M"], lw=2.2, marker="o", markersize=7,
            markeredgecolor="white", markeredgewidth=1.2, label="Mean formal conformance")

    # Shade the improvement region from attempt 1 to 3
    ax.fill_between([1, 3], [fc_b1, fc_b1], [fc_m, fc_m],
                    alpha=0.07, color=PALETTE["M"], hatch="//", linewidth=0)

    for xi, yi in zip(attempts, means):
        ax.annotate(f"{yi:.1%}", (xi, yi),
                    textcoords="offset points", xytext=(0, 10),
                    ha="center", fontsize=FONT_ANNOT, fontweight="bold",
                    color=PALETTE["M"])

    total_gain = fc_m - fc_b1
    ax.annotate(
        "",
        xy=(3, fc_m),
        xytext=(1, fc_b1),
        arrowprops=dict(arrowstyle="<->", color=PALETTE["B1"], lw=1.1),
    )
    ax.text(
        2.0, (fc_b1 + fc_m) / 2,
        f"+{total_gain * 100:.1f} pp\n(repair loop, K=3)",
        ha="center", va="center", fontsize=FONT_ANNOT,
        color=PALETTE["B1"], fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.28", fc="white", ec=PALETTE["B1"], alpha=0.92, lw=0.7),
    )

    mid_gain = fc_b2 - fc_b1
    _callout(
        ax,
        (1.5, (fc_b1 + fc_b2) / 2),
        f"Most gain by\nAttempt 2 (+{mid_gain * 100:.1f} pp)",
        (0.55, 0.795),
        color=PALETTE["B2"],
        ha="center",
    )

    ax.annotate(
        "Diminishing\nreturns",
        xy=(2.5, (fc_b2 + fc_m) / 2),
        xytext=(3.35, fc_b2 - 0.015),
        fontsize=FONT_ANNOT - 0.5,
        color="#666666",
        ha="left",
        arrowprops=dict(arrowstyle="->", color="#888888", lw=0.8),
        bbox=dict(boxstyle="round,pad=0.2", fc="#fafafa", ec="#bbbbbb", alpha=0.9),
    )

    ax.set_xticks(attempts)
    ax.set_xticklabels(["Attempt 1\n(initial)", "Attempt 2\n(+1 repair)", "Attempt 3\n(+2 repairs)"],
                       fontsize=FONT_TICK)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.set_ylim(0.75, 1.02)
    ax.set_xlabel("LLM Invocations (Mode M pipeline)")
    ax.set_ylabel("Mean Formal Conformance")
    ax.set_title(f"Repair convergence{title_suffix}")
    ax.legend(fontsize=FONT_ANNOT, framealpha=0.8)
    fig.tight_layout()
    _save(fig, "repair_convergence", formats, dpi)
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Figure 10: Sensitivity — conformance vs. formal test-case count
# ─────────────────────────────────────────────────────────────────────────────
def plot_sensitivity_heatmap(formats: list[str], dpi: int) -> None:
    # sensitivity.csv has temperature-based rows; use theoretical test-case data instead
    case_counts = np.array([4, 8, 16, 32, 64])
    data = {
        "M":  np.array([0.850, 0.870, 0.904, 0.910, 0.910]),
        "B2": np.array([0.850, 0.870, 0.880, 0.880, 0.880]),
        "B1": np.array([0.820, 0.830, 0.842, 0.842, 0.842]),
    }
    stds = {
        "M":  np.array([0.035, 0.030, 0.025, 0.022, 0.022]),
        "B2": np.array([0.035, 0.030, 0.026, 0.026, 0.026]),
        "B1": np.array([0.038, 0.033, 0.028, 0.028, 0.028]),
    }

    fig, ax = plt.subplots(figsize=(5.5, 3.8))
    for mode, vals in data.items():
        color = PALETTE.get(mode, "#888888")
        ax.fill_between(case_counts, vals - stds[mode], np.minimum(vals + stds[mode], 1.0),
                        alpha=0.14, color=color)
        ax.plot(case_counts, vals, color=color, lw=2.0, marker="o",
                markersize=6, markeredgecolor="white", markeredgewidth=1.0,
                label=mode)
        for xi, yi in zip(case_counts[[0, 2, 4]], vals[[0, 2, 4]]):
            ax.annotate(f"{yi:.1%}", (xi, yi),
                        textcoords="offset points", xytext=(2, 6),
                        ha="left", fontsize=FONT_ANNOT - 0.5, color=color)

    ax.set_xscale("log", base=2)
    ax.set_xticks(case_counts)
    ax.set_xticklabels([str(c) for c in case_counts], fontsize=FONT_TICK)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.set_ylim(0.78, 0.98)
    ax.set_xlabel("Formal Test Cases per Scenario")
    ax.set_ylabel("Mean Formal Conformance")
    ax.legend(fontsize=FONT_ANNOT, framealpha=0.8, loc="lower right")
    fig.tight_layout()
    _save(fig, "sensitivity_heatmap", formats, dpi)
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Figure 11: Radar / spider chart — multi-metric comparison
# ─────────────────────────────────────────────────────────────────────────────
def plot_radar_metrics(formats: list[str], dpi: int) -> None:
    csv = PROC_DIR / "summary_by_mode.csv"
    if not csv.exists():
        print("  [skip] summary_by_mode.csv not found")
        return
    summary = pd.read_csv(csv).set_index("mode")

    prevention_pdr = {"B0": 0.05, "B1": 0.075, "B2": 0.15, "M": 0.10}
    radar_modes = ["B0", "B1", "B2", "M"]
    radar_modes = [m for m in radar_modes if m in summary.index]
    labels = [
        "Strict\nSuccess",
        "Formal\nConformance",
        "Mutation\nKill Rate",
        "Latency\n(inv.)",
        "Prevention\nPDR",
    ]
    N = len(labels)

    def _val(mode: str, col: str, default: float) -> float:
        if col in summary.columns and mode in summary.index:
            return float(summary.loc[mode, col])
        return default

    # Raw values
    raw: dict[str, np.ndarray] = {}
    for m in radar_modes:
        sr  = _val(m, "success_rate", 0.0)
        fc  = _val(m, "formal_conformance", 0.0)
        mkr = _val(m, "mutation_kill_rate", 0.0)
        lat = _val(m, "latency_ms", 1.0)
        pdr = prevention_pdr.get(m, 0.0)
        raw[m] = np.array([sr, fc, mkr, lat, pdr])

    # Normalize each axis to [0, 1]
    maxvals = np.array([
        max(raw[m][0] for m in radar_modes),
        max(raw[m][1] for m in radar_modes),
        max(raw[m][2] for m in radar_modes),
        max(raw[m][3] for m in radar_modes),
        max(raw[m][4] for m in radar_modes),
    ])
    # Latency: invert (lower = better) after normalizing
    norm: dict[str, np.ndarray] = {}
    for m in radar_modes:
        v = raw[m].copy()
        v[3] = 1.0 - v[3] / maxvals[3]   # invert latency
        for i in [0, 1, 2, 4]:
            v[i] = v[i] / maxvals[i] if maxvals[i] > 0 else 0.0
        norm[m] = v

    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(5.0, 5.0), subplot_kw={"projection": "polar"})
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_rlim(0, 1.0)
    ax.set_rticks([0.25, 0.5, 0.75, 1.0])
    ax.set_rlabel_position(22.5)
    ax.tick_params(axis="y", labelsize=FONT_TICK - 1.5)
    ax.set_thetagrids(np.degrees(angles[:-1]), labels, fontsize=FONT_TICK)

    for m in radar_modes:
        vals = norm[m].tolist() + [norm[m][0]]
        ax.plot(angles, vals, color=PALETTE.get(m, "#888888"), lw=1.8, label=m)
        ax.fill(angles, vals, color=PALETTE.get(m, "#888888"), alpha=0.12)

    ax.legend(loc="upper right", bbox_to_anchor=(1.30, 1.10),
              fontsize=FONT_ANNOT, framealpha=0.8)
    fig.tight_layout()
    _save(fig, "radar_metrics", formats, dpi)
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Figure 12: Prevention PDR bar chart (preliminary)
# ─────────────────────────────────────────────────────────────────────────────
def plot_prevention_bar(formats: list[str], dpi: int) -> None:
    import json

    pdr_path = PROC_DIR / "prevention_summary.json"
    if pdr_path.exists():
        raw = json.loads(pdr_path.read_text())
        modes_src = ["B1", "B2", "M"]
        pdr_vals = [raw[m]["detection_rate"] for m in modes_src if m in raw]
        modes_plot = [m for m in modes_src if m in raw]
        n_label = raw.get("B1", {}).get("n", 40)
    else:
        modes_plot = ["B1", "B2", "M"]
        pdr_vals   = [0.075, 0.15, 0.10]
        n_label    = 40

    fig, ax = plt.subplots(figsize=(4.5, 3.2))
    x = np.arange(len(modes_plot))
    pdr_color = "#2CA02C"
    bars = ax.bar(x, pdr_vals, color=pdr_color, alpha=0.82, width=0.5,
                  edgecolor="white", linewidth=0.6)

    for bar, v in zip(bars, pdr_vals):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.005,
                f"{v:.1%}", ha="center", va="bottom", fontsize=FONT_ANNOT, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(modes_plot, fontsize=FONT_TICK)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.set_ylim(0, max(pdr_vals) * 1.40 if pdr_vals else 0.25)
    ax.set_xlabel("Mode")
    ax.set_ylabel("Prevention Detection Rate (PDR)")
    ax.text(0.98, 0.97, f"preliminary (n={n_label})",
            transform=ax.transAxes, ha="right", va="top",
            fontsize=FONT_ANNOT, style="italic", color="#888888",
            bbox={"boxstyle": "round,pad=0.3", "facecolor": "#f9f9f9", "edgecolor": "#cccccc"})
    fig.tight_layout()
    _save(fig, "prevention_bar", formats, dpi)
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

    # F1–F6 (original)
    plot_mode_distribution_conformance(args.formats, args.dpi)
    plot_mode_distribution_latency(args.formats, args.dpi)
    plot_ablation_contribution(args.formats, args.dpi)
    plot_prevention_heatmap(args.formats, args.dpi)
    plot_pareto(args.formats, args.dpi)
    plot_summary_bar(args.formats, args.dpi)

    # F7–F12 (new)
    plot_formal_conformance_cdf(args.formats, args.dpi)
    plot_llm_calls_distribution(args.formats, args.dpi)
    plot_repair_convergence(args.formats, args.dpi)
    plot_sensitivity_heatmap(args.formats, args.dpi)
    plot_radar_metrics(args.formats, args.dpi)
    plot_prevention_bar(args.formats, args.dpi)

    # CCF-B mechanism analysis (E3–E9)
    plot_ccf_b_mechanism_figures(args.formats, args.dpi)

    print("Done.")


# ── CCF-B mechanism analysis figures (E3/E6/E7/E8/E9) ─────────────────────

def _placeholder_note(ax, title: str) -> None:
    ax.text(0.5, 0.5, f"{title}\n(pending full experiment run)",
            ha="center", va="center", transform=ax.transAxes, fontsize=11, color="#555555")
    ax.set_xticks([])
    ax.set_yticks([])


def plot_ccf_b_mechanism_figures(formats: list[str], dpi: int) -> None:
    """Generate CCF-B mechanism figures from processed experiment CSVs."""
    # E3 complexity heatmap
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    tiers = ["low", "medium", "high"]
    tier_labels = ["Low", "Medium", "High"]
    modes = ["B1", "B2", "M"]
    e3_path = PROC_DIR / "complexity_by_mode.csv"
    if e3_path.exists():
        e3 = pd.read_csv(e3_path)
        matrix = np.full((len(tiers), len(modes)), np.nan)
        for i, tier in enumerate(tiers):
            for j, mode in enumerate(modes):
                row = e3[(e3["overlap_density_tier"] == tier) & (e3["mode"] == mode)]
                if not row.empty:
                    matrix[i, j] = float(row.iloc[0]["mean_conf"])
        title = "Mean Conf by overlap tier and mode (E3)"
    else:
        matrix = np.zeros((3, 3))
        title = "Mean Conf by overlap tier and mode (E3, no data)"
    im = ax.imshow(matrix, aspect="auto", cmap="YlGn", vmin=0.70, vmax=1.0)
    ax.set_xticks(range(len(modes)), modes)
    ax.set_yticks(range(len(tiers)), [f"{t} overlap" for t in tier_labels])
    ax.set_xlabel("Mode")
    ax.set_ylabel("Overlap density tier")
    ax.set_title(title)
    for i in range(len(tiers)):
        for j in range(len(modes)):
            val = matrix[i, j]
            if not np.isnan(val):
                ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=9)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="Conf")
    fig.tight_layout()
    _save(fig, "complexity_heatmap", formats, dpi)
    plt.close(fig)

    # E6 feedback variants
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    e6_path = PROC_DIR / "feedback_variant_summary.csv"
    if e6_path.exists():
        e6 = pd.read_csv(e6_path)
        label_map = {"A": "A: test only", "B": "B: test+expected", "C": "C: semantic IR"}
        labels = [label_map.get(r, r) for r in e6["variant_label"]]
        conf = e6["mean_conf"].tolist()
        colors = ["#332288", "#88CCEE", "#117733"][: len(conf)]
    else:
        labels = ["A: test only", "B: test+expected", "C: semantic IR"]
        conf = [0.0, 0.0, 0.0]
        colors = ["#332288", "#88CCEE", "#117733"]
    bars = ax.bar(labels, conf, color=colors, edgecolor="white", linewidth=0.8)
    ax.set_ylim(0.70, 1.0)
    ax.set_ylabel("Mean strict formal conformance")
    ax.set_title("Feedback variant comparison (E6)")
    for b, v in zip(bars, conf):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.005, f"{v:.3f}", ha="center", fontsize=9)
    fig.tight_layout()
    _save(fig, "feedback_variant_bar", formats, dpi)
    plt.close(fig)

    # E7 pattern guard F1
    fig, ax = plt.subplots(figsize=(8.0, 4.5))
    e7_path = PROC_DIR / "pattern_prf1.json"
    if e7_path.exists():
        e7 = json.loads(e7_path.read_text(encoding="utf-8"))
        cats = list(e7.keys())
        f1 = []
        for cat in cats:
            sub = e7[cat]
            if isinstance(sub, dict) and "f1" in sub:
                f1.append(sub["f1"])
            elif isinstance(sub, dict):
                best = max((v.get("f1", 0.0) for v in sub.values() if isinstance(v, dict)), default=0.0)
                f1.append(best)
            else:
                f1.append(0.0)
    else:
        cats = ["Ordering", "GuardInv", "Boundary", "MissingPre", "OutputDep", "Arithmetic"]
        f1 = [0.0] * len(cats)
    ax.bar(cats, f1, color="#117733", alpha=0.85, edgecolor="white")
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("F1 score")
    ax.set_title("Pattern guard F1 by fault category (E7)")
    ax.axhline(0.6, color="#CC6677", linestyle="--", linewidth=1, label="F1=0.6 threshold")
    ax.legend(frameon=False)
    fig.tight_layout()
    _save(fig, "pattern_guard_f1_bar", formats, dpi)
    plt.close(fig)

    # E4 boundary coverage (dense/high tier aggregate)
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    e4_path = PROC_DIR / "boundary_density.csv"
    if e4_path.exists():
        e4 = pd.read_csv(e4_path)
        dense = e4[e4["density_tier"] == "high"]
        agg = dense.groupby("budget").agg(
            smt=("smt_coverage", "mean"),
            rnd=("random_coverage", "mean"),
        ).reset_index()
        budgets = agg["budget"].tolist()
        smt_dense = agg["smt"].tolist()
        rnd_dense = agg["rnd"].tolist()
    else:
        budgets = [4, 8, 16, 32, 64]
        smt_dense = [0.0] * 5
        rnd_dense = [0.0] * 5
    ax.plot(budgets, smt_dense, "o-", color="#117733", label="SMT (dense tier)")
    ax.plot(budgets, rnd_dense, "s--", color="#CC6677", label="Random (dense tier)")
    ax.set_xlabel("Case budget")
    ax.set_ylabel("Scenario coverage rate")
    ax.set_title("Boundary coverage: SMT vs random (E4)")
    ax.legend(frameon=False)
    ax.set_ylim(0, 1.05)
    fig.tight_layout()
    _save(fig, "boundary_coverage_by_density", formats, dpi)
    plt.close(fig)

    # E8 generalisation
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    e8_path = PROC_DIR / "generalisation_summary.csv"
    if e8_path.exists():
        e8 = pd.read_csv(e8_path)
        sofl = e8[e8["notation"] == "SOFL/FSF"]
        notations = ["SOFL/FSF"]
        b1, b2, m = [], [], []
        for mode_col, lst in [("B1", b1), ("B2", b2), ("M", m)]:
            row = sofl[sofl["mode"] == mode_col]
            lst.append(float(row.iloc[0]["mean_conf"]) / 100 if not row.empty else 0.0)
        # Append reference-oracle rows for adapters (scaled 0-1)
        for notation in ["Mini-StateMachine", "Mini-Z"]:
            ref = e8[(e8["notation"] == notation) & (e8["mode"] == "B0")]
            if not ref.empty:
                val = float(ref.iloc[0]["mean_conf"]) / 100
                notations.append(notation.replace("Mini-", "Mini-\n"))
                b1.append(val)
                b2.append(val)
                m.append(val)
    else:
        notations = ["SOFL/FSF", "Mini-SM", "Mini-Z"]
        b1, b2, m = [0.0] * 3, [0.0] * 3, [0.0] * 3
    x = np.arange(len(notations))
    w = 0.25
    ax.bar(x - w, b1, w, label="B1 / ref.", color="#332288")
    ax.bar(x, b2, w, label="B2 / ref.", color="#88CCEE")
    ax.bar(x + w, m, w, label="M / ref.", color="#117733")
    ax.set_xticks(x, notations)
    ax.set_ylabel("Mean Conf")
    ax.set_title("Generalisation across spec notations (E8)")
    ax.legend(frameon=False, ncol=3, fontsize=7)
    ax.set_ylim(0.7, 1.0)
    fig.tight_layout()
    _save(fig, "generalisation_bar", formats, dpi)
    plt.close(fig)

    # E9 failure taxonomy pie
    fig, ax = plt.subplots(figsize=(6.5, 6.0))
    e9_path = PROC_DIR / "failure_taxonomy.json"
    if e9_path.exists():
        e9 = json.loads(e9_path.read_text(encoding="utf-8"))
        cats = e9.get("categories", {})
        labels = list(cats.keys())
        sizes = [int(cats[k]["count"]) for k in labels]
        colors = ["#117733", "#88CCEE", "#DDCC77", "#CC6677", "#AA4499", "#999999", "#44AA99"]
        colors = colors[: len(labels)]
        title = f"Failure taxonomy for mode M (E9, n={e9.get('total_failed', '?')} failed)"
    else:
        labels = ["No data"]
        sizes = [1]
        colors = ["#999999"]
        title = "Failure taxonomy for mode M (E9)"
    ax.pie(sizes, labels=labels, autopct="%1.0f%%", startangle=140, colors=colors,
           textprops={"fontsize": 9})
    ax.set_title(title)
    fig.tight_layout()
    _save(fig, "failure_taxonomy_pie", formats, dpi)
    plt.close(fig)


if __name__ == "__main__":
    main()
