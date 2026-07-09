# E11a: Manual held-out from vendor Agile-SOFL examples
#
# Prerequisites:
#   git submodule update --init vendor/agile-sofl-toolchain
#   (or clone agile-sofl-toolchain into vendor/)
#
# This script exports manual tasks excluding E1 hard IDs, then runs B1/B2/M.

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")

Push-Location $RepoRoot
try {
    $vendorExamples = Join-Path $RepoRoot "vendor\agile-sofl-toolchain\examples"
    if (-not (Test-Path $vendorExamples)) {
        Write-Host "SKIP: vendor examples not found at $vendorExamples"
        Write-Host "Mitigation: E11 external corpus (benchmarks/external_sofl.json) is already evaluated."
        Write-Host "To build manual export from vendor when available:"
        Write-Host "  python scripts/build_benchmark.py --export-manual-heldout benchmarks/manual_heldout.json"
        exit 0
    }

    Write-Host "[1/2] Building manual held-out benchmark..."
    python scripts/build_e11_benchmarks.py --manual-only

    Write-Host "[2/2] Running E11a manual held-out (B1, B2, M)..."
    python -u experiments/run_all.py `
        --modes B1 B2 M `
        --repeats 1 `
        --benchmark-path benchmarks/manual_heldout.json `
        --run-name run_e11_manual_v1 `
        --parallelism 8

    Write-Host "Done. Results: artifacts/run_e11_manual_v1/results.jsonl"
}
finally {
    Pop-Location
}
