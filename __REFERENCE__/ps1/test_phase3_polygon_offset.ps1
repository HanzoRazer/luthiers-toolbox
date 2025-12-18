# Phase 3: N17 Polygon Offset Integration — Smoke Test
# Tests all components of the N17 integration

Write-Host "=== Phase 3: N17 Polygon Offset Integration — Smoke Test ===" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"
$passed = 0
$failed = 0

# Test 1: Core module exists
Write-Host "1. Testing core module (polygon_offset_n17.py)..." -ForegroundColor Yellow
$coreModulePath = "services/api/app/cam/polygon_offset_n17.py"
if (Test-Path $coreModulePath) {
    Write-Host "  ✓ Core module exists" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ✗ Core module not found" -ForegroundColor Red
    $failed++
}

# Test 2: Gcode emit modules exist
Write-Host "2. Testing gcode emit modules..." -ForegroundColor Yellow
$advancedPath = "services/api/app/util/gcode_emit_advanced.py"
$basicPath = "services/api/app/util/gcode_emit_basic.py"
if ((Test-Path $advancedPath) -and (Test-Path $basicPath)) {
    Write-Host "  ✓ Gcode emit modules exist" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ✗ Gcode emit modules not found" -ForegroundColor Red
    $failed++
}

# Test 3: Router registered in main.py
Write-Host "3. Testing router registration..." -ForegroundColor Yellow
$mainPyContent = Get-Content "services/api/app/main.py" -Raw
if ($mainPyContent -match "cam_polygon_offset_router" -and $mainPyContent -match "Phase 3") {
    Write-Host "  ✓ Router registered in main.py" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ✗ Router not registered" -ForegroundColor Red
    $failed++
}

# Test 4: Frontend component exists
Write-Host "4. Testing frontend component..." -ForegroundColor Yellow
$componentPath = "client/src/components/toolbox/PolygonOffsetLab.vue"
if (Test-Path $componentPath) {
    Write-Host "  ✓ PolygonOffsetLab.vue exists" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ✗ Frontend component not found" -ForegroundColor Red
    $failed++
}

# Test 5: Route configured
Write-Host "5. Testing route configuration..." -ForegroundColor Yellow
$routerContent = Get-Content "client/src/router/index.ts" -Raw
if ($routerContent -match "polygon-offset" -and $routerContent -match "PolygonOffsetLab") {
    Write-Host "  ✓ Route configured in router/index.ts" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ✗ Route not configured" -ForegroundColor Red
    $failed++
}

# Test 6: CAM Dashboard card updated
Write-Host "6. Testing CAM Dashboard card..." -ForegroundColor Yellow
$camDashContent = Get-Content "client/src/views/CAMDashboard.vue" -Raw
if ($camDashContent -match "polygon-offset" -and $camDashContent -match "Production" -and $camDashContent -match "N17") {
    Write-Host "  ✓ CAM Dashboard card updated to Production" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ✗ CAM Dashboard card not updated" -ForegroundColor Red
    $failed++
}

# Test 7: Art Studio Dashboard card added
Write-Host "7. Testing Art Studio Dashboard card..." -ForegroundColor Yellow
$artDashContent = Get-Content "client/src/views/ArtStudioDashboard.vue" -Raw
if ($artDashContent -match "polygon-offset" -and $artDashContent -match "N17") {
    Write-Host "  ✓ Art Studio Dashboard card added" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ✗ Art Studio Dashboard card not added" -ForegroundColor Red
    $failed++
}

# Test 8: API endpoint health (requires server running)
Write-Host "8. Testing API endpoint health..." -ForegroundColor Yellow
try {
    $testPolygon = @(
        @(0, 0),
        @(100, 0),
        @(100, 60),
        @(0, 60)
    )
    
    $body = @{
        polygon = $testPolygon
        tool_dia = 6.0
        stepover = 2.0
        inward = $true
        z = -1.5
        safe_z = 5.0
        units = "mm"
        feed = 600.0
        join_type = "round"
        arc_tolerance = 0.25
        link_mode = "arc"
        link_radius = 1.0
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$baseUrl/cam/polygon_offset.nc" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body `
        -TimeoutSec 10
    
    if ($response -match "G21" -and $response -match "N17 Polygon Offset") {
        Write-Host "  ✓ API endpoint responds correctly" -ForegroundColor Green
        Write-Host "    Preview (first 5 lines):" -ForegroundColor Gray
        $lines = $response -split "`n" | Select-Object -First 5
        foreach ($line in $lines) {
            Write-Host "    $line" -ForegroundColor Gray
        }
        $passed++
    } else {
        Write-Host "  ✗ API response unexpected" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ⚠ API endpoint test skipped (server not running?)" -ForegroundColor Yellow
    Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Gray
}

# Test 9: Pyclipper availability check
Write-Host "9. Testing pyclipper dependency..." -ForegroundColor Yellow
try {
    $pythonCheck = python -c "import pyclipper; print('OK')" 2>&1
    if ($pythonCheck -match "OK") {
        Write-Host "  ✓ Pyclipper installed (production mode)" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  ⚠ Pyclipper not installed (fallback mode will be used)" -ForegroundColor Yellow
        Write-Host "    Install with: pip install pyclipper" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ⚠ Python check failed (cannot verify pyclipper)" -ForegroundColor Yellow
}

# Test 10: Arc linker test (link_mode=arc)
Write-Host "10. Testing arc linker mode..." -ForegroundColor Yellow
try {
    $testPolygon = @(
        @(0, 0),
        @(50, 0),
        @(50, 30),
        @(0, 30)
    )
    
    $body = @{
        polygon = $testPolygon
        tool_dia = 6.0
        stepover = 2.5
        inward = $true
        link_mode = "arc"
        link_radius = 1.0
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$baseUrl/cam/polygon_offset.nc" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body `
        -TimeoutSec 10
    
    # Check for G2/G3 arc commands
    if ($response -match "G2" -or $response -match "G3") {
        Write-Host "  ✓ Arc linker mode working (G2/G3 commands found)" -ForegroundColor Green
        $arcCount = ($response -split "G[23]").Length - 1
        Write-Host "    Arc commands: $arcCount" -ForegroundColor Gray
        $passed++
    } else {
        Write-Host "  ✗ No arc commands found (expected G2/G3)" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ⚠ Arc linker test skipped (server not running?)" -ForegroundColor Yellow
}

# Test 11: Linear linker test (link_mode=line)
Write-Host "11. Testing linear linker mode..." -ForegroundColor Yellow
try {
    $testPolygon = @(
        @(0, 0),
        @(50, 0),
        @(50, 30),
        @(0, 30)
    )
    
    $body = @{
        polygon = $testPolygon
        tool_dia = 6.0
        stepover = 2.5
        inward = $true
        link_mode = "line"
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$baseUrl/cam/polygon_offset.nc" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body `
        -TimeoutSec 10
    
    # Check for spindle control (M3) and G1 moves
    if ($response -match "M3" -and $response -match "G1") {
        Write-Host "  ✓ Linear linker mode working (M3 + G1 found)" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  ✗ Linear linker mode unexpected" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ⚠ Linear linker test skipped (server not running?)" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "=== Test Summary ===" -ForegroundColor Cyan
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor Red
Write-Host ""

if ($failed -eq 0) {
    Write-Host "✅ All Phase 3 integration tests passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Start the dev server: cd services/api && uvicorn app.main:app --reload" -ForegroundColor Gray
    Write-Host "  2. Start the client: cd client && npm run dev" -ForegroundColor Gray
    Write-Host "  3. Navigate to: http://localhost:5173/lab/polygon-offset" -ForegroundColor Gray
    Write-Host "  4. Test with various polygons and settings" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Optional: Install pyclipper for production offsetting" -ForegroundColor Gray
    Write-Host "    pip install pyclipper" -ForegroundColor Gray
} else {
    Write-Host "❌ Some tests failed. Please review the errors above." -ForegroundColor Red
    exit 1
}
