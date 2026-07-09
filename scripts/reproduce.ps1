# Offline reproducibility smoke test for SgDP / HSP-Agile artifact.
$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

Write-Host "==> [1/3] Unit tests (SpecIR, Feedback IR, schema validation)"
python -m pytest tests/test_spec_ir.py tests/test_feedback_ir.py tests/test_schema_validate.py -q
if ($LASTEXITCODE -ne 0) { throw "pytest failed" }

Write-Host "==> [2/3] Paper metrics (uses bundled artifacts when available)"
$FeedbackDir = Join-Path $Root "artifacts\run_feedback_v2\feedback_variants"
if (Test-Path $FeedbackDir) {
    python paper/hsp-agile/scripts/prepare_mechanism_data.py --feedback-dir $FeedbackDir
    if ($LASTEXITCODE -ne 0) { throw "prepare_mechanism_data failed" }
} else {
    Write-Host "    (skip prepare_mechanism_data: $FeedbackDir not found)"
}

Write-Host "==> [3/3] Regenerate matplotlib figures"
python paper/hsp-agile/figures/scripts/plot_mpl_figures.py
if ($LASTEXITCODE -ne 0) { throw "plot_mpl_figures failed" }

Write-Host "==> Reproduce smoke complete."
Write-Host "    Full LLM experiments: python experiments/run_all.py --quick"
Write-Host "    E6 feedback variants: python experiments/run_sweep.py --experiment feedback_variants --task-limit 3"
