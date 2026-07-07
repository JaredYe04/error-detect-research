"""Base adapter interface for SgDP framework instantiations.

An adapter translates a specification in language L into the TaskSpec IR
consumed by the shared pipeline, enabling generalisation study (E8).

Any new spec language must implement SpecAdapter and register its tasks
as a list of TaskSpec-compatible dicts (same schema as FSF tasks).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class SpecAdapter(ABC):
    """Abstract base for a specification language adapter.

    Subclasses must implement:
      - parse(spec_text) → task dict compatible with ErrorPreventionPipeline
      - notation_name: short string identifying the spec language
    """

    @property
    @abstractmethod
    def notation_name(self) -> str:
        """Short identifier, e.g. 'sofl', 'mini_z', 'statemachine'."""

    @abstractmethod
    def parse(self, spec_text: str, task_id: str) -> dict[str, Any]:
        """Parse a specification string into a TaskSpec IR dict.

        The returned dict must contain at minimum:
          taskId, name, signature (inputs/outputs), fsfScenarios (ordered),
          promptSpec, referenceCode (optional).

        The 'fsfScenarios' list must follow the FSF ordering convention:
          [{index, kind, test, def}, ..., {index, kind:'others', test:'others', def:...}]
        so that the shared formal checker and pattern guard work without modification.
        """

    def load_task_file(self, path: str) -> dict[str, Any]:
        """Convenience: read a spec file and parse it."""
        from pathlib import Path
        text = Path(path).read_text(encoding="utf-8")
        task_id = Path(path).stem
        return self.parse(text, task_id)

    def load_task_dir(self, dir_path: str) -> list[dict[str, Any]]:
        """Load all spec files from a directory."""
        from pathlib import Path
        tasks = []
        for p in sorted(Path(dir_path).iterdir()):
            if p.is_file() and p.suffix in (".spec", ".z", ".fsm", ".txt", ".json"):
                try:
                    tasks.append(self.load_task_file(str(p)))
                except Exception as e:
                    print(f"[adapter] Skipping {p}: {e}")
        return tasks
