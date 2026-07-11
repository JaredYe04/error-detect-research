# GitHub Live Harvest → RealSpec Eval (Wave-3)
# Requires: GH_TOKEN or `gh auth login`
#
# Usage:
#   powershell -File scripts/run_github_harvest_eval.ps1
#   powershell -File scripts/run_github_harvest_eval.ps1 -MaxDownloads 100 -Model ecnu-plus

param(
    [int]$MaxDownloads = 80,
    [int]$PerQuery = 15,
    [string]$Model = "ecnu-plus",
    [string]$RunName = "run_github_harvest_v1",
    [switch]$SkipEval
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host "== 0) Auth check ==" -ForegroundColor Cyan
python scripts/harvest_github_wave3.py --dry-run-auth
if ($LASTEXITCODE -ne 0) {
    Write-Host @"

GitHub auth missing. Do ONE of:
  A) `$env:GH_TOKEN = 'ghp_...'`   # classic PAT with public repo read
  B) gh auth login

Then re-run this script.
"@ -ForegroundColor Yellow
    exit 2
}

Write-Host "== 1) Live harvest ==" -ForegroundColor Cyan
python scripts/harvest_github_wave3.py --live --max-downloads $MaxDownloads --per-query $PerQuery
$harvestExit = $LASTEXITCODE

Write-Host "== 2) Build / re-validate corpus ==" -ForegroundColor Cyan
# Pick latest wave3 run
$latest = Get-ChildItem artifacts/github_harvest -Directory -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
if (-not $latest) {
    Write-Host "No harvest run directory found." -ForegroundColor Red
    exit 1
}
python scripts/build_github_harvest_corpus.py --from-run $latest.Name --rebuild-realspec

$bench = "benchmarks/github_harvest_v1.json"
if (-not (Test-Path $bench)) {
    Write-Host "No convertible tasks yet. Inspect $($latest.FullName)\06_skipped.jsonl" -ForegroundColor Yellow
    exit 1
}
$n = (Get-Content $bench -Raw | ConvertFrom-Json).Count
Write-Host "Corpus size: $n tasks" -ForegroundColor Green
if ($n -lt 1) { exit 1 }

if ($SkipEval) {
    Write-Host "SkipEval set; stopping before LLM run." -ForegroundColor Yellow
    exit $harvestExit
}

Write-Host "== 3) Eval B1/B2/M_eq ==" -ForegroundColor Cyan
python -u experiments/run_all.py `
    --modes B1 B2 M_eq `
    --repeats 1 `
    --benchmark-path $bench `
    --run-name $RunName `
    --parallelism 4 `
    --force-max-attempts 3 `
    --model $Model `
    --seed 42

Write-Host "Done. Results: artifacts/$RunName" -ForegroundColor Green
