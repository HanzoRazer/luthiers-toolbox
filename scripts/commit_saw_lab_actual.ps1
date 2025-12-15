# =============================================================================
# COMMIT_SAW_LAB_ACTUAL.PS1
# Commits Saw Lab files in dependency order - UPDATED for actual file structure
# Target Branch: feature/rmos-2-0-skeleton
# =============================================================================

$ErrorActionPreference = "Stop"

# Configuration
$BranchName = "feature/rmos-2-0-skeleton"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)  # Go up from scripts/

Write-Host "=== Saw Lab Commit Script (Actual Structure) ===" -ForegroundColor Cyan
Write-Host "Target Branch: $BranchName" -ForegroundColor Yellow
Write-Host "Repository Root: $RepoRoot" -ForegroundColor Yellow
Write-Host ""

# Change to repo root
Push-Location $RepoRoot

try {
    # Verify we're on correct branch
    $currentBranch = git branch --show-current
    if ($currentBranch -ne $BranchName) {
        Write-Host "WARNING: Current branch is '$currentBranch', expected '$BranchName'" -ForegroundColor Yellow
        $continue = Read-Host "Continue anyway? (y/n)"
        if ($continue -ne "y") {
            Write-Host "Aborted." -ForegroundColor Red
            exit 1
        }
    }

    # ==========================================================================
    # STEP 1: JSON Data Files (Foundational)
    # ==========================================================================
    Write-Host "`n=== Step 1: JSON Data Files ===" -ForegroundColor Magenta
    
    $step1Files = @(
        "saw_lab_blades.json",                          # Root level (contains blades + presets)
        "tests/data/saw_lab_materials.json"             # Test fixtures
    )
    
    $step1Exists = @()
    foreach ($file in $step1Files) {
        $fullPath = Join-Path $RepoRoot $file
        if (Test-Path $fullPath) {
            $step1Exists += $file
            Write-Host "  [EXISTS] $file" -ForegroundColor Green
        } else {
            Write-Host "  [MISSING] $file" -ForegroundColor Yellow
        }
    }
    
    if ($step1Exists.Count -gt 0) {
        git add $step1Exists
        git commit -m "feat(saw-lab): Step 1 - JSON data fixtures (blades, materials)" --allow-empty
        Write-Host "  Committed Step 1" -ForegroundColor Green
    }

    # ==========================================================================
    # STEP 2: Calculator Modules (Physics layer)
    # ==========================================================================
    Write-Host "`n=== Step 2: Calculator Modules ===" -ForegroundColor Magenta
    
    $step2Files = @(
        "services/api/app/saw_lab/calculators/__init__.py",
        "services/api/app/saw_lab/calculators/saw_rimspeed.py",
        "services/api/app/saw_lab/calculators/saw_bite_load.py",
        "services/api/app/saw_lab/calculators/saw_heat.py",
        "services/api/app/saw_lab/calculators/saw_deflection.py",
        "services/api/app/saw_lab/calculators/saw_kickback.py"
    )
    
    $step2Exists = @()
    foreach ($file in $step2Files) {
        $fullPath = Join-Path $RepoRoot $file
        if (Test-Path $fullPath) {
            $step2Exists += $file
            Write-Host "  [EXISTS] $file" -ForegroundColor Green
        } else {
            Write-Host "  [MISSING] $file" -ForegroundColor Yellow
        }
    }
    
    if ($step2Exists.Count -gt 0) {
        git add $step2Exists
        git commit -m "feat(saw-lab): Step 2 - Calculator modules (physics layer)" --allow-empty
        Write-Host "  Committed Step 2" -ForegroundColor Green
    }

    # ==========================================================================
    # STEP 3: Core Models and Types
    # ==========================================================================
    Write-Host "`n=== Step 3: Core Models ===" -ForegroundColor Magenta
    
    $step3Files = @(
        "services/api/app/saw_lab/__init__.py",
        "services/api/app/saw_lab/models.py",
        "services/api/app/saw_lab/geometry.py",
        "services/api/app/saw_lab/debug_schemas.py"
    )
    
    $step3Exists = @()
    foreach ($file in $step3Files) {
        $fullPath = Join-Path $RepoRoot $file
        if (Test-Path $fullPath) {
            $step3Exists += $file
            Write-Host "  [EXISTS] $file" -ForegroundColor Green
        } else {
            Write-Host "  [MISSING] $file" -ForegroundColor Yellow
        }
    }
    
    if ($step3Exists.Count -gt 0) {
        git add $step3Exists
        git commit -m "feat(saw-lab): Step 3 - Core models and schemas" --allow-empty
        Write-Host "  Committed Step 3" -ForegroundColor Green
    }

    # ==========================================================================
    # STEP 4: Risk Evaluator (Safety layer)
    # ==========================================================================
    Write-Host "`n=== Step 4: Risk Evaluator ===" -ForegroundColor Magenta
    
    $step4Files = @(
        "services/api/app/saw_lab/risk_evaluator.py"
    )
    
    $step4Exists = @()
    foreach ($file in $step4Files) {
        $fullPath = Join-Path $RepoRoot $file
        if (Test-Path $fullPath) {
            $step4Exists += $file
            Write-Host "  [EXISTS] $file" -ForegroundColor Green
        } else {
            Write-Host "  [MISSING] $file" -ForegroundColor Yellow
        }
    }
    
    if ($step4Exists.Count -gt 0) {
        git add $step4Exists
        git commit -m "feat(saw-lab): Step 4 - Risk evaluator (safety layer)" --allow-empty
        Write-Host "  Committed Step 4" -ForegroundColor Green
    }

    # ==========================================================================
    # STEP 5: Path Planner
    # ==========================================================================
    Write-Host "`n=== Step 5: Path Planner ===" -ForegroundColor Magenta
    
    $step5Files = @(
        "services/api/app/saw_lab/path_planner.py"
    )
    
    $step5Exists = @()
    foreach ($file in $step5Files) {
        $fullPath = Join-Path $RepoRoot $file
        if (Test-Path $fullPath) {
            $step5Exists += $file
            Write-Host "  [EXISTS] $file" -ForegroundColor Green
        } else {
            Write-Host "  [MISSING] $file" -ForegroundColor Yellow
        }
    }
    
    if ($step5Exists.Count -gt 0) {
        git add $step5Exists
        git commit -m "feat(saw-lab): Step 5 - Path planner" --allow-empty
        Write-Host "  Committed Step 5" -ForegroundColor Green
    }

    # ==========================================================================
    # STEP 6: Toolpath Builder
    # ==========================================================================
    Write-Host "`n=== Step 6: Toolpath Builder ===" -ForegroundColor Magenta
    
    $step6Files = @(
        "services/api/app/saw_lab/toolpath_builder.py"
    )
    
    $step6Exists = @()
    foreach ($file in $step6Files) {
        $fullPath = Join-Path $RepoRoot $file
        if (Test-Path $fullPath) {
            $step6Exists += $file
            Write-Host "  [EXISTS] $file" -ForegroundColor Green
        } else {
            Write-Host "  [MISSING] $file" -ForegroundColor Yellow
        }
    }
    
    if ($step6Exists.Count -gt 0) {
        git add $step6Exists
        git commit -m "feat(saw-lab): Step 6 - Toolpath builder" --allow-empty
        Write-Host "  Committed Step 6" -ForegroundColor Green
    }

    # ==========================================================================
    # STEP 7: FastAPI Routers
    # ==========================================================================
    Write-Host "`n=== Step 7: FastAPI Routers ===" -ForegroundColor Magenta
    
    $step7Files = @(
        "services/api/app/saw_lab/debug_router.py",
        "services/api/app/routers/saw_blade_router.py",
        "services/api/app/routers/saw_gcode_router.py",
        "services/api/app/routers/saw_telemetry_router.py",
        "services/api/app/routers/saw_validate_router.py"
    )
    
    $step7Exists = @()
    foreach ($file in $step7Files) {
        $fullPath = Join-Path $RepoRoot $file
        if (Test-Path $fullPath) {
            $step7Exists += $file
            Write-Host "  [EXISTS] $file" -ForegroundColor Green
        } else {
            Write-Host "  [MISSING] $file" -ForegroundColor Yellow
        }
    }
    
    if ($step7Exists.Count -gt 0) {
        git add $step7Exists
        git commit -m "feat(saw-lab): Step 7 - FastAPI routers" --allow-empty
        Write-Host "  Committed Step 7" -ForegroundColor Green
    }

    # ==========================================================================
    # STEP 8: Tests
    # ==========================================================================
    Write-Host "`n=== Step 8: Tests ===" -ForegroundColor Magenta
    
    $step8Files = @(
        "test_saw_lab_integration.py",                                      # Root level
        "test_saw_toolpath_builder.py",                                     # Root level
        "services/api/tests/test_saw_toolpath_builder.py",                  # services/api/tests
        "services/api/app/tests/test_saw_bridge_profiles_integration.py"   # app/tests
    )
    
    $step8Exists = @()
    foreach ($file in $step8Files) {
        $fullPath = Join-Path $RepoRoot $file
        if (Test-Path $fullPath) {
            $step8Exists += $file
            Write-Host "  [EXISTS] $file" -ForegroundColor Green
        } else {
            Write-Host "  [MISSING] $file" -ForegroundColor Yellow
        }
    }
    
    if ($step8Exists.Count -gt 0) {
        git add $step8Exists
        git commit -m "feat(saw-lab): Step 8 - Test suite" --allow-empty
        Write-Host "  Committed Step 8" -ForegroundColor Green
    }

    # ==========================================================================
    # Summary
    # ==========================================================================
    Write-Host "`n=== Commit Summary ===" -ForegroundColor Cyan
    Write-Host "Saw Lab commits completed on branch: $currentBranch" -ForegroundColor Green
    Write-Host ""
    Write-Host "Recent commits:" -ForegroundColor Yellow
    git log --oneline -8

} finally {
    Pop-Location
}

Write-Host "`n=== Done ===" -ForegroundColor Cyan
