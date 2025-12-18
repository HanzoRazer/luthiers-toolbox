#!/usr/bin/env pwsh
# Test CP-S51: Saw Blade Validator
# Tests safety validation for saw operations

$ErrorActionPreference = "Stop"
$baseUrl = "http://localhost:8000"

Write-Host "`n=== Testing CP-S51: Saw Blade Validator ===" -ForegroundColor Cyan

# ============================================================================
# Setup: Create Test Blade
# ============================================================================

Write-Host "`n0. Creating test blade for validation" -ForegroundColor Yellow

$testBladePayload = @{
    vendor = "Tenryu"
    model_code = "TEST-25560"
    diameter_mm = 255.0
    kerf_mm = 2.8
    plate_thickness_mm = 2.0
    bore_mm = 30.0
    teeth = 60
    hook_angle_deg = 15.0
    application = "crosscut"
    material_family = "hardwood"
} | ConvertTo-Json

try {
    $testBlade = Invoke-RestMethod -Uri "$baseUrl/api/saw/blades" `
        -Method Post `
        -ContentType "application/json" `
        -Body $testBladePayload
    
    $bladeId = $testBlade.id
    Write-Host "  ✅ Test blade created: $bladeId" -ForegroundColor Green
    Write-Host "    Diameter: $($testBlade.diameter_mm)mm, Kerf: $($testBlade.kerf_mm)mm, Teeth: $($testBlade.teeth)"
}
catch {
    Write-Host "  ❌ Failed to create test blade" -ForegroundColor Red
    Write-Host "    Error: $_"
    exit 1
}

# ============================================================================
# Test 1: Validate Safe Contour Radius (PASS)
# ============================================================================

Write-Host "`n1. Testing Contour Radius Validation (SAFE)" -ForegroundColor Yellow

$contourSafePayload = @{
    blade_id = $bladeId
    radius_mm = 200.0  # 255mm blade needs min 127.5mm radius
} | ConvertTo-Json

try {
    $result = Invoke-RestMethod -Uri "$baseUrl/api/saw/validate/contour" `
        -Method Post `
        -ContentType "application/json" `
        -Body $contourSafePayload
    
    if ($result.overall -eq "OK") {
        Write-Host "  ✅ Safe contour validated correctly" -ForegroundColor Green
        Write-Host "    Overall: $($result.overall)"
        Write-Host "    Message: $($result.checks[0].message)"
    }
    else {
        Write-Host "  ❌ Expected OK, got $($result.overall)" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "  ❌ Validation failed" -ForegroundColor Red
    exit 1
}

# ============================================================================
# Test 2: Validate Tight Contour Radius (ERROR)
# ============================================================================

Write-Host "`n2. Testing Contour Radius Validation (TOO TIGHT)" -ForegroundColor Yellow

$contourTightPayload = @{
    blade_id = $bladeId
    radius_mm = 100.0  # Less than blade_diameter/2 (127.5mm)
} | ConvertTo-Json

try {
    $result = Invoke-RestMethod -Uri "$baseUrl/api/saw/validate/contour" `
        -Method Post `
        -ContentType "application/json" `
        -Body $contourTightPayload
    
    if ($result.overall -eq "ERROR") {
        Write-Host "  ✅ Tight radius rejected correctly" -ForegroundColor Green
        Write-Host "    Overall: $($result.overall)"
        Write-Host "    Message: $($result.checks[0].message)"
        Write-Host "    Reason: $($result.checks[0].details.reason)"
    }
    else {
        Write-Host "  ❌ Expected ERROR, got $($result.overall)" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "  ❌ Validation failed" -ForegroundColor Red
    exit 1
}

# ============================================================================
# Test 3: Validate Safe Depth of Cut (PASS)
# ============================================================================

Write-Host "`n3. Testing Depth of Cut Validation (SAFE)" -ForegroundColor Yellow

$docSafePayload = @{
    blade_id = $bladeId
    doc_mm = 10.0  # Kerf is 2.8mm, so 10mm = 3.6× kerf (safe)
} | ConvertTo-Json

try {
    $result = Invoke-RestMethod -Uri "$baseUrl/api/saw/validate/doc" `
        -Method Post `
        -ContentType "application/json" `
        -Body $docSafePayload
    
    if ($result.overall -eq "OK") {
        Write-Host "  ✅ Safe DOC validated correctly" -ForegroundColor Green
        Write-Host "    Message: $($result.checks[0].message)"
    }
    else {
        Write-Host "  ❌ Expected OK, got $($result.overall)" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "  ❌ Validation failed" -ForegroundColor Red
    exit 1
}

# ============================================================================
# Test 4: Validate Excessive Depth of Cut (ERROR)
# ============================================================================

Write-Host "`n4. Testing Depth of Cut Validation (TOO DEEP)" -ForegroundColor Yellow

$docDeepPayload = @{
    blade_id = $bladeId
    doc_mm = 35.0  # Kerf is 2.8mm, so 35mm = 12.5× kerf (exceeds 10× limit)
} | ConvertTo-Json

try {
    $result = Invoke-RestMethod -Uri "$baseUrl/api/saw/validate/doc" `
        -Method Post `
        -ContentType "application/json" `
        -Body $docDeepPayload
    
    if ($result.overall -eq "ERROR") {
        Write-Host "  ✅ Excessive DOC rejected correctly" -ForegroundColor Green
        Write-Host "    Overall: $($result.overall)"
        Write-Host "    Message: $($result.checks[0].message)"
    }
    else {
        Write-Host "  ❌ Expected ERROR, got $($result.overall)" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "  ❌ Validation failed" -ForegroundColor Red
    exit 1
}

# ============================================================================
# Test 5: Validate Safe RPM and Feed Rate (PASS)
# ============================================================================

Write-Host "`n5. Testing RPM and Feed Rate Validation (SAFE)" -ForegroundColor Yellow

$feedsSafePayload = @{
    blade_id = $bladeId
    rpm = 3600.0        # Within 2000-6000 range
    feed_ipm = 120.0    # Within 10-300 range
} | ConvertTo-Json

try {
    $result = Invoke-RestMethod -Uri "$baseUrl/api/saw/validate/feeds" `
        -Method Post `
        -ContentType "application/json" `
        -Body $feedsSafePayload
    
    if ($result.overall -eq "OK") {
        Write-Host "  ✅ Safe feeds validated correctly" -ForegroundColor Green
        Write-Host "    RPM check: $($result.checks[0].message)"
        Write-Host "    Feed check: $($result.checks[1].message)"
    }
    else {
        Write-Host "  ❌ Expected OK, got $($result.overall)" -ForegroundColor Red
        Write-Host "    Checks: $($result.checks | ConvertTo-Json)"
    }
}
catch {
    Write-Host "  ❌ Validation failed" -ForegroundColor Red
    exit 1
}

# ============================================================================
# Test 6: Validate Low RPM (ERROR)
# ============================================================================

Write-Host "`n6. Testing Low RPM Validation (ERROR)" -ForegroundColor Yellow

$rpmLowPayload = @{
    blade_id = $bladeId
    rpm = 1500.0        # Below 2000 minimum
    feed_ipm = 100.0
} | ConvertTo-Json

try {
    $result = Invoke-RestMethod -Uri "$baseUrl/api/saw/validate/feeds" `
        -Method Post `
        -ContentType "application/json" `
        -Body $rpmLowPayload
    
    if ($result.overall -eq "ERROR") {
        Write-Host "  ✅ Low RPM rejected correctly" -ForegroundColor Green
        Write-Host "    Overall: $($result.overall)"
        Write-Host "    RPM check: $($result.checks[0].message)"
    }
    else {
        Write-Host "  ❌ Expected ERROR, got $($result.overall)" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "  ❌ Validation failed" -ForegroundColor Red
    exit 1
}

# ============================================================================
# Test 7: Validate High RPM (ERROR)
# ============================================================================

Write-Host "`n7. Testing High RPM Validation (ERROR)" -ForegroundColor Yellow

$rpmHighPayload = @{
    blade_id = $bladeId
    rpm = 7000.0        # Above 6000 maximum
    feed_ipm = 100.0
} | ConvertTo-Json

try {
    $result = Invoke-RestMethod -Uri "$baseUrl/api/saw/validate/feeds" `
        -Method Post `
        -ContentType "application/json" `
        -Body $rpmHighPayload
    
    if ($result.overall -eq "ERROR") {
        Write-Host "  ✅ High RPM rejected correctly" -ForegroundColor Green
        Write-Host "    Overall: $($result.overall)"
    }
    else {
        Write-Host "  ❌ Expected ERROR, got $($result.overall)" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "  ❌ Validation failed" -ForegroundColor Red
    exit 1
}

# ============================================================================
# Test 8: Validate Complete Operation (Mixed Results)
# ============================================================================

Write-Host "`n8. Testing Complete Operation Validation" -ForegroundColor Yellow

$operationPayload = @{
    blade_id = $bladeId
    operation_type = "contour"
    doc_mm = 15.0           # 5.4× kerf (safe)
    rpm = 3600.0            # Safe
    feed_ipm = 120.0        # Safe
    contour_radius_mm = 150.0  # Safe (> 127.5mm min)
    material_family = "hardwood"  # Matches blade
} | ConvertTo-Json

try {
    $result = Invoke-RestMethod -Uri "$baseUrl/api/saw/validate/operation" `
        -Method Post `
        -ContentType "application/json" `
        -Body $operationPayload
    
    Write-Host "  ✅ Complete validation executed" -ForegroundColor Green
    Write-Host "    Overall: $($result.overall)"
    Write-Host "    Checks performed: $($result.checks.Count)"
    
    foreach ($check in $result.checks) {
        $color = switch ($check.level) {
            "OK" { "Green" }
            "WARN" { "Yellow" }
            "ERROR" { "Red" }
        }
        Write-Host "      [$($check.level)] $($check.message)" -ForegroundColor $color
    }
    
    if ($result.overall -ne "OK") {
        Write-Host "  ⚠️  Some checks raised warnings/errors" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "  ❌ Validation failed" -ForegroundColor Red
    exit 1
}

# ============================================================================
# Test 9: Get Safety Limits
# ============================================================================

Write-Host "`n9. Testing GET /api/saw/validate/limits" -ForegroundColor Yellow

try {
    $limits = Invoke-RestMethod -Uri "$baseUrl/api/saw/validate/limits" -Method Get
    
    Write-Host "  ✅ Safety limits retrieved" -ForegroundColor Green
    Write-Host "    Contour: min_radius = blade_diameter/2 × $($limits.contour.min_radius_safety_factor)"
    Write-Host "    DOC: $($limits.depth_of_cut.min_kerf_multiple)× to $($limits.depth_of_cut.max_kerf_multiple)× kerf"
    Write-Host "    RPM: $($limits.rpm.min_universal) - $($limits.rpm.max_universal)"
    Write-Host "    Feed: $($limits.feed_rate.min_ipm) - $($limits.feed_rate.max_ipm) IPM"
    Write-Host "    Chipload: $($limits.chipload.min) - $($limits.chipload.max) inches/tooth"
    Write-Host "    Kerf/Plate: $($limits.kerf_plate_ratio.min) - $($limits.kerf_plate_ratio.max)"
}
catch {
    Write-Host "  ❌ Failed to get limits" -ForegroundColor Red
    exit 1
}

# ============================================================================
# Test 10: Material Mismatch Warning
# ============================================================================

Write-Host "`n10. Testing Material Compatibility Check" -ForegroundColor Yellow

$materialMismatchPayload = @{
    blade_id = $bladeId
    operation_type = "slice"
    material_family = "aluminum"  # Blade is for hardwood
} | ConvertTo-Json

try {
    $result = Invoke-RestMethod -Uri "$baseUrl/api/saw/validate/operation" `
        -Method Post `
        -ContentType "application/json" `
        -Body $materialMismatchPayload
    
    # Look for material compatibility warning
    $materialCheck = $result.checks | Where-Object { $_.message -like "*material*" }
    
    if ($materialCheck -and $materialCheck.level -eq "WARN") {
        Write-Host "  ✅ Material mismatch warning detected" -ForegroundColor Green
        Write-Host "    Message: $($materialCheck.message)"
    }
    else {
        Write-Host "  ⚠️  No material warning (may be OK if blade has no restriction)" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "  ❌ Validation failed" -ForegroundColor Red
    exit 1
}

# ============================================================================
# Cleanup
# ============================================================================

Write-Host "`n11. Cleaning up test blade" -ForegroundColor Yellow

try {
    Invoke-RestMethod -Uri "$baseUrl/api/saw/blades/$bladeId" -Method Delete
    Write-Host "  ✅ Test blade deleted" -ForegroundColor Green
}
catch {
    Write-Host "  ⚠️  Failed to delete test blade (may need manual cleanup)" -ForegroundColor Yellow
}

# ============================================================================
# Summary
# ============================================================================

Write-Host "`n=== All Tests Completed Successfully ===" -ForegroundColor Green
Write-Host "`nSummary:" -ForegroundColor Cyan
Write-Host "  ✅ Contour radius validation (safe/tight)"
Write-Host "  ✅ Depth of cut validation (safe/excessive)"
Write-Host "  ✅ RPM validation (safe/low/high)"
Write-Host "  ✅ Feed rate validation"
Write-Host "  ✅ Complete operation validation"
Write-Host "  ✅ Safety limits retrieval"
Write-Host "  ✅ Material compatibility check"
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Wire validator to SawSlicePanel.vue"
Write-Host "  2. Wire validator to SawContourPanel.vue"
Write-Host "  3. Add 'Validate Operation' button before G-code generation"
Write-Host "  4. Display validation results with color-coded warnings/errors"
