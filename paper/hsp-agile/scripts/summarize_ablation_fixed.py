#!/usr/bin/env python3
"""Summarize fixed-oracle A1/A2/A3 ablation vs M from run_e1_m_win_v2."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def load_conf(run_dir: Path) -> dict[str, list[float]]:
    path = run_dir / "results.jsonl"
    by: dict[str, list[float]] = defaultdict(list)
    for line in path.open(encoding="utf-8"):
        r = json.loads(line)
        mode = r.get("mode", "?")
        conf = r.get("formal_conformance")
        if conf is None:
            conf = r.get("strict_formal_conformance", 0.0)
        by[mode].append(float(conf))
    return by


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--ablation-dir",
        type=Path,
        default=Path("artifacts/run_e1_ablation_fixed_v1"),
    )
    ap.add_argument(
        "--m-dir",
        type=Path,
        default=Path("artifacts/run_e1_m_win_v2"),
        help="Authoritative M (and optional B1/B2) under fixed oracle",
    )
    args = ap.parse_args()

    abl = load_conf(args.ablation_dir)
    m_by = load_conf(args.m_dir)
    m_mean = _mean(m_by.get("M", []))

    print(f"M reference ({args.m_dir.name}): n={len(m_by.get('M', []))} mean={100*m_mean:.1f}%")
    print(f"Ablation ({args.ablation_dir.name}):")
    for mode in ("A1", "A2", "A3"):
        vals = abl.get(mode, [])
        mean = _mean(vals)
        delta_pp = (mean - m_mean) * 100
        print(f"  {mode}: n={len(vals)} mean={100*mean:.1f}%  Δ vs M = {delta_pp:+.1f} pp")


if __name__ == "__main__":
    main()
