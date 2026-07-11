# HANDOFF — Provide GitHub auth, then we run live harvest + eval

## Why

Published desensitized pilot (n=28) is not enough for external validity.
Wave-3 framework is ready to pull **public** GitHub specs and evaluate them.

## What you do (1 minute)

In **your** PowerShell (same machine / same user as the agent terminal):

```powershell
# Option A (preferred for non-interactive scripts)
$env:GH_TOKEN = "ghp_YOUR_CLASSIC_PAT"
# scopes: public_repo   OR fine-grained: Contents=Read on public repositories

# Option B
gh auth login
```

Then reply in chat: **「token 已设置」** (do not paste the secret).

Optional check yourself:

```powershell
cd d:\repos\error-detect-research
python scripts/harvest_github_wave3.py --dry-run-auth
# expect: "ok": true
```

## What I will run after that

```powershell
powershell -File scripts/run_github_harvest_eval.ps1 -MaxDownloads 100 -Model ecnu-plus
```

This will:
1. Search GitHub (SOFL/ASFL, decision tables, FSM, interlocking, alarms, …)
2. Download candidates → classify → convert → Z3 validate
3. Write `benchmarks/github_harvest_v1.json`
4. Merge into RealSpec
5. Run B1/B2/M_eq eval → `artifacts/run_github_harvest_v1`

## Already in place

| Piece | Path |
|-------|------|
| Auth | `src/harvest/auth.py` |
| Queries | `src/harvest/queries.py` |
| Live harvest | `scripts/harvest_github_wave3.py` |
| One-shot eval | `scripts/run_github_harvest_eval.ps1` |
| Manual seed fallback | `scripts/ingest_manual_harvest_seeds.py` |
| Docs | `benchmarks/GITHUB_HARVEST_README.md` |

Auth dry-run **currently fails** on this machine (expected until you set the token).
