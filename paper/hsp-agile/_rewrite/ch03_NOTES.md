# Ch.03 Formalization — Rewrite Notes

## What was removed (meta / hedges)
- Opening “mathematical core / does not yet describe a pipeline” framing.
- Rhetorical roadmap question (“What must be true of … before …?”).
- Caption “Takeaway:” slogans (replaced with factual hinge descriptions).
- Motivational hedge in `prop:order-required` proof (“need not be the case… would not test ordering at all”) — replaced by an explicit non-equal-postcondition hypothesis.
- Soft wording around “typically small” boundary measure in the corollary statement.
- Primary dependence on `classify_signal` as the sole running example; `lst:llm-incorrect` (broken / superseded) replaced by `lst:others-bug`.

## What was restructured
- **Primary vignette** = catch-all tier (`classify_tier` / Listings `lst:others-fsf`--`lst:others-bug`); **secondary** = `classify_signal` + `compute_tax` / ordering–overlap, always marked.
- **Accept moved earlier** (new order: Task → SpecIR → Oracle → **Accept/BAP** → Witnesses/semantics → Metrics → Benchmark → Complexity). SpecIR and Accept now precede boundary / random-vs-SMT constructions.
- Semantics section retitled “Witnesses and Scenario Semantics”; primary examples use residual $\Phi_3$; figures kept but captions mark secondary overlap vs primary catch-all.
- Claim spine stated once at `def:accept`: $\mathrm{Accept}\Leftrightarrow\mathrm{Conf}{=}1\wedge\mathrm{Screen}{=}\mathit{pass}$ (no E1/E6/E2 numbers in this chapter).

## Symbol / number fixes
- **ε collision fixed:**
  - Boundary margin: $\delta$ and $\mathcal{B}_\delta(t)$ (was $\varepsilon$ / $\mathcal{B}_\varepsilon$).
  - Fault exposure: $\varepsilon_c$, $\varepsilon_{\min}$ (was overloaded $\varepsilon=\min\varepsilon_c$).
  - Relative boundary measure: $\rho=\mu(\mathcal{B}_\delta)/\mu(\mathcal{X})$ (was a third use of $\varepsilon$).
- No AUTHORITATIVE_NUMBERS inserted (formalization chapter correctly stays number-free aside from complexity order-of-magnitude runtime remarks already present).

## Labels
- **Preserved:** all `def:*`, `lem:coverage`, `cor:random-vs-smt`, `prop:order-required`, `sec:form:*`, `fig:specir-walkthrough`, `fig:fsf-semantics`, `ch:formalization`.
- **Cross-refs updated in prose only:** primary examples now cite `lst:others-bug` / `lst:others-fsf`; secondary cite `lst:tax-fsf` and `classify_signal`. Forward refs to `eq:priority`, `thm:witness-soundness`, `tab:patterns`, `eq:phi-intro` retained.
- **Could not preserve as-is (content, not label):** figure TikZ bodies still depict `classify_signal` geometry — captions now explicitly mark them secondary; regenerating TikZ to `classify_tier` is deferred (live `diagrams/` not edited from this agent).
- Section label `sec:form:semantics` preserved despite title change.

## Follow-ups for orchestrator / sibling agents
- Ch.4 should switch primary observation from `lst:llm-incorrect` to `lst:others-bug` and mark `classify_signal` secondary for consistency.
- Optional later: redraw `specir_walkthrough` / `fsf_semantics` TikZ around `classify_tier` residual $\Phi_3$.
