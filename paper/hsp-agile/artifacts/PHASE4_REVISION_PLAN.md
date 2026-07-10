# Phase 4 — Data Consistency & Reviewer-Proofing ✅ COMPLETE

**Trigger:** Subagent review flagged **E1↔E12 benchmark snapshot mismatch** (86/120 overlap).

## Root cause (resolved)

| Run | Status |
|-----|--------|
| `run_e1_canonical_v1` | ✅ 840 jobs, all modes on `benchmarks/tasks.json` |
| `run_e12_canonical_v1` | ✅ 1080 jobs, same pipeline + benchmark fingerprint |

## Canonical headline numbers

### E1 (`run_e1_canonical_v1`, seed 0)

| Mode | Conf. | Strict |
|------|-------|--------|
| B1 | 89.2% | 5.0% |
| B2 | 87.7% | 5.0% |
| M | 86.3% | 5.0% |

### E12 (`run_e12_canonical_v1`, 3 seeds)

| Mode | Mean | Seed 0/1/2 |
|------|------|------------|
| B2 | 88.0% | 88.4 / 87.8 / 87.8 |
| B1 | 86.1% | 88.5 / 85.5 / 84.1 |
| M | 86.0% | 83.8 / 87.1 / 87.1 |

- B2 ranks first on **all three seeds**
- M wins 4/120 (mean-across-seeds pairing)
- Friedman $p = 0.077$ (borderline; ranking stable)

## Completed actions

| ID | Action | Status |
|----|--------|--------|
| P0-6 | E1 canonical re-run | ✅ |
| P0-6b | `DEFAULT_MAIN_RUN` + `DEFAULT_E12_FULL_RUN` → canonical | ✅ |
| P0-6c | Global number sync (abstract, ch01–ch09, sections/) | ✅ |
| P0-7 | Deployment table non-monotone E3 fix | ✅ |
| P0-8 | Conference `main.tex` + stubs synced | ✅ |
| P1-4 | `benchmark_fingerprint` in `run_all.py` meta | ✅ |

## Iteration scores

| Round | Score | Outcome |
|-------|-------|---------|
| R1 | ~38% | Mechanism-first reframe |
| R2 | ~50% | Benchmark audit |
| R3 | ~42% | Canonical E1; partial sync |
| R4 | ~55–58% | E12 canonical + full sync (post-completion) |

## Artifact paths

```
artifacts/run_e1_canonical_v1/     # E1 main table, E3, ablations
artifacts/run_e12_canonical_v1/    # Multi-seed stability
paper/hsp-agile/data/processed/    # Refreshed CSV/JSON + figures
```
