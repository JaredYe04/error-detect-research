# ch05 rewrite notes

## What was removed (meta)
- Opening framing as “not a contribution catalogue.”
- Pattern-section rebuttal: “not a claim that hand-authored rules are the only admissible screen” / “not overfit to BENCH-120 as a scientific contribution.”
- Subsection titles that read as claim defence (“Abstract Role…”, “Pluggability: Rules Today…”, “Conjunctive Acceptance Gate Role”).
- Caption boilerplate “Key observation / How to read” (content retained in plain captions).
- Repeated claim-tagging in the intro (C2/C3/C4 inventory); claims kept only in the chapter summary.
- Secondary vignette as the default path (`classify_signal` / `compute_tax` as primary narrative).

## What was restructured
- Architecture → modules → trade-offs retained; opening now states “system realisation; algorithms in Ch.4.”
- **Primary vignette** switched to catch-all tier classifier (`OTHERWISE` → `Review`, candidate emits `Pass`), with an explicit Semantic Feedback IR JSON example in §LLM / repair-feedback.
- `classify_signal` / ordering mentioned once as secondary regime.
- Pattern screen collapsed into one section (role → PoC detectors → pluggability → conjunctive gate) without defensive “Non-claim” prose.
- Checker section points to Algorithm `alg:checker` in method; keeps `alg:case-gen` / `alg:repair-loop` as implementation sketches.
- Domain-bound mismatch (`[-5,20]` solver vs `[0,100]^5` metadata) stated once, factually, with appendix pointer.

## Number / claim hygiene
- No result numbers moved into this chapter (E6/E2 stay out).
- Mode table and latency ballparks unchanged.
- Accept equation restated once for the screen module (same as live chapter).

## Labels preserved
All major labels retained: `ch:implementation`, `sec:impl:*`, `fig:component-arch`, `fig:system-class`, `fig:fsf-parser-class`, `fig:checker-activity`, `fig:pipeline-state`, `alg:case-gen`, `alg:repair-loop`, `tab:impl-modes`.
Figure `\IfFileExists` / `\pumlfig` paths unchanged.

## Cross-refs kept (depend on other chapters)
- `lst:others-fsf`, `lst:others-bug` (Ch.1)
- `eq:accept`, `eq:priority`, `eq:conformance`, `alg:sgdp`, `alg:checker`, `fig:sgdp-overview`, `fig:accept-tree`, `fig:repair-feedback`, `tab:patterns`, `sec:method:guard`, `subsec:method:prompt`, `subsec:conformance-acceptance`, `def:scenario`, `def:oracle`, `app:reproducibility`, `sec:results:sensitivity`

## Could not / did not change
- Live `chapters/ch05_implementation.tex` untouched (staging only).
- Did not invent witness inputs beyond the vignette schema; mid-band `(score=3, floor=10)` is illustrative of residual activation, consistent with the FSF listing.
