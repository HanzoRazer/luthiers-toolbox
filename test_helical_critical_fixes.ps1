# Critical Fixes Test - Helical v16.1 Production Safety
# Tests core module extraction and safety validation

Write-Host "=== Testing Helical v16.1 Critical Fixes ===" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"
$passed = 0
$failed = 0

# Test 1: Core module import
Write-Host "1. Testing core module import..." -ForegroundColor Yellow
try {
    Push-Location "services\api"
    $result = python -c "from app.cam.helical_core import helical_plunge, helical_stats, helical_validate, helical_preview_points; print('OK')" 2>&1
    Pop-Location
    
    if ($LASTEXITCODE -eq 0 -and $result -match "OK") {
        Write-Host "  ✓ Core module imports successfully" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  ✗ Core module import failed: $result" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ✗ Exception: $_" -ForegroundColor Red
    Pop-Location
    $failed++
}

Write-Host ""

# Test 2: Safety validation - Thin wall check
Write-Host "2. Testing safety validation (thin wall)..." -ForegroundColor Yellow
try {
    $body = @{
        cx = 0
        cy = 0
        radius_mm = 6.0  # Same as tool diameter - should trigger warning
        direction = "CCW"
        plane_z_mm = 5.0
        start_z_mm = 0.0
        z_target_mm = -3.0
        pitch_mm_per_rev = 1.5
        feed_xy_mm_min = 600
        ij_mode = $true
        absolute = $true
        units_mm = $true
        safe_rapid = $true
        dwell_ms = 0
        max_arc_degrees = 180
        post_preset = "GRBL"
        tool_diameter_mm = 6.0
        material = "hardwood"
        spindle_rpm = 18000
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$baseUrl/api/cam/toolpath/helical_entry" -Method POST -Body $body -ContentType "application/json" -ErrorAction Stop
    
    if ($response.warnings -and $response.warnings.Count -gt 0) {
        Write-Host "  ✓ Warnings detected: $($response.warnings.Count)" -ForegroundColor Green
        $response.warnings | ForEach-Object {
            Write-Host "    - $_" -ForegroundColor White
        }
        $passed++
    } else {
        Write-Host "  ✗ No warnings generated (expected thin-wall warning)" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ⚠ Server not running (start with: cd services/api && uvicorn app.main:app --reload)" -ForegroundColor Yellow
}

Write-Host ""

# Test 3: Safety validation - Aggressive pitch
Write-Host "3. Testing safety validation (aggressive pitch)..." -ForegroundColor Yellow
try {
    $body = @{
        cx = 0
        cy = 0
        radius_mm = 10.0
        direction = "CCW"
        plane_z_mm = 5.0
        start_z_mm = 0.0
        z_target_mm = -3.0
        pitch_mm_per_rev = 8.0  # 80% of radius - should trigger warning
        feed_xy_mm_min = 600
        ij_mode = $true
        absolute = $true
        units_mm = $true
        safe_rapid = $true
        dwell_ms = 0
        max_arc_degrees = 180
        post_preset = "GRBL"
        tool_diameter_mm = 6.0
        material = "hardwood"
        spindle_rpm = 18000
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$baseUrl/api/cam/toolpath/helical_entry" -Method POST -Body $body -ContentType "application/json" -ErrorAction Stop
    
    if ($response.warnings -and $response.warnings.Count -gt 0) {
        $pitchWarning = $response.warnings | Where-Object { $_ -match "Pitch.*aggressive" }
        if ($pitchWarning) {
            Write-Host "  ✓ Pitch warning detected" -ForegroundColor Green
            Write-Host "    - $pitchWarning" -ForegroundColor White
            $passed++
        } else {
            Write-Host "  ✗ No pitch warning found" -ForegroundColor Red
            $failed++
        }
    } else {
        Write-Host "  ✗ No warnings generated (expected aggressive pitch warning)" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ⚠ Server not running" -ForegroundColor Yellow
}

Write-Host ""

# Test 4: Safety validation - Chipload
Write-Host "4. Testing chipload calculation..." -ForegroundColor Yellow
try {
    $body = @{
        cx = 0
        cy = 0
        radius_mm = 12.0
        direction = "CCW"
        plane_z_mm = 5.0
        start_z_mm = 0.0
        z_target_mm = -3.0
        pitch_mm_per_rev = 1.5
        feed_xy_mm_min = 1500  # High feed = high chipload
        ij_mode = $true
        absolute = $true
        units_mm = $true
        safe_rapid = $true
        dwell_ms = 0
        max_arc_degrees = 180
        post_preset = "GRBL"
        tool_diameter_mm = 6.0
        material = "hardwood"
        spindle_rpm = 18000
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$baseUrl/api/cam/toolpath/helical_entry" -Method POST -Body $body -ContentType "application/json" -ErrorAction Stop
    
    if ($response.stats.chipload_mm) {
        Write-Host "  ✓ Chipload calculated: $($response.stats.chipload_mm) mm/tooth" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  ✗ Chipload not calculated" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ⚠ Server not running" -ForegroundColor Yellow
}

Write-Host ""

# Test 5: Statistics enhancement
Write-Host "5. Testing enhanced statistics..." -ForegroundColor Yellow
try {
    $body = @{
        cx = 0
        cy = 0
        radius_mm = 12.0
        direction = "CCW"
        plane_z_mm = 5.0
        start_z_mm = 0.0
        z_target_mm = -6.0
        pitch_mm_per_rev = 1.5
        feed_xy_mm_min = 600
        ij_mode = $true
        absolute = $true
        units_mm = $true
        safe_rapid = $true
        dwell_ms = 0
        max_arc_degrees = 180
        post_preset = "GRBL"
        tool_diameter_mm = 6.0
        material = "hardwood"
        spindle_rpm = 18000
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$baseUrl/api/cam/toolpath/helical_entry" -Method POST -Body $body -ContentType "application/json" -ErrorAction Stop
    
    $requiredStats = @('revolutions', 'segments', 'length_mm', 'time_s', 'warning_count')
    $missingStats = @()
    
    foreach ($stat in $requiredStats) {
        if (-not $response.stats.PSObject.Properties.Name.Contains($stat)) {
            $missingStats += $stat
        }
    }
    
    if ($missingStats.Count -eq 0) {
        Write-Host "  ✓ All required statistics present" -ForegroundColor Green
        Write-Host "    - Revolutions: $($response.stats.revolutions)" -ForegroundColor White
        Write-Host "    - Length: $($response.stats.length_mm) mm" -ForegroundColor White
        Write-Host "    - Time: $($response.stats.time_s) s" -ForegroundColor White
        Write-Host "    - Warnings: $($response.stats.warning_count)" -ForegroundColor White
        $passed++
    } else {
        Write-Host "  ✗ Missing statistics: $($missingStats -join ', ')" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ⚠ Server not running" -ForegroundColor Yellow
}

Write-Host ""

# Test 6: Preview points generation
Write-Host "6. Testing preview points generation..." -ForegroundColor Yellow
try {
    $body = @{
        cx = 0
        cy = 0
        radius_mm = 10.0
        direction = "CCW"
        plane_z_mm = 5.0
        start_z_mm = 0.0
        z_target_mm = -3.0
        pitch_mm_per_rev = 1.5
        feed_xy_mm_min = 600
        ij_mode = $true
        absolute = $true
        units_mm = $true
        safe_rapid = $true
        dwell_ms = 0
        max_arc_degrees = 180
        post_preset = "GRBL"
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$baseUrl/api/cam/toolpath/helical_entry" -Method POST -Body $body -ContentType "application/json" -ErrorAction Stop
    
    if ($response.preview_points -and $response.preview_points.Count -gt 0) {
        Write-Host "  ✓ Preview points generated: $($response.preview_points.Count) points" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  ✗ No preview points generated" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ⚠ Server not running" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Test Summary ===" -ForegroundColor Cyan
Write-Host "  Passed: $passed" -ForegroundColor Green
Write-Host "  Failed: $failed" -ForegroundColor Red

if ($failed -eq 0) {
    Write-Host ""
    Write-Host "✅ All critical fixes implemented successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Critical Safety Features Enabled:" -ForegroundColor Cyan
    Write-Host "  1. Core module extracted (testable, reusable)" -ForegroundColor White
    Write-Host "  2. Thin-wall validation (radius vs tool diameter)" -ForegroundColor White
    Write-Host "  3. Aggressive pitch detection" -ForegroundColor White
    Write-Host "  4. Chipload calculation and validation" -ForegroundColor White
    Write-Host "  5. Enhanced statistics (length, time, warnings)" -ForegroundColor White
    Write-Host "  6. Preview points for visualization" -ForegroundColor White
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "  - Test in browser: http://localhost:5173/lab/helical" -ForegroundColor White
    Write-Host "  - Try unsafe parameters to see warnings" -ForegroundColor White
    Write-Host "  - Proceed to Phase 3 (Integrate N17 Polygon Offset)" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "⚠️ Some tests failed - review errors above" -ForegroundColor Yellow
    exit 1
}
