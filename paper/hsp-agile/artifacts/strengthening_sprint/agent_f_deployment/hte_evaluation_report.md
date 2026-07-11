# Headroom-Triggered Escalation Evaluation

## Scope

This report evaluates Headroom-Triggered Escalation (HTE) using only features available before repair execution. The inspected pre-hoc feature set is the one listed in `deployment_rules.json`: overlap rate, guard-atom/operator counts, atom density per guard, prompt spec length, and input/output/scenario counts.

Post-hoc signals such as `conf_test_only`, repair attempts, feedback length, and first-failure violations are excluded from the trigger. They are valid outcome labels or diagnostics only after an experiment has run.

## Data Inspected

- `deployment_rules.json`
- `deployment_tree_rules.txt`
- `cv_metrics.json`
- `policy_eval.json`
- `task_feature_db.json`
- `winner_feature_summary.json`
- `winner_feature_analysis.md`
- `winner_feature_tables.md`
- `summary_by_mode.csv`
- `generalisation_summary.csv`
- `e6_paired_summary.csv` / `.json`
- `e6_ecnu_max_summary.csv`
- RealSpec, public-harvest, desensitized-industrial, and advisory processed summaries

## Label Definition

The only usable task-level label in the hard-task feature DB is whether typed Semantic Feedback IR beats the test-only comparator:

`positive = delta_ir_minus_test_only > 0`

This gives 14 positives, 4 losses, and 102 ties over 120 hard synthetic tasks. Ties and losses are treated as negatives for precision/recall because an escalation trigger should identify cases where M/semantic IR adds value.

This is an in-sample diagnostic label, not an externally validated deployment label.

## In-Sample HTE Diagnostics

| Rule | Triggered | TP | FP | FN | TN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Deployment tree (`deployment_tree_rules.txt`) | 66/120 | 11 | 55 | 3 | 51 | 0.167 | 0.786 | 0.275 |
| Simple tier rule from `deployment_rules.json` (`high` or `low` -> inspect M) | 86/120 | 11 | 75 | 3 | 31 | 0.128 | 0.786 | 0.220 |
| Low-overlap tier only | 48/120 | 7 | 41 | 7 | 65 | 0.146 | 0.500 | 0.226 |
| High-overlap tier only | 38/120 | 4 | 34 | 10 | 72 | 0.105 | 0.286 | 0.154 |
| Boundary density >= 2.571 | 80/120 | 10 | 70 | 4 | 36 | 0.125 | 0.714 | 0.213 |
| Overlap rate >= 1.0 | 115/120 | 14 | 101 | 0 | 5 | 0.122 | 1.000 | 0.217 |

The base positive rate is 14/120 = 0.117. The pre-hoc rules improve recall but not precision enough to support an automatic escalation claim. The best inspected pre-hoc tree reaches 0.167 precision, only about 5.0 percentage points above base rate, while escalating 55% of tasks.

## Cross-Validation and Signal Check

The existing predictor artifacts also indicate weak pre-hoc signal:

- Classifier AUC is 0.5098, near chance.
- Mean cross-validated F1 is 0.2551.
- Delta-regressor CV MAE is 0.1898, worse than the predict-zero baseline MAE of 0.1247.
- Several nominal features have no variation in the hard synthetic feature DB: all tasks have 7 scenarios, 5 inputs, 3 outputs, and `Nested` guard complexity.

The prior high-lift threshold rules based on `conf_test_only` are not admissible for this HTE setting because they require running the comparator first. They should not be cited as pre-hoc deployment performance.

## External / Processed Summary Checklist

The processed external summaries do not provide enough positive escalation labels for a precision/recall claim:

| Source | Observed Signal | HTE Use |
|---|---|---|
| RealSpec B1/B2/M summary | B2 = M = 1.000 over 103 tasks | Saturated; no M-over-B2 positives |
| RealSpec E6 B1-fail summary | test-only, test-expected, and semantic IR all 1.000 over 30 tasks | Saturated; no escalation labels |
| Real priority micro summary | M_eq vs B2: 0 wins, 0 losses, 30 ties | Null/tie set |
| GitHub harvest summary | M_eq vs B2: 1 win, 1 loss, 46 ties; equal mean Conf | Too few positives and no useful lift |
| Desensitized real SOFL pilot | all modes 100% over 28 tasks | Saturated; no escalation labels |
| Generalisation summary | mixed corpus means only, no task-feature-paired HTE labels | Not evaluable for precision/recall |
| E11 external summary | aggregate mode means only; M lower than B1/B2 | Not an HTE-positive label set |
| E6 ecnu-max summary | variant means nearly tied, no paired trigger table in summary | Not enough signal |

## Deployment Interpretation

HTE should be reported as a conservative release-policy checklist, not as a reliable ML predictor:

1. Default to B2/test-feedback when no release gate requires full escalation.
2. Permit pre-hoc rules such as the deployment tree or high/low overlap tier only as advisory inspection triggers.
3. Escalate to M/typed Semantic Feedback IR when release requirements demand Accept/FAR assurance or when a separate validated headroom signal exists.
4. Do not claim external precision/recall until task-level external features and paired B2-vs-M labels are available.

## Bottom Line

Labels exist for the hard synthetic feature DB, so precision/recall can be reported in-sample. The result is weak: the best inspected pre-hoc HTE rule has precision 0.167 and recall 0.786 against a base positive rate of 0.117. External and processed summaries are saturated, tied, or aggregate-only, so they support a transparent null report rather than a deployment-performance claim.
