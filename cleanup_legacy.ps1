<#
.SYNOPSIS
  Repo cleanup script for Luthier's ToolBox.

.DESCRIPTION
  Automatically finds and moves recognized legacy folders into the __ARCHIVE__
  hierarchy, based on name patterns.
  
  TUNED FOR ACTUAL REPO CONTENTS - December 5, 2025
  Patterns match: ToolBox_*, ltb-*, Feature_*, legacy servers, build bundle .py files

  Designed to be run from the repo root.

.PARAMETER DryRun
  If set, the script only reports what it WOULD move, without actually moving anything.

.EXAMPLE
  # See what would be moved, without touching anything
  .\cleanup_legacy.ps1 -DryRun

.EXAMPLE
  # Actually move recognized legacy folders into __ARCHIVE__
  .\cleanup_legacy.ps1
#>

param(
    [switch]$DryRun
)

Write-Host "=== Luthier's ToolBox Legacy Cleanup ===" -ForegroundColor Cyan
Write-Host "DryRun mode: $DryRun`n" -ForegroundColor Yellow

# ------------------------------------------------------------------------------------
# 1. Resolve repo root (directory where this script lives)
# ------------------------------------------------------------------------------------
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# ------------------------------------------------------------------------------------
# 2. Define archive structure
# ------------------------------------------------------------------------------------
$archiveRoot        = Join-Path $ScriptDir "__ARCHIVE__"
$buildBundlesDir    = Join-Path $archiveRoot "build_bundles"
$patchBundlesDir    = Join-Path $archiveRoot "patch_bundles"
$serverLegacyDir    = Join-Path $archiveRoot "server_legacy"
$legacySubsystemsDir= Join-Path $archiveRoot "legacy_subsystems"
$sandboxHistoryDir  = Join-Path $archiveRoot "sandbox_history"

# Build bundle subdirectories for Python files
$buildBundlesRmos       = Join-Path $buildBundlesDir "rmos"
$buildBundlesSawLab     = Join-Path $buildBundlesDir "saw_lab"
$buildBundlesArtStudio  = Join-Path $buildBundlesDir "art_studio"
$buildBundlesToolpath   = Join-Path $buildBundlesDir "toolpath"
$buildBundlesAi         = Join-Path $buildBundlesDir "ai"
$buildBundlesCalc       = Join-Path $buildBundlesDir "calculators"
$buildBundlesMisc       = Join-Path $buildBundlesDir "misc"

$archiveDirs = @(
    $archiveRoot,
    $buildBundlesDir,
    $buildBundlesRmos,
    $buildBundlesSawLab,
    $buildBundlesArtStudio,
    $buildBundlesToolpath,
    $buildBundlesAi,
    $buildBundlesCalc,
    $buildBundlesMisc,
    $patchBundlesDir,
    $serverLegacyDir,
    $legacySubsystemsDir,
    $sandboxHistoryDir
)

foreach ($dir in $archiveDirs) {
    if (-not (Test-Path $dir)) {
        if ($DryRun) {
            Write-Host "[DryRun] Would create archive directory: $dir" -ForegroundColor DarkGray
        } else {
            Write-Host "Creating archive directory: $dir" -ForegroundColor DarkGray
            New-Item -ItemType Directory -Path $dir | Out-Null
        }
    }
}

# ------------------------------------------------------------------------------------
# 3. Define recognized legacy patterns - TUNED FOR ACTUAL REPO CONTENTS
#    Last updated: December 5, 2025
#    Based on actual directory listing from repo root
# ------------------------------------------------------------------------------------

# Each entry: Pattern, TargetArchiveDir, Description
$rules = @(
    # ===================================================================================
    # PATCH BUNDLES (ToolBox_*) - 50+ directories of applied patches
    # ===================================================================================
    @{ Pattern = "ToolBox_Patch*";              Target = $patchBundlesDir;     Description = "ToolBox Patch bundle" },
    @{ Pattern = "ToolBox_All_Scripts*";        Target = $patchBundlesDir;     Description = "Scripts consolidated bundle" },
    @{ Pattern = "ToolBox_Scripts_Recovered*";  Target = $patchBundlesDir;     Description = "Recovered scripts bundle" },
    @{ Pattern = "ToolBox_Art_Studio*";         Target = $patchBundlesDir;     Description = "Art Studio patch bundle" },
    @{ Pattern = "ToolBox_CurveLab*";           Target = $patchBundlesDir;     Description = "CurveLab patch bundle" },
    @{ Pattern = "ToolBox_CurveMath*";          Target = $patchBundlesDir;     Description = "CurveMath patch bundle" },
    @{ Pattern = "ToolBox_Monorepo*";           Target = $patchBundlesDir;     Description = "Monorepo patch bundle" },
    @{ Pattern = "ToolBox_Workspace*";          Target = $patchBundlesDir;     Description = "Workspace patch bundle" },
    @{ Pattern = "ToolBox_DXF*";                Target = $patchBundlesDir;     Description = "DXF patch bundle" },
    @{ Pattern = "ToolBox_PathDoctor*";         Target = $patchBundlesDir;     Description = "PathDoctor utility bundle" },
    @{ Pattern = "ToolBox_*";                   Target = $patchBundlesDir;     Description = "Other ToolBox bundle (catch-all)" },

    # ===================================================================================
    # FEATURE EXTRACTIONS - Already integrated
    # ===================================================================================
    @{ Pattern = "Feature_*";                   Target = $patchBundlesDir;     Description = "Feature extraction bundle" },
    @{ Pattern = "Integration_Patch_*";         Target = $patchBundlesDir;     Description = "Integration patch bundle" },
    @{ Pattern = "README_Community_Patch*";     Target = $patchBundlesDir;     Description = "Community patch readme" },
    @{ Pattern = "WiringWorkbench_*";           Target = $patchBundlesDir;     Description = "Wiring workbench patch" },
    @{ Pattern = "CAM_Roadmap_*";               Target = $patchBundlesDir;     Description = "CAM roadmap bundle" },

    # ===================================================================================
    # LEGACY SERVER - Pre-RMOS 2.0 backend
    # ===================================================================================
    @{ Pattern = "server";                      Target = $serverLegacyDir;     Description = "Legacy FastAPI server (pre-RMOS)" },
    @{ Pattern = "blueprint-reader";            Target = $serverLegacyDir;     Description = "Legacy blueprint reader" },

    # ===================================================================================
    # LEGACY SUBSYSTEMS - Old project directories
    # ===================================================================================
    @{ Pattern = "Guitar Design HTML app";      Target = $legacySubsystemsDir; Description = "Legacy HTML guitar designer" },
    @{ Pattern = "Luthiers Tool Box";           Target = $legacySubsystemsDir; Description = "Legacy MVP (old naming)" },
    @{ Pattern = "Lutherier Project";           Target = $legacySubsystemsDir; Description = "Legacy CAD project files" },
    @{ Pattern = "Luthiers_ToolBox_Smart_Guitar*"; Target = $legacySubsystemsDir; Description = "Smart Guitar bundle (separate project)" },
    @{ Pattern = "Luthiers_Tool_Box_Addons*";   Target = $legacySubsystemsDir; Description = "Addons bundle (integrated)" },
    @{ Pattern = "OM Project";                  Target = $legacySubsystemsDir; Description = "OM Project (legacy)" },
    @{ Pattern = "Archtop";                     Target = $legacySubsystemsDir; Description = "Archtop project (legacy)" },
    @{ Pattern = "Soprano Ukuele";              Target = $legacySubsystemsDir; Description = "Ukulele project (legacy)" },
    @{ Pattern = "Stratocaster";                Target = $legacySubsystemsDir; Description = "Stratocaster project (legacy)" },
    @{ Pattern = "vibe-blueprintanalyzer*";     Target = $legacySubsystemsDir; Description = "Vibe analyzer (external)" },

    # ===================================================================================
    # LTB PRODUCT VARIANTS - May need review before archiving
    # ===================================================================================
    @{ Pattern = "ltb-bridge-designer";         Target = $legacySubsystemsDir; Description = "LTB Bridge Designer variant" },
    @{ Pattern = "ltb-enterprise";              Target = $legacySubsystemsDir; Description = "LTB Enterprise variant" },
    @{ Pattern = "ltb-express";                 Target = $legacySubsystemsDir; Description = "LTB Express variant" },
    @{ Pattern = "ltb-fingerboard-designer";    Target = $legacySubsystemsDir; Description = "LTB Fingerboard Designer variant" },
    @{ Pattern = "ltb-headstock-designer";      Target = $legacySubsystemsDir; Description = "LTB Headstock Designer variant" },
    @{ Pattern = "ltb-neck-designer";           Target = $legacySubsystemsDir; Description = "LTB Neck Designer variant" },
    @{ Pattern = "ltb-parametric-guitar";       Target = $legacySubsystemsDir; Description = "LTB Parametric Guitar variant" },
    @{ Pattern = "ltb-pro";                     Target = $legacySubsystemsDir; Description = "LTB Pro variant" },
    @{ Pattern = "ltb-test-dummy";              Target = $legacySubsystemsDir; Description = "LTB Test Dummy (dev artifact)" },

    # ===================================================================================
    # TOOL DATABASES - External vendor data (keep for reference)
    # ===================================================================================
    @{ Pattern = "Bits-Bits-CarveCo*";          Target = $legacySubsystemsDir; Description = "CarveCo tool database" },
    @{ Pattern = "Myers-Woodshop-Set*";         Target = $legacySubsystemsDir; Description = "Myers Woodshop tool set" },
    @{ Pattern = "Two-Moose-Set*";              Target = $legacySubsystemsDir; Description = "Two Moose tool set" },
    @{ Pattern = "MUST-Be-UNZIPPED*";           Target = $legacySubsystemsDir; Description = "Unzipped tool database" },
    @{ Pattern = "Carveco Tool Database*";      Target = $legacySubsystemsDir; Description = "Carveco database export" },
    @{ Pattern = "SainSmart*";                  Target = $legacySubsystemsDir; Description = "SainSmart tool data" },
    @{ Pattern = "Fusion360 Tool Database";     Target = $legacySubsystemsDir; Description = "Fusion360 tool library" },

    # ===================================================================================
    # SANDBOXES (if any exist)
    # ===================================================================================
    @{ Pattern = "sandbox_*";                   Target = $sandboxHistoryDir;   Description = "Retired sandbox" },
    @{ Pattern = "sandbox";                     Target = $sandboxHistoryDir;   Description = "Sandbox root" }
)

# ------------------------------------------------------------------------------------
# 4. Logging
# ------------------------------------------------------------------------------------
$logFile = Join-Path $ScriptDir "cleanup_legacy_log.txt"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
"=== Cleanup run at $timestamp (DryRun = $DryRun) ===" | Out-File -FilePath $logFile -Append

function Log-Action {
    param(
        [string]$Message
    )
    $Message | Out-File -FilePath $logFile -Append
}

# ------------------------------------------------------------------------------------
# 5. Scan and move legacy directories
# ------------------------------------------------------------------------------------

# Helper: ensure we only consider top-level entries in repo root (no nested scanning)
$topLevelDirs = Get-ChildItem -Path $ScriptDir -Directory

$movesPlanned = 0

foreach ($rule in $rules) {
    $pattern = $rule.Pattern
    $target  = $rule.Target
    $desc    = $rule.Description

    # Find matching top-level directories
    $matches = $topLevelDirs | Where-Object { $_.Name -like $pattern }

    foreach ($item in $matches) {
        $sourcePath = $item.FullName
        $destPath   = Join-Path $target $item.Name

        # ===================================================================================
        # PROTECTED DIRECTORIES - Never move these
        # ===================================================================================
        $protected = @(
            "__ARCHIVE__",
            "services",
            "packages",
            "docs",
            "docker",
            "scripts",
            "tests",
            "data",
            "projects",
            "templates",
            "tools",
            "ci",
            "migrations",
            "reports",
            "public_badges",
            "client",
            ".git",
            ".github",
            ".vscode",
            ".venv",
            ".husky",
            ".eslint-rules",
            "node_modules"
        )
        
        if ($protected -contains $item.Name) {
            continue
        }

        $movesPlanned++

        # If destination exists, add a timestamp suffix to avoid collision
        if (Test-Path $destPath) {
            $suffix = Get-Date -Format "yyyyMMdd_HHmmss"
            $destPath = Join-Path $target ("{0}_{1}" -f $item.Name, $suffix)
        }

        $msg = "Rule: '$pattern' ($desc) => Move '$sourcePath' → '$destPath'"
        Write-Host $msg -ForegroundColor Green
        Log-Action $msg

        if (-not $DryRun) {
            try {
                Move-Item -Path $sourcePath -Destination $destPath -Force
            } catch {
                $err = "ERROR moving '$sourcePath' → '$destPath': $($_.Exception.Message)"
                Write-Host $err -ForegroundColor Red
                Log-Action $err
            }
        } else {
            Write-Host "[DryRun] No actual move performed." -ForegroundColor Yellow
        }
    }
}

if ($movesPlanned -eq 0) {
    Write-Host "No legacy folders matched the current patterns." -ForegroundColor Yellow
    Log-Action "No moves performed (no matches)."
} else {
    Write-Host "`nTotal legacy folders matched: $movesPlanned" -ForegroundColor Cyan
    if ($DryRun) {
        Write-Host "Dry run complete. Review 'cleanup_legacy_log.txt' before running without -DryRun." -ForegroundColor Yellow
    } else {
        Write-Host "Cleanup complete. See 'cleanup_legacy_log.txt' for details." -ForegroundColor Green
    }
}

# ------------------------------------------------------------------------------------
# 6. OPTIONAL: Move root Python build bundle files
#    Uncomment to enable file-level cleanup (more aggressive)
# ------------------------------------------------------------------------------------

Write-Host "`n=== Checking for root Python build bundle files ===" -ForegroundColor Cyan

# Define file patterns and their target directories
$fileRules = @(
    @{ Pattern = "rmos_*.py";              Target = $buildBundlesRmos;      Description = "RMOS build bundle" },
    @{ Pattern = "RMOS_*.py";              Target = $buildBundlesRmos;      Description = "RMOS build bundle (caps)" },
    @{ Pattern = "calculators_saw_*.py";   Target = $buildBundlesSawLab;    Description = "Saw calculator bundle" },
    @{ Pattern = "Saw Lab 2.0*.py";        Target = $buildBundlesSawLab;    Description = "Saw Lab skeleton" },
    @{ Pattern = "saw_lab_*.py";           Target = $buildBundlesSawLab;    Description = "Saw Lab bundle" },
    @{ Pattern = "Saw_*.py";               Target = $buildBundlesSawLab;    Description = "Saw bundle (caps)" },
    @{ Pattern = "art_studio_*.py";        Target = $buildBundlesArtStudio; Description = "Art Studio bundle" },
    @{ Pattern = "toolpath_*.py";          Target = $buildBundlesToolpath;  Description = "Toolpath bundle" },
    @{ Pattern = "ai_graphics_*.py";       Target = $buildBundlesAi;        Description = "AI Graphics bundle" },
    @{ Pattern = "ai_core_*.py";           Target = $buildBundlesAi;        Description = "AI Core bundle" },
    @{ Pattern = "ai_rmos_*.py";           Target = $buildBundlesAi;        Description = "AI RMOS bundle" },
    @{ Pattern = "constraint_profiles_ai.py"; Target = $buildBundlesAi;     Description = "Constraint profiles AI" },
    @{ Pattern = "calculators_service*.py"; Target = $buildBundlesCalc;     Description = "Calculator service bundle" },
    @{ Pattern = "rosette_feasibility_scorer.py"; Target = $buildBundlesRmos; Description = "Rosette scorer bundle" },
    @{ Pattern = "schemas_logs_ai.py";     Target = $buildBundlesRmos;      Description = "Schemas logs AI" },
    @{ Pattern = "compare_automation_router.py"; Target = $buildBundlesMisc; Description = "Compare router bundle" },
    @{ Pattern = "mode_preview_routes.py"; Target = $buildBundlesMisc;      Description = "Mode preview routes" },
    @{ Pattern = "gcode_reader.py";        Target = $buildBundlesMisc;      Description = "G-code reader utility" }
)

$filesPlanned = 0
$topLevelFiles = Get-ChildItem -Path $ScriptDir -File -Filter "*.py"

foreach ($fileRule in $fileRules) {
    $pattern = $fileRule.Pattern
    $target  = $fileRule.Target
    $desc    = $fileRule.Description
    
    $fileMatches = $topLevelFiles | Where-Object { $_.Name -like $pattern }
    
    foreach ($file in $fileMatches) {
        $sourcePath = $file.FullName
        $destPath   = Join-Path $target $file.Name
        
        $filesPlanned++
        
        if (Test-Path $destPath) {
            $suffix = Get-Date -Format "yyyyMMdd_HHmmss"
            $destPath = Join-Path $target ("{0}_{1}{2}" -f $file.BaseName, $suffix, $file.Extension)
        }
        
        $msg = "File: '$pattern' ($desc) => Move '$($file.Name)' → '$target'"
        Write-Host $msg -ForegroundColor Magenta
        Log-Action $msg
        
        if (-not $DryRun) {
            try {
                Move-Item -Path $sourcePath -Destination $destPath -Force
            } catch {
                $err = "ERROR moving file '$sourcePath': $($_.Exception.Message)"
                Write-Host $err -ForegroundColor Red
                Log-Action $err
            }
        } else {
            Write-Host "[DryRun] No actual file move performed." -ForegroundColor Yellow
        }
    }
}

if ($filesPlanned -gt 0) {
    Write-Host "`nTotal Python build bundle files matched: $filesPlanned" -ForegroundColor Magenta
}

# ------------------------------------------------------------------------------------
# 7. Summary
# ------------------------------------------------------------------------------------
$totalMoves = $movesPlanned + $filesPlanned
Write-Host "`n=== CLEANUP SUMMARY ===" -ForegroundColor Cyan
Write-Host "  Directories: $movesPlanned" -ForegroundColor Green
Write-Host "  Files:       $filesPlanned" -ForegroundColor Magenta
Write-Host "  Total:       $totalMoves" -ForegroundColor White

if ($DryRun -and $totalMoves -gt 0) {
    Write-Host "`n⚠️  This was a DRY RUN. No files were actually moved." -ForegroundColor Yellow
    Write-Host "    Review cleanup_legacy_log.txt and run without -DryRun to apply." -ForegroundColor Yellow
}