#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Best-effort GitHub / public-spec harvest hints for RealSpec expansion.

Without a GitHub token this writes a curated seed list and optional local scan.
With `gh` available it can search repositories (best-effort).
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = (
    ROOT
    / "paper"
    / "hsp-agile"
    / "artifacts"
    / "strengthening_sprint"
    / "agent_d_industrial"
    / "github_seed_list.json"
)

SEEDS = [
    {
        "query": "SOFL formal specification",
        "notes": "Academic SOFL examples; prefer published case studies already in bib",
    },
    {
        "query": "extension:mzn MiniZinc",
        "notes": "Constraint problems ???candidate SpecIR lowering",
    },
    {
        "query": "state machine transition guard yaml OR json",
        "notes": "FSM transition tables",
    },
    {
        "query": "decision table requirements OR protocol",
        "notes": "Decision tables with ordered rules",
    },
    {
        "path_globs": ["*.fsm", "*.spec", "*statemachine*.json", "*decision*table*"],
        "notes": "Local / mirror scan patterns",
    },
]


def try_gh_search(query: str, limit: int = 5) -> list[dict]:
    try:
        proc = subprocess.run(
            ["gh", "search", "repos", query, "--limit", str(limit), "--json", "fullName,url,description"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if proc.returncode != 0:
            return [{"error": proc.stderr.strip() or "gh failed", "query": query}]
        return json.loads(proc.stdout or "[]")
    except Exception as e:  # noqa: BLE001
        return [{"error": str(e), "query": query}]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live-search", action="store_true", help="Call gh search (needs network + gh auth)")
    args = ap.parse_args()
    OUT.parent.mkdir(parents=True, exist_ok=True)

    payload = {"seeds": SEEDS, "live_results": []}
    if args.live_search:
        for s in SEEDS:
            q = s.get("query")
            if not q:
                continue
            payload["live_results"].append({"query": q, "repos": try_gh_search(q)})

    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
