"""JSON Schema validation for SpecIR and Semantic Feedback IR artifacts."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO_ROOT / "schemas"


@lru_cache(maxsize=4)
def _load_schema(name: str) -> dict[str, Any]:
    path = SCHEMA_DIR / name
    return json.loads(path.read_text(encoding="utf-8"))


def validate_spec_ir(data: dict[str, Any]) -> None:
    """Validate a SpecIR dict against schemas/spec_ir.schema.json."""
    from jsonschema import Draft7Validator

    Draft7Validator(_load_schema("spec_ir.schema.json")).validate(data)


def validate_semantic_feedback(data: dict[str, Any]) -> None:
    """Validate one Semantic Feedback record against its JSON schema."""
    from jsonschema import Draft7Validator

    Draft7Validator(_load_schema("semantic_feedback.schema.json")).validate(data)
