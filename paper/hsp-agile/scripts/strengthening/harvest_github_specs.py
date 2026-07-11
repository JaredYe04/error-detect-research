#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deprecated entrypoint — use scripts/harvest_github_wave3.py.

Keeps the old path working:
  python paper/hsp-agile/scripts/strengthening/harvest_github_specs.py --live-search
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TARGET = ROOT / "scripts" / "harvest_github_wave3.py"

if __name__ == "__main__":
    # Map legacy flag
    argv = []
    for a in sys.argv[1:]:
        if a == "--live-search":
            argv.append("--live")
        else:
            argv.append(a)
    if "--live" not in argv and "--dry-run-auth" not in argv:
        argv = ["--dry-run-auth", *argv]
    sys.argv = [str(TARGET), *argv]
    print(f"[deprecated] redirecting to {TARGET.relative_to(ROOT)}")
    runpy.run_path(str(TARGET), run_name="__main__")
