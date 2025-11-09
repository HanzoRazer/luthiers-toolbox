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

# Test 1: POST /cam/adaptive3/offset_spiral.nc - Basic arc generation
Write-Host "`n1. Testing POST /cam/adaptive3/offset_spiral.nc (G2/G3 arcs)" -ForegroundColor White

$body = @{
    boundary = @(
        @(0, 0), @(100, 0), @(100, 60), @(0, 60)
    )
    islands = @(
        @(@(30, 15), @(70, 15), @(70, 45), @(30, 45))
    )
    tool_d = 6.0
    stepover = 0.45
    stepdown = 1.5
    margin = 0.5
    feed_xy = 1200
    feed_z = 400
    safe_z = 5.0
    final_depth = -3.0
    use_arcs = $true
    feed_floor_pct = 0.75
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/cam/adaptive3/offset_spiral.nc" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body

    # Should be G-code text
    if ($response -match "G21" -and $response -match "G90") {
        Write-Host "  ✓ G-code generated" -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "  ✗ Invalid G-code format" -ForegroundColor Red
        $testsFailed++
    }

    # Check for G2/G3 commands
    if ($response -match "G2\s" -or $response -match "G3\s") {
        Write-Host "  ✓ G2/G3 arcs found" -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "  ✗ No G2/G3 arcs (use_arcs may not be working)" -ForegroundColor Red
        $testsFailed++
    }

    # Show first 15 lines
    Write-Host "`n  First 15 lines:" -ForegroundColor Gray
    $lines = $response -split "`n" | Select-Object -First 15
    foreach ($line in $lines) {
        Write-Host "    $line" -ForegroundColor DarkGray
    }

} catch {
    Write-Host "  ✗ Request failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# Test 2: No arcs mode (use_arcs=false)
Write-Host "`n2. Testing linear mode (use_arcs=false)" -ForegroundColor White

$bodyLinear = @{
    boundary = @(
        @(0, 0), @(50, 0), @(50, 30), @(0, 30)
    )
    islands = @()
    tool_d = 6.0
    stepover = 0.45
    stepdown = 1.5
    margin = 0.5
    feed_xy = 1200
    feed_z = 400
    safe_z = 5.0
    final_depth = -1.5
    use_arcs = $false
    feed_floor_pct = 0.80
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/cam/adaptive3/offset_spiral.nc" `
        -Method POST `
        -ContentType "application/json" `
        -Body $bodyLinear

    # Should have G1 but no G2/G3
    if ($response -match "G1\s" -and $response -notmatch "G2\s" -and $response -notmatch "G3\s") {
        Write-Host "  ✓ Linear moves only (no arcs)" -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "  ✗ Unexpected arc commands in linear mode" -ForegroundColor Red
        $testsFailed++
    }

} catch {
    Write-Host "  ✗ Request failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# Test 3: Feed floor validation
Write-Host "`n3. Testing feed floor commands" -ForegroundColor White

$bodyFeedFloor = @{
    boundary = @(
        @(0, 0), @(60, 0), @(60, 40), @(0, 40)
    )
    islands = @()
    tool_d = 6.0
    stepover = 0.50
    stepdown = 2.0
    margin = 0.5
    feed_xy = 1000
    feed_z = 300
    safe_z = 5.0
    final_depth = -6.0  # 3 passes
    use_arcs = $true
    feed_floor_pct = 0.60  # 60% of normal feed
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/cam/adaptive3/offset_spiral.nc" `
        -Method POST `
        -ContentType "application/json" `
        -Body $bodyFeedFloor

    # Should have multiple Z levels and feed reductions
    $feedCommands = ($response -split "`n" | Where-Object { $_ -match "F\d+" }).Count
    if ($feedCommands -gt 3) {
        Write-Host "  ✓ Feed floor commands present (multiple F values)" -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "  ✗ Feed floor commands missing" -ForegroundColor Red
        $testsFailed++
    }

    # Check for multiple Z depths
    $zCommands = ($response -split "`n" | Where-Object { $_ -match "Z-" }).Count
    if ($zCommands -ge 3) {
        Write-Host "  ✓ Multiple stepdown levels detected" -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "  ✗ Expected multiple Z levels" -ForegroundColor Red
        $testsFailed++
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
