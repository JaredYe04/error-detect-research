# ch02 rewrite notes (Formalist+Pedagogue)

## What was removed (meta / defensiveness)
- All “not a claim that…” / uniqueness-disclaimer hedges after Related Work and Gap.
- Gap-section re-hash of agents / APR / Alloy / Self-Debug already covered in Related Work.
- Second positioning table (`tab:related-positioning` content) — near-duplicate of `tab:related-work`.
- Entire `tab:repair-loops` float with **pre-fix** Conf.% (87.7 / 81–87 / 81.8 / 79.0 / 80.3 / 86.3) and the E13 / E18 Conf narrative that cited those stale numbers as primary colour.
- Reviewer-facing tone and “irreducible increment … not a claim” framing; replaced with confident combination-of-ingredients positioning.
- Inline E6 win-count / Conf-dominance digressions from the background narrative (deferred to Results).

## What was restructured
- **Concept-first order preserved and strengthened:** SOFL → FSF (semantics) → LLM → CEGIS → SMT → patterns → mutation → Related Work → short Gap.
- **FSF vignette policy:** catch-all / `OTHERWISE`→`Review` is now the **primary** semantics example; `classify_signal` ordering is explicitly **secondary** (aligned with Ch.1 and REWRITE_BRIEF).
- LLM failure modes reordered: residual/catch-all first, then order, then boundary.
- Related Work + Gap **deduplicated:** Gap is now a short claim spine (Premise / C2 / C3 + C4 deployment pointer), not a second literature survey.
- **One positioning table:** kept `tab:related-work` as the sole comparison; added Self-Refine/Self-Debug/Reflexion row (formerly only in the dropped second table); dual-labelled `\label{tab:related-positioning}` as an alias on the same float for cross-ref stability.
- Baseline B1/B2/B6/M described once in prose; ranking numbers pointed to Results rather than embedded Conf tables.
- Accept predicate previewed once in Gap as conjunctive release (claim spine), without method-chapter result dumps.

## Number fixes / hygiene
- Dropped all primary-narrative use of historical pre-fix E1 Conf figures.
- No invented numbers; no E1/E6/E2 numeric claims in this chapter (intent + axes only).
- Fixed-oracle / authoritative figures remain the responsibility of Results (per AUTHORITATIVE_NUMBERS).

## Labels preserved
| Label | Status |
|-------|--------|
| `ch:background` | kept |
| `sec:bg:sofl`, `sec:bg:fsf`, `sec:bg:fsf:semantics` | kept |
| `sec:bg:llm`, `sec:bg:cegis`, `sec:bg:smt` | kept |
| `sec:bg:patterns`, `sec:bg:mutation` | kept |
| `sec:bg:related`, `sec:bg:gap` | kept |
| `fig:cegis-loop` | kept (same `\tikzinput`) |
| `tab:related-work` | kept (sole table) |
| `tab:related-positioning` | **alias** on same table (content merged) |
| `tab:repair-loops` | **dropped** — no remaining cross-refs outside this chapter; Conf columns were pre-fix |

## Labels / floats not preserved as independent objects
- `tab:repair-loops` — removed with the pre-fix Conf table. If a later chapter or conference stub cites it, retarget to `tab:main-results` / mode definitions in Ch.6, or restore a results-only baseline table without historical Conf.

## Cite / input hygiene
- Major `\cite{...}` clusters retained and slightly consolidated; added `yasunaga2021breakitfix` into the APR paragraph (was only in old Gap).
- No `\input{tables/...}` in original ch02; none added.
- Cross-refs to `ch:intro`, `lst:others-fsf`, `ch:formalization`, `fig:fsf-semantics`, `app:patterns`, `def:pdr`/`def:far`, `ch:experiments`, `ch:results` preserved/used.
)
