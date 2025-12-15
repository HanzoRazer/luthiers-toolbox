Here’s a ready-to-use PowerShell script you can drop into your repo to commit the Saw Lab files in the correct order.

Save this as (for example):

commit_saw_lab.ps1 in the root of your Luthiers ToolBox repo.

<#
    commit_saw_lab.ps1

    Purpose:
      Stage and commit Saw Lab 2.0 files in a safe dependency order:

        1) Data (JSON)
        2) Calculators
        3) Models / Types
        4) saw_bridge adapter
        5) Path planner(s)
        6) Toolpath builder
        7) Router(s)
        8) Tests

    Usage:
      1. Open a PowerShell window in the repo root.
      2. Run:
           .\commit_saw_lab.ps1
         or dry-run:
           .\commit_saw_lab.ps1 -DryRun

      Optional:
        .\commit_saw_lab.ps1 -BranchName "feature/saw-lab-2-0"
#>

param(
    [switch]$DryRun,
    [string]$BranchName = "feature/saw-lab-2-0"
)

# ---------------------------
# Helper functions
# ---------------------------

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "==============================="
    Write-Host $Text
    Write-Host "==============================="
}

function Assert-GitAvailable {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Error "git is not available in PATH. Install git or open a Developer PowerShell with git."
        exit 1
    }
}

function Assert-GitRepo {
    if (-not (Test-Path ".git")) {
        Write-Error "This script must be run from the root of a git repository (where .git folder lives)."
        exit 1
    }
}

function Ensure-Branch {
    param([string]$Name)

    $current = git rev-parse --abbrev-ref HEAD 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Unable to detect current git branch."
        exit 1
    }

    if ($current -eq $Name) {
        Write-Host "Already on branch '$Name'."
        return
    }

    $exists = git branch --list $Name 2>$null
    if ($exists) {
        Write-Host "Switching to existing branch '$Name'..."
        git checkout $Name
    }
    else {
        Write-Host "Creating and switching to new branch '$Name'..."
        git checkout -b $Name
    }
}

function Stage-StepFiles {
    param(
        [string]$StepName,
        [string[]]$Files
    )

    Write-Header "STEP: $StepName"

    if (-not $Files -or $Files.Count -eq 0) {
        Write-Host "  (No files listed for this step.)"
        return
    }

    $existing = @()
    $missing  = @()

    foreach ($f in $Files) {
        if (Test-Path $f) {
            $existing += $f
        }
        else {
            $missing += $f
        }
    }

    if ($missing.Count -gt 0) {
        Write-Warning "Some files for this step were NOT found:"
        $missing | ForEach-Object { Write-Warning "  MISSING: $_" }
    }

    if ($existing.Count -eq 0) {
        Write-Host "No existing files to stage for this step."
        return
    }

    if ($DryRun) {
        Write-Host "Dry run: would stage files:"
        $existing | ForEach-Object { Write-Host "  $_" }
    }
    else {
        Write-Host "Staging files:"
        $existing | ForEach-Object { Write-Host "  $_" }
        git add @existing
    }
}

function Commit-Step {
    param(
        [string]$Message
    )

    if ($DryRun) {
        Write-Host "Dry run: would commit with message:"
        Write-Host "  $Message"
        return
    }

    $status = git status --porcelain
    if (-not $status) {
        Write-Host "No changes staged for this step; skipping commit."
        return
    }

    Write-Host "Committing..."
    git commit -m $Message
}

# ---------------------------
# Main
# ---------------------------

Write-Header "Saw Lab 2.0 Commit Script"

Assert-GitAvailable
Assert-GitRepo
Ensure-Branch -Name $BranchName

if ($DryRun) {
    Write-Host "Running in DRY-RUN mode. No files will actually be staged or committed."
}

# Define steps as an ordered list
$steps = @(
    @{
        Name    = "Step 1 – Saw Lab data (JSON: blades/materials/presets)";
        Files   = @(
            "services/api/app/data/saw_lab_blades.json",
            "services/api/app/data/saw_lab_materials.json",
            "services/api/app/data/saw_lab_presets.json"
        );
        Commit  = "feat(saw-lab): add Saw Lab blade/material data files"
    },
    @{
        Name    = "Step 2 – Saw Lab calculators (rim speed, bite, heat, deflection, kickback)";
        Files   = @(
            "services/api/app/saw_lab/calculators/rim_speed.py",
            "services/api/app/saw_lab/calculators/bite_per_tooth.py",
            "services/api/app/saw_lab/calculators/heat_model.py",
            "services/api/app/saw_lab/calculators/deflection_model.py",
            "services/api/app/saw_lab/calculators/kickback_model.py",
            "services/api/app/saw_lab/calculators/common.py"
        );
        Commit  = "feat(saw-lab): add Saw Lab physics calculator modules"
    },
    @{
        Name    = "Step 3 – Saw Lab models and types";
        Files   = @(
            "services/api/app/saw_lab/models.py",
            "services/api/app/saw_lab/types.py"
        );
        Commit  = "feat(saw-lab): add Saw Lab models and types"
    },
    @{
        Name    = "Step 4 – saw_bridge adapter (RMOS ↔ Saw Lab)";
        Files   = @(
            "services/api/app/calculators/saw_bridge.py"
        );
        Commit  = "feat(saw-lab): wire Saw Lab physics via saw_bridge adapter"
    },
    @{
        Name    = "Step 5 – Saw Lab path planner(s)";
        Files   = @(
            "services/api/app/saw_lab/path_planner.py",
            "services/api/app/saw_lab/path_planner_2_1.py",
            "services/api/app/saw_lab/config.py"
        );
        Commit  = "feat(saw-lab): add Saw Lab path planners and config"
    },
    @{
        Name    = "Step 6 – Saw Lab toolpath builder / operations";
        Files   = @(
            "services/api/app/saw_lab/toolpath_builder.py",
            "services/api/app/saw_lab/operations.py"
        );
        Commit  = "feat(saw-lab): add Saw Lab toolpath builder and operations"
    },
    @{
        Name    = "Step 7 – Saw Lab router(s)";
        Files   = @(
            "services/api/app/routers/saw_lab_router.py"
        );
        Commit  = "feat(saw-lab): expose Saw Lab API router"
    },
    @{
        Name    = "Step 8 – Saw Lab tests";
        Files   = @(
            "services/api/app/tests/saw_lab/test_rim_speed.py",
            "services/api/app/tests/saw_lab/test_bite_model.py",
            "services/api/app/tests/saw_lab/test_heat_model.py",
            "services/api/app/tests/saw_lab/test_deflection_model.py",
            "services/api/app/tests/saw_lab/test_kickback_model.py",
            "services/api/app/tests/saw_lab/test_path_planner_single_board.py"
        );
        Commit  = "test(saw-lab): add Saw Lab physics and planner tests"
    }
)

foreach ($step in $steps) {
    Stage-StepFiles -StepName $step.Name -Files $step.Files
    Commit-Step -Message $step.Commit
}

Write-Header "Saw Lab 2.0 Commit Script finished"

if ($DryRun) {
    Write-Host "Dry run complete. Review staged file list above, then rerun without -DryRun when ready."
}
else {
    Write-Host "All steps processed. Run 'git log --oneline' to review commits."
}

How to use this script

Put commit_saw_lab.ps1 in the root of your repo (same level as .git).

In PowerShell:

cd "C:\Users\thepr\Downloads\Luthiers ToolBox"
.\commit_saw_lab.ps1 -DryRun   # to see what it would do
.\commit_saw_lab.ps1           # to actually stage + commit


If some files aren’t ready yet, the script will show them as MISSING and skip them for that step (so you can still commit partial pieces in order).

If you want to tweak any filenames (for example if you renamed path_planner_2_1.py), just edit the arrays in $steps to match your real paths.