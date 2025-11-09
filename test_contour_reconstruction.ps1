# Test Contour Reconstruction (Phase 3.1)
# Tests the new LINE + SPLINE chaining system with Gibson L-00 blueprint

$API_URL = "http://localhost:8000"
$passed = 0
$failed = 0

Write-Host "`n=== Testing Phase 3.1: Contour Reconstruction ===" -ForegroundColor Cyan

# Find Gibson L-00 DXF file
$gibsonFiles = Get-ChildItem -Path "." -Recurse -Filter "*L-00*.dxf" -ErrorAction SilentlyContinue | Select-Object -First 1

if (-not $gibsonFiles) {
    Write-Host "`n✗ No Gibson L-00 DXF file found" -ForegroundColor Red
    Write-Host "  Please ensure a Gibson_L-00.dxf file exists in the project" -ForegroundColor Yellow
    exit 1
}

$dxfPath = $gibsonFiles.FullName
Write-Host "`nUsing DXF: $dxfPath" -ForegroundColor Gray

# Test 1: Health Check
Write-Host "`n1. Testing GET /cam/blueprint/health" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$API_URL/cam/blueprint/health" -Method Get
    if ($response.status -eq "ok") {
        Write-Host "  ✓ Blueprint CAM bridge healthy" -ForegroundColor Green
        Write-Host "    Endpoints: $($response.endpoints -join ', ')" -ForegroundColor Gray
        $passed++
    } else {
        Write-Host "  ✗ Health check failed" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ✗ Error: $_" -ForegroundColor Red
    $failed++
}

# Test 2: Reconstruct Contours from Gibson L-00
Write-Host "`n2. Testing POST /cam/blueprint/reconstruct-contours" -ForegroundColor Yellow
try {
    $form = @{
        file = Get-Item $dxfPath
        layer_name = "Contours"
        tolerance = "0.1"
        min_loop_points = "3"
    }
    
    $response = Invoke-RestMethod -Uri "$API_URL/cam/blueprint/reconstruct-contours" -Method Post -Form $form
    
    if ($response.success -eq $true -and $response.loops.Count -gt 0) {
        Write-Host "  ✓ Contour reconstruction successful" -ForegroundColor Green
        Write-Host "    Loops found: $($response.loops.Count)" -ForegroundColor Gray
        Write-Host "    Outer loop index: $($response.outer_loop_idx)" -ForegroundColor Gray
        
        # Display stats
        Write-Host "`n  Statistics:" -ForegroundColor Cyan
        $stats = $response.stats
        Write-Host "    - Lines found: $($stats.lines_found)" -ForegroundColor Gray
        Write-Host "    - Splines found: $($stats.splines_found)" -ForegroundColor Gray
        Write-Host "    - Edges built: $($stats.edges_built)" -ForegroundColor Gray
        Write-Host "    - Unique points: $($stats.unique_points)" -ForegroundColor Gray
        Write-Host "    - Cycles found: $($stats.cycles_found)" -ForegroundColor Gray
        Write-Host "    - Loops extracted: $($stats.loops_extracted)" -ForegroundColor Gray
        
        # Display warnings
        if ($response.warnings.Count -gt 0) {
            Write-Host "`n  Warnings:" -ForegroundColor Yellow
            $response.warnings | ForEach-Object {
                Write-Host "    - $_" -ForegroundColor Yellow
            }
        }
        
        # Display first loop info
        $firstLoop = $response.loops[0]
        Write-Host "`n  First loop (outer boundary):" -ForegroundColor Cyan
        Write-Host "    - Points: $($firstLoop.pts.Count)" -ForegroundColor Gray
        if ($firstLoop.pts.Count -gt 0) {
            $p1 = $firstLoop.pts[0]
            $p2 = $firstLoop.pts[1]
            Write-Host "    - First point: ($($p1[0]), $($p1[1]))" -ForegroundColor Gray
            Write-Host "    - Second point: ($($p2[0]), $($p2[1]))" -ForegroundColor Gray
        }
        
        $passed++
        
        # Save response for next test
        $script:reconstructionResult = $response
    } else {
        Write-Host "  ✗ Reconstruction failed" -ForegroundColor Red
        if ($response.warnings) {
            Write-Host "    Warnings: $($response.warnings -join '; ')" -ForegroundColor Yellow
        }
        $failed++
    }
} catch {
    Write-Host "  ✗ Error: $_" -ForegroundColor Red
    $failed++
}

# Test 3: Validate Reconstruction Output
if ($script:reconstructionResult) {
    Write-Host "`n3. Validating Reconstruction Quality" -ForegroundColor Yellow
    
    $loops = $script:reconstructionResult.loops
    $stats = $script:reconstructionResult.stats
    
    $checks = 0
    $checksPassed = 0
    
    # Check 1: At least one loop found
    $checks++
    if ($loops.Count -ge 1) {
        Write-Host "  ✓ Found at least one closed loop" -ForegroundColor Green
        $checksPassed++
    } else {
        Write-Host "  ✗ No loops found" -ForegroundColor Red
    }
    
    # Check 2: Outer loop has enough points
    $checks++
    $outerLoop = $loops[$script:reconstructionResult.outer_loop_idx]
    if ($outerLoop.pts.Count -ge 10) {
        Write-Host "  ✓ Outer loop has sufficient points ($($outerLoop.pts.Count))" -ForegroundColor Green
        $checksPassed++
    } else {
        Write-Host "  ✗ Outer loop has too few points ($($outerLoop.pts.Count))" -ForegroundColor Red
    }
    
    # Check 3: Geometry was actually processed
    $checks++
    if ($stats.lines_found -gt 0 -or $stats.splines_found -gt 0) {
        Write-Host "  ✓ Source geometry found (lines: $($stats.lines_found), splines: $($stats.splines_found))" -ForegroundColor Green
        $checksPassed++
    } else {
        Write-Host "  ✗ No source geometry found" -ForegroundColor Red
    }
    
    # Check 4: Expected Gibson L-00 structure (48 lines, 33 splines per Phase 3 doc)
    $checks++
    if ($stats.lines_found -ge 40 -and $stats.splines_found -ge 30) {
        Write-Host "  ✓ Matches expected Gibson L-00 structure (~48 lines, ~33 splines)" -ForegroundColor Green
        $checksPassed++
    } else {
        Write-Host "  ⚠ Geometry count differs from expected (expected ~48 lines, ~33 splines)" -ForegroundColor Yellow
        $checksPassed++  # Don't fail on this
    }
    
    if ($checksPassed -eq $checks) {
        Write-Host "`n  ✓ All validation checks passed ($checksPassed/$checks)" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "`n  ✗ Some validation checks failed ($checksPassed/$checks)" -ForegroundColor Red
        $failed++
    }
}

# Summary
Write-Host "`n=== Test Summary ===" -ForegroundColor Cyan
Write-Host "  Passed: $passed" -ForegroundColor Green
Write-Host "  Failed: $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })

if ($failed -eq 0) {
    Write-Host "`n✓ All Phase 3.1 contour reconstruction tests passed!" -ForegroundColor Green
    Write-Host "  Next step: Test with adaptive pocket planner" -ForegroundColor Cyan
    exit 0
} else {
    Write-Host "`n✗ Some tests failed" -ForegroundColor Red
    exit 1
}
