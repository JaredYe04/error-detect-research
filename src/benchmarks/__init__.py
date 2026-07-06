"""Build and persist benchmark task suite."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.asfl_bridge import collect_tasks_from_examples
from src.benchmarks.hard_gen import generate_hard_tasks
from src.benchmarks.references import get_reference_code

ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_PATH = ROOT / "benchmarks" / "tasks.json"
HARD_BENCHMARK_PATH = ROOT / "benchmarks" / "hard_tasks.json"


def build_benchmark(*, min_scenarios: int = 1) -> list[dict[str, Any]]:
    tasks = collect_tasks_from_examples()
    enriched: list[dict[str, Any]] = []
    for task in tasks:
        if len(task.get("fsfScenarios", [])) < min_scenarios:
            continue
        ref = get_reference_code(task["taskId"], task)
        if ref:
            task["referenceCode"] = ref
            enriched.append(task)
    return enriched


def save_hard_benchmark(
    *,
    path: Path | None = None,
    n_tasks: int = 160,
    scenarios_per_task: int = 8,
    seed: int = 42,
) -> Path:
    path = path or HARD_BENCHMARK_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    tasks = generate_hard_tasks(
        n_tasks=n_tasks,
        scenarios_per_task=scenarios_per_task,
        seed=seed,
    )
    path.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def save_benchmark(path: Path | None = None, *, include_hard: bool = True) -> Path:
    path = path or BENCHMARK_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    tasks = build_benchmark()
    if include_hard:
        if not HARD_BENCHMARK_PATH.exists():
            save_hard_benchmark()
        hard_tasks = json.loads(HARD_BENCHMARK_PATH.read_text(encoding="utf-8"))
        tasks.extend(hard_tasks)
    path.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_benchmark(path: Path | None = None, *, include_hard: bool = True) -> list[dict[str, Any]]:
    path = path or BENCHMARK_PATH
    if not path.exists():
        save_benchmark(path, include_hard=include_hard)
    return json.loads(path.read_text(encoding="utf-8"))
