# Data Verdict — updated after gemini combo n=40

**Date:** 2026-07-11  
**Run:** `artifacts/run_ir_combo_seed_gemini_n40_v1` (1080/1080 rows)

## Verdict: **MATCHES expectations** → update paper (done); no further expand required for this claim

### What we expected
Expanding gemini combo seeds beyond n=14 would keep FULL (`semantic_ir`) ahead of
unstructured `test_only` / `test_expected` with CI excluding 0, while uniqueness
vs `ir_no_expected` may remain non-significant (E14-consistent).

### What we got (pooled n=120 task×seed)

| Contrast | Δ | W/L/T | 95% CI | Excl. 0 |
|----------|---|-------|--------|---------|
| FULL vs test_only | **+33.2 pp** | 47/8/65 | [25.1, 41.9] | **Yes** |
| FULL vs test_expected | **+32.6 pp** | 47/8/65 | [24.6, 41.1] | **Yes** |
| FULL vs ir_no_expected | +5.0 pp | 29/17/74 | [−3.5, 13.6] | No |

Per-seed FULL vs test_only: +27.2 / +34.4 / +38.1 pp — **all CI excl 0**.

### Paper actions taken
- `tables/gemini_combo_n40.tex` + Ch7 §Hard Combo-Seed Support
- Conference RQ1 paragraph updated
- `AUTHORITATIVE_NUMBERS.md` corpus card + numbers
- RQ1 answer mentions supporting evidence without uniqueness overclaim

### Explicit non-actions
- Do **not** claim typed IR beats every structured ablation
- Do **not** cite gpt-4o-mini/deepseek combo (saturated)
- Do **not** further expand n for this claim unless a new hypothesis appears

### Core claims status (unchanged pass)
E6 +7.7 / equal-K +2.5 / ablation A3>A1>A2≈0 / E2 PDR-FAR / C4 B2 default — all still primary.
