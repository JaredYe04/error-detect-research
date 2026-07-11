# Strengthening Sprint — Executive Findings

**Policy:** Experiment-first. Paper narrative is **frozen**. Interim pilots must not drive Abstract/Intro/C2 edits.

## Completed infrastructure (not conclusions)

| Track | Output |
|-------|--------|
| A Feature DB / winner analysis | `agent_a_evidence/` |
| B Field render variants | `src/repair/feedback_ir.py` |
| B Easy others_const pilot | under-separates → motivates harder seeds |
| C RealSpec corpus | 103 tasks (all have `referenceCode`) |
| RealSpec B1/B2/M ranking | B1 90.3% / B2 100% / M 100% (saturated for M−B2) |

## Active experiments

| ID | Experiment | Artifact |
|----|------------|----------|
| H1 | Hard seeds @ ecnu-plus (14 E6-win) | `run_ir_hard_seed_ablation_ecnu_plus_v1` |
| H2 | Hard seeds @ gemini-2.5-flash | `run_ir_hard_seed_ablation_gemini_flash_v1` |
| H4 | Hard seeds n=30 from hard_all_120 | `run_ir_hard_seed_ablation_ecnu_plus_n120_v1` |
| H5 | Hard seeds on RealSpec | queued |
| H6 | Weaker model (gpt-4o-mini) RealSpec hard seeds | queued |

## Hypotheses under test (not claims)

1. Harder structural bugs yield larger FULL−ablation gaps than `others_const`
2. Weaker models increase repair headroom so field ablation is measurable
3. RealSpec hard-seed (injected) shows the same ordering as synthetic hard seeds

## Explicit non-actions

- Do **not** rewrite C2 as “others/expression-only”
- Do **not** drop typed-IR uniqueness language from pilots alone
- Do **not** invent enable-predictor claims (AUC≈0.51)

Only after H1–H6 + CIs: decide whether to keep, narrow, or revise wording.
