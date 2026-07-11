#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build Task Feature Database joining hard-task annotations + E6 (and optional equal-K) scores.

Outputs (default):
  paper/hsp-agile/artifacts/strengthening_sprint/agent_a_evidence/
    task_feature_db.csv / .json
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
DEFAULT_TASKS = ROOT / "benchmarks" / "hard_tasks_annotated.json"
DEFAULT_E6 = ROOT / "artifacts" / "run_feedback_v2" / "feedback_variants" / "results.jsonl"
DEFAULT_EQUAL_K = ROOT / "artifacts" / "run_e1_equal_k_v1" / "results.jsonl"
OUT_DIR = (
    ROOT
    / "paper"
    / "hsp-agile"
    / "artifacts"
    / "strengthening_sprint"
    / "agent_a_evidence"
)

REL_OPS = re.compile(r"\b(le|ge|lt|gt|eq|ne)\b", re.I)
AND_SPLIT = re.compile(r"\s&&\s")


def _load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _conf(row: dict) -> float:
    for key in ("strict_formal_conformance", "formal_conformance", "mean_conf"):
        if key in row and row[key] is not None:
            return float(row[key])
    return 0.0


def _guard_metrics(scenarios: list[dict]) -> dict:
    n_atoms = 0
    n_and = 0
    n_rel = 0
    n_others = 0
    max_atoms = 0
    for sc in scenarios:
        test = str(sc.get("test") or sc.get("guard") or "")
        if test.strip().lower() == "others" or sc.get("kind") == "others":
            n_others += 1
            continue
        atoms = [a for a in AND_SPLIT.split(test) if a.strip()]
        n_atoms += len(atoms)
        max_atoms = max(max_atoms, len(atoms))
        n_and += max(0, len(atoms) - 1)
        n_rel += len(REL_OPS.findall(test))
    return {
        "n_guard_atoms": n_atoms,
        "n_and_ops": n_and,
        "n_rel_ops": n_rel,
        "n_others": n_others,
        "max_atoms_per_guard": max_atoms,
        "mean_atoms_per_guard": round(n_atoms / max(len(scenarios) - n_others, 1), 4),
    }


def _attempt_stats(row: dict) -> dict:
    hist = row.get("attempt_history") or []
    confs = [float(h.get("formal_conformance", 0.0) or 0.0) for h in hist]
    fb_lens = []
    for h in hist:
        sf = h.get("semantic_feedback") or []
        fb_lens.append(len(json.dumps(sf, ensure_ascii=False)))
    regressions = 0
    for i in range(1, len(confs)):
        if confs[i] + 1e-12 < confs[i - 1]:
            regressions += 1
    return {
        "n_attempts": len(hist),
        "conf_attempt_1": confs[0] if confs else None,
        "conf_attempt_last": confs[-1] if confs else None,
        "n_conf_regressions": regressions,
        "mean_feedback_json_len": round(sum(fb_lens) / len(fb_lens), 1) if fb_lens else 0.0,
    }


def build_features(
    tasks_path: Path,
    e6_path: Path,
    equal_k_path: Path | None,
) -> list[dict]:
    tasks = json.loads(tasks_path.read_text(encoding="utf-8"))
    e6_rows = _load_jsonl(e6_path)
    by_task_variant: dict[str, dict[str, dict]] = defaultdict(dict)
    for r in e6_rows:
        tid = r.get("task_id") or r.get("taskId")
        var = r.get("feedback_variant") or r.get("variant")
        if tid and var:
            by_task_variant[str(tid)][str(var)] = r

    equal_k: dict[str, dict[str, float]] = defaultdict(dict)
    if equal_k_path and equal_k_path.exists():
        for r in _load_jsonl(equal_k_path):
            tid = r.get("task_id") or r.get("taskId")
            mode = str(r.get("mode") or "")
            if tid and mode:
                equal_k[str(tid)][mode] = _conf(r)

    out: list[dict] = []
    for t in tasks:
        tid = t["taskId"]
        sig = t.get("signature") or {}
        scenarios = t.get("fsfScenarios") or []
        cx = t.get("complexity") or {}
        prompt = t.get("promptSpec") or ""
        gm = _guard_metrics(scenarios)
        row: dict = {
            "task_id": tid,
            "n_scenarios": int(cx.get("scenario_count") or len(scenarios)),
            "n_inputs": len(sig.get("inputs") or []),
            "n_outputs": len(sig.get("outputs") or []),
            "overlap_rate": float(cx.get("overlap_rate") or 0.0),
            "overlap_density_tier": cx.get("overlap_density_tier") or "unknown",
            "guard_complexity": cx.get("guard_complexity") or "unknown",
            "has_external_vars": bool(cx.get("has_external_vars")),
            "prompt_spec_len": len(prompt) if isinstance(prompt, str) else len(json.dumps(prompt)),
            "multi_output": int(len(sig.get("outputs") or []) >= 2),
            **gm,
        }

        variants = by_task_variant.get(tid, {})
        for vname in ("test_only", "test_expected", "semantic_ir"):
            vr = variants.get(vname)
            if vr is None:
                row[f"conf_{vname}"] = None
                row[f"attempts_{vname}"] = None
                continue
            row[f"conf_{vname}"] = _conf(vr)
            stats = _attempt_stats(vr)
            row[f"attempts_{vname}"] = stats["n_attempts"]
            if vname == "semantic_ir":
                row.update({f"ir_{k}": v for k, v in stats.items()})

        c_ir = row.get("conf_semantic_ir")
        c_a = row.get("conf_test_only")
        c_b = row.get("conf_test_expected")
        if c_ir is not None and c_a is not None:
            delta = float(c_ir) - float(c_a)
            row["delta_ir_minus_test_only"] = round(delta, 6)
            if delta > 1e-12:
                row["e6_winner"] = "semantic_ir"
            elif delta < -1e-12:
                row["e6_winner"] = "test_only"
            else:
                row["e6_winner"] = "tie"
        else:
            row["delta_ir_minus_test_only"] = None
            row["e6_winner"] = "missing"

        if c_ir is not None and c_b is not None:
            row["delta_ir_minus_test_expected"] = round(float(c_ir) - float(c_b), 6)
        else:
            row["delta_ir_minus_test_expected"] = None

        ek = equal_k.get(tid, {})
        if "B2" in ek and ("M_eq" in ek or "M" in ek):
            m_score = ek.get("M_eq", ek.get("M"))
            row["conf_equal_k_b2"] = ek["B2"]
            row["conf_equal_k_m"] = m_score
            d = float(m_score) - float(ek["B2"])
            row["delta_equal_k_m_minus_b2"] = round(d, 6)
            if d > 1e-12:
                row["equal_k_winner"] = "M"
            elif d < -1e-12:
                row["equal_k_winner"] = "B2"
            else:
                row["equal_k_winner"] = "tie"
        else:
            row["conf_equal_k_b2"] = None
            row["conf_equal_k_m"] = None
            row["delta_equal_k_m_minus_b2"] = None
            row["equal_k_winner"] = "missing"

        out.append(row)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tasks", type=Path, default=DEFAULT_TASKS)
    ap.add_argument("--e6", type=Path, default=DEFAULT_E6)
    ap.add_argument("--equal-k", type=Path, default=DEFAULT_EQUAL_K)
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    rows = build_features(args.tasks, args.e6, args.equal_k)
    json_path = args.out_dir / "task_feature_db.json"
    csv_path = args.out_dir / "task_feature_db.csv"
    json_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")

    if rows:
        keys = list(rows[0].keys())
        import csv

        with csv_path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(rows)

    wins = sum(1 for r in rows if r.get("e6_winner") == "semantic_ir")
    losses = sum(1 for r in rows if r.get("e6_winner") == "test_only")
    ties = sum(1 for r in rows if r.get("e6_winner") == "tie")
    print(f"Wrote {len(rows)} rows ???{json_path}")
    print(f"E6 winners: IR={wins} test_only={losses} tie={ties}")


if __name__ == "__main__":
    main()
