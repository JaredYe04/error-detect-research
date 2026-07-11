"""Unit tests for GitHub harvest converters (no network)."""

from __future__ import annotations

from src.harvest.classify import classify_candidate
from src.harvest.to_fsf import classify_and_convert, decision_table_to_task, validate_task


def test_decision_table_roundtrip():
    table = {
        "name": "LinkAlert",
        "inputs": [
            {"name": "link_down", "type": "int"},
            {"name": "latency", "type": "int"},
        ],
        "outputs": [{"name": "severity", "type": "int"}],
        "rules": [
            {"guard": "link_down eq 1", "post": "severity eq 3"},
            {"guard": "latency gt 5", "post": "severity eq 2"},
        ],
        "default": {"post": "severity eq 0"},
    }
    task = decision_table_to_task(
        table, provenance={"repo": "example/repo", "path": "rules/link.json"}
    )
    st = validate_task(task)
    assert st["ok"], st


def test_classify_json_decision_table():
    text = """
    {
      "name": "X",
      "inputs": [{"name": "a", "type": "int"}],
      "outputs": [{"name": "b", "type": "int"}],
      "rules": [{"guard": "a gt 0", "post": "b eq 1"}],
      "default": {"post": "b eq 0"}
    }
    """
    rec = classify_candidate(path="x.json", text=text, repo="r/r")
    assert rec["kind"] == "decision_table"
    _rec, task, st = classify_and_convert(
        path="x.json", text=text, repo="r/r", query_id="test"
    )
    assert task is not None
    assert st.get("ok")


def test_python_ops_normalized():
    table = {
        "name": "Ops",
        "inputs": [{"name": "x", "type": "int"}],
        "outputs": [{"name": "y", "type": "int"}],
        "rules": [{"guard": "x >= 2", "post": "y == 1"}],
        "default": {"post": "y == 0"},
    }
    task = decision_table_to_task(table, provenance={"repo": "a/b", "path": "t.json"})
    assert "ge" in task["fsfScenarios"][0]["test"]
    st = validate_task(task)
    assert st["ok"], st
