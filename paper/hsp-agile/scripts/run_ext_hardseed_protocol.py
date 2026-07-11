#!/usr/bin/env python3
"""Execute E6_EXT_HARDSEED_PROTOCOL on archived hard-seed JSONL runs.

Filters to headroom (test_only Conf < 1), pairs semantic_ir vs test_only,
and writes artifacts/run_ext_hardseed_e6_v2/ summary for the paper.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "artifacts" / "run_ext_hardseed_e6_v2"
SOURCES = [
    ("hkca09_v1", ROOT / "artifacts" / "run_hkca09_hard_seed_e6_v1" / "results.jsonl"),
    ("hkca09_v2", ROOT / "artifacts" / "run_hkca09_hard_seed_e6_v2" / "results.jsonl"),
    ("hkca09_wrong_relop_gemini", ROOT / "artifacts" / "run_hkca09_wrong_relop_gemini_v1" / "results.jsonl"),
    ("hkca09_wrong_relop_gemini_v2", ROOT / "artifacts" / "run_hkca09_wrong_relop_gemini_v2" / "results.jsonl"),
    ("github_wrong_relop_gemini", ROOT / "artifacts" / "run_github_wrong_relop_gemini_v1" / "results.jsonl"),
    ("realspec_ecnu", ROOT / "artifacts" / "run_ir_hard_seed_realspec_ecnu_v1" / "results.jsonl"),
    ("realspec_wrong_relop_gemini", ROOT / "artifacts" / "run_ir_hard_seed_realspec_wrong_relop_gemini_full_v1" / "results.jsonl"),
    ("industrial_gemini", ROOT / "artifacts" / "run_industrial_hard_seed_gemini_v1" / "results.jsonl"),
]


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n <= 0:
        return (0.0, 0.0)
    p = k / n
    den = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((centre - margin) / den, (centre + margin) / den)


def bootstrap_ci(deltas: np.ndarray, B: int = 5000, seed: int = 42) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    if len(deltas) == 0:
        return (float("nan"), float("nan"))
    means = []
    for _ in range(B):
        sample = rng.choice(deltas, size=len(deltas), replace=True)
        means.append(float(np.mean(sample)))
    lo, hi = np.percentile(means, [2.5, 97.5])
    return (float(lo), float(hi))


def load_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def conf_of(row: dict) -> float | None:
    for key in (
        "formal_conformance",
        "final_conf",
        "conf",
        "mean_conf",
        "conformance",
    ):
        if key in row and row[key] is not None:
            return float(row[key])
    return None


def variant_of(row: dict) -> str | None:
    v = row.get("feedback_variant") or row.get("variant") or row.get("feedback")
    if v is None:
        return None
    return str(v)


def pair_key(row: dict) -> tuple:
    return (
        row.get("task_id") or row.get("taskId"),
        row.get("seed_type") or row.get("seed") or "default",
        row.get("model") or "unknown",
    )


def summarise(pairs: list[dict], label: str) -> dict:
    deltas = np.array([p["delta"] for p in pairs], dtype=float)
    wins = int(np.sum(deltas > 1e-9))
    losses = int(np.sum(deltas < -1e-9))
    ties = int(len(deltas) - wins - losses)
    mean_delta = float(np.mean(deltas)) if len(deltas) else float("nan")
    ci = bootstrap_ci(deltas * 100.0)  # pp
    try:
        # Wilcoxon needs non-zero diffs; use zeros kept for ties
        w_p = float(stats.wilcoxon(deltas, zero_method="wilcox", alternative="two-sided").pvalue) if wins + losses >= 1 else float("nan")
    except Exception:
        w_p = float("nan")
    d_n = wins + losses
    d_rate = wins / d_n if d_n else float("nan")
    d_lo, d_hi = wilson(wins, d_n) if d_n else (float("nan"), float("nan"))
    return {
        "label": label,
        "n": len(pairs),
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "mean_delta_pp": mean_delta * 100.0,
        "ci95_pp": [ci[0], ci[1]],
        "ci_excludes_0": bool(ci[0] > 0 or ci[1] < 0) if len(deltas) else False,
        "wilcoxon_p": w_p,
        "decisive_n": d_n,
        "decisive_win_rate": d_rate,
        "decisive_wilson": [d_lo, d_hi],
        "mean_test_only": float(np.mean([p["a"] for p in pairs])) if pairs else float("nan"),
        "mean_semantic_ir": float(np.mean([p["c"] for p in pairs])) if pairs else float("nan"),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    by_source = {}
    all_pairs = []
    for name, path in SOURCES:
        rows = load_rows(path)
        grouped: dict[tuple, dict[str, float]] = defaultdict(dict)
        meta: dict[tuple, dict] = {}
        for r in rows:
            v = variant_of(r)
            c = conf_of(r)
            if v is None or c is None:
                continue
            # normalize variant names
            vl = v.lower()
            if vl in ("a", "test_only", "test-only"):
                key_v = "test_only"
            elif vl in ("c", "full", "semantic_ir", "semantic-ir"):
                key_v = "semantic_ir"
            else:
                continue
            k = pair_key(r)
            grouped[k][key_v] = c
            meta[k] = {
                "task_id": k[0],
                "seed_type": k[1],
                "model": k[2],
                "source": name,
            }
        pairs = []
        for k, vals in grouped.items():
            if "test_only" not in vals or "semantic_ir" not in vals:
                continue
            a, c = vals["test_only"], vals["semantic_ir"]
            # Protocol headroom filter
            if not (a < 1.0 - 1e-12):
                continue
            pairs.append(
                {
                    **meta[k],
                    "a": a,
                    "c": c,
                    "delta": c - a,
                }
            )
        by_source[name] = summarise(pairs, name)
        by_source[name]["pairs"] = pairs
        all_pairs.extend(pairs)

    # Deduplicate identical (task, seed, model) keeping first
    seen = set()
    uniq = []
    for p in all_pairs:
        key = (p["task_id"], p["seed_type"], p["model"])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(p)

    # Primary protocol report: wrong_relop family + pooled headroom
    by_seed: dict[str, list] = defaultdict(list)
    for p in uniq:
        by_seed[str(p["seed_type"])].append(p)

    report = {
        "protocol": "E6_EXT_HARDSEED_PROTOCOL",
        "filter": "test_only Conf < 1",
        "comparison": "semantic_ir - test_only",
        "n_sources_scanned": len(SOURCES),
        "n_unique_pairs_headroom": len(uniq),
        "pooled_headroom": summarise(uniq, "pooled_headroom"),
        "by_seed_type": {s: summarise(ps, s) for s, ps in sorted(by_seed.items())},
        "by_source": {k: {kk: vv for kk, vv in v.items() if kk != "pairs"} for k, v in by_source.items()},
        "primary_claim_family": "wrong_relop",
    }
    # Prefer wrong_relop if n>=15; else pooled
    wr = by_seed.get("wrong_relop", [])
    report["primary"] = summarise(wr, "wrong_relop_headroom") if len(wr) >= 15 else report["pooled_headroom"]
    report["meets_n30"] = bool(report["primary"]["n"] >= 30)

    (OUT / "protocol_summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    # CSV of pairs
    lines = ["task_id,seed_type,model,source,test_only,semantic_ir,delta"]
    for p in uniq:
        lines.append(
            f"{p['task_id']},{p['seed_type']},{p['model']},{p['source']},{p['a']:.6f},{p['c']:.6f},{p['delta']:.6f}"
        )
    (OUT / "headroom_pairs.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # LaTeX snippet row
    prim = report["primary"]
    status = "Significant support" if prim.get("ci_excludes_0") and prim["mean_delta_pp"] > 0 else (
        "Mixed / null" if prim["n"] >= 15 else "Insufficient after filter"
    )
    tex = f"""% Auto-generated by scripts/run_ext_hardseed_protocol.py — do not hand-edit numbers.
% Inserted into e6_ext_multi_status via paper sync.
% Primary: {prim['label']} n={prim['n']} delta={prim['mean_delta_pp']:.1f}pp W/L/T={prim['wins']}/{prim['losses']}/{prim['ties']}
"""
    (OUT / "tex_note.tex").write_text(tex, encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("n_unique_pairs_headroom", "meets_n30", "primary", "by_seed_type")}, indent=2))


if __name__ == "__main__":
    main()
