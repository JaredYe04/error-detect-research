# Author Response — CCF-B Phase 4 (canonical pipeline)

Maps reviewer questions to evidence after canonical E1 + E12 re-runs.

| Q | Question | Response | Evidence |
|---|----------|----------|----------|
| Q1 | Why ~3.3× latency for no Conf gain vs B2? | We do **not** claim universal purchase. Deploy M when conjunctive release or prevention (PDR/FAR) is required; B2 is default otherwise. | `tab:deployment-boundary`; E2; abstract |
| Q2 | Benchmark circularity / overlap filter? | E1 is an **overlap stress-test**, not representative sample. E10 (no filter) shows B2 > M (89.1% vs 83.1%, 0/100 wins). | `tab:e10-random`; `run_e10_random_v2` |
| Q3 | E12 instability / single seed? | **E12-canonical** (`run_e12_canonical_v1`, same pipeline as E1): B2 leads all seeds (mean 88.0% vs M 86.0%); M wins 4/120; Friedman p=0.077 (ranking stable). | `tab:e12-stability`; `e12_stability_summary.json` |
| Q4 | A2 vs M on Conf? | Canonical E1: A2 80.3% vs M 86.3%. Pattern guard is prevention gate, not Conf booster. **E17**: advisory vs hard gate. | `tab:main-results`; `tab:e17-advisory` |
| Q5 | E11 M trails B1/B2? | External corpus has **moderate overlap**; confirms deployment boundary. **E15** stratifies E11 by tier. | `e11_overlap_stratified.csv`; ch08 §deployment |
| Q6 | B4≈B2 vs E6 +7.7pp? | **E14** length-matched: `execution_trace_matched` 85.4% vs test-only 73.8%. | `tab:e14-feedback`; `run_e14_sweep_v1` |
| Q7 | 5% strict success after K=3? | Accept is conjunctive by design; prevention metrics (PDR/FAR) differentiate M. | E9 taxonomy; E2 |
| Q8 | Single model? | Primary E1/E12 use `ecnu-plus`. **E16-canonical** (`run_e16_canonical_v1`, $n{=}120$, `ecnu-max`): all modes 89.2\%---no ranking reversal. | `tab:e16-canonical`; `e16_model_summary.csv` |

## Canonical experiment artifacts

| Run | Jobs | Role |
|-----|------|------|
| `run_e1_canonical_v1` | 840 | E1 main table, E3, ablations (B0,A1–A3,B1,B2,M) |
| `run_e12_canonical_v1` | 1080 | Multi-seed stability (B1,B2,M × 3 seeds) |
| `run_e8c_full_v2` | 120 | HumanEval/MBPP-FSF |
| `run_e10_random_v2` | 300 | Unfiltered random benchmark |
| `run_e14_sweep_v1` | 480 | Length-matched feedback |
| `run_e17_advisory_v1` | 360 | Advisory pattern guard |
| `run_e16_canonical_v1` | 360 | Second model (`ecnu-max`, $n{=}120$) |

Benchmark fingerprint: `322157816b37c34e` (shared by E1/E12 canonical runs).

Refresh: `python paper/hsp-agile/scripts/refresh_paper_assets.py --run-dir artifacts/run_e1_canonical_v1`
