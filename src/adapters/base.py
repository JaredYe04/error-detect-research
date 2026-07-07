"""Base adapter interface for SgDP framework instantiations.

An adapter translates a specification in language L into the SpecIR canonical
form, which is then lowered to a TaskSpec dict by the FSF Lowerer for the
shared pipeline. This enables generalisation study (E8).

Any new spec language must implement SpecAdapter; backward-compatible TaskSpec
dicts are obtained via to_task_spec() or load_task_file()/load_task_dir().
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any

from src.ir.spec_ir import SpecIR


class SpecAdapter(ABC):
    """Abstract base for a specification language adapter.

    Subclasses must implement:
      - parse(spec_text, task_id) → SpecIR (notation-agnostic IR)
      - notation_name: short string identifying the spec language

    The SpecIR produced by parse() is lowered to a TaskSpec dict by
    to_task_spec() using the FSFLowerer, preserving full backward
    compatibility with the existing pipeline.
    """

    @property
    @abstractmethod
    def notation_name(self) -> str:
        """Short identifier, e.g. 'sofl', 'mini_z', 'statemachine'."""

    @abstractmethod
    def parse(self, spec_text: str, task_id: str) -> SpecIR:
        """Parse a specification string into a SpecIR.

        The returned SpecIR contains all cases in first-match order,
        with guard_text and post_text populated for FSF round-tripping.
        Use to_task_spec() to obtain the FSF-shaped TaskSpec dict.
        """

    def to_task_spec(self, spec: SpecIR) -> dict[str, Any]:
        """Lower a SpecIR to a TaskSpec-compatible dict via FSFLowerer."""
        from src.ir.lowerers.fsf_lowerer import FSFLowerer
        return FSFLowerer.lower(spec)

    def load_task_file(self, path: Any) -> dict[str, Any]:
        """Convenience: read a spec file and return a TaskSpec dict."""
        from pathlib import Path
        text = Path(path).read_text(encoding="utf-8")
        task_id = Path(path).stem.replace("-", "_").replace(".", "_")
        return self.to_task_spec(self.parse(text, task_id))

    def load_task_dir(self, dir_path: Any) -> list[dict[str, Any]]:
        """Load all spec files from a directory."""
        from pathlib import Path
        tasks = []
        for p in Path(dir_path).iterdir():
            try:
                tasks.append(self.load_task_file(p))
            except Exception as e:
                print(f"[adapter] Skipping {p}: {e}")
        return tasks
