# Wave-1 hard-seed cross-run summary

**Narrative still frozen.**

## H1_ecnu_e6win14 (tasks=14, rows=378)

| Seed | FULL | A | NO_EXP | FULL-A W/L/T | d_pp | CI95 | excl0 | FULL-NO_EXP |
|------|-----:|--:|-------:|-------------:|-----:|------|:-----:|------------:|
| invert_order | 0.9911 | 0.9643 | 0.9911 | 4/1/9 | 2.68 | [-0.89, 6.25] | False | 1/1/12 d0.0 excl=False |
| swap_bodies | 1.0 | 0.9554 | 0.9911 | 5/0/9 | 4.46 | [1.79, 7.14] | True | 1/0/13 d0.89 excl=False |
| wrong_relop | 1.0 | 0.9613 | 0.869 | 3/0/11 | 3.87 | [0.0, 8.33] | False | 4/0/10 d13.1 excl=True |

CI excludes 0: swap_bodies|semantic_ir_vs_test_only, wrong_relop|semantic_ir_vs_ir_no_expected

## H2_gemini_e6win14 (tasks=14, rows=378)

| Seed | FULL | A | NO_EXP | FULL-A W/L/T | d_pp | CI95 | excl0 | FULL-NO_EXP |
|------|-----:|--:|-------:|-------------:|-----:|------|:-----:|------------:|
| invert_order | 1.0 | 0.6875 | 1.0 | 5/0/9 | 31.25 | [9.82, 56.25] | True | 0/0/14 d0.0 excl=False |
| swap_bodies | 1.0 | 0.8661 | 1.0 | 2/0/12 | 13.39 | [0.0, 33.93] | False | 0/0/14 d0.0 excl=False |
| wrong_relop | 0.2232 | 0.0357 | 0.3661 | 4/3/7 | 18.75 | [0.0, 41.07] | False | 1/3/10 d-14.29 excl=False |

CI excludes 0: invert_order|semantic_ir_vs_test_only

## H6_gpt4omini_e6win14 (tasks=14, rows=378)

| Seed | FULL | A | NO_EXP | FULL-A W/L/T | d_pp | CI95 | excl0 | FULL-NO_EXP |
|------|-----:|--:|-------:|-------------:|-----:|------|:-----:|------------:|
| invert_order | 1.0 | 1.0 | 1.0 | 0/0/14 | 0.0 | [0.0, 0.0] | False | 0/0/14 d0.0 excl=False |
| swap_bodies | 1.0 | 1.0 | 1.0 | 0/0/14 | 0.0 | [0.0, 0.0] | False | 0/0/14 d0.0 excl=False |
| wrong_relop | 1.0 | 1.0 | 1.0 | 0/0/14 | 0.0 | [0.0, 0.0] | False | 0/0/14 d0.0 excl=False |

No paired contrast with CI excluding 0.

## H4_ecnu_hard60 (tasks=60, rows=1620)

| Seed | FULL | A | NO_EXP | FULL-A W/L/T | d_pp | CI95 | excl0 | FULL-NO_EXP |
|------|-----:|--:|-------:|-------------:|-----:|------|:-----:|------------:|
| invert_order | 0.975 | 0.9729 | 0.9646 | 8/7/45 | 0.21 | [-1.46, 1.67] | False | 10/12/38 d1.04 excl=False |
| swap_bodies | 0.9917 | 0.9792 | 0.9771 | 10/4/46 | 1.25 | [-0.21, 2.71] | False | 9/2/49 d1.46 excl=True |
| wrong_relop | 0.9667 | 0.9771 | 0.9785 | 5/8/47 | -1.04 | [-4.31, 2.22] | False | 5/7/48 d-1.18 excl=False |

CI excludes 0: swap_bodies|semantic_ir_vs_ir_no_expected

## H5_realspec_gemini (tasks=38, rows=864)

| Seed | FULL | A | NO_EXP | FULL-A W/L/T | d_pp | CI95 | excl0 | FULL-NO_EXP |
|------|-----:|--:|-------:|-------------:|-----:|------|:-----:|------------:|
| invert_order | 1.0 | 1.0 | 1.0 | 0/0/34 | 0.0 | [0.0, 0.0] | False | 0/0/34 d0.0 excl=False |
| swap_bodies | 1.0 | 1.0 | 1.0 | 0/0/34 | 0.0 | [0.0, 0.0] | False | 0/0/34 d0.0 excl=False |
| wrong_relop | 0.4536 | 0.2857 | 0.4357 | 7/1/20 | 16.79 | [0.71, 34.64] | True | 3/2/23 d1.79 excl=False |

CI excludes 0: wrong_relop|semantic_ir_vs_test_only

## H5_realspec_ecnu (tasks=18, rows=378)

| Seed | FULL | A | NO_EXP | FULL-A W/L/T | d_pp | CI95 | excl0 | FULL-NO_EXP |
|------|-----:|--:|-------:|-------------:|-----:|------|:-----:|------------:|
| invert_order | 0.97 | 0.9611 | 0.9667 | 2/2/11 | 0.89 | [-6.0, 7.78] | False | 1/2/12 d0.33 excl=False |
| swap_bodies | 1.0 | 0.9111 | 1.0 | 2/0/13 | 8.89 | [0.0, 24.44] | False | 0/0/15 d0.0 excl=False |
| wrong_relop | 0.8861 | 0.9556 | 0.9653 | 1/3/8 | -6.94 | [-22.5, 8.89] | False | 1/3/8 d-7.92 excl=False |

No paired contrast with CI excluding 0.

## H6_realspec_gpt4omini (tasks=13, rows=270)

| Seed | FULL | A | NO_EXP | FULL-A W/L/T | d_pp | CI95 | excl0 | FULL-NO_EXP |
|------|-----:|--:|-------:|-------------:|-----:|------|:-----:|------------:|
| invert_order | 1.0 | 1.0 | 1.0 | 0/0/11 | 0.0 | [0.0, 0.0] | False | 0/0/11 d0.0 excl=False |
| swap_bodies | 1.0 | 1.0 | 1.0 | 0/0/11 | 0.0 | [0.0, 0.0] | False | 0/0/11 d0.0 excl=False |
| wrong_relop | 1.0 | 1.0 | 1.0 | 0/0/8 | 0.0 | [0.0, 0.0] | False | 0/0/8 d0.0 excl=False |

No paired contrast with CI excluding 0.
