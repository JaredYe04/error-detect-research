#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stub: convert decision-table / FSM transition rows into FSF-like scenarios."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def decision_table_to_fsf(table: dict) -> dict:
    """Convert a simple ordered decision table to an FSF-shaped task.

    Expected input::
        {
          "name": "...",
          "inputs": [{"name": "x", "type": "nat"}, ...],
          "outputs": [{"name": "y", "type": "nat"}, ...],
          "rules": [
            {"guard": "x gt 0", "post": "y eq 1"},
            ...
          ],
          "default": {"post": "y eq 0"}
        }
    """
    scenarios = []
    for i, rule in enumerate(table.get("rules") or [], start=1):
        scenarios.append(
            {
                "index": i,
                "kind": "scenario",
                "test": rule["guard"],
                "def": rule["post"],
            }
        )
    if table.get("default"):
        scenarios.append(
            {
                "index": len(scenarios) + 1,
                "kind": "others",
                "test": "others",
                "def": table["default"]["post"],
            }
        )
    return {
        "taskId": f"DecisionTable.{table.get('name', 'anon')}",
        "kind": "process",
        "signature": {"inputs": table.get("inputs", []), "outputs": table.get("outputs", [])},
        "fsfScenarios": scenarios,
        "realspec": {"source_type": "decision_table", "provenance": table.get("provenance", "hand-authored")},
    }


def fsm_to_fsf(fsm: dict) -> dict:
    """Convert flat guarded transitions (state, guard, action/next) to ordered scenarios."""
    scenarios = []
    for i, tr in enumerate(fsm.get("transitions") or [], start=1):
        guard = tr.get("guard") or "true"
        src = tr.get("from") or tr.get("source")
        post = tr.get("post") or f"state eq {tr.get('to') or tr.get('target')}"
        scenarios.append(
            {
                "index": i,
                "kind": "scenario",
                "test": f"(state eq {src}) && ({guard})" if src is not None else guard,
                "def": post,
            }
        )
    scenarios.append(
        {
            "index": len(scenarios) + 1,
            "kind": "others",
            "test": "others",
            "def": fsm.get("default_post", "state eq state"),
        }
    )
    return {
        "taskId": f"FSM.{fsm.get('name', 'anon')}",
        "kind": "process",
        "signature": fsm.get(
            "signature",
            {
                "inputs": [{"name": "state", "type": "nat"}, {"name": "event", "type": "nat"}],
                "outputs": [{"name": "state", "type": "nat"}],
            },
        ),
        "fsfScenarios": scenarios,
        "realspec": {"source_type": "fsm", "provenance": fsm.get("provenance", "hand-authored")},
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--example", action="store_true", help="Emit a worked example JSON")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    example = decision_table_to_fsf(
        {
            "name": "LinkAlert",
            "provenance": "industrial vignette (telecom severity ordering)",
            "inputs": [
                {"name": "link_down", "type": "nat"},
                {"name": "latency_ms", "type": "nat"},
            ],
            "outputs": [{"name": "severity", "type": "nat"}],
            "rules": [
                {"guard": "link_down eq 1", "post": "severity eq 3"},
                {"guard": "latency_ms gt 200", "post": "severity eq 2"},
            ],
            "default": {"post": "severity eq 0"},
        }
    )
    text = json.dumps(example, indent=2)
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    if args.example or not args.out:
        print(text)


if __name__ == "__main__":
    main()
