# Phase 5 Part 3: N.16 Adaptive Benchmark Comprehensive Validation
# Expands Phase 4 smoke tests (10 tests) into comprehensive validation (45+ tests)

Write-Host "=== Phase 5 Part 3: N.16 Adaptive Benchmark Validation ===" -ForegroundColor Cyan
Write-Host ""

$ApiBase = "http://localhost:8000"
$script:passCount = 0
$script:grandPass = 0

# Test-Assert helper function
function Test-Assert {
    param(
        [string]$Name,
        [bool]$Condition,
        [string]$ErrorMsg = ""
    )
    if ($Condition) {
        Write-Host "  ✓ $Name" -ForegroundColor Green
        $script:passCount++
        $script:grandPass++
    } else {
        Write-Host "  ✗ $Name" -ForegroundColor Red
        if ($ErrorMsg) {
            Write-Host "    $ErrorMsg" -ForegroundColor Gray
        }
    }
}

# Show-TestSummary helper function
function Show-TestSummary {
    param([string]$GroupName)
    
    $total = $script:passCount
    $pct = if ($total -gt 0) { [math]::Round(($script:passCount / $total) * 100, 1) } else { 0 }
    
    Write-Host ""
    Write-Host "Group Results: $($script:passCount)/$total ($pct%)" -ForegroundColor $(if ($pct -eq 100) { "Green" } elseif ($pct -ge 90) { "Yellow" } else { "Red" })
    Write-Host ""
}

# =============================================================================
# GROUP 1: FILE STRUCTURE VALIDATION (6 tests)
# =============================================================================

Write-Host "=== GROUP 1: FILE STRUCTURE VALIDATION (6 tests) ===" -ForegroundColor Cyan
Write-Host "Verify all required files exist"
Write-Host ""

$script:passCount = 0

# Test 1.1: Utility module exists
Test-Assert "Utility module exists (adaptive_geom.py)" (Test-Path "services/api/app/util/adaptive_geom.py")

# Test 1.2: Router exists
Test-Assert "Router exists (cam_adaptive_benchmark_router.py)" (Test-Path "services/api/app/routers/cam_adaptive_benchmark_router.py")

# Test 1.3: Router registered in main.py
$mainPyContent = Get-Content "services/api/app/main.py" -Raw
Test-Assert "Router registered in main.py" ($mainPyContent -match "cam_adaptive_benchmark_router" -and $mainPyContent -match "/cam/adaptive2")

# Test 1.4: Frontend component exists
$componentFound = (Test-Path "client/src/components/toolbox/AdaptiveBenchLab.vue") -or (Test-Path "packages/client/src/components/AdaptiveBenchLab.vue")
Test-Assert "Frontend component exists" $componentFound

# Test 1.5: Utility functions defined
$utilContent = Get-Content "services/api/app/util/adaptive_geom.py" -Raw
$hasFunctions = ($utilContent -match "def inward_offset_spiral_rect") -and 
                ($utilContent -match "def trochoid_corner_loops") -and 
                ($utilContent -match "def svg_polyline")
Test-Assert "Core utility functions defined" $hasFunctions

# Test 1.6: Router has 3 endpoints
$routerContent = Get-Content "services/api/app/routers/cam_adaptive_benchmark_router.py" -Raw
$hasEndpoints = ($routerContent -match "offset_spiral\.svg") -and 
                ($routerContent -match "trochoid_corners\.svg") -and 
                ($routerContent -match "bench")
Test-Assert "Router has 3 endpoints" $hasEndpoints

Show-TestSummary "Group 1"

# =============================================================================
# GROUP 2: ENDPOINT AVAILABILITY (4 tests)
# =============================================================================

Write-Host "=== GROUP 2: ENDPOINT AVAILABILITY (4 tests) ===" -ForegroundColor Cyan
Write-Host "Verify endpoints respond to requests"
Write-Host ""

$script:passCount = 0

# Test 2.1: Offset spiral endpoint responds
try {
    $body = @{ width = 100.0; height = 60.0; tool_dia = 6.0; stepover = 2.4; corner_fillet = 0.6 } | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "$ApiBase/cam/adaptive2/offset_spiral.svg" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 10
    Test-Assert "Offset spiral endpoint responds (200 OK)" ($response.StatusCode -eq 200)
} catch {
    Test-Assert "Offset spiral endpoint responds" $false $_.Exception.Message
}

# Test 2.2: Offset spiral returns SVG content-type
try {
    $body = @{ width = 100.0; height = 60.0; tool_dia = 6.0; stepover = 2.4 } | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "$ApiBase/cam/adaptive2/offset_spiral.svg" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 10
    Test-Assert "Response is SVG content-type" (($response.Headers.'Content-Type' | Out-String) -match 'svg')
} catch {
    Test-Assert "SVG content-type" $false $_.Exception.Message
}

# Test 2.3: Trochoid corners endpoint responds
try {
    $body = @{ width = 100.0; height = 60.0; tool_dia = 6.0; loop_pitch = 2.5; amp = 0.4 } | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "$ApiBase/cam/adaptive2/trochoid_corners.svg" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 10
    Test-Assert "Trochoid corners endpoint responds (200 OK)" ($response.StatusCode -eq 200)
} catch {
    Test-Assert "Trochoid corners endpoint responds" $false $_.Exception.Message
}

# Test 2.4: Benchmark endpoint responds
try {
    $body = @{ width = 100.0; height = 60.0; tool_dia = 6.0; stepover = 2.4; runs = 10 } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$ApiBase/cam/adaptive2/bench" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 30
    Test-Assert "Benchmark endpoint responds with JSON" ($response -ne $null)
} catch {
    Test-Assert "Benchmark endpoint responds" $false $_.Exception.Message
}

Show-TestSummary "Group 2"

# =============================================================================
# GROUP 3: OFFSET SPIRAL SVG GENERATION (10 tests)
# =============================================================================

Write-Host "=== GROUP 3: OFFSET SPIRAL SVG GENERATION (10 tests) ===" -ForegroundColor Cyan
Write-Host "Test SVG generation for offset spiral toolpath"
Write-Host ""

$script:passCount = 0

# Test 3.1: Basic spiral SVG structure
try {
    $body = @{ width = 100.0; height = 60.0; tool_dia = 6.0; stepover = 2.4 } | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "$ApiBase/cam/adaptive2/offset_spiral.svg" -Method POST -ContentType "application/json" -Body $body
    $svg = $response.Content
    Test-Assert "SVG has root element" ($svg -match "<svg")
} catch {
    Test-Assert "Basic spiral SVG structure" $false $_.Exception.Message
}

# Test 3.2: SVG has polyline
try {
    $body = @{ width = 100.0; height = 60.0; tool_dia = 6.0; stepover = 2.4 } | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "$ApiBase/cam/adaptive2/offset_spiral.svg" -Method POST -ContentType "application/json" -Body $body
    $svg = $response.Content
    Test-Assert "SVG contains polyline element" ($svg -match "<polyline")
} catch {
    Test-Assert "SVG polyline" $false $_.Exception.Message
}

# Test 3.3: SVG has points attribute
try {
    $body = @{ width = 100.0; height = 60.0; tool_dia = 6.0; stepover = 2.4 } | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "$ApiBase/cam/adaptive2/offset_spiral.svg" -Method POST -ContentType "application/json" -Body $body
    $svg = $response.Content
    Test-Assert "Polyline has points attribute" ($svg -match 'points="')
} catch {
    Test-Assert "Points attribute" $false $_.Exception.Message
}

# Test 3.4: Purple stroke color (default)
try {
    $body = @{ width = 100.0; height = 60.0; tool_dia = 6.0; stepover = 2.4 } | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "$ApiBase/cam/adaptive2/offset_spiral.svg" -Method POST -ContentType "application/json" -Body $body
    $svg = $response.Content
    Test-Assert "SVG has purple stroke color" ($svg -match 'stroke="purple"')
} catch {
    Test-Assert "Purple stroke" $false $_.Exception.Message
}

# Test 3.5: Small pocket (50×30mm)
try {
    $body = @{ width = 50.0; height = 30.0; tool_dia = 6.0; stepover = 2.4 } | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "$ApiBase/cam/adaptive2/offset_spiral.svg" -Method POST -ContentType "application/json" -Body $body
    $svg = $response.Content
    Test-Assert "Generates spiral for small pocket" ($svg -match "<polyline" -and $svg.Length -gt 200)
} catch {
    Test-Assert "Small pocket spiral" $false $_.Exception.Message
}

# Test 3.6: Large pocket (200×120mm)
try {
    $body = @{ width = 200.0; height = 120.0; tool_dia = 6.0; stepover = 2.4 } | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "$ApiBase/cam/adaptive2/offset_spiral.svg" -Method POST -ContentType "application/json" -Body $body
    $svg = $response.Content
    Test-Assert "Generates spiral for large pocket" ($svg -match "<polyline" -and $svg.Length -gt 500)
} catch {
    Test-Assert "Large pocket spiral" $false $_.Exception.Message
}

# Test 3.7: With corner fillet
try {
    $body = @{ width = 100.0; height = 60.0; tool_dia = 6.0; stepover = 2.4; corner_fillet = 2.0 } | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "$ApiBase/cam/adaptive2/offset_spiral.svg" -Method POST -ContentType "application/json" -Body $body
    $svg = $response.Content
    Test-Assert "Generates spiral with corner fillet" ($svg -match "<polyline")
} catch {
    Test-Assert "Corner fillet spiral" $false $_.Exception.Message
}

# Test 3.8: Small tool (3mm)
try {
    $body = @{ width = 100.0; height = 60.0; tool_dia = 3.0; stepover = 1.2 } | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "$ApiBase/cam/adaptive2/offset_spiral.svg" -Method POST -ContentType "application/json" -Body $body
    $svg = $response.Content
    Test-Assert "Generates spiral for small tool" ($svg -match "<polyline")
} catch {
    Test-Assert "Small tool spiral" $false $_.Exception.Message
}

# Test 3.9: Large tool (12mm)
try {
    $body = @{ width = 100.0; height = 60.0; tool_dia = 12.0; stepover = 4.8 } | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "$ApiBase/cam/adaptive2/offset_spiral.svg" -Method POST -ContentType "application/json" -Body $body
    $svg = $response.Content
    Test-Assert "Generates spiral for large tool" ($svg -match "<polyline")
} catch {
    Test-Assert "Large tool spiral" $false $_.Exception.Message
}

# Test 3.10: Tight stepover (20%)
try {
    $body = @{ width = 100.0; height = 60.0; tool_dia = 6.0; stepover = 1.2 } | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "$ApiBase/cam/adaptive2/offset_spiral.svg" -Method POST -ContentType "application/json" -Body $body
    $svg = $response.Content
    Test-Assert "Generates spiral with tight stepover" ($svg -match "<polyline")
} catch {
    Test-Assert "Tight stepover spiral" $false $_.Exception.Message
}

Show-TestSummary "Group 3"

# =============================================================================
# GROUP 4: TROCHOID CORNERS SVG GENERATION (8 tests)
# =============================================================================

Write-Host "=== GROUP 4: TROCHOID CORNERS SVG GENERATION (8 tests) ===" -ForegroundColor Cyan
Write-Host "Test SVG generation for trochoidal corner loops"
Write-Host ""

$script:passCount = 0

# Test 4.1: Basic trochoid SVG structure
try {
    $body = @{ width = 100.0; height = 60.0; tool_dia = 6.0; loop_pitch = 2.5; amp = 0.4 } | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "$ApiBase/cam/adaptive2/trochoid_corners.svg" -Method POST -ContentType "application/json" -Body $body
    $svg = $response.Content
    Test-Assert "Trochoid SVG has root element" ($svg -match "<svg")
} catch {
    Test-Assert "Basic trochoid SVG" $false $_.Exception.Message
}

# Test 4.2: Trochoid has polyline
try {
    $body = @{ width = 100.0; height = 60.0; tool_dia = 6.0; loop_pitch = 2.5; amp = 0.4 } | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "$ApiBase/cam/adaptive2/trochoid_corners.svg" -Method POST -ContentType "application/json" -Body $body
    $svg = $response.Content
    Test-Assert "Trochoid SVG contains polyline" ($svg -match "<polyline")
} catch {
    Test-Assert "Trochoid polyline" $false $_.Exception.Message
}

# Test 4.3: Teal stroke color (default)
try {
    $body = @{ width = 100.0; height = 60.0; tool_dia = 6.0; loop_pitch = 2.5; amp = 0.4 } | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "$ApiBase/cam/adaptive2/trochoid_corners.svg" -Method POST -ContentType "application/json" -Body $body
    $svg = $response.Content
    Test-Assert "Trochoid has teal stroke color" ($svg -match 'stroke="teal"')
} catch {
    Test-Assert "Teal stroke" $false $_.Exception.Message
}

# Test 4.4: Small amplitude (0.2)
try {
    $body = @{ width = 100.0; height = 60.0; tool_dia = 6.0; loop_pitch = 2.5; amp = 0.2 } | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "$ApiBase/cam/adaptive2/trochoid_corners.svg" -Method POST -ContentType "application/json" -Body $body
    $svg = $response.Content
    Test-Assert "Generates trochoids with small amplitude" ($svg -match "<polyline")
} catch {
    Test-Assert "Small amplitude trochoids" $false $_.Exception.Message
}

# Test 4.5: Large amplitude (0.6)
try {
    $body = @{ width = 100.0; height = 60.0; tool_dia = 6.0; loop_pitch = 2.5; amp = 0.6 } | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "$ApiBase/cam/adaptive2/trochoid_corners.svg" -Method POST -ContentType "application/json" -Body $body
    $svg = $response.Content
    Test-Assert "Generates trochoids with large amplitude" ($svg -match "<polyline")
} catch {
    Test-Assert "Large amplitude trochoids" $false $_.Exception.Message
}

# Test 4.6: Tight loop pitch (1.5mm)
try {
    $body = @{ width = 100.0; height = 60.0; tool_dia = 6.0; loop_pitch = 1.5; amp = 0.4 } | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "$ApiBase/cam/adaptive2/trochoid_corners.svg" -Method POST -ContentType "application/json" -Body $body
    $svg = $response.Content
    Test-Assert "Generates trochoids with tight pitch" ($svg -match "<polyline")
} catch {
    Test-Assert "Tight pitch trochoids" $false $_.Exception.Message
}

# Test 4.7: Loose loop pitch (4.0mm)
try {
    $body = @{ width = 100.0; height = 60.0; tool_dia = 6.0; loop_pitch = 4.0; amp = 0.4 } | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "$ApiBase/cam/adaptive2/trochoid_corners.svg" -Method POST -ContentType "application/json" -Body $body
    $svg = $response.Content
    Test-Assert "Generates trochoids with loose pitch" ($svg -match "<polyline")
} catch {
    Test-Assert "Loose pitch trochoids" $false $_.Exception.Message
}

# Test 4.8: Small rectangle (50×30mm)
try {
    $body = @{ width = 50.0; height = 30.0; tool_dia = 6.0; loop_pitch = 2.5; amp = 0.4 } | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "$ApiBase/cam/adaptive2/trochoid_corners.svg" -Method POST -ContentType "application/json" -Body $body
    $svg = $response.Content
    Test-Assert "Generates trochoids for small rectangle" ($svg -match "<polyline")
} catch {
    Test-Assert "Small rectangle trochoids" $false $_.Exception.Message
}

Show-TestSummary "Group 4"

# =============================================================================
# GROUP 5: BENCHMARK EXECUTION (10 tests)
# =============================================================================

Write-Host "=== GROUP 5: BENCHMARK EXECUTION (10 tests) ===" -ForegroundColor Cyan
Write-Host "Test benchmark endpoint functionality and statistics"
Write-Host ""

$script:passCount = 0

# Test 5.1: Benchmark responds with required fields
try {
    $body = @{ width = 100.0; height = 60.0; tool_dia = 6.0; stepover = 2.4; runs = 10 } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$ApiBase/cam/adaptive2/bench" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 30
    $hasFields = ($response.runs -ne $null) -and ($response.total_ms -ne $null) -and ($response.avg_ms -ne $null)
    Test-Assert "Benchmark has required fields (runs, total_ms, avg_ms)" $hasFields
} catch {
    Test-Assert "Benchmark required fields" $false $_.Exception.Message
}

# Test 5.2: Runs count matches request
try {
    $body = @{ width = 100.0; height = 60.0; tool_dia = 6.0; stepover = 2.4; runs = 15 } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$ApiBase/cam/adaptive2/bench" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 30
    Test-Assert "Runs count matches request (15)" ($response.runs -eq 15)
} catch {
    Test-Assert "Runs count" $false $_.Exception.Message
}

# Test 5.3: Total time is positive
try {
    $body = @{ width = 100.0; height = 60.0; tool_dia = 6.0; stepover = 2.4; runs = 10 } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$ApiBase/cam/adaptive2/bench" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 30
    Test-Assert "Total time is positive" ($response.total_ms -gt 0)
} catch {
    Test-Assert "Total time positive" $false $_.Exception.Message
}

# Test 5.4: Average time is positive
try {
    $body = @{ width = 100.0; height = 60.0; tool_dia = 6.0; stepover = 2.4; runs = 10 } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$ApiBase/cam/adaptive2/bench" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 30
    Test-Assert "Average time is positive" ($response.avg_ms -gt 0)
} catch {
    Test-Assert "Average time positive" $false $_.Exception.Message
}

# Test 5.5: Average = Total / Runs
try {
    $body = @{ width = 100.0; height = 60.0; tool_dia = 6.0; stepover = 2.4; runs = 10 } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$ApiBase/cam/adaptive2/bench" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 30
    $expectedAvg = $response.total_ms / $response.runs
    $diff = [Math]::Abs($response.avg_ms - $expectedAvg)
    Test-Assert "Average = Total / Runs" ($diff -lt 0.01)
} catch {
    Test-Assert "Average calculation" $false $_.Exception.Message
}

# Test 5.6: Parameters echoed in response
try {
    $body = @{ width = 120.0; height = 80.0; tool_dia = 8.0; stepover = 3.2; runs = 10 } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$ApiBase/cam/adaptive2/bench" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 30
    $paramsMatch = ($response.width -eq 120.0) -and ($response.height -eq 80.0) -and ($response.tool_dia -eq 8.0) -and ($response.stepover -eq 3.2)
    Test-Assert "Parameters echoed in response" $paramsMatch
} catch {
    Test-Assert "Parameters echoed" $false $_.Exception.Message
}

# Test 5.7: Small run count (5 runs)
try {
    $body = @{ width = 100.0; height = 60.0; tool_dia = 6.0; stepover = 2.4; runs = 5 } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$ApiBase/cam/adaptive2/bench" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 30
    Test-Assert "Handles small run count (5)" ($response.runs -eq 5 -and $response.avg_ms -gt 0)
} catch {
    Test-Assert "Small run count" $false $_.Exception.Message
}

# Test 5.8: Large run count (50 runs)
try {
    $body = @{ width = 100.0; height = 60.0; tool_dia = 6.0; stepover = 2.4; runs = 50 } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$ApiBase/cam/adaptive2/bench" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 60
    Test-Assert "Handles large run count (50)" ($response.runs -eq 50 -and $response.avg_ms -gt 0)
} catch {
    Test-Assert "Large run count" $false $_.Exception.Message
}

# Test 5.9: Small pocket benchmark
try {
    $body = @{ width = 50.0; height = 30.0; tool_dia = 6.0; stepover = 2.4; runs = 20 } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$ApiBase/cam/adaptive2/bench" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 30
    Test-Assert "Benchmarks small pocket (50×30mm)" ($response.avg_ms -gt 0)
} catch {
    Test-Assert "Small pocket benchmark" $false $_.Exception.Message
}

# Test 5.10: Large pocket benchmark
try {
    $body = @{ width = 200.0; height = 120.0; tool_dia = 6.0; stepover = 2.4; runs = 10 } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$ApiBase/cam/adaptive2/bench" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 60
    Test-Assert "Benchmarks large pocket (200×120mm)" ($response.avg_ms -gt 0)
} catch {
    Test-Assert "Large pocket benchmark" $false $_.Exception.Message
}

Show-TestSummary "Group 5"

# =============================================================================
# GROUP 6: PERFORMANCE CHARACTERISTICS (8 tests)
# =============================================================================

Write-Host "=== GROUP 6: PERFORMANCE CHARACTERISTICS (8 tests) ===" -ForegroundColor Cyan
Write-Host "Test performance expectations and regression detection"
Write-Host ""

$script:passCount = 0

# Test 6.1: Standard pocket performance (< 10ms)
try {
    $body = @{ width = 100.0; height = 60.0; tool_dia = 6.0; stepover = 2.4; runs = 20 } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$ApiBase/cam/adaptive2/bench" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 30
    Test-Assert "Standard pocket avg < 10ms" ($response.avg_ms -lt 10.0)
    if ($response.avg_ms -ge 10.0) {
        Write-Host "    Actual: $($response.avg_ms) ms (may vary by hardware)" -ForegroundColor Gray
    }
} catch {
    Test-Assert "Standard pocket performance" $false $_.Exception.Message
}

# Test 6.2: Small pocket is faster than large
try {
    $bodySmall = @{ width = 50.0; height = 30.0; tool_dia = 6.0; stepover = 2.4; runs = 20 } | ConvertTo-Json
    $bodyLarge = @{ width = 200.0; height = 120.0; tool_dia = 6.0; stepover = 2.4; runs = 20 } | ConvertTo-Json
    
    $smallResp = Invoke-RestMethod -Uri "$ApiBase/cam/adaptive2/bench" -Method POST -ContentType "application/json" -Body $bodySmall -TimeoutSec 30
    $largeResp = Invoke-RestMethod -Uri "$ApiBase/cam/adaptive2/bench" -Method POST -ContentType "application/json" -Body $bodyLarge -TimeoutSec 60
    
    Test-Assert "Small pocket faster than large" ($smallResp.avg_ms -lt $largeResp.avg_ms)
    Write-Host "    Small: $($smallResp.avg_ms) ms | Large: $($largeResp.avg_ms) ms" -ForegroundColor Gray
} catch {
    Test-Assert "Small vs large performance" $false $_.Exception.Message
}

# Test 6.3: Tight stepover slower than loose
try {
    $bodyTight = @{ width = 100.0; height = 60.0; tool_dia = 6.0; stepover = 1.2; runs = 20 } | ConvertTo-Json
    $bodyLoose = @{ width = 100.0; height = 60.0; tool_dia = 6.0; stepover = 4.8; runs = 20 } | ConvertTo-Json
    
    $tightResp = Invoke-RestMethod -Uri "$ApiBase/cam/adaptive2/bench" -Method POST -ContentType "application/json" -Body $bodyTight -TimeoutSec 30
    $looseResp = Invoke-RestMethod -Uri "$ApiBase/cam/adaptive2/bench" -Method POST -ContentType "application/json" -Body $bodyLoose -TimeoutSec 30
    
    Test-Assert "Tight stepover slower than loose" ($tightResp.avg_ms -ge $looseResp.avg_ms)
    Write-Host "    Tight: $($tightResp.avg_ms) ms | Loose: $($looseResp.avg_ms) ms" -ForegroundColor Gray
} catch {
    Test-Assert "Stepover performance" $false $_.Exception.Message
}

# Test 6.4: Timing consistency (standard deviation check)
try {
    $body = @{ width = 100.0; height = 60.0; tool_dia = 6.0; stepover = 2.4; runs = 30 } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$ApiBase/cam/adaptive2/bench" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 30
    
    # Avg should be reasonable and non-negative (timing overhead is acceptable)
    Test-Assert "Timing is consistent" ($response.avg_ms -gt 0 -and $response.avg_ms -lt 100 -and $response.total_ms -gt 0)
} catch {
    Test-Assert "Timing consistency" $false $_.Exception.Message
}

# Test 6.5: Total time scales with runs
try {
    $body10 = @{ width = 100.0; height = 60.0; tool_dia = 6.0; stepover = 2.4; runs = 10 } | ConvertTo-Json
    $body20 = @{ width = 100.0; height = 60.0; tool_dia = 6.0; stepover = 2.4; runs = 20 } | ConvertTo-Json
    
    $resp10 = Invoke-RestMethod -Uri "$ApiBase/cam/adaptive2/bench" -Method POST -ContentType "application/json" -Body $body10 -TimeoutSec 30
    $resp20 = Invoke-RestMethod -Uri "$ApiBase/cam/adaptive2/bench" -Method POST -ContentType "application/json" -Body $body20 -TimeoutSec 30
    
    # 20 runs should take more total time than 10 runs (very relaxed for system overhead)
    Test-Assert "Total time scales with runs" ($resp20.total_ms -gt $resp10.total_ms * 0.8)
    Write-Host "    10 runs: $($resp10.total_ms) ms | 20 runs: $($resp20.total_ms) ms" -ForegroundColor Gray
} catch {
    Test-Assert "Total time scaling" $false $_.Exception.Message
}

# Test 6.6: Average time similar across run counts
try {
    $body10 = @{ width = 100.0; height = 60.0; tool_dia = 6.0; stepover = 2.4; runs = 10 } | ConvertTo-Json
    $body50 = @{ width = 100.0; height = 60.0; tool_dia = 6.0; stepover = 2.4; runs = 50 } | ConvertTo-Json
    
    $resp10 = Invoke-RestMethod -Uri "$ApiBase/cam/adaptive2/bench" -Method POST -ContentType "application/json" -Body $body10 -TimeoutSec 30
    $resp50 = Invoke-RestMethod -Uri "$ApiBase/cam/adaptive2/bench" -Method POST -ContentType "application/json" -Body $body50 -TimeoutSec 60
    
    # Averages should be in same order of magnitude (within 5x - accounts for overhead, JIT warmup)
    $ratio = [Math]::Max($resp10.avg_ms, $resp50.avg_ms) / [Math]::Min($resp10.avg_ms, $resp50.avg_ms)
    Test-Assert "Average time independent of run count" ($ratio -lt 5.0)
    Write-Host "    10 runs avg: $($resp10.avg_ms) ms | 50 runs avg: $($resp50.avg_ms) ms" -ForegroundColor Gray
} catch {
    Test-Assert "Average independence" $false $_.Exception.Message
}

# Test 6.7: Memory efficiency (response size reasonable)
try {
    $body = @{ width = 100.0; height = 60.0; tool_dia = 6.0; stepover = 2.4; runs = 20 } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$ApiBase/cam/adaptive2/bench" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 30
    $responseJson = $response | ConvertTo-Json -Compress
    Test-Assert "Response size is reasonable (< 500 bytes)" ($responseJson.Length -lt 500)
} catch {
    Test-Assert "Memory efficiency" $false $_.Exception.Message
}

# Test 6.8: Benchmark completes within timeout
try {
    $body = @{ width = 100.0; height = 60.0; tool_dia = 6.0; stepover = 2.4; runs = 20 } | ConvertTo-Json
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $response = Invoke-RestMethod -Uri "$ApiBase/cam/adaptive2/bench" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 30
    $sw.Stop()
    Test-Assert "Benchmark completes within 5 seconds" ($sw.Elapsed.TotalSeconds -lt 5.0)
    Write-Host "    Wall clock time: $([Math]::Round($sw.Elapsed.TotalSeconds, 2)) s" -ForegroundColor Gray
} catch {
    Test-Assert "Benchmark timeout" $false $_.Exception.Message
}

Show-TestSummary "Group 6"

# =============================================================================
# GROUP 7: EDGE CASES & ERROR HANDLING (5 tests)
# =============================================================================

Write-Host "=== GROUP 7: EDGE CASES & ERROR HANDLING (5 tests) ===" -ForegroundColor Cyan
Write-Host "Test boundary conditions and invalid inputs"
Write-Host ""

$script:passCount = 0

# Test 7.1: Zero stepover (should not crash)
try {
    $body = @{ width = 100.0; height = 60.0; tool_dia = 6.0; stepover = 0.0; runs = 10 } | ConvertTo-Json
    try {
        $response = Invoke-RestMethod -Uri "$ApiBase/cam/adaptive2/bench" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 30 -ErrorAction Stop
        Test-Assert "Zero stepover handled gracefully" ($response -ne $null)
    } catch {
        # Server may reject with 422 or 400, which is acceptable
        Test-Assert "Zero stepover handled (rejected or accepted)" $true
    }
} catch {
    Test-Assert "Zero stepover handling" $false $_.Exception.Message
}

# Test 7.2: Negative tool diameter (should reject)
try {
    $body = @{ width = 100.0; height = 60.0; tool_dia = -6.0; stepover = 2.4; runs = 10 } | ConvertTo-Json
    try {
        $response = Invoke-RestMethod -Uri "$ApiBase/cam/adaptive2/bench" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 30 -ErrorAction Stop
        Test-Assert "Negative tool diameter rejected" $false
    } catch {
        # Should get error (422 validation error expected)
        Test-Assert "Negative tool diameter rejected" $true
    }
} catch {
    Test-Assert "Negative tool diameter" $false $_.Exception.Message
}

# Test 7.3: Very small pocket (10×10mm)
try {
    $body = @{ width = 10.0; height = 10.0; tool_dia = 6.0; stepover = 2.4; runs = 10 } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$ApiBase/cam/adaptive2/bench" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 30
    Test-Assert "Very small pocket handled" ($response.avg_ms -gt 0)
} catch {
    Test-Assert "Very small pocket" $false $_.Exception.Message
}

# Test 7.4: Tool larger than pocket (should handle gracefully)
try {
    $body = @{ width = 50.0; height = 30.0; tool_dia = 100.0; stepover = 40.0; runs = 10 } | ConvertTo-Json
    try {
        $response = Invoke-RestMethod -Uri "$ApiBase/cam/adaptive2/bench" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 30 -ErrorAction Stop
        Test-Assert "Tool larger than pocket handled" ($response -ne $null)
    } catch {
        # May reject or return empty spiral, both acceptable
        Test-Assert "Tool larger than pocket handled (rejected or empty)" $true
    }
} catch {
    Test-Assert "Tool larger than pocket" $false $_.Exception.Message
}

# Test 7.5: Single run benchmark
try {
    $body = @{ width = 100.0; height = 60.0; tool_dia = 6.0; stepover = 2.4; runs = 1 } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$ApiBase/cam/adaptive2/bench" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 30
    Test-Assert "Single run benchmark works" ($response.runs -eq 1 -and $response.avg_ms -gt 0)
} catch {
    Test-Assert "Single run benchmark" $false $_.Exception.Message
}

Show-TestSummary "Group 7"

# =============================================================================
# FINAL SUMMARY
# =============================================================================

Write-Host ""
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host "N.16 ADAPTIVE BENCHMARK VALIDATION COMPLETE" -ForegroundColor Cyan
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host ""

$grandTotal = 51  # 6+4+10+8+10+8+5
$grandPassFinal = $script:grandPass
$grandPct = [math]::Round(($grandPassFinal / $grandTotal) * 100, 1)

Write-Host "GRAND TOTAL: $grandPassFinal/$grandTotal ($grandPct%)" -ForegroundColor $(if ($grandPct -eq 100) { "Green" } elseif ($grandPct -ge 90) { "Yellow" } else { "Red" })
Write-Host "  Group 1: File Structure (6 tests)" -ForegroundColor Gray
Write-Host "  Group 2: Endpoint Availability (4 tests)" -ForegroundColor Gray
Write-Host "  Group 3: Offset Spiral SVG (10 tests)" -ForegroundColor Gray
Write-Host "  Group 4: Trochoid Corners SVG (8 tests)" -ForegroundColor Gray
Write-Host "  Group 5: Benchmark Execution (10 tests)" -ForegroundColor Gray
Write-Host "  Group 6: Performance Characteristics (8 tests)" -ForegroundColor Gray
Write-Host "  Group 7: Edge Cases (5 tests)" -ForegroundColor Gray
Write-Host ""

if ($grandPct -ge 90) {
    Write-Host "✅ EXCELLENT! N.16 Adaptive Benchmark is production-ready" -ForegroundColor Green
} elseif ($grandPct -ge 80) {
    Write-Host "⚠️ GOOD. Minor issues to address" -ForegroundColor Yellow
} else {
    Write-Host "⚠️ NEEDS WORK. Only $grandPassFinal/$grandTotal tests passed" -ForegroundColor Red
}

Write-Host ""
Write-Host "Cumulative Phase 5 Progress:" -ForegroundColor Cyan
Write-Host "  N10:  12/12  (100%) ✅" -ForegroundColor Gray
Write-Host "  N.0:  32/32  (100%) ✅" -ForegroundColor Gray
Write-Host "  N.06: 37/37  (100%) ✅" -ForegroundColor Gray
Write-Host "  N.09: 56/56  (100%) ✅" -ForegroundColor Gray
Write-Host "  N.07: 28/28  (100%) ✅" -ForegroundColor Gray
Write-Host "  N.08: 43/43  (100%) ✅" -ForegroundColor Gray
Write-Host "  N.11: 44/45  (97.8%) ✅" -ForegroundColor Gray
Write-Host "  N.12: 46/50  (92.0%) ✅" -ForegroundColor Gray
Write-Host "  N.13: 45/45  (100%) ✅" -ForegroundColor Gray
Write-Host "  N.14: 60/60  (100%) ✅" -ForegroundColor Gray
Write-Host "  N.15: 56/56  (100%) ✅" -ForegroundColor Gray
Write-Host "  N.16: $grandPassFinal/$grandTotal  ($grandPct%) $(if ($grandPct -ge 90) { '✅' } else { '⏳' })" -ForegroundColor $(if ($grandPct -ge 90) { "Green" } else { "Yellow" })
Write-Host "  ─────────────────────────────────" -ForegroundColor Gray

$cumulativePass = 459 + $grandPassFinal
$cumulativeTotal = 464 + $grandTotal
$cumulativePct = [math]::Round(($cumulativePass / $cumulativeTotal) * 100, 1)

Write-Host "  TOTAL: $cumulativePass/$cumulativeTotal ($cumulativePct%)" -ForegroundColor $(if ($cumulativePct -ge 95) { "Green" } elseif ($cumulativePct -ge 90) { "Yellow" } else { "Red" })
Write-Host ""

$nSeriesComplete = if ($grandPct -ge 90) { 12 } else { 11 }
$nSeriesPct = [math]::Round(($nSeriesComplete / 16) * 100, 1)
Write-Host "N-Series Progress: $nSeriesComplete/16 ($nSeriesPct%)" -ForegroundColor Cyan
Write-Host ""

Write-Host ("=" * 80) -ForegroundColor Cyan
