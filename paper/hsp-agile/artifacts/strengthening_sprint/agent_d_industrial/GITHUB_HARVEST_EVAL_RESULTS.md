# GitHub Live Harvest + Eval (Wave-3) — Results

**Date:** 2026-07-11  
**Auth:** `gh` as JaredYe04  
**Corpus:** `benchmarks/github_harvest_v1.json` (**n=48**)  
**Run:** `artifacts/run_github_harvest_v1`

## Pipeline executed

1. Broad code search: 110 hits / 100 downloads (0 auto-convert — noisy)
2. Targeted repos: `HKCA09/SOFL-Maintainability-Experiment-Dataset`, `ICARUSxyz/FCoTFL`, `JaredYe04/agile-sofl-toolchain`
3. Lightweight ASFL `FSF :` parser → Z3 validate → **47 OK** (+1 manual seed = 48)
4. RealSpec rebuild: **168** tasks (`github_harvest=47`)
5. Eval B1/B2/M_eq on `ecnu-plus`, equal \(K{=}3\)

## Results

| Mode | Mean Conf. | Strict | vs B2 |
|------|------------|--------|-------|
| B1 | 85.8% | 75.0% | — |
| B2 | **89.9%** | 79.2% | — |
| M_eq | 89.9% | 79.2% | 1/1/46 |

## Interpretation (C4)

Public GitHub Agile-SOFL examples are **not saturated**. Test-feedback B2 matches equal-\(K\) M_eq on mean Conf. and both beat one-shot B1. Prefer B2 by default; escalate to full M only for Accept / FAR bars.

## Honesty

- Converted from **public** `.asfl` FSF sections (ecommerce / smart-city / hospital / library).
- Node ASFL parser vendor build missing; used `asfl_fsf_lite` instead.
- HKCA09 full SOFL modules (ATM.txt etc.) downloaded but not yet auto-FSF’d (complex postconditions) — next expansion target.
- Not proprietary Casco/Mitsubishi dumps.
