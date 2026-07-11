# Desensitized Real SOFL Pilot — Results

**Date:** 2026-07-11  
**Run:** `artifacts/run_desens_real_sofl_v1`  
**Corpus:** `benchmarks/published_industrial_pilot.json` (**n=28**, was 10)  
**Model:** `ecnu-plus` · equal \(K{=}3\) · modes B1 / B2 / M_eq

## Corpus construction

Expanded from public literature (desensitized compact integers):

| Domain | Sources |
|--------|---------|
| Railway crossing / approach lock | Liu et al. WIFT'98 (Mitsubishi trial) |
| Interlocking (route/signal/point/flank/conflict) | Luo et al. SOFL'17 Casco + public interlocking-table patterns |
| ATM deposit/transfer/inquire/daily cap | Agile-SOFL ATM example; Liu SOFL book |
| Hotel / library / water-tank / inventory | Liu 2004 SOFL book applications |
| Access / med-dose / power / insurance | Li & Liu IET / QRS fault-prevention modelling style |

Z3 validation: **0 fails / 28** (`published_industrial_pilot_validation.json`).

## Results (mean Conf. / Strict)

| Mode | Mean Conf. | Strict | n |
|------|------------|--------|--:|
| B1 | **100.0%** | 100.0% | 28 |
| B2 | **100.0%** | 100.0% | 28 |
| M_eq | **100.0%** | 100.0% | 28 |

Paired M_eq vs B2: **0 / 0 / 28** (W/L/T).

## Interpretation (C4)

On this **published-industrial desensitized** pilot, all modes saturate under `ecnu-plus`.
This **supports C4**: prefer B2 by default for mean Conf. / latency; escalate to
full M only when conjunctive `Accept=1` or FAR≤5% is required.

It does **not** falsify E6 (+7.7 pp typed IR on hard BENCH-120 under repair headroom).

## Honesty

- Not proprietary Casco/Mitsubishi/bank production dumps.
- Not a claim that M is useless — prevention (E2) and Accept remain the escalate signals.
- GitHub live harvest blocked without `gh auth`; Wave-2 used published literature reconstruction instead.
