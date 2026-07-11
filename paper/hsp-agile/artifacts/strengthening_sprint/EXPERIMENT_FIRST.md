# Experiment-First Status

**Policy:** Narrative frozen. Wave-1 analyzed; Wave-2 running.

## Wave-1 verdict (see `agent_b_ir_ablation/WAVE1_VERDICT.md`)

- Best signals: gemini invert_order FULL>A (+31pp); RealSpec gemini wrong_relop FULL>A (+17pp); ecnu swap_bodies / wrong_relop field.
- gpt-4o-mini saturated (useless as "weak" model on single seeds).
- hard_all n=60 diluted E6-win14 gaps.

## Wave-2 running

| ID | Experiment | Out dir |
|----|------------|---------|
| W2a | Combo seeds @ gpt-4o-mini | `run_ir_combo_seed_gpt4omini_v1` |
| W2b | Combo seeds @ gemini | `run_ir_combo_seed_gemini_v1` |
| W2c | Combo seeds @ deepseek-chat | `run_ir_combo_seed_deepseek_v1` |
| W2d | RealSpec wrong_relop full @ gemini | `run_ir_hard_seed_realspec_wrong_relop_gemini_full_v1` |
