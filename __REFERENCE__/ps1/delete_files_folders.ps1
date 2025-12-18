# Delete all "files (XX)" folders
$folders = Get-ChildItem -Directory | Where-Object { $_.Name -match '^files \(\d+\)$' }

Write-Host "Found $($folders.Count) 'files (XX)' folders to delete"

foreach ($f in $folders) {
    Remove-Item -Path $f.FullName -Recurse -Force
    Write-Host "[DELETED] $($f.Name)" -ForegroundColor Green
}

Write-Host "Done!"
