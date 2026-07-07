"""Normalize pipeline task inputs (SpecIR or legacy TaskSpec dict)."""

from __future__ import annotations

from typing import Any

from src.ir.spec_ir import SpecIR
from src.ir.lowerers.fsf_lowerer import FSFLowerer


def normalize_task(task: SpecIR | dict[str, Any]) -> dict[str, Any]:
    """Return a TaskSpec dict for the HSP-Agile pipeline.

    Accepts either a SpecIR instance or a legacy TaskSpec dict.  SpecIR inputs
    are lowered via FSFLowerer.  Legacy dicts without embedded ``_spec_ir`` are
    canonicalised through ``SOFLAdapter.from_task_spec`` so every task carries
    the notation-agnostic SpecIR trace required by the framework layer.
    """
    if isinstance(task, SpecIR):
        return FSFLowerer.lower(task)
    if isinstance(task, dict) and "_spec_ir" in task:
        return task
    if isinstance(task, dict):
        if task.get("fsfScenarios"):
            from src.adapters.sofl_adapter import SOFLAdapter
            return FSFLowerer.lower(SOFLAdapter.from_task_spec(task))
        return task
    raise TypeError(f"Expected SpecIR or dict, got {type(task)!r}")
