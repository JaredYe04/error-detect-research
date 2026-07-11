# Paper Strengthening Sprint — Mission Control

**Start:** 2026-07-11  
**Duration target:** 2–3 weeks  
**Goal:** Borderline → Reviewer-proof (not higher mean Accuracy)

## Three Reviewer Questions

1. Why must HSP/SgDP exist?
2. When to enable HSP vs B2?
3. Why is Typed Semantic Feedback IR irreplaceable?

## One-sentence story

> Typed Semantic Feedback is not universally better; it has irreplaceable value on high-overlap, ordered-guard, boundary-rich specs — and a pre-hoc rule decides when to pay for the full loop.

**Honesty update (Agent A/F):** pre-hoc classifier on BENCH-120 features is weak (AUC≈0.51); E6 deltas are non-monotone across overlap tertiles. Keep Accept/FAR as primary C4; field ablation is the uniqueness proof.

## Agent status

| Agent | Status |
|-------|--------|
| A Evidence Mining | DONE |
| B IR Field Ablation | CODE DONE; LLM PENDING |
| C RealSpec | DONE (103 tasks) |
| D Industrial | PARTIAL (in RealSpec) |
| E Failure Taxonomy | DONE |
| F Deployment Predictor | DONE (honest-negative) |
| G/H Story | OUTLINE DONE |

Details: `EXECUTIVE_FINDINGS.md`
