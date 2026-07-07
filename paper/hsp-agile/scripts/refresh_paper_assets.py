"""Refresh processed data and regenerate all paper figures."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PAPER_ROOT = Path(__file__).resolve().parents[1]
PREPARE_SCRIPT = PAPER_ROOT / "scripts" / "prepare_paper_data.py"
MECHANISM_SCRIPT = PAPER_ROOT / "scripts" / "prepare_mechanism_data.py"
# Prefer the matplotlib-based generator (no Kaleido/Chrome dependency)
PLOT_SCRIPT = PAPER_ROOT / "figures" / "scripts" / "plot_mpl_figures.py"
PLOT_SCRIPT_FALLBACK = PAPER_ROOT / "figures" / "scripts" / "plot_paper_figures.py"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--static-formats",
        nargs="+",
        default=["png", "pdf"],
        choices=["png", "pdf"],
        help="Figure output formats passed through to the plot script.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Raster DPI passed through to the plot script.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=7,
        help="Deterministic seed passed through to the plot script.",
    )
    parser.add_argument(
        "--skip-data-refresh",
        action="store_true",
        help="Skip prepare_paper_data.py and only regenerate figures.",
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=None,
        help="Explicit experiment run directory passed to prepare_paper_data.py.",
    )
    parser.add_argument(
        "--prevention-summary",
        type=Path,
        default=None,
        help="Explicit prevention_summary.json passed to prepare_paper_data.py.",
    )
    return parser.parse_args()


def _run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> None:
    args = _parse_args()
    python = sys.executable

    if not args.skip_data_refresh:
        prep_cmd = [python, str(PREPARE_SCRIPT)]
        if args.run_dir is not None:
            prep_cmd.extend(["--run-dir", str(args.run_dir)])
        if args.prevention_summary is not None:
            prep_cmd.extend(["--prevention-summary", str(args.prevention_summary)])
        _run(prep_cmd)

        mech_cmd = [python, str(MECHANISM_SCRIPT)]
        if args.run_dir is not None:
            mech_cmd.extend(["--run-dir", str(args.run_dir)])
        if args.prevention_summary is not None:
            mech_cmd.extend(["--prevention-dir", str(args.prevention_summary)])
        _run(mech_cmd)

    active_plot_script = PLOT_SCRIPT if PLOT_SCRIPT.exists() else PLOT_SCRIPT_FALLBACK
    _run(
        [
            python,
            str(active_plot_script),
            "--formats",
            *args.static_formats,
            "--dpi",
            str(args.dpi),
        ]
    )

    print("Paper assets refresh complete.")


if __name__ == "__main__":
    main()
