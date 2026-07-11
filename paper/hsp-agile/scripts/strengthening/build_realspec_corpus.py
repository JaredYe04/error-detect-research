#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Merge existing non-synthetic benchmarks into RealSpec v1 (Agents C+D)."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT_JSON = ROOT / "benchmarks" / "realspec" / "realspec_v1.json"
OUT_README = ROOT / "benchmarks" / "realspec" / "README.md"
INV = (
    ROOT
    / "paper"
    / "hsp-agile"
    / "artifacts"
    / "strengthening_sprint"
    / "agent_c_realspec"
    / "REALSPEC_INVENTORY.md"
)

SOURCES = [
    ("benchmarks/external_sofl.json", "textbook"),
    ("benchmarks/manual_heldout.json", "textbook"),
    ("benchmarks/industrial_sofl.json", "industrial_pattern"),
    ("benchmarks/published_industrial_pilot.json", "published_case"),
    ("benchmarks/real_derived/humaneval_fsf.json", "real_derived"),
    ("benchmarks/real_derived/mbpp_fsf.json", "real_derived"),
]


def _load_tasks(path: Path) -> list[dict]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("tasks", "items", "benchmark"):
            if isinstance(data.get(key), list):
                return data[key]
    return []


def _content_hash(task: dict) -> str:
    scenarios = task.get("fsfScenarios") or task.get("scenarios") or []
    sig = task.get("signature") or {}
    blob = json.dumps({"scenarios": scenarios, "signature": sig}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def normalize(task: dict, source_file: str, source_type: str) -> dict:
    tid = task.get("taskId") or task.get("id") or task.get("name")
    if not tid:
        tid = f"realspec.{_content_hash(task)}"
    out = dict(task)
    out["taskId"] = str(tid)
    out["realspec"] = {
        "source_file": source_file.replace("\\", "/"),
        "source_type": source_type,
        "content_hash": _content_hash(task),
        "provenance": task.get("externalProvenance")
        or task.get("provenance")
        or task.get("source")
        or source_file,
    }
    # Ensure scenarios key
    if "fsfScenarios" not in out and "scenarios" in out:
        out["fsfScenarios"] = out["scenarios"]
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT_JSON)
    args = ap.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    INV.parent.mkdir(parents=True, exist_ok=True)

    merged: list[dict] = []
    seen_hash: set[str] = set()
    seen_id: set[str] = set()
    counts: dict[str, int] = {}
    skipped_dup = 0

    for rel, stype in SOURCES:
        path = ROOT / rel
        tasks = _load_tasks(path)
        for t in tasks:
            nt = normalize(t, rel, stype)
            h = nt["realspec"]["content_hash"]
            tid = nt["taskId"]
            if h in seen_hash or tid in seen_id:
                skipped_dup += 1
                continue
            seen_hash.add(h)
            seen_id.add(tid)
            merged.append(nt)
            counts[stype] = counts.get(stype, 0) + 1

    args.out.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")

    inv = [
        "# RealSpec Inventory",
        "",
        f"**Total tasks:** {len(merged)} (deduped; skipped {skipped_dup} duplicates)",
        "",
        "## By source_type",
        "",
        "| source_type | n |",
        "|-------------|--:|",
    ]
    for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
        inv.append(f"| {k} | {v} |")
    inv.extend(
        [
            "",
            "## Sources merged",
            "",
            *[f"- `{s}` ???`{t}`" for s, t in SOURCES],
            "",
            "## Gaps",
            "",
            "- GitHub live harvest still thin (see `harvest_github_specs.py`)",
            "- FSM / decision-table converters are stubs for expansion",
            "- No proprietary vendor dumps claimed",
            "",
            f"Output: `{args.out.relative_to(ROOT).as_posix()}`",
        ]
    )
    INV.write_text("\n".join(inv) + "\n", encoding="utf-8")

    readme = f"""# RealSpec v1

Non-synthetic / external-provenance ordered-guard tasks for HSP-Agile external validity.

- **File:** `realspec_v1.json`
- **Count:** {len(merged)}
- **Types:** {', '.join(f'{k}={v}' for k, v in sorted(counts.items()))}

Each task carries `realspec.source_type` and `realspec.provenance`.

Rebuild:

```bash
python paper/hsp-agile/scripts/strengthening/build_realspec_corpus.py
```
"""
    OUT_README.write_text(readme, encoding="utf-8")
    (
        ROOT
        / "paper"
        / "hsp-agile"
        / "artifacts"
        / "strengthening_sprint"
        / "agent_c_realspec"
        / "STATUS.md"
    ).write_text(
        f"# Agent C STATUS\n\nDONE: RealSpec v1 with {len(merged)} tasks.\n",
        encoding="utf-8",
    )
    (
        ROOT
        / "paper"
        / "hsp-agile"
        / "artifacts"
        / "strengthening_sprint"
        / "agent_d_industrial"
        / "COLLECTION_LOG.md"
    ).write_text(
        "# Industrial Collection Log\n\n"
        "## Harvested into RealSpec\n\n"
        f"- industrial_pattern: {counts.get('industrial_pattern', 0)}\n"
        f"- published_case: {counts.get('published_case', 0)}\n\n"
        "## Not claimed\n\n"
        "- Live proprietary Agile-SOFL vendor traces (blocked on access)\n"
        "- GitHub bulk scrape pending API / manual curation seeds\n",
        encoding="utf-8",
    )
    (
        ROOT
        / "paper"
        / "hsp-agile"
        / "artifacts"
        / "strengthening_sprint"
        / "agent_d_industrial"
        / "STATUS.md"
    ).write_text("# Agent D STATUS\n\nDONE: industrial sources folded into RealSpec; live vendor still TODO.\n", encoding="utf-8")

    print(f"RealSpec v1: {len(merged)} tasks ???{args.out}")
    print(counts)


if __name__ == "__main__":
    main()
