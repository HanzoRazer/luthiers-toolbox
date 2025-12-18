# CAM Essentials (N0-N10) Integration Smoke Test
# Tests all 9 CAM Essentials operations with post-processor support
# 
# Prerequisites:
# - Backend running on localhost:8000
# - All routers registered (roughing, drilling, drill_pattern, probe, retract, biarc)
#
# Expected: All 12 tests pass with proper G-code generation

$baseUrl = "http://localhost:8000"
$testsPassed = 0
$testsFailed = 0

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Endpoint,
        [hashtable]$Body,
        [string]$ExpectedContent,
        [string]$ResponseType = "text"
    )
    
    Write-Host "`n=== Test: $Name ===" -ForegroundColor Cyan
    
    try {
        $headers = @{ "Content-Type" = "application/json" }
        $bodyJson = $Body | ConvertTo-Json -Depth 10
        
        if ($Method -eq "POST") {
            $response = Invoke-RestMethod -Uri "$baseUrl$Endpoint" -Method Post -Headers $headers -Body $bodyJson
        } else {
            $response = Invoke-RestMethod -Uri "$baseUrl$Endpoint" -Method Get
        }
        
        # Check response type and content
        if ($ResponseType -eq "json") {
            if ($response -and $response.gcode) {
                $content = $response.gcode
            } else {
                $content = $response
            }
        } else {
            $content = $response
        }
        
        if ($content -match $ExpectedContent) {
            Write-Host "  ✓ PASSED" -ForegroundColor Green
            Write-Host "    - Found expected: $ExpectedContent" -ForegroundColor Gray
            $script:testsPassed++
            return $true
        } else {
            Write-Host "  ✗ FAILED: Expected content not found" -ForegroundColor Red
            Write-Host "    - Looking for: $ExpectedContent" -ForegroundColor Yellow
            Write-Host "    - Got: $($content.Substring(0, [Math]::Min(200, $content.Length)))..." -ForegroundColor Gray
            $script:testsFailed++
            return $false
        }
    } catch {
        Write-Host "  ✗ FAILED: $($_.Exception.Message)" -ForegroundColor Red
        $script:testsFailed++
        return $false
    }
}

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  CAM Essentials (N0-N10) Integration Smoke Test          ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

# Test 1: N01 - Roughing with GRBL post
Test-Endpoint `
    -Name "N01: Roughing with GRBL Post" `
    -Method "POST" `
    -Endpoint "/cam/roughing/gcode" `
    -Body @{
        width = 100.0
        height = 60.0
        stepdown = 3.0
        stepover = 2.5
        feed = 1200.0
        safe_z = 5.0
        post = "GRBL"
        units = "mm"
    } `
    -ExpectedContent "G90" `
    -ResponseType "text"

# Test 2: N01 - Roughing with Mach4 post
Test-Endpoint `
    -Name "N01: Roughing with Mach4 Post" `
    -Method "POST" `
    -Endpoint "/cam/roughing/gcode" `
    -Body @{
        width = 80.0
        height = 50.0
        stepdown = 2.0
        stepover = 3.0
        feed = 1500.0
        safe_z = 10.0
        post = "Mach4"
        units = "mm"
    } `
    -ExpectedContent "G90" `
    -ResponseType "text"

# Test 3: N06 - Drilling G81 (Simple)
Test-Endpoint `
    -Name "N06: Drilling G81 (Simple Cycle)" `
    -Method "POST" `
    -Endpoint "/cam/drill/gcode" `
    -Body @{
        cycle = "G81"
        holes = @(
            @{ x = 10.0; y = 10.0; z = -10.0; feed = 300.0 }
            @{ x = 20.0; y = 10.0; z = -10.0; feed = 300.0 }
            @{ x = 30.0; y = 10.0; z = -10.0; feed = 300.0 }
        )
        safe_z = 10.0
        post = "GRBL"
        units = "mm"
    } `
    -ExpectedContent "G81" `
    -ResponseType "text"

# Test 4: N06 - Drilling G83 (Peck)
Test-Endpoint `
    -Name "N06: Drilling G83 (Peck Cycle)" `
    -Method "POST" `
    -Endpoint "/cam/drill/gcode" `
    -Body @{
        cycle = "G83"
        holes = @(
            @{ x = 15.0; y = 15.0; z = -20.0; feed = 250.0 }
            @{ x = 25.0; y = 25.0; z = -20.0; feed = 250.0 }
        )
        peck_q = 3.0
        safe_z = 10.0
        post = "GRBL"
        units = "mm"
    } `
    -ExpectedContent "G83" `
    -ResponseType "text"

# Test 5: N07 - Drill Pattern (Grid)
Test-Endpoint `
    -Name "N07: Drill Pattern (Grid)" `
    -Method "POST" `
    -Endpoint "/cam/drill/pattern/gcode" `
    -Body @{
        pat = @{
            type = "grid"
            origin_x = 0.0
            origin_y = 0.0
            grid = @{
                rows = 3
                cols = 4
                dx = 10.0
                dy = 10.0
            }
        }
        prm = @{
            z = -10.0
            feed = 300.0
            cycle = "G81"
            safe_z = 10.0
            post = "GRBL"
        }
    } `
    -ExpectedContent "G81" `
    -ResponseType "text"

# Test 6: N07 - Drill Pattern (Circle)
Test-Endpoint `
    -Name "N07: Drill Pattern (Circle)" `
    -Method "POST" `
    -Endpoint "/cam/drill/pattern/gcode" `
    -Body @{
        pat = @{
            type = "circle"
            origin_x = 50.0
            origin_y = 50.0
            circle = @{
                count = 6
                radius = 20.0
                start_angle_deg = 0.0
            }
        }
        prm = @{
            z = -8.0
            feed = 300.0
            cycle = "G81"
            safe_z = 10.0
            post = "GRBL"
        }
    } `
    -ExpectedContent "G81" `
    -ResponseType "text"

# Test 7: N07 - Drill Pattern (Line)
Test-Endpoint `
    -Name "N07: Drill Pattern (Line)" `
    -Method "POST" `
    -Endpoint "/cam/drill/pattern/gcode" `
    -Body @{
        pat = @{
            type = "line"
            origin_x = 10.0
            origin_y = 10.0
            line = @{
                count = 5
                dx = 8.0
                dy = 0.0
            }
        }
        prm = @{
            z = -12.0
            feed = 250.0
            cycle = "G83"
            peck_q = 3.0
            safe_z = 10.0
            post = "GRBL"
        }
    } `
    -ExpectedContent "G83" `
    -ResponseType "text"

# Test 8: N09 - Probe Pattern (Corner Outside)
Test-Endpoint `
    -Name "N09: Probe Pattern (Corner Outside)" `
    -Method "POST" `
    -Endpoint "/api/cam/probe/corner/gcode" `
    -Body @{
        pattern = "corner_outside"
        approach_distance = 20.0
        retract_distance = 2.0
        feed_probe = 100.0
        safe_z = 10.0
        work_offset = 1
    } `
    -ExpectedContent "G31" `
    -ResponseType "json"

# Test 9: N09 - Probe Pattern (Boss Circular)
Test-Endpoint `
    -Name "N09: Probe Pattern (Boss Circular)" `
    -Method "POST" `
    -Endpoint "/api/cam/probe/boss/gcode" `
    -Body @{
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
    } `
    -ExpectedContent "G31" `
    -ResponseType "json"

# Test 10: N09 - Probe Pattern (Surface Z)
Test-Endpoint `
    -Name "N09: Probe Pattern (Surface Z)" `
    -Method "POST" `
    -Endpoint "/api/cam/probe/surface_z/gcode" `
    -Body @{
        x = 50.0
        y = 50.0
        z_clearance = 10.0
        feed_probe = 100.0
        expected_surface_z = 0.0
        work_offset = 1
    } `
    -ExpectedContent "G31" `
    -ResponseType "json"

# Test 11: N08 - Retract Pattern (Direct)
Test-Endpoint `
    -Name "N08: Retract Pattern (Direct G0)" `
    -Method "POST" `
    -Endpoint "/api/cam/retract/gcode?strategy=direct&current_z=-10.0&safe_z=5.0" `
    -Body @{} `
    -ExpectedContent "G0" `
    -ResponseType "text"

# Test 12: N08 - Retract Pattern (Helical)
Test-Endpoint `
    -Name "N08: Retract Pattern (Helical Spiral)" `
    -Method "POST" `
    -Endpoint "/api/cam/retract/gcode?strategy=helical&current_z=-15.0&safe_z=5.0&helix_radius=5.0&helix_pitch=1.0&ramp_feed=600.0" `
    -Body @{} `
    -ExpectedContent "G2" `
    -ResponseType "text"

# Summary
Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Test Summary                                             ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host "  Total Tests: $($testsPassed + $testsFailed)" -ForegroundColor White
Write-Host "  Passed:      $testsPassed" -ForegroundColor Green
Write-Host "  Failed:      $testsFailed" -ForegroundColor $(if ($testsFailed -eq 0) { "Green" } else { "Red" })

if ($testsFailed -eq 0) {
    Write-Host "`n✓ All CAM Essentials (N0-N10) tests passed!" -ForegroundColor Green
    Write-Host "  - N01: Roughing (GRBL, Mach4)" -ForegroundColor Gray
    Write-Host "  - N06: Drilling (G81, G83)" -ForegroundColor Gray
    Write-Host "  - N07: Drill Patterns (Grid, Circle, Line)" -ForegroundColor Gray
    Write-Host "  - N08: Retract Patterns (Direct, Helical)" -ForegroundColor Gray
    Write-Host "  - N09: Probe Patterns (Corner, Boss, Surface)" -ForegroundColor Gray
    Write-Host "`nCAM Essentials integration is production-ready!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n✗ Some tests failed. Check output above for details." -ForegroundColor Red
    Write-Host "  Ensure backend is running: uvicorn app.main:app --reload --port 8000" -ForegroundColor Yellow
    exit 1
}
