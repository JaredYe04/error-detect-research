"""Classify and lightly normalize harvested files into converter inputs."""

from __future__ import annotations

import json
import re
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # noqa: BLE001
    yaml = None


def _load_structured(text: str) -> Any | None:
    text = text.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:  # noqa: BLE001
        pass
    if yaml is not None:
        try:
            return yaml.safe_load(text)
        except Exception:  # noqa: BLE001
            return None
    return None


def classify_candidate(
    *,
    path: str,
    text: str,
    repo: str = "",
) -> dict[str, Any]:
    """Return classification record with optional structured payload."""
    lower = path.lower()
    kind = "unknown"
    payload: Any = None

    if lower.endswith(".asfl") or lower.endswith(".sofl"):
        kind = "asfl"
    elif lower.endswith(".dmn"):
        kind = "dmn"
    elif lower.endswith(".mzn"):
        kind = "minizinc"
    else:
        payload = _load_structured(text)
        if isinstance(payload, dict):
            if _looks_decision_table(payload):
                kind = "decision_table"
            elif _looks_fsm(payload):
                kind = "fsm"
            elif _looks_fsf_task(payload):
                kind = "fsf_task"
            elif _looks_dmn_json(payload):
                kind = "dmn_json"
        elif isinstance(payload, list) and payload and isinstance(payload[0], dict):
            if all("guard" in x or "when" in x or "if" in x for x in payload[:3]):
                kind = "rule_list"
                payload = {"name": path.split("/")[-1], "rules": payload}

    if kind == "unknown" and re.search(r"\bprocess\b.*\bpre\b|\bif\s*\(.*\)\s*=>", text, re.I | re.S):
        kind = "sofl_text"

    return {
        "repo": repo,
        "path": path,
        "kind": kind,
        "bytes": len(text.encode("utf-8")),
        "payload": payload if kind not in {"asfl", "sofl_text", "dmn", "minizinc"} else None,
        "text_preview": text[:400],
    }


def _looks_decision_table(obj: dict) -> bool:
    if "rules" in obj and isinstance(obj["rules"], list):
        return True
    if "decisionTable" in obj or "decision_table" in obj:
        return True
    if "inputs" in obj and "outputs" in obj and ("rules" in obj or "rows" in obj):
        return True
    return False


def _looks_fsm(obj: dict) -> bool:
    return "transitions" in obj and isinstance(obj["transitions"], list)


def _looks_fsf_task(obj: dict) -> bool:
    return "fsfScenarios" in obj and "signature" in obj


def _looks_dmn_json(obj: dict) -> bool:
    return "hitPolicy" in obj or "hit_policy" in obj or obj.get("kind") == "decisionTable"
