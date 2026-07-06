"""Merge multiple run_* result directories into one combined run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True, help="Output run directory")
    parser.add_argument("inputs", nargs="+", type=Path, help="Input run directories")
    args = parser.parse_args()

    out_dir = args.output
    out_dir.mkdir(parents=True, exist_ok=True)
    out_jsonl = out_dir / "results.jsonl"

    seen: set[tuple[str, str, int, int]] = set()
    merged: list[dict] = []
    for run_dir in args.inputs:
        path = run_dir / "results.jsonl"
        if not path.exists():
            continue
        for row in _read_jsonl(path):
            key = (row["mode"], row["task_id"], int(row.get("repeat", 0)), int(row.get("grid_idx", 0)))
            if key in seen:
                continue
            seen.add(key)
            merged.append(row)

    merged.sort(key=lambda r: (r["mode"], r.get("repeat", 0), r["task_id"]))
    out_jsonl.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in merged) + "\n", encoding="utf-8")

    meta = {
        "input_runs": [str(p) for p in args.inputs],
        "records": len(merged),
        "modes": sorted({r["mode"] for r in merged}),
        "tasks": len({r["task_id"] for r in merged}),
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Merged {len(merged)} records into {out_dir}")


if __name__ == "__main__":
    main()
