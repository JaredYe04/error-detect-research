"""Additional SMT stress probe: more variables / nonlinear-ish constraints.

Shows when witness cost grows so the paper can motivate hybrid fuzzing.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from z3 import And, Int, Or, Solver, sat

OUT = Path("paper/hsp-agile/artifacts/smt_scalability_v1/stress_probe.json")


def time_n_vars(n: int, box: int = 1000, repeats: int = 5) -> dict:
    xs = [Int(f"x{i}") for i in range(n)]
    # Chain of overlapping priority-style regions (still LIA but denser).
    samples = []
    for _ in range(repeats):
        s = Solver()
        s.set("timeout", 10000)
        for x in xs:
            s.add(x >= -box, x <= box)
        # Force a thin intersection resembling first-match residuals.
        for i in range(n - 1):
            s.add(xs[i] >= xs[i + 1] - 3)
            s.add(Or(xs[i] < 0, xs[i] > 10, xs[i + 1] == xs[i] - 1))
        t0 = time.perf_counter()
        r = s.check()
        ms = (time.perf_counter() - t0) * 1000
        samples.append({"ms": ms, "result": str(r)})
    return {
        "n_vars": n,
        "box": [-box, box],
        "mean_ms": sum(s["ms"] for s in samples) / len(samples),
        "max_ms": max(s["ms"] for s in samples),
        "results": [s["result"] for s in samples],
    }


def time_nonlinear(box: int = 100, repeats: int = 5) -> dict:
    """Mild nonlinear probe (product constraint) — often harder than LIA."""
    samples = []
    for _ in range(repeats):
        x, y, z = Int("x"), Int("y"), Int("z")
        s = Solver()
        s.set("timeout", 10000)
        s.add(x >= -box, x <= box, y >= -box, y <= box, z >= -box, z <= box)
        s.add(x * y + z == 1234)
        s.add(x > y)
        s.add(z < 0)
        t0 = time.perf_counter()
        r = s.check()
        ms = (time.perf_counter() - t0) * 1000
        samples.append({"ms": ms, "result": str(r)})
    return {
        "kind": "nonlinear_product",
        "box": [-box, box],
        "mean_ms": sum(s["ms"] for s in samples) / len(samples),
        "max_ms": max(s["ms"] for s in samples),
        "results": [s["result"] for s in samples],
    }


def main() -> None:
    rows = [time_n_vars(n) for n in (4, 8, 16, 32, 48)]
    nonlin = [time_nonlinear(box=b) for b in (20, 100, 1000)]
    out = {"var_chain": rows, "nonlinear": nonlin}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
