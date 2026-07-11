#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Summarize RealSpec B1/B2/M run + optional join to source_type."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = (
    ROOT
    / "paper"
    / "hsp-agile"
    / "artifacts"
    / "strengthening_sprint"
    / "agent_c_realspec"
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--results",
        type=Path,
        default=ROOT / "artifacts" / "run_realspec_v1_b1b2m" / "results.jsonl",
    )
    ap.add_argument(
        "--benchmark",
        type=Path,
        default=ROOT / "benchmarks" / "realspec" / "realspec_v1.json",
    )
    ap.add_argument("--out-dir", type=Path, default=OUT)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    if not args.results.exists():
        print(f"Waiting for {args.results}")
        return

    tasks = {t["taskId"]: t for t in json.loads(args.benchmark.read_text(encoding="utf-8"))}
    rows = [json.loads(l) for l in args.results.read_text(encoding="utf-8").splitlines() if l.strip()]

    by_mode: dict[str, list[float]] = defaultdict(list)
    by_src_mode: dict[tuple[str, str], list[float]] = defaultdict(list)
    for r in rows:
        mode = str(r.get("mode"))
        tid = r.get("task_id")
        conf = float(r.get("formal_conformance") or 0.0)
        by_mode[mode].append(conf)
        src = (tasks.get(tid) or {}).get("realspec", {}).get("source_type", "unknown")
        by_src_mode[(src, mode)].append(conf)

    summary = {
        "n_rows": len(rows),
        "mean_conf_by_mode": {
            m: round(sum(xs) / len(xs), 4) for m, xs in sorted(by_mode.items())
        },
        "n_by_mode": {m: len(xs) for m, xs in sorted(by_mode.items())},
        "mean_conf_by_source_mode": {
            f"{s}|{m}": round(sum(xs) / len(xs), 4)
            for (s, m), xs in sorted(by_src_mode.items())
        },
    }
    (args.out_dir / "realspec_b1b2m_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    lines = [
        "# RealSpec B1/B2/M Summary",
        "",
        f"Rows={summary['n_rows']}",
        "",
        "## Mean Conf by mode",
        "```json",
        json.dumps(summary["mean_conf_by_mode"], indent=2),
        "```",
        "",
        "## By source_type × mode",
        "```json",
        json.dumps(summary["mean_conf_by_source_mode"], indent=2),
        "```",
        "",
        "## Reading for C4",
        "If B2 >= M on mean Conf for industrial/textbook slices, that supports default-B2.",
        "If M leads only on a source_type, escalate selectively.",
    ]
    (args.out_dir / "REALSPEC_RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
