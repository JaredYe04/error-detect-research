"""Monitor run progress from progress.json in real time."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


def _fmt_eta(sec: float | None) -> str:
    if sec is None:
        return "?"
    if sec < 60:
        return f"{sec:.0f}s"
    if sec < 3600:
        return f"{sec/60:.1f}m"
    return f"{sec/3600:.1f}h"


def main() -> None:
    parser = argparse.ArgumentParser(description="Monitor experiment progress.json")
    parser.add_argument("run_dir", type=Path, help="Run directory under artifacts/")
    parser.add_argument("--interval", type=float, default=2.0, help="Refresh interval (seconds)")
    args = parser.parse_args()

    progress_path = args.run_dir / "progress.json"
    print(f"Monitoring: {progress_path}")
    last_line = ""
    while True:
        if not progress_path.exists():
            line = "progress.json not found yet..."
            if line != last_line:
                print(line)
                last_line = line
            time.sleep(args.interval)
            continue
        try:
            data = json.loads(progress_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            time.sleep(args.interval)
            continue

        status = data.get("status", "unknown")
        completed = int(data.get("completed", 0))
        total = int(data.get("total", 0))
        percent = float(data.get("percent", 0.0))
        eta = _fmt_eta(data.get("eta_sec"))
        rate = float(data.get("rate_per_sec", 0.0))
        msg = data.get("last_message", "")
        line = (
            f"[{status}] {completed}/{total} ({percent:.2f}%) "
            f"rate={rate:.3f}/s eta={eta} last='{msg}'"
        )
        if line != last_line:
            print(line)
            last_line = line
        if status == "completed":
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
