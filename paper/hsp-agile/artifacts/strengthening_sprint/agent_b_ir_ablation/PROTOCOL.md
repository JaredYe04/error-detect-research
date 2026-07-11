# IR Field Ablation Protocol (Agent B)

## Goal

Identify which Semantic Feedback IR fields are **irreplaceable** for repair under mode M, $K{=}3$.

## Variants

| Key | What is removed / changed |
|-----|---------------------------|
| `test_only` | Anchor: unstructured tests |
| `semantic_ir` | Full 9-field IR |
| `ir_no_scenario_id` | Hide scenario index |
| `ir_no_expected` | Omit expected outputs |
| `ir_no_constraint` | Omit guard / boundary predicate text |
| `ir_no_reason` | Omit reason |
| `ir_no_suggested_fix` | Omit fix hint |
| `ir_nl_only` | Prose paraphrase (no structured labels) |

Causal hygiene: field ablations do **not** append the extra scenario-postcondition hint used by full `semantic_ir` in the pipeline (see `build_repair_feedback`).

## Smoke (n=5 tasks)

```powershell
cd d:\repos\error-detect-research
python experiments/run_sweep.py `
  --experiment ir_field_ablation `
  --run-name run_ir_field_ablation_smoke `
  --task-limit 5 `
  --parallelism 4
```

## Full campaign (n=120, seed via model stochasticity; repeat with --seed if wired)

```powershell
python experiments/run_sweep.py `
  --experiment ir_field_ablation `
  --run-name run_ir_field_ablation_v1 `
  --parallelism 8
```

Optional multi-seed: re-run with different `--model` temperature settings or repeat nights; analysis script aggregates by `task_id`×`feedback_variant`.

## Analyze

```powershell
python paper/hsp-agile/scripts/strengthening/analyze_ir_field_ablation.py `
  --results artifacts/run_ir_field_ablation_v1/ir_field_ablation/results.jsonl
```

## Success criterion for paper

Report which ablations lose ≥X pp vs full IR with CI / paired W/L/T.
Expected reviewer-facing claim shape:

> Scenario identity + boundary constraint text are necessary; removing them collapses the E6 gain toward test_only.
