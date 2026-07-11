# ch01 / abstract rewrite notes (Formalist+Pedagogue)

## What was removed (revision meta)
- ``What a reviewer should remember'', ``lead sell'', ``Non-claim:'' labels
- ``Anticipated Reviewer…'' / checklist tone; ``demoted'' as slogan
- Abstract C2/C3/C4 bullet stack that restated the takeaway as rebuttal FAQ
- ``not a claim that we invent a new code generator'' parenthetical
- ``stress-tests only'' as slogan → factual ``appendix material / ranking runs''
- ``One-sentence takeaway'' paragraph label (folded into opening prose)

## What was restructured
- **Abstract:** concept (lucky-pass catch-all) → Accept definition → FAR/PDR →
  E2 then E6 then equal-$K$ then C4 deployment guidance; keywords unchanged in
  spirit.
- **Ch.1:** same section spine; contributions reordered emphasis already matched
  brief (C3 → C2 → C4) but prose now states claims + evidence + honest
  *scope* instead of Claim/Evidence/Non-claim triads.
- Primary vignette remains OTHERWISE→Review / LLM→Pass; secondary tax/overlap
  clearly marked.
- RQ and organisation: ``demoted'' → ``secondary'' / ``appendix''.

## Number fixes (AUTHORITATIVE_NUMBERS)
- E2: M PDR/FAR **95.0%/5.0%** vs B2 **91.2%/8.8%** (unchanged; correct).
- E6: explicit **86.9% vs 79.1% → +7.7 pp**; W/L/T **14/4/102**; CI
  **[2.3, 13.6]**; p=**0.018**; **14/14** others, **0/14** ordering.
- Equal-$K$: M_eq **100.0%** vs B2 **97.5%** (+2.5 pp; 3/0/117) now in
  abstract and C4.
- E1 appendix preview: **84.2/98.3/100.0%**; E12: B2 **100%** every seed, M
  **99.7%** (no ``M dominates all seeds'').
- Field FULL vs NL-only **+28.0 pp** retained from live ch01.
- Did **not** cite historical pre-fix Conf. or 0.14/0.22 FAR.

## Labels / cites preserved
- Labels: `ch:intro`, `sec:intro:*`, `eq:acceptance`, `eq:phi-intro`,
  `fig:defect-vs-test`, `fig:sgdp-overview`, `fig:contribution-map`,
  `lst:others-fsf`, `lst:others-bug`, `lst:tax-fsf`, `lst:tax-bug`.
- Tables/refs kept: `tab:evidence-ladder`, `tab:e6-*`, `tab:field-structure`,
  `tab:defect-evidence-map`, `tab:deployment-boundary`,
  `sec:results:acl-case`, `app:stress`, chapter refs.
- All major `\cite{...}` from live ch01 retained.

## Labels not preserved / N/A
- None dropped. Abstract still has no own `\label` (matches live `front/abstract.tex`).

## Staging paths
- `_rewrite/abstract.tex` — complete replacement for `front/abstract.tex`
- `_rewrite/ch01_introduction.tex` — complete replacement for
  `chapters/ch01_introduction.tex`
- Live `front/` and `chapters/` untouched.
