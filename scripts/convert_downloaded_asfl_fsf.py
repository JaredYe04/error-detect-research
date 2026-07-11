#!/usr/bin/env python3
"""Convert already-downloaded harvest files with the lightweight ASFL FSF parser."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.benchmarks.complexity import annotate_tasks_complexity
from src.harvest.asfl_fsf_lite import extract_fsf_tasks_from_asfl
from src.harvest.to_fsf import validate_task


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--download-dir",
        type=Path,
        default=ROOT / "artifacts" / "github_harvest" / "wave3_targeted_v1" / "downloaded",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "benchmarks" / "github_harvest_v1.json",
    )
    args = ap.parse_args()

    tasks: list[dict] = []
    rejected = []
    for path in sorted(args.download_dir.iterdir()):
        name = path.name.lower()
        if not (name.endswith(".asfl") or ".asfl" in name or name.endswith(".sofl") or ".sofl" in name):
            # also try txt modules that may embed FSF
            if not (".txt" in name and ("sofl" in name or "atm" in name or "course" in name or "hospital" in name or "stock" in name or "vending" in name or "transport" in name)):
                if ".asfl" not in name and not name.endswith(".asfl"):
                    # still try any file containing "FSF :"
                    text_probe = path.read_text(encoding="utf-8", errors="replace")
                    if "FSF" not in text_probe and "FSF :" not in text_probe:
                        continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if "FSF" not in text and "FSF :" not in text:
            continue
        # recover repo/path from filename convention OWNER_REPO__path
        parts = path.name.split("__", 1)
        repo = parts[0].replace("_", "/", 1) if "_" in parts[0] else parts[0]
        rel = parts[1].replace("_", "/") if len(parts) > 1 else path.name
        extracted = extract_fsf_tasks_from_asfl(
            text, provenance={"repo": repo, "path": rel, "local": str(path)}
        )
        for t in extracted:
            st = validate_task(t)
            if st.get("ok"):
                tasks.append(t)
                print(f"OK {t['taskId']} from {path.name}")
            else:
                rejected.append({"taskId": t.get("taskId"), "file": path.name, "status": st})
                print(f"REJECT {t.get('taskId')} {st}")

    # merge existing
    by_id = {t["taskId"]: t for t in tasks}
    if args.out.exists():
        try:
            for t in json.loads(args.out.read_text(encoding="utf-8")):
                by_id.setdefault(t["taskId"], t)
        except Exception:  # noqa: BLE001
            pass
    final = list(by_id.values())
    annotate_tasks_complexity(final)
    args.out.write_text(json.dumps(final, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    rej = args.out.with_name("github_harvest_v1_rejected.json")
    rej.write_text(json.dumps(rejected, indent=2), encoding="utf-8")
    print(f"Wrote {args.out} n={len(final)} rejected={len(rejected)}")
    return 0 if final else 1


if __name__ == "__main__":
    raise SystemExit(main())
