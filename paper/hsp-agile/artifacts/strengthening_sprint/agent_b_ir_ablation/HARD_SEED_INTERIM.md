# Hard-seed IR ablation — interim (experiment only)

**Policy:** Tracking only. Paper narrative frozen.

## Done

### H1 ecnu-plus (14×3, 378)

| Contrast | W/L/T | Δ pp | CI excl 0 |
|----------|-------|-----:|:---------:|
| swap_bodies FULL−A | 5/0/9 | +4.5 | yes |
| wrong_relop FULL−NO_EXP | 4/0/10 | +13.1 | yes |
| invert_order FULL−A | 4/1/9 | +2.7 | no |

### H2 gemini-2.5-flash (14×3, 378) — DONE

| Contrast | W/L/T | Δ pp | CI excl 0 |
|----------|-------|-----:|:---------:|
| invert_order FULL−A | 5/0/9 | **+31.3** | **yes** |
| swap_bodies FULL−A | 2/0/12 | +13.4 | no |
| wrong_relop FULL−A | 4/3/7 | +18.8 | no |

Note: on gemini, field ablations often saturate with FULL (little field uniqueness); `wrong_relop` FULL mean Conf only ~0.22 (seed often too hard). Stronger signal is **FULL > test_only** on invert_order.

## Running fleet

| Run | Target | Progress (approx) |
|-----|--------|-------------------|
| H4a hard_all 0–30 @ ecnu | 810 | ~351 |
| H4b hard_all 30–60 @ ecnu | 810 | ~28 |
| H5a RealSpec @ gemini n=20→40 | 378→~900 | ~168 (n=20 first) |
| H5b RealSpec @ ecnu n=20 | 378 | ~45 |
| H6a E6-win14 @ gpt-4o-mini | 378 | ~17 |
| H6b RealSpec @ gpt-4o-mini n=15 | after H5a-20 | queued in same shell |

## Next after current wave

1. Expand RealSpec gemini to 40 (same out-dir, resume) once n=20 writer finishes
2. Stats pass on H4/H5/H6
3. If still saturated: try even weaker / harder multi-bug seeds
