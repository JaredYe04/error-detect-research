# Hard-Benchmark Experiment Scheme (v2)

## Goal
- Increase discrimination across `B1/B2/M/A1/A2/A3`.
- Run full prevention evaluation with both `spec_confusion` and `impl_screening`.
- Produce paper-ready artifacts (stats + high-information figures + PDF).

## Dataset Design
- Base tasks: extracted from Agile-SOFL examples.
- Hard tasks: synthetic precedence-sensitive FSF tasks with multi-output constraints.
- Current size:
  - total tasks: 213
  - hard tasks: 180

## Main Experimental Matrix
- Modes: `B0 B1 B2 M A1 A2 A3`
- Repeats: `1` (expand to `>=3` for final camera-ready stats)
- Run command:

```bash
python experiments/run_all.py --modes B0 B1 B2 M A1 A2 A3 --repeats 1 --run-name run_hard_full_v2
```

## Why This Should Differentiate Better
- `strict_formal_conformance` uses larger case budgets than pass/fail-only checks.
- `strict_failures` counts hidden regressions even when coarse `formal=1.00`.
- Hard tasks enforce ordered conditions and multi-output coupling.
- `M` uses full acceptance rule; ablations remove one component each.

## Full Prevention Evaluation

```bash
python experiments/run_prevention.py --modes B1 B2 M A1 A2 A3 --run-name prevention_full_v1
```

Notes:
- Resume-safe by default (`--run-name` directory reused).
- Evaluates both:
  - `spec_confusion`
  - `impl_screening`

## Analysis + Paper Pipeline

```bash
python experiments/analyze.py artifacts/run_hard_full_v2
python paper/hsp-agile/scripts/prepare_paper_data.py
python paper/hsp-agile/figures/scripts/plot_paper_figures.py --static-formats png pdf --dpi 300 --seed 7
python paper/hsp-agile/scripts/update_stats_table.py
powershell -ExecutionPolicy Bypass -File paper/hsp-agile/scripts/build_pdf.ps1
```

## Success Criteria
- Strict metrics show clear mode separation.
- At least one main comparison and one ablation effect reaches statistical significance.
- Prevention heatmap and Pareto figure support narrative (quality/latency tradeoff).
