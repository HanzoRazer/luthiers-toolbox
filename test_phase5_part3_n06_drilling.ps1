# Phase 5 Part 3: N.06 Modal Cycles Test Script
# Tests drilling operations (G81-G89) with modal and expanded modes

Write-Host "`n=== N.06 Modal Cycles Test Suite ===" -ForegroundColor Cyan
Write-Host "Testing drilling operations with smart post-processor adaptation`n"

$baseUrl = "http://localhost:8000/api/cam"
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

# Test 1: List available cycles
Test-Step "GET /api/cam/drill/cycles - List available cycles"
try {
    $cycles = Invoke-RestMethod -Uri "$baseUrl/drill/cycles" -Method GET
    Assert-Success ($cycles.cycles.Count -ge 5) "Found $($cycles.cycles.Count) cycles"
    Assert-Success ($cycles.cycles[0].id -eq "G81") "G81 cycle exists"
    Assert-Success ($cycles.cycles[1].id -eq "G83") "G83 cycle exists"
    Assert-Success ($cycles.cycles[3].id -eq "G84") "G84 tapping cycle exists"
} catch {
    Assert-Success $false "Failed to list cycles: $($_.Exception.Message)"
}

# Test 2: G81 Simple Drill (GRBL - expanded)
Test-Step "POST /api/cam/drill/gcode - G81 Simple Drill (GRBL expanded)"
try {
    $body = @{
        cycle = "G81"
        holes = @(
            @{x = 10.0; y = 10.0},
            @{x = 20.0; y = 10.0},
            @{x = 30.0; y = 10.0}
        )
        depth = -20.0
        retract = 2.0
        feed = 300.0
        safe_z = 10.0
        post_id = "GRBL"
    } | ConvertTo-Json -Depth 10
    
    $result = Invoke-RestMethod -Uri "$baseUrl/drill/gcode" -Method POST -Body $body -ContentType "application/json"
    
    Assert-Success ($result.stats.holes -eq 3) "Processed 3 holes"
    Assert-Success ($result.stats.mode -eq "expanded") "GRBL uses expanded mode"
    Assert-Success ($result.gcode -match "G0") "Contains G0 rapid moves"
    Assert-Success ($result.gcode -match "G1.*Z-20\.0") "Drills to -20mm depth"
    Assert-Success ($result.gcode -notmatch "^G81") "No G81 canned cycle in move (expanded)"
    
    Write-Host "    Stats: $($result.stats.holes) holes, mode=$($result.stats.mode)" -ForegroundColor Gray
} catch {
    Assert-Success $false "G81 GRBL test failed: $($_.Exception.Message)"
}

# Test 3: G81 Simple Drill (Mach4 - modal)
Test-Step "POST /api/cam/drill/gcode - G81 Simple Drill (Mach4 modal)"
try {
    $body = @{
        cycle = "G81"
        holes = @(
            @{x = 10.0; y = 10.0},
            @{x = 20.0; y = 10.0}
        )
        depth = -15.0
        retract = 2.0
        feed = 400.0
        safe_z = 10.0
        post_id = "Mach4"
    } | ConvertTo-Json -Depth 10
    
    $result = Invoke-RestMethod -Uri "$baseUrl/drill/gcode" -Method POST -Body $body -ContentType "application/json"
    
    Assert-Success ($result.stats.holes -eq 2) "Processed 2 holes"
    Assert-Success ($result.stats.mode -eq "modal") "Mach4 uses modal mode"
    Assert-Success ($result.gcode -match "G81") "Contains G81 canned cycle"
    Assert-Success ($result.gcode -match "G80") "Contains G80 cancel"
    
    Write-Host "    Stats: $($result.stats.holes) holes, mode=$($result.stats.mode)" -ForegroundColor Gray
} catch {
    Assert-Success $false "G81 Mach4 test failed: $($_.Exception.Message)"
}

# Test 4: G83 Peck Drill
Test-Step "POST /api/cam/drill/gcode - G83 Peck Drill"
try {
    $body = @{
        cycle = "G83"
        holes = @(
            @{x = 15.0; y = 15.0},
            @{x = 25.0; y = 15.0}
        )
        depth = -30.0
        retract = 2.0
        feed = 250.0
        safe_z = 10.0
        peck_depth = 5.0
        post_id = "LinuxCNC"
    } | ConvertTo-Json -Depth 10
    
    $result = Invoke-RestMethod -Uri "$baseUrl/drill/gcode" -Method POST -Body $body -ContentType "application/json"
    
    Assert-Success ($result.stats.cycle -eq "G83") "G83 cycle type"
    Assert-Success ($result.stats.peck_depth -eq 5.0) "Peck depth 5mm"
    Assert-Success ($result.stats.pecks_per_hole -ge 6) "At least 6 pecks per hole (30mm / 5mm)"
    Assert-Success ($result.gcode -match "G83") "Contains G83 cycle"
    
    Write-Host "    Stats: $($result.stats.pecks_per_hole) pecks/hole, depth=$($result.stats.depth)mm" -ForegroundColor Gray
} catch {
    Assert-Success $false "G83 test failed: $($_.Exception.Message)"
}

# Test 5: G73 Chip Break
Test-Step "POST /api/cam/drill/gcode - G73 Chip Break"
try {
    $body = @{
        cycle = "G73"
        holes = @(
            @{x = 12.0; y = 12.0}
        )
        depth = -25.0
        retract = 2.0
        feed = 300.0
        safe_z = 10.0
        peck_depth = 6.0
        post_id = "Haas"
    } | ConvertTo-Json -Depth 10
    
    $result = Invoke-RestMethod -Uri "$baseUrl/drill/gcode" -Method POST -Body $body -ContentType "application/json"
    
    Assert-Success ($result.stats.cycle -eq "G73") "G73 cycle type"
    Assert-Success ($result.stats.peck_depth -eq 6.0) "Peck depth 6mm"
    Assert-Success ($result.gcode -match "G73") "Contains G73 cycle"
    
    Write-Host "    Stats: chip break mode, depth=$($result.stats.depth)mm" -ForegroundColor Gray
} catch {
    Assert-Success $false "G73 test failed: $($_.Exception.Message)"
}

# Test 6: G84 Rigid Tap
Test-Step "POST /api/cam/drill/gcode - G84 Rigid Tap (M6×1.0)"
try {
    $body = @{
        cycle = "G84"
        holes = @(
            @{x = 18.0; y = 18.0},
            @{x = 28.0; y = 18.0}
        )
        depth = -18.0
        retract = 2.0
        thread_pitch = 1.0
        spindle_rpm = 500.0
        safe_z = 10.0
        post_id = "Mach4"
    } | ConvertTo-Json -Depth 10
    
    $result = Invoke-RestMethod -Uri "$baseUrl/drill/gcode" -Method POST -Body $body -ContentType "application/json"
    
    $expectedFeed = 500.0 * 1.0  # RPM × pitch = 500 mm/min
    
    Assert-Success ($result.stats.cycle -eq "G84") "G84 cycle type"
    Assert-Success ($result.stats.thread_pitch -eq 1.0) "Thread pitch 1.0mm"
    Assert-Success ($result.stats.tap_feed -eq $expectedFeed) "Tap feed = RPM × pitch = $expectedFeed mm/min"
    Assert-Success ($result.gcode -match "G84") "Contains G84 cycle"
    Assert-Success ($result.gcode -match "M3|M4") "Contains spindle commands"
    
    Write-Host "    Stats: M6×1.0 thread, feed=$($result.stats.tap_feed) mm/min" -ForegroundColor Gray
} catch {
    Assert-Success $false "G84 test failed: $($_.Exception.Message)"
}

# Test 7: G85 Boring
Test-Step "POST /api/cam/drill/gcode - G85 Boring"
try {
    $body = @{
        cycle = "G85"
        holes = @(
            @{x = 14.0; y = 14.0}
        )
        depth = -12.0
        retract = 2.0
        feed = 200.0
        safe_z = 10.0
        post_id = "PathPilot"
    } | ConvertTo-Json -Depth 10
    
    $result = Invoke-RestMethod -Uri "$baseUrl/drill/gcode" -Method POST -Body $body -ContentType "application/json"
    
    Assert-Success ($result.stats.cycle -eq "G85") "G85 cycle type"
    Assert-Success ($result.gcode -match "G85") "Contains G85 cycle"
    
    Write-Host "    Stats: boring mode, depth=$($result.stats.depth)mm" -ForegroundColor Gray
} catch {
    Assert-Success $false "G85 test failed: $($_.Exception.Message)"
}

# Test 8: Force Expansion (override post)
Test-Step "POST /api/cam/drill/gcode - Force expansion (Mach4 → expanded)"
try {
    $body = @{
        cycle = "G81"
        holes = @(
            @{x = 5.0; y = 5.0}
        )
        depth = -10.0
        retract = 2.0
        feed = 300.0
        safe_z = 10.0
        post_id = "Mach4"
        expand_cycles = $true
    } | ConvertTo-Json -Depth 10
    
    $result = Invoke-RestMethod -Uri "$baseUrl/drill/gcode" -Method POST -Body $body -ContentType "application/json"
    
    Assert-Success ($result.stats.mode -eq "expanded") "Forced expansion despite Mach4 post"
    Assert-Success ($result.gcode -notmatch "^G81") "No canned cycle in move (forced expand)"
    
    Write-Host "    Stats: forced expansion mode" -ForegroundColor Gray
} catch {
    Assert-Success $false "Force expansion test failed: $($_.Exception.Message)"
}

# Test 9: Validation - No holes
Test-Step "POST /api/cam/drill/gcode - Validation (no holes)"
try {
    $body = @{
        cycle = "G81"
        holes = @()
        depth = -10.0
    } | ConvertTo-Json -Depth 10
    
    $result = Invoke-RestMethod -Uri "$baseUrl/drill/gcode" -Method POST -Body $body -ContentType "application/json" -ErrorAction Stop
    Assert-Success $false "Should have rejected empty holes array"
} catch {
    Assert-Success ($_.Exception.Response.StatusCode -eq 400) "Rejected empty holes (400 error)"
}

# Test 10: Validation - G84 without thread_pitch
Test-Step "POST /api/cam/drill/gcode - Validation (G84 missing pitch)"
try {
    $body = @{
        cycle = "G84"
        holes = @(@{x = 10; y = 10})
        depth = -10.0
        spindle_rpm = 500.0
    } | ConvertTo-Json -Depth 10
    
    $result = Invoke-RestMethod -Uri "$baseUrl/drill/gcode" -Method POST -Body $body -ContentType "application/json" -ErrorAction Stop
    Assert-Success $false "Should have rejected G84 without thread_pitch"
} catch {
    Assert-Success ($_.Exception.Response.StatusCode -eq 400) "Rejected G84 without pitch (400 error)"
}

# Test 11: Get post support info
Test-Step "GET /api/cam/drill/posts - Get post-processor support"
try {
    $postInfo = Invoke-RestMethod -Uri "$baseUrl/drill/posts" -Method GET
    Assert-Success ($postInfo.modal_cycles_supported.Count -gt 0) "Found posts supporting modal cycles"
    Assert-Success ($postInfo.requires_expansion.Count -gt 0) "Found posts requiring expansion"
    Assert-Success ($postInfo.requires_expansion -contains "GRBL") "GRBL listed as requiring expansion"
    
    Write-Host "    Modal supported: $($postInfo.modal_cycles_supported -join ', ')" -ForegroundColor Gray
    Write-Host "    Requires expansion: $($postInfo.requires_expansion -join ', ')" -ForegroundColor Gray
} catch {
    Assert-Success $false "Post support info failed: $($_.Exception.Message)"
}

# Test 12: Download G-code file
Test-Step "POST /api/cam/drill/gcode/download - Download as .nc file"
try {
    $body = @{
        cycle = "G83"
        holes = @(
            @{x = 10.0; y = 10.0}
        )
        depth = -15.0
        retract = 2.0
        feed = 300.0
        peck_depth = 5.0
        post_id = "GRBL"
    } | ConvertTo-Json -Depth 10
    
    $response = Invoke-WebRequest -Uri "$baseUrl/drill/gcode/download" -Method POST -Body $body -ContentType "application/json"
    
    Assert-Success ($response.StatusCode -eq 200) "Download successful (HTTP 200)"
    Assert-Success ($response.Headers["Content-Disposition"] -match "drilling_g83_1holes\.nc") "Filename matches pattern"
    Assert-Success ($response.Content.Length -gt 50) "G-code content not empty"
    
    Write-Host "    Downloaded: $($response.Content.Length) bytes" -ForegroundColor Gray
} catch {
    Assert-Success $false "Download failed: $($_.Exception.Message)"
}

# Summary
Write-Host "`n=== Test Summary ===" -ForegroundColor Cyan
Write-Host "Total Tests: $($testsPassed + $testsFailed)" -ForegroundColor White
Write-Host "Passed: $testsPassed" -ForegroundColor Green
Write-Host "Failed: $testsFailed" -ForegroundColor Red

if ($testsFailed -eq 0) {
    Write-Host "`n✅ All tests passed!" -ForegroundColor Green
    Write-Host "`nN.06 Modal Cycles is working correctly!" -ForegroundColor Cyan
    Write-Host "- G81-G85 cycles implemented" -ForegroundColor Gray
    Write-Host "- Smart post-processor adaptation (modal vs expanded)" -ForegroundColor Gray
    Write-Host "- GRBL auto-expands, Mach4/LinuxCNC uses canned cycles" -ForegroundColor Gray
    Write-Host "- Validation and error handling working" -ForegroundColor Gray
} else {
    Write-Host "`n❌ Some tests failed. Review output above." -ForegroundColor Red
    exit 1
}

Write-Host "`n=== End of N.06 Test Suite ===" -ForegroundColor Cyan
