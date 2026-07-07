Param([switch]$Clean)
$TectonicExe = Resolve-Path "d:\repos\error-detect-research\tools\tectonic\tectonic.exe"
$PaperRoot = $PSScriptRoot | Split-Path -Parent
$BuildDir = Join-Path $PaperRoot "build"
New-Item -ItemType Directory -Force -Path $BuildDir | Out-Null
if ($Clean) { Remove-Item "$BuildDir\*" -Recurse -Force -ErrorAction SilentlyContinue }

Write-Host "[1/3] Refreshing paper data assets..."
$RefreshScript = Join-Path $PaperRoot "scripts\refresh_paper_assets.py"
if (Test-Path $RefreshScript) { python $RefreshScript }

Write-Host "[2/3] Running figure generation..."
$FigScript = Join-Path $PaperRoot "figures\scripts\plot_mpl_figures.py"
if (Test-Path $FigScript) {
    python $FigScript --formats pdf png --dpi 200
}
$PumlScript = Join-Path $PaperRoot "scripts\render_puml.py"
if (Test-Path $PumlScript) { python $PumlScript }

Write-Host "[3/3] Compiling LaTeX..."
Push-Location $PaperRoot
& $TectonicExe --keep-logs --outdir $BuildDir "main.tex"
if ($LASTEXITCODE -ne 0) { Pop-Location; throw "Tectonic compilation failed" }
Pop-Location
Write-Host "PDF: $(Join-Path $BuildDir 'main.pdf')"
