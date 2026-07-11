"""Plot SMT domain latency curve for paper figure."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "paper" / "hsp-agile" / "artifacts" / "smt_scalability_v1" / "domain_latency.csv"
OUT = ROOT / "paper" / "hsp-agile" / "figures" / "smt_domain_latency.pdf"


def main() -> None:
    rows = list(csv.DictReader(CSV.open(encoding="utf-8")))
    # Prefer int domains in widening order; append real last.
    order = [
        "int[-5,20]",
        "int[-20,50]",
        "int[-100,100]",
        "int[-1000,1000]",
        "real[-100.0,100.0]",
    ]
    by = {r["domain"]: r for r in rows}
    labels, means, p95s = [], [], []
    for k in order:
        if k not in by:
            continue
        labels.append(k.replace("int", "LIA").replace("real", "Real"))
        means.append(float(by[k]["mean_ms"]))
        p95s.append(float(by[k]["p95_ms"]))

    fig, ax = plt.subplots(figsize=(6.2, 3.4))
    x = range(len(labels))
    ax.plot(list(x), means, marker="o", label="mean ms / task", color="#1f4e79")
    ax.plot(list(x), p95s, marker="s", linestyle="--", label="p95 ms / task", color="#c45c26")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=18, ha="right")
    ax.set_ylabel("Z3 witness time (ms)")
    ax.set_xlabel("SMT domain / encoding")
    ax.set_title("SMT scalability on real_priority_micro ($n{=}30$)")
    ax.legend(frameon=False)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
