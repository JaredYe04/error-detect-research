Param(
    [Parameter(Mandatory = $true)]
    [string]$RunDir,
    [string]$PythonExe = "python",
    [string]$PreventionModes = "B1,B2,M,A1,A2,A3",
    [string]$PreventionOutputDir = "",
    [string]$PreventionRunName = "",
    [string]$Formats = "png,pdf",
    [int]$Dpi = 300,
    [int]$Seed = 7,
    [switch]$SkipPrevention = $false
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-Log {
    param(
        [string]$Level,
        [string]$Message
    )
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$ts][$Level] $Message"
}

function Invoke-Checked {
    param(
        [string]$Label,
        [string]$Exe,
        [string[]]$CommandArgs
    )
    Write-Log "STEP" $Label
    Write-Host "  + $Exe $($CommandArgs -join ' ')"
    & $Exe @CommandArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Step failed ($Label), exit code: $LASTEXITCODE"
    }
}

function Resolve-WorkspacePath {
    param(
        [string]$PathValue,
        [string]$BaseDir
    )
    if ([string]::IsNullOrWhiteSpace($PathValue)) {
        return ""
    }
    if ([System.IO.Path]::IsPathRooted($PathValue)) {
        return (Resolve-Path $PathValue).Path
    }
    return (Resolve-Path (Join-Path $BaseDir $PathValue)).Path
}

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$PaperRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

$ResolvedRunDir = Resolve-WorkspacePath -PathValue $RunDir -BaseDir $RepoRoot
if (-not (Test-Path (Join-Path $ResolvedRunDir "results.jsonl"))) {
    throw "Run directory must contain results.jsonl: $ResolvedRunDir"
}

if ([string]::IsNullOrWhiteSpace($PreventionOutputDir)) {
    $ResolvedPreventionOutputDir = Join-Path $RepoRoot "artifacts\prevention_eval"
} else {
    if ([System.IO.Path]::IsPathRooted($PreventionOutputDir)) {
        $ResolvedPreventionOutputDir = $PreventionOutputDir
    } else {
        $ResolvedPreventionOutputDir = Join-Path $RepoRoot $PreventionOutputDir
    }
}
New-Item -ItemType Directory -Force -Path $ResolvedPreventionOutputDir | Out-Null

if ([string]::IsNullOrWhiteSpace($PreventionRunName)) {
    $PreventionRunName = "prevention_$((Split-Path $ResolvedRunDir -Leaf))"
}
$PreventionSummaryPath = Join-Path (Join-Path $ResolvedPreventionOutputDir $PreventionRunName) "prevention_summary.json"

$modes = @()
foreach ($mode in $PreventionModes.Split(",")) {
    $trimmed = $mode.Trim()
    if ($trimmed) {
        $modes += $trimmed
    }
}
if ($modes.Count -eq 0) {
    throw "PreventionModes cannot be empty."
}

$formatList = @()
foreach ($fmt in $Formats.Split(",")) {
    $trimmed = $fmt.Trim()
    if ($trimmed) {
        $formatList += $trimmed
    }
}
if ($formatList.Count -eq 0) {
    throw "Formats cannot be empty."
}

Write-Log "INFO" "Repo root: $RepoRoot"
Write-Log "INFO" "Run dir: $ResolvedRunDir"
Write-Log "INFO" "Paper root: $PaperRoot"
Write-Log "INFO" "Prevention output: $ResolvedPreventionOutputDir (run: $PreventionRunName)"

if (-not $SkipPrevention) {
    $preventionArgs = @(
        (Join-Path $RepoRoot "experiments\run_prevention.py"),
        "--modes"
    ) + $modes + @(
        "--output", $ResolvedPreventionOutputDir,
        "--run-name", $PreventionRunName
    )
    Invoke-Checked -Label "1/6 prevention evaluation" -Exe $PythonExe -CommandArgs $preventionArgs
} else {
    Write-Log "STEP" "1/6 prevention evaluation (skipped)"
}

$analyzeArgs = @(
    (Join-Path $RepoRoot "experiments\analyze.py"),
    $ResolvedRunDir
)
Invoke-Checked -Label "2/6 analyze run results" -Exe $PythonExe -CommandArgs $analyzeArgs

$prepareArgs = @(
    (Join-Path $PaperRoot "scripts\prepare_paper_data.py"),
    "--run-dir", $ResolvedRunDir,
    "--prevention-summary", $PreventionSummaryPath
)
Invoke-Checked -Label "3/6 prepare paper data" -Exe $PythonExe -CommandArgs $prepareArgs

$refreshArgs = @(
    (Join-Path $PaperRoot "scripts\refresh_paper_assets.py"),
    "--skip-data-refresh",
    "--static-formats"
) + $formatList + @(
    "--dpi", "$Dpi",
    "--seed", "$Seed"
)
Invoke-Checked -Label "4/6 regenerate figures" -Exe $PythonExe -CommandArgs $refreshArgs

$statsArgs = @(
    (Join-Path $PaperRoot "scripts\update_stats_table.py"),
    "--run-dir", $ResolvedRunDir
)
Invoke-Checked -Label "5/6 update stats table" -Exe $PythonExe -CommandArgs $statsArgs

$BuildScript = Join-Path $PaperRoot "scripts\build.ps1"
Write-Log "STEP" "6/6 rebuild PDF"
Write-Host "  + powershell -ExecutionPolicy Bypass -File $BuildScript -Which long -SkipRefresh -Formats $Formats -Dpi $Dpi -Seed $Seed"
& powershell -ExecutionPolicy Bypass -File $BuildScript -Which long -SkipRefresh -Formats $Formats -Dpi $Dpi -Seed $Seed
if ($LASTEXITCODE -ne 0) {
    throw "Step failed (6/6 rebuild PDF), exit code: $LASTEXITCODE"
}

$PdfPath = Join-Path $PaperRoot "build\main.pdf"
if (-not (Test-Path $PdfPath)) {
    throw "Pipeline completed without PDF at expected path: $PdfPath"
}

Write-Log "OK" "Post-experiment pipeline completed successfully."
Write-Log "OK" "PDF: $PdfPath"
