"""Post-hoc power analysis for paired Wilcoxon comparisons (REV-5)."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm, wilcoxon

PAPER_ROOT = Path(__file__).resolve().parents[1]
PROC = PAPER_ROOT / "data" / "processed"
CSV = PAPER_ROOT / "data" / "raw" / "results_raw.csv"


def _cliffs_delta(x: np.ndarray, y: np.ndarray) -> float:
    n, m = len(x), len(y)
    if n == 0 or m == 0:
        return 0.0
    gt = sum(1 for a in x for b in y if a > b)
    lt = sum(1 for a in x for b in y if a < b)
    return (gt - lt) / (n * m)


def _approx_power(n: int, delta: float, alpha: float = 0.05) -> float:
    """Normal approximation for paired Wilcoxon power."""
    if n <= 1 or delta == 0:
        return alpha
    z_alpha = norm.ppf(1 - alpha / 2)
    effect = abs(delta) * math.sqrt(n)
    z_beta = effect - z_alpha
    return float(norm.cdf(z_beta))


def _n_for_power(delta: float, power: float = 0.8, alpha: float = 0.05) -> int:
    z_alpha = norm.ppf(1 - alpha / 2)
    z_beta = norm.ppf(power)
    if abs(delta) < 1e-9:
        return 10**9
    return int(math.ceil(((z_alpha + z_beta) / abs(delta)) ** 2))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--csv", type=Path, default=CSV)
    p.add_argument("--out", type=Path, default=PROC / "power_analysis.json")
    args = p.parse_args()

    df = pd.read_csv(args.csv)
    if "repeat" in df.columns:
        df = df[df["repeat"] == 0]
    conf_col = "strict_formal_conformance" if "strict_formal_conformance" in df.columns else "formal_conformance"

    results: dict[str, object] = {"n": 120, "comparisons": {}}
    for other in ["B1", "B2"]:
        m = df[df["mode"] == "M"].set_index("task_id")[conf_col]
        o = df[df["mode"] == other].set_index("task_id")[conf_col]
        common = m.index.intersection(o.index)
        x = m.loc[common].to_numpy()
        y = o.loc[common].to_numpy()
        delta = _cliffs_delta(x, y)
        try:
            _, pval = wilcoxon(x, y)
        except ValueError:
            pval = 1.0
        results["comparisons"][f"M_vs_{other}"] = {
            "cliffs_delta": delta,
            "wilcoxon_p": float(pval),
            "observed_power_approx": _approx_power(len(common), delta),
            "n_for_80pct_power": _n_for_power(delta),
        }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
