# Real-Priority Micro-Benchmark (`real_priority_micro_v1`)

External-validity micro-benchmark of **30** ordered first-match FSF tasks
(firewall / ACL / billing / role-gate / tax + industrial / GitHub / HKCA09 /
published-industrial slices). **Not** produced by `HardTaskGenerator`.

## Build

```powershell
python -c "from src.benchmarks.real_priority_micro import export_and_validate; export_and_validate(target_n=30)"
```

## Equal-K eval

```powershell
python -u experiments/run_all.py `
  --modes B1 B2 M_eq --repeats 1 `
  --benchmark-path benchmarks/real_priority_micro_v1.json `
  --run-name run_real_priority_micro_v1 `
  --parallelism 4 --force-max-attempts 3 `
  --model ecnu-plus --seed 42
```

Summarize:

```powershell
python paper/hsp-agile/scripts/summarize_real_priority_micro.py
```

## SMT domain ablation

```powershell
python -u scripts/run_smt_scalability_ablation.py `
  --benchmark-path benchmarks/real_priority_micro_v1.json --repeats 3
python -u scripts/run_smt_stress_probe.py
python -u scripts/plot_smt_domain_latency.py
```

Artifacts: `paper/hsp-agile/artifacts/smt_scalability_v1/`,
`paper/hsp-agile/figures/smt_domain_latency.pdf`.
