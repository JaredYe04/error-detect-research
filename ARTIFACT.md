# SgDP / HSP-Agile Artifact Guide

This repository ships a reproducibility package for the **Specification-guided Defect Prevention Framework (SgDP)** and its **HSP-Agile** instantiation (SOFL/FSF).

## Quick reproduce (offline smoke)

```bash
# Linux / macOS / WSL / Git Bash
bash scripts/reproduce.sh

# Windows PowerShell
powershell -File scripts/reproduce.ps1
```

```bash
# Docker (isolated environment)
docker compose build
docker compose run --rm sgdp
```

The smoke path runs:

1. Unit tests (`test_spec_ir`, `test_feedback_ir`, `test_schema_validate`)
2. Paper metric aggregation from `artifacts/run_feedback_v2/` when present
3. Matplotlib figure regeneration under `paper/hsp-agile/figures/`

## Full experiment replication

Requires an OpenAI-compatible API key in `.env`:

```bash
pip install -e .
python experiments/run_all.py --quick          # smoke: B0,B1,M × 1 repeat
python experiments/run_sweep.py --experiment feedback_variants --run-name run_feedback_v2
python paper/hsp-agile/scripts/prepare_mechanism_data.py --feedback-dir artifacts/run_feedback_v2/feedback_variants
cd paper/hsp-agile && powershell -File scripts/build.ps1 -Which long -SkipRefresh
```

## ASE / SANER artifact checklist (self-check)

| Criterion | Status | Location |
|-----------|--------|----------|
| **Available** | Yes | Public git repository |
| **Functional** | Yes | `scripts/reproduce.sh` / `.ps1` |
| **Reusable** | Yes | `Dockerfile`, `docker-compose.yml` |
| **Documented** | Yes | This file, `README.md`, Appendix A |
| **Schemas** | Yes | `schemas/spec_ir.schema.json`, `schemas/semantic_feedback.schema.json` |
| **Tests** | Yes | `tests/test_spec_ir.py`, `test_feedback_ir.py`, `test_schema_validate.py` |
| **Raw logs** | Partial | `artifacts/run_feedback_v2/` (E6); main E1 run bundled separately |
| **Paper build** | Yes | `paper/hsp-agile/scripts/build.ps1 -Which all` |

## Key paths

| Path | Purpose |
|------|---------|
| `src/ir/spec_ir.py` | SpecIR datamodel |
| `src/adapters/` | Notation adapters (SOFL, Mini-Z, StateMachine) |
| `src/pipeline/runner.py` | Pipeline + Semantic Feedback IR |
| `paper/hsp-agile/data/processed/` | Aggregated CSV/JSON for figures |
| `paper/hsp-agile/build/main.pdf` | Compiled report |

## Citation

See `CITATION.cff` for metadata. BibTeX entry in `paper/hsp-agile/bib/references.bib` (thesis sources).

## License

MIT — see `LICENSE`.
