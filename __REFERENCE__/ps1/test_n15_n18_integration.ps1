# N15-N18 Frontend Integration Test Script
# Tests all 4 CAM toolbox components via backend smoke tests
# Date: November 17, 2025

$ErrorActionPreference = "Stop"

Write-Host "`n=== N15-N18 Frontend Integration Smoke Tests ===" -ForegroundColor Cyan
Write-Host "Testing backend APIs for all CAM toolbox components`n" -ForegroundColor Gray

$baseUrl = "http://localhost:8000"
$passed = 0
$failed = 0

# Test helper function
function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Endpoint,
        [hashtable]$Body,
        [string]$ExpectedContent = $null
    )
    
    Write-Host "Testing: $Name" -ForegroundColor Yellow
    
    try {
        $response = Invoke-RestMethod -Uri "$baseUrl$Endpoint" `
            -Method Post `
            -ContentType "application/json" `
            -Body ($Body | ConvertTo-Json -Depth 10)
        
        if ($ExpectedContent -and $response -notmatch $ExpectedContent) {
            Write-Host "  ✗ FAILED: Expected content not found" -ForegroundColor Red
            $script:failed++
        } else {
            Write-Host "  ✓ PASSED" -ForegroundColor Green
            $script:passed++
        }
    } catch {
        Write-Host "  ✗ FAILED: $($_.Exception.Message)" -ForegroundColor Red
        $script:failed++
    }
}

# ============================================================================
# N15: G-code Backplot Tests
# ============================================================================

Write-Host "`n--- N15: G-code Backplot & Estimation ---" -ForegroundColor Cyan

# Test 1: Simple G-code backplot
Test-Endpoint -Name "N15 Backplot SVG Generation" `
    -Endpoint "/api/cam/gcode/plot.svg" `
    -Body @{
        gcode = @"
G21
G90
G0 X0 Y0
G1 X50 Y0 F1200
G1 X50 Y30 F1200
G1 X0 Y30 F1200
G1 X0 Y0 F1200
M30
"@
        units = "mm"
    } `
    -ExpectedContent "svg"

# Test 2: G-code time estimation
$estimateResponse = Invoke-RestMethod -Uri "$baseUrl/api/cam/gcode/estimate" `
    -Method Post `
    -ContentType "application/json" `
    -Body (@{
        gcode = "G21`nG90`nG0 X0 Y0`nG1 X100 Y0 F1200`nM30"
        units = "mm"
    } | ConvertTo-Json)

Write-Host "Testing: N15 Time Estimation" -ForegroundColor Yellow
if ($estimateResponse.travel_mm -gt 0 -and $estimateResponse.t_total_min -gt 0) {
    Write-Host "  ✓ PASSED (Travel: $($estimateResponse.travel_mm)mm, Time: $($estimateResponse.t_total_min)min)" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ✗ FAILED: Invalid response structure" -ForegroundColor Red
    $failed++
}

# ============================================================================
# N16: Adaptive Benchmark Tests
# ============================================================================

Write-Host "`n--- N16: Adaptive Kernel Benchmark ---" -ForegroundColor Cyan

# Test 3: Offset spiral benchmark
Test-Endpoint -Name "N16 Offset Spiral" `
    -Endpoint "/cam/adaptive2/offset_spiral.svg" `
    -Body @{
        width = 100
        height = 60
        tool_dia = 6.0
        stepover = 2.4
        corner_fillet = 0.0
    } `
    -ExpectedContent "svg"

# Test 4: Trochoid corners benchmark
Test-Endpoint -Name "N16 Trochoid Corners" `
    -Endpoint "/cam/adaptive2/trochoid_corners.svg" `
    -Body @{
        width = 100
        height = 60
        tool_dia = 6.0
        loop_pitch = 2.5
        amp = 0.4
    } `
    -ExpectedContent "svg"

# ============================================================================
# N17: Polygon Offset Tests
# ============================================================================

Write-Host "`n--- N17: Polygon Offset (Pyclipper) ---" -ForegroundColor Cyan

# Test 5: Polygon offset preview
$polygonPreview = Invoke-RestMethod -Uri "$baseUrl/cam/polygon_offset.preview" `
    -Method Post `
    -ContentType "application/json" `
    -Body (@{
        polygon = @(@(0,0), @(100,0), @(100,60), @(0,60))
        tool_dia = 6.0
        stepover = 0.4
        link_mode = "arc"
        units = "mm"
    } | ConvertTo-Json -Depth 10)

Write-Host "Testing: N17 Polygon Offset Preview" -ForegroundColor Yellow
if ($polygonPreview.passes -and $polygonPreview.passes.Count -gt 0) {
    Write-Host "  ✓ PASSED (Passes: $($polygonPreview.passes.Count), Points: $($polygonPreview.meta.total_points))" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ✗ FAILED: No offset passes generated" -ForegroundColor Red
    $failed++
}

# Test 6: Polygon offset G-code
Test-Endpoint -Name "N17 Polygon Offset G-code" `
    -Endpoint "/cam/polygon_offset.nc" `
    -Body @{
        polygon = @(@(0,0), @(100,0), @(100,60), @(0,60))
        tool_dia = 6.0
        stepover = 0.4
        link_mode = "linear"
        units = "mm"
    } `
    -ExpectedContent "G21"

# ============================================================================
# N18: Adaptive Spiral Tests
# ============================================================================

Write-Host "`n--- N18: Adaptive Spiral with Arc Linker ---" -ForegroundColor Cyan

# Test 7: Adaptive spiral G-code
Test-Endpoint -Name "N18 Spiral G-code Generation" `
    -Endpoint "/cam/adaptive3/offset_spiral.nc" `
    -Body @{
        polygon = @(@(0,0), @(100,0), @(100,60), @(0,60))
        tool_dia = 6.0
        stepover = 2.4
        z = -1.5
        safe_z = 5.0
        base_feed = 1200.0
        units = "mm"
    } `
    -ExpectedContent "G90"

# ============================================================================
# Summary
# ============================================================================

Write-Host "`n=== Test Results Summary ===" -ForegroundColor Cyan
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor Red

if ($failed -eq 0) {
    Write-Host "`n✓ All N15-N18 backend endpoints validated!" -ForegroundColor Green
    Write-Host "Frontend components ready for integration." -ForegroundColor Gray
    exit 0
} else {
    Write-Host "`n✗ Some tests failed. Check backend server status." -ForegroundColor Red
    exit 1
}
