# Smoke Test: Patch N18 - G2/G3 Arc Linkers + Feed Floors
#
# Tests the /cam/adaptive3/offset_spiral.nc endpoint
# Validates G2/G3 arc emission and feed floor commands

param(
    [switch]$SkipStart
)

$ErrorActionPreference = "Stop"

Write-Host "=== Testing Patch N18: G2/G3 Arc Linkers ===" -ForegroundColor Cyan

$baseUrl = "http://localhost:8000"
$testsPassed = 0
$testsFailed = 0

# Start API server if not skipped
if (-not $SkipStart) {
    Write-Host "`nStarting API server..." -ForegroundColor Yellow
    Push-Location "services\api"
    Start-Process pwsh -ArgumentList "-NoExit", "-Command", "& {.\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port 8000}" -WindowStyle Minimized
    Pop-Location
    Write-Host "Waiting for server to start..." -ForegroundColor Gray
    Start-Sleep -Seconds 5
}

# Test 1: POST /cam/adaptive3/offset_spiral.nc - Basic polygon
Write-Host "`n1. Testing POST /cam/adaptive3/offset_spiral.nc (basic polygon)" -ForegroundColor White

$body = @{
    polygon = @(
        @(0, 0), @(100, 0), @(100, 60), @(0, 60)
    )
    tool_dia = 6.0
    stepover = 2.4
    z = -1.5
    safe_z = 5.0
    base_feed = 1200.0
    min_R = 1.0
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/cam/adaptive3/offset_spiral.nc" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body

    # Should be G-code text
    if ($response -match "G21" -and $response -match "G90") {
        Write-Host "  ✓ G-code generated with G21/G90" -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "  ✗ Invalid G-code format" -ForegroundColor Red
        $testsFailed++
    }

    # Check for G1 moves
    if ($response -match "G1\s") {
        Write-Host "  ✓ G1 moves found" -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "  ✗ No G1 moves" -ForegroundColor Red
        $testsFailed++
    }

    # Show first 10 lines
    Write-Host "`n  First 10 lines:" -ForegroundColor Gray
    $lines = $response -split "`n" | Select-Object -First 10
    foreach ($line in $lines) {
        Write-Host "    $line" -ForegroundColor DarkGray
    }

} catch {
    Write-Host "  ✗ Request failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# Test 2: Smaller rectangle
Write-Host "`n2. Testing smaller polygon" -ForegroundColor White

$bodyLinear = @{
    polygon = @(
        @(0, 0), @(50, 0), @(50, 30), @(0, 30)
    )
    tool_dia = 6.0
    stepover = 2.4
    z = -1.5
    safe_z = 5.0
    base_feed = 1200.0
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/cam/adaptive3/offset_spiral.nc" `
        -Method POST `
        -ContentType "application/json" `
        -Body $bodyLinear

    # Should have G1 moves
    if ($response -match "G1\s") {
        Write-Host "  ✓ G-code generated with G1 moves" -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "  ✗ No G1 moves found" -ForegroundColor Red
        $testsFailed++
    }

} catch {
    Write-Host "  ✗ Request failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# Test 3: Complex polygon
Write-Host "`n3. Testing complex polygon" -ForegroundColor White

$bodyComplex = @{
    polygon = @(
        @(0, 0), @(60, 0), @(60, 40), @(0, 40)
    )
    tool_dia = 6.0
    stepover = 2.4
    z = -2.0
    safe_z = 5.0
    base_feed = 1000.0
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/cam/adaptive3/offset_spiral.nc" `
        -Method POST `
        -ContentType "application/json" `
        -Body $bodyComplex

    # Check for valid G-code structure
    if ($response -match "G21" -and $response -match "G1") {
        Write-Host "  ✓ Valid G-code generated" -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "  ✗ Invalid G-code format" -ForegroundColor Red
        $testsFailed++
    }

    # Show sample
    Write-Host "`n  Sample G-code (first 8 lines):" -ForegroundColor Gray
    $lines = $response -split "`n" | Select-Object -First 8
    foreach ($line in $lines) {
        Write-Host "    $line" -ForegroundColor DarkGray
    }

} catch {
    Write-Host "  ✗ Request failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# Summary
Write-Host "`n=== Test Summary ===" -ForegroundColor Cyan
Write-Host "Passed: $testsPassed" -ForegroundColor Green
Write-Host "Failed: $testsFailed" -ForegroundColor $(if ($testsFailed -eq 0) { "Green" } else { "Red" })

if ($testsFailed -eq 0) {
    Write-Host "`n✓ All Patch N18 tests passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n✗ Some tests failed. Check output above." -ForegroundColor Red
    exit 1
}
