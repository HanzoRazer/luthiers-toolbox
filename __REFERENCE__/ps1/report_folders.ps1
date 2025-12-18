# Report remaining top-level folders
$dirs = Get-ChildItem -Directory | Where-Object { $_.Name -notlike '.*' }
Write-Host "Remaining folders: $($dirs.Count)"
Write-Host ""
foreach ($d in $dirs) {
    Write-Host $d.Name
}
