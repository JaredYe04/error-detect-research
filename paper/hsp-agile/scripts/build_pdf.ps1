Param(
    [switch]$SkipRefresh = $false,
    [string]$Formats = "png,pdf",
    [int]$Dpi = 300,
    [int]$Seed = 7,
    [string]$RunDir = "",
    [string]$PreventionSummary = ""
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
$PaperRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$TectonicExe = Join-Path $RepoRoot "tools\tectonic\tectonic.exe"

if (!(Test-Path $TectonicExe)) {
    throw "Tectonic not found at $TectonicExe. Install it first."
}

if (-not $SkipRefresh) {
    Write-Host "[1/3] Refreshing paper data and figures..."
    $formatArgs = @()
    foreach ($f in $Formats.Split(",")) {
        $trim = $f.Trim()
        if ($trim) { $formatArgs += $trim }
    }
    $refreshArgs = @((Join-Path $PaperRoot "scripts\refresh_paper_assets.py"), "--static-formats")
    $refreshArgs += $formatArgs
    $refreshArgs += @("--dpi", "$Dpi", "--seed", "$Seed")
    if ($RunDir) {
        $refreshArgs += @("--run-dir", $RunDir)
    }
    if ($PreventionSummary) {
        $refreshArgs += @("--prevention-summary", $PreventionSummary)
    }
    & python @refreshArgs
    if ($LASTEXITCODE -ne 0) { throw "refresh_paper_assets failed" }
}

$buildDir = Join-Path $PaperRoot "build"
New-Item -ItemType Directory -Force -Path $buildDir | Out-Null

Write-Host "[2/3] Compiling LaTeX with Tectonic..."
Push-Location $PaperRoot
try {
    & $TectonicExe --keep-logs --synctex --outdir $buildDir "main.tex"
    if ($LASTEXITCODE -ne 0) { throw "Tectonic compilation failed" }
}
finally {
    Pop-Location
}

$pdf = Join-Path $buildDir "main.pdf"
if (!(Test-Path $pdf)) {
    throw "Build succeeded but PDF not found: $pdf"
}

Write-Host "[3/3] PDF generated: $pdf"
