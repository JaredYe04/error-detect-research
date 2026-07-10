#!/usr/bin/env python3
"""Import vendor Agile-SOFL ``.asfl`` examples into a benchmark JSON.

Preferred path for *real* production / toolchain SOFL artefacts:

  vendor/agile-sofl-toolchain/examples/*.asfl

Until those files exist (NDA / Hosei SpecTool packs), use the published-
industrial reconstruction instead::

  python scripts/export_published_industrial_pilot.py

Usage::

  python scripts/import_vendor_asfl.py \\
    --vendor-dir vendor/agile-sofl-toolchain/examples \\
    --out benchmarks/vendor_asfl_pilot.json

Requires Node.js and ``scripts/asfl_extract.mjs``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.asfl_bridge import collect_tasks_from_examples  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--vendor-dir",
        type=Path,
        default=ROOT / "vendor" / "agile-sofl-toolchain" / "examples",
        help="Directory containing *.asfl files",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "benchmarks" / "vendor_asfl_pilot.json",
        help="Output benchmark JSON path",
    )
    ap.add_argument(
        "--merge-published",
        action="store_true",
        help="Also append published-industrial reconstructions",
    )
    args = ap.parse_args()

    vendor_dir = args.vendor_dir
    if not vendor_dir.is_dir():
        print(
            f"[import_vendor_asfl] missing directory: {vendor_dir}\n"
            "  Place NDA / SpecTool .asfl files there, or run:\n"
            "    python scripts/export_published_industrial_pilot.py\n"
            "  See vendor/README.md for acquisition contacts.",
            file=sys.stderr,
        )
        return 2

    asfl_files = sorted(vendor_dir.glob("*.asfl"))
    if not asfl_files:
        print(
            f"[import_vendor_asfl] no *.asfl under {vendor_dir}\n"
            "  Acquisition order: Hosei SpecTool packs → Casco/Mitsubishi NDA → "
            "published-industrial fallback (vendor/README.md).",
            file=sys.stderr,
        )
        return 3

    tasks = collect_tasks_from_examples(vendor_dir)
    if args.merge_published:
        from src.benchmarks.published_industrial_pilot import (  # noqa: WPS433
            PUBLISHED_INDUSTRIAL_PILOT_TASKS,
        )

        tasks = list(tasks) + list(PUBLISHED_INDUSTRIAL_PILOT_TASKS)

    payload = {
        "name": "vendor_asfl_pilot",
        "n": len(tasks),
        "source": "vendor/agile-sofl-toolchain/examples",
        "honesty": (
            "Tasks imported from local .asfl files. Do not claim Casco/Mitsubishi "
            "production dumps unless those NDA artefacts are the files present."
        ),
        "tasks": tasks,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[import_vendor_asfl] wrote {len(tasks)} tasks → {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
