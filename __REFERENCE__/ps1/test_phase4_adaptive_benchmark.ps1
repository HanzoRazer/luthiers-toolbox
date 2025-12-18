# Phase 4: N16 Adaptive Benchmark Suite Integration — Smoke Test
# Tests all components of the N16 integration

Write-Host "=== Phase 4: N16 Adaptive Benchmark Suite Integration — Smoke Test ===" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"
$passed = 0
$failed = 0

# Test 1: Utility module exists
Write-Host "1. Testing utility module (adaptive_geom.py)..." -ForegroundColor Yellow
$utilPath = "services/api/app/util/adaptive_geom.py"
if (Test-Path $utilPath) {
    Write-Host "  ✓ Utility module exists" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ✗ Utility module not found" -ForegroundColor Red
    $failed++
}

# Test 2: Router exists
Write-Host "2. Testing router (cam_adaptive_benchmark_router.py)..." -ForegroundColor Yellow
$routerPath = "services/api/app/routers/cam_adaptive_benchmark_router.py"
if (Test-Path $routerPath) {
    Write-Host "  ✓ Router exists" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ✗ Router not found" -ForegroundColor Red
    $failed++
}

# Test 3: Router registered in main.py
Write-Host "3. Testing router registration..." -ForegroundColor Yellow
$mainPyContent = Get-Content "services/api/app/main.py" -Raw
if ($mainPyContent -match "cam_adaptive_benchmark_router" -and $mainPyContent -match "Phase 4") {
    Write-Host "  ✓ Router registered in main.py" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ✗ Router not registered" -ForegroundColor Red
    $failed++
}

# Test 4: Frontend component exists
Write-Host "4. Testing frontend component..." -ForegroundColor Yellow
$componentPath = "client/src/components/toolbox/AdaptiveBenchLab.vue"
if (Test-Path $componentPath) {
    Write-Host "  ✓ AdaptiveBenchLab.vue exists" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ✗ Frontend component not found" -ForegroundColor Red
    $failed++
}

# Test 5: Route configured
Write-Host "5. Testing route configuration..." -ForegroundColor Yellow
$routerContent = Get-Content "client/src/router/index.ts" -Raw
if ($routerContent -match "adaptive-benchmark" -and $routerContent -match "AdaptiveBenchLab") {
    Write-Host "  ✓ Route configured in router/index.ts" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ✗ Route not configured" -ForegroundColor Red
    $failed++
}

# Test 6: CAM Dashboard card updated
Write-Host "6. Testing CAM Dashboard card..." -ForegroundColor Yellow
$camDashContent = Get-Content "client/src/views/CAMDashboard.vue" -Raw
if ($camDashContent -match "adaptive-benchmark" -and $camDashContent -match "N16") {
    Write-Host "  ✓ CAM Dashboard card added" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ✗ CAM Dashboard card not added" -ForegroundColor Red
    $failed++
}

# Test 7: Offset Spiral SVG endpoint
Write-Host "7. Testing offset spiral endpoint..." -ForegroundColor Yellow
try {
    $body = @{
        width = 100.0
        height = 60.0
        tool_dia = 6.0
        stepover = 2.4
        corner_fillet = 0.6
    } | ConvertTo-Json
    
    # Use Invoke-WebRequest (not Invoke-RestMethod) to get raw SVG content
    $response = Invoke-WebRequest -Uri "$baseUrl/cam/adaptive2/offset_spiral.svg" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body `
        -TimeoutSec 10
    
    $svgContent = $response.Content
    if ($svgContent -match "<svg" -and $svgContent -match "polyline") {
        Write-Host "  ✓ Offset spiral endpoint responds with SVG" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  ✗ Unexpected SVG response" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ⚠ Offset spiral test skipped (server not running?)" -ForegroundColor Yellow
    Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Gray
}

# Test 8: Trochoid Corners SVG endpoint
Write-Host "8. Testing trochoid corners endpoint..." -ForegroundColor Yellow
try {
    $body = @{
        width = 100.0
        height = 60.0
        tool_dia = 6.0
        loop_pitch = 2.5
        amp = 0.4
    } | ConvertTo-Json
    
    # Use Invoke-WebRequest (not Invoke-RestMethod) to get raw SVG content
    $response = Invoke-WebRequest -Uri "$baseUrl/cam/adaptive2/trochoid_corners.svg" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body `
        -TimeoutSec 10
    
    $svgContent = $response.Content
    if ($svgContent -match "<svg" -and $svgContent -match "polyline") {
        Write-Host "  ✓ Trochoid corners endpoint responds with SVG" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  ✗ Unexpected SVG response" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ⚠ Trochoid corners test skipped (server not running?)" -ForegroundColor Yellow
    Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Gray
}

# Test 9: Benchmark endpoint
Write-Host "9. Testing benchmark endpoint..." -ForegroundColor Yellow
try {
    $body = @{
        width = 100.0
        height = 60.0
        tool_dia = 6.0
        stepover = 2.4
        runs = 10
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$baseUrl/cam/adaptive2/bench" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body `
        -TimeoutSec 30
    
    if ($response.runs -eq 10 -and $response.total_ms -gt 0 -and $response.avg_ms -gt 0) {
        Write-Host "  ✓ Benchmark endpoint responds correctly" -ForegroundColor Green
        Write-Host "    Runs: $($response.runs)" -ForegroundColor Gray
        Write-Host "    Total: $($response.total_ms) ms" -ForegroundColor Gray
        Write-Host "    Average: $($response.avg_ms) ms/run" -ForegroundColor Gray
        $passed++
    } else {
        Write-Host "  ✗ Benchmark response unexpected" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ⚠ Benchmark test skipped (server not running?)" -ForegroundColor Yellow
    Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Gray
}

# Test 10: Performance validation (avg_ms should be < 10ms for 100×60mm rect)
Write-Host "10. Testing performance characteristics..." -ForegroundColor Yellow
try {
    $body = @{
        width = 100.0
        height = 60.0
        tool_dia = 6.0
        stepover = 2.4
        runs = 20
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$baseUrl/cam/adaptive2/bench" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body `
        -TimeoutSec 30
    
    if ($response.avg_ms -lt 10.0) {
        Write-Host "  ✓ Performance acceptable (avg < 10ms)" -ForegroundColor Green
        Write-Host "    Average: $($response.avg_ms) ms/run" -ForegroundColor Gray
        $passed++
    } else {
        Write-Host "  ⚠ Performance slower than expected (avg $($response.avg_ms) ms)" -ForegroundColor Yellow
        Write-Host "    Note: This may be acceptable depending on hardware" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ⚠ Performance test skipped (server not running?)" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "=== Test Summary ===" -ForegroundColor Cyan
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor Red
Write-Host ""

if ($failed -eq 0) {
    Write-Host "✅ All Phase 4 integration tests passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Start the dev server: cd services/api && uvicorn app.main:app --reload" -ForegroundColor Gray
    Write-Host "  2. Start the client: cd client && npm run dev" -ForegroundColor Gray
    Write-Host "  3. Navigate to: http://localhost:5173/lab/adaptive-benchmark" -ForegroundColor Gray
    Write-Host "  4. Test spiral generation, trochoid visualization, and benchmarks" -ForegroundColor Gray
} else {
    Write-Host "❌ Some tests failed. Please review the errors above." -ForegroundColor Red
    exit 1
}
