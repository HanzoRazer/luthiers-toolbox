# Test BackplotGcode.vue (N15) Backend
# Verifies gcode_backplot_router endpoints are working

$ErrorActionPreference = "Stop"

Write-Host "=== Testing N15 Backplot Backend ===" -ForegroundColor Cyan

$baseUrl = "http://localhost:8000"

# Test G-code
$testGcode = @"
G21
G90
G0 X0 Y0 Z5
G0 X10 Y0
G1 Z-1.5 F300
G1 X10 Y10 F1200
G1 X0 Y10
G1 X0 Y0
G0 Z5
M30
"@

# 1. Test /api/cam/gcode/plot.svg
Write-Host "`n1. Testing POST /api/cam/gcode/plot.svg" -ForegroundColor Yellow
try {
    $plotBody = @{
        gcode = $testGcode
        units = "mm"
        stroke = "blue"
    } | ConvertTo-Json

    $svg = Invoke-RestMethod -Method Post `
        -Uri "$baseUrl/api/cam/gcode/plot.svg" `
        -Body $plotBody `
        -ContentType "application/json"

    if ($svg -match "<svg") {
        Write-Host "  ✓ SVG generated successfully" -ForegroundColor Green
        Write-Host "  SVG length: $($svg.Length) characters" -ForegroundColor Gray
    } else {
        Write-Host "  ✗ Invalid SVG response" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  ✗ Failed: $_" -ForegroundColor Red
    exit 1
}

# 2. Test /api/cam/gcode/estimate
Write-Host "`n2. Testing POST /api/cam/gcode/estimate" -ForegroundColor Yellow
try {
    $estimateBody = @{
        gcode = $testGcode
        units = "mm"
        rapid_mm_min = 3000.0
        default_feed_mm_min = 500.0
    } | ConvertTo-Json

    $estimate = Invoke-RestMethod -Method Post `
        -Uri "$baseUrl/api/cam/gcode/estimate" `
        -Body $estimateBody `
        -ContentType "application/json"

    Write-Host "  ✓ Estimate successful" -ForegroundColor Green
    Write-Host "  Travel: $([math]::Round($estimate.travel_mm, 2)) mm" -ForegroundColor Gray
    Write-Host "  Cutting: $([math]::Round($estimate.cut_mm, 2)) mm" -ForegroundColor Gray
    Write-Host "  Total time: $([math]::Round($estimate.t_total_min * 60, 2)) seconds" -ForegroundColor Gray
    Write-Host "  Points: $($estimate.points_xy.Count)" -ForegroundColor Gray

    # Validate expected fields
    $required = @('travel_mm', 'cut_mm', 't_rapid_min', 't_feed_min', 't_total_min', 'points_xy')
    $missing = $required | Where-Object { -not $estimate.PSObject.Properties[$_] }
    
    if ($missing.Count -gt 0) {
        Write-Host "  ✗ Missing fields: $($missing -join ', ')" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  ✗ Failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== All N15 Backend Tests Passed ===" -ForegroundColor Green
Write-Host "`nNext: Run 'cd client && npm run dev' to test the Vue component" -ForegroundColor Cyan
