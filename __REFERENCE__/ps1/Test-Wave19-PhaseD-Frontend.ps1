#!/usr/bin/env pwsh
# Test-Wave19-PhaseD-Frontend.ps1
# Tests for Wave 19 Phase D: Frontend Integration for Fan-Fret CAM

Write-Host "=== Wave 19 Phase D: Frontend Integration Tests ===" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"
$testsRun = 0
$testsPassed = 0

function Test-APIEndpoint {
    param(
        [string]$TestName,
        [hashtable]$RequestBody,
        [scriptblock]$Validation
    )
    
    $script:testsRun++
    Write-Host "Test $testsRun`: $TestName" -ForegroundColor Yellow
    
    try {
        $jsonBody = $RequestBody | ConvertTo-Json -Depth 10
        $response = Invoke-RestMethod -Uri "$baseUrl/api/cam/fret_slots/preview" `
            -Method Post `
            -ContentType "application/json" `
            -Body $jsonBody `
            -ErrorAction Stop
        
        & $Validation $response
        
        Write-Host "  ✓ PASS" -ForegroundColor Green
        $script:testsPassed++
        return $true
    }
    catch {
        Write-Host "  ✗ FAIL: $_" -ForegroundColor Red
        return $false
    }
}

# Test 1: Standard Mode Request (simulating frontend with fan-fret disabled)
Test-APIEndpoint -TestName "Standard mode API request (fanFretEnabled=false)" `
    -RequestBody @{
        model_id = "lp_24_75"
        mode = "standard"
        scale_length_mm = 628.65
        fret_count = 22
        nut_width_mm = 43.0
        heel_width_mm = 56.0
        slot_width_mm = 0.6
        slot_depth_mm = 3.0
        post_id = "GRBL"
    } `
    -Validation {
        param($r)
        if (-not $r.statistics) { throw "Missing statistics" }
        if (-not $r.toolpaths) { throw "Missing toolpaths" }
        if ($r.toolpaths.Count -ne 22) { throw "Expected 22 toolpaths, got $($r.toolpaths.Count)" }
        if (-not $r.dxf_content) { throw "Missing DXF content" }
        if (-not $r.gcode_content) { throw "Missing G-code content" }
        if ($r.gcode_content -notmatch "MODE=standard") { throw "G-code missing MODE=standard" }
    }

# Test 2: Fan-Fret Mode Request (simulating frontend with fan-fret enabled)
Test-APIEndpoint -TestName "Fan-fret mode API request (fanFretEnabled=true)" `
    -RequestBody @{
        model_id = "lp_24_75"
        mode = "fan"
        treble_scale_mm = 647.7
        bass_scale_mm = 660.4
        perpendicular_fret = 7
        fret_count = 22
        nut_width_mm = 43.0
        heel_width_mm = 56.0
        slot_width_mm = 0.6
        slot_depth_mm = 3.0
        post_id = "GRBL"
    } `
    -Validation {
        param($r)
        if (-not $r.statistics) { throw "Missing statistics" }
        if (-not $r.toolpaths) { throw "Missing toolpaths" }
        if ($r.toolpaths.Count -ne 22) { throw "Expected 22 toolpaths, got $($r.toolpaths.Count)" }
        
        # Check for angled frets (not all perpendicular)
        $angledFrets = $r.toolpaths | Where-Object { [Math]::Abs($_.angle_rad) -gt 0.001 }
        if ($angledFrets.Count -eq 0) { throw "No angled frets found in fan-fret mode" }
        
        if (-not $r.dxf_content) { throw "Missing DXF content" }
        if ($r.dxf_content -notmatch "FRET_SLOTS_FAN") { throw "DXF missing FRET_SLOTS_FAN layer" }
        
        if (-not $r.gcode_content) { throw "Missing G-code content" }
        if ($r.gcode_content -notmatch "MODE=fan") { throw "G-code missing MODE=fan" }
    }

# Test 3: Per-Fret Risk Analysis (Phase C integration)
Test-APIEndpoint -TestName "Per-fret risk analysis in frontend response" `
    -RequestBody @{
        model_id = "lp_24_75"
        mode = "fan"
        treble_scale_mm = 647.7
        bass_scale_mm = 660.4
        perpendicular_fret = 7
        fret_count = 22
        nut_width_mm = 43.0
        heel_width_mm = 56.0
        slot_width_mm = 0.6
        slot_depth_mm = 3.0
        post_id = "GRBL"
    } `
    -Validation {
        param($r)
        if (-not $r.per_fret_risks) { throw "Missing per_fret_risks array" }
        if ($r.per_fret_risks.Count -ne 22) { throw "Expected 22 risk entries" }
        
        # Check first risk entry structure
        $risk0 = $r.per_fret_risks[0]
        if (-not $risk0.fret_number) { throw "Missing fret_number in risk" }
        if (-not $risk0.angle_deg) { throw "Missing angle_deg in risk" }
        if (-not $risk0.chipload_risk) { throw "Missing chipload_risk" }
        if (-not $risk0.heat_risk) { throw "Missing heat_risk" }
        if (-not $risk0.overall_risk) { throw "Missing overall_risk" }
        
        if (-not $r.risk_summary) { throw "Missing risk_summary" }
        if (-not $r.risk_summary.total_frets) { throw "Missing total_frets" }
        if (-not $r.risk_summary.green_count) { throw "Missing green_count" }
    }

# Test 4: Perpendicular Fret Validation
Test-APIEndpoint -TestName "Perpendicular fret at specified position" `
    -RequestBody @{
        model_id = "lp_24_75"
        mode = "fan"
        treble_scale_mm = 647.7
        bass_scale_mm = 660.4
        perpendicular_fret = 7
        fret_count = 22
        nut_width_mm = 43.0
        heel_width_mm = 56.0
        slot_width_mm = 0.6
        slot_depth_mm = 3.0
        post_id = "GRBL"
    } `
    -Validation {
        param($r)
        $fret7 = $r.toolpaths | Where-Object { $_.fret_number -eq 7 }
        if (-not $fret7) { throw "Fret 7 not found" }
        
        # Perpendicular fret should have near-zero angle
        if ([Math]::Abs($fret7.angle_rad) -gt 0.05) {
            throw "Fret 7 angle too large: $($fret7.angle_rad) rad"
        }
        
        Write-Host "    Fret 7 angle: $([Math]::Abs($fret7.angle_rad * 180 / [Math]::PI)) degrees (perpendicular)" -ForegroundColor Cyan
    }

# Test 5: Toggle Between Modes (simulating user switching fan-fret on/off)
Test-APIEndpoint -TestName "Switch from fan-fret to standard mode" `
    -RequestBody @{
        model_id = "lp_24_75"
        mode = "standard"
        scale_length_mm = 628.65
        fret_count = 22
        nut_width_mm = 43.0
        heel_width_mm = 56.0
        slot_width_mm = 0.6
        slot_depth_mm = 3.0
        post_id = "GRBL"
    } `
    -Validation {
        param($r)
        # In standard mode, all frets should be perpendicular
        $angledFrets = $r.toolpaths | Where-Object { [Math]::Abs($_.angle_rad) -gt 0.001 }
        if ($angledFrets.Count -gt 0) { throw "Found angled frets in standard mode" }
        
        if ($r.gcode_content -match "MODE=fan") { throw "G-code has MODE=fan in standard request" }
    }

# Test 6: Different Perpendicular Fret Values
Test-APIEndpoint -TestName "Perpendicular fret = 12 (middle)" `
    -RequestBody @{
        model_id = "lp_24_75"
        mode = "fan"
        treble_scale_mm = 647.7
        bass_scale_mm = 660.4
        perpendicular_fret = 12
        fret_count = 22
        nut_width_mm = 43.0
        heel_width_mm = 56.0
        slot_width_mm = 0.6
        slot_depth_mm = 3.0
        post_id = "GRBL"
    } `
    -Validation {
        param($r)
        $fret12 = $r.toolpaths | Where-Object { $_.fret_number -eq 12 }
        if ([Math]::Abs($fret12.angle_rad) -gt 0.05) {
            throw "Fret 12 not perpendicular"
        }
    }

# Test 7: Extended-Range 7-String Configuration
Test-APIEndpoint -TestName "7-string extended range (25.5 treble, 27 bass)" `
    -RequestBody @{
        model_id = "strat_25_5"
        mode = "fan"
        treble_scale_mm = 647.7  # 25.5 inches
        bass_scale_mm = 685.8    # 27 inches
        perpendicular_fret = 7
        fret_count = 24
        nut_width_mm = 48.0
        heel_width_mm = 62.0
        slot_width_mm = 0.6
        slot_depth_mm = 3.0
        post_id = "GRBL"
    } `
    -Validation {
        param($r)
        if ($r.toolpaths.Count -ne 24) { throw "Expected 24 frets" }
        
        # Higher scale difference should produce more pronounced angles
        $maxAngle = ($r.toolpaths | ForEach-Object { [Math]::Abs($_.angle_rad) } | Measure-Object -Maximum).Maximum
        if ($maxAngle -lt 0.05) { throw "Angles too small for extended range" }
        
        Write-Host "    Max fret angle: $($maxAngle * 180 / [Math]::PI) degrees" -ForegroundColor Cyan
    }

# Summary
Write-Host ""
Write-Host "=== Phase D Frontend Integration Test Results ===" -ForegroundColor Cyan
Write-Host "Tests Passed: $testsPassed / $testsRun" -ForegroundColor $(if ($testsPassed -eq $testsRun) { "Green" } else { "Yellow" })
Write-Host ""

if ($testsPassed -eq $testsRun) {
    Write-Host "✅ All Phase D tests passing! Frontend ready for user testing." -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host "1. Start Vue dev server: cd packages/client && npm run dev"
    Write-Host "2. Navigate to Instrument Geometry panel"
    Write-Host "3. Enable 'Fan-Fret (Multi-Scale)' checkbox"
    Write-Host "4. Configure treble/bass scales and perpendicular fret"
    Write-Host "5. Click 'Generate CAM Preview'"
    Write-Host "6. Verify angled fret lines render in preview"
    Write-Host "7. Check per-fret risk colors (Green/Yellow/Red)"
    exit 0
} else {
    Write-Host "❌ $($testsRun - $testsPassed) test(s) failed" -ForegroundColor Red
    exit 1
}
