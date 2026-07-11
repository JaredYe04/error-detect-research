# HKCA09 SOFL → FSF Expansion + Eval

**Date:** 2026-07-11  
**Source:** public `HKCA09/SOFL-Maintainability-Experiment-Dataset`  
  (ATM, Course/Hospital registration, Vending, Stock, Transit)  
**Corpus:** `benchmarks/hkca09_sofl_fsf.json` (**n=35**, Z3-validated)  
**Honesty:** integer ordered-guard **reconstructions** of decision precedence
(not bit-identical SOFL posts; maps/seqs not SMT-encodable as-is).

## Why this expansion

Auto-extracted `.asfl` GitHub harvest (`n=48`) and one-shot E6 on real
headroom both **saturate** (B2 ≈ M_eq; feedback variants all Conf=1.0).
Aggregate Conf ties do **not** serve C2. HKCA09 modules add
**overlap-rich** precedence (auth / capacity / balance / success) so:

1. **C4 ranking** — B1 has headroom; B2 recovers (default B2).
2. **C2 mechanism** — hard-seed repair (freeze ordering/relop bug → one
   T=0 repair) isolates typed IR vs `test_only` when one-shot Conf is saturated.

## Ranking (`run_hkca09_b1b2m_v1`, equal K=3, ecnu-plus)

| Mode | Mean Conf. | vs B2 |
|------|------------|-------|
| B1 | 74.3% | — |
| B2 | **100.0%** | — |
| M_eq | 100.0% | 0/0/35 |

B1 fails on 9/35 tasks. B2 matches M_eq — **supports C4 default B2**.

## One-shot E6 (`run_real_e6_headroom_v1`, n=57)

All of `test_only` / `test_expected` / `semantic_ir` → mean Conf **100%**
(0/0/57). Confirms saturation; **do not cite as C2 lead**.

## Hard-seed C2

### v1 (`run_hkca09_hard_seed_e6_v1`) — invert_order / wrong_relop

| Seed | test_only | semantic_ir | Δ pp | W/L/T | CI excl0 |
|------|-----------|-------------|------|-------|----------|
| wrong_relop | 69.3% | **82.0%** | **+12.7** | 9/5/12 | no |
| invert_order | 96.3% | 93.9% | −2.3 | 2/6/22 | no |

### v2 (`run_hkca09_hard_seed_e6_v2`) — swap / combo / drop

| Seed | test_only | semantic_ir | Δ pp | W/L/T |
|------|-----------|-------------|------|-------|
| swap_bodies | 95.7% | 95.0% | −0.8 | 4/6/20 |
| combo_invert_relop | 89.1% | 67.7% | −21.5 | 1/11/16 |
| drop_first_guard | 93.6% | 67.8% | −25.7 | 0/14/14 |

**Reading:** typed IR helps on **relop/constraint** seeds; on aggressive
structural seeds (drop guard / combo invert) unstructured test dumps can
win under `ecnu-plus`. Aligns with paper claim that IR value is
**conditional**, not universal. Primary C2 remains BENCH-120 E6 (+7.7 pp).

## RealSpec

Rebuild includes `github_sofl` (+35). Total **203** tasks.
