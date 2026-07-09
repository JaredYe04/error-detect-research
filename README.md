# Specification-guided Defect Prevention (SgDP) / HSP-Agile

Research artifact for the **Specification-guided Defect Prevention Framework (SgDP)** with **HSP-Agile** as the primary SOFL/FSF instantiation. The pipeline combines a canonical **SpecIR** layer, Z3 witness generation, **Semantic Feedback IR** repair, and pattern-guard screening under a conjunctive acceptance predicate.

```
Text_L → Adapter → SpecIR → Witness (Z3) → LLM → Verifier → Accept
                              ↑__________________|  Semantic Feedback IR
```

See `paper/hsp-agile/build/main.pdf` for the full report and `ARTIFACT.md` for the reproducibility checklist.

## Reproduce (offline smoke)

```bash
pip install -e .
bash scripts/reproduce.sh              # Linux/macOS/WSL
# powershell -File scripts/reproduce.ps1   # Windows

# Docker
docker compose build && docker compose run --rm sgdp
```

## Quick Start (full experiments)

```bash
# 1. Install
pip install -e .
cd vendor/agile-sofl-toolchain && npm install && npm run build:parser && cd ../..

# 2. Configure API key in .env (ECNU OpenAI-compatible)
# ECNU_API_KEY=sk-...

# 3. Build benchmark from example specs
python scripts/build_benchmark.py

# 4. Run unit tests
python -m pytest tests/ -q

# 5. Run experiments
python experiments/run_all.py --quick          # smoke: B0,B1,M × 1 repeat
python experiments/run_all.py --repeats 2      # full matrix
python experiments/run_all.py --sensitivity    # temperature grid

# 6. Analyze results
python experiments/analyze.py artifacts/run_YYYYMMDD_HHMMSS
```

## Experiment Modes

| Mode | Description |
|------|-------------|
| B0 | Reference implementation (FSF-compiled ground truth) |
| B1 | LLM one-shot + no formal/pattern |
| B2 | LLM + FSF unit-test feedback loop |
| M | Full pipeline: LLM + formal + patterns + repair |
| A1 | Ablation: no formal check |
| A2 | Ablation: no pattern guard |
| A3 | Ablation: no repair loop |

## Key Metrics

- **success_rate** — passes formal conformance + pattern guard
- **formal_conformance** — FSF scenario pass ratio
- **mutation_kill_rate** — detects injected spec/impl faults
- **verify@k** — success within k LLM attempts

## Project Layout

```
src/
  ir/                 # SpecIR, FSF lowerer, schema validation
  adapters/           # SOFL, Mini-Z, Mini-StateMachine adapters
  asfl_bridge.py      # Node parser bridge
  llm/                # ECNU API adapter
  formal/             # FSF evaluator + Z3 case generation
  patterns/           # Error pattern DSL (rules.yaml)
  mutation/           # Spec/impl mutation operators
  pipeline/           # Integrated runner + Semantic Feedback IR
  repair/             # FeedbackRenderer / feedback_ir
  benchmarks/         # Task suite + reference generator
schemas/              # spec_ir.schema.json, semantic_feedback.schema.json
paper/hsp-agile/      # CCF-B report sources, figures, build scripts
experiments/
  run_all.py          # Batch experiment runner
  analyze.py          # Wilcoxon tests, ablation, plots
benchmarks/tasks.json # Generated task suite
artifacts/            # Raw results & analysis
vendor/agile-sofl-toolchain/  # Upstream parser/editor
```

## Academic Alignment

- SOFL fault prevention: Li & Liu, QRS 2022 / IET Software 2023
- LLM + formal verification: verify@k (TOSEM 2024, DafnyBench)
- Specification mutation: NIST / Circus mutation testing

## API

Uses ECNU campus LLM API (`ecnu-plus` recommended): https://developer.ecnu.edu.cn/vitepress/llm/model.html
