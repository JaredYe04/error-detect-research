# Mock PC Review — Round 6

**Paper:** Deployment-Aware Specification-Guided Repair (HSP-Agile / SgDP)  
**Venue target:** CCF-B (SE / FM-adjacent)  
**Reviewer stance:** Methods + empirical rigor, skeptical of synthetic benchmarks  
**Date:** 2026-07-10

---

## Overall recommendation

| Metric | Score |
|--------|------:|
| **Acceptance probability** | **64%** |
| **Confidence** | Medium |
| **Decision** | **Weak Accept** (borderline; fixable credibility gaps) |

**Δ vs R5 (est. 65–68%):** −2 to +1 pp. Narrative honesty improved materially, but **cross-chapter number drift** (especially B0 / A2) would alarm a careful reviewer and partially offsets Phase 5 gains.

---

## Summary (2 sentences)

The paper reframes a specification-guided LLM repair loop as a **conditional deployment** problem rather than universal M > B2 superiority. The lead evidence is clean: E6 (+7.7 pp typed Semantic Feedback IR under controlled comparison) plus a practitioner-facing deployment table; aggregate E1/E12 show B2 ≥ M with disclosed non-significance and low power.

---

## Strengths

1. **Honest aggregate negative result.** Canonical E1 (B1 89.2 / B2 87.7 / M 86.3) and E12 (B2 leads all seeds, Friedman *p* = 0.077, M wins 4/120) are reported without overselling. Power analysis (δ ≈ −0.014, ~3.6% power) is rare and appreciated.

2. **Mechanism-first evidence (E6).** Holding *K*, tasks, and model fixed, full Semantic Feedback IR vs test-only is the paper's strongest causal claim (+7.7 pp). E14 length-matched sweep partially addresses fairness concerns.

3. **Deployment boundary (C4) as primary deliverable.** Table `tab:deployment-boundary` synthesises E3/E10/E11/E8c into actionable guidance ("default B2; deploy M for Accept / PDR-FAR / typed IR"). This is more defensible than headline conformance.

4. **Prevention metrics (E2).** PDR 95.0% / FAR 5.0% vs B2 91.2% / 8.8% gives a concrete reason to pay 3.3× latency—not mean Conf.

5. **External validity attempts.** E10 (unfiltered random, B2 89.1% vs M 83.1%), E11 (*n* = 22 external SOFL), E16 (ecnu-max, *n* = 120), and E8c (HumanEval/MBPP) bound rather than prove transfer—but they exist.

6. **Reproducibility.** Canonical run IDs, benchmark fingerprint, refresh scripts, and superseded-corpus footnote (86-task / M 90.4%) show mature artifact hygiene.

---

## Weaknesses (ranked)

### W1 — Cross-chapter numeric inconsistency (**Major, credibility**)

Multiple chapters still cite **B0 at 27.5%** as difficulty calibration (`ch06` L147, `ch07` L426, `ch08` L43, L525), but canonical `summary_by_mode.csv` reports **B0 Conf 89.2%, Strict 5.0%**—identical to B1.

A PC reviewer will ask: *Is the benchmark hard? Is B0 a meaningful floor? Did the authors re-run without updating prose?*

**Required fix:** Reconcile B0 metric (strict vs conf vs old run) or regenerate calibration narrative from canonical CSV.

### W2 — C1 / overlap narrative still partially contradicts E3 (**Major, claims**)

Canonical E3 tertiles are **non-monotone** (M ties B2 at high, trails at medium). Yet:

- `abstract.tex` L19–20: "gain is largest in the high-overlap tier" (conflates E6 with E3)
- `ch08` L38: "E3/E4 support C1 (gap grows with overlap)"
- `ch01` C4: "full M when overlap is dense"

E10 aggregate also favours B2. The honest story is **overlap-conditional / mechanism-specific**, not "dense overlap ⇒ M."

**Required fix:** Tighten abstract, ch08 §interpretation, and C4 wording to match `tab:e3-tiers` + E10 figure.

### W3 — Residual A2 ablation stale text (**Minor but visible**)

`ch08` L44–45 still states A2 **+0.5 pp** on Conf; canonical table has A2 **80.3%** vs M **86.3%** (−6 pp). Partially fixed in ch07/sections but not in ch08 opening interpretation.

### W4 — Synthetic benchmark dominance (**Structural**)

120-task hard SOFL/FSF corpus is author-constructed with overlap filter. E11 (*n* = 22) and E8c help but do not fully address "benchmark chases the method." E16 null result (all 89.2% on second model) further weakens discriminative claims on easier endpoint.

### W5 — Strict-success paradox under-explained for practitioners (**Minor**)

5% strict success across modes is explained as conjunctive Accept design, but ch08 still says "114 tasks (95.0%) do not reach acceptance" while also citing 90 residual failures in E9 taxonomy—internal counting needs one clear denominator sentence.

### W6 — E14 weakens "semantic IR" uniqueness (**Minor**)

`execution_trace_matched` (85.4%) ≫ `semantic_ir` (75.1%) suggests structured *trace* feedback may dominate region typing. Authors disclose this; PC may ask whether C2 is "any structured trace" vs "SpecIR regions."

---

## Questions for authors

1. **B0 calibration:** Which metric is 27.5%—an old strict-success run, a different benchmark slice, or stale prose? Please make B0/B1 relationship consistent everywhere.

2. **When exactly should a team deploy M over B2?** Give a decision procedure with *one* measurable signal (e.g., conjunctive Accept required, or PDR target > 93%) that does not rely on overlap tertiles alone.

3. **E6 vs E14:** Under length-matched traces, does region-typed Semantic IR still beat execution-trace-matched on the *same* failure cases (paired per task)?

4. **Industrial SOFL:** Any pilot on non-synthetic practitioner specs beyond 22 external tasks?

---

## Dimension scores

| Dimension | Score (1–5) | Note |
|-----------|:-----------:|------|
| Problem significance | 4 | Ordered-guard / test-gap is real for Agile-SOFL |
| Technical depth | 4 | SpecIR + SMT witnesses + typed IR well motivated |
| Evaluation rigor | 3.5 | Broad experiments; synthetic core; power limited |
| Honesty / negative results | 4.5 | Best-in-class disclosure for this genre |
| Clarity | 3.5 | Mechanism-first helps; number drift hurts |
| Reproducibility | 4.5 | Canonical runs + scripts |
| Novelty vs repair loops | 3 | Incremental over verifier-loop / self-debug; deployment table differentiates |

---

## Conference vs thesis

| Track | Fit |
|-------|-----|
| **10-page conference skeleton** | Ready structurally; abstract + results_stub align with honest narrative |
| **Full thesis** | Strong artifact; needs B0/A2/C1 prose pass before camera-ready |

---

## Actionable fix list (to reach ~70%+)

| Priority | Item | Est. Δ |
|----------|------|--------|
| P0 | Fix B0 27.5% vs 89.2% across ch06/ch07/ch08 | +3–4% |
| P0 | Abstract + ch08 C1: remove "gap grows with overlap" | +2% |
| P1 | ch08 L44–45 A2 −6 pp (not +0.5) | +1% |
| P1 | Align E9 failure counts (90 vs 114) | +0.5% |
| P2 | E11 expansion or case study vignette | +1–2% |
| P2 | Compile conference PDF + bib check | +0.5% (presentation) |

**Projected score after P0–P1:** **68–72%** (solid Weak Accept / low Borderline Accept).

---

## PC one-liner (for meta-review)

> *Credible conditional-deployment paper with a strong E6 mechanism and unusually honest negative aggregates; acceptance hinges on eliminating stale B0/A2/C1 prose that currently undermines trust in an otherwise careful empirical package.*

---

## R6 fix status (2026-07-10)

| Item | Status |
|------|--------|
| P0 B0 27.5% → canonical 89.2% | ✅ |
| P0 C1/overlap narrative | ✅ |
| P1 A2 −6 pp | ✅ |
| P1 E9 114 vs 90 | ✅ |
| P1 power δ / 3.6% | ✅ |

*Author response: `AUTHOR_RESPONSE_R6.md`. Post-fix est. 68–72%.*

---

*Round 6 reviewer simulation. Not an official PC decision.*
