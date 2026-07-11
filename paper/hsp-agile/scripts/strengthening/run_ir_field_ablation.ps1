# Smoke + full IR field ablation launcher (Agent B)
param(
  [ValidateSet("smoke", "full")]
  [string]$Mode = "smoke",
  [int]$Parallelism = 6,
  [string]$Model = ""
)

$ErrorActionPreference = "Stop"
Set-Location (Resolve-Path "$PSScriptRoot\..\..\..\..")

if ($Mode -eq "smoke") {
  $runName = "run_ir_field_ablation_smoke"
  $limit = 5
} else {
  $runName = "run_ir_field_ablation_v1"
  $limit = $null
}

$args = @(
  "experiments/run_sweep.py",
  "--experiment", "ir_field_ablation",
  "--run-name", $runName,
  "--parallelism", "$Parallelism"
)
if ($limit) { $args += @("--task-limit", "$limit") }
if ($Model) { $args += @("--model", $Model) }

Write-Host "Launching: python $($args -join ' ')"
python @args

python paper/hsp-agile/scripts/strengthening/analyze_ir_field_ablation.py `
  --results "artifacts/$runName/ir_field_ablation/results.jsonl"
