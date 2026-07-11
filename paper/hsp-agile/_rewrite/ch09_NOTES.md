# ch09 Conclusion rewrite notes (Formalist+Pedagogue)

## What was removed (revision meta)
- Opening ``not a claim that we built a universally better code generator''
  (forbidden Non-claim pattern; claim stated positively as Accept decision).
- Closing ``not a universal Conf.\ crown'' (defensive; redundant with Deployment).
- Soft ``scientific hypothesis is narrow'' framing → confident Accept-first
  opening aligned with staged abstract.
- ``near-ceiling ranking tables are appendix stress-tests only'' slogan →
  factual ``secondary stress material, not as the safety headline''.
- Section title ``What to Remember'' → ``Takeaways'' (label
  `sec:conc:remember` kept; less FAQ tone).
- Bold checklist labels on takeaway items (``Lead metric'' / ``Mechanism'' /
  ``Budget'') → plain numbered points.
- Scope paragraph no longer previews industrial future work (that stays in
  Future Directions only).

## What was restructured
- **Opening:** abstract idea (Accept = release decision) → concrete catch-all
  vignette (OTHERWISE→Review / LLM→Pass) → HSP-Agile vehicle.
- **Summary:** Problem → Evidence (E2 Accept/FAR lead, then E6 full card, then
  equal-$K$, ACL) → Deployment (B2 default) → Scope (honest limits only).
- **Takeaways:** three bullets mirror claim spine (Accept/FAR; E6 catch-all;
  C4 budget) without reviewer jargon.
- **Future work:** same four directions; concrete next steps (``keeping the
  Accept conjunction fixed'', ``tracks the release bar'') — not apologetic gaps.
- **Closing:** SgDP as practical decision framework; evidence list ends on
  deployment table.

## Number fixes (AUTHORITATIVE_NUMBERS)
- E2: M **PDR 95.0% / FAR 5.0%** vs B2 **91.2% / 8.8%**.
- E6: **86.9% vs 79.1% → +7.7 pp**; W/L/T **14/4/102**; CI **[2.3, 13.6]**;
  p=**0.018**; **14/14** others, **0/14** ordering.
- Equal-$K$: M_eq **100.0%** vs B2 **97.5%** (+2.5 pp; 3/0/117) in Evidence
  (live chapter only handwaved ``often tie'').
- Did **not** cite E1 K=5 bundle Conf.\ as primary mechanism, historical
  pre-fix, E12 as M-dominance, or 0.14/0.22 FAR.

## Labels / cites preserved
- `ch:conclusion`, `sec:conc:summary`, `sec:conc:remember`,
  `sec:conc:future`, `sec:conc:closing`
- `tab:deployment-boundary` (Deployment + Takeaways + Closing)

## Labels not preserved / N/A
- None dropped. Display title for `sec:conc:remember` is ``Takeaways'';
  cross-refs by label remain valid.

## Staging path
- `_rewrite/ch09_conclusion.tex` — complete replacement for
  `chapters/ch09_conclusion.tex`
- Live `chapters/` untouched.
