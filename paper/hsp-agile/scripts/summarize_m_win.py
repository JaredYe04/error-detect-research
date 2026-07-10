"""Aggregate run_e1_m_win_v1 (or any results.jsonl) and print paper-ready stats."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def load_rows(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", type=Path, required=True)
    args = ap.parse_args()
    rows = load_rows(args.run_dir / "results.jsonl")
    by_mode: dict[str, list[float]] = defaultdict(list)
    by_task: dict[str, dict[str, float]] = defaultdict(dict)
    for r in rows:
        conf = float(r["strict_formal_conformance"])
        by_mode[r["mode"]].append(conf)
        by_task[r["task_id"]][r["mode"]] = conf

    print(f"run_dir={args.run_dir} n_rows={len(rows)}")
    for mode in sorted(by_mode):
        vals = by_mode[mode]
        mean = sum(vals) / len(vals)
        strict = sum(1 for v in vals if v >= 1.0 - 1e-12) / len(vals)
        print(f"  {mode}: n={len(vals)} Conf={100*mean:.1f}% Strict={100*strict:.1f}%")

    if "M" in by_mode and "B2" in by_mode:
        mw = bw = ties = 0
        deltas = []
        for tid, d in by_task.items():
            if "M" not in d or "B2" not in d:
                continue
            delta = d["M"] - d["B2"]
            deltas.append(delta)
            if delta > 1e-9:
                mw += 1
            elif delta < -1e-9:
                bw += 1
            else:
                ties += 1
        m_mean = sum(by_mode["M"]) / len(by_mode["M"])
        b2_mean = sum(by_mode["B2"]) / len(by_mode["B2"])
        print(
            f"  M vs B2: delta={100*(m_mean-b2_mean):+.1f}pp "
            f"wins={mw}/{mw+bw+ties} losses={bw} ties={ties}"
        )


if __name__ == "__main__":
    main()
