"""Generate publication-ready deterministic Plotly figures for HSP-Agile."""

from __future__ import annotations

import argparse
import random
import shutil
import subprocess
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pandas.errors import EmptyDataError
from plotly.subplots import make_subplots

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

PAPER_ROOT = Path(__file__).resolve().parents[2]
PROC_DIR = PAPER_ROOT / "data" / "processed"
FIG_DIR = PAPER_ROOT / "figures"
MODE_ORDER = ["B0", "B1", "B2", "M", "A1", "A2", "A3"]
DEFAULT_SEED = 7
DEFAULT_STATIC_FORMATS = ["png", "pdf"]
FONT_FAMILY = "Arial"
BASE_FONT_SIZE = 13
TITLE_FONT_SIZE = 16
LEGEND_FONT_SIZE = 11
CB_PALETTE = px.colors.qualitative.Safe
FIGURE_IDS = {
    "mode_distribution_strict_conformance",
    "mode_distribution_latency",
    "ablation_contribution_ci",
    "prevention_heatmap_by_mode_eval",
    "pareto_quality_vs_latency",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--static-formats",
        nargs="+",
        default=DEFAULT_STATIC_FORMATS,
        choices=["png", "pdf"],
        help="Static output formats written via plotly+kaleido.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Raster DPI used for static PNG output.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Random seed for deterministic plotting behavior.",
    )
    parser.add_argument(
        "--only",
        nargs="+",
        choices=sorted(FIGURE_IDS),
        help="Optional figure IDs to generate.",
    )
    parser.add_argument(
        "--no-html",
        action="store_true",
        help="Skip interactive HTML export and only write static figures.",
    )
    return parser.parse_args()


def _set_deterministic_seed(seed: int) -> None:
    random.seed(seed)
    if np is not None:
        np.random.seed(seed)


def _safe_read_csv(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path)
    except EmptyDataError:
        return None
    if df.empty:
        return None
    return df


def _ordered_mode_list(values: pd.Series | list[str]) -> list[str]:
    present = [m for m in MODE_ORDER if m in set(values)]
    extra = sorted(m for m in set(values) if m not in set(MODE_ORDER))
    return present + extra


def _mode_color_map(values: pd.Series | list[str]) -> dict[str, str]:
    order = _ordered_mode_list(values)
    return {mode: CB_PALETTE[idx % len(CB_PALETTE)] for idx, mode in enumerate(order)}


def _base_layout(fig: go.Figure, title: str, height: int = 440, width: int = 900) -> go.Figure:
    fig.update_layout(
        title={"text": title, "x": 0.01, "xanchor": "left", "font": {"size": TITLE_FONT_SIZE}},
        template="plotly_white",
        width=width,
        height=height,
        font={"family": FONT_FAMILY, "size": BASE_FONT_SIZE},
        margin={"l": 72, "r": 24, "t": 72, "b": 64},
        legend={
            "title": {"text": ""},
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1.0,
            "font": {"size": LEGEND_FONT_SIZE},
            "itemsizing": "constant",
        },
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(0,0,0,0.08)", zeroline=False, title_standoff=8)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(0,0,0,0.08)", zeroline=False, title_standoff=8)
    return fig


def _empty_figure(message: str, title: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=message, showarrow=False, x=0.5, y=0.5, xref="paper", yref="paper")
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return _base_layout(fig, title=title, height=360, width=760)


def _save_figure(fig: go.Figure, stem: str, static_formats: list[str], dpi: int, write_html: bool = True) -> None:
    html_path = FIG_DIR / f"{stem}.html"
    if write_html:
        fig.write_html(str(html_path), include_plotlyjs="cdn", full_html=True)

    try:
        _save_static_with_kaleido(fig=fig, stem=stem, static_formats=static_formats, dpi=dpi)
    except Exception as exc:
        print(f"[warn] Kaleido export failed for {stem}: {exc}. Falling back to matplotlib renderer.")
        try:
            _save_static_with_matplotlib(fig=fig, stem=stem, static_formats=static_formats, dpi=dpi)
        except Exception as exc2:
            print(f"[warn] matplotlib fallback also failed for {stem}: {exc2}. Trying headless Chrome.")
            if not write_html:
                fig.write_html(str(html_path), include_plotlyjs="cdn", full_html=True)
            try:
                _save_static_with_headless_chrome(html_path=html_path, stem=stem, static_formats=static_formats, dpi=dpi)
            except Exception as exc3:
                print(f"[error] All export methods failed for {stem}: {exc3}")


def _save_static_with_matplotlib(fig: go.Figure, stem: str, static_formats: list[str], dpi: int) -> None:
    """Convert a Plotly figure to matplotlib and save as PDF/PNG.
    
    This fallback uses plotly's to_image with orca if available, otherwise
    renders via an embedded HTML+matplotlib approach.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.backends.backend_pdf import PdfPages

    # Extract data from plotly figure for matplotlib rendering
    fig_dict = fig.to_dict()
    layout = fig_dict.get("layout", {})
    data = fig_dict.get("data", [])
    title = layout.get("title", {}).get("text", stem)
    width_px = layout.get("width", 900)
    height_px = layout.get("height", 440)
    fig_w = width_px / 96
    fig_h = height_px / 96

    mpl_fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_title(title, fontsize=11, loc="left", pad=8)

    # Colorblind-safe palette (matches CB_PALETTE order)
    palette = ["#88CCEE", "#CC6677", "#DDCC77", "#117733", "#332288", "#AA4499", "#44AA99"]

    rendered = False
    for idx, trace in enumerate(data):
        ttype = trace.get("type", "")
        color = palette[idx % len(palette)]
        if ttype == "violin":
            y_vals = trace.get("y")
            x_vals = trace.get("x")
            if y_vals is not None and x_vals is not None:
                import pandas as _pd
                df_tmp = _pd.DataFrame({"x": x_vals, "y": y_vals})
                groups = df_tmp.groupby("x")["y"].apply(list)
                positions = list(range(len(groups)))
                vp = ax.violinplot([groups[k] for k in groups.index], positions=positions, showmedians=True)
                ax.set_xticks(positions)
                ax.set_xticklabels(list(groups.index), fontsize=8)
                rendered = True
        elif ttype == "bar":
            x_vals = trace.get("x", [])
            y_vals = trace.get("y", [])
            if x_vals and y_vals:
                colors = [palette[i % len(palette)] for i in range(len(x_vals))]
                ax.bar(range(len(x_vals)), y_vals, color=colors)
                ax.set_xticks(range(len(x_vals)))
                ax.set_xticklabels(x_vals, fontsize=8)
                rendered = True
        elif ttype == "scatter":
            x_vals = trace.get("x", [])
            y_vals = trace.get("y", [])
            mode = trace.get("mode", "markers")
            label = trace.get("name", "")
            if x_vals and y_vals:
                if "lines" in mode:
                    ax.plot(x_vals, y_vals, label=label, color=color)
                else:
                    ax.scatter(x_vals, y_vals, label=label, color=color, s=40)
                rendered = True
        elif ttype == "heatmap":
            z = trace.get("z")
            if z is not None:
                import numpy as _np
                im = ax.imshow(_np.array(z, dtype=float), aspect="auto", cmap="viridis")
                x_labels = trace.get("x", [])
                y_labels = trace.get("y", [])
                if x_labels:
                    ax.set_xticks(range(len(x_labels)))
                    ax.set_xticklabels(x_labels, fontsize=7)
                if y_labels:
                    ax.set_yticks(range(len(y_labels)))
                    ax.set_yticklabels(y_labels, fontsize=7)
                plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
                rendered = True

    if not rendered:
        ax.text(0.5, 0.5, f"[{stem}]", ha="center", va="center", transform=ax.transAxes, fontsize=12, color="gray")

    x_title = layout.get("xaxis", {}).get("title", {})
    y_title = layout.get("yaxis", {}).get("title", {})
    if isinstance(x_title, dict):
        ax.set_xlabel(x_title.get("text", ""), fontsize=9)
    elif isinstance(x_title, str):
        ax.set_xlabel(x_title, fontsize=9)
    if isinstance(y_title, dict):
        ax.set_ylabel(y_title.get("text", ""), fontsize=9)
    elif isinstance(y_title, str):
        ax.set_ylabel(y_title, fontsize=9)

    handles, labels = ax.get_legend_handles_labels()
    if labels:
        ax.legend(handles, labels, fontsize=7, loc="upper right")

    ax.grid(True, alpha=0.25, linewidth=0.5)
    mpl_fig.tight_layout()

    for fmt in sorted(set(static_formats)):
        out_path = FIG_DIR / f"{stem}.{fmt}"
        if fmt == "pdf":
            with PdfPages(str(out_path)) as pdf:
                pdf.savefig(mpl_fig, dpi=dpi, bbox_inches="tight")
        else:
            mpl_fig.savefig(str(out_path), dpi=dpi, bbox_inches="tight", format=fmt)
    plt.close(mpl_fig)


def _save_static_with_kaleido(fig: go.Figure, stem: str, static_formats: list[str], dpi: int) -> None:
    scale = max(1, round(dpi / 96))
    for fmt in sorted(set(static_formats)):
        out_path = FIG_DIR / f"{stem}.{fmt}"
        fig.write_image(str(out_path), format=fmt, scale=scale)


def _find_chrome_binary() -> str | None:
    candidates = [
        Path.home() / "AppData" / "Local" / "plotly" / "choreographer" / "deps" / "chrome-win64" / "chrome.exe",
        Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
        Path("C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"),
        Path("C:/Program Files/Microsoft/Edge/Application/msedge.exe"),
        Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    for cmd in ["chrome", "chrome.exe", "msedge", "msedge.exe"]:
        browser = shutil.which(cmd)
        if browser:
            return browser
    return None


def _save_static_with_headless_chrome(html_path: Path, stem: str, static_formats: list[str], dpi: int) -> None:
    browser = _find_chrome_binary()
    if not browser:
        raise RuntimeError("No Chrome/Edge executable found for static export fallback.")
    file_url = html_path.resolve().as_uri()
    width = 960
    height = 540
    scale = max(1, round(dpi / 96))

    for fmt in sorted(set(static_formats)):
        out_path = FIG_DIR / f"{stem}.{fmt}"
        if fmt == "png":
            cmd = [
                browser,
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--hide-scrollbars",
                f"--force-device-scale-factor={scale}",
                f"--window-size={width},{height}",
                "--virtual-time-budget=5000",
                f"--screenshot={out_path}",
                file_url,
            ]
        elif fmt == "pdf":
            cmd = [
                browser,
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--hide-scrollbars",
                "--virtual-time-budget=5000",
                f"--print-to-pdf={out_path}",
                file_url,
            ]
        else:  # pragma: no cover - guarded by argparse choices
            continue
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _plot_mode_distribution(metric: str, static_formats: list[str], dpi: int, write_html: bool) -> None:
    df = _safe_read_csv(PROC_DIR / "distribution_by_mode.csv")
    metric_label = "Strict Conformance" if metric == "strict_conformance" else "Latency (ms)"
    fig_id = "mode_distribution_strict_conformance" if metric == "strict_conformance" else "mode_distribution_latency"
    title = f"{metric_label} Distribution by Mode"
    if df is None or metric not in df.columns:
        _save_figure(_empty_figure("Distribution data unavailable", title), fig_id, static_formats, dpi, write_html=write_html)
        return

    order = _ordered_mode_list(df["mode"])
    color_map = _mode_color_map(df["mode"])
    mode_counts = df.groupby("mode").size().to_dict()
    fig = px.violin(
        df,
        x="mode",
        y=metric,
        color="mode",
        category_orders={"mode": order},
        color_discrete_map=color_map,
        box=True,
        points="suspectedoutliers",
        hover_data=["mode", metric],
    )
    fig.update_traces(
        meanline_visible=True,
        opacity=0.80,
        marker={"size": 3, "opacity": 0.45},
        line={"width": 1.0},
    )
    fig.update_layout(showlegend=False)
    fig.update_xaxes(
        title="Mode",
        categoryorder="array",
        categoryarray=order,
        tickvals=order,
        ticktext=[f"{m}<br>(n={mode_counts.get(m, 0)})" for m in order],
    )
    if metric == "strict_conformance":
        fig.update_yaxes(title="Strict Conformance", range=[0.0, 1.0], tickformat=".0%")
    else:
        fig.update_yaxes(title="Latency (ms, log scale)", type="log")
    _save_figure(_base_layout(fig, title=title), fig_id, static_formats, dpi, write_html=write_html)


def _plot_ablation_contribution(static_formats: list[str], dpi: int, write_html: bool) -> None:
    df = _safe_read_csv(PROC_DIR / "ablation_contribution.csv")
    if df is None:
        _save_figure(
            _empty_figure("Ablation data unavailable (needs M and ablation modes)", "Ablation Contribution vs M"),
            "ablation_contribution_ci",
            static_formats,
            dpi,
            write_html=write_html,
        )
        return

    order = _ordered_mode_list(df["mode"])
    df = df.copy()
    df["mode"] = pd.Categorical(df["mode"], categories=order, ordered=True)
    df = df.sort_values("mode")
    color_map = _mode_color_map(df["mode"].astype(str).tolist())
    baseline_mode = str(df["baseline_mode"].iloc[0]) if "baseline_mode" in df.columns and not df.empty else "M"
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df["mode"],
            y=df["delta_vs_baseline"],
            error_y={
                "type": "data",
                "symmetric": False,
                "array": df["ci_high"] - df["delta_vs_baseline"],
                "arrayminus": df["delta_vs_baseline"] - df["ci_low"],
                "visible": True,
                "thickness": 1.2,
                "width": 4,
            },
            marker_color=[color_map[str(mode)] for mode in df["mode"]],
            customdata=df[["success_rate", "baseline_success_rate", "n", "baseline_n", "ci_method"]].values,
            text=[f"{v:+.2%}" for v in df["delta_vs_baseline"]],
            textposition="outside",
            hovertemplate=(
                "Mode=%{x}<br>"
                f"Delta vs {baseline_mode}=%{{y:.3f}}<br>"
                "Mode success=%{customdata[0]:.3f} (n=%{customdata[2]})<br>"
                "Baseline success=%{customdata[1]:.3f} (n=%{customdata[3]})<br>"
                "CI method=%{customdata[4]}<extra></extra>"
            ),
        )
    )
    fig.add_hline(y=0.0, line_width=1.2, line_color="black", line_dash="dot")
    fig.update_xaxes(title="Ablation Mode", categoryorder="array", categoryarray=order)
    fig.update_yaxes(title=f"Delta Strict Success vs {baseline_mode}", tickformat="+.0%")
    _save_figure(
        _base_layout(fig, title=f"Ablation Contribution with 95% CI (vs {baseline_mode})"),
        "ablation_contribution_ci",
        static_formats,
        dpi,
        write_html=write_html,
    )


def _plot_prevention_heatmap(static_formats: list[str], dpi: int, write_html: bool) -> None:
    df = _safe_read_csv(PROC_DIR / "prevention_heatmap.csv")
    if df is None:
        _save_figure(
            _empty_figure("Prevention heatmap data unavailable", "Prevention by Mode x Eval Type"),
            "prevention_heatmap_by_mode_eval",
            static_formats,
            dpi,
            write_html=write_html,
        )
        return

    mode_order = _ordered_mode_list(df["mode"])
    eval_order = sorted(df["eval_type"].unique())
    detection = (
        df.pivot(index="eval_type", columns="mode", values="detection_rate")
        .reindex(index=eval_order, columns=mode_order)
        .fillna(0.0)
    )
    far = (
        df.pivot(index="eval_type", columns="mode", values="false_accept_rate")
        .reindex(index=eval_order, columns=mode_order)
        .fillna(0.0)
    )
    n_obs = (
        df.pivot(index="eval_type", columns="mode", values="n")
        .reindex(index=eval_order, columns=mode_order)
        .fillna(0)
    )

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Detection Rate", "False Accept Rate"),
        horizontal_spacing=0.10,
    )
    fig.add_trace(
        go.Heatmap(
            z=detection.values,
            x=detection.columns.tolist(),
            y=detection.index.tolist(),
            zmin=0.0,
            zmax=1.0,
            colorscale="Cividis",
            colorbar={"title": "Detection", "len": 0.9, "thickness": 12},
            text=detection.values,
            texttemplate="%{text:.2f}",
            textfont={"size": 10},
            customdata=n_obs.values,
            hovertemplate="Mode=%{x}<br>Eval=%{y}<br>Detection=%{z:.3f}<br>n=%{customdata}<extra></extra>",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Heatmap(
            z=far.values,
            x=far.columns.tolist(),
            y=far.index.tolist(),
            zmin=0.0,
            zmax=1.0,
            colorscale="Cividis_r",
            showscale=False,
            text=far.values,
            texttemplate="%{text:.2f}",
            textfont={"size": 10},
            customdata=n_obs.values,
            hovertemplate="Mode=%{x}<br>Eval=%{y}<br>FAR=%{z:.3f}<br>n=%{customdata}<extra></extra>",
        ),
        row=1,
        col=2,
    )
    fig.update_xaxes(title="Mode", row=1, col=1)
    fig.update_xaxes(title="Mode", row=1, col=2)
    fig.update_yaxes(title="Eval Type", row=1, col=1)
    fig.update_yaxes(title="Eval Type", row=1, col=2)
    _save_figure(
        _base_layout(fig, title="Prevention Heatmap by Mode x Eval Type", height=500),
        "prevention_heatmap_by_mode_eval",
        static_formats,
        dpi,
        write_html=write_html,
    )


def _compute_pareto_frontier(df: pd.DataFrame) -> pd.DataFrame:
    sorted_df = df.sort_values("latency_ms").reset_index(drop=True)
    frontier_rows: list[dict[str, float | str]] = []
    best_quality = float("-inf")
    for _, row in sorted_df.iterrows():
        quality = float(row["quality"])
        if quality >= best_quality:
            frontier_rows.append({"mode": row["mode"], "latency_ms": row["latency_ms"], "quality": quality})
            best_quality = quality
    return pd.DataFrame(frontier_rows)


def _plot_pareto(static_formats: list[str], dpi: int, write_html: bool) -> None:
    df = _safe_read_csv(PROC_DIR / "pareto_by_mode.csv")
    if df is None:
        _save_figure(
            _empty_figure("Pareto data unavailable", "Pareto: Quality vs Latency"),
            "pareto_quality_vs_latency",
            static_formats,
            dpi,
            write_html=write_html,
        )
        return

    order = _ordered_mode_list(df["mode"])
    color_map = _mode_color_map(df["mode"])
    fig = px.scatter(
        df,
        x="latency_ms",
        y="quality",
        color="mode",
        category_orders={"mode": order},
        color_discrete_map=color_map,
        size="n",
        text="mode",
        hover_data=["success_rate", "strict_failures", "n"],
        labels={"latency_ms": "Latency (ms)", "quality": "Strict Conformance"},
    )
    frontier = _compute_pareto_frontier(df)
    if not frontier.empty:
        fig.add_trace(
            go.Scatter(
                x=frontier["latency_ms"],
                y=frontier["quality"],
                mode="lines+markers",
                name="Pareto Frontier",
                line={"dash": "dash", "width": 2, "color": "black"},
                marker={"size": 8, "color": "black"},
                hovertemplate="Latency=%{x:.2f} ms<br>Quality=%{y:.3f}<extra>Pareto</extra>",
            )
        )
    fig.update_traces(textposition="top center", marker={"line": {"color": "white", "width": 0.8}})
    fig.update_xaxes(type="log", title="Latency (ms, log scale)")
    fig.update_yaxes(title="Strict Conformance", range=[0.0, 1.0], tickformat=".0%")
    _save_figure(
        _base_layout(fig, title="Pareto Chart: Quality vs Latency"),
        "pareto_quality_vs_latency",
        static_formats,
        dpi,
        write_html=write_html,
    )


def main() -> None:
    args = _parse_args()
    _set_deterministic_seed(args.seed)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    selected = set(args.only) if args.only else FIGURE_IDS
    write_html = not args.no_html

    if "mode_distribution_strict_conformance" in selected:
        _plot_mode_distribution(
            metric="strict_conformance",
            static_formats=args.static_formats,
            dpi=args.dpi,
            write_html=write_html,
        )
    if "mode_distribution_latency" in selected:
        _plot_mode_distribution(
            metric="latency_ms",
            static_formats=args.static_formats,
            dpi=args.dpi,
            write_html=write_html,
        )
    if "ablation_contribution_ci" in selected:
        _plot_ablation_contribution(static_formats=args.static_formats, dpi=args.dpi, write_html=write_html)
    if "prevention_heatmap_by_mode_eval" in selected:
        _plot_prevention_heatmap(static_formats=args.static_formats, dpi=args.dpi, write_html=write_html)
    if "pareto_quality_vs_latency" in selected:
        _plot_pareto(static_formats=args.static_formats, dpi=args.dpi, write_html=write_html)

    print(f"Figures written to: {FIG_DIR}")
    print(f"Interactive format: {'html' if write_html else 'disabled (--no-html)'}")
    print(f"Static formats: {', '.join(sorted(set(args.static_formats)))}")
    print(f"Seed: {args.seed}")


if __name__ == "__main__":
    main()
