# Show what's left at root level
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ROOT LEVEL FOLDERS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Get-ChildItem -Directory | ForEach-Object {
    $count = (Get-ChildItem -Path $_.FullName -Recurse -File -ErrorAction SilentlyContinue).Count
    Write-Host ("  {0,-40} ({1,5} files)" -f $_.Name, $count)
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ROOT LEVEL FILES (by type)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
$files = Get-ChildItem -File
$byExt = $files | Group-Object Extension | Sort-Object Count -Descending
foreach ($g in $byExt) {
    $ext = if ($g.Name -eq "") { "(no ext)" } else { $g.Name }
    Write-Host ""
    Write-Host "$ext - $($g.Count) files:" -ForegroundColor Yellow
    foreach ($f in $g.Group) {
        Write-Host "  $($f.Name)" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Folders: $((Get-ChildItem -Directory).Count)"
Write-Host "  Files:   $((Get-ChildItem -File).Count)"
