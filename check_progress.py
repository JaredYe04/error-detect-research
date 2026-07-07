"""Quick progress monitor for running experiments."""
import json
import pathlib
import sys
import time

RUNS = [
    ("E1-ext (B3/B4/B5)", "artifacts/run_ccf_b_extended_v1/progress.json"),
    ("E6 (feedback variants)", "artifacts/run_feedback_v1/feedback_variants/progress.json"),
    ("Real-derived (E8c)", "artifacts/run_real_derived_v1/progress.json"),
    ("Generalisation v2", "artifacts/run_generalisation_v2/progress.json"),
]

def show_once():
    for name, path in RUNS:
        p = pathlib.Path(path)
        if not p.exists():
            print(f"{name}: not started")
            continue
        d = json.loads(p.read_text())
        eta = d.get("eta_sec") or 0
        rjobs = d.get("running_jobs", "?")
        rate = d.get("rate_per_sec", 0)
        print(
            f"{name}: {d['completed']}/{d['total']} ({d['percent']:.1f}%)"
            f"  running_jobs={rjobs}"
            f"  rate={rate:.3f}/s"
            f"  ETA={eta/60:.1f}min"
            f"  [{d['status']}]"
        )
        if d.get("last_message"):
            print(f"  last: {d['last_message'][:80]}")

if __name__ == "__main__":
    watch = "--watch" in sys.argv
    interval = 10
    while True:
        show_once()
        if not watch:
            break
        print("---")
        time.sleep(interval)
