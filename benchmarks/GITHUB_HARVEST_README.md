# GitHub Live Harvest Framework (Wave-3)

This pipeline finds **public** ordered-guard / decision-table / FSM / SOFL-like
artefacts on GitHub, converts what it can into FSF tasks, validates with Z3,
merges into RealSpec, and runs B1/B2/M_eq.

> Honesty: auto-conversion only keeps tasks that pass witness + reference
> checks. Many search hits will be skipped (logged). That is expected.

## What you provide

One of:

```powershell
# Option A — classic PAT (recommended for scripts)
$env:GH_TOKEN = "ghp_xxxxxxxx"   # scopes: public_repo  OR fine-grained Contents:Read on public repos

# Option B — GitHub CLI
gh auth login
```

Then tell the agent the token is set (do **not** paste the token into chat if
avoidable — set it in the terminal / user env).

## One-shot

```powershell
powershell -File scripts/run_github_harvest_eval.ps1 -MaxDownloads 100 -Model ecnu-plus
```

Auth-only check:

```powershell
python scripts/harvest_github_wave3.py --dry-run-auth
```

## Pipeline stages

| Stage | Script / path |
|-------|----------------|
| Auth | `src/harvest/auth.py` |
| Queries | `src/harvest/queries.py` |
| Search + download | `scripts/harvest_github_wave3.py --live` |
| Classify + convert | `src/harvest/classify.py`, `src/harvest/to_fsf.py` |
| Re-validate / export | `scripts/build_github_harvest_corpus.py` |
| Eval | `experiments/run_all.py` on `benchmarks/github_harvest_v1.json` |
| Artifacts | `artifacts/github_harvest/<run>/` |

## Outputs

- `benchmarks/github_harvest_v1.json` — validated FSF tasks
- `artifacts/github_harvest/<run>/SUMMARY.md`
- `artifacts/run_github_harvest_v1/` — LLM eval (after full script)

## If conversion yield is low

1. Open `06_skipped.jsonl` / `04_classified.jsonl`
2. Prioritize `02b_repo_hits.json` high-star repos for manual schema shaping
3. Drop schema-shaped JSON decision tables into `artifacts/github_harvest/manual_seed/` (future hook)
4. Vendor `.asfl` still goes under `vendor/agile-sofl-toolchain/examples/`

## Relation to published pilot

| Corpus | n (approx) | Role |
|--------|------------|------|
| `published_industrial_pilot.json` | 28 | Desensitized literature reconstructions |
| `industrial_sofl.json` | 31 | Practitioner-pattern (not vendor) |
| `github_harvest_v1.json` | 48 | Public GitHub `.asfl` convertible specs |
| `hkca09_sofl_fsf.json` | **35** | HKCA09 SOFL→FSF reconstructions (overlap-rich) |
| RealSpec merge | **203** | All of the above + textbook + real_derived |

HKCA09 expansion + hard-seed C2: see
`paper/hsp-agile/artifacts/strengthening_sprint/agent_d_industrial/HKCA09_FSF_EXPANSION.md`.
