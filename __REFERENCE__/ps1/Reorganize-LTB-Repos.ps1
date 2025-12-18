# Reorganize-LTB-Repos.ps1
# Moves spinoff repos out of the main Luthiers ToolBox folder
#
# IMPORTANT: Close VS Code before running this script!
#
# To run:
#   1. Open PowerShell as Administrator (right-click → Run as Administrator)
#   2. Navigate to your Downloads folder: cd "C:\Users\thepr\Downloads"
#   3. Run: .\Reorganize-LTB-Repos.ps1

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  Luthiers ToolBox Repo Reorganizer  " -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check if VS Code is running
$vscode = Get-Process -Name "Code" -ErrorAction SilentlyContinue
if ($vscode) {
    Write-Host "WARNING: VS Code is still running!" -ForegroundColor Red
    Write-Host "Please close VS Code and run this script again." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit
}

# Set the base path
$basePath = "C:\Users\thepr\Downloads"
$mainRepo = Join-Path $basePath "Luthiers ToolBox"

# Check if main folder exists
if (-not (Test-Path $mainRepo)) {
    Write-Host "ERROR: Could not find folder: $mainRepo" -ForegroundColor Red
    Write-Host "Please check the path and try again." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit
}

# List of spinoff repos to move
$spinoffs = @(
    "blueprint-reader",
    "guitar_tap",
    "ltb-bridge-designer",
    "ltb-enterprise",
    "ltb-express",
    "ltb-fingerboard-designer",
    "ltb-headstock-designer",
    "ltb-neck-designer",
    "ltb-parametric-guitar",
    "ltb-pro",
    "ltb-test-dummy"
)

Write-Host "Moving spinoff repos out of main folder..." -ForegroundColor Yellow
Write-Host ""

$moved = 0
$skipped = 0

foreach ($repo in $spinoffs) {
    $source = Join-Path $mainRepo $repo
    $dest = Join-Path $basePath $repo
    
    if (Test-Path $source) {
        if (Test-Path $dest) {
            Write-Host "  SKIP: $repo (already exists in Downloads)" -ForegroundColor Yellow
            $skipped++
        } else {
            Write-Host "  Moving: $repo" -ForegroundColor Green
            Move-Item -Path $source -Destination $dest
            $moved++
        }
    } else {
        Write-Host "  SKIP: $repo (not found in main folder)" -ForegroundColor Gray
        $skipped++
    }
}

Write-Host ""
Write-Host "--------------------------------------" -ForegroundColor Cyan

# Ask about renaming main folder
Write-Host ""
Write-Host "Optional: Rename 'Luthiers ToolBox' to 'luthiers-toolbox'?" -ForegroundColor Yellow
Write-Host "(Removes the space, matches GitHub naming convention)" -ForegroundColor Gray
$rename = Read-Host "Rename? (y/n)"

if ($rename -eq "y" -or $rename -eq "Y") {
    $newName = Join-Path $basePath "luthiers-toolbox"
    if (Test-Path $newName) {
        Write-Host "Cannot rename: 'luthiers-toolbox' folder already exists" -ForegroundColor Red
    } else {
        Rename-Item -Path $mainRepo -NewName "luthiers-toolbox"
        Write-Host "Renamed to: luthiers-toolbox" -ForegroundColor Green
        $mainRepo = $newName
    }
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  DONE!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Moved: $moved repos" -ForegroundColor Green
Write-Host "Skipped: $skipped repos" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Open VS Code" -ForegroundColor White
Write-Host "  2. File -> Open Folder" -ForegroundColor White
Write-Host "  3. Select: $mainRepo" -ForegroundColor White
Write-Host "  4. Ctrl+Shift+G to verify only ONE repo shows" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to exit"
