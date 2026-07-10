# Submission Checklist — HSP-Agile (CCF-B target)

**Last updated:** 2026-07-10 (Phase 5 polish)

## Data provenance (must pass before submit)

- [x] E1 canonical: `artifacts/run_e1_canonical_v1` (840 jobs, BENCH-120 fingerprint `322157816b37c34e`)
- [x] E12 canonical: `artifacts/run_e12_canonical_v1` (1080 jobs, same fingerprint)
- [x] E16 canonical: `artifacts/run_e16_canonical_v1` (360 jobs, ecnu-max)
- [x] `python paper/hsp-agile/scripts/refresh_paper_assets.py --run-dir artifacts/run_e1_canonical_v1`
- [x] `python paper/hsp-agile/scripts/update_stats_table.py`
- [ ] Re-run refresh after any new experiment before camera-ready

## Headline numbers (cross-check abstract ↔ ch07 ↔ conference)

| Claim | Canonical value | Where |
|-------|-----------------|-------|
| E6 typed IR | +7.7 pp (86.9 vs 79.1) | abstract, ch07 E6 |
| E1 seed-0 | B1 89.2 / B2 87.7 / M 86.3 | tab:main-results |
| E12 3-seed | B2 88.0 mean, M 86.0, Friedman p=0.077 | ch07 E12 |
| E10 random | B2 89.1, M 83.1, 0/100 wins | ch07 E10 |
| E2 prevention | M PDR 95.0 / FAR 5.0 vs B2 91.2 / 8.8 | ch07 E2 |
| E16 ecnu-max | all 89.2% (n=120) | ch07 E16 |
| Power M vs B2 | δ≈−0.014, ~3.6% | power_analysis.json, ch06 |

## Narrative guardrails (reviewer traps)

- [x] Do **not** claim universal M > B2 on aggregate Conf
- [x] Do **not** cite Friedman p<0.001 (use p=0.077)
- [x] Do **not** use superseded 86-task E1 (M 90.4%) without footnote
- [x] E3 tertiles described as **non-monotone**
- [x] Default deployment: **B2**; M for Accept / PDR-FAR / E6 mechanism
- [x] A2 ablation: ~−6 pp Conf (not +0.5 pp / 90.9%)
- [x] Strict success 5% (not 25%) on synthetic hard set

## LaTeX build

- [ ] Thesis PDF: compile `paper/hsp-agile/main.tex` (requires TeX install)
- [ ] Conference PDF: compile `paper/hsp-agile-conference/main.tex`
- [ ] BibTeX: zero `??` citations; run `BIB_VERIFICATION_REPORT.md` spot-check
- [ ] All `\ref{fig:...}` and `\ref{tab:...}` resolve (no undefined references)

## Figures & tables

- [x] `performance_vs_overlap.pdf` in conference results stub
- [x] `sections/05_results.tex` synced to canonical CSVs (no TBD)
- [x] `tables/stats_summary.tex` regenerated from `update_stats_table.py`
- [ ] Spot-check figure captions match honest narrative (E3, pareto, generalisation)

## Threats & reproducibility

- [x] E10/E11 external validity paragraphs in ch06/ch08
- [x] Power analysis disclosed (under-powered for M vs B2 aggregate)
- [x] `appendices/app_a_reproducibility.tex` run IDs match canonical artifacts
- [ ] Artifact package README lists exact refresh commands

## Optional (not blocking)

- [ ] E11 expansion beyond n=22
- [ ] Vendor submodule manual held-out (`run_e11_manual.ps1`)
- [ ] Mock PC round 6 review (target ≥70%)

## Pre-submit grep (run locally)

```powershell
rg "90\.4|TBD|p<0\.001|M's advantage|universal M" paper/hsp-agile/chapters paper/hsp-agile/sections paper/hsp-agile/front
```

Expected: only intentional historical footnotes (e.g. ch01 superseded corpus note).

## Sign-off

| Role | Status | Date |
|------|--------|------|
| Data refresh | ✅ canonical | 2026-07-10 |
| Narrative sync | ✅ R6 P0/P1 | 2026-07-10 |
| R6 fixes | ✅ B0, C1, A2, E9, power | 2026-07-10 |
| PDF compile | ⏳ needs pdflatex | — |
| Final PC mock | ✅ R6 → est. 68–72% | 2026-07-10 |

See `AUTHOR_RESPONSE_R6.md` for itemised fixes.
