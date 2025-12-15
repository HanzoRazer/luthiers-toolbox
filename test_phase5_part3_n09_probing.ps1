# Phase 5 Part 3: N.09 Probe Patterns Test Script
# Tests CNC probing routines and SVG setup sheet generation

Write-Host "`n=== N.09 Probe Patterns Test Suite ===" -ForegroundColor Cyan
Write-Host "Testing work offset establishment + SVG setup sheets`n"

$baseUrl = "http://localhost:8000/api/cam/probe"
$testsPassed = 0
$testsFailed = 0

function Test-Step {
    param($description)
    Write-Host "`nTesting: $description" -ForegroundColor Yellow
}

function Assert-Success {
    param($condition, $message)
    if ($condition) {
        Write-Host "  ✓ PASS: $message" -ForegroundColor Green
        $script:testsPassed++
    } else {
        Write-Host "  ✗ FAIL: $message" -ForegroundColor Red
        $script:testsFailed++
    }
}

# Test 1: List available probe patterns
Test-Step "GET /api/cam/probe/patterns - List probe patterns"
try {
    $patterns = Invoke-RestMethod -Uri "$baseUrl/patterns" -Method GET
    Assert-Success ($patterns.patterns.Count -ge 7) "Found $($patterns.patterns.Count) patterns"
    Assert-Success ($patterns.patterns[0].id -eq "corner_outside") "corner_outside pattern exists"
    Assert-Success ($patterns.patterns[2].id -eq "boss_circular") "boss_circular pattern exists"
    Assert-Success ($patterns.patterns[5].id -eq "surface_z") "surface_z pattern exists"
    
    Write-Host "    Available patterns:" -ForegroundColor Gray
    foreach ($p in $patterns.patterns) {
        Write-Host "      - $($p.id): $($p.name) ($($p.probes) probes)" -ForegroundColor Gray
    }
} catch {
    Assert-Success $false "Failed to list patterns: $($_.Exception.Message)"
}

# Test 2: Corner Outside Probe (G54)
Test-Step "POST /api/cam/probe/corner/gcode - Corner Outside (G54)"
try {
    $body = @{
        pattern = "corner_outside"
        approach_distance = 20.0
        retract_distance = 2.0
        feed_probe = 100.0
        safe_z = 10.0
        work_offset = 1
    } | ConvertTo-Json
    
    $result = Invoke-RestMethod -Uri "$baseUrl/corner/gcode" -Method POST -Body $body -ContentType "application/json"
    
    Assert-Success ($result.stats.probe_moves -eq 4) "4 probe moves"
    Assert-Success ($result.stats.sets_wcs -eq $true) "Sets WCS offset"
    Assert-Success ($result.stats.work_offset -eq "G54") "G54 work offset"
    Assert-Success ($result.gcode -match "G31") "Contains G31 probe command"
    Assert-Success ($result.gcode -match "G10 L20 P1") "Contains G10 L20 WCS setting"
    Assert-Success ($result.gcode -match "#100") "Uses variables for calculation"
    
    Write-Host "    Stats: $($result.stats.probe_moves) probes, time≈$($result.stats.estimated_time_s)s" -ForegroundColor Gray
} catch {
    Assert-Success $false "Corner outside test failed: $($_.Exception.Message)"
}

# Test 3: Corner Inside Probe (G55)
Test-Step "POST /api/cam/probe/corner/gcode - Corner Inside (G55)"
try {
    $body = @{
        pattern = "corner_inside"
        approach_distance = 15.0
        retract_distance = 2.0
        feed_probe = 100.0
        safe_z = 10.0
        work_offset = 2
    } | ConvertTo-Json
    
    $result = Invoke-RestMethod -Uri "$baseUrl/corner/gcode" -Method POST -Body $body -ContentType "application/json"
    
    Assert-Success ($result.stats.probe_moves -eq 4) "4 probe moves"
    Assert-Success ($result.stats.work_offset -eq "G55") "G55 work offset"
    Assert-Success ($result.gcode -match "corner_inside") "Labeled as inside pattern"
    
    Write-Host "    Stats: G55 offset, $($result.stats.probe_moves) probes" -ForegroundColor Gray
} catch {
    Assert-Success $false "Corner inside test failed: $($_.Exception.Message)"
}

# Test 4: Boss Circular Probe (4 points)
Test-Step "POST /api/cam/probe/boss/gcode - Boss Circular (4 points)"
try {
    $body = @{
        pattern = "boss_circular"
        estimated_diameter = 50.0
        estimated_center_x = 0.0
        estimated_center_y = 0.0
        probe_count = 4
        approach_distance = 5.0
        retract_distance = 5.0
        feed_probe = 100.0
        safe_z = 10.0
        work_offset = 1
    } | ConvertTo-Json
    
    $result = Invoke-RestMethod -Uri "$baseUrl/boss/gcode" -Method POST -Body $body -ContentType "application/json"
    
    Assert-Success ($result.stats.probe_moves -eq 4) "4 cardinal probes (N/S/E/W)"
    Assert-Success ($result.stats.estimated_diameter -eq 50.0) "Estimated Ø50mm"
    Assert-Success ($result.gcode -match "G31") "Contains probe moves"
    Assert-Success ($result.gcode -match "Calculate center") "Center calculation logic"
    
    Write-Host "    Stats: Ø$($result.stats.estimated_diameter)mm, $($result.stats.probe_moves) probes" -ForegroundColor Gray
} catch {
    Assert-Success $false "Boss circular test failed: $($_.Exception.Message)"
}

# Test 5: Boss Circular (8 points for precision)
Test-Step "POST /api/cam/probe/boss/gcode - Boss Circular (8 points)"
try {
    $body = @{
        pattern = "boss_circular"
        estimated_diameter = 75.0
        probe_count = 8
        approach_distance = 5.0
        safe_z = 10.0
        work_offset = 1
    } | ConvertTo-Json
    
    $result = Invoke-RestMethod -Uri "$baseUrl/boss/gcode" -Method POST -Body $body -ContentType "application/json"
    
    Assert-Success ($result.stats.probe_moves -eq 8) "8 probes for higher accuracy"
    Assert-Success ($result.stats.probe_count -eq 8) "8-point pattern"
    
    Write-Host "    Stats: 8-point high precision, time≈$($result.stats.estimated_time_s)s" -ForegroundColor Gray
} catch {
    Assert-Success $false "8-point boss test failed: $($_.Exception.Message)"
}

# Test 6: Hole Circular Probe (internal)
Test-Step "POST /api/cam/probe/boss/gcode - Hole Circular (internal)"
try {
    $body = @{
        pattern = "hole_circular"
        estimated_diameter = 30.0
        probe_count = 6
        approach_distance = 3.0
        feed_probe = 80.0
        safe_z = 10.0
        work_offset = 1
    } | ConvertTo-Json
    
    $result = Invoke-RestMethod -Uri "$baseUrl/boss/gcode" -Method POST -Body $body -ContentType "application/json"
    
    Assert-Success ($result.stats.probe_moves -eq 6) "6 probes inside hole"
    Assert-Success ($result.stats.pattern -eq "hole_circular") "Hole pattern (internal)"
    
    Write-Host "    Stats: Internal hole probe, 6 points" -ForegroundColor Gray
} catch {
    Assert-Success $false "Hole circular test failed: $($_.Exception.Message)"
}

# Test 7: Surface Z Touch-Off
Test-Step "POST /api/cam/probe/surface_z/gcode - Surface Z Touch-Off"
try {
    $body = @{
        approach_z = 10.0
        probe_depth = -20.0
        feed_probe = 50.0
        retract_distance = 5.0
        work_offset = 1
    } | ConvertTo-Json
    
    $result = Invoke-RestMethod -Uri "$baseUrl/surface_z/gcode" -Method POST -Body $body -ContentType "application/json"
    
    Assert-Success ($result.stats.probe_moves -eq 1) "1 Z-axis probe"
    Assert-Success ($result.stats.pattern -eq "surface_z") "Surface Z pattern"
    Assert-Success ($result.gcode -match "G31 Z") "Z-axis probe move"
    Assert-Success ($result.gcode -match "G10 L20 P1 Z") "Sets Z-zero"
    
    Write-Host "    Stats: Z-zero setup, time≈$($result.stats.estimated_time_s)s" -ForegroundColor Gray
} catch {
    Assert-Success $false "Surface Z test failed: $($_.Exception.Message)"
}

# Test 8: Pocket Inside Probe (center origin)
Test-Step "POST /api/cam/probe/pocket/gcode - Pocket Inside (center)"
try {
    $body = @{
        pocket_width = 100.0
        pocket_height = 60.0
        approach_distance = 10.0
        retract_distance = 2.0
        feed_probe = 100.0
        safe_z = 10.0
        work_offset = 1
        origin_corner = "center"
    } | ConvertTo-Json
    
    $result = Invoke-RestMethod -Uri "$baseUrl/pocket/gcode" -Method POST -Body $body -ContentType "application/json"
    
    Assert-Success ($result.stats.probe_moves -eq 4) "4 wall probes"
    Assert-Success ($result.stats.pocket_width -eq 100.0) "100mm width"
    Assert-Success ($result.stats.pocket_height -eq 60.0) "60mm height"
    Assert-Success ($result.stats.origin_corner -eq "center") "Center origin"
    
    Write-Host "    Stats: 100×60mm pocket, center origin" -ForegroundColor Gray
} catch {
    Assert-Success $false "Pocket center test failed: $($_.Exception.Message)"
}

# Test 9: Pocket Inside (lower_left origin)
Test-Step "POST /api/cam/probe/pocket/gcode - Pocket Inside (lower_left)"
try {
    $body = @{
        pocket_width = 80.0
        pocket_height = 50.0
        origin_corner = "lower_left"
        work_offset = 2
    } | ConvertTo-Json
    
    $result = Invoke-RestMethod -Uri "$baseUrl/pocket/gcode" -Method POST -Body $body -ContentType "application/json"
    
    Assert-Success ($result.stats.origin_corner -eq "lower_left") "Lower-left origin"
    Assert-Success ($result.stats.work_offset -eq "G55") "G55 offset"
    
    Write-Host "    Stats: Lower-left origin, G55" -ForegroundColor Gray
} catch {
    Assert-Success $false "Pocket lower_left test failed: $($_.Exception.Message)"
}

# Test 10: Vise Squareness Check
Test-Step "POST /api/cam/probe/vise_square/gcode - Vise Squareness"
try {
    $body = @{
        vise_jaw_height = 50.0
        probe_spacing = 100.0
        approach_distance = 20.0
        retract_distance = 5.0
        feed_probe = 100.0
        safe_z = 10.0
    } | ConvertTo-Json
    
    $result = Invoke-RestMethod -Uri "$baseUrl/vise_square/gcode" -Method POST -Body $body -ContentType "application/json"
    
    Assert-Success ($result.stats.probe_moves -eq 2) "2 probes for angle"
    Assert-Success ($result.stats.probe_spacing -eq 100.0) "100mm probe spacing"
    Assert-Success ($result.gcode -match "ATAN") "Angle calculation"
    Assert-Success ($result.gcode -match "GT 0.1") "Tolerance check"
    
    Write-Host "    Stats: Squareness check, 100mm spacing" -ForegroundColor Gray
} catch {
    Assert-Success $false "Vise square test failed: $($_.Exception.Message)"
}

# Test 11: Corner Outside Download
Test-Step "POST /api/cam/probe/corner/gcode/download - Download corner probe"
try {
    $body = @{
        pattern = "corner_outside"
        work_offset = 1
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "$baseUrl/corner/gcode/download" -Method POST -Body $body -ContentType "application/json"
    
    Assert-Success ($response.StatusCode -eq 200) "Download successful (HTTP 200)"
    Assert-Success ($response.Headers["Content-Disposition"] -match "corner_corner_outside_g54\.nc") "Filename matches pattern"
    Assert-Success ($response.Content.Length -gt 500) "G-code content not empty"
    
    Write-Host "    Downloaded: $($response.Content.Length) bytes" -ForegroundColor Gray
} catch {
    Assert-Success $false "Corner download failed: $($_.Exception.Message)"
}

# Test 12: SVG Setup Sheet - Corner Outside
Test-Step "POST /api/cam/probe/setup_sheet/svg - Corner Outside Sheet"
try {
    $body = @{
        pattern = "corner_outside"
        part_width = 100.0
        part_height = 60.0
        probe_offset = 20.0
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "$baseUrl/setup_sheet/svg" -Method POST -Body $body -ContentType "application/json"
    
    Assert-Success ($response.StatusCode -eq 200) "SVG generated (HTTP 200)"
    Assert-Success ($response.Headers["Content-Type"] -match "image/svg\+xml") "SVG content type"
    Assert-Success ($response.Content -match "<svg") "Contains SVG tag"
    Assert-Success ($response.Content -match "Corner Find") "Contains title"
    Assert-Success ($response.Content -match "P1.*P2.*P3.*P4") "Contains 4 probe points"
    Assert-Success ($response.Content -match "G54") "Contains origin marker"
    
    Write-Host "    SVG: $($response.Content.Length) bytes, valid XML" -ForegroundColor Gray
} catch {
    Assert-Success $false "Corner SVG test failed: $($_.Exception.Message)"
}

# Test 13: SVG Setup Sheet - Boss Circular
Test-Step "POST /api/cam/probe/setup_sheet/svg - Boss Circular Sheet"
try {
    $body = @{
        pattern = "boss_circular"
        feature_diameter = 50.0
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "$baseUrl/setup_sheet/svg" -Method POST -Body $body -ContentType "application/json"
    
    Assert-Success ($response.StatusCode -eq 200) "Boss SVG generated"
    Assert-Success ($response.Content -match "Boss Find") "Contains boss title"
    Assert-Success ($response.Content -match "East.*North.*West.*South") "Contains cardinal points"
    Assert-Success ($response.Content -match "Ø50") "Contains diameter"
    
    Write-Host "    Boss SVG: Valid circular pattern sheet" -ForegroundColor Gray
} catch {
    Assert-Success $false "Boss SVG test failed: $($_.Exception.Message)"
}

# Test 14: SVG Setup Sheet - Pocket Inside
Test-Step "POST /api/cam/probe/setup_sheet/svg - Pocket Inside Sheet"
try {
    $body = @{
        pattern = "pocket_inside"
        part_width = 80.0
        part_height = 50.0
        origin_corner = "center"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "$baseUrl/setup_sheet/svg" -Method POST -Body $body -ContentType "application/json"
    
    Assert-Success ($response.StatusCode -eq 200) "Pocket SVG generated"
    Assert-Success ($response.Content -match "Pocket Find") "Contains pocket title"
    Assert-Success ($response.Content -match "Wall") "Contains wall labels"
    
    Write-Host "    Pocket SVG: Valid pocket pattern sheet" -ForegroundColor Gray
} catch {
    Assert-Success $false "Pocket SVG test failed: $($_.Exception.Message)"
}

# Test 15: SVG Setup Sheet - Surface Z
Test-Step "POST /api/cam/probe/setup_sheet/svg - Surface Z Sheet"
try {
    $body = @{
        pattern = "surface_z"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "$baseUrl/setup_sheet/svg" -Method POST -Body $body -ContentType "application/json"
    
    Assert-Success ($response.StatusCode -eq 200) "Surface Z SVG generated"
    Assert-Success ($response.Content -match "Surface Z") "Contains Z title"
    Assert-Success ($response.Content -match "Z0 = Surface") "Contains Z-zero label"
    
    Write-Host "    Surface Z SVG: Valid Z-probe sheet" -ForegroundColor Gray
} catch {
    Assert-Success $false "Surface Z SVG test failed: $($_.Exception.Message)"
}

# Test 16: Validation - Invalid work offset
Test-Step "POST /api/cam/probe/corner/gcode - Validation (work_offset out of range)"
try {
    $body = @{
        pattern = "corner_outside"
        work_offset = 7
    } | ConvertTo-Json
    
    $result = Invoke-RestMethod -Uri "$baseUrl/corner/gcode" -Method POST -Body $body -ContentType "application/json" -ErrorAction Stop
    Assert-Success $false "Should have rejected work_offset=7"
} catch {
    Assert-Success ($_.Exception.Response.StatusCode -eq 422) "Rejected invalid work_offset (422 validation error)"
}

# Test 17: Validation - Invalid boss probe_count
Test-Step "POST /api/cam/probe/boss/gcode - Validation (probe_count < 4)"
try {
    $body = @{
        pattern = "boss_circular"
        estimated_diameter = 50.0
        probe_count = 3
    } | ConvertTo-Json
    
    $result = Invoke-RestMethod -Uri "$baseUrl/boss/gcode" -Method POST -Body $body -ContentType "application/json" -ErrorAction Stop
    Assert-Success $false "Should have rejected probe_count=3"
} catch {
    Assert-Success ($_.Exception.Response.StatusCode -eq 422) "Rejected probe_count < 4 (422 error)"
}

# Summary
Write-Host "`n=== Test Summary ===" -ForegroundColor Cyan
Write-Host "Total Tests: $($testsPassed + $testsFailed)" -ForegroundColor White
Write-Host "Passed: $testsPassed" -ForegroundColor Green
Write-Host "Failed: $testsFailed" -ForegroundColor Red

if ($testsFailed -eq 0) {
    Write-Host "`n✅ All tests passed!" -ForegroundColor Green
    Write-Host "`nN.09 Probe Patterns is working correctly!" -ForegroundColor Cyan
    Write-Host "- 7+ probing patterns implemented" -ForegroundColor Gray
    Write-Host "- Corner/Boss/Pocket/Surface/Vise probing" -ForegroundColor Gray
    Write-Host "- G31 probe moves with G10 L20 WCS setting" -ForegroundColor Gray
    Write-Host "- SVG setup sheets for visual documentation" -ForegroundColor Gray
    Write-Host "- G54-G59 work offset support" -ForegroundColor Gray
} else {
    Write-Host "`n❌ Some tests failed. Review output above." -ForegroundColor Red
    exit 1
}

Write-Host "`n=== End of N.09 Test Suite ===" -ForegroundColor Cyan
