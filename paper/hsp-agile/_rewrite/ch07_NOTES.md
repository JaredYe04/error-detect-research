# Ch.7 Rewrite Notes

## Restructured
- Evidence-ladder section order: **RQ1 (E6 mechanism) → RQ3 (E2 prevention) → RQ4 (equal-$K$ / C4) → ACL case → RQ2 (overlap negative) → ranking archive**.
- RQ1 no longer dumps six co-equal experiments: opens with catch-all rescue + E6; then E5 (budget), E14 (structured scope), combo/field, ablation, E17 as clearly subordinated subsections.
- Roadmap table columns: Role / Section / Key figure (was RQ-first dump).
- Abstract-first paragraphs at section and major-subsection opens; E6 vignette leads RQ1 and frames RQ3’s complementary ordering story.

## Removed (meta / slogans)
- “What not to read as the headline”
- “do not re-litigate claim hygiene”
- “not a Conf.\ crown”
- “stress-test(s) only” as slogan → one factual statement: E1 $K{=}5$ is a multi-factor bundle / saturation context
- “Answer to RQ*” defensive tone tightened; “Claim (C…)” bold lead-ins cut where redundant with abstract-first opens
- “Is this one synthetic template?” rhetorical FAQ cut → factual HardCase-id span sentence
- “reviewer question” field-ablation framing → direct scientific question

## Numbers (AUTHORITATIVE_NUMBERS)
- E6: 86.9 / 79.1 / 78.9; +7.7 pp; W/L/T 14/4/102; CI [2.3, 13.6]; p=0.018; 14/14 catch-all, 0/14 ordering — unchanged.
- E2 impl-screening: M PDR 95.0% / FAR 5.0% vs B2 91.2% / 8.8% — unchanged.
- Equal-$K$: M_eq 100.0% vs B2 97.5% (+2.5 pp; 3/0/117) — unchanged.
- E1 fixed-oracle: 84.2 / 98.3 / 100.0%; E12: B2 100% / M 99.7%; ablation A3 −25.8 / A1 −17.5 / A2 0.0 — unchanged.
- No invented numbers; all `\input{tables/...}` preserved.

## Labels preserved
- `ch:results`, `tab:results-roadmap`, `sec:results:rq1`–`rq5`, `sec:results:e14`, `sec:results:gemini-combo`, `sec:results:ablation-fixed`, `sec:results:e17`, `sec:results:acl-case`, `sec:results:e1-stress`
- All figure/table labels (`fig:feedback-variant`, `fig:convergence`, `fig:ablation`, `fig:prevention-*`, `fig:pattern-f1`, `fig:complexity`, `tab:feedback-e6`, `tab:e6-*`, `tab:prevention`, `tab:equal-k-*`, listings, etc.)
- **New subsection label:** `sec:results:e6` (optional anchor for E6 block; no external refs broken)
- Cross-ref to `sec:results:e4` / `tab:deployment-boundary` / `app:stress` / `fig:e10-overlap` unchanged (defined elsewhere)

## Inputs / floats preserved
- All original `\input{tables/...}`, `\widefig{figures/...}`, `\inputfsf` / `\inputpython` / ACL listing inputs retained.
