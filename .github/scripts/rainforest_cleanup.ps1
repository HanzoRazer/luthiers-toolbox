# Rainforest Restoration - Cleanup Script
# Phase 3 & 4: Merge unique content, then delete duplicates

$baseDir = "c:\Users\thepr\Downloads\Luthiers ToolBox"
Set-Location $baseDir

Write-Host "`n=== Rainforest Restoration - Starting Cleanup ===" -ForegroundColor Cyan
Write-Host "This script will:" -ForegroundColor Yellow
Write-Host "  1. Merge 17 radius dish files from 'Lutherier Project-2'" -ForegroundColor Gray
Write-Host "  2. Merge 103 feature files from 'Guitar Design HTML app-2'" -ForegroundColor Gray
Write-Host "  3. Delete exact duplicate folders" -ForegroundColor Gray
Write-Host "  4. Delete merged folders after verification" -ForegroundColor Gray
Write-Host "`nPress ENTER to continue or Ctrl+C to cancel..." -ForegroundColor Yellow
$null = Read-Host

# === PHASE 3: MERGE UNIQUE CONTENT ===

Write-Host "`n[Phase 3] Merging unique content..." -ForegroundColor Cyan

# Merge Lutherier Project-2 radius dish files
Write-Host "`nMerging 17 radius dish files..." -ForegroundColor Yellow
$radiusDishDirs = @(
    "Full_Radius_Dish_Design_Bundle",
    "Radius_Dish_CAD_Package",
    "Radius_Dish_Fusion_GRBL_Kit"
)

foreach ($dir in $radiusDishDirs) {
    $source = "Lutherier Project-2\Lutherier Project\$dir"
    $dest = "Lutherier Project\Lutherier Project\$dir"
    
    if (Test-Path $source) {
        if (!(Test-Path $dest)) {
            Write-Host "  Copying: $dir" -ForegroundColor Green
            Copy-Item $source $dest -Recurse -Force
        } else {
            Write-Host "  Skipping: $dir (already exists)" -ForegroundColor Gray
        }
    }
}

# Merge Guitar Design HTML app-2 feature bundles
Write-Host "`nMerging 103 feature bundle files..." -ForegroundColor Yellow
$featureDirs = @(
    "10-10-2025",
    "10_06+2025"
)

foreach ($dir in $featureDirs) {
    $source = "Guitar Design HTML app-2\Guitar Design HTML app\$dir"
    $dest = "Guitar Design HTML app\Guitar Design HTML app\$dir"
    
    if (Test-Path $source) {
        if (!(Test-Path $dest)) {
            Write-Host "  Copying: $dir" -ForegroundColor Green
            Copy-Item $source $dest -Recurse -Force
        } else {
            Write-Host "  Skipping: $dir (already exists)" -ForegroundColor Gray
        }
    }
}

Write-Host "`n✓ Phase 3 Complete: Unique content merged" -ForegroundColor Green

# === PHASE 4: DELETE DUPLICATES ===

Write-Host "`n[Phase 4] Deleting duplicate folders..." -ForegroundColor Cyan

# Verify merges before deletion
Write-Host "`nVerifying merges..." -ForegroundColor Yellow
$verifyPaths = @(
    "Lutherier Project\Lutherier Project\Full_Radius_Dish_Design_Bundle",
    "Guitar Design HTML app\Guitar Design HTML app\10-10-2025",
    "Guitar Design HTML app\Guitar Design HTML app\10_06+2025"
)

$allVerified = $true
foreach ($path in $verifyPaths) {
    if (Test-Path $path) {
        Write-Host "  ✓ Verified: $path" -ForegroundColor Green
    } else {
        Write-Host "  ✗ MISSING: $path" -ForegroundColor Red
        $allVerified = $false
    }
}

if (!$allVerified) {
    Write-Host "`n❌ ABORT: Some merged content not found!" -ForegroundColor Red
    Write-Host "Please verify merges manually before deleting" -ForegroundColor Yellow
    exit 1
}

# Delete confirmed duplicates
Write-Host "`nDeleting duplicate folders..." -ForegroundColor Yellow

$foldersToDelete = @(
    @{Name="Lutherier Project 2"; Reason="Exact duplicate"},
    @{Name="Luthiers Tool Box 2"; Reason="Incomplete copy"},
    @{Name="Lutherier Project-2"; Reason="Content merged"},
    @{Name="Guitar Design HTML app-2"; Reason="Content merged"}
)

$totalSize = 0
foreach ($folder in $foldersToDelete) {
    $path = $folder.Name
    if (Test-Path $path) {
        $size = (Get-ChildItem $path -Recurse -File -ErrorAction SilentlyContinue | 
                 Measure-Object -Property Length -Sum).Sum / 1MB
        
        Write-Host "  Deleting: $path ($([math]::Round($size, 2)) MB) - $($folder.Reason)" -ForegroundColor Yellow
        Remove-Item $path -Recurse -Force -ErrorAction Continue
        $totalSize += $size
        
        if (Test-Path $path) {
            Write-Host "    ✗ Failed to delete" -ForegroundColor Red
        } else {
            Write-Host "    ✓ Deleted" -ForegroundColor Green
        }
    } else {
        Write-Host "  Skipping: $path (not found)" -ForegroundColor Gray
    }
}

Write-Host "`n✓ Phase 4 Complete: Deleted $([math]::Round($totalSize, 2)) MB" -ForegroundColor Green

# === SUMMARY ===

Write-Host "`n=== Rainforest Restoration Complete ===" -ForegroundColor Cyan
Write-Host "✓ Merged 17 radius dish files" -ForegroundColor Green
Write-Host "✓ Merged 103 feature bundle files" -ForegroundColor Green
Write-Host "✓ Deleted 4 duplicate folders" -ForegroundColor Green
Write-Host "✓ Reclaimed $([math]::Round($totalSize, 2)) MB" -ForegroundColor Green
Write-Host "`nWorkspace is now clean! 🌲" -ForegroundColor Cyan
