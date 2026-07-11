# E6 Win-Task Qualitative Relabel (Agent A continuation)

**Source:** `artifacts/run_feedback_v2/feedback_variants/results.jsonl`  
**Win set:** 14 tasks where `semantic_ir` > `test_only`

## Headline (Reviewer-critical)

The E6 +7.7 pp gain is **not** primarily an *ordering / overlap-precedence* story on this corpus.

Across all semantic feedback records on the 14 win tasks:

| Signal | Value |
|--------|-------|
| `violation_type` | **arithmetic 100%** (87/87) |
| `suggested_fix` | **correct the output expression for the active scenario** (87/87) |
| `scenario_index` | **8 only** (87/87) — the FSF `others` catch-all |

So typed IR wins by helping the model **identify and repair the catch-all (`others`) scenario output**, not by teaching first-match reordering of overlapping guards.

## Why this still supports C2 (scoped)

- `test_expected` alone did **not** match full IR on E6 (78.9% vs 86.9%) → **expected output is insufficient**
- Full IR adds **scenario identity** (`Scenario 8` / `others` / constraint) + structured reason
- Therefore the irreplaceable fields to test in Agent B are especially:
  1. `scenario_index` / scenario naming (`ir_no_scenario_id`)
  2. `constraint_text` for others (`ir_no_constraint`)
  3. `expected` (`ir_no_expected`) as secondary

## Why fixed-oracle re-runs saturate

After the others-witness measurement correction, first-match `others` regions are correctly constrained. Many former E6-hard tasks now reach Conf=1.0 on attempt 1 → **repair feedback never fires** → field ablation ties at 100%.

Decisive-18 re-run under current harness: **all variants Conf=1.0** (null experiment).

## Paper wording (use this)

> Under controlled E6, typed Semantic Feedback IR improves repair over unstructured test-only (+7.7 pp). Qualitative inspection of the 14 win tasks shows the gain concentrates on repairing the catch-all `others` scenario (scenario index 8; arithmetic/output expression mismatches). This supports scenario-typed feedback, but does **not** by itself establish an overlap-ordering mechanism on BENCH-120. Ordering/overlap claims must rest on other evidence (witness design, prevention operators, worked examples) or a re-labeled / re-filtered corpus.

## Files

- `e6_win_qualitative.json`
- `e6_win_tasks.json`
