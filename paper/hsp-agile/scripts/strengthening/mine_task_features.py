#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mine per-task features + E6 winner labels from existing artifacts.

Primary inputs:
  benchmarks/hard_tasks_annotated.json
  artifacts/run_feedback_v2/feedback_variants/results.jsonl

Optional secondary winner labels:
  artifacts/run_e1_m_win_v2/results.jsonl
  artifacts/run_e1_equal_k_v1/results.jsonl
  artifacts/run_e14_sweep_v1/results.jsonl

Outputs (default):
  paper/hsp-agile/artifacts/strengthening_sprint/agent_a_evidence/
    task_feature_db.csv / .json
    winner_feature_summary.json
    winner_feature_tables.md
    FINDINGS.md
    optional overlap_vs_delta.png, scenario_count_vs_delta.png
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

# .../paper/hsp-agile/scripts/strengthening/this_file.py ???repo root = parents[4]
ROOT = Path(__file__).resolve().parents[4]
DEFAULT_TASKS = ROOT / "benchmarks" / "hard_tasks_annotated.json"
DEFAULT_E6 = ROOT / "artifacts" / "run_feedback_v2" / "feedback_variants" / "results.jsonl"
DEFAULT_OUT = (
    ROOT
    / "paper"
    / "hsp-agile"
    / "artifacts"
    / "strengthening_sprint"
    / "agent_a_evidence"
)

EPS = 1e-12
REL_OPS = re.compile(r"\b(le|lt|ge|gt|eq|ne)\b|<=|>=|<|>|==|!=")
VARIANTS = ("test_only", "test_expected", "semantic_ir")
LABEL_TO_VARIANT = {
    "A": "test_only",
    "B": "test_expected",
    "C": "semantic_ir",
    "test_only": "test_only",
    "test_expected": "test_expected",
    "semantic_ir": "semantic_ir",
    "full_semantic_ir": "semantic_ir",
}

FEATURE_COLS = [
    "n_scenarios",
    "n_inputs",
    "n_outputs",
    "overlap_rate",
    "boundary_density",
    "prompt_spec_len",
    "n_repair_attempts_semantic_ir",
    "n_repair_attempts_test_only",
    "mean_feedback_len_semantic_ir",
    "mean_feedback_len_test_only",
    "n_violations_first_fail_semantic_ir",
    "conf_test_only",
    "conf_semantic_ir",
]


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _variant(row: dict) -> str | None:
    raw = row.get("feedback_variant") or row.get("variant") or row.get("variant_label")
    if raw is None:
        return None
    key = str(raw).strip()
    return LABEL_TO_VARIANT.get(key, LABEL_TO_VARIANT.get(key.lower(), key))


def _conf(row: dict) -> float:
    if "strict_formal_conformance" in row:
        return float(row["strict_formal_conformance"])
    if "formal_conformance" in row:
        return float(row["formal_conformance"])
    raise KeyError("missing conformance field")


def _feedback_text_len(fb: Any) -> int:
    if fb is None:
        return 0
    if isinstance(fb, str):
        return len(fb)
    return len(json.dumps(fb, ensure_ascii=False, sort_keys=True))


def _mean_feedback_len(row: dict) -> float | None:
    hist = row.get("attempt_history")
    if isinstance(hist, list) and hist:
        lens = [_feedback_text_len(h.get("semantic_feedback")) for h in hist if isinstance(h, dict)]
        return sum(lens) / len(lens) if lens else None
    fb = row.get("semantic_feedback")
    if fb is None:
        return None
    return float(_feedback_text_len(fb))


def _n_repair_attempts(row: dict) -> int:
    hist = row.get("attempt_history")
    if isinstance(hist, list) and hist:
        return len(hist)
    attempts = row.get("attempts")
    if attempts is not None:
        return int(attempts)
    return 0


def _first_failing_attempt(hist: list) -> dict | None:
    for h in hist:
        if not isinstance(h, dict):
            continue
        passed = h.get("formal_passed")
        conf = h.get("formal_conformance")
        if passed is False or (conf is not None and float(conf) < 1.0 - EPS):
            return h
    return hist[0] if hist and isinstance(hist[0], dict) else None


def _violation_hist(row: dict) -> dict[str, int]:
    hist = row.get("attempt_history")
    fb = None
    if isinstance(hist, list) and hist:
        fail = _first_failing_attempt(hist)
        if fail is not None:
            fb = fail.get("semantic_feedback")
    if fb is None:
        fb = row.get("semantic_feedback")
    counts: Counter[str] = Counter()
    if isinstance(fb, list):
        for item in fb:
            if isinstance(item, dict):
                vt = item.get("violation_type") or "unknown"
                counts[str(vt)] += 1
    elif isinstance(fb, dict):
        vt = fb.get("violation_type") or "unknown"
        counts[str(vt)] += 1
    return dict(counts)


def boundary_density(scenarios: list[dict]) -> float:
    """Mean relational-operator count per non-others scenario."""
    non_others = [s for s in scenarios if s.get("kind") != "others"]
    if not non_others:
        return 0.0
    n_ops = 0
    for sc in non_others:
        n_ops += len(REL_OPS.findall(sc.get("test", "") or ""))
    return n_ops / len(non_others)


def task_static_features(task: dict) -> dict[str, Any]:
    sig = task.get("signature") or {}
    inputs = sig.get("inputs") or sig.get("params") or []
    outputs = sig.get("outputs") or []
    scenarios = task.get("fsfScenarios") or []
    cpx = task.get("complexity") or {}
    non_others = [s for s in scenarios if s.get("kind") != "others"]
    n_scenarios = int(cpx.get("scenario_count", len(non_others)))
    prompt = task.get("promptSpec") or ""
    return {
        "task_id": task.get("taskId") or task.get("task_id"),
        "n_scenarios": n_scenarios,
        "n_inputs": len(inputs),
        "n_outputs": len(outputs),
        "overlap_rate": float(cpx.get("overlap_rate", 0.0)),
        "overlap_tier": cpx.get("overlap_density_tier") or cpx.get("overlap_tier") or "unknown",
        "guard_complexity": cpx.get("guard_complexity") or "unknown",
        "boundary_density": round(boundary_density(scenarios), 4),
        "prompt_spec_len": len(prompt),
        "has_external_vars": bool(cpx.get("has_external_vars", False)),
    }


def e6_winner_label(scores: dict[str, float]) -> str:
    present = {v: scores[v] for v in VARIANTS if v in scores}
    if len(present) < 2:
        return "incomplete"
    best = max(present.values())
    winners = [v for v, c in present.items() if abs(c - best) <= EPS]
    if len(winners) == 1:
        return winners[0]
    return "tie"


def cohen_d(a: list[float], b: list[float]) -> float | None:
    if len(a) < 2 or len(b) < 2:
        return None
    ma, mb = statistics.mean(a), statistics.mean(b)
    va = statistics.variance(a)  # sample variance
    vb = statistics.variance(b)
    pooled = math.sqrt(((len(a) - 1) * va + (len(b) - 1) * vb) / (len(a) + len(b) - 2))
    if pooled < EPS:
        return 0.0
    return (ma - mb) / pooled


def summarize_numeric(vals: list[float]) -> dict[str, Any]:
    if not vals:
        return {"n": 0, "mean": None, "median": None, "std": None, "min": None, "max": None}
    return {
        "n": len(vals),
        "mean": statistics.mean(vals),
        "median": statistics.median(vals),
        "std": statistics.stdev(vals) if len(vals) > 1 else 0.0,
        "min": min(vals),
        "max": max(vals),
    }


def load_mode_conf(path: Path, mode_a: str, mode_b: str) -> dict[str, dict[str, float]]:
    """Return task_id -> {mode: conf} for two modes."""
    if not path.exists():
        return {}
    by_task: dict[str, dict[str, float]] = defaultdict(dict)
    for r in load_jsonl(path):
        tid = r.get("task_id") or r.get("taskId")
        mode = r.get("mode")
        if not tid or mode not in (mode_a, mode_b):
            continue
        by_task[tid][mode] = _conf(r)
    return dict(by_task)


def load_e14_conf(path: Path) -> dict[str, dict[str, float]]:
    if not path.exists():
        return {}
    by_task: dict[str, dict[str, float]] = defaultdict(dict)
    for r in load_jsonl(path):
        tid = r.get("task_id") or r.get("taskId")
        variant = _variant(r)
        if not tid or not variant:
            continue
        by_task[tid][variant] = _conf(r)
    return dict(by_task)


def paired_label(scores: dict[str, float], focal: str, other: str) -> str:
    if focal not in scores or other not in scores:
        return "missing"
    d = scores[focal] - scores[other]
    if d > EPS:
        return f"{focal}_win"
    if d < -EPS:
        return f"{other}_win"
    return "tie"


def build_records(
    tasks: list[dict],
    e6_rows: list[dict],
    *,
    e1_m_win: Path | None = None,
    e1_equal_k: Path | None = None,
    e14: Path | None = None,
) -> list[dict]:
    by_task_variant: dict[str, dict[str, dict]] = defaultdict(dict)
    for r in e6_rows:
        tid = r.get("task_id") or r.get("taskId")
        variant = _variant(r)
        if tid and variant:
            by_task_variant[tid][variant] = r

    secondary: dict[str, dict[str, str]] = defaultdict(dict)
    if e1_m_win and e1_m_win.exists():
        mwin = load_mode_conf(e1_m_win, "M", "B2")
        for tid, sc in mwin.items():
            secondary[tid]["e1_m_win_v2_M_vs_B2"] = paired_label(sc, "M", "B2")
    if e1_equal_k and e1_equal_k.exists():
        eq = load_mode_conf(e1_equal_k, "M_eq", "B2")
        for tid, sc in eq.items():
            secondary[tid]["e1_equal_k_M_eq_vs_B2"] = paired_label(sc, "M_eq", "B2")
    if e14 and e14.exists():
        e14_scores = load_e14_conf(e14)
        for tid, sc in e14_scores.items():
            secondary[tid]["e14_semantic_ir_vs_test_only"] = paired_label(
                sc, "semantic_ir", "test_only"
            )
            secondary[tid]["e14_trace_vs_semantic_ir"] = paired_label(
                sc, "execution_trace_matched", "semantic_ir"
            )

    records: list[dict] = []
    for task in tasks:
        feats = task_static_features(task)
        tid = feats["task_id"]
        variants = by_task_variant.get(tid, {})
        scores = {v: _conf(variants[v]) for v in VARIANTS if v in variants}

        conf_a = scores.get("test_only")
        conf_b = scores.get("test_expected")
        conf_c = scores.get("semantic_ir")
        delta_ca = (conf_c - conf_a) if conf_a is not None and conf_c is not None else None

        if delta_ca is None:
            ca_group = "incomplete"
        elif delta_ca > EPS:
            ca_group = "M_win"  # C > A
        elif delta_ca < -EPS:
            ca_group = "A_win"  # A > C (B2-like loss for semantic_ir)
        else:
            ca_group = "tie"

        row: dict[str, Any] = {
            **feats,
            "conf_test_only": conf_a,
            "conf_test_expected": conf_b,
            "conf_semantic_ir": conf_c,
            "delta_C_minus_A": delta_ca,
            "delta_C_minus_B": (conf_c - conf_b) if conf_b is not None and conf_c is not None else None,
            "E6_winner": e6_winner_label(scores),
            "E6_CA_group": ca_group,
            "is_rescue_zero_A": bool(conf_a is not None and abs(conf_a) <= EPS and ca_group == "M_win"),
        }

        for v in VARIANTS:
            if v not in variants:
                row[f"n_repair_attempts_{v}"] = None
                row[f"mean_feedback_len_{v}"] = None
                row[f"violation_hist_{v}"] = {}
                row[f"n_violations_first_fail_{v}"] = None
                continue
            vr = variants[v]
            row[f"n_repair_attempts_{v}"] = _n_repair_attempts(vr)
            row[f"mean_feedback_len_{v}"] = _mean_feedback_len(vr)
            vhist = _violation_hist(vr)
            row[f"violation_hist_{v}"] = vhist
            row[f"n_violations_first_fail_{v}"] = sum(vhist.values())

        # Flatten top violation types from semantic_ir first-fail for CSV
        vhist_c = row.get("violation_hist_semantic_ir") or {}
        for vt, cnt in sorted(vhist_c.items()):
            row[f"vt_semantic_ir_{vt}"] = cnt

        for k, v in secondary.get(tid, {}).items():
            row[k] = v

        records.append(row)
    return records


def group_stats(records: list[dict], group_key: str) -> dict[str, Any]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        groups[str(r.get(group_key, "unknown"))].append(r)

    out: dict[str, Any] = {"group_key": group_key, "groups": {}}
    for gname, rows in sorted(groups.items(), key=lambda x: (-len(x[1]), x[0])):
        feat_stats = {}
        for col in FEATURE_COLS:
            vals = [float(r[col]) for r in rows if r.get(col) is not None]
            feat_stats[col] = summarize_numeric(vals)
        # categorical
        tier_c = Counter(r.get("overlap_tier") for r in rows)
        guard_c = Counter(r.get("guard_complexity") for r in rows)
        out["groups"][gname] = {
            "n": len(rows),
            "task_ids": [r["task_id"] for r in rows],
            "features": feat_stats,
            "overlap_tier_counts": dict(tier_c),
            "guard_complexity_counts": dict(guard_c),
            "mean_delta_C_minus_A": statistics.mean(
                [float(r["delta_C_minus_A"]) for r in rows if r.get("delta_C_minus_A") is not None]
            )
            if any(r.get("delta_C_minus_A") is not None for r in rows)
            else None,
        }
    return out


def effect_sizes(records: list[dict]) -> dict[str, Any]:
    m_win = [r for r in records if r.get("E6_CA_group") == "M_win"]
    a_win = [r for r in records if r.get("E6_CA_group") == "A_win"]
    tie = [r for r in records if r.get("E6_CA_group") == "tie"]
    # B2-like per mission: A >= C (A_win + tie)
    b2_like = a_win + tie

    effects: dict[str, Any] = {}
    for col in FEATURE_COLS:
        a_vals = [float(r[col]) for r in m_win if r.get(col) is not None]
        b_vals = [float(r[col]) for r in b2_like if r.get(col) is not None]
        c_vals = [float(r[col]) for r in a_win if r.get(col) is not None]
        t_vals = [float(r[col]) for r in tie if r.get(col) is not None]
        effects[col] = {
            "cohen_d_M_win_vs_B2_like": cohen_d(a_vals, b_vals),
            "cohen_d_M_win_vs_A_win": cohen_d(a_vals, c_vals),
            "cohen_d_M_win_vs_tie": cohen_d(a_vals, t_vals),
            "mean_M_win": statistics.mean(a_vals) if a_vals else None,
            "mean_B2_like": statistics.mean(b_vals) if b_vals else None,
            "mean_A_win": statistics.mean(c_vals) if c_vals else None,
            "mean_tie": statistics.mean(t_vals) if t_vals else None,
            "median_M_win": statistics.median(a_vals) if a_vals else None,
            "median_B2_like": statistics.median(b_vals) if b_vals else None,
            "median_A_win": statistics.median(c_vals) if c_vals else None,
            "median_tie": statistics.median(t_vals) if t_vals else None,
        }
    return {
        "n_M_win": len(m_win),
        "n_A_win": len(a_win),
        "n_tie": len(tie),
        "n_B2_like_A_ge_C": len(b2_like),
        "note": "B2-like = A_win + tie (A >= C). M-win = C > A.",
        "features": effects,
    }


def find_thresholds(records: list[dict]) -> dict[str, Any]:
    """Data-driven regimes where semantic_ir win rate is elevated."""
    m_win = [r for r in records if r.get("E6_CA_group") == "M_win"]
    n_win = len(m_win)
    n_all = len([r for r in records if r.get("E6_CA_group") != "incomplete"])
    base_rate = n_win / n_all if n_all else 0.0

    def rate_in(pred) -> dict[str, Any]:
        subset = [r for r in records if r.get("E6_CA_group") != "incomplete" and pred(r)]
        wins = [r for r in subset if r["E6_CA_group"] == "M_win"]
        n = len(subset)
        return {
            "n_subset": n,
            "n_M_win": len(wins),
            "win_rate": (len(wins) / n) if n else None,
            "share_of_all_wins": (len(wins) / n_win) if n_win else None,
            "lift_vs_base": ((len(wins) / n) / base_rate) if n and base_rate else None,
            "task_ids_wins": [r["task_id"] for r in wins],
        }

    # Candidate thresholds from M-win medians / tertiles of full set
    overlaps = sorted(float(r["overlap_rate"]) for r in records if r.get("overlap_rate") is not None)
    scenarios = sorted(int(r["n_scenarios"]) for r in records if r.get("n_scenarios") is not None)
    bds = sorted(float(r["boundary_density"]) for r in records if r.get("boundary_density") is not None)

    def percentile(sorted_vals: list[float], p: float) -> float:
        if not sorted_vals:
            return 0.0
        idx = min(len(sorted_vals) - 1, max(0, int(round(p * (len(sorted_vals) - 1)))))
        return float(sorted_vals[idx])

    candidates: list[tuple[str, Any]] = []
    for thr in sorted(set([percentile(overlaps, q) for q in (0.33, 0.5, 0.67, 0.75)] + [1.0, 1.2, 1.3, 1.4])):
        candidates.append((f"overlap_rate>={thr:.3f}", lambda r, t=thr: float(r["overlap_rate"]) >= t))
    for thr in sorted(set(scenarios)):
        candidates.append((f"n_scenarios>={thr}", lambda r, t=thr: int(r["n_scenarios"]) >= t))
    for thr in sorted(set([percentile(bds, q) for q in (0.33, 0.5, 0.67)])):
        candidates.append((f"boundary_density>={thr:.3f}", lambda r, t=thr: float(r["boundary_density"]) >= t))
    for tier in ("high", "medium", "low"):
        candidates.append((f"overlap_tier=={tier}", lambda r, t=tier: r.get("overlap_tier") == t))
    for g in ("Nested", "AND", "Mixed", "Arithmetic", "Simple"):
        candidates.append((f"guard_complexity=={g}", lambda r, t=g: r.get("guard_complexity") == t))

    # Combined regimes of interest
    med_overlap_win = statistics.median([float(r["overlap_rate"]) for r in m_win]) if m_win else None
    med_scen_win = statistics.median([int(r["n_scenarios"]) for r in m_win]) if m_win else None
    if med_overlap_win is not None and med_scen_win is not None:
        candidates.append(
            (
                f"overlap_rate>={med_overlap_win:.3f}_AND_n_scenarios>={int(med_scen_win)}",
                lambda r, o=med_overlap_win, s=int(med_scen_win): float(r["overlap_rate"]) >= o
                and int(r["n_scenarios"]) >= s,
            )
        )
    candidates.append(
        (
            "overlap_tier==high_AND_n_scenarios>=7",
            lambda r: r.get("overlap_tier") == "high" and int(r["n_scenarios"]) >= 7,
        )
    )
    candidates.append(
        (
            "overlap_rate>=1.3_AND_n_scenarios>=7",
            lambda r: float(r["overlap_rate"]) >= 1.3 and int(r["n_scenarios"]) >= 7,
        )
    )
    # Baseline-Conf regimes (rescue analysis)
    def _conf_a(r: dict) -> float | None:
        v = r.get("conf_test_only")
        return None if v is None else float(v)

    candidates.append(
        (
            "conf_test_only==0",
            lambda r: (_conf_a(r) is not None and abs(_conf_a(r)) <= EPS),  # type: ignore[arg-type]
        )
    )
    candidates.append(
        (
            "conf_test_only<0.25",
            lambda r: (_conf_a(r) is not None and _conf_a(r) < 0.25),  # type: ignore[arg-type]
        )
    )
    candidates.append(
        (
            "conf_test_only<0.5",
            lambda r: (_conf_a(r) is not None and _conf_a(r) < 0.5),  # type: ignore[arg-type]
        )
    )
    candidates.append(
        (
            "conf_test_only==0_AND_overlap_tier==low",
            lambda r: (
                _conf_a(r) is not None
                and abs(_conf_a(r)) <= EPS  # type: ignore[arg-type]
                and r.get("overlap_tier") == "low"
            ),
        )
    )
    candidates.append(
        (
            "conf_test_only==0_AND_overlap_tier==high",
            lambda r: (
                _conf_a(r) is not None
                and abs(_conf_a(r)) <= EPS  # type: ignore[arg-type]
                and r.get("overlap_tier") == "high"
            ),
        )
    )

    scored = []
    for name, pred in candidates:
        rec = rate_in(pred)
        rec["rule"] = name
        # Vacuous if subset is the full suite
        rec["vacuous"] = rec["n_subset"] == n_all
        scored.append(rec)

    # Prefer non-vacuous rules: high lift, then coverage of wins, then win_rate
    scored_sorted = sorted(
        scored,
        key=lambda x: (
            1 if x.get("vacuous") else 0,
            -(x["lift_vs_base"] or 0),
            -(x["share_of_all_wins"] or 0),
            -(x["win_rate"] or 0),
        ),
    )
    return {
        "base_rate_M_win": base_rate,
        "n_tasks": n_all,
        "n_M_win": n_win,
        "m_win_median_overlap_rate": med_overlap_win,
        "m_win_median_n_scenarios": med_scen_win,
        "m_win_mean_overlap_rate": statistics.mean([float(r["overlap_rate"]) for r in m_win]) if m_win else None,
        "m_win_mean_n_scenarios": statistics.mean([float(r["n_scenarios"]) for r in m_win]) if m_win else None,
        "rules": scored_sorted,
    }


def write_csv(records: list[dict], path: Path) -> None:
    # Collect all keys; serialize nested dicts as JSON strings
    keys: list[str] = []
    seen = set()
    preferred = [
        "task_id",
        "E6_winner",
        "E6_CA_group",
        "delta_C_minus_A",
        "delta_C_minus_B",
        "conf_test_only",
        "conf_test_expected",
        "conf_semantic_ir",
        "n_scenarios",
        "n_inputs",
        "n_outputs",
        "overlap_rate",
        "overlap_tier",
        "guard_complexity",
        "boundary_density",
        "prompt_spec_len",
        "has_external_vars",
    ]
    for k in preferred:
        if k not in seen:
            keys.append(k)
            seen.add(k)
    for r in records:
        for k in r:
            if k not in seen:
                keys.append(k)
                seen.add(k)

    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in records:
            flat = {}
            for k in keys:
                v = r.get(k)
                if isinstance(v, (dict, list)):
                    flat[k] = json.dumps(v, ensure_ascii=False)
                else:
                    flat[k] = v
            w.writerow(flat)


def fmt_num(x: Any, digits: int = 3) -> str:
    if x is None:
        return "???
    if isinstance(x, float):
        return f"{x:.{digits}f}"
    return str(x)


def write_tables_md(summary: dict, effects: dict, thresholds: dict, path: Path) -> None:
    lines: list[str] = []
    lines.append("# Winner Feature Tables (E6 Evidence Mining)")
    lines.append("")
    lines.append("Source: `run_feedback_v2/feedback_variants` paired with `hard_tasks_annotated.json`.")
    lines.append("")
    lines.append("## 1. Outcome counts")
    lines.append("")
    lines.append("| Group | Definition | n |")
    lines.append("|-------|------------|---|")
    lines.append(f"| M-win | C > A (`semantic_ir` > `test_only`) | {effects['n_M_win']} |")
    lines.append(f"| A-win | A > C | {effects['n_A_win']} |")
    lines.append(f"| Tie (C=A) | C == A | {effects['n_tie']} |")
    lines.append(f"| B2-like | A ???C (A-win + tie) | {effects['n_B2_like_A_ge_C']} |")
    lines.append("")

    # Three-way winner
    e6w = summary["by_E6_winner"]["groups"]
    lines.append("## 2. Three-way E6_winner (argmax Conf)")
    lines.append("")
    lines.append("| E6_winner | n |")
    lines.append("|-----------|---|")
    for g, rec in sorted(e6w.items(), key=lambda x: -x[1]["n"]):
        lines.append(f"| {g} | {rec['n']} |")
    lines.append("")

    lines.append("## 3. Feature means by C???A group")
    lines.append("")
    header_feats = [
        "conf_test_only",
        "conf_semantic_ir",
        "overlap_rate",
        "n_scenarios",
        "boundary_density",
        "prompt_spec_len",
        "n_repair_attempts_semantic_ir",
        "mean_feedback_len_semantic_ir",
    ]
    lines.append("| Feature | M-win mean | M-win median | A-win mean | Tie mean | B2-like mean | Cohen d (M vs B2-like) |")
    lines.append("|---------|------------|--------------|------------|----------|--------------|------------------------|")
    for col in header_feats:
        e = effects["features"][col]
        lines.append(
            f"| {col} | {fmt_num(e['mean_M_win'])} | {fmt_num(e['median_M_win'])} | "
            f"{fmt_num(e['mean_A_win'])} | {fmt_num(e['mean_tie'])} | {fmt_num(e['mean_B2_like'])} | "
            f"{fmt_num(e['cohen_d_M_win_vs_B2_like'])} |"
        )
    lines.append("")

    lines.append("## 4. Categorical composition (C???A groups)")
    lines.append("")
    ca = summary["by_E6_CA_group"]["groups"]
    lines.append("### Overlap tier")
    lines.append("")
    lines.append("| Group | low | medium | high |")
    lines.append("|-------|-----|--------|------|")
    for g in ("M_win", "A_win", "tie"):
        if g not in ca:
            continue
        c = ca[g]["overlap_tier_counts"]
        lines.append(f"| {g} | {c.get('low', 0)} | {c.get('medium', 0)} | {c.get('high', 0)} |")
    lines.append("")
    lines.append("### Guard complexity")
    lines.append("")
    guards = sorted({g for rec in ca.values() for g in rec["guard_complexity_counts"]})
    lines.append("| Group | " + " | ".join(guards) + " |")
    lines.append("|-------|" + "|".join(["---"] * len(guards)) + "|")
    for g in ("M_win", "A_win", "tie"):
        if g not in ca:
            continue
        c = ca[g]["guard_complexity_counts"]
        lines.append("| " + g + " | " + " | ".join(str(c.get(x, 0)) for x in guards) + " |")
    lines.append("")

    lines.append("## 5. Threshold / regime scan (elevated M-win rate)")
    lines.append("")
    lines.append(f"Base M-win rate: **{effects['n_M_win']}/{thresholds['n_tasks']}** "
                 f"= {thresholds['base_rate_M_win']:.3f}.")
    lines.append("")
    lines.append("Non-vacuous rules sorted by lift (vacuous full-suite rules listed last).")
    lines.append("")
    lines.append("| Rule | n_subset | n_M_win | win_rate | share_of_14_wins | lift | vacuous |")
    lines.append("|------|----------|---------|----------|------------------|------|---------|")
    for rule in thresholds["rules"][:30]:
        lines.append(
            f"| `{rule['rule']}` | {rule['n_subset']} | {rule['n_M_win']} | "
            f"{fmt_num(rule['win_rate'])} | {fmt_num(rule['share_of_all_wins'])} | "
            f"{fmt_num(rule['lift_vs_base'])} | {rule.get('vacuous', False)} |"
        )
    lines.append("")

    # List the 14 wins
    m_ids = ca.get("M_win", {}).get("task_ids", [])
    lines.append("## 6. The 14 M-win tasks (C > A)")
    lines.append("")
    lines.append(
        "| task_id | Conf_A | Conf_C | ??C???A | overlap_rate | tier | "
        "boundary_density | guard |"
    )
    lines.append(
        "|---------|--------|--------|------|--------------|------|"
        "------------------|-------|"
    )
    by_id = {r["task_id"]: r for r in summary["_records_for_table"]}
    for tid in m_ids:
        r = by_id[tid]
        lines.append(
            f"| {tid} | {fmt_num(r['conf_test_only'], 4)} | {fmt_num(r['conf_semantic_ir'], 4)} | "
            f"{fmt_num(r['delta_C_minus_A'], 4)} | {fmt_num(r['overlap_rate'])} | {r['overlap_tier']} | "
            f"{fmt_num(r['boundary_density'])} | {r['guard_complexity']} |"
        )
    lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_findings(effects: dict, thresholds: dict, summary: dict, path: Path) -> None:
    m_n = effects["n_M_win"]
    a_n = effects["n_A_win"]
    t_n = effects["n_tie"]
    base = thresholds["base_rate_M_win"]

    feat = effects["features"]
    ov = feat["overlap_rate"]
    bd = feat["boundary_density"]
    ca_conf = feat["conf_test_only"]
    cc_conf = feat["conf_semantic_ir"]

    ca = summary["by_E6_CA_group"]["groups"]
    m_tiers = ca.get("M_win", {}).get("overlap_tier_counts", {})
    m_guards = ca.get("M_win", {}).get("guard_complexity_counts", {})

    rules = thresholds["rules"]
    non_vacuous = [r for r in rules if not r.get("vacuous")]
    # Prefer high-lift rules that still cover a meaningful share of wins
    cover_half = [
        r
        for r in non_vacuous
        if (r.get("share_of_all_wins") or 0) >= 0.5
        and (r.get("lift_vs_base") or 0) >= 1.5
        and (r.get("n_subset") or 0) >= 5
    ]
    if not cover_half:
        cover_half = [
            r
            for r in non_vacuous
            if (r.get("share_of_all_wins") or 0) >= 0.5
            and (r.get("lift_vs_base") or 0) >= 1.1
            and (r.get("n_subset") or 0) >= 5
        ]
    focus = (cover_half or non_vacuous)[:8]

    # Key rescue rules
    rescue0 = next((r for r in rules if r["rule"] == "conf_test_only==0"), None)
    rescue25 = next((r for r in rules if r["rule"] == "conf_test_only<0.25"), None)
    high7 = next((r for r in rules if r["rule"] == "overlap_tier==high_AND_n_scenarios>=7"), None)
    ov13 = next((r for r in rules if r["rule"] == "overlap_rate>=1.3_AND_n_scenarios>=7"), None)
    low_tier = next((r for r in rules if r["rule"] == "overlap_tier==low"), None)

    records = summary["_records_for_table"]
    m_rows = [r for r in records if r.get("E6_CA_group") == "M_win"]
    a_rows = [r for r in records if r.get("E6_CA_group") == "A_win"]
    n_zero_a_m = sum(1 for r in m_rows if abs(float(r["conf_test_only"])) <= EPS)
    n_zero_a_all = sum(
        1
        for r in records
        if r.get("conf_test_only") is not None and abs(float(r["conf_test_only"])) <= EPS
    )

    lines = []
    lines.append("# FINDINGS ???Why does E6 (`semantic_ir`) win?")
    lines.append("")
    lines.append(
        "**Scope:** Existing E6 run only (`run_feedback_v2`, n=120 tasks ?? 3 variants). "
        "No new LLM experiments. Numbers computed by `mine_task_features.py`."
    )
    lines.append("")
    lines.append("## Headline outcome")
    lines.append("")
    lines.append(
        f"Paired C???A (`semantic_ir` ???`test_only`): **{m_n} M-wins / {a_n} A-wins / {t_n} ties** "
        f"(ties dominate: {t_n}/120 = {100 * t_n / 120:.1f}%). "
        "The mean Conf. advantage of typed IR is concentrated in a small non-tie slice."
    )
    lines.append("")
    lines.append(
        "Three-way argmax winner (`E6_winner`) is almost always `tie` (118/120): "
        "when C beats A, `test_expected` often matches C, so unique `semantic_ir` argmax is rare (2/120). "
        "All primary claims below use the **paired C???A** definition (matches paper W/L/T = 14/4/102)."
    )
    lines.append("")
    lines.append("## Primary regime: rescue from collapsed test-only Conf.")
    lines.append("")
    lines.append(
        f"M-win tasks have near-floor **Conf under `test_only`** "
        f"(mean={fmt_num(ca_conf['mean_M_win'], 4)}, median={fmt_num(ca_conf['median_M_win'], 4)}) "
        f"versus B2-like "
        f"(mean={fmt_num(ca_conf['mean_B2_like'], 4)}; Cohen d={fmt_num(ca_conf['cohen_d_M_win_vs_B2_like'])}). "
        f"Under `semantic_ir` they recover to mean Conf={fmt_num(cc_conf['mean_M_win'], 4)}."
    )
    lines.append("")
    lines.append(
        f"**{n_zero_a_m}/{m_n} of the E6 wins have `conf_test_only == 0`** "
        f"(suite-wide zero-A tasks: {n_zero_a_all}/120)."
    )
    if rescue0:
        lines.append(
            f"- Rule `conf_test_only==0`: **{rescue0['n_M_win']}/{rescue0['n_subset']}** M-wins "
            f"(win_rate={fmt_num(rescue0['win_rate'])}, "
            f"covers {rescue0['n_M_win']}/{m_n} = {fmt_num(rescue0['share_of_all_wins'])} of E6 wins, "
            f"lift={fmt_num(rescue0['lift_vs_base'])})."
        )
    if rescue25:
        lines.append(
            f"- Rule `conf_test_only<0.25`: **{rescue25['n_M_win']}/{rescue25['n_subset']}** M-wins "
            f"(win_rate={fmt_num(rescue25['win_rate'])}, "
            f"covers {fmt_num(rescue25['share_of_all_wins'])} of E6 wins, "
            f"lift={fmt_num(rescue25['lift_vs_base'])})."
        )
    lines.append("")
    lines.append(
        f"A-wins (n={a_n}) are the mirror image: high `test_only` "
        f"(mean={fmt_num(ca_conf['mean_A_win'], 4)}) collapsing under `semantic_ir` "
        f"(mean={fmt_num(cc_conf['mean_A_win'], 4)})."
    )
    lines.append("")
    lines.append("## Static spec features: weak / homogeneous on this suite")
    lines.append("")
    lines.append(
        "The annotated HardSynthetic suite is nearly homogeneous on several axes used in the "
        "deployment story: **all 120 tasks** have `n_scenarios=7`, `guard_complexity=Nested`, "
        "`n_inputs=5`, `n_outputs=3`. Therefore scenario-count and guard-complexity thresholds "
        "cannot separate winners here."
    )
    lines.append("")
    lines.append(
        f"Overlap does **not** favor M-wins on E6: mean overlap_rate "
        f"M-win={fmt_num(ov['mean_M_win'])} vs B2-like={fmt_num(ov['mean_B2_like'])} "
        f"(Cohen d={fmt_num(ov['cohen_d_M_win_vs_B2_like'])}). "
        f"boundary_density similarly flat "
        f"(M={fmt_num(bd['mean_M_win'])} vs B2-like={fmt_num(bd['mean_B2_like'])}; "
        f"d={fmt_num(bd['cohen_d_M_win_vs_B2_like'])})."
    )
    lines.append("")
    lines.append(
        f"Among the {m_n} wins, overlap tiers are: "
        + ", ".join(f"{k}={v}" for k, v in sorted(m_tiers.items()))
        + "; guard complexity: "
        + ", ".join(f"{k}={v}" for k, v in sorted(m_guards.items()))
        + "."
    )
    lines.append("")
    if low_tier:
        lines.append(
            f"`overlap_tier==low` has mild positive lift "
            f"({low_tier['n_M_win']}/{low_tier['n_subset']}, "
            f"covers {low_tier['n_M_win']}/{m_n} wins, lift={fmt_num(low_tier['lift_vs_base'])}) "
            "???opposite of a pure high-overlap necessity claim on this run."
        )
    if high7:
        lines.append(
            f"Story-aligned `overlap_tier==high` ???`n_scenarios???`: "
            f"{high7['n_M_win']}/{high7['n_subset']} "
            f"(covers {high7['n_M_win']}/{m_n} wins, lift={fmt_num(high7['lift_vs_base'])})."
        )
    if ov13:
        lines.append(
            f"Numeric cut `overlap_rate???.3` ???`n_scenarios???`: "
            f"{ov13['n_M_win']}/{ov13['n_subset']} "
            f"(covers {ov13['n_M_win']}/{m_n} wins, lift={fmt_num(ov13['lift_vs_base'])})."
        )
    lines.append("")
    lines.append("### Concrete thresholds (data-driven, non-vacuous)")
    lines.append("")
    lines.append(f"Base M-win rate = {m_n}/{thresholds['n_tasks']} = {base:.3f}.")
    lines.append("")
    for r in focus:
        lines.append(
            f"- **`{r['rule']}`**: {r['n_M_win']}/{r['n_subset']} M-wins "
            f"(win_rate={fmt_num(r['win_rate'])}, "
            f"covers {r['n_M_win']}/{m_n} = {fmt_num(r['share_of_all_wins'])} of all E6 wins, "
            f"lift={fmt_num(r['lift_vs_base'])})."
        )
    lines.append("")
    best_cover = max(focus, key=lambda x: (x.get("share_of_all_wins") or 0, x.get("lift_vs_base") or 0)) if focus else None
    if best_cover:
        lines.append(
            f"**How many of the {m_n} E6 wins share the strongest covering regime "
            f"(`{best_cover['rule']}`)?** "
            f"**{best_cover['n_M_win']} / {m_n}** "
            f"({100 * (best_cover['share_of_all_wins'] or 0):.1f}%)."
        )
        lines.append("")

    lines.append("## Interpretation (honest)")
    lines.append("")
    lines.append(
        "On E6, typed Semantic Feedback IR is **not universally better**: "
        f"most tasks are exact C=A ties ({t_n}/120). "
        "Where it wins, the dominant pattern is **repair rescue**: "
        "`test_only` fails almost completely (often Conf=0), while typed IR recovers to high Conf "
        "(~0.875???.958). Static overlap/scenario features are too homogeneous here to support an "
        "ex-ante high-overlap deployment rule from E6 alone."
    )
    lines.append("")
    lines.append(
        "Implication for the sprint story: use E6 to argue **IR irreplaceability on hard repair "
        "failures** (field-rich feedback when the baseline loop collapses). "
        "Defer **when-to-enable / high-overlap predictor** claims to Agent F using features that "
        "actually vary, or to stratified runs with more complexity diversity."
    )
    lines.append("")
    lines.append("## Caveats")
    lines.append("")
    lines.append(
        f"1. **Ties dominate** ({t_n}/120). Feature contrasts rest on a small decisive set "
        f"({m_n}+{a_n}={m_n + a_n} non-ties); Cohen d vs B2-like is diluted by 102 ties."
    )
    lines.append(
        "2. **Homogeneous generator:** scenario_count / Nested / I/O arity do not vary ???"
        "null results on those axes are expected, not evidence against the mechanism elsewhere."
    )
    lines.append(
        "3. **Overlap story not supported by E6 alone:** M-wins are not enriched for high "
        "overlap_tier; do not invent a high-overlap necessity claim from this table."
    )
    lines.append(
        "4. **Confounding with difficulty:** zero-A tasks may be harder for reasons correlated "
        "with (unmeasured) bug patterns; rescue ???proof that overlap causes IR value."
    )
    lines.append(
        "5. **Secondary labels** (E1 M-win, equal-K, E14) are attached in `task_feature_db` "
        "for cross-checks but do not redefine the E6 C???A winner used here."
    )
    lines.append(
        "6. **boundary_density** = (# relational ops in non-others guards) / n_scenarios ???proxy only."
    )
    lines.append("")
    lines.append("## Artifacts")
    lines.append("")
    lines.append("- `task_feature_db.csv` / `task_feature_db.json`")
    lines.append("- `winner_feature_summary.json`")
    lines.append("- `winner_feature_tables.md`")
    lines.append("- optional `overlap_vs_delta.png`, `scenario_count_vs_delta.png`")
    lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def maybe_plots(records: list[dict], out_dir: Path) -> list[Path]:
    written: list[Path] = []
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return written

    xs_o, ys, cols = [], [], []
    xs_s = []
    for r in records:
        if r.get("delta_C_minus_A") is None:
            continue
        xs_o.append(float(r["overlap_rate"]))
        xs_s.append(float(r["n_scenarios"]))
        ys.append(float(r["delta_C_minus_A"]))
        g = r.get("E6_CA_group")
        cols.append({"M_win": "tab:green", "A_win": "tab:red", "tie": "0.7"}.get(g, "0.5"))

    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    ax.scatter(xs_o, ys, c=cols, alpha=0.75, edgecolors="none", s=36)
    ax.axhline(0.0, color="k", lw=0.8, alpha=0.5)
    ax.set_xlabel("overlap_rate")
    ax.set_ylabel("delta_C_minus_A (Conf)")
    ax.set_title("E6: overlap_rate vs C???A delta")
    p1 = out_dir / "overlap_vs_delta.png"
    fig.tight_layout()
    fig.savefig(p1, dpi=140)
    plt.close(fig)
    written.append(p1)

    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    # jitter scenarios slightly for visibility
    import random as _rnd

    rng = _rnd.Random(0)
    xs_sj = [x + rng.uniform(-0.15, 0.15) for x in xs_s]
    ax.scatter(xs_sj, ys, c=cols, alpha=0.75, edgecolors="none", s=36)
    ax.axhline(0.0, color="k", lw=0.8, alpha=0.5)
    ax.set_xlabel("n_scenarios (jittered)")
    ax.set_ylabel("delta_C_minus_A (Conf)")
    ax.set_title("E6: scenario_count vs C???A delta")
    p2 = out_dir / "scenario_count_vs_delta.png"
    fig.tight_layout()
    fig.savefig(p2, dpi=140)
    plt.close(fig)
    written.append(p2)
    return written


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tasks", type=Path, default=DEFAULT_TASKS)
    ap.add_argument("--e6", type=Path, default=DEFAULT_E6)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument(
        "--e1-m-win",
        type=Path,
        default=ROOT / "artifacts" / "run_e1_m_win_v2" / "results.jsonl",
    )
    ap.add_argument(
        "--e1-equal-k",
        type=Path,
        default=ROOT / "artifacts" / "run_e1_equal_k_v1" / "results.jsonl",
    )
    ap.add_argument(
        "--e14",
        type=Path,
        default=ROOT / "artifacts" / "run_e14_sweep_v1" / "results.jsonl",
    )
    args = ap.parse_args()

    if not args.tasks.exists():
        print(f"missing {args.tasks}", file=sys.stderr)
        return 1
    if not args.e6.exists():
        print(f"missing {args.e6}", file=sys.stderr)
        return 1

    tasks = json.loads(args.tasks.read_text(encoding="utf-8"))
    if isinstance(tasks, dict):
        tasks = list(tasks.values())
    e6_rows = load_jsonl(args.e6)

    records = build_records(
        tasks,
        e6_rows,
        e1_m_win=args.e1_m_win,
        e1_equal_k=args.e1_equal_k,
        e14=args.e14,
    )

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / "task_feature_db.csv"
    json_path = out_dir / "task_feature_db.json"
    write_csv(records, csv_path)
    json_path.write_text(json.dumps(records, indent=2), encoding="utf-8")

    by_ca = group_stats(records, "E6_CA_group")
    by_winner = group_stats(records, "E6_winner")
    effects = effect_sizes(records)
    thresholds = find_thresholds(records)

    # Winner counts for three-way
    winner_counts = Counter(r["E6_winner"] for r in records)
    ca_counts = Counter(r["E6_CA_group"] for r in records)

    summary = {
        "source_e6": str(args.e6.resolve()),
        "source_tasks": str(args.tasks.resolve()),
        "n_tasks": len(records),
        "n_e6_rows": len(e6_rows),
        "E6_winner_counts": dict(winner_counts),
        "E6_CA_group_counts": dict(ca_counts),
        "by_E6_CA_group": by_ca,
        "by_E6_winner": by_winner,
        "effect_sizes": effects,
        "thresholds": {
            k: v
            for k, v in thresholds.items()
            if k != "rules"
        },
        "threshold_rules_top": thresholds["rules"][:40],
        "note": (
            "M_win = conf(semantic_ir) > conf(test_only). "
            "B2-like = A >= C. Effect sizes: Cohen's d."
        ),
    }
    # Keep task ids in group stats; strip huge duplication from summary file is fine
    summary_path = out_dir / "winner_feature_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # tables need raw records
    table_summary = {
        "by_E6_winner": by_winner,
        "by_E6_CA_group": by_ca,
        "_records_for_table": records,
    }
    tables_path = out_dir / "winner_feature_tables.md"
    write_tables_md(table_summary, effects, thresholds, tables_path)

    findings_path = out_dir / "FINDINGS.md"
    write_findings(effects, thresholds, table_summary, findings_path)

    plots = maybe_plots(records, out_dir)

    # Console digest
    print(f"n_tasks={len(records)} e6_rows={len(e6_rows)}")
    print(f"E6_CA_group: {dict(ca_counts)}")
    print(f"E6_winner: {dict(winner_counts)}")
    print(
        f"overlap_rate mean M_win={fmt_num(effects['features']['overlap_rate']['mean_M_win'])} "
        f"B2_like={fmt_num(effects['features']['overlap_rate']['mean_B2_like'])} "
        f"d={fmt_num(effects['features']['overlap_rate']['cohen_d_M_win_vs_B2_like'])}"
    )
    print(f"Wrote {csv_path}")
    print(f"Wrote {json_path}")
    print(f"Wrote {summary_path}")
    print(f"Wrote {tables_path}")
    print(f"Wrote {findings_path}")
    for p in plots:
        print(f"Wrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
