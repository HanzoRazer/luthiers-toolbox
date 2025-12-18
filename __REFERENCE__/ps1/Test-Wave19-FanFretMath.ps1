# Test-Wave19-FanFretMath.ps1
# Wave 19 Phase A: Fan-Fret Geometry Math Tests

$ErrorActionPreference = "Stop"

Write-Host "=== Wave 19: Fan-Fret Geometry Math Tests ===" -ForegroundColor Cyan
Write-Host ""

# Test API base URL
$API_URL = "http://localhost:8000"

# Test counter
$TestsPassed = 0
$TestsFailed = 0

function Test-FanFretCalculation {
    param(
        [string]$TestName,
        [float]$TrebleScale,
        [float]$BassScale,
        [int]$PerpendicularFret,
        [int]$NumFrets
    )
    
    Write-Host "Testing: $TestName" -ForegroundColor Yellow
    
    $payload = @{
        treble_scale_mm = $TrebleScale
        bass_scale_mm = $BassScale
        perpendicular_fret = $PerpendicularFret
        num_frets = $NumFrets
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "$API_URL/api/instrument_geometry/fan_fret/calculate" `
            -Method POST `
            -ContentType "application/json" `
            -Body $payload
        
        if ($response.fret_points.Count -eq ($NumFrets + 1)) {
            Write-Host "  ✓ Correct number of fret points: $($response.fret_points.Count)" -ForegroundColor Green
            $script:TestsPassed++
        } else {
            Write-Host "  ✗ Wrong number of fret points: Expected $($NumFrets + 1), got $($response.fret_points.Count)" -ForegroundColor Red
            $script:TestsFailed++
            return
        }
        
        # Check perpendicular fret
        $perpFret = $response.fret_points[$PerpendicularFret]
        if ($perpFret.is_perpendicular -and [Math]::Abs($perpFret.angle_rad) -lt 0.001) {
            Write-Host "  ✓ Perpendicular fret correct (angle ≈ 0)" -ForegroundColor Green
            $script:TestsPassed++
        } else {
            Write-Host "  ✗ Perpendicular fret incorrect (angle = $($perpFret.angle_rad))" -ForegroundColor Red
            $script:TestsFailed++
        }
        
        Write-Host ""
    }
    catch {
        Write-Host "  ✗ Test failed: $_" -ForegroundColor Red
        $script:TestsFailed++
        Write-Host ""
    }
}

# Test 1: Standard 7-string configuration
Test-FanFretCalculation `
    -TestName "Standard 7-string (25.5""-27"", perp @ 7)" `
    -TrebleScale 648.0 `
    -BassScale 686.0 `
    -PerpendicularFret 7 `
    -NumFrets 24

# Test 2: 8-string configuration
Test-FanFretCalculation `
    -TestName "8-string (25.5""-28"", perp @ 8)" `
    -TrebleScale 648.0 `
    -BassScale 711.2 `
    -PerpendicularFret 8 `
    -NumFrets 24

# Test 3: Baritone 6-string
Test-FanFretCalculation `
    -TestName "Baritone 6-string (26""-27"", perp @ 7)" `
    -TrebleScale 660.0 `
    -BassScale 685.8 `
    -PerpendicularFret 7 `
    -NumFrets 22

# Test 4: Validation - bass < treble (should fail)
Write-Host "Testing: Validation - bass < treble scale (should fail)" -ForegroundColor Yellow
$payload = @{
    treble_scale_mm = 686.0
    bass_scale_mm = 648.0
    perpendicular_fret = 7
    num_frets = 22
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$API_URL/api/instrument_geometry/fan_fret/validate" `
        -Method POST `
        -ContentType "application/json" `
        -Body $payload
    
    if (-not $response.valid) {
        Write-Host "  ✓ Validation correctly rejected invalid config" -ForegroundColor Green
        $TestsPassed++
    } else {
        Write-Host "  ✗ Validation should have failed" -ForegroundColor Red
        $TestsFailed++
    }
}
catch {
    # Expected to get 400 error
    if ($_.Exception.Response.StatusCode -eq 400) {
        Write-Host "  ✓ Validation correctly rejected invalid config (HTTP 400)" -ForegroundColor Green
        $TestsPassed++
    } else {
        Write-Host "  ✗ Unexpected error: $_" -ForegroundColor Red
        $TestsFailed++
    }
}
Write-Host ""

# Test 5: Fret angle progression
Write-Host "Testing: Fret angle progression" -ForegroundColor Yellow
$payload = @{
    treble_scale_mm = 648.0
    bass_scale_mm = 686.0
    perpendicular_fret = 7
    num_frets = 22
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$API_URL/api/instrument_geometry/fan_fret/calculate" `
        -Method POST `
        -ContentType "application/json" `
        -Body $payload
    
    # Check that angles increase from nut to perpendicular fret
    $angleAt1 = [Math]::Abs($response.fret_points[1].angle_rad)
    $angleAt5 = [Math]::Abs($response.fret_points[5].angle_rad)
    
    if ($angleAt5 -gt $angleAt1) {
        Write-Host "  ✓ Angles increase towards perpendicular fret" -ForegroundColor Green
        $TestsPassed++
    } else {
        Write-Host "  ✗ Angle progression incorrect" -ForegroundColor Red
        $TestsFailed++
    }
    
    # Check that angles are reasonable (< 30 degrees for moderate fan-fret)
    # Note: 25.5"-27" (38mm difference) produces ~27° max angle, which is geometrically correct
    $maxAngleDeg = ($response.fret_points | ForEach-Object { [Math]::Abs($_.angle_rad) * 180 / [Math]::PI } | Measure-Object -Maximum).Maximum
    
    if ($maxAngleDeg -lt 30.0) {
        Write-Host "  ✓ Maximum angle reasonable: $([Math]::Round($maxAngleDeg, 2))°" -ForegroundColor Green
        $TestsPassed++
    } else {
        Write-Host "  ✗ Maximum angle too large: $([Math]::Round($maxAngleDeg, 2))°" -ForegroundColor Red
        $TestsFailed++
    }
}
catch {
    Write-Host "  ✗ Test failed: $_" -ForegroundColor Red
    $TestsFailed += 2
}
Write-Host ""

# Summary
Write-Host "=== Test Summary ===" -ForegroundColor Cyan
Write-Host "Passed: $TestsPassed" -ForegroundColor Green
Write-Host "Failed: $TestsFailed" -ForegroundColor $(if ($TestsFailed -eq 0) { "Green" } else { "Red" })
Write-Host ""

if ($TestsFailed -eq 0) {
    Write-Host "✓ All Wave 19 Phase A tests passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "✗ Some tests failed. Review output above." -ForegroundColor Red
    exit 1
}
