# Winner Feature Analysis (Agent A)

## Headline (E6: semantic_ir vs test_only)

| Outcome | Count |
|---------|------:|
| semantic_ir wins | 14 |
| test_only wins | 4 |
| ties | 102 |
| mean ?? Conf (all tasks) | 7.743 pp |

## By overlap density tier

| Tier | n | wins | losses | ties | mean ?? (pp) |
|------|--:|-----:|-------:|-----:|------------:|
| high | 38 | 4 | 0 | 34 | 9.211 |
| medium | 34 | 3 | 3 | 28 | 2.206 |
| low | 48 | 7 | 1 | 40 | 10.503 |

## Feature means: IR-win vs test_only-win tasks

```json
{
  "overlap_rate": {
    "win_mean": 1.1963,
    "loss_mean": 1.2083,
    "tie_mean": 1.2461
  },
  "n_guard_atoms": {
    "win_mean": 17.7857,
    "loss_mean": 18.25,
    "tie_mean": 17.8137
  },
  "n_and_ops": {
    "win_mean": 10.7857,
    "loss_mean": 11.25,
    "tie_mean": 10.8137
  },
  "n_rel_ops": {
    "win_mean": 17.7857,
    "loss_mean": 18.25,
    "tie_mean": 17.8137
  },
  "mean_atoms_per_guard": {
    "win_mean": 2.5408,
    "loss_mean": 2.6071,
    "tie_mean": 2.5448
  },
  "max_atoms_per_guard": {
    "win_mean": 3.0,
    "loss_mean": 3.0,
    "tie_mean": 3.0
  },
  "prompt_spec_len": {
    "win_mean": 680.0,
    "loss_mean": 684.25,
    "tie_mean": 680.3725
  },
  "n_outputs": {
    "win_mean": 3.0,
    "loss_mean": 3.0,
    "tie_mean": 3.0
  },
  "n_inputs": {
    "win_mean": 5.0,
    "loss_mean": 5.0,
    "tie_mean": 5.0
  }
}
```

## Point-biserial correlations (decisive tasks only)

```json
[
  {
    "feature": "n_guard_atoms",
    "n": 18,
    "corr": -0.3407
  },
  {
    "feature": "n_and_ops",
    "n": 18,
    "corr": -0.3407
  },
  {
    "feature": "n_rel_ops",
    "n": 18,
    "corr": -0.3407
  },
  {
    "feature": "mean_atoms_per_guard",
    "n": 18,
    "corr": -0.3407
  },
  {
    "feature": "prompt_spec_len",
    "n": 18,
    "corr": -0.2934
  },
  {
    "feature": "overlap_rate",
    "n": 18,
    "corr": -0.0347
  }
]
```

## Logistic probe (interpretable, small-n)

```json
{
  "features": [
    "overlap_rate",
    "n_guard_atoms",
    "n_and_ops",
    "prompt_spec_len",
    "n_outputs"
  ],
  "cv_accuracy_mean": 0.7333,
  "cv_accuracy_std": 0.1616,
  "coefs": {
    "overlap_rate": -0.4523,
    "n_guard_atoms": -0.3924,
    "n_and_ops": -0.3924,
    "prompt_spec_len": -0.194,
    "n_outputs": 0.0
  },
  "n_decisive": 18,
  "n_wins": 14
}
```

## Reviewer-facing takeaway

Typed Semantic Feedback IR gains are **concentrated**, not uniform:
- Most tasks are **ties**; the +7.7 pp mean is driven by a **small win set** (14 tasks).
- Compare tier mean ?? and win counts above to see whether high-overlap / atom-dense specs
  disproportionately host IR wins (this is the pre-hoc deployment signal Agent F consumes).

## Files

- `task_feature_db.csv` / `.json`
- `winner_by_tier.csv`
- `e6_win_tasks.json`
- `feature_win_correlations.json`
