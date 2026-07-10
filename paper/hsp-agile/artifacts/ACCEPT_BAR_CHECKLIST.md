# CCF-B Accept-Bar Checklist

**Date:** 2026-07-10 (updated after equal-K fill-in)  
**Target:** ICSME / SANER / QRS (CCF-B) — long report + conference cut  
**Policy:** Lead = E6 + E2 + C4; equal-K Conf = `M_eq`; E1 $K{=}5$ = stress-test only.

| ID | Item | Status | Evidence / files |
|----|------|--------|------------------|
| P0-1 | Conference 10-page narrative (E6→E2→C4; demote E1) | **DONE** | `paper/hsp-agile-conference/main.tex`, `sections/conference/*_stub.tex` |
| P0-2 | E6 paired stats + CI (lead claim) | **DONE** | W/L/T 14/4/102; CI [2.3,13.6]; p=0.018 — `scripts/e6_paired_analysis.py`, `tables/e6_paired_stats.tex` |
| P0-3 | Equal-K Conf ranking (B2 vs M_eq, K=3) | **DONE** | `run_e1_equal_k_v1`: M_eq 100.0% vs B2 97.5% (+2.5 pp; 3/0/117) — `tables/equal_k_m_vs_b2.tex` |
| P0-4 | C4 decision rule (one measurable escalate signal) | **DONE** | Escalate iff Accept=1 OR FAR≤5%; not overlap tertiles |
| P0-5 | Industrial/cross-model support C4 default B2 | **DONE** | n=31 B2=100% under gpt-4o/Claude |
| P1-1 | Redefine C1 (no monotone overlap claim) | **DONE** | ch01 C1; ch07 RQ2 “hypothesis not supported” |
| P1-2 | Redefine C2 (scoped vs E14; not uniqueness) | **DONE** | abstract, ch01, conference |
| P1-3 | Authoritative numbers table in main text | **DONE** | `tables/authoritative_numbers.tex` in ch06 |
| P1-4 | Expand related work / bib (LLM-APR, Alloy, TLA+) | **DONE** | `bib/references.bib` + ch02 |
| P1-5 | Pattern gate → E2/E17 not Conf ablation | **DONE** | ch01 C3; ch07/ch08 |
| P2-1 | Industrial decision vignette | **DONE** | `chapters/ch08_industrial_case.tex` |
| P2-2 | Historical corpora demoted / labeled | **DONE** | AUTHORITATIVE 四语料卡；E1 K=5 标 stress-test；历史行标 archive |
| P2-3 | Live production SOFL pilot | **TODO** | Needs vendor access; vignette covers pattern corpus |

## Accept-bar reading (post equal-K)

| Dimension | Assessment |
|-----------|------------|
| Lead claim statistical support | **Strong** (E6 CI excludes 0, p=0.018) |
| Equal-K Conf ranking | **Filled** (M_eq +2.5 pp, 3/120 wins) |
| Causal clarity | **Good** (E6 single-factor; equal-K separate; K=5 bundle demoted) |
| Overclaiming risk | **Low** if narrative kept |
| External validity | **Bounded** (honest industrial-pattern + model headroom) |
| Est. acceptance (conference cut) | **~68–75%** Weak Accept / Accept edge |

## Key numbers to cite

| Claim | Number |
|-------|--------|
| E6 C−A | +7.7 pp; 14/4/102; CI [2.3, 13.6]; p=0.018 |
| E2 M vs B2 | PDR 95.0 / FAR 5.0 vs 91.2 / 8.8 |
| Equal-K | M_eq 100.0 vs B2 97.5 (+2.5 pp; 3/0/117) |
| E1 bundle | M 100.0 vs B2 98.3 (+1.7 pp; stress-test) |
| Industrial | B2 100% under gpt-4o/Claude (n=31) |
