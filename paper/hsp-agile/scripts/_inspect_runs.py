#!/usr/bin/env python3
"""Quick inspect of E6 / E1 run artifacts."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / "artifacts"


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def summarize_modes(name: str) -> None:
    p = ART / name / "results.jsonl"
    if not p.exists():
        print(f"{name}: MISSING")
        return
    rows = load_jsonl(p)
    modes: dict[str, dict] = {}
    for r in rows:
        m = r.get("mode") or "?"
        if m not in modes:
            modes[m] = {
                "n": 0,
                "k": r.get("configured_max_attempts") or r.get("max_attempts"),
                "fb": r.get("feedback_variant"),
                "conf": [],
            }
        modes[m]["n"] += 1
        c = r.get("strict_formal_conformance", r.get("formal_conformance"))
        if c is not None:
            modes[m]["conf"].append(float(c))
    print(f"=== {name} ({len(rows)} rows)")
    for m, d in sorted(modes.items()):
        mean = sum(d["conf"]) / len(d["conf"]) if d["conf"] else None
        mean_s = f"{100 * mean:.1f}" if mean is not None else "NA"
        print(f"  {m}: n={d['n']} K={d['k']} fb={d['fb']} meanConf={mean_s}")


def summarize_feedback(name: str) -> None:
    p = ART / name / "results.jsonl"
    if not p.exists():
        # try nested
        cands = list((ART / name).rglob("results.jsonl")) if (ART / name).exists() else []
        print(f"{name}: MISSING top-level; nested={ [str(c) for c in cands[:5]] }")
        return
    rows = load_jsonl(p)
    print(f"=== {name} n={len(rows)} keys={sorted(rows[0].keys())[:25]}")
    vars_ = defaultdict(list)
    for r in rows:
        v = r.get("feedback_variant") or r.get("variant") or "?"
        c = r.get("strict_formal_conformance", r.get("formal_conformance"))
        if c is not None:
            vars_[v].append(float(c))
    for v, vals in sorted(vars_.items()):
        print(f"  {v}: n={len(vals)} mean={100 * sum(vals)/len(vals):.1f}%")


def main() -> None:
    for name in [
        "run_feedback_v2",
        "run_feedback_v1",
        "run_e6_ecnu_max_v1",
        "run_e1_m_win_v2",
        "run_hard_full_parallel_v1",
        "run_e1_canonical_v1",
    ]:
        if "feedback" in name or "e6" in name:
            summarize_feedback(name)
        else:
            summarize_modes(name)


if __name__ == "__main__":
    main()
