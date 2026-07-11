# Failure Taxonomy (Agent E)

**Corpus:** E6 `run_feedback_v2` (semantic_ir under mode M).  
**Not** the historical pre-fix E9 pie (Strict???%).

## Counts

| Slice | n |
|-------|--:|
| Tasks with semantic_ir row | 120 |
| IR not at Conf=1.0 | 114 |
| IR rescues vs test_only | 14 |

## Primary category among IR residuals (Conf < 1)

| Category | n |
|----------|--:|
| Arithmetic | 98 |
| RepairRegression | 16 |

## Categories on IR-rescue tasks (where typed IR beat test_only)

These are the failure modes typed IR most often *fixes* (primary label from IR attempt history ???often the residual type mid-repair):

| Category | n |
|----------|--:|
| Arithmetic | 13 |
| RepairRegression | 1 |

## Definitions

- **Ordering:** first-match / scenario precedence violations
- **Boundary:** off-by-one / relational edge errors
- **Arithmetic:** wrong output expression under correct branch
- **RepairRegression:** Conf decreases across attempts
- **OverRepair:** new violation categories appear after a repair step
- **Hallucination / MissingGuard / WrongThreshold / StateLongRange:** as named

## Implications for IR design

- If Ordering/Boundary dominate residuals ???strengthen scenario_id + constraint_text fields (Agent B).
- If RepairRegression is common ???early-stopping / argmax Conf selection matters.
- If Arithmetic dominates ???witnesses-on-guards alone are insufficient (known limitation).

## Files

- `failure_taxonomy.json` / `.csv`
