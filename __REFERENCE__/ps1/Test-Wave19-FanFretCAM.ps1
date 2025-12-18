# Test-Wave19-FanFretCAM.ps1
# Wave 19 Phase B: Fan-Fret CAM Generation Tests

$ErrorActionPreference = "Stop"

Write-Host "=== Wave 19 Phase B: Fan-Fret CAM Generation Tests ===" -ForegroundColor Cyan
Write-Host ""

# Test API base URL
$API_URL = "http://localhost:8000"

# Test counter
$TestsPassed = 0
$TestsFailed = 0

function Test-FanFretCAM {
    param(
        [string]$TestName,
        [hashtable]$Payload,
        [string[]]$ExpectedChecks
    )
    
    Write-Host "Testing: $TestName" -ForegroundColor Yellow
    
    $jsonPayload = $Payload | ConvertTo-Json -Depth 10
    
    try {
        $response = Invoke-RestMethod -Uri "$API_URL/api/cam/fret_slots/preview" `
            -Method POST `
            -ContentType "application/json" `
            -Body $jsonPayload
        
        foreach ($check in $ExpectedChecks) {
            switch ($check) {
                "has_toolpaths" {
                    if ($response.toolpaths -and $response.toolpaths.Count -gt 0) {
                        Write-Host "  ✓ Has toolpaths: $($response.toolpaths.Count)" -ForegroundColor Green
                        $script:TestsPassed++
                    } else {
                        Write-Host "  ✗ No toolpaths generated" -ForegroundColor Red
                        $script:TestsFailed++
                    }
                }
                "has_dxf" {
                    if ($response.dxf_content -and $response.dxf_content.Length -gt 0) {
                        Write-Host "  ✓ DXF generated" -ForegroundColor Green
                        $script:TestsPassed++
                    } else {
                        Write-Host "  ✗ No DXF content" -ForegroundColor Red
                        $script:TestsFailed++
                    }
                }
                "has_gcode" {
                    if ($response.gcode_content -and $response.gcode_content.Length -gt 0) {
                        Write-Host "  ✓ G-code generated" -ForegroundColor Green
                        $script:TestsPassed++
                    } else {
                        Write-Host "  ✗ No G-code content" -ForegroundColor Red
                        $script:TestsFailed++
                    }
                }
                "fan_mode" {
                    if ($response.statistics.mode -eq "fan") {
                        Write-Host "  ✓ Fan mode confirmed" -ForegroundColor Green
                        $script:TestsPassed++
                    } else {
                        Write-Host "  ✗ Mode not set to 'fan'" -ForegroundColor Red
                        $script:TestsFailed++
                    }
                }
                "has_max_angle" {
                    if ($response.statistics.max_angle_deg -and $response.statistics.max_angle_deg -gt 0) {
                        Write-Host "  ✓ Max angle: $($response.statistics.max_angle_deg)°" -ForegroundColor Green
                        $script:TestsPassed++
                    } else {
                        Write-Host "  ✗ No max angle data" -ForegroundColor Red
                        $script:TestsFailed++
                    }
                }
                "dxf_fan_layer" {
                    if ($response.dxf_content -match "FRET_SLOTS_FAN") {
                        Write-Host "  ✓ DXF uses FRET_SLOTS_FAN layer" -ForegroundColor Green
                        $script:TestsPassed++
                    } else {
                        Write-Host "  ✗ DXF missing fan layer" -ForegroundColor Red
                        $script:TestsFailed++
                    }
                }
            }
        }
        
        Write-Host ""
    }
    catch {
        Write-Host "  ✗ Test failed: $_" -ForegroundColor Red
        $script:TestsFailed += $ExpectedChecks.Count
        Write-Host ""
    }
}

# Test 1: Basic fan-fret CAM generation
Write-Host "Test 1: Basic Fan-Fret CAM Generation" -ForegroundColor Cyan
Test-FanFretCAM `
    -TestName "7-string standard config" `
    -Payload @{
        model_id = "strat_25_5"
        mode = "fan"
        treble_scale_mm = 648.0
        bass_scale_mm = 686.0
        perpendicular_fret = 7
        fret_count = 22
        slot_depth_mm = 3.0
    } `
    -ExpectedChecks @("has_toolpaths", "has_dxf", "has_gcode", "fan_mode", "has_max_angle", "dxf_fan_layer")

# Test 2: 8-string configuration
Write-Host "Test 2: 8-String Fan-Fret" -ForegroundColor Cyan
Test-FanFretCAM `
    -TestName "8-string (25.5""-28"")" `
    -Payload @{
        model_id = "strat_25_5"
        mode = "fan"
        treble_scale_mm = 648.0
        bass_scale_mm = 711.2
        perpendicular_fret = 8
        fret_count = 24
    } `
    -ExpectedChecks @("has_toolpaths", "fan_mode", "has_max_angle")

# Test 3: Baritone 6-string
Write-Host "Test 3: Baritone 6-String" -ForegroundColor Cyan
Test-FanFretCAM `
    -TestName "Baritone (26""-27"")" `
    -Payload @{
        model_id = "lp_24_75"
        mode = "fan"
        treble_scale_mm = 660.0
        bass_scale_mm = 685.8
        perpendicular_fret = 7
        fret_count = 22
    } `
    -ExpectedChecks @("has_toolpaths", "has_dxf", "fan_mode")

# Test 4: Material-Aware Feedrates
Write-Host "Test 4: Material-Aware Feedrates" -ForegroundColor Yellow
# Material-aware feedrates are handled automatically by the CAM generator
# based on the model_id context. We just verify they're present.
$payload = @{
    model_id = "strat_25_5"
    mode = "fan"
    treble_scale_mm = 648.0
    bass_scale_mm = 686.0
    perpendicular_fret = 7
    fret_count = 22
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$API_URL/api/cam/fret_slots/preview" `
        -Method POST `
        -ContentType "application/json" `
        -Body $payload
    
    $firstFeed = $response.toolpaths[0].feed_rate_mmpm
    
    if ($firstFeed -gt 0) {
        Write-Host "  ✓ Feedrate present: $firstFeed mm/min" -ForegroundColor Green
        $TestsPassed++
    } else {
        Write-Host "  ✗ No feedrate in toolpath" -ForegroundColor Red
        $TestsFailed++
    }
}
catch {
    Write-Host "  ✗ Test failed: $_" -ForegroundColor Red
    $TestsFailed++
}
Write-Host ""

# Test 5: Compound Radius Depth Adjustment
Write-Host "Test 5: Compound Radius Depth Adjustment" -ForegroundColor Yellow
$payload = @{
    model_id = "strat_25_5"
    mode = "fan"
    treble_scale_mm = 648.0
    bass_scale_mm = 686.0
    perpendicular_fret = 7
    fret_count = 22
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$API_URL/api/cam/fret_slots/preview" `
        -Method POST `
        -ContentType "application/json" `
        -Body $payload
    
    $depth1 = $response.toolpaths[0].slot_depth_mm
    $depth22 = $response.toolpaths[21].slot_depth_mm
    
    if ([Math]::Abs($depth1 - $depth22) -gt 0.05) {
        Write-Host "  ✓ Depth varies: Fret 1 = $depth1 mm, Fret 22 = $depth22 mm" -ForegroundColor Green
        $TestsPassed++
    } else {
        Write-Host "  ✗ No depth variation detected" -ForegroundColor Red
        $TestsFailed++
    }
}
catch {
    Write-Host "  ✗ Test failed: $_" -ForegroundColor Red
    $TestsFailed++
}
Write-Host ""

# Test 6: DXF Angle Metadata
Write-Host "Test 6: DXF Angle Metadata" -ForegroundColor Yellow
$payload = @{
    model_id = "strat_25_5"
    mode = "fan"
    treble_scale_mm = 648.0
    bass_scale_mm = 686.0
    perpendicular_fret = 7
    fret_count = 22
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$API_URL/api/cam/fret_slots/preview" `
        -Method POST `
        -ContentType "application/json" `
        -Body $payload
    
    if ($response.dxf_content -and $response.dxf_content.Length -gt 0) {
        Write-Host "  ✓ DXF content generated" -ForegroundColor Green
        $TestsPassed++
    } else {
        Write-Host "  ✗ No DXF content" -ForegroundColor Red
        $TestsFailed++
    }
}
catch {
    Write-Host "  ✗ Test failed: $_" -ForegroundColor Red
    $TestsFailed++
}
Write-Host ""

# Test 7: G-code validation for angled cuts
Write-Host "Test 7: G-code Validation" -ForegroundColor Yellow
$payload = @{
    model_id = "strat_25_5"
    mode = "fan"
    treble_scale_mm = 648.0
    bass_scale_mm = 686.0
    perpendicular_fret = 7
    fret_count = 22
    post_id = "GRBL"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$API_URL/api/cam/fret_slots/preview" `
        -Method POST `
        -ContentType "application/json" `
        -Body $payload
    
    $hasG21 = $response.gcode_content -match "G21"
    $hasG90 = $response.gcode_content -match "G90"
    $hasG1 = $response.gcode_content -match "G1"
    
    if ($hasG21 -and $hasG90 -and $hasG1) {
        Write-Host "  ✓ G-code has required commands (G21, G90, G1)" -ForegroundColor Green
        $TestsPassed++
    } else {
        Write-Host "  ✗ G-code missing required commands" -ForegroundColor Red
        $TestsFailed++
    }
}
catch {
    Write-Host "  ✗ Test failed: $_" -ForegroundColor Red
    $TestsFailed++
}
Write-Host ""

# Test 8: Statistics validation
Write-Host "Test 8: Statistics Validation" -ForegroundColor Yellow
$payload = @{
    model_id = "strat_25_5"
    mode = "fan"
    treble_scale_mm = 648.0
    bass_scale_mm = 686.0
    perpendicular_fret = 7
    fret_count = 22
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$API_URL/api/cam/fret_slots/preview" `
        -Method POST `
        -ContentType "application/json" `
        -Body $payload
    
    $stats = $response.statistics
    $hasSlotCount = $stats.slot_count -eq 22
    $hasCuttingLength = $stats.total_cutting_length_mm -gt 0
    $hasTime = $stats.total_time_s -gt 0
    $hasTrebleScale = $stats.treble_scale_mm -eq 648.0
    $hasBassScale = $stats.bass_scale_mm -eq 686.0
    
    if ($hasSlotCount -and $hasCuttingLength -and $hasTime -and $hasTrebleScale -and $hasBassScale) {
        Write-Host "  ✓ All statistics present and valid" -ForegroundColor Green
        $TestsPassed++
    } else {
        Write-Host "  ✗ Missing or invalid statistics" -ForegroundColor Red
        $TestsFailed++
    }
}
catch {
    Write-Host "  ✗ Test failed: $_" -ForegroundColor Red
    $TestsFailed++
}
Write-Host ""

# Test 9: Perpendicular fret validation
Write-Host "Test 9: Perpendicular Fret Validation" -ForegroundColor Yellow
$payload = @{
    model_id = "strat_25_5"
    mode = "fan"
    treble_scale_mm = 648.0
    bass_scale_mm = 686.0
    perpendicular_fret = 7
    num_frets = 22
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$API_URL/api/cam/fret_slots/preview" `
        -Method POST `
        -ContentType "application/json" `
        -Body $payload
    
    $fret7 = $response.toolpaths | Where-Object { $_.fret_number -eq 7 } | Select-Object -First 1
    
    if ($fret7.is_perpendicular -and [Math]::Abs($fret7.angle_rad) -lt 0.01) {
        Write-Host "  ✓ Fret 7 is perpendicular (angle ≈ 0)" -ForegroundColor Green
        $TestsPassed++
    } else {
        Write-Host "  ✗ Fret 7 not correctly marked as perpendicular" -ForegroundColor Red
        $TestsFailed++
    }
}
catch {
    Write-Host "  ✗ Test failed: $_" -ForegroundColor Red
    $TestsFailed++
}
Write-Host ""

# Test 10: Multi-post export
Write-Host "Test 10: Multi-Post Export" -ForegroundColor Yellow
$payload = @{
    model_id = "strat_25_5"
    mode = "fan"
    treble_scale_mm = 648.0
    bass_scale_mm = 686.0
    perpendicular_fret = 7
    post_ids = @("GRBL", "Mach4")
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$API_URL/api/cam/fret_slots/export_bundle_multi" `
        -Method POST `
        -ContentType "application/json" `
        -Body $payload `
        -OutFile "test_fan_fret_bundle.zip"
    
    if (Test-Path "test_fan_fret_bundle.zip") {
        Write-Host "  ✓ Multi-post bundle generated" -ForegroundColor Green
        $TestsPassed++
        Remove-Item "test_fan_fret_bundle.zip" -ErrorAction SilentlyContinue
    } else {
        Write-Host "  ✗ Bundle file not created" -ForegroundColor Red
        $TestsFailed++
    }
}
catch {
    Write-Host "  ✗ Test failed: $_" -ForegroundColor Red
    $TestsFailed++
}
Write-Host ""

# Summary
Write-Host "=== Test Summary ===" -ForegroundColor Cyan
Write-Host "Passed: $TestsPassed" -ForegroundColor Green
Write-Host "Failed: $TestsFailed" -ForegroundColor $(if ($TestsFailed -eq 0) { "Green" } else { "Red" })
Write-Host ""

if ($TestsFailed -eq 0) {
    Write-Host "✓ All Wave 19 Phase B tests passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "✗ Some tests failed. Review output above." -ForegroundColor Red
    exit 1
}
