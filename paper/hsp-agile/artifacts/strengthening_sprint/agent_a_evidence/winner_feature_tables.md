# Winner Feature Tables (E6 Evidence Mining)

Source: `run_feedback_v2/feedback_variants` paired with `hard_tasks_annotated.json`.

## 1. Outcome counts

| Group | Definition | n |
|-------|------------|---|
| M-win | C > A (`semantic_ir` > `test_only`) | 14 |
| A-win | A > C | 4 |
| Tie (C=A) | C == A | 102 |
| B2-like | A ≥ C (A-win + tie) | 106 |

## 2. Three-way E6_winner (argmax Conf)

| E6_winner | n |
|-----------|---|
| tie | 118 |
| semantic_ir | 2 |

## 3. Feature means by C−A group

| Feature | M-win mean | M-win median | A-win mean | Tie mean | B2-like mean | Cohen d (M vs B2-like) |
|---------|------------|--------------|------------|----------|--------------|------------------------|
| conf_test_only | 0.045 | 0.000 | 0.896 | 0.890 | 0.890 | -12.858 |
| conf_semantic_ir | 0.911 | 0.875 | 0.188 | 0.890 | 0.863 | 0.327 |
| overlap_rate | 1.196 | 1.167 | 1.208 | 1.246 | 1.245 | -0.292 |
| n_scenarios | 7.000 | 7.000 | 7.000 | 7.000 | 7.000 | 0.000 |
| boundary_density | 2.541 | 2.571 | 2.607 | 2.545 | 2.547 | -0.065 |
| prompt_spec_len | 680.000 | 681.000 | 684.250 | 680.373 | 680.519 | -0.071 |
| n_repair_attempts_semantic_ir | 3.000 | 3.000 | 3.000 | 2.990 | 2.991 | 0.103 |
| mean_feedback_len_semantic_ir | 830.810 | 1004.333 | 739.500 | 1008.301 | 998.157 | -0.436 |

## 4. Categorical composition (C−A groups)

### Overlap tier

| Group | low | medium | high |
|-------|-----|--------|------|
| M_win | 7 | 3 | 4 |
| A_win | 1 | 3 | 0 |
| tie | 40 | 28 | 34 |

### Guard complexity

| Group | Nested |
|-------|---|
| M_win | 14 |
| A_win | 4 |
| tie | 102 |

## 5. Threshold / regime scan (elevated M-win rate)

Base M-win rate: **14/120** = 0.117.

Non-vacuous rules sorted by lift (vacuous full-suite rules listed last).

| Rule | n_subset | n_M_win | win_rate | share_of_14_wins | lift | vacuous |
|------|----------|---------|----------|------------------|------|---------|
| `conf_test_only==0` | 13 | 13 | 1.000 | 0.929 | 8.571 | False |
| `conf_test_only<0.25` | 13 | 13 | 1.000 | 0.929 | 8.571 | False |
| `conf_test_only<0.5` | 13 | 13 | 1.000 | 0.929 | 8.571 | False |
| `conf_test_only==0_AND_overlap_tier==low` | 6 | 6 | 1.000 | 0.429 | 8.571 | False |
| `conf_test_only==0_AND_overlap_tier==high` | 4 | 4 | 1.000 | 0.286 | 8.571 | False |
| `overlap_tier==low` | 48 | 7 | 0.146 | 0.500 | 1.250 | False |
| `boundary_density>=2.571` | 80 | 10 | 0.125 | 0.714 | 1.071 | False |
| `overlap_rate>=1.000` | 115 | 14 | 0.122 | 1.000 | 1.043 | False |
| `overlap_rate>=1.300` | 38 | 4 | 0.105 | 0.286 | 0.902 | False |
| `overlap_rate>=1.333` | 38 | 4 | 0.105 | 0.286 | 0.902 | False |
| `overlap_tier==high` | 38 | 4 | 0.105 | 0.286 | 0.902 | False |
| `overlap_tier==high_AND_n_scenarios>=7` | 38 | 4 | 0.105 | 0.286 | 0.902 | False |
| `overlap_rate>=1.3_AND_n_scenarios>=7` | 38 | 4 | 0.105 | 0.286 | 0.902 | False |
| `overlap_rate>=1.200` | 72 | 7 | 0.097 | 0.500 | 0.833 | False |
| `overlap_rate>=1.208` | 72 | 7 | 0.097 | 0.500 | 0.833 | False |
| `overlap_tier==medium` | 34 | 3 | 0.088 | 0.214 | 0.756 | False |
| `overlap_rate>=1.292` | 46 | 4 | 0.087 | 0.286 | 0.745 | False |
| `overlap_rate>=1.167` | 82 | 7 | 0.085 | 0.500 | 0.732 | False |
| `overlap_rate>=1.167_AND_n_scenarios>=7` | 82 | 7 | 0.085 | 0.500 | 0.732 | False |
| `overlap_rate>=1.400` | 27 | 2 | 0.074 | 0.143 | 0.635 | False |
| `guard_complexity==AND` | 0 | 0 | — | 0.000 | — | False |
| `guard_complexity==Mixed` | 0 | 0 | — | 0.000 | — | False |
| `guard_complexity==Arithmetic` | 0 | 0 | — | 0.000 | — | False |
| `guard_complexity==Simple` | 0 | 0 | — | 0.000 | — | False |
| `n_scenarios>=7` | 120 | 14 | 0.117 | 1.000 | 1.000 | True |
| `boundary_density>=2.429` | 120 | 14 | 0.117 | 1.000 | 1.000 | True |
| `guard_complexity==Nested` | 120 | 14 | 0.117 | 1.000 | 1.000 | True |

## 6. The 14 M-win tasks (C > A)

| task_id | Conf_A | Conf_C | ΔC−A | overlap_rate | tier | boundary_density | guard |
|---------|--------|--------|------|--------------|------|------------------|-------|
| HardSynthetic.HardCase004 | 0.0000 | 0.9583 | 0.9583 | 1.000 | low | 2.571 | Nested |
| HardSynthetic.HardCase005 | 0.0000 | 0.8750 | 0.8750 | 1.250 | medium | 2.429 | Nested |
| HardSynthetic.HardCase010 | 0.0000 | 0.9583 | 0.9583 | 1.125 | low | 2.571 | Nested |
| HardSynthetic.HardCase012 | 0.0000 | 0.8750 | 0.8750 | 1.333 | high | 2.571 | Nested |
| HardSynthetic.HardCase028 | 0.0000 | 0.8750 | 0.8750 | 1.208 | medium | 2.571 | Nested |
| HardSynthetic.HardCase037 | 0.6250 | 0.9583 | 0.3333 | 1.000 | low | 2.714 | Nested |
| HardSynthetic.HardCase047 | 0.0000 | 0.9583 | 0.9583 | 1.083 | low | 2.571 | Nested |
| HardSynthetic.HardCase065 | 0.0000 | 0.8750 | 0.8750 | 1.500 | high | 2.429 | Nested |
| HardSynthetic.HardCase097 | 0.0000 | 0.8750 | 0.8750 | 1.333 | high | 2.571 | Nested |
| HardSynthetic.HardCase104 | 0.0000 | 0.8750 | 0.8750 | 1.250 | medium | 2.429 | Nested |
| HardSynthetic.HardCase116 | 0.0000 | 0.8750 | 0.8750 | 1.458 | high | 2.429 | Nested |
| HardSynthetic.HardCase118 | 0.0000 | 0.9583 | 0.9583 | 1.042 | low | 2.571 | Nested |
| HardSynthetic.HardCase122 | 0.0000 | 0.9583 | 0.9583 | 1.083 | low | 2.571 | Nested |
| HardSynthetic.HardCase124 | 0.0000 | 0.8750 | 0.8750 | 1.083 | low | 2.571 | Nested |

