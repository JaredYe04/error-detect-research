"""Bridge to Node.js Agile-SOFL parser."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EXTRACT_SCRIPT = ROOT / "scripts" / "asfl_extract.mjs"


def extract_spec(asfl_path: str | Path, *, tasks: bool = False) -> dict[str, Any]:
    """Parse an .asfl file and return structured JSON via the Node bridge."""
    path = Path(asfl_path).resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    cmd = ["node", str(EXTRACT_SCRIPT), str(path)]
    if tasks:
        cmd.append("--tasks")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        check=False,
    )
    if result.returncode != 0 and not result.stdout.strip():
        raise RuntimeError(f"asfl_extract failed: {result.stderr}")
    data = json.loads(result.stdout)
    return data


def collect_tasks_from_examples(examples_dir: str | Path | None = None) -> list[dict[str, Any]]:
    """Collect codegen tasks from all example specifications."""
    base = Path(examples_dir or ROOT / "vendor" / "agile-sofl-toolchain" / "examples")
    tasks: list[dict[str, Any]] = []
    for asfl in sorted(base.glob("*.asfl")):
        data = extract_spec(asfl, tasks=True)
        if not data.get("ok"):
            continue
        for task in data.get("tasks", []):
            task["sourceBasename"] = asfl.name
            tasks.append(task)
    return tasks
