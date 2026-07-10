#!/usr/bin/env python3
"""Aggregate n1n multi-model E6 / industrial / E16 campaign artifacts.

Resilient: missing or incomplete runs are skipped with a warning; partial
``results.jsonl`` files are still summarised.

Writes (under ``paper/hsp-agile/data/processed/``):
  - e6_n1n_cross_model.csv
  - industrial_cross_model.csv
  - e16_n1n_stratified.csv

Also writes ``paper/hsp-agile/tables/cross_model_{e6,industrial,e16}.tex``
and prints a markdown summary plus paste-ready PLACEHOLDER lines to stdout.

Usage:
  python paper/hsp-agile/scripts/aggregate_n1n_campaigns.py
  python paper/hsp-agile/scripts/aggregate_n1n_campaigns.py --artifacts-root artifacts
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PAPER = Path(__file__).resolve().parents[1]
PROC = PAPER / "data" / "processed"
TABLES = PAPER / "tables"

# (model_label, relative path under artifacts/)
E6_RUNS: list[tuple[str, str]] = [
    ("gpt-4o", "run_e6_n1n_gpt4o_s30/feedback_variants"),
    ("claude-4.6", "run_e6_n1n_claude46_s30/feedback_variants"),
    ("deepseek", "run_e6_n1n_deepseek_s30/feedback_variants"),
]

INDUSTRIAL_RUNS: list[tuple[str, str]] = [
    ("gpt-4o", "run_industrial_gpt4o_v1"),
    ("claude-4.6", "run_industrial_claude46_v1"),
    ("deepseek", "run_industrial_deepseek_v1"),  # optional
]

E16_RUNS: list[tuple[str, str]] = [
    ("gpt-4o", "run_e16_n1n_gpt4o_s30"),
    ("claude-4.6", "run_e16_n1n_claude46_s30"),  # optional
    ("deepseek", "run_e16_n1n_deepseek_s30"),  # optional
]

VARIANT_ORDER = ("test_only", "test_expected", "semantic_ir")
VARIANT_LABEL = {"test_only": "A", "test_expected": "B", "semantic_ir": "C"}
MODE_ORDER = ("B1", "B2", "M", "A1", "A2", "A3", "B0", "B3", "B4", "B5", "B6")


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _conf_of(row: dict) -> float | None:
    for key in ("formal_conformance", "strict_formal_conformance", "conf"):
        if key in row and row[key] is not None:
            try:
                return float(row[key])
            except (TypeError, ValueError):
                continue
    return None


def _success_of(row: dict) -> float | None:
    for key in ("strict_formal_passed", "success", "passed"):
        if key in row and row[key] is not None:
            val = row[key]
            if isinstance(val, bool):
                return 1.0 if val else 0.0
            try:
                return float(val)
            except (TypeError, ValueError):
                continue
    return None


def _latency_of(row: dict) -> float | None:
    if "latency_ms" in row and row["latency_ms"] is not None:
        try:
            return float(row["latency_ms"])
        except (TypeError, ValueError):
            return None
    return None


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def _fmt(x: float, digits: int = 4) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return ""
    return f"{x:.{digits}f}"


def _pct(x: float, digits: int = 1) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "XX.X"
    return f"{100.0 * x:.{digits}f}"


def _pp(x: float, digits: int = 1) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "XX.X"
    return f"{x:.{digits}f}"


def _warn(msg: str) -> None:
    print(f"[warn] {msg}", file=sys.stderr)


def _progress_note(run_dir: Path) -> str:
    prog = run_dir / "progress.json"
    if not prog.exists():
        return ""
    try:
        data = json.loads(prog.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    status = data.get("status", "?")
    completed = data.get("completed")
    total = data.get("total")
    if completed is not None and total is not None:
        return f"progress={completed}/{total} status={status}"
    return f"status={status}"


def _resolve_results(run_dir: Path) -> Path | None:
    """Prefer results.jsonl; accept nested feedback_variants/results.jsonl."""
    for candidate in (run_dir / "results.jsonl", run_dir / "feedback_variants" / "results.jsonl"):
        if candidate.exists():
            return candidate
    return None


def aggregate_e6(artifacts: Path) -> list[dict]:
    out: list[dict] = []
    for model, rel in E6_RUNS:
        run_dir = artifacts / rel
        results_path = _resolve_results(run_dir)
        if results_path is None:
            _warn(f"E6 missing: {run_dir} (no results.jsonl)")
            continue
        note = _progress_note(run_dir)
        if note:
            print(f"[e6] {model}: {note}", file=sys.stderr)
        rows = _load_jsonl(results_path)
        if not rows:
            _warn(f"E6 empty: {results_path}")
            continue

        by_var: dict[str, list[float]] = defaultdict(list)
        for r in rows:
            variant = r.get("feedback_variant") or r.get("variant")
            if not variant:
                continue
            c = _conf_of(r)
            if c is None:
                continue
            by_var[str(variant)].append(c)

        means: dict[str, tuple[float, int]] = {}
        for v in VARIANT_ORDER:
            vals = by_var.get(v, [])
            if vals:
                means[v] = (_mean(vals), len(vals))

        delta = float("nan")
        if "semantic_ir" in means and "test_only" in means:
            delta = (means["semantic_ir"][0] - means["test_only"][0]) * 100.0

        for v in VARIANT_ORDER:
            if v not in means:
                continue
            mean_conf, n = means[v]
            out.append(
                {
                    "model": model,
                    "variant": VARIANT_LABEL[v],
                    "mean_conf": round(mean_conf, 4),
                    "n": n,
                    "delta_C_minus_A_pp": round(delta, 2) if not math.isnan(delta) else "",
                }
            )
        missing = [VARIANT_LABEL[v] for v in VARIANT_ORDER if v not in means]
        if missing:
            _warn(f"E6 {model}: incomplete variants {missing} at {results_path}")
    return out


def aggregate_mode_runs(
    artifacts: Path,
    campaigns: list[tuple[str, str]],
    label: str,
    *,
    with_latency: bool,
) -> list[dict]:
    out: list[dict] = []
    for model, rel in campaigns:
        run_dir = artifacts / rel
        results_path = _resolve_results(run_dir)
        if results_path is None:
            # Optional deepseek / extra e16 dirs: skip quietly if absent.
            optional = "deepseek" in rel or (
                label == "e16" and "gpt4o" not in rel
            )
            if not run_dir.exists():
                if not optional:
                    _warn(f"{label} missing dir: {run_dir}")
                continue
            _warn(f"{label} missing results.jsonl: {run_dir}")
            continue
        note = _progress_note(run_dir)
        if note:
            print(f"[{label}] {model}: {note}", file=sys.stderr)
        rows = _load_jsonl(results_path)
        if not rows:
            _warn(f"{label} empty: {results_path}")
            continue

        by_mode: dict[str, list[dict]] = defaultdict(list)
        for r in rows:
            mode = r.get("mode")
            if not mode:
                continue
            by_mode[str(mode)].append(r)

        modes = [m for m in MODE_ORDER if m in by_mode] + sorted(
            m for m in by_mode if m not in MODE_ORDER
        )
        for mode in modes:
            group = by_mode[mode]
            confs = [c for c in (_conf_of(r) for r in group) if c is not None]
            succs = [s for s in (_success_of(r) for r in group) if s is not None]
            lats = [x for x in (_latency_of(r) for r in group) if x is not None]
            rec: dict = {
                "model": model,
                "mode": mode,
                "n": len(group),
                "conf": round(_mean(confs), 4) if confs else "",
                "strict": round(_mean(succs), 4) if succs else "",
            }
            if with_latency:
                rec["latency_ms"] = round(_mean(lats), 2) if lats else ""
            out.append(rec)
    return out


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)


def write_e6_tex(rows: list[dict], path: Path) -> None:
    """Write a conference-ready booktabs table (or PLACEHOLDER cells)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    by_model: dict[str, dict[str, dict]] = defaultdict(dict)
    for r in rows:
        by_model[r["model"]][r["variant"]] = r

    models = []
    for m, _ in E6_RUNS:
        if m in by_model:
            models.append(m)
    for m in by_model:
        if m not in models:
            models.append(m)

    lines = [
        r"% Auto-generated by aggregate_n1n_campaigns.py — do not edit by hand.",
        r"\begin{table}[t]",
        r"  \centering",
        r"  \caption{E6 feedback variants across n1n models "
        r"(A=\texttt{test\_only}, B=\texttt{test\_expected}, C=\texttt{semantic\_ir}). "
        r"Conf.\ as mean formal conformance (\%); "
        r"$\Delta$ is C$-$A in percentage points.}",
        r"  \label{tab:cross-model-e6}",
        r"  \footnotesize",
        r"  \begin{tabular}{lcccc}",
        r"    \toprule",
        r"    Model & A (\%) & B (\%) & C (\%) & $\Delta$(C$-$A) \\",
        r"    \midrule",
    ]

    if not models:
        lines.append(
            r"    \textit{(pending)} & XX.X & XX.X & XX.X & XX.X \\"
        )
    else:
        for model in models:
            cells = by_model[model]
            a = cells.get("A", {})
            b = cells.get("B", {})
            c = cells.get("C", {})
            a_s = _pct(float(a["mean_conf"])) if a.get("mean_conf") != "" and a else "XX.X"
            b_s = _pct(float(b["mean_conf"])) if b.get("mean_conf") != "" and b else "XX.X"
            c_s = _pct(float(c["mean_conf"])) if c.get("mean_conf") != "" and c else "XX.X"
            delta_raw = a.get("delta_C_minus_A_pp", "") if a else ""
            if delta_raw == "" and c:
                delta_raw = c.get("delta_C_minus_A_pp", "")
            try:
                d_s = _pp(float(delta_raw)) if delta_raw != "" else "XX.X"
            except (TypeError, ValueError):
                d_s = "XX.X"
            # Bold C when delta is available and positive
            c_cell = rf"\textbf{{{c_s}}}" if d_s != "XX.X" and float(delta_raw or 0) > 0 else c_s
            lines.append(f"    {model} & {a_s} & {b_s} & {c_cell} & {d_s} \\\\")

    lines.extend(
        [
            r"    \bottomrule",
            r"  \end{tabular}",
            r"\end{table}",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_mode_tex(
    rows: list[dict],
    path: Path,
    *,
    caption: str,
    label: str,
    with_latency: bool,
) -> None:
    """Write B1/B2/M booktabs table for industrial or E16 aggregates."""
    path.parent.mkdir(parents=True, exist_ok=True)
    by_model: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_model[r["model"]].append(r)

    model_order: list[str] = []
    for m, _ in (INDUSTRIAL_RUNS if with_latency else E16_RUNS):
        if m in by_model and m not in model_order:
            model_order.append(m)
    for m in by_model:
        if m not in model_order:
            model_order.append(m)

    if with_latency:
        header = r"    Model & Mode & $n$ & Conf.\ (\%) & Strict (\%) & Lat.\ (ms) \\"
        colspec = r"  \begin{tabular}{llcccc}"
        empty = r"    \textit{(pending)} & --- & --- & XX.X & XX.X & --- \\"
    else:
        header = r"    Model & Mode & $n$ & Conf.\ (\%) & Strict (\%) \\"
        colspec = r"  \begin{tabular}{llccc}"
        empty = r"    \textit{(pending)} & --- & --- & XX.X & XX.X \\"

    lines = [
        r"% Auto-generated by aggregate_n1n_campaigns.py — do not edit by hand.",
        r"\begin{table}[t]",
        r"  \centering",
        rf"  \caption{{{caption}}}",
        rf"  \label{{{label}}}",
        r"  \footnotesize",
        colspec,
        r"    \toprule",
        header,
        r"    \midrule",
    ]

    if not model_order:
        lines.append(empty)
    else:
        for model in model_order:
            first = True
            for r in by_model[model]:
                model_cell = model if first else ""
                first = False
                conf = r.get("conf", "")
                strict = r.get("strict", "")
                conf_s = _pct(float(conf)) if conf != "" else "XX.X"
                strict_s = _pct(float(strict)) if strict != "" else "XX.X"
                if with_latency:
                    lat = r.get("latency_ms", "")
                    lat_s = f"{float(lat):.0f}" if lat != "" else "---"
                    lines.append(
                        f"    {model_cell} & {r['mode']} & {r['n']} & "
                        f"{conf_s} & {strict_s} & {lat_s} \\\\"
                    )
                else:
                    lines.append(
                        f"    {model_cell} & {r['mode']} & {r['n']} & "
                        f"{conf_s} & {strict_s} \\\\"
                    )
            lines.append(r"    \addlinespace")
        if lines[-1].strip() == r"\addlinespace":
            lines.pop()

    lines.extend(
        [
            r"    \bottomrule",
            r"  \end{tabular}",
            r"\end{table}",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    sep = ["---"] * len(headers)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(sep) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def print_markdown(e6: list[dict], industrial: list[dict], e16: list[dict]) -> None:
    print("\n## n1n campaign aggregation\n")

    print("### E6 cross-model (feedback variants)\n")
    if not e6:
        print("_No E6 artifacts found yet._\n")
        print("Paste placeholders: A=XX.X%, B=XX.X%, C=XX.X%, delta(C-A)=XX.X pp\n")
    else:
        md_rows = []
        for r in e6:
            md_rows.append(
                [
                    r["model"],
                    r["variant"],
                    _pct(float(r["mean_conf"])) if r.get("mean_conf") != "" else "XX.X",
                    str(r["n"]),
                    str(r["delta_C_minus_A_pp"]) if r.get("delta_C_minus_A_pp") != "" else "XX.X",
                ]
            )
        print(_md_table(["model", "variant", "conf%", "n", "delta(C-A) pp"], md_rows))
        print()
        # compact paste lines per model
        by_model: dict[str, dict[str, dict]] = defaultdict(dict)
        for r in e6:
            by_model[r["model"]][r["variant"]] = r
        print("Paste-ready (per model):")
        for model, cells in by_model.items():
            a = cells.get("A", {}).get("mean_conf", "")
            b = cells.get("B", {}).get("mean_conf", "")
            c = cells.get("C", {}).get("mean_conf", "")
            d = cells.get("A", {}).get("delta_C_minus_A_pp") or cells.get("C", {}).get(
                "delta_C_minus_A_pp", ""
            )
            print(
                f"  {model}: A={_pct(float(a)) if a != '' else 'XX.X'}%, "
                f"B={_pct(float(b)) if b != '' else 'XX.X'}%, "
                f"C={_pct(float(c)) if c != '' else 'XX.X'}%, "
                f"delta(C-A)={d if d != '' else 'XX.X'} pp"
            )
        print()

    print("### Industrial cross-model\n")
    if not industrial:
        print("_No industrial artifacts found yet._\n")
    else:
        md_rows = []
        for r in industrial:
            conf = r.get("conf", "")
            strict = r.get("strict", "")
            lat = r.get("latency_ms", "")
            md_rows.append(
                [
                    r["model"],
                    r["mode"],
                    str(r["n"]),
                    _pct(float(conf)) if conf != "" else "XX.X",
                    _pct(float(strict)) if strict != "" else "XX.X",
                    str(lat) if lat != "" else "---",
                ]
            )
        print(_md_table(["model", "mode", "n", "conf%", "strict%", "latency_ms"], md_rows))
        print()

    print("### E16 n1n stratified\n")
    if not e16:
        print("_No E16 n1n artifacts found yet._\n")
    else:
        md_rows = []
        for r in e16:
            conf = r.get("conf", "")
            strict = r.get("strict", "")
            md_rows.append(
                [
                    r["model"],
                    r["mode"],
                    str(r["n"]),
                    _pct(float(conf)) if conf != "" else "XX.X",
                    _pct(float(strict)) if strict != "" else "XX.X",
                ]
            )
        print(_md_table(["model", "mode", "n", "conf%", "strict%"], md_rows))
        print()


def main() -> None:
    # Avoid Windows console UnicodeEncodeError on markdown dashes.
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifacts-root",
        type=Path,
        default=ROOT / "artifacts",
        help="Root directory containing run_* campaign folders.",
    )
    args = parser.parse_args()
    artifacts = args.artifacts_root.resolve()

    PROC.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)

    e6 = aggregate_e6(artifacts)
    industrial = aggregate_mode_runs(
        artifacts, INDUSTRIAL_RUNS, "industrial", with_latency=True
    )
    e16 = aggregate_mode_runs(artifacts, E16_RUNS, "e16", with_latency=False)

    write_csv(
        PROC / "e6_n1n_cross_model.csv",
        ["model", "variant", "mean_conf", "n", "delta_C_minus_A_pp"],
        e6,
    )
    write_csv(
        PROC / "industrial_cross_model.csv",
        ["model", "mode", "n", "conf", "strict", "latency_ms"],
        industrial,
    )
    write_csv(
        PROC / "e16_n1n_stratified.csv",
        ["model", "mode", "n", "conf", "strict"],
        e16,
    )
    write_e6_tex(e6, TABLES / "cross_model_e6.tex")
    write_mode_tex(
        industrial,
        TABLES / "cross_model_industrial.tex",
        caption=(
            r"Industrial SOFL corpus (B1/B2/M) on n1n endpoints. "
            r"Conf.\ = mean formal conformance; Strict = conjunctive accept rate."
        ),
        label="tab:cross-model-industrial",
        with_latency=True,
    )
    write_mode_tex(
        e16,
        TABLES / "cross_model_e16.tex",
        caption=(
            r"E16 stratified subset (B1/B2/M) on n1n endpoints."
        ),
        label="tab:cross-model-e16",
        with_latency=False,
    )

    print(f"Wrote {PROC / 'e6_n1n_cross_model.csv'} ({len(e6)} rows)", file=sys.stderr)
    print(f"Wrote {PROC / 'industrial_cross_model.csv'} ({len(industrial)} rows)", file=sys.stderr)
    print(f"Wrote {PROC / 'e16_n1n_stratified.csv'} ({len(e16)} rows)", file=sys.stderr)
    print(f"Wrote {TABLES / 'cross_model_e6.tex'}", file=sys.stderr)
    print(f"Wrote {TABLES / 'cross_model_industrial.tex'}", file=sys.stderr)
    print(f"Wrote {TABLES / 'cross_model_e16.tex'}", file=sys.stderr)

    print_markdown(e6, industrial, e16)


if __name__ == "__main__":
    main()
