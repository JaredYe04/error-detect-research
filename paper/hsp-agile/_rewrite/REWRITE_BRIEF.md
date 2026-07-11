# Full Rewrite Brief (Orchestrator Constitution)

## Mentor Guidelines (mandatory)
1. **Abstract-then-Concrete:** Open paragraphs/sections with the high-level idea, then details.
2. **Concept First:** Define basic notions before mechanisms that use them.
3. **Example-Driven:** Keep/strengthen concrete vignettes (catch-all tier classifier as PRIMARY).
4. **Cohesive Integration:** Weave text, figures, tables, and math naturally (no orphan floats).

## Voice (CCF-B journal / conference)
- Objective, confident, evidence-led. No defensiveness.
- **FORBIDDEN phrases/patterns:** "reviewer concern", "What a reviewer should remember", "lead sell", "Non-claim:", "not a claim that…", "Anticipated Reviewer Questions", "to answer the reviewer", "make … explicit for reviewers", "demoted", "stress-tests only" as slogan (state role factually once), checklist jargon (C2/C3/C4 OK if defined once, then use sparingly).
- State scope honestly as *limitations* or *deployment guidance*, not as rebuttal FAQ.
- Preserve human scientific logic; polish language and structure only.

## Immutable claim spine (AUTHORITATIVE_NUMBERS)
- **Lead story:** acceptance safety = conjunctive release  
  `Accept ⇔ Conf=1 ∧ Screen=pass` — not "better generator".
- **E6 (C2 mechanism):** semantic_ir 86.9% vs test_only 79.1% → **+7.7 pp**; W/L/T **14/4/102**; CI **[2.3, 13.6]**; p=0.018; **14/14** wins are catch-all/`others` rescues, **0/14** ordering.
- **E2 (C3 prevention):** impl-screening M **PDR 95.0% / FAR 5.0%** vs B2 **91.2% / 8.8%**. Never use 0.14/0.22 FAR in method chapter.
- **Equal-K (hygiene):** M_eq **100.0%** vs B2 **97.5%** (+2.5 pp; 3/0/117).
- **E1 stress only:** B1/B2/M 84.2/98.3/100.0%; M is K=5 bundle — not single-factor C2.
- **E12:** B2 100% every seed; M 99.7% — do not claim M dominates all seeds.
- Prefer B2 by default; escalate to M when Accept/FAR and headroom require it.
- Cite fixed-oracle runs as primary; mention others-witness measurement correction once as enabling fair eval.
- Do not invent numbers. If unsure, keep the existing table `\input` and correct surrounding prose.

## Running example policy
- **Primary vignette everywhere:** tier/catch-all `OTHERWISE` → must return `Review`, LLM emits `Pass`; busy Reject/Pass tests green.
- **Secondary:** ordered overlaps (`classify_signal` / tax) for witness ordering and Φ_i — clearly marked secondary.
- Unify discontinuity: Ch.1 catch-all must still be the conceptual anchor in Ch.3–4.

## Technical constraints
- Keep existing `\label{...}`, major `\cite{...}`, `\input{tables/...}`, `\includegraphics` paths unless broken.
- Keep equation environments and theorem/definition environments when scientifically sound; tighten proofs; remove "motivational theorem" presentation if it overclaims — rephrase as Proposition/Remark if needed.
- Move results numbers out of Method into Results (Method may preview intent, not E6 win counts).
- Target: shorter, clearer chapters — cut duplication aggressively (esp. Ch.2 Gap vs Related; Ch.6 encyclopedia; Ch.8 FAQ).
- Output **complete compilable `.tex` chapter body** (same top-level `\chapter{...}` as original).
- Write ONLY to the assigned staging path under `_rewrite/`. Do not edit live `chapters/` or `front/`.

## Deliverable per agent
1. Write the full rewritten file to the assigned path.
2. Write a short `_rewrite/<id>_NOTES.md` with: what was removed (meta), what was restructured, any number fixes, any labels you could not preserve.
