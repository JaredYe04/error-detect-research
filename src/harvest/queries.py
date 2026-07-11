"""Curated GitHub code/repo search queries for ordered-guard / formal specs."""

from __future__ import annotations

from typing import Any

# Code search (gh search code / REST search/code)
CODE_QUERIES: list[dict[str, Any]] = [
    {
        "id": "sofl_asfl",
        "query": "SOFL OR ASFL OR \"functional scenario\" extension:asfl OR extension:sofl",
        "notes": "Native Agile-SOFL / SOFL artefacts",
        "priority": 1,
    },
    {
        "id": "sofl_text",
        "query": "\"process\" \"pre\" \"post\" SOFL language:Markdown OR language:Text",
        "notes": "SOFL process snippets in docs",
        "priority": 2,
    },
    {
        "id": "decision_table_json",
        "query": "\"decision table\" OR decisionTable OR \"rules\" guard extension:json",
        "notes": "JSON decision tables",
        "priority": 1,
    },
    {
        "id": "decision_table_yaml",
        "query": "\"decision table\" OR decision_table OR \"ordered rules\" extension:yml OR extension:yaml",
        "notes": "YAML decision tables",
        "priority": 1,
    },
    {
        "id": "fsm_transitions",
        "query": "\"transitions\" \"guard\" state machine extension:json OR extension:yaml",
        "notes": "FSM transition tables with guards",
        "priority": 1,
    },
    {
        "id": "dmn_like",
        "query": "\"hitPolicy\" OR \"hit policy\" OR decisionTable extension:json OR extension:dmn",
        "notes": "DMN-like decision tables",
        "priority": 2,
    },
    {
        "id": "railway_interlock",
        "query": "interlocking route signal point guard railway extension:json OR extension:yml",
        "notes": "Railway interlocking-style tables",
        "priority": 1,
    },
    {
        "id": "alarm_priority",
        "query": "alarm severity priority preempt OR \"first match\" extension:json OR extension:yaml",
        "notes": "Alarm / severity ordered rules",
        "priority": 2,
    },
    {
        "id": "minizinc_guards",
        "query": "constraint guard extension:mzn",
        "notes": "MiniZinc (adapter candidate; lower priority for FSF)",
        "priority": 3,
    },
]

# Repo search (discovery → then list files)
REPO_QUERIES: list[dict[str, Any]] = [
    {"id": "sofl_repos", "query": "SOFL formal specification", "limit": 20},
    {"id": "agile_sofl", "query": "Agile-SOFL OR \"agile sofl\"", "limit": 10},
    {"id": "interlocking_spec", "query": "railway interlocking specification", "limit": 15},
    {"id": "decision_tables", "query": "decision table rules engine json", "limit": 15},
    {"id": "statemachine_yaml", "query": "state machine transitions yaml guard", "limit": 15},
]

# Filename / path globs when cloning or listing a repo tree
PATH_GLOBS: list[str] = [
    "*.asfl",
    "*.sofl",
    "*decision*table*.json",
    "*decision*table*.yml",
    "*decision*table*.yaml",
    "*statemachine*.json",
    "*state*machine*.yml",
    "*transitions*.json",
    "*transitions*.yml",
    "*interlock*.json",
    "*alarm*rule*.json",
    "*.dmn",
]

# Known public seeds (always try when auth works; also useful as smoke targets)
SEED_REPOS: list[dict[str, str]] = [
    {
        "fullName": "ShaoyingLiu/SOFL",
        "notes": "Placeholder — replace if 404; search will discover live mirrors",
    },
]
