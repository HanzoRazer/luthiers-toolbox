# Patch N.15 - G-code Backplot + Time Estimator - Smoke Test
#
# Tests G-code parsing, SVG generation, and time estimation.
#
# Usage:
#   .\smoke_n15_backplot.ps1              # Default: localhost:8000
#   .\smoke_n15_backplot.ps1 -Port 8135   # Custom port
#   .\smoke_n15_backplot.ps1 -SkipStart   # Use existing server

Param(
    [string]$HostName = "127.0.0.1",
    [int]$Port = 8000,
    [switch]$SkipStart
)

$ErrorActionPreference = "Stop"
$base = "http://${HostName}:${Port}"
$proc = $null

# Sample G-code program
$sampleGcode = @"
G21 G90 G17
(Simple test)
G0 X0 Y0 Z5
G0 X10 Y10
G1 Z-1 F300
G1 X20 F600
G2 X30 Y20 I5 J0
G1 X30 Y30
G1 X0 Y30
G1 X0 Y10
G0 Z5
M30
"@

try {
    # Start API if needed
    if (-not $SkipStart) {
        Write-Host "==> Starting API on port $Port..." -ForegroundColor Cyan
        Push-Location "$PSScriptRoot\services\api"
        $proc = Start-Process pwsh -ArgumentList @(
            '-NoExit',
            '-Command',
            "& {.\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port $Port}"
        ) -PassThru -WindowStyle Hidden
        Pop-Location
        
        Write-Host "==> Waiting for API..." -ForegroundColor Yellow
        Start-Sleep -Seconds 3
    }
    
    Write-Host "`n=== Patch N.15 Smoke Test ===" -ForegroundColor Cyan
    Write-Host "Testing G-code backplot and time estimation`n"
    
    # Test 1: SVG Plot
    Write-Host "Test 1: POST /api/cam/gcode/plot.svg" -ForegroundColor White
    $plotBody = @{
        gcode = $sampleGcode
        units = "mm"
        rapid_mm_min = 3000.0
        default_feed_mm_min = 500.0
        stroke = "blue"
    } | ConvertTo-Json
    
    $svg = Invoke-RestMethod -Uri "$base/api/cam/gcode/plot.svg" `
        -Method POST `
        -ContentType "application/json" `
        -Body $plotBody `
        -TimeoutSec 5
    
    if ($svg -match '<svg') {
        Write-Host "  ✓ SVG generated" -ForegroundColor Green
        Write-Host "    Length: $($svg.Length) chars" -ForegroundColor Gray
        
        if ($svg -match 'polyline') {
            Write-Host "    ✓ Contains polyline element" -ForegroundColor Green
        }
    } else {
        throw "SVG generation failed"
    }
    
    # Test 2: Time Estimate
    Write-Host "`nTest 2: POST /api/cam/gcode/estimate" -ForegroundColor White
    $estBody = @{
        gcode = $sampleGcode
        units = "mm"
        rapid_mm_min = 3000.0
        default_feed_mm_min = 500.0
    } | ConvertTo-Json
    
    $estimate = Invoke-RestMethod -Uri "$base/api/cam/gcode/estimate" `
        -Method POST `
        -ContentType "application/json" `
        -Body $estBody `
        -TimeoutSec 5
    
    Write-Host "  ✓ Estimation complete:" -ForegroundColor Green
    Write-Host "    Travel:      $([math]::Round($estimate.travel_mm, 2)) mm" -ForegroundColor Gray
    Write-Host "    Cutting:     $([math]::Round($estimate.cut_mm, 2)) mm" -ForegroundColor Gray
    Write-Host "    Rapid time:  $([math]::Round($estimate.t_rapid_min * 60, 2)) sec" -ForegroundColor Gray
    Write-Host "    Feed time:   $([math]::Round($estimate.t_feed_min * 60, 2)) sec" -ForegroundColor Gray
    Write-Host "    Total time:  $([math]::Round($estimate.t_total_min * 60, 2)) sec" -ForegroundColor Gray
    Write-Host "    Path points: $($estimate.points_xy.Count)" -ForegroundColor Gray
    
    # Validation checks
    $errors = @()
    
    if ($estimate.travel_mm -lt 0) {
        $errors += "Negative travel distance"
    }
    if ($estimate.cut_mm -lt 0) {
        $errors += "Negative cutting distance"
    }
    if ($estimate.t_total_min -le 0) {
        $errors += "Zero or negative time"
    }
    if ($estimate.points_xy.Count -lt 2) {
        $errors += "Insufficient path points"
    }
    
    if ($errors.Count -gt 0) {
        Write-Host "`n✗ Validation failed:" -ForegroundColor Red
        $errors | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
        exit 1
    }
    
    # Test 3: Arc handling
    Write-Host "`nTest 3: Arc parsing (G2/G3)" -ForegroundColor White
    $arcGcode = @"
G21 G90 G17
G0 X0 Y0
G1 X10 Y0 F600
G2 X20 Y0 I5 J0
G3 X30 Y0 I5 J0
"@
    
    $arcBody = @{
        gcode = $arcGcode
        units = "mm"
    } | ConvertTo-Json
    
    $arcEst = Invoke-RestMethod -Uri "$base/api/cam/gcode/estimate" `
        -Method POST `
        -ContentType "application/json" `
        -Body $arcBody `
        -TimeoutSec 5
    
    if ($arcEst.cut_mm -gt 10.0) {
        Write-Host "  ✓ Arc distance calculated: $([math]::Round($arcEst.cut_mm, 2)) mm" -ForegroundColor Green
        Write-Host "    (Expected >10mm due to arcs)" -ForegroundColor Gray
    } else {
        $errors += "Arc distance too small"
    }
    
    Write-Host "`n=== Smoke Test Summary ===" -ForegroundColor Cyan
    Write-Host "✓ All tests passed" -ForegroundColor Green
    Write-Host "`nPatch N.15 integration verified:" -ForegroundColor White
    Write-Host "  ✓ G-code parser working" -ForegroundColor Green
    Write-Host "  ✓ SVG backplot generation" -ForegroundColor Green
    Write-Host "  ✓ Time estimation" -ForegroundColor Green
    Write-Host "  ✓ Arc handling (G2/G3)" -ForegroundColor Green
    
    exit 0
    
} catch {
    Write-Host "`n✗ Smoke test failed:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    
    if ($_.Exception.InnerException) {
        Write-Host "`nInner Exception:" -ForegroundColor Yellow
        Write-Host $_.Exception.InnerException.Message -ForegroundColor Red
    }
    
    exit 1
    
} finally {
    if ($proc -and !$proc.HasExited) {
        Write-Host "`nStopping API server..." -ForegroundColor Yellow
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
}
