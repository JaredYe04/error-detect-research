#!/usr/bin/env python3
"""Pool gemini combo n40 + extra40 into n80 C2 support summary + tex."""

from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = [
    ROOT / "artifacts" / "run_ir_combo_seed_gemini_n40_v1" / "results.jsonl",
    ROOT / "artifacts" / "run_ir_combo_seed_gemini_extra40_v1" / "results.jsonl",
]
OUT_JSON = ROOT / "paper" / "hsp-agile" / "data" / "processed" / "gemini_combo_n80_summary.json"
OUT_TEX = ROOT / "paper" / "hsp-agile" / "tables" / "gemini_combo_n80.tex"
OUT_ART = (
    ROOT
    / "paper"
    / "hsp-agile"
    / "artifacts"
    / "strengthening_sprint"
    / "gemini_combo_n80_summary.json"
)
VARIANTS = ("test_only", "test_expected", "semantic_ir", "ir_no_expected")
SEEDS = ("combo_invert_relop", "combo_swap_relop", "drop_first_guard")


def _load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _ci(deltas: list[float], *, b: int = 5000, seed: int = 42) -> tuple[float, float]:
    rng = random.Random(seed)
    n = len(deltas)
    means = sorted(sum(deltas[rng.randrange(n)] for _ in range(n)) / n for _ in range(b))
    return means[int(0.025 * b)], means[int(0.975 * b)]


def paired(by_cell: dict[tuple[str, str], dict[str, float]], focal: str, comp: str) -> dict:
    deltas = []
    for scores in by_cell.values():
        if focal in scores and comp in scores:
            deltas.append(scores[focal] - scores[comp])
    if not deltas:
        return {}
    w = sum(1 for d in deltas if d > 1e-12)
    l = sum(1 for d in deltas if d < -1e-12)
    t = len(deltas) - w - l
    lo, hi = _ci(deltas)
    return {
        "n": len(deltas),
        "full_mean": sum(by_cell[k][focal] for k in by_cell if focal in by_cell[k] and comp in by_cell[k])
        / len(deltas),
        "comp_mean": sum(by_cell[k][comp] for k in by_cell if focal in by_cell[k] and comp in by_cell[k])
        / len(deltas),
        "delta_pp": 100 * sum(deltas) / len(deltas),
        "wins": w,
        "losses": l,
        "ties": t,
        "ci95_pp": [100 * lo, 100 * hi],
        "ci_excludes_0": bool(lo > 0 or hi < 0),
    }


def main() -> int:
    rows = []
    for p in RUNS:
        rows.extend(_load(p))
    # keep only combo seeds + core variants
    rows = [
        r
        for r in rows
        if r.get("seed_type") in SEEDS and r.get("feedback_variant") in VARIANTS
    ]
    by_cell: dict[tuple[str, str], dict[str, float]] = defaultdict(dict)
    tasks = set()
    for r in rows:
        tid, st = r["task_id"], r["seed_type"]
        by_cell[(tid, st)][r["feedback_variant"]] = float(r["formal_conformance"])
        tasks.add(tid)

    # Prefer cells that have at least FULL + test_only
    cells = {k: v for k, v in by_cell.items() if "semantic_ir" in v and "test_only" in v}

    summary = {
        "run": "pooled n40 + extra40",
        "model": "gemini-2.5-flash",
        "n_tasks": len(tasks),
        "n_paired_cells": len(cells),
        "n_rows": len(rows),
        "pooled": {},
        "by_seed_vs_test_only": {},
    }
    for comp in ("test_only", "test_expected", "ir_no_expected"):
        summary["pooled"][comp] = paired(cells, "semantic_ir", comp)
    for seed in SEEDS:
        sub = {k: v for k, v in cells.items() if k[1] == seed}
        summary["by_seed_vs_test_only"][seed] = paired(sub, "semantic_ir", "test_only")

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    OUT_ART.parent.mkdir(parents=True, exist_ok=True)
    OUT_ART.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    p = summary["pooled"]
    to = p.get("test_only") or {}
    te = p.get("test_expected") or {}
    ne = p.get("ir_no_expected") or {}

    def row(label: str, d: dict) -> str:
        if not d:
            return f"    {label} & --- & --- & --- & --- \\\\"
        excl = "Yes" if d.get("ci_excludes_0") else "No"
        return (
            f"    {label} & \\textbf{{+{d['delta_pp']:.1f}}} & "
            f"{d['wins']}/{d['losses']}/{d['ties']} & "
            f"$[{d['ci95_pp'][0]:.1f},\\,{d['ci95_pp'][1]:.1f}]$ & {excl} \\\\"
            if d["delta_pp"] >= 0
            else (
                f"    {label} & ${d['delta_pp']:.1f}$ & "
                f"{d['wins']}/{d['losses']}/{d['ties']} & "
                f"$[{d['ci95_pp'][0]:.1f},\\,{d['ci95_pp'][1]:.1f}]$ & {excl} \\\\"
            )
        )

    lines = [
        "% Auto-pooled from run_ir_combo_seed_gemini_n40_v1 + extra40_v1.",
        "\\begin{table}[t]",
        "  \\centering",
        "  \\caption{Hard combo-seed feedback contrast on \\texttt{gemini-2.5-flash}",
        "    (pooled $n{\\approx}" + str(summary["n_tasks"]) + "$ tasks $\\times$ 3 seed types;",
        "    \\texttt{run\\_ir\\_combo\\_seed\\_gemini\\_n40\\_v1}+\\texttt{extra40}).",
        "    FULL $=$ \\texttt{semantic\\_ir}.",
        "    Lead C2 remains E6 on \\texttt{ecnu-plus}; this table strengthens",
        "    supporting evidence under harder injected bugs.",
        "    FULL beats unstructured test-only / test$+$expected when CI excludes~0;",
        "    FULL vs.\\ \\texttt{ir\\_no\\_expected} remains scoped (E14-consistent).}",
        "  \\label{tab:gemini-combo-n80}",
        "  \\footnotesize",
        "  \\begin{tabular}{lcccc}",
        "    \\toprule",
        "    Contrast & $\\Delta$ (pp) & W/L/T & 95\\% CI (pp) & Excl.~0 \\\\",
        "    \\midrule",
        f"    \\multicolumn{{5}}{{l}}{{\\textit{{Pooled}} ($n{{=}}{to.get('n', 0)}$ task$\\times$seed cells)}} \\\\",
        row("FULL vs.\\ \\texttt{test\\_only}", to),
        row("FULL vs.\\ \\texttt{test\\_expected}", te),
        row("FULL vs.\\ \\texttt{ir\\_no\\_expected}", ne) if ne else "    FULL vs.\\ \\texttt{ir\\_no\\_expected} & --- & --- & --- & --- \\\\",
        "    \\midrule",
        "    \\multicolumn{5}{l}{\\textit{By seed} (FULL vs.\\ \\texttt{test\\_only})} \\\\",
    ]
    for seed in SEEDS:
        d = summary["by_seed_vs_test_only"].get(seed) or {}
        lines.append(row(f"\\texttt{{{seed}}}", d))
    lines += [
        "    \\bottomrule",
        "  \\end{tabular}",
        "\\end{table}",
        "",
    ]
    OUT_TEX.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print("->", OUT_JSON)
    print("->", OUT_TEX)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
