<#
.SYNOPSIS
    Unified paper build script for HSP-Agile / Acceptance Safety.
    Single entry point for all documents produced by this project.

.PARAMETER Which
    What to build: "long" (default)  — long report with refresh + figures + tectonic
                   "conf"           — conference cut (IEEEtran, 10-page)
                   "all"            — both long + conf
.PARAMETER SkipRefresh
    Skip data refresh and figure regeneration (compile only). Default: $false.
.PARAMETER Clean
    Clean long-report build directory before compiling.
.PARAMETER Formats
    Figure output formats (default: "png,pdf").
.PARAMETER Dpi
    Figure DPI (default: 200).
.PARAMETER Seed
    Random seed for figures (default: 7).

.EXAMPLE
    powershell -File scripts/build.ps1 -Which all
    powershell -File scripts/build.ps1 -Which conf
    powershell -File scripts/build.ps1 -Which long -Clean
    powershell -File scripts/build.ps1 -Which long -SkipRefresh
#>
param(
    [ValidateSet("long", "conf", "all")]
    [string]$Which = "long",
    [switch]$SkipRefresh = $false,
    [switch]$Clean = $false,
    [string]$Formats = "png,pdf",
    [int]$Dpi = 200,
    [int]$Seed = 7
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
$LongRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$ConfRoot = Resolve-Path (Join-Path $LongRoot "..\hsp-agile-conference")
$TectonicExe = Join-Path $RepoRoot "tools\tectonic\tectonic.exe"

if (!(Test-Path $TectonicExe)) {
    throw "Tectonic not found at $TectonicExe. Run tools\install_tectonic.ps1 first."
}

function Invoke-LongBuild {
    param()

    $BuildDir = Join-Path $LongRoot "build"
    New-Item -ItemType Directory -Force -Path $BuildDir | Out-Null
    if ($Clean) {
        Remove-Item "$BuildDir\*" -Recurse -Force -ErrorAction SilentlyContinue
    }

    if (-not $SkipRefresh) {
        Write-Host "[1/3] Refreshing paper data assets..."

        $RefreshScript = Join-Path $LongRoot "scripts\refresh_paper_assets.py"
        if (Test-Path $RefreshScript) {
            $formatArgs = @()
            foreach ($f in $Formats.Split(",")) {
                $trim = $f.Trim()
                if ($trim) { $formatArgs += $trim }
            }
            $ra = @($RefreshScript, "--static-formats") + $formatArgs + @("--dpi", "$Dpi", "--seed", "$Seed")
            & python @ra
            if ($LASTEXITCODE -ne 0) { throw "refresh_paper_assets failed" }
        }

        Write-Host "[2/3] Running figure generation..."
        $FigScript = Join-Path $LongRoot "figures\scripts\plot_mpl_figures.py"
        if (Test-Path $FigScript) {
            & python $FigScript --formats pdf png --dpi $Dpi
            if ($LASTEXITCODE -ne 0) { throw "plot_mpl_figures failed" }
        }
        $PumlScript = Join-Path $LongRoot "scripts\render_puml.py"
        if (Test-Path $PumlScript) {
            & python $PumlScript
            if ($LASTEXITCODE -ne 0) { throw "render_puml failed" }
        }
    }

    Write-Host "[3/3] Compiling long-report LaTeX..."
    Push-Location $LongRoot
    try {
        & $TectonicExe --keep-logs --synctex --outdir $BuildDir "main.tex"
        if ($LASTEXITCODE -ne 0) { throw "Tectonic long-report compilation failed" }
    }
    finally {
        Pop-Location
    }

    # Sync a copy to the paper root for convenience
    Copy-Item (Join-Path $BuildDir "main.pdf") (Join-Path $LongRoot "main.pdf") -Force
    Write-Host "Long-report PDF: $(Join-Path $BuildDir 'main.pdf')"
}

function Invoke-ConfBuild {
    Write-Host "Compiling conference-cut LaTeX..."
    Push-Location $ConfRoot
    try {
        # conference uses ../hsp-agile/bib/references.bib directly
        & $TectonicExe --keep-logs --synctex "main.tex"
        if ($LASTEXITCODE -ne 0) { throw "Tectonic conference compilation failed" }
    }
    finally {
        Pop-Location
    }
    $pdf = Join-Path $ConfRoot "main.pdf"
    if (Test-Path $pdf) {
        try { python -c "from pypdf import PdfReader; print('Conference pages:', len(PdfReader(r'$pdf').pages))" }
        catch { Write-Host "(page count not available: install pypdf)" }
    }
    Write-Host "Conference PDF: $pdf"
}

# ── Dispatch ───────────────────────────────────────────────────────────────────

switch ($Which) {
    "long" { Invoke-LongBuild }
    "conf" { Invoke-ConfBuild }
    "all"  {
        Invoke-LongBuild
        Invoke-ConfBuild
        Write-Host "`nBoth builds completed."
    }
}