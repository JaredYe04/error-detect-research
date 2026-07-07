"""Build a 25-task precedence-sensitive proxy benchmark from hard synthetic tasks.

These tasks are structurally equivalent to real-world multi-branch specs but
sourced from the Z3-filtered hard suite (not HumanEval/MBPP). Used for E8c
external-validity plumbing without manual HumanEval conversion.

Usage:
    python scripts/build_real_derived_proxy.py --limit 25
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.benchmarks.complexity import annotate_tasks_complexity

OUT_PATH = ROOT / "benchmarks" / "real_derived_proxy_tasks.json"


def build_proxy(limit: int = 25) -> list[dict]:
    annotated_path = ROOT / "benchmarks" / "hard_tasks_annotated.json"
    hard_path = ROOT / "benchmarks" / "hard_tasks.json"
    if annotated_path.exists():
        tasks = json.loads(annotated_path.read_text(encoding="utf-8"))
    elif hard_path.exists():
        tasks = json.loads(hard_path.read_text(encoding="utf-8"))
        tasks = annotate_tasks_complexity(tasks)
    else:
        raise FileNotFoundError("Run scripts/build_benchmark.py --annotate first")

    hard = [t for t in tasks if "HardSynthetic" in t.get("taskId", "")]
    # Prefer high overlap + >= 4 scenarios
    ranked = sorted(
        hard,
        key=lambda t: (
            t.get("complexity", {}).get("overlap_density_tier") == "high",
            t.get("complexity", {}).get("overlap_rate", 0),
            t.get("complexity", {}).get("scenario_count", 0),
        ),
        reverse=True,
    )
    selected = ranked[:limit]
    proxy: list[dict] = []
    for t in selected:
        item = dict(t)
        orig_id = item["taskId"]
        item["taskId"] = orig_id.replace("HardSynthetic.", "RealProxy.")
        item["sourceDataset"] = "HardSyntheticProxy"
        item["sourceId"] = orig_id
        item["module"] = "RealProxy"
        proxy.append(item)
    return proxy


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--out", type=Path, default=OUT_PATH)
    args = parser.parse_args()
    proxy = build_proxy(args.limit)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(proxy, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(proxy)} proxy tasks → {args.out}")


if __name__ == "__main__":
    main()
