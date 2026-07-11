# Agent B STATUS (updated)

## Completed

- Field render variants + unit tests
- Full-pipeline ablations: smoke / decisive-18 / headroom34 → **ceiling null**
- Seeded others-constant ablation: `artifacts/run_ir_seeded_others_ablation_v1/` (14 seeds × 9 variants)

## Seeded summary

Almost all variants recover simple constant bugs; `test_only` / `ir_no_reason` / `ir_no_suggested_fix` at 0.991 vs 1.0 for full IR.

## Blocked claim

Cannot yet claim “scenario_id + constraint are irreplaceable” from these runs.

## Next

Harder seeds (scenario-body swap / guard-order inversion) or weaker endpoint.
