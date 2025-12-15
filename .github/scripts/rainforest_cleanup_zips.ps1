# Rainforest Restoration - Phase 5: ZIP Archive Cleanup
# Delete extracted ZIP archives to reduce clutter

$baseDir = "c:\Users\thepr\Downloads\Luthiers ToolBox"
Set-Location $baseDir

Write-Host "`n=== Phase 5: ZIP Archive Cleanup ===" -ForegroundColor Cyan
Write-Host "This script will delete ZIP files that have been extracted." -ForegroundColor Yellow
Write-Host "`nPress ENTER to continue or Ctrl+C to cancel..." -ForegroundColor Yellow
$null = Read-Host

# Find all ZIPs with extracted folders
Write-Host "`nScanning for extracted ZIPs..." -ForegroundColor Yellow

$zipsToDelete = Get-ChildItem -Filter "*.zip" -File | Where-Object {
    $extractedFolder = $_.FullName -replace '\.zip$', ''
    Test-Path $extractedFolder
}

if ($zipsToDelete.Count -eq 0) {
    Write-Host "No extracted ZIPs found to delete." -ForegroundColor Gray
    exit 0
}

Write-Host "`nFound $($zipsToDelete.Count) extracted ZIPs:" -ForegroundColor Cyan
$zipsToDelete | ForEach-Object {
    $sizeMB = [math]::Round($_.Length / 1MB, 2)
    Write-Host "  $($_.Name) ($sizeMB MB)" -ForegroundColor Gray
}

# Verify extracted folders exist
Write-Host "`nVerifying extracted folders..." -ForegroundColor Yellow
$allVerified = $true
foreach ($zip in $zipsToDelete) {
    $extractedFolder = $zip.FullName -replace '\.zip$', ''
    if (Test-Path $extractedFolder) {
        Write-Host "  ✓ Folder exists for: $($zip.Name)" -ForegroundColor Green
    } else {
        Write-Host "  ✗ MISSING folder for: $($zip.Name)" -ForegroundColor Red
        $allVerified = $false
    }
}

if (!$allVerified) {
    Write-Host "`n❌ ABORT: Some extracted folders not found!" -ForegroundColor Red
    exit 1
}

# Delete ZIPs
Write-Host "`nDeleting extracted ZIP files..." -ForegroundColor Yellow
$totalSize = 0

foreach ($zip in $zipsToDelete) {
    $sizeMB = $zip.Length / 1MB
    Write-Host "  Deleting: $($zip.Name)" -ForegroundColor Yellow
    
    try {
        Remove-Item $zip.FullName -Force
        $totalSize += $sizeMB
        Write-Host "    ✓ Deleted" -ForegroundColor Green
    } catch {
        Write-Host "    ✗ Failed: $_" -ForegroundColor Red
    }
}

# Summary
Write-Host "`n=== Phase 5 Complete ===" -ForegroundColor Cyan
Write-Host "✓ Deleted $($zipsToDelete.Count) ZIP archives" -ForegroundColor Green
Write-Host "✓ Reclaimed $([math]::Round($totalSize, 2)) MB" -ForegroundColor Green
Write-Host "✓ Extracted folders preserved" -ForegroundColor Green

# Keep track for final summary
Write-Host "`nNote: v8 and v9_env_patch ZIPs kept (not extracted)" -ForegroundColor Gray
