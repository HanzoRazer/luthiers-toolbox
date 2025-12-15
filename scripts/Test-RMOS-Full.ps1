param(
    [string]$BaseUrl = "http://localhost:8000/rmos",
    [switch]$Verbose
)

Write-Host "=== RMOS FULL SMOKE SUITE ==="
Write-Host "Base URL:" $BaseUrl
Write-Host ""

function Write-Ok($msg) { Write-Host "[ OK ]" $msg -ForegroundColor Green }
function Write-Err($msg) { Write-Host "[ERR]" $msg -ForegroundColor Red }

try {
    # Test 1: Manufacturing + batch (previous script)
    . "$PSScriptRoot\Test-RMOS-Sandbox.ps1" -BaseUrl $BaseUrl -Verbose:$Verbose

    # Test 2: Single-slice preview
    . "$PSScriptRoot\Test-RMOS-SlicePreview.ps1" -BaseUrl $BaseUrl -Verbose:$Verbose

    Write-Ok "RMOS FULL SMOKE SUITE COMPLETED."
    exit 0
}
catch {
    Write-Err "RMOS FULL SMOKE SUITE FAILED."
    Write-Err $_.Exception.Message
    exit 1
}
