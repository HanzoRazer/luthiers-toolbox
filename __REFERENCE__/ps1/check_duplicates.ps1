# Check for Duplicates Between Legacy Folders and Core Repo
# Compares files in Tier 2 folders against services/, packages/, docs/

$ErrorActionPreference = "SilentlyContinue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DUPLICATE FILE ANALYSIS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Core directories (the "real" codebase)
$coreDirs = @("services", "packages", "docs", "scripts")

# Tier 2 legacy folders to check
$legacyFolders = @(
    "Governance_Code_Bundle",
    "ToolBox_Patch*",
    "ToolBox_All_Scripts_*",
    "ToolBox_Art_Studio*",
    "ToolBox_CurveLab*",
    "ToolBox_CurveMath*",
    "ToolBox_DXF*",
    "ToolBox_Monorepo*",
    "ToolBox_PathDoctor*",
    "ToolBox_Scripts_Recovered*",
    "ToolBox_Workspace*",
    "Guitar Design HTML app",
    "Luthiers Tool Box",
    "Luthiers_Tool_Box_*",
    "luthiers_toolbox_*",
    "Archtop",
    "Stratocaster",
    "Golden Path",
    "Integration_Patch_*",
    "WiringWorkbench_*",
    "phantom_cleanup_patch",
    "security_patch_dxf",
    "phase_bc_for_repo",
    "temp_patch",
    "temp_extract_*",
    "files (*)",
    "README_Community_Patch*",
    "Feature_*",
    "vibe-blueprintanalyzer-main"
)

# Build index of core files (filename -> paths)
Write-Host "[PHASE 1] Indexing core repository files..." -ForegroundColor Yellow
$coreIndex = @{}
$coreFileCount = 0

foreach ($coreDir in $coreDirs) {
    if (Test-Path $coreDir) {
        $files = Get-ChildItem -Path $coreDir -Recurse -File -ErrorAction SilentlyContinue |
                 Where-Object { $_.FullName -notlike "*node_modules*" -and $_.FullName -notlike "*__pycache__*" }

        foreach ($f in $files) {
            $name = $f.Name.ToLower()
            if (-not $coreIndex.ContainsKey($name)) {
                $coreIndex[$name] = @()
            }
            $coreIndex[$name] += $f.FullName.Replace((Get-Location).Path + "\", "")
            $coreFileCount++
        }
    }
}

Write-Host "  Indexed $coreFileCount files from core directories" -ForegroundColor Green
Write-Host ""

# Check each legacy folder for duplicates
Write-Host "[PHASE 2] Checking legacy folders for duplicates..." -ForegroundColor Yellow
Write-Host ""

$results = @()

foreach ($pattern in $legacyFolders) {
    $folders = Get-ChildItem -Directory -Filter $pattern -ErrorAction SilentlyContinue

    foreach ($folder in $folders) {
        $legacyFiles = Get-ChildItem -Path $folder.FullName -Recurse -File -ErrorAction SilentlyContinue |
                       Where-Object { $_.FullName -notlike "*node_modules*" -and $_.FullName -notlike "*__pycache__*" }

        $totalFiles = $legacyFiles.Count
        $duplicates = 0
        $unique = 0
        $dupList = @()

        foreach ($lf in $legacyFiles) {
            $name = $lf.Name.ToLower()
            if ($coreIndex.ContainsKey($name)) {
                $duplicates++
                $dupList += @{
                    legacy = $lf.FullName.Replace((Get-Location).Path + "\", "")
                    core = $coreIndex[$name][0]
                }
            } else {
                $unique++
            }
        }

        if ($totalFiles -gt 0) {
            $dupPercent = [math]::Round(($duplicates / $totalFiles) * 100, 1)

            $results += @{
                folder = $folder.Name
                total = $totalFiles
                duplicates = $duplicates
                unique = $unique
                percent = $dupPercent
                samples = $dupList | Select-Object -First 3
            }
        }
    }
}

# Sort by duplicate percentage (highest first)
$results = $results | Sort-Object { $_.percent } -Descending

# Display results
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DUPLICATE ANALYSIS RESULTS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host ("{0,-55} {1,6} {2,6} {3,6} {4,8}" -f "FOLDER", "TOTAL", "DUPS", "UNIQ", "DUP %")
Write-Host ("{0,-55} {1,6} {2,6} {3,6} {4,8}" -f "------", "-----", "----", "----", "-----")

foreach ($r in $results) {
    $color = if ($r.percent -ge 80) { "Green" }
             elseif ($r.percent -ge 50) { "Yellow" }
             else { "Red" }

    $folderName = if ($r.folder.Length -gt 53) { $r.folder.Substring(0, 50) + "..." } else { $r.folder }

    Write-Host ("{0,-55} {1,6} {2,6} {3,6} {4,7}%" -f $folderName, $r.total, $r.duplicates, $r.unique, $r.percent) -ForegroundColor $color
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "LEGEND" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  GREEN  (80%+)  = Safe to delete, mostly duplicates" -ForegroundColor Green
Write-Host "  YELLOW (50-79%) = Review before deleting" -ForegroundColor Yellow
Write-Host "  RED    (<50%)  = Has unique content, archive carefully" -ForegroundColor Red
Write-Host ""

# Show some sample duplicates
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SAMPLE DUPLICATES (proof they exist in core)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$shown = 0
foreach ($r in $results) {
    if ($r.samples.Count -gt 0 -and $shown -lt 10) {
        Write-Host "$($r.folder):" -ForegroundColor Yellow
        foreach ($s in $r.samples) {
            Write-Host "  Legacy: $($s.legacy)" -ForegroundColor DarkGray
            Write-Host "  Core:   $($s.core)" -ForegroundColor Green
            Write-Host ""
        }
        $shown++
    }
}

# Summary stats
$totalLegacyFiles = ($results | Measure-Object -Property total -Sum).Sum
$totalDuplicates = ($results | Measure-Object -Property duplicates -Sum).Sum
$totalUnique = ($results | Measure-Object -Property unique -Sum).Sum
$overallPercent = if ($totalLegacyFiles -gt 0) { [math]::Round(($totalDuplicates / $totalLegacyFiles) * 100, 1) } else { 0 }

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Legacy folders analyzed:  $($results.Count)"
Write-Host "  Total files in legacy:    $totalLegacyFiles"
Write-Host "  Duplicates found:         $totalDuplicates ($overallPercent%)" -ForegroundColor Green
Write-Host "  Unique files:             $totalUnique" -ForegroundColor Yellow
Write-Host ""

if ($overallPercent -ge 70) {
    Write-Host "RECOMMENDATION: High duplicate rate. Safe to archive/delete most legacy folders." -ForegroundColor Green
} elseif ($overallPercent -ge 40) {
    Write-Host "RECOMMENDATION: Moderate duplicates. Review unique files before cleanup." -ForegroundColor Yellow
} else {
    Write-Host "RECOMMENDATION: Low duplicate rate. Many unique files - archive carefully." -ForegroundColor Red
}
