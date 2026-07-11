# ch04 Method — Rewrite Notes

## Number fixes
- **E2 FAR/PDR (authoritative):** table `tab:far-validation` and prose now cite impl-screening **M FAR 5.0% / PDR 95.0%** vs **B2 FAR 8.8% / PDR 91.2%**.
- Removed incorrect decimals **0.14 / 0.22** (and B1 0.38) from Method FAR table/prose.
- Bound column kept as illustrative envelope ≈47% under $\varepsilon{=}0.08$, $n{=}9$.

## Empirical results moved out of Method
- Removed E6 win counts (14/4/102, 14/14 catch-all, 13/14 Conf=0, etc.).
- Removed E14 uniqueness / mean-Conf comparisons (`execution_trace_matched` exceeds `semantic_ir`, etc.).
- Removed field-structure ablation claims from Method.
- Feedback IR section now states **design intent** only; forward-ref to Ch.~Results for E6/E14.
- Hypothesis `hyp:structured-feedback` kept; points to Results figures without quoting deltas.

## Vignette policy
- **Primary** worked example: catch-all tier classifier (`lst:others-fsf` / `lst:others-bug`); IR JSON is `output` / scenario 3 / Review vs Pass.
- **Secondary:** `classify_signal` ordering trail kept as `fig:worked-example-trace` with explicit secondary caption; $\Phi_1$–$\Phi_3$ labels `eq:phi1-example` / `eq:phi2-example` preserved; tax listings cross-ref’d.
- Replaced broken refs to `lst:fsf-spec` / `lst:llm-incorrect` (no longer defined in Ch.1).

## Stage 4 dedup
- Screen rationale stated once under `subsec:method:why-screen`.
- PoC catalogue once under `subsec:method:smell-poc`.
- Pluggability once under `subsec:method:pluggable-screen` (stripped “do not sell” / “not a claim” meta).
- Detection wiring unchanged in role.

## Labels
- `sec:method:screen` and `sec:method:guard` remain **intentional aliases on the same Stage~4 section** (Ch.5+ still refs `sec:method:guard`; Method prose uses `sec:method:screen`).
- `thm:far-bound` kept as label; environment demoted **Theorem → Proposition** with crisp i.i.d.\ assumptions; scope moved to new `rem:far-bound-scope`.
- `thm:witness-soundness` kept as label; environment remains Proposition; stripped “for reviewers” framing.
- All other major labels / `\input` / figures / algorithms preserved.
- Added `eq:phi-catchall` for primary vignette (new; no clash).
- Subsection titles slightly tightened (`Pluggable Screen Interface`); labels `subsec:method:*` unchanged.

## Meta / voice stripped
- “explicit for reviewers”, “not a claim”, “do not sell”, “Non-claim”, uniqueness disclaimers, and E6 qualitative win-coding prose removed from Method.
- Stage-summary Accept row now cites Prop.~\ref{thm:far-bound} (not “motiv. bound”).

## Follow-ups (out of scope for this staging file)
- Optional: redraw `worked_example_trace.tex` / `repair_feedback.tex` for catch-all primary (currently secondary ordering visuals; captions mark secondary / Results forward-ref).
- Live `chapters/ch04_method.tex` not edited (staging only).
