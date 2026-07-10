# Phase 2 experiment runner (requires LLM API access)
# Usage: .\paper\hsp-agile\scripts\run_phase2_experiments.ps1 [-Quick]

param(
    [switch]$Quick,
    [int]$Parallelism = 10
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
Set-Location $Root

Write-Host "=== BENCH-sync (120 tasks) ==="
python scripts/sync_benchmark_120.py

if ($Quick) {
    $taskLimitArgs = @("--task-limit", "5")
    $repeats = 1
} else {
    $taskLimitArgs = @()
    $repeats = 3
}

Write-Host "=== E8c-fix (HumanEval/MBPP B1 B2 M) ==="
python -u experiments/run_real_derived.py --run-name run_e8c_full_v2 --modes B1 B2 M --parallelism $Parallelism

Write-Host "=== E1 canonical (120 x B0 B1 B2 M A1-A3) ==="
python -u experiments/run_all.py --modes B0 B1 B2 M A1 A2 A3 --repeats 1 --run-name run_e1_canonical_v1 --parallelism $Parallelism @taskLimitArgs

Write-Host "=== E12 canonical (120 x $repeats x B1 B2 M) ==="
python -u experiments/run_all.py --modes B1 B2 M --repeats $repeats --run-name run_e12_canonical_v1 --parallelism $Parallelism @taskLimitArgs
if ($LASTEXITCODE -ne 0) { throw "E12-canonical failed with exit code $LASTEXITCODE" }

Write-Host "=== B6-align full corpus ==="
python -u experiments/run_all.py --modes B6 B2 M --repeats 1 --run-name run_b6_full_v2 --parallelism $Parallelism @taskLimitArgs
if ($LASTEXITCODE -ne 0) { throw "B6-align failed with exit code $LASTEXITCODE" }

Write-Host "=== E10+ completion ==="
python -u experiments/run_all.py --modes B1 B2 M --repeats 1 --benchmark-path benchmarks/random_tasks_annotated.json --run-name run_e10_random_v2 --parallelism $Parallelism @taskLimitArgs
if ($LASTEXITCODE -ne 0) { throw "E10+ failed with exit code $LASTEXITCODE" }

Write-Host "=== E16 second model pilot (30 stratified) ==="
if ($Quick) {
    Write-Host "(skipped in -Quick; ecnu-thinking requires separate API entitlement)"
} else {
    python -u experiments/run_all.py --modes B1 B2 M --repeats 1 --task-subset benchmarks/e12_stratified_30.json --model ecnu-max --run-name run_e16_model_pilot_v1 --parallelism $Parallelism
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "E16 skipped or failed (exit $LASTEXITCODE); continuing without second-model pilot."
    }
}

Write-Host "=== E14 length-matched sweep ==="
if ($Quick) {
    python -u experiments/run_e14_sweep.py --run-name run_e14_sweep_v1 --task-limit 5
} else {
    python -u experiments/run_e14_sweep.py --run-name run_e14_sweep_v1
}

Write-Host "=== E17 M_adv advisory pattern guard ==="
python -u experiments/run_all.py --modes M_adv A2 M --repeats 1 --run-name run_e17_advisory_v1 --parallelism $Parallelism @taskLimitArgs
if ($LASTEXITCODE -ne 0) { throw "E17 failed with exit code $LASTEXITCODE" }

Write-Host "=== Refresh paper assets ==="
python paper/hsp-agile/scripts/refresh_paper_assets.py --run-dir artifacts/run_e1_canonical_v1
python paper/hsp-agile/scripts/update_stats_table.py

Write-Host "Phase 2 experiments complete."
