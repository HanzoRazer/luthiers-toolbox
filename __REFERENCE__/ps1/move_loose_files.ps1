# Move loose files (.txt, .ps1, .py) to __REFERENCE__ with their own folders
$ErrorActionPreference = "Stop"

# Create target directories
$targets = @("__REFERENCE__\txt", "__REFERENCE__\ps1", "__REFERENCE__\py")
foreach ($t in $targets) {
    if (-not (Test-Path $t)) {
        New-Item -ItemType Directory -Path $t | Out-Null
        Write-Host "Created $t/" -ForegroundColor Cyan
    }
}

# Move .txt files
$txtFiles = Get-ChildItem -File -Filter "*.txt"
$txtCount = 0
foreach ($f in $txtFiles) {
    Move-Item -Path $f.FullName -Destination "__REFERENCE__\txt\" -Force
    $txtCount++
}
Write-Host "[MOVED] $txtCount .txt files to __REFERENCE__/txt/" -ForegroundColor Green

# Move .ps1 files
$ps1Files = Get-ChildItem -File -Filter "*.ps1"
$ps1Count = 0
foreach ($f in $ps1Files) {
    Move-Item -Path $f.FullName -Destination "__REFERENCE__\ps1\" -Force
    $ps1Count++
}
Write-Host "[MOVED] $ps1Count .ps1 files to __REFERENCE__/ps1/" -ForegroundColor Green

# Move .py files
$pyFiles = Get-ChildItem -File -Filter "*.py"
$pyCount = 0
foreach ($f in $pyFiles) {
    Move-Item -Path $f.FullName -Destination "__REFERENCE__\py\" -Force
    $pyCount++
}
Write-Host "[MOVED] $pyCount .py files to __REFERENCE__/py/" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  .txt files moved: $txtCount"
Write-Host "  .ps1 files moved: $ps1Count"
Write-Host "  .py files moved:  $pyCount"
Write-Host "  Total: $($txtCount + $ps1Count + $pyCount)"
