"""Backfill attempt_history into results.jsonl from saved LLM logs.

Replays formal checks (and pattern guard for M) on code extracted from
llm_logs/ without additional LLM calls. Used when results.jsonl predates
attempt_history logging in runner.py.

Usage:
    python experiments/backfill_attempt_history.py \\
        --run-dir artifacts/run_hard_full_parallel_v1 \\
        --modes M B2 B1
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.benchmarks import load_benchmark
from src.formal.checker import extract_python_code, run_formal_check
from src.patterns.matcher import PatternGuard
from src.pipeline.runner import config_for_mode


def _load_tasks() -> dict[str, dict]:
    tasks = load_benchmark()
    hard = [t for t in tasks if "HardSynthetic" in t.get("taskId", "")]
    return {t["taskId"]: t for t in hard}


def _collect_log_attempts(log_dir: Path, modes: set[str]) -> dict[tuple[str, str], dict[int, str]]:
    """Map (task_id, mode) -> {attempt: response_text}."""
    grouped: dict[tuple[str, str], dict[int, str]] = defaultdict(dict)
    if not log_dir.exists():
        return grouped
    for log_file in log_dir.rglob("llm_*.json"):
        try:
            data = json.loads(log_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        meta = data.get("metadata") or {}
        task_id = meta.get("task_id")
        mode = meta.get("mode")
        attempt = meta.get("attempt")
        if not task_id or mode not in modes or not attempt:
            continue
        response = data.get("response") or ""
        grouped[(task_id, mode)][int(attempt)] = response
    return grouped


def _build_history(
    task: dict,
    mode: str,
    attempt_responses: dict[int, str],
) -> list[dict]:
    cfg = config_for_mode(mode)
    guard = PatternGuard()
    history: list[dict] = []
    for attempt in sorted(attempt_responses.keys()):
        code = extract_python_code(attempt_responses[attempt])
        fr = run_formal_check(code, task, max_cases=cfg.formal_max_cases)
        high = 0
        if cfg.enable_patterns:
            matches = guard.check(code, task)
            high = sum(1 for m in matches if m.severity in {"high", "critical"})
        history.append({
            "attempt": attempt,
            "conf": fr.conformance_rate,
            "cex_count": len(fr.counterexamples),
            "pattern_count": high,
            "feedback_variant": cfg.feedback_variant,
            "source": "llm_log_backfill",
        })
    return history


def backfill(run_dir: Path, modes: list[str], *, in_place: bool = True) -> int:
    tasks = _load_tasks()
    log_dir = run_dir / "llm_logs"
    grouped = _collect_log_attempts(log_dir, set(modes))
    results_path = run_dir / "results.jsonl"
    if not results_path.exists():
        raise FileNotFoundError(results_path)

    updated = 0
    out_lines: list[str] = []
    with results_path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            mode = rec.get("mode")
            task_id = rec.get("task_id")
            if mode in modes and (task_id, mode) in grouped and task_id in tasks:
                history = _build_history(tasks[task_id], mode, grouped[(task_id, mode)])
                if history:
                    rec["attempt_history"] = history
                    updated += 1
            out_lines.append(json.dumps(rec, ensure_ascii=False))

    target = results_path if in_place else run_dir / "results_with_history.jsonl"
    target.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print(f"[backfill] Updated {updated} records → {target}")
    return updated


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--modes", nargs="+", default=["M", "B2", "B1"])
    parser.add_argument("--no-in-place", action="store_true")
    args = parser.parse_args()
    backfill(args.run_dir.resolve(), args.modes, in_place=not args.no_in_place)


if __name__ == "__main__":
    main()
