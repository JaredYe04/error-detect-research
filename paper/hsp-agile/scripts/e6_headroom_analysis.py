#!/usr/bin/env python3
"""E6-H headroom stratification for C-A on run_feedback_v2.

Primary stratum H is tasks where A/test_only has Conf < 1.  The script also
emits the stricter rescue subset where A/test_only has Conf = 0 and a candidate
CatchAll-40 task list grounded in existing E6 qualitative/win-profile evidence.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from e6_paired_analysis import (
    EPS,
    FOCAL,
    DEFAULT_RUN,
    PAPER_PROC,
    _conf,
    _variant,
    bootstrap_ci,
    load_rows,
    wilcoxon_p,
)

PAPER = Path(__file__).resolve().parents[1]
ROOT = PAPER.parents[1]
TABLE_DIR = PAPER / "tables"
QUAL = (
    PAPER
    / "artifacts"
    / "strengthening_sprint"
    / "agent_a_evidence"
    / "e6_win_qualitative.json"
)
WIN_TASKS = (
    PAPER
    / "artifacts"
    / "strengthening_sprint"
    / "agent_a_evidence"
    / "e6_win_tasks.json"
)

COMPARATOR = "test_only"
OUT_JSON = "e6_headroom_summary.json"
OUT_CSV = "e6_headroom_summary.csv"
OUT_CANDIDATES = "e6_headroom_catchall40_candidates.csv"
OUT_TEX = "e6_headroom_summary.tex"


def wilson_ci(successes: int, n: int, z: float = 1.959963984540054) -> dict[str, float | None]:
    if n <= 0:
        return {"rate": None, "ci_low": None, "ci_high": None}
    p = successes / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2.0 * n)) / denom
    half = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * n)) / n) / denom
    return {
        "rate": p,
        "ci_low": max(0.0, centre - half),
        "ci_high": min(1.0, centre + half),
    }


def relation(delta: float) -> str:
    if delta > EPS:
        return "win"
    if delta < -EPS:
        return "loss"
    return "tie"


def task_number(task_id: str) -> int:
    m = re.search(r"(\d+)$", task_id)
    return int(m.group(1)) if m else 0


def paired_cliffs_delta(wins: int, losses: int, n: int) -> float | None:
    if n <= 0:
        return None
    return (wins - losses) / n


def build_by_task(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_task: dict[str, dict[str, Any]] = defaultdict(dict)
    for row in rows:
        tid = row.get("task_id") or row.get("taskId")
        variant = _variant(row)
        if not tid or not variant:
            continue
        by_task[str(tid)][variant] = row
    return by_task


def task_record(task_id: str, rows: dict[str, Any]) -> dict[str, Any] | None:
    if FOCAL not in rows or COMPARATOR not in rows:
        return None
    a_conf = _conf(rows[COMPARATOR])
    c_conf = _conf(rows[FOCAL])
    delta = c_conf - a_conf
    return {
        "task_id": task_id,
        "conf_test_only": a_conf,
        "conf_semantic_ir": c_conf,
        "delta": delta,
        "relation": relation(delta),
    }


def summarise_stratum(name: str, records: list[dict[str, Any]], description: str) -> dict[str, Any]:
    deltas = [float(r["delta"]) for r in records]
    wins = sum(1 for d in deltas if d > EPS)
    losses = sum(1 for d in deltas if d < -EPS)
    ties = len(deltas) - wins - losses
    n = len(deltas)
    mean_focal = sum(float(r["conf_semantic_ir"]) for r in records) / n if n else 0.0
    mean_comparator = sum(float(r["conf_test_only"]) for r in records) / n if n else 0.0
    ci = bootstrap_ci(deltas)
    all_win_ci = wilson_ci(wins, n)
    decisive_n = wins + losses
    decisive_ci = wilson_ci(wins, decisive_n)
    return {
        "stratum": name,
        "description": description,
        "focal": FOCAL,
        "comparator": COMPARATOR,
        "n_paired": n,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "mean_focal": mean_focal,
        "mean_comparator": mean_comparator,
        "delta_pp": 100.0 * (mean_focal - mean_comparator),
        "mean_delta_pp": ci["mean_delta_pp"],
        "ci_low_pp": ci["ci_low_pp"],
        "ci_high_pp": ci["ci_high_pp"],
        "bootstrap_B": ci.get("B"),
        "bootstrap_seed": ci.get("seed"),
        "wilcoxon_p": wilcoxon_p(deltas),
        "paired_cliffs_delta": paired_cliffs_delta(wins, losses, n),
        "win_rate_all": all_win_ci["rate"],
        "win_rate_all_wilson_low": all_win_ci["ci_low"],
        "win_rate_all_wilson_high": all_win_ci["ci_high"],
        "decisive_n": decisive_n,
        "decisive_win_rate": decisive_ci["rate"],
        "decisive_win_rate_wilson_low": decisive_ci["ci_low"],
        "decisive_win_rate_wilson_high": decisive_ci["ci_high"],
        "task_ids": [str(r["task_id"]) for r in records],
    }


def qualitative_by_task() -> dict[str, dict[str, Any]]:
    if not QUAL.exists():
        return {}
    raw = json.loads(QUAL.read_text(encoding="utf-8"))
    return {str(row.get("task_id")): row for row in raw if row.get("task_id")}


def win_task_sets() -> tuple[set[str], set[str]]:
    if not WIN_TASKS.exists():
        return set(), set()
    raw = json.loads(WIN_TASKS.read_text(encoding="utf-8"))
    return set(raw.get("semantic_ir_wins", [])), set(raw.get("test_only_wins", []))


def catchall_signal(row: dict[str, Any] | None, qual: dict[str, Any] | None) -> dict[str, Any]:
    feedback_items: list[dict[str, Any]] = []
    if qual and isinstance(qual.get("sample_feedback"), dict):
        feedback_items.append(qual["sample_feedback"])
    if row:
        feedback_items.extend(x for x in row.get("semantic_feedback", []) if isinstance(x, dict))
        for attempt in row.get("attempt_history", []):
            feedback_items.extend(
                x for x in attempt.get("semantic_feedback", []) if isinstance(x, dict)
            )

    for item in feedback_items:
        constraint = str(item.get("constraint_text", "")).lower()
        scenario = item.get("scenario_index")
        if "others" in constraint or scenario == 8:
            return {
                "has_catchall_signal": True,
                "violation_type": item.get("violation_type"),
                "scenario_index": scenario,
                "constraint_text": item.get("constraint_text"),
            }

    return {
        "has_catchall_signal": False,
        "violation_type": None,
        "scenario_index": None,
        "constraint_text": None,
    }


def candidate_rows(
    records: list[dict[str, Any]],
    by_task: dict[str, dict[str, Any]],
    limit: int = 40,
) -> list[dict[str, Any]]:
    qual = qualitative_by_task()
    semantic_wins, test_only_wins = win_task_sets()
    rows = []
    for rec in records:
        tid = str(rec["task_id"])
        signal = catchall_signal(by_task.get(tid, {}).get(FOCAL), qual.get(tid))
        row = {
            "rank": 0,
            "task_id": tid,
            "conf_test_only": float(rec["conf_test_only"]),
            "conf_semantic_ir": float(rec["conf_semantic_ir"]),
            "delta": float(rec["delta"]),
            "relation": rec["relation"],
            "is_current_semantic_ir_win": tid in semantic_wins,
            "is_current_test_only_win": tid in test_only_wins,
            "is_conf0_rescue_regime": abs(float(rec["conf_test_only"])) <= EPS,
            **signal,
        }
        row["rationale"] = (
            "E6 C>A win with qualitative catch-all/others evidence"
            if row["is_current_semantic_ir_win"]
            else "Headroom task with catch-all/others feedback signal"
            if row["has_catchall_signal"]
            else "Headroom task selected as fill candidate"
        )
        rows.append(row)

    rows.sort(
        key=lambda r: (
            not bool(r["is_current_semantic_ir_win"]),
            not bool(r["has_catchall_signal"]),
            not bool(r["is_conf0_rescue_regime"]),
            -float(r["delta"]),
            task_number(str(r["task_id"])),
        )
    )
    out = rows[:limit]
    for i, row in enumerate(out, start=1):
        row["rank"] = i
    return out


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def fmt_pp(value: float | None) -> str:
    if value is None:
        return "--"
    return f"{value:+.1f}"


def fmt_ci(lo: float | None, hi: float | None, scale: float = 1.0) -> str:
    if lo is None or hi is None:
        return "--"
    return f"[{scale * lo:.1f}, {scale * hi:.1f}]"


def write_tex(summary_rows: list[dict[str, Any]], path: Path) -> None:
    lines = [
        "% Auto-generated by scripts/e6_headroom_analysis.py -- do not hand-edit.",
        r"\begin{table}[t]",
        r"  \centering",
        r"  \caption{E6-H paired headroom analysis for C$-$A on \texttt{run\_feedback\_v2}.",
        r"    H is the subset where A/test-only has Conf$<1$; H0 is the stricter Conf$=0$ rescue subset.",
        r"    Cliff's $\delta$ is paired sign delta $(W-L)/n$; win-rate CI is Wilson on all paired tasks.}",
        r"  \label{tab:e6-headroom}",
        r"  \footnotesize",
        r"  \begin{tabular}{lccccc}",
        r"    \toprule",
        r"    Stratum & $n$ & W/L/T & $\Delta$Conf. pp & 95\% CI pp & $\delta$ / win CI \\",
        r"    \midrule",
    ]
    labels = {
        "all": "All",
        "H_conf_lt_1": r"H: A Conf$<1$",
        "H_conf_eq_0": r"H0: A Conf$=0$",
        "H_conf_gt_0_lt_1": r"H+: $0<$A Conf$<1$",
    }
    for row in summary_rows:
        delta = fmt_pp(row.get("delta_pp"))
        ci = fmt_ci(row.get("ci_low_pp"), row.get("ci_high_pp"))
        win_ci = fmt_ci(
            row.get("win_rate_all_wilson_low"),
            row.get("win_rate_all_wilson_high"),
            100.0,
        )
        cliffs = row.get("paired_cliffs_delta")
        cliffs_s = "--" if cliffs is None else f"{cliffs:+.3f}"
        lines.extend(
            [
                f"    {labels.get(row['stratum'], row['stratum'])} & {row['n_paired']} "
                f"& {row['wins']}/{row['losses']}/{row['ties']} "
                f"& ${delta}$ & ${ci}$ & ${cliffs_s}$ / ${win_ci}$ \\\\",
            ]
        )
    lines.extend(
        [
            r"    \bottomrule",
            r"  \end{tabular}",
            r"\end{table}",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def analyse(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_task = build_by_task(rows)
    records = []
    for tid, task_rows in by_task.items():
        rec = task_record(tid, task_rows)
        if rec:
            records.append(rec)

    strata = [
        (
            "all",
            records,
            "All C-A paired tasks.",
        ),
        (
            "H_conf_lt_1",
            [r for r in records if float(r["conf_test_only"]) < 1.0 - EPS],
            "Primary headroom subset H where A/test_only Conf < 1.",
        ),
        (
            "H_conf_eq_0",
            [r for r in records if abs(float(r["conf_test_only"])) <= EPS],
            "Strict rescue subset where A/test_only Conf = 0.",
        ),
        (
            "H_conf_gt_0_lt_1",
            [
                r
                for r in records
                if float(r["conf_test_only"]) > EPS
                and float(r["conf_test_only"]) < 1.0 - EPS
            ],
            "Partial-headroom subset where 0 < A/test_only Conf < 1.",
        ),
    ]
    summaries = [summarise_stratum(name, recs, desc) for name, recs, desc in strata]
    candidates = candidate_rows(strata[1][1], by_task)

    qual_counts = Counter()
    for row in candidates:
        if row["has_catchall_signal"]:
            qual_counts[str(row["constraint_text"])] += 1

    return {
        "source": None,
        "n_rows": len(rows),
        "n_tasks": len(by_task),
        "comparison": f"{FOCAL} - {COMPARATOR}",
        "strata": summaries,
        "catchall40_candidates": candidates,
        "catchall40_summary": {
            "n_candidates": len(candidates),
            "semantic_ir_wins_included": sum(
                1 for r in candidates if r["is_current_semantic_ir_win"]
            ),
            "conf0_rescue_regime_included": sum(
                1 for r in candidates if r["is_conf0_rescue_regime"]
            ),
            "catchall_signal_included": sum(1 for r in candidates if r["has_catchall_signal"]),
            "constraint_text_counts": dict(qual_counts),
            "selection_note": (
                "Ranked from primary H (A/test_only Conf<1), prioritizing existing "
                "semantic_ir wins and qualitative catch-all/others evidence."
            ),
        },
        "note": (
            "Bootstrap 95% CI is on mean paired C-A delta (B=5000, seed=42). "
            "Cliff's delta is reported as paired sign delta (wins-losses)/n. "
            "Wilson CI is reported for wins/n over all paired tasks and for wins/(wins+losses)."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    ap.add_argument("--out-dir", type=Path, default=PAPER_PROC)
    ap.add_argument("--table-dir", type=Path, default=TABLE_DIR)
    args = ap.parse_args()

    jsonl = args.run_dir / "results.jsonl"
    if not jsonl.exists():
        print(f"missing {jsonl}", file=sys.stderr)
        return 1

    rows = load_rows(jsonl)
    summary = analyse(rows)
    summary["source"] = str(jsonl.resolve())

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / OUT_JSON
    csv_path = out_dir / OUT_CSV
    candidate_path = out_dir / OUT_CANDIDATES
    tex_path = args.table_dir / OUT_TEX

    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    summary_fields = [
        "stratum",
        "description",
        "n_paired",
        "wins",
        "losses",
        "ties",
        "mean_focal",
        "mean_comparator",
        "delta_pp",
        "ci_low_pp",
        "ci_high_pp",
        "wilcoxon_p",
        "paired_cliffs_delta",
        "win_rate_all",
        "win_rate_all_wilson_low",
        "win_rate_all_wilson_high",
        "decisive_n",
        "decisive_win_rate",
        "decisive_win_rate_wilson_low",
        "decisive_win_rate_wilson_high",
    ]
    write_csv(csv_path, summary["strata"], summary_fields)
    candidate_fields = [
        "rank",
        "task_id",
        "conf_test_only",
        "conf_semantic_ir",
        "delta",
        "relation",
        "is_current_semantic_ir_win",
        "is_current_test_only_win",
        "is_conf0_rescue_regime",
        "has_catchall_signal",
        "violation_type",
        "scenario_index",
        "constraint_text",
        "rationale",
    ]
    write_csv(candidate_path, summary["catchall40_candidates"], candidate_fields)
    write_tex(summary["strata"], tex_path)

    print(f"source={summary['source']} n_rows={summary['n_rows']} n_tasks={summary['n_tasks']}")
    for row in summary["strata"]:
        print(
            f"{row['stratum']}: n={row['n_paired']} W/L/T={row['wins']}/{row['losses']}/{row['ties']} "
            f"delta={row['delta_pp']:+.1f} pp CI=[{row['ci_low_pp']:.1f}, {row['ci_high_pp']:.1f}] "
            f"cliff={row['paired_cliffs_delta']:+.3f} "
            f"win={100.0 * row['win_rate_all']:.1f}% "
            f"wilson=[{100.0 * row['win_rate_all_wilson_low']:.1f}, "
            f"{100.0 * row['win_rate_all_wilson_high']:.1f}]"
        )
    csum = summary["catchall40_summary"]
    print(
        f"CatchAll-40 candidates: n={csum['n_candidates']} "
        f"wins={csum['semantic_ir_wins_included']} "
        f"conf0={csum['conf0_rescue_regime_included']} "
        f"catchall_signal={csum['catchall_signal_included']}"
    )
    print(f"Wrote {json_path.relative_to(ROOT)}")
    print(f"Wrote {csv_path.relative_to(ROOT)}")
    print(f"Wrote {candidate_path.relative_to(ROOT)}")
    print(f"Wrote {tex_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
