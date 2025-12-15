# Test-Wave19-PerFretRisk.ps1
# Wave 19 Phase C: Per-Fret Risk Analysis Tests

$ErrorActionPreference = "Stop"

Write-Host "=== Wave 19 Phase C: Per-Fret Risk Analysis Tests ===" -ForegroundColor Cyan
Write-Host ""

# Test API base URL
$API_URL = "http://localhost:8000"

# Test counter
$TestsPassed = 0
$TestsFailed = 0

# Test 1: Standard mode CAM with risk analysis
Write-Host "Test 1: Standard Mode CAM with Risk Analysis" -ForegroundColor Yellow
$payload = @{
    model_id = "strat_25_5"
    mode = "standard"
    fret_count = 22
    slot_depth_mm = 3.0
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$API_URL/api/cam/fret_slots/preview" `
        -Method POST `
        -ContentType "application/json" `
        -Body $payload
    
    if ($response.toolpaths -and $response.toolpaths.Count -eq 22) {
        Write-Host "  ✓ Generated 22 toolpaths" -ForegroundColor Green
        $TestsPassed++
    } else {
        Write-Host "  ✗ Wrong toolpath count: $($response.toolpaths.Count)" -ForegroundColor Red
        $TestsFailed++
    }
    
    if ($response.per_fret_risks -and $response.per_fret_risks.Count -eq 22) {
        Write-Host "  ✓ Generated 22 per-fret risk assessments" -ForegroundColor Green
        $TestsPassed++
    } else {
        Write-Host "  ✗ Wrong risk assessment count" -ForegroundColor Red
        $TestsFailed++
    }
    
    if ($response.risk_summary) {
        Write-Host "  ✓ Risk summary present" -ForegroundColor Green
        Write-Host "    Green: $($response.risk_summary.green_count)" -ForegroundColor Green
        Write-Host "    Yellow: $($response.risk_summary.yellow_count)" -ForegroundColor Yellow
        Write-Host "    Red: $($response.risk_summary.red_count)" -ForegroundColor Red
        $TestsPassed++
    } else {
        Write-Host "  ✗ No risk summary" -ForegroundColor Red
        $TestsFailed++
    }
}
catch {
    Write-Host "  ✗ Test failed: $_" -ForegroundColor Red
    $TestsFailed += 3
}
Write-Host ""

# Test 2: Fan-fret mode CAM with risk analysis
Write-Host "Test 2: Fan-Fret Mode CAM with Risk Analysis" -ForegroundColor Yellow
$payload = @{
    model_id = "strat_25_5"
    mode = "fan"
    treble_scale_mm = 648.0
    bass_scale_mm = 686.0
    perpendicular_fret = 7
    fret_count = 22
    slot_depth_mm = 3.0
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$API_URL/api/cam/fret_slots/preview" `
        -Method POST `
        -ContentType "application/json" `
        -Body $payload
    
    if ($response.toolpaths -and $response.toolpaths.Count -eq 22) {
        Write-Host "  ✓ Generated 22 fan-fret toolpaths" -ForegroundColor Green
        $TestsPassed++
    } else {
        Write-Host "  ✗ Wrong toolpath count" -ForegroundColor Red
        $TestsFailed++
    }
    
    # Check that some frets have non-zero angles
    $nonZeroAngles = ($response.toolpaths | Where-Object { [Math]::Abs($_.angle_rad) -gt 0.001 }).Count
    if ($nonZeroAngles -gt 0) {
        Write-Host "  ✓ Fan-fret angles detected: $nonZeroAngles frets" -ForegroundColor Green
        $TestsPassed++
    } else {
        Write-Host "  ✗ No fan-fret angles found" -ForegroundColor Red
        $TestsFailed++
    }
    
    # Check risk analysis
    if ($response.per_fret_risks) {
        Write-Host "  ✓ Per-fret risks generated" -ForegroundColor Green
        $TestsPassed++
        
        # Check for angle-based risk factors
        $highAngleFrets = ($response.per_fret_risks | Where-Object { $_.angle_deg -gt 10.0 }).Count
        Write-Host "    High-angle frets (>10°): $highAngleFrets" -ForegroundColor Cyan
        
        # Check max risks
        $maxChipload = ($response.per_fret_risks | Measure-Object -Property chipload_risk -Maximum).Maximum
        $maxHeat = ($response.per_fret_risks | Measure-Object -Property heat_risk -Maximum).Maximum
        $maxDeflection = ($response.per_fret_risks | Measure-Object -Property deflection_risk -Maximum).Maximum
        
        Write-Host "    Max chipload risk: $maxChipload" -ForegroundColor Cyan
        Write-Host "    Max heat risk: $maxHeat" -ForegroundColor Cyan
        Write-Host "    Max deflection risk: $maxDeflection" -ForegroundColor Cyan
    } else {
        Write-Host "  ✗ No per-fret risks" -ForegroundColor Red
        $TestsFailed++
    }
}
catch {
    Write-Host "  ✗ Test failed: $_" -ForegroundColor Red
    $_.ErrorDetails.Message
    $TestsFailed += 3
}
Write-Host ""

# Test 3: High-risk fret identification
Write-Host "Test 3: High-Risk Fret Identification" -ForegroundColor Yellow
$payload = @{
    model_id = "strat_25_5"
    mode = "fan"
    treble_scale_mm = 648.0
    bass_scale_mm = 711.2  # 8-string config (larger angle)
    perpendicular_fret = 8
    fret_count = 24
    slot_depth_mm = 3.5  # Deeper cuts = higher risk
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$API_URL/api/cam/fret_slots/preview" `
        -Method POST `
        -ContentType "application/json" `
        -Body $payload
    
    if ($response.risk_summary.high_risk_frets) {
        $highRiskCount = $response.risk_summary.high_risk_frets.Count
        Write-Host "  ✓ Identified $highRiskCount high-risk frets" -ForegroundColor Green
        $TestsPassed++
        
        # Show first high-risk fret details
        if ($highRiskCount -gt 0) {
            $firstHighRisk = $response.risk_summary.high_risk_frets[0]
            Write-Host "    Example high-risk fret:" -ForegroundColor Cyan
            Write-Host "      Fret: $($firstHighRisk.fret_number)" -ForegroundColor Cyan
            Write-Host "      Angle: $($firstHighRisk.angle_deg)°" -ForegroundColor Cyan
            Write-Host "      Chipload risk: $($firstHighRisk.chipload_risk)" -ForegroundColor Cyan
            Write-Host "      Warnings: $($firstHighRisk.warnings.Count)" -ForegroundColor Cyan
        }
    } else {
        Write-Host "  ✓ No high-risk frets identified (safe config)" -ForegroundColor Green
        $TestsPassed++
    }
}
catch {
    Write-Host "  ✗ Test failed: $_" -ForegroundColor Red
    $TestsFailed++
}
Write-Host ""

# Test 4: DXF and G-code generation
Write-Host "Test 4: DXF and G-code Generation" -ForegroundColor Yellow
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
    
    if ($response.dxf_content -and $response.dxf_content.Length -gt 100) {
        Write-Host "  ✓ DXF content generated ($($response.dxf_content.Length) chars)" -ForegroundColor Green
        $TestsPassed++
        
        # Check for fan-fret layer
        if ($response.dxf_content -match "FRET_SLOTS_FAN") {
            Write-Host "  ✓ DXF uses FRET_SLOTS_FAN layer" -ForegroundColor Green
            $TestsPassed++
        } else {
            Write-Host "  ✗ DXF missing fan-fret layer" -ForegroundColor Red
            $TestsFailed++
        }
    } else {
        Write-Host "  ✗ DXF content too short or missing" -ForegroundColor Red
        $TestsFailed += 2
    }
    
    if ($response.gcode_content -and $response.gcode_content.Length -gt 100) {
        Write-Host "  ✓ G-code content generated ($($response.gcode_content.Length) chars)" -ForegroundColor Green
        $TestsPassed++
        
        # Check for mode metadata
        if ($response.gcode_content -match "MODE=fan") {
            Write-Host "  ✓ G-code has fan mode metadata" -ForegroundColor Green
            $TestsPassed++
        } else {
            Write-Host "  ✗ G-code missing mode metadata" -ForegroundColor Red
            $TestsFailed++
        }
    } else {
        Write-Host "  ✗ G-code content too short or missing" -ForegroundColor Red
        $TestsFailed += 2
    }
}
catch {
    Write-Host "  ✗ Test failed: $_" -ForegroundColor Red
    $TestsFailed += 4
}
Write-Host ""

# Test 5: Statistics validation
Write-Host "Test 5: Statistics Validation" -ForegroundColor Yellow
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
    
    if ($stats.slot_count -eq 22) {
        Write-Host "  ✓ Slot count correct: 22" -ForegroundColor Green
        $TestsPassed++
    } else {
        Write-Host "  ✗ Wrong slot count: $($stats.slot_count)" -ForegroundColor Red
        $TestsFailed++
    }
    
    if ($stats.max_angle_deg -and $stats.max_angle_deg -gt 0) {
        Write-Host "  ✓ Max angle tracked: $($stats.max_angle_deg)°" -ForegroundColor Green
        $TestsPassed++
    } else {
        Write-Host "  ✗ Max angle not tracked" -ForegroundColor Red
        $TestsFailed++
    }
    
    if ($stats.mode -eq "fan") {
        Write-Host "  ✓ Mode metadata correct" -ForegroundColor Green
        $TestsPassed++
    } else {
        Write-Host "  ✗ Wrong mode: $($stats.mode)" -ForegroundColor Red
        $TestsFailed++
    }
}
catch {
    Write-Host "  ✗ Test failed: $_" -ForegroundColor Red
    $TestsFailed += 3
}
Write-Host ""

# Summary
Write-Host "=== Test Summary ===" -ForegroundColor Cyan
Write-Host "Passed: $TestsPassed" -ForegroundColor Green
Write-Host "Failed: $TestsFailed" -ForegroundColor $(if ($TestsFailed -eq 0) { "Green" } else { "Red" })
Write-Host ""

if ($TestsFailed -eq 0) {
    Write-Host "✓ All Wave 19 Phase C tests passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "✗ Some tests failed. Review output above." -ForegroundColor Red
    exit 1
}
