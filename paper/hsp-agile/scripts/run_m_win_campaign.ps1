# M-win campaign: re-run E1 / E12 / E10 under the strengthened mode-M pipeline
# (best-effort selection + E14-informed feedback), then refresh paper assets.
#
# Usage (from repo root):
#   .\paper\hsp-agile\scripts\run_m_win_campaign.ps1
#   .\paper\hsp-agile\scripts\run_m_win_campaign.ps1 -Quick          # task-limit 5, E12 repeats=1
#   .\paper\hsp-agile\scripts\run_m_win_campaign.ps1 -Parallelism 8
#   .\paper\hsp-agile\scripts\run_m_win_campaign.ps1 -SkipE10        # skip random-benchmark E10
#   .\paper\hsp-agile\scripts\run_m_win_campaign.ps1 -SkipRefresh    # skip refresh_paper_assets.py
#
# Run names (authoritative placeholders until results land):
#   E1  -> artifacts/run_e1_m_win_v1
#   E12 -> artifacts/run_e12_m_win_v1
#   E10 -> artifacts/run_e10_m_win_v1
#
# Requires LLM API access (same as run_phase2_experiments.ps1).
# See artifacts/AUTHORITATIVE_NUMBERS.md for which run ids to cite.

param(
    [switch]$Quick,
    [switch]$SkipE10,
    [switch]$SkipRefresh,
    [int]$Parallelism = 10
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
Set-Location $Root

$RefreshScript = Join-Path $PSScriptRoot "refresh_paper_assets.py"
$RandomBench = Join-Path $Root "benchmarks\random_tasks_annotated.json"

if ($Quick) {
    $taskLimitArgs = @("--task-limit", "5")
    $e12Repeats = 1
} else {
    $taskLimitArgs = @()
    $e12Repeats = 3
}

Write-Host "=== E1 M-win (B0 B1 B2 M A1 A2 A3, repeats=1) ==="
python -u experiments/run_all.py `
    --modes B0 B1 B2 M A1 A2 A3 `
    --repeats 1 `
    --run-name run_e1_m_win_v1 `
    --parallelism $Parallelism `
    @taskLimitArgs
if ($LASTEXITCODE -ne 0) { throw "E1 M-win failed with exit code $LASTEXITCODE" }

Write-Host "=== E12 M-win (B1 B2 M, repeats=$e12Repeats) ==="
python -u experiments/run_all.py `
    --modes B1 B2 M `
    --repeats $e12Repeats `
    --run-name run_e12_m_win_v1 `
    --parallelism $Parallelism `
    @taskLimitArgs
if ($LASTEXITCODE -ne 0) { throw "E12 M-win failed with exit code $LASTEXITCODE" }

if (-not $SkipE10) {
    if (Test-Path $RandomBench) {
        Write-Host "=== E10 M-win (random benchmark B1 B2 M) ==="
        python -u experiments/run_all.py `
            --modes B1 B2 M `
            --repeats 1 `
            --benchmark-path benchmarks/random_tasks_annotated.json `
            --run-name run_e10_m_win_v1 `
            --parallelism $Parallelism `
            @taskLimitArgs
        if ($LASTEXITCODE -ne 0) { throw "E10 M-win failed with exit code $LASTEXITCODE" }
    } else {
        Write-Warning "E10 skipped: missing $RandomBench"
    }
} else {
    Write-Host "=== E10 skipped (-SkipE10) ==="
}

if (-not $SkipRefresh) {
    if (Test-Path $RefreshScript) {
        Write-Host "=== Refresh paper assets (pointing at run_e1_m_win_v1) ==="
        python $RefreshScript --run-dir artifacts/run_e1_m_win_v1
        if ($LASTEXITCODE -ne 0) { throw "refresh_paper_assets failed with exit code $LASTEXITCODE" }
    } else {
        Write-Warning "refresh_paper_assets.py not found at $RefreshScript; skipping."
    }
} else {
    Write-Host "=== Refresh skipped (-SkipRefresh) ==="
}

Write-Host "M-win campaign complete."
Write-Host "  E1:  artifacts/run_e1_m_win_v1"
Write-Host "  E12: artifacts/run_e12_m_win_v1"
if (-not $SkipE10 -and (Test-Path $RandomBench)) {
    Write-Host "  E10: artifacts/run_e10_m_win_v1"
}
