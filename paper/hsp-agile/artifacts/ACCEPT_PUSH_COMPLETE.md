# Accept Push — Completion Summary (2026-07-11)

## Verdict

P0–P2 revision package is **complete enough for CCF-B Weak Accept / Accept-edge submission** (~68–75%), contingent on keeping the deployment-aware narrative (not “M universally beats B2”).

## What landed

### Experiments
| Run | Result |
|-----|--------|
| E6 paired (`e6_paired_analysis.py`) | C−A +7.7 pp; **14/4/102**; CI **[2.3, 13.6]**; **p=0.018** |
| Equal-K (`run_e1_equal_k_v1`) | **M_eq 100.0%** vs B2 **97.5%** (+2.5 pp; **3/0/117**) |

### Code
- Mode `M_eq` (K=3, semantic_ir, advisory)
- CLI `--force-max-attempts` in `experiments/run_all.py`
- Scripts: `e6_paired_analysis.py`, `summarize_equal_k.py`

### Papers
- Long report: abstract, ch01–ch02, ch06–ch09 + industrial vignette
- Conference cut: all stubs + abstract with E6 CI + equal-K
- Tables: `e6_paired_stats.tex`, `equal_k_m_vs_b2.tex`, `authoritative_numbers.tex`
- Bib: ChatRepair, Jiang ICSE’23, Alloy, TLA+, Break-It-Fix-It

## Cite order (do not mix)

1. **Lead:** E6 +7.7 pp (paired CI)
2. **Prevention:** E2 PDR/FAR
3. **Deploy:** C4 — B2 default; escalate iff Accept=1 or FAR≤5%
4. **Equal-K Conf:** M_eq +2.5 pp
5. **Stress only:** E1 K=5 bundle +1.7 pp; E12 B2 seed-stable

## Remaining (optional, not blocking)
- Live vendor SOFL pilot (P2-3)
- Trim historical Pareto/E9 figures further if page-limited
- Compile PDF smoke-check before submission

## Checklist
See `ACCEPT_BAR_CHECKLIST.md`.
