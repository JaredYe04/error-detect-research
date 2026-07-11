#!/usr/bin/env python3
"""Paired summary for real/headroom E6 feedback_variants results."""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _bootstrap_ci(deltas: list[float], *, b: int = 5000, seed: int = 42) -> tuple[float, float]:
    if not deltas:
        return 0.0, 0.0
    rng = random.Random(seed)
    n = len(deltas)
    means = []
    for _ in range(b):
        sample = [deltas[rng.randrange(n)] for _ in range(n)]
        means.append(_mean(sample))
    means.sort()
    lo = means[int(0.025 * b)]
    hi = means[int(0.975 * b)]
    return lo, hi


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--results",
        type=Path,
        default=ROOT / "artifacts" / "run_real_e6_headroom_v1" / "feedback_variants" / "results.jsonl",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT
        / "paper"
        / "hsp-agile"
        / "artifacts"
        / "strengthening_sprint"
        / "agent_d_industrial"
        / "REAL_E6_HEADROOM_PAIRED.json",
    )
    ap.add_argument("--metric", default="formal_conformance")
    args = ap.parse_args()

    if not args.results.exists():
        print(f"missing {args.results}")
        return 2

    rows = [json.loads(l) for l in args.results.read_text(encoding="utf-8").splitlines() if l.strip()]
    by_var: dict[str, dict[str, float]] = defaultdict(dict)
    for r in rows:
        var = r.get("feedback_variant") or r.get("variant") or r.get("mode")
        tid = r.get("task_id")
        if var is None or tid is None:
            continue
        by_var[str(var)][str(tid)] = float(r.get(args.metric) or 0)

    summary = {"n_rows": len(rows), "metric": args.metric, "variants": {}, "paired": {}}
    for var, scores in by_var.items():
        vals = list(scores.values())
        summary["variants"][var] = {
            "n": len(vals),
            "mean": round(_mean(vals), 4),
            "strict_rate": round(
                _mean([1.0 if v >= 1.0 - 1e-12 else 0.0 for v in vals]), 4
            ),
        }

    focal = "semantic_ir"
    for comp in ("test_only", "test_expected"):
        if focal not in by_var or comp not in by_var:
            continue
        common = sorted(set(by_var[focal]) & set(by_var[comp]))
        deltas = [by_var[focal][t] - by_var[comp][t] for t in common]
        wins = sum(1 for d in deltas if d > 1e-12)
        losses = sum(1 for d in deltas if d < -1e-12)
        ties = len(deltas) - wins - losses
        lo, hi = _bootstrap_ci(deltas)
        summary["paired"][f"{focal}_vs_{comp}"] = {
            "n": len(common),
            "mean_delta": round(_mean(deltas), 4),
            "wins": wins,
            "losses": losses,
            "ties": ties,
            "ci95": [round(lo, 4), round(hi, 4)],
            "excl0": bool(lo > 0 or hi < 0),
        }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    md = args.out.with_suffix(".md")
    lines = [
        "# Real / headroom E6 paired summary",
        "",
        f"Source: `{args.results.as_posix()}`",
        "",
        "## Means",
        "",
    ]
    for var, st in summary["variants"].items():
        lines.append(f"- **{var}**: mean Conf {100*st['mean']:.1f}% (n={st['n']})")
    lines += ["", "## Paired", ""]
    for k, p in summary["paired"].items():
        lines.append(
            f"- **{k}**: Δ={100*p['mean_delta']:+.1f} pp; W/L/T {p['wins']}/{p['losses']}/{p['ties']}; "
            f"CI95 [{100*p['ci95'][0]:+.1f}, {100*p['ci95'][1]:+.1f}]; excl0={p['excl0']}"
        )
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"-> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
