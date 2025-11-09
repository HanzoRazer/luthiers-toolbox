$addDir = Join-Path (Get-Location) "wirein\add"

if (-Not (Test-Path $addDir)) {
    Write-Error "Error: wirein\add directory not found"
    Write-Host "Usage: Create wirein\add\ with files to copy, then run this script"
    exit 1
}

Write-Host "Copying files from wirein\add\ to repository root..."
robocopy $addDir (Get-Location) /E /NFL /NDL /NJH /NJS /NP | Out-Null

if ($LastExitCode -lt 8) {
    Write-Host "✓ Done. Now run:"
    Write-Host "  git add ."
    Write-Host "  git commit -m 'feat: wire-in packages/ + services/api'"
} else {
    throw "robocopy failed with exit code: $LastExitCode"
}
