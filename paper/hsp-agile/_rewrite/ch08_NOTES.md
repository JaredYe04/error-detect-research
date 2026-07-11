# ch08 Discussion rewrite notes (Formalist+Pedagogue)

## What was removed (meta / FAQ)
- Entire `\subsection{Anticipated Reviewer Questions}` and FAQ-to-reviewer voice
  (`sec:disc:threats-faq` **dropped** — content folded into Limitations / Threats).
- Defensive slogans: “do not claim M dominates”, “not a failure mode to explain
  away”, “What a reviewer should…”, repeated “archive-only / do not cite”
  latency admonitions; “not a stronger code generator” Non-claim opener.
- Standalone **Failure Analysis (E9)** section → one Limitations paragraph
  pointing to App.~\ref{app:stress}.
- Heavy re-listing of Ch.7 aggregates (E8 absolute % tables, E13/E18 Conf.
  reprint blocks, duplicate E1/E10/E12 scorecards in the paradox section,
  historical Conf./Strict paradox numbers).
- Redundant “Prevention evaluation completeness” paragraph that only restated E2.
- Checklist jargon (“C3”, “C4 rule”) in discussion/industrial prose.

## What was restructured
- Opening: interpret, don’t reprint Results; Accept as lead story first
  (abstract → concrete catch-all).
- Core findings: E6 (+7.7 pp, 14/14 catch-all) + E2 PDR/FAR + equal-$K$ +
  honest E12 saturation in one place; catch-all vignette recalled once.
- Paradox: concept (Conf vs Strict) → fixed-oracle tracking (no full
  scorecard reprint) → prevention as differentiator; historical artefact
  mentioned once.
- Practice: B2 default / escalate-to-M; checker; pluggable screen; FAR theorem
  vs operational FAR.
- Generalisation + deployment table retained; “when B2 wins” kept as
  conditional guidance (positive framing).
- Limitations absorb former FAQ: $n{=}120$/power, overlap filter, endpoints,
  SMT box, repair $K$, E9 archive.
- Threats: standard four-way split; seed/Strict/A2 points moved here as
  conclusion/construct validity (no FAQ subsection).
- SpecIR scope table retained; industrial vignette via `\input`.

## Industrial vignette
- Cleaned file: `_rewrite/ch08_industrial_case.tex` (label
  `sec:disc:industrial-case` preserved).
- Discussion keeps `\input{chapters/ch08_industrial_case}` so promotion is
  drop-in: copy **both** `_rewrite/ch08_*.tex` → `chapters/` together.
- Live `chapters/` untouched until that promotion.
- Paragraph title “What saturation leaves open” (was “does not falsify”).

## Numbers (AUTHORITATIVE_NUMBERS)
- E6: 86.9 vs 79.1 → **+7.7 pp**; W/L/T **14/4/102**; CI **[2.3, 13.6]**;
  p=**0.018**; **14/14** others, **0/14** ordering.
- E2: M **95.0% / 5.0%** vs B2 **91.2% / 8.8%**.
- Equal-$K$: M_eq **100.0%** vs B2 **97.5%** (+2.5 pp; 3/0/117).
- E1 fixed-oracle: latency **10457 / 9576** ms; llm_calls **~1.16 / ~1.18**;
  M vs B2 win rate cited once under threats (${+}1.7$ pp; 2/120).
- E12: B2 **100%** every seed; M **99.7%** — stated as finding, not slogan.
- Fixed-oracle ablation: A1/A3 Conf.\ cost; A2 zero at ceiling (prevention via E2).
- No invented numbers; no 0.14/0.22 FAR; no pre-fix ~5% Strict as primary.

## Labels preserved
- `ch:discussion`, `sec:disc:interpretation`, `sec:disc:paradox`,
  `sec:disc:implications`, `sec:disc:generalisation`, `sec:disc:deployment`,
  `sec:disc:limitations`, `sec:disc:smt-hybrid`, `sec:disc:related`,
  `sec:disc:threats`, `sec:disc:specir-scope`, `sec:disc:industrial-case`,
  `tab:deployment-boundary`, `tab:specir-scope`.
- Cross-refs kept: `eq:accept`, `thm:far-bound`, `fig:defect-vs-test`,
  `fig:smt-domain-latency`, `tab:smt-scalability`, `tab:cross-model-industrial`,
  `tab:desens-real-sofl`, `tab:defect-evidence-map`, method/results/appendix
  anchors cited in live chapter.

## Labels not preserved
- `sec:disc:failure-analysis` (E9 section removed; content → Limitations).
- `sec:disc:threats-faq` (FAQ subsection deleted).

## Staging paths
- `_rewrite/ch08_discussion.tex`
- `_rewrite/ch08_industrial_case.tex`
- Live `chapters/ch08_*.tex` untouched.

## SpecIR / promotion
- `tab:specir-scope` content and column widths unchanged from live chapter.
