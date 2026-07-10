# Author Response — Mock PC Round 6

**Date:** 2026-07-10  
**Status:** P0/P1 fixes applied in thesis + conference stubs

## W1 — B0 27.5% vs canonical 89.2%

**Response:** Stale prose from pre-canonical runs. B0 on `run_e1_canonical_v1` is 89.2% mean Conf., 5.0% strict (one-shot, ~0.2s), matching B1 at seed~0.

**Files updated:** `ch06` L147, `ch07` §Reading the Distributions, `ch08` §interpretation + FAQ, `sections/04_experimental_setup.tex`

## W2 — C1 / overlap narrative vs E3

**Response:** Removed "gap grows with overlap" and "dense overlap ⇒ M" everywhere. C4 now keys on conjunctive Accept, PDR/FAR, and E6 mechanism; E3/E10 explicitly non-monotone.

**Files updated:** `front/abstract.tex`, `ch01` C4/RQ2, `ch06` claim map, `ch07` sensitivity, `ch08` §interpretation + B2-vs-M + deployment practice, `ch09`

## W3 — A2 +0.5 pp stale

**Response:** Canonical A2 = 80.3% vs M 86.3% (−6.0 pp). Updated `ch08` §interpretation (A2 section was already fixed in prior pass).

## W4 — E9 90 vs 114 count

**Response:** Clarified: 114/120 fail conjunctive Accept; E9 labels 90 with sufficient diagnostic signal; 24 uncategorized.

**File updated:** `ch08` §Failure Analysis (E9)

## W5 — Power analysis stale δ

**Response:** `ch08` threats now cite δ=−0.036 (M vs B1), δ=−0.014 (M vs B2), power ~5.8% / ~3.6%, n≈39k for 80% power.

## Post-fix estimated score

**68–72%** (Weak Accept / low Borderline Accept) per R6 action table.

## Remaining (P2, non-blocking)

- `sections/06_discussion_threats.tex` stub TBDs (superseded by `ch08`)
- Conference PDF compile (no `pdflatex` on build host)
- E11 n>22 expansion
