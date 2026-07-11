# Data Verdict — Gemini Combo C2 Support (updated)

**Primary supporting run (pooled):**  
`run_ir_combo_seed_gemini_n40_v1` + `run_ir_combo_seed_gemini_extra40_v1`  
→ **n=80 tasks × 3 seeds = 240 paired cells** (`gemini-2.5-flash`)

## Pooled FULL (semantic_ir) vs comparators

| Contrast | Δ pp | W/L/T | 95% CI (pp) | Excl. 0 |
|----------|-----:|-------|-------------|---------|
| vs test_only | **+26.5** | 78/27/135 | [21.0, 32.2] | **Yes** |
| vs test_expected | **+26.7** | 79/18/143 | [21.0, 32.3] | **Yes** |
| vs ir_no_expected | +5.0 | 29/17/74 | [-3.3, 13.6] | No (n40 field slice) |

Per-seed vs test_only (all excl 0): invert +23.4 / swap +26.7 / drop +29.2.

## Claim hierarchy

1. **Lead C2:** E6 BENCH-120 +7.7 pp (CI excl 0) on ecnu-plus  
2. **Supporting C2:** this pooled gemini combo table  
3. **C4 only:** GitHub harvest / HKCA09 ranking ties; do not read as C2 null  
4. **Scoped / negative:** HKCA09@gemini hard-seed favors test_only — not a C2 headline

## Artifacts

- `tables/gemini_combo_n80.tex` (cite)
- `tables/gemini_combo_n40.tex` (archive slice)
- `data/processed/gemini_combo_n80_summary.json`
