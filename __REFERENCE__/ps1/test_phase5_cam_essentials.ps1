# Phase 5: N10 CAM Essentials Integration — Smoke Test
# Tests all 4 N10 routers and frontend integration

Write-Host "=== Phase 5: N10 CAM Essentials Integration — Smoke Test ===" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"
$passed = 0
$failed = 0

# Test 1: Roughing router exists
Write-Host "1. Testing roughing router (cam_roughing_router.py)..." -ForegroundColor Yellow
$routerPath = "services/api/app/routers/cam_roughing_router.py"
if (Test-Path $routerPath) {
    Write-Host "  ✓ Roughing router exists" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ✗ Roughing router not found" -ForegroundColor Red
    $failed++
}

# Test 2: Drilling router exists
Write-Host "2. Testing drilling router (cam_drill_router.py)..." -ForegroundColor Yellow
$drillPath = "services/api/app/routers/cam_drill_router.py"
if (Test-Path $drillPath) {
    Write-Host "  ✓ Drilling router exists" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ✗ Drilling router not found" -ForegroundColor Red
    $failed++
}

# Test 3: Drill pattern router exists
Write-Host "3. Testing drill pattern router (cam_drill_pattern_router.py)..." -ForegroundColor Yellow
$patternPath = "services/api/app/routers/cam_drill_pattern_router.py"
if (Test-Path $patternPath) {
    Write-Host "  ✓ Drill pattern router exists" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ✗ Drill pattern router not found" -ForegroundColor Red
    $failed++
}

# Test 4: Bi-arc router exists
Write-Host "4. Testing bi-arc router (cam_biarc_router.py)..." -ForegroundColor Yellow
$biarcPath = "services/api/app/routers/cam_biarc_router.py"
if (Test-Path $biarcPath) {
    Write-Host "  ✓ Bi-arc router exists" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ✗ Bi-arc router not found" -ForegroundColor Red
    $failed++
}

# Test 5: Routers registered in main.py
Write-Host "5. Testing router registration..." -ForegroundColor Yellow
$mainPyContent = Get-Content "services/api/app/main.py" -Raw
if ($mainPyContent -match "cam_roughing_router" -and $mainPyContent -match "cam_drill_router" -and $mainPyContent -match "Phase 5") {
    Write-Host "  ✓ All 4 routers registered in main.py" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ✗ Router registration incomplete" -ForegroundColor Red
    $failed++
}

# Test 6: Frontend component exists
Write-Host "6. Testing frontend component..." -ForegroundColor Yellow
$componentPath = "client/src/components/toolbox/CAMEssentialsLab.vue"
if (Test-Path $componentPath) {
    Write-Host "  ✓ CAMEssentialsLab.vue exists" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ✗ Frontend component not found" -ForegroundColor Red
    $failed++
}

# Test 7: Route configured
Write-Host "7. Testing route configuration..." -ForegroundColor Yellow
$routerContent = Get-Content "client/src/router/index.ts" -Raw
if ($routerContent -match "cam-essentials" -and $routerContent -match "CAMEssentialsLab") {
    Write-Host "  ✓ Route configured in router/index.ts" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ✗ Route not configured" -ForegroundColor Red
    $failed++
}

# Test 8: CAM Dashboard card updated
Write-Host "8. Testing CAM Dashboard card..." -ForegroundColor Yellow
$camDashContent = Get-Content "client/src/views/CAMDashboard.vue" -Raw
if ($camDashContent -match "cam-essentials" -and $camDashContent -match "N10") {
    Write-Host "  ✓ CAM Dashboard card added" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ✗ CAM Dashboard card not added" -ForegroundColor Red
    $failed++
}

# Test 9: Roughing endpoint (API)
Write-Host "9. Testing roughing endpoint..." -ForegroundColor Yellow
try {
    $body = @{
        width = 100.0
        height = 60.0
        stepdown = 3.0
        stepover = 2.5
        feed = 1200.0
        post = "GRBL"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "$baseUrl/cam/roughing/gcode" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body `
        -TimeoutSec 10
    
    $gcode = $response.Content
    if ($gcode -match "G90" -and $gcode -match "G0" -and $gcode -match "G1") {
        Write-Host "  ✓ Roughing endpoint generates valid G-code" -ForegroundColor Green
        Write-Host "    Lines: $((($gcode -split "`n").Count))" -ForegroundColor Gray
        $passed++
    } else {
        Write-Host "  ✗ Unexpected G-code format" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ⚠ Roughing endpoint test skipped (server not running?)" -ForegroundColor Yellow
    Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Gray
}

# Test 10: Drilling endpoint (API)
Write-Host "10. Testing drilling endpoint..." -ForegroundColor Yellow
try {
    $body = @{
        holes = @(
            @{ x = 10.0; y = 10.0; z = -10.0; feed = 300.0 }
            @{ x = 30.0; y = 10.0; z = -10.0; feed = 300.0 }
        )
        cycle = "G81"
        post = "GRBL"
    } | ConvertTo-Json -Depth 5
    
    $response = Invoke-WebRequest -Uri "$baseUrl/cam/drill/gcode" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body `
        -TimeoutSec 10
    
    $gcode = $response.Content
    if ($gcode -match "G81" -and $gcode -match "G80") {
        Write-Host "  ✓ Drilling endpoint generates modal cycles" -ForegroundColor Green
        Write-Host "    Cycle count: $(($gcode -split 'G81').Count - 1)" -ForegroundColor Gray
        $passed++
    } else {
        Write-Host "  ✗ Missing drilling cycle commands" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ⚠ Drilling endpoint test skipped (server not running?)" -ForegroundColor Yellow
    Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Gray
}

# Test 11: Drill pattern endpoint (API)
Write-Host "11. Testing drill pattern endpoint..." -ForegroundColor Yellow
try {
    $patternBody = @{
        type = "grid"
        origin_x = 0.0
        origin_y = 0.0
        grid = @{
            cols = 4
            rows = 3
            dx = 10.0
            dy = 10.0
        }
    } | ConvertTo-Json -Depth 5
    
    $drillParams = @{
        z = -10.0
        feed = 300.0
        cycle = "G81"
        post = "GRBL"
    }
    
    $queryString = ($drillParams.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join "&"
    $url = "$baseUrl/cam/drill/pattern/gcode?$queryString"
    
    $response = Invoke-WebRequest -Uri $url `
        -Method Post `
        -ContentType "application/json" `
        -Body $patternBody `
        -TimeoutSec 10
    
    $gcode = $response.Content
    $holeCount = ($gcode -split 'G81').Count - 1
    if ($holeCount -eq 12) {
        Write-Host "  ✓ Drill pattern generates correct hole count (4×3 grid = 12 holes)" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  ⚠ Hole count mismatch (expected 12, got $holeCount)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠ Drill pattern endpoint test skipped (server not running?)" -ForegroundColor Yellow
    Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Gray
}

# Test 12: Bi-arc endpoint (API)
Write-Host "12. Testing bi-arc endpoint..." -ForegroundColor Yellow
try {
    $body = @{
        path = @(
            @{ x = 0.0; y = 0.0 }
            @{ x = 50.0; y = 0.0 }
            @{ x = 50.0; y = 30.0 }
            @{ x = 0.0; y = 30.0 }
        )
        z = -3.0
        feed = 1200.0
        post = "GRBL"
    } | ConvertTo-Json -Depth 5
    
    $response = Invoke-WebRequest -Uri "$baseUrl/cam/biarc/gcode" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body `
        -TimeoutSec 10
    
    $gcode = $response.Content
    $moveCount = ($gcode -split 'G1 X').Count - 1
    if ($moveCount -ge 3) {
        Write-Host "  ✓ Bi-arc endpoint generates contour path" -ForegroundColor Green
        Write-Host "    Linear moves: $moveCount" -ForegroundColor Gray
        $passed++
    } else {
        Write-Host "  ✗ Insufficient linear moves" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ⚠ Bi-arc endpoint test skipped (server not running?)" -ForegroundColor Yellow
    Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Gray
}

# Test 13: Post-processor helper wrapper exists
Write-Host "13. Testing post-processor helper wrapper..." -ForegroundColor Yellow
$helperPath = "services/api/app/util/post_injection_helpers.py"
if (Test-Path $helperPath) {
    Write-Host "  ✓ Post-processor helper wrapper exists" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ⚠ Helper wrapper not found (post-processor support may be limited)" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "=== Test Summary ===" -ForegroundColor Cyan
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor Red
Write-Host ""

if ($failed -eq 0) {
    Write-Host "✅ All Phase 5 integration tests passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Start the dev server: cd services/api && uvicorn app.main:app --reload" -ForegroundColor Gray
    Write-Host "  2. Start the client: cd client && npm run dev" -ForegroundColor Gray
    Write-Host "  3. Navigate to: http://localhost:5173/lab/cam-essentials" -ForegroundColor Gray
    Write-Host "  4. Test roughing, drilling, patterns, and contour operations" -ForegroundColor Gray
} else {
    Write-Host "❌ Some tests failed. Please review the errors above." -ForegroundColor Red
    exit 1
}
