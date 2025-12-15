#!/usr/bin/env pwsh
# Test Unit Conversion & Validation for NeckLab Presets
# Tests mm↔inch conversion, parameter validation, and revert functionality

$baseUrl = "http://localhost:8000"
Write-Host "=== Testing Unit Conversion & Validation ===" -ForegroundColor Cyan
Write-Host ""

# Test 1: Create metric preset (mm units)
Write-Host "1. Creating metric neck preset (mm units)..." -ForegroundColor Yellow
$metricPreset = @{
    name = "Test Metric Neck"
    description = "Test preset with millimeter dimensions"
    tags = @("test", "metric", "neck")
    kind = "neck"
    neck_params = @{
        units = "mm"
        scale_length = 628.65    # 24.75 inches in mm
        nut_width = 43.053       # 1.695 inches in mm
        heel_width = 57.15       # 2.25 inches in mm
        blank_length = 762.0     # 30 inches in mm
        blank_width = 82.55      # 3.25 inches in mm
        blank_thickness = 25.4   # 1.0 inch in mm
        neck_length = 406.4      # 16 inches in mm
        neck_angle = 4.0         # degrees (not converted)
        fretboard_radius = 304.8 # 12 inches in mm
        fretboard_offset = 1.5
        include_fretboard = $true
        thickness_1st_fret = 22.225  # 0.875 inch in mm
        thickness_12th_fret = 23.825 # 0.9375 inch in mm
        radius_at_1st = 31.75        # 1.25 inch in mm
        radius_at_12th = 34.925      # 1.375 inch in mm
        headstock_angle = 15.0
        headstock_length = 228.6     # 9 inches in mm
        headstock_thickness = 15.875 # 0.625 inch in mm
        tuner_layout = 82.55         # 3.25 inches in mm
        tuner_diameter = 10.0        # ~0.39 inch in mm
        alignment_pin_holes = $false
    }
}

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/presets" -Method Post -Body ($metricPreset | ConvertTo-Json -Depth 10) -ContentType "application/json"
    $metricPresetId = $response.id
    Write-Host "✓ Metric preset created: $metricPresetId" -ForegroundColor Green
    Write-Host "  scale_length: $($metricPreset.neck_params.scale_length) mm (should convert to 24.75 inches)" -ForegroundColor DarkGray
} catch {
    Write-Host "✗ Failed to create metric preset: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 2: Create imperial preset (inch units)
Write-Host "2. Creating imperial neck preset (inch units)..." -ForegroundColor Yellow
$imperialPreset = @{
    name = "Test Imperial Neck"
    description = "Test preset with inch dimensions"
    tags = @("test", "imperial", "neck")
    kind = "neck"
    neck_params = @{
        units = "inch"
        scale_length = 25.5      # Fender scale
        nut_width = 1.650
        heel_width = 2.125
        blank_length = 28.0
        blank_width = 3.0
        blank_thickness = 0.875
        neck_length = 15.0
        neck_angle = 0.0         # Fender style bolt-on
        fretboard_radius = 9.5
        fretboard_offset = 0.125
        include_fretboard = $true
        thickness_1st_fret = 0.800
        thickness_12th_fret = 0.950
        radius_at_1st = 1.125
        radius_at_12th = 1.250
        headstock_angle = 8.5
        headstock_length = 8.5
        headstock_thickness = 0.575
        tuner_layout = 3.0
        tuner_diameter = 0.375
        alignment_pin_holes = $true
    }
}

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/presets" -Method Post -Body ($imperialPreset | ConvertTo-Json -Depth 10) -ContentType "application/json"
    $imperialPresetId = $response.id
    Write-Host "✓ Imperial preset created: $imperialPresetId" -ForegroundColor Green
    Write-Host "  scale_length: $($imperialPreset.neck_params.scale_length) inch (no conversion needed)" -ForegroundColor DarkGray
} catch {
    Write-Host "✗ Failed to create imperial preset: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 3: Create invalid preset (out-of-range values)
Write-Host "3. Creating invalid neck preset (out-of-range values)..." -ForegroundColor Yellow
$invalidPreset = @{
    name = "Test Invalid Neck"
    description = "Test preset with invalid parameters for validation"
    tags = @("test", "invalid")
    kind = "neck"
    neck_params = @{
        units = "inch"
        scale_length = 35.0      # Too long (max 30)
        nut_width = 1.0          # Too narrow (min 1.5)
        neck_angle = 12.0        # Too steep (max 10)
        headstock_angle = 30.0   # Too steep (max 25)
        blank_thickness = 0.25   # Too thin (min 0.5)
        thickness_12th_fret = 0.65  # Less than 1st fret (should warn)
        thickness_1st_fret = 0.85
        heel_width = 1.5         # Less than nut_width (should warn)
        blank_length = 25.0
        blank_width = 3.0
        fretboard_radius = 12.0
        fretboard_offset = 0.1
        include_fretboard = $true
        radius_at_1st = 1.0
        radius_at_12th = 1.0
        headstock_length = 9.0
        headstock_thickness = 0.6
        tuner_layout = 3.0
        tuner_diameter = 0.35
        neck_length = 16.0
        alignment_pin_holes = $false
    }
}

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/presets" -Method Post -Body ($invalidPreset | ConvertTo-Json -Depth 10) -ContentType "application/json"
    $invalidPresetId = $response.id
    Write-Host "✓ Invalid preset created: $invalidPresetId" -ForegroundColor Green
    Write-Host "  (Backend allows invalid values; frontend should warn)" -ForegroundColor DarkGray
} catch {
    Write-Host "✗ Failed to create invalid preset: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 4: Fetch and verify conversion functions work
Write-Host "4. Testing conversion functions in TypeScript..." -ForegroundColor Yellow
Write-Host "  Manual verification required:" -ForegroundColor Cyan
Write-Host "  1. Load metric preset ($metricPresetId) in NeckLab" -ForegroundColor Cyan
Write-Host "     Expected: scale_length converts from 628.65mm to 24.75 inch" -ForegroundColor Cyan
Write-Host "  2. Load imperial preset ($imperialPresetId) in NeckLab" -ForegroundColor Cyan
Write-Host "     Expected: No conversion, loads as-is (25.5 inch)" -ForegroundColor Cyan
Write-Host "  3. Load invalid preset ($invalidPresetId) in NeckLab" -ForegroundColor Cyan
Write-Host "     Expected: Yellow warning box shows 6-8 validation warnings" -ForegroundColor Cyan
Write-Host ""

# Test 5: Verify validation warnings appear
Write-Host "5. Expected validation warnings for invalid preset:" -ForegroundColor Yellow
Write-Host "  ⚠ scale_length: 35.000 inch outside valid range (20-30 inch)" -ForegroundColor Yellow
Write-Host "  ⚠ nut_width: 1.000 inch outside valid range (1.5-2.5 inch)" -ForegroundColor Yellow
Write-Host "  ⚠ neck_angle: 12.000 degrees outside valid range (0-10 degrees)" -ForegroundColor Yellow
Write-Host "  ⚠ headstock_angle: 30.000 degrees outside valid range (0-25 degrees)" -ForegroundColor Yellow
Write-Host "  ⚠ blank_thickness: 0.250 inch outside valid range (0.5-2.0 inch)" -ForegroundColor Yellow
Write-Host "  ⚠ Neck thickness at 12th fret should be >= thickness at 1st fret" -ForegroundColor Yellow
Write-Host "  ⚠ Heel width should be >= nut width for typical neck taper" -ForegroundColor Yellow
Write-Host ""

# Test 6: Frontend test checklist
Write-Host "=== Frontend Test Checklist ===" -ForegroundColor Cyan
Write-Host "Open http://localhost:5173/lab/neck?preset_id=$metricPresetId" -ForegroundColor White
Write-Host "1. ✓ Blue banner shows: 'Loaded preset: Test Metric Neck (converted from mm to inch)'" -ForegroundColor White
Write-Host "2. ✓ scale_length field shows: 24.75 (not 628.65)" -ForegroundColor White
Write-Host "3. ✓ nut_width field shows: 1.695 (not 43.053)" -ForegroundColor White
Write-Host "4. ✓ No yellow validation warning box appears" -ForegroundColor White
Write-Host ""

Write-Host "Open http://localhost:5173/lab/neck?preset_id=$invalidPresetId" -ForegroundColor White
Write-Host "5. ✓ Blue banner shows: 'Loaded preset: Test Invalid Neck'" -ForegroundColor White
Write-Host "6. ✓ Yellow warning box appears with 6-8 warnings" -ForegroundColor White
Write-Host "7. ✓ Critical errors (scale_length, neck_angle) shown in red text" -ForegroundColor White
Write-Host "8. ✓ Warnings (thickness taper, heel/nut ratio) shown in yellow text" -ForegroundColor White
Write-Host ""

Write-Host "Modify any parameter and check:" -ForegroundColor White
Write-Host "9. ✓ Purple banner appears: 'Modified from preset'" -ForegroundColor White
Write-Host "10. ✓ 'Revert to Original' button is enabled" -ForegroundColor White
Write-Host "11. ✓ Click revert → form returns to loaded values" -ForegroundColor White
Write-Host "12. ✓ Revalidation occurs after revert" -ForegroundColor White
Write-Host ""

# Summary
Write-Host "=== Unit Conversion Tests Complete ===" -ForegroundColor Green
Write-Host "Created 3 test presets:" -ForegroundColor White
Write-Host "  - Metric preset: $metricPresetId (628.65mm → 24.75\")" -ForegroundColor White
Write-Host "  - Imperial preset: $imperialPresetId (25.5\" no conversion)" -ForegroundColor White
Write-Host "  - Invalid preset: $invalidPresetId (validation warnings)" -ForegroundColor White
Write-Host ""
Write-Host "Next: Complete frontend testing checklist above" -ForegroundColor Cyan
Write-Host "Expected conversion formula: inch = mm / 25.4" -ForegroundColor DarkGray
Write-Host "Expected conversion formula: mm = inch * 25.4" -ForegroundColor DarkGray
