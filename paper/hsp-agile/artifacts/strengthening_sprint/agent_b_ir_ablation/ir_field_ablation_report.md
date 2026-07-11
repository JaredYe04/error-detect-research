# IR Field Ablation Summary

Rows=144 tasks=18

## Mean Conf by variant
```json
{
  "ir_nl_only": 1.0,
  "ir_no_constraint": 1.0,
  "ir_no_expected": 1.0,
  "ir_no_reason": 1.0,
  "ir_no_scenario_id": 1.0,
  "ir_no_suggested_fix": 1.0,
  "semantic_ir": 1.0,
  "test_only": 1.0
}
```

## Paired: full semantic_ir ???variant (negative ???field mattered)
```json
[
  {
    "a": "semantic_ir",
    "b": "ir_nl_only",
    "n": 18,
    "wins": 0,
    "losses": 0,
    "ties": 18,
    "mean_delta_pp": 0.0
  },
  {
    "a": "semantic_ir",
    "b": "ir_no_constraint",
    "n": 18,
    "wins": 0,
    "losses": 0,
    "ties": 18,
    "mean_delta_pp": 0.0
  },
  {
    "a": "semantic_ir",
    "b": "ir_no_expected",
    "n": 18,
    "wins": 0,
    "losses": 0,
    "ties": 18,
    "mean_delta_pp": 0.0
  },
  {
    "a": "semantic_ir",
    "b": "ir_no_reason",
    "n": 18,
    "wins": 0,
    "losses": 0,
    "ties": 18,
    "mean_delta_pp": 0.0
  },
  {
    "a": "semantic_ir",
    "b": "ir_no_scenario_id",
    "n": 18,
    "wins": 0,
    "losses": 0,
    "ties": 18,
    "mean_delta_pp": 0.0
  },
  {
    "a": "semantic_ir",
    "b": "ir_no_suggested_fix",
    "n": 18,
    "wins": 0,
    "losses": 0,
    "ties": 18,
    "mean_delta_pp": 0.0
  },
  {
    "a": "semantic_ir",
    "b": "test_only",
    "n": 18,
    "wins": 0,
    "losses": 0,
    "ties": 18,
    "mean_delta_pp": 0.0
  }
]
```

## Ranked harm when removing a field (lower mean_delta_pp = more critical)
- `ir_nl_only`: ??=0.0 pp (W/L/T 0/0/18)
- `ir_no_constraint`: ??=0.0 pp (W/L/T 0/0/18)
- `ir_no_expected`: ??=0.0 pp (W/L/T 0/0/18)
- `ir_no_reason`: ??=0.0 pp (W/L/T 0/0/18)
- `ir_no_scenario_id`: ??=0.0 pp (W/L/T 0/0/18)
- `ir_no_suggested_fix`: ??=0.0 pp (W/L/T 0/0/18)
- `test_only`: ??=0.0 pp (W/L/T 0/0/18)
