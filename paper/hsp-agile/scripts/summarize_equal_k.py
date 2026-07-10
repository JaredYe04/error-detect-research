#!/usr/bin/env python3
"""Summarize equal-K M vs B2 from existing artifacts and/or attempt_history.

Priority:
1) If a dedicated equal-K fixed-oracle run exists, use it.
2) Else truncate strengthened M attempt_history at K=3 when present.
3) Else report historical K=3 corpora as archive-only (not primary ranking).

Outputs:
  paper/hsp-agile/data/processed/equal_k_summary.json
  paper/hsp-agile/tables/equal_k_m_vs_b2.tex
  paper/hsp-agile/artifacts/P0_EQUAL_K_AND_E6_STATS.md
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / "artifacts"
OUT_PROC = Path(__file__).resolve().parents[1] / "data" / "processed"
OUT_TAB = Path(__file__).resolve().parents[1] / "tables"
OUT_ART = Path(__file__).resolve().parents[1] / "artifacts"


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def conf_of(r: dict) -> float | None:
    for k in ("strict_formal_conformance", "formal_conformance"):
        if k in r and r[k] is not None:
            return float(r[k])
    return None


def paired_wlt(a: dict[str, float], b: dict[str, float]) -> tuple[int, int, int]:
    wins = losses = ties = 0
    for tid in set(a) & set(b):
        d = a[tid] - b[tid]
        if d > 1e-12:
            wins += 1
        elif d < -1e-12:
            losses += 1
        else:
            ties += 1
    return wins, losses, ties


def summarize_run(run_name: str, modes: tuple[str, ...] = ("B1", "B2", "M", "M_eq")) -> dict | None:
    p = ART / run_name / "results.jsonl"
    if not p.exists():
        return None
    rows = load_jsonl(p)
    by_mode: dict[str, dict[str, float]] = defaultdict(dict)
    meta: dict[str, dict] = {}
    for r in rows:
        m = r.get("mode")
        if m not in modes:
            continue
        tid = r.get("task_id") or r.get("taskId")
        c = conf_of(r)
        if not tid or c is None:
            continue
        by_mode[m][tid] = c
        if m not in meta:
            meta[m] = {
                "configured_max_attempts": r.get("configured_max_attempts") or r.get("max_attempts"),
                "feedback_variant": r.get("feedback_variant"),
            }
    out_modes = {}
    for m, scores in by_mode.items():
        vals = list(scores.values())
        out_modes[m] = {
            "n": len(vals),
            "mean_conf": sum(vals) / len(vals) if vals else None,
            **meta.get(m, {}),
            "by_task": scores,
        }
    return {"run": run_name, "modes": out_modes}


def truncate_m_at_k(run_name: str, k: int = 3) -> dict | None:
    """If attempt_history exists on M rows, take Conf at min(k, last available)."""
    p = ART / run_name / "results.jsonl"
    if not p.exists():
        return None
    rows = load_jsonl(p)
    m_scores: dict[str, float] = {}
    b2_scores: dict[str, float] = {}
    used_hist = 0
    for r in rows:
        tid = r.get("task_id") or r.get("taskId")
        if not tid:
            continue
        mode = r.get("mode")
        if mode == "B2":
            c = conf_of(r)
            if c is not None:
                b2_scores[tid] = c
        elif mode == "M":
            hist = r.get("attempt_history") or []
            if isinstance(hist, list) and hist:
                # history entries may be dicts with conformance at attempt index
                chosen = None
                for entry in hist:
                    if not isinstance(entry, dict):
                        continue
                    att = entry.get("attempt") or entry.get("k") or entry.get("iteration")
                    conf = entry.get("strict_formal_conformance") or entry.get(
                        "formal_conformance"
                    ) or entry.get("conf")
                    if conf is None:
                        continue
                    if att is None or int(att) <= k:
                        chosen = float(conf)
                if chosen is not None:
                    m_scores[tid] = chosen
                    used_hist += 1
                    continue
            c = conf_of(r)
            if c is not None:
                m_scores[tid] = c
    if not m_scores or not b2_scores:
        return None
    w, l, t = paired_wlt(m_scores, b2_scores)
    return {
        "run": run_name,
        "protocol": f"truncate_M_attempt_history_at_K={k} vs final B2",
        "used_history_rows": used_hist,
        "n_paired": w + l + t,
        "M_mean": sum(m_scores.values()) / len(m_scores),
        "B2_mean": sum(b2_scores[t] for t in m_scores if t in b2_scores) / max(1, len(set(m_scores) & set(b2_scores))),
        "wins": w,
        "losses": l,
        "ties": t,
        "note": (
            "Proxy equal-K only if attempt_history present; "
            "otherwise falls back to final M Conf (NOT equal-K)."
        ),
    }


def write_tex(summary: dict, path: Path) -> None:
    eq = summary.get("equal_k_primary") or {}
    hist = summary.get("historical_k3") or {}
    lines = [
        r"% Auto-generated by summarize_equal_k.py -- do not edit by hand.",
        r"\begin{table}[t]",
        r"  \centering",
        r"  \caption{Equal-$K$ Conf.\ ranking hygiene.",
        r"    Lead mechanism evidence remains E6 ($K{=}3$ within~M).",
        r"    Primary equal-$K$ Conf.\ row: \texttt{run\_e1\_equal\_k\_v1}",
        r"    (B2 vs.\ \texttt{M\_eq}, both $K{=}3$).",
        r"    Strengthened E1 M-win ($K{=}5$ bundle) is a stress-test only.}",
        r"  \label{tab:equal-k}",
        r"  \footnotesize",
        r"  \begin{tabular}{llccc}",
        r"    \toprule",
        r"    Corpus & Protocol & B2 (\%) & M / M\_eq (\%) & $\Delta$ \\",
        r"    \midrule",
    ]
    if eq.get("modes"):
        b2 = eq["modes"].get("B2", {})
        m = eq["modes"].get("M_eq") or eq["modes"].get("M") or {}
        label = "M\\_eq" if "M_eq" in eq["modes"] else "M"
        if b2.get("mean_conf") is not None and m.get("mean_conf") is not None:
            dpp = 100 * (m["mean_conf"] - b2["mean_conf"])
            wlt = eq.get("paired_wlt") or {}
            wlt_s = ""
            if wlt:
                wlt_s = f" ({wlt.get('wins',0)}/{wlt.get('losses',0)}/{wlt.get('ties',0)})"
            lines.append(
                f"    \\textbf{{{eq['run']}}} & $K{{=}}3$ B2 vs.\\ {label}{wlt_s} & "
                f"{100*b2['mean_conf']:.1f} & \\textbf{{{100*m['mean_conf']:.1f}}} & "
                f"\\textbf{{{dpp:+.1f}\\,pp}} \\\\"
            )
    if hist.get("modes"):
        b2 = hist["modes"].get("B2", {})
        m = hist["modes"].get("M", {})
        if b2.get("mean_conf") is not None and m.get("mean_conf") is not None:
            dpp = 100 * (m["mean_conf"] - b2["mean_conf"])
            lines.append(
                f"    {hist['run']} (archive) & $K{{=}}3$ both & "
                f"{100*b2['mean_conf']:.1f} & {100*m['mean_conf']:.1f} & "
                f"{dpp:+.1f}\\,pp \\\\"
            )
    lines += [
        r"    \midrule",
        r"    E6 (within M) & $K{=}3$ feedback sweep & --- & --- & +7.7\,pp (C$-$A) \\",
        r"    E1 M-win (bundle) & M $K{=}5$ vs.\ B2 $K{=}3$ & 98.3 & 100.0 & +1.7\,pp \\",
        r"    \bottomrule",
        r"  \end{tabular}",
        r"\end{table}",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    # Dedicated equal-K fixed-oracle run
    equal = None
    for cand in ("run_e1_equal_k_v1", "run_e1_m_k3_fixed_v1"):
        equal = summarize_run(cand)
        if equal and equal.get("modes"):
            break
        equal = None

    if equal and "B2" in equal["modes"]:
        mkey = "M_eq" if "M_eq" in equal["modes"] else ("M" if "M" in equal["modes"] else None)
        if mkey:
            w, l, t = paired_wlt(equal["modes"][mkey]["by_task"], equal["modes"]["B2"]["by_task"])
            equal["paired_wlt"] = {"wins": w, "losses": l, "ties": t, "m_mode": mkey}
            equal["delta_pp"] = 100.0 * (
                equal["modes"][mkey]["mean_conf"] - equal["modes"]["B2"]["mean_conf"]
            )

    historical = summarize_run("run_hard_full_parallel_v1")
    canonical = summarize_run("run_e1_canonical_v1")
    proxy = truncate_m_at_k("run_e1_m_win_v2", k=3)

    hist_shape = None
    p = ART / "run_e1_m_win_v2" / "results.jsonl"
    if p.exists():
        for r in load_jsonl(p):
            if r.get("mode") == "M" and r.get("attempt_history"):
                hist_shape = r["attempt_history"][:3]
                break

    summary = {
        "equal_k_primary": equal,
        "historical_k3": historical,
        "canonical_pre_fix_k3": canonical,
        "proxy_truncate": proxy,
        "m_win_attempt_history_sample": hist_shape,
        "recommendation": (
            "Primary equal-K Conf ranking: run_e1_equal_k_v1 (B2 vs M_eq, K=3). "
            "Lead mechanism remains E6 (+7.7 pp). "
            "Strengthened E1 M-win (K=5) is stress-test only."
        ),
    }

    OUT_PROC.mkdir(parents=True, exist_ok=True)
    out_json = OUT_PROC / "equal_k_summary.json"
    # strip by_task for size
    slim = json.loads(json.dumps(summary, default=str))
    for key in ("equal_k_primary", "historical_k3", "canonical_pre_fix_k3"):
        block = slim.get(key)
        if block and "modes" in block:
            for m, d in block["modes"].items():
                d.pop("by_task", None)
    out_json.write_text(json.dumps(slim, indent=2), encoding="utf-8")
    write_tex(summary, OUT_TAB / "equal_k_m_vs_b2.tex")

    # Markdown status
    e6_path = OUT_PROC / "e6_paired_summary.json"
    e6 = json.loads(e6_path.read_text(encoding="utf-8")) if e6_path.exists() else None
    md = []
    md.append("# P0: Equal-K + E6 Stats Status\n")
    md.append("## E6 paired stats\n")
    if e6:
        md.append(f"- Source: `{e6.get('source')}`\n")
        for c in e6.get("comparisons", []):
            md.append(
                f"- vs `{c['comparator']}`: W/L/T={c['wins']}/{c['losses']}/{c['ties']}, "
                f"Δ={c['delta_pp']:+.1f} pp, "
                f"95% CI [{c.get('ci_low_pp')}, {c.get('ci_high_pp')}], "
                f"wilcoxon_p={c.get('wilcoxon_p')}\n"
            )
    else:
        md.append("- TODO: run `python paper/hsp-agile/scripts/e6_paired_analysis.py`\n")
    md.append("\n## Equal-K Conf ranking\n")
    md.append(
        f"- Fixed-oracle E1 (`run_e1_m_win_v2`): M K=5 vs B2 K=3 — **bundle**, not equal-K.\n"
    )
    if historical:
        b2 = historical["modes"]["B2"]["mean_conf"]
        m = historical["modes"]["M"]["mean_conf"]
        md.append(
            f"- Archive equal-K=3 (`run_hard_full_parallel_v1`): "
            f"B2 {100*b2:.1f}% / M {100*m:.1f}% "
            f"(pre-fix / different oracle regime — not primary).\n"
        )
    md.append(f"- Proxy truncate: `{json.dumps(proxy, default=str)[:500] if proxy else None}`\n")
    md.append(f"- Dedicated equal-K run: `{equal['run'] if equal else 'NOT FOUND'}`\n")
    if equal and equal.get("paired_wlt"):
        mkey = equal["paired_wlt"]["m_mode"]
        md.append(
            f"- **Primary:** {mkey} {100*equal['modes'][mkey]['mean_conf']:.1f}% vs B2 "
            f"{100*equal['modes']['B2']['mean_conf']:.1f}% "
            f"(Δ {equal.get('delta_pp', 0):+.1f} pp; "
            f"W/L/T {equal['paired_wlt']['wins']}/"
            f"{equal['paired_wlt']['losses']}/{equal['paired_wlt']['ties']})\n"
        )
    md.append("\n## Paper policy\n")
    md.append(
        "1. Lead Conf claim = E6 (+7.7 pp) at K=3 with paired CI.\n"
        "2. Equal-K Conf ranking = run_e1_equal_k_v1 (B2 vs M_eq).\n"
        "3. Fixed-oracle E1 M-win (K=5) reported as stress-test bundle only.\n"
        "4. Deploy claim = C4 (B2 default; M for Accept/FAR≤5%).\n"
    )
    OUT_ART.mkdir(parents=True, exist_ok=True)
    (OUT_ART / "P0_EQUAL_K_AND_E6_STATS.md").write_text("".join(md), encoding="utf-8")
    print(f"Wrote {out_json}")
    print(f"Wrote {OUT_TAB / 'equal_k_m_vs_b2.tex'}")
    print(f"Wrote {OUT_ART / 'P0_EQUAL_K_AND_E6_STATS.md'}")


if __name__ == "__main__":
    main()
