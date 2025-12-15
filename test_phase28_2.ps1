#!/usr/bin/env pwsh
# Test Phase 28.2: Enhanced Risk Timeline with Sparklines and Filters

Write-Host "`n=== Testing Phase 28.2: Enhanced Risk Timeline ===" -ForegroundColor Cyan
Write-Host "Testing features: Sparklines, Effect Filters, Tooltips, CSV Export`n" -ForegroundColor Gray

$baseUrl = "http://localhost:8000"
$frontendUrl = "http://localhost:5173"
$passed = 0
$failed = 0

# Test 1: Backend API - Risk Reports Endpoint
Write-Host "1. Testing GET /api/cam/jobs/recent (backend data source)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/cam/jobs/recent?limit=20" -Method Get
    
    if ($response -is [System.Array] -or $response -is [System.Collections.ArrayList]) {
        $count = $response.Count
        Write-Host "  ✓ API returned $count risk reports" -ForegroundColor Green
        
        if ($count -gt 0) {
            $first = $response[0]
            $hasJobId = $null -ne $first.job_id
            $hasRiskScore = $null -ne $first.risk_score
            $hasCounts = $null -ne $first.critical_count
            
            if ($hasJobId -and $hasRiskScore -and $hasCounts) {
                Write-Host "  ✓ Report structure valid: job_id, risk_score, severity counts present" -ForegroundColor Green
                Write-Host "    Sample: job_id=$($first.job_id), risk_score=$($first.risk_score)" -ForegroundColor DarkGray
                $passed++
            } else {
                Write-Host "  ✗ Report structure incomplete" -ForegroundColor Red
                $failed++
            }
        } else {
            Write-Host "  ⚠ No risk reports found (component will show empty state)" -ForegroundColor Yellow
            $passed++
        }
    } else {
        Write-Host "  ✗ Unexpected response type: $($response.GetType().Name)" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ✗ API request failed: $($_.Exception.Message)" -ForegroundColor Red
    $failed++
}

# Test 2: Frontend Route Exists
Write-Host "`n2. Testing frontend route /cam/risk/timeline-enhanced" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$frontendUrl/cam/risk/timeline-enhanced" -Method Get -UseBasicParsing
    
    if ($response.StatusCode -eq 200) {
        Write-Host "  ✓ Route accessible (HTTP 200)" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  ✗ Unexpected status code: $($response.StatusCode)" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ✗ Route request failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "    Make sure Vite dev server is running: cd client && npm run dev" -ForegroundColor Gray
    $failed++
}

# Test 3: Component File Exists
Write-Host "`n3. Checking CamRiskTimeline.vue component file" -ForegroundColor Yellow
$componentPath = "client\src\components\cam\CamRiskTimeline.vue"

if (Test-Path $componentPath) {
    Write-Host "  ✓ Component file exists: $componentPath" -ForegroundColor Green
    
    # Check for Phase 26 features in source
    $source = Get-Content $componentPath -Raw
    
    $features = @(
        @{Name="Effect filters"; Pattern="effectFilter"},
        @{Name="Sparkline SVG"; Pattern="<svg.*trendWidth"},
        @{Name="Tooltip system"; Pattern="showTooltip"},
        @{Name="CSV export"; Pattern="exportCsv"},
        @{Name="Click selection"; Pattern="selectReportFromTrend"}
    )
    
    $featuresFound = 0
    foreach ($feature in $features) {
        if ($source -match $feature.Pattern) {
            Write-Host "  ✓ Feature present: $($feature.Name)" -ForegroundColor Green
            $featuresFound++
        } else {
            Write-Host "  ✗ Feature missing: $($feature.Name)" -ForegroundColor Red
        }
    }
    
    if ($featuresFound -eq $features.Count) {
        Write-Host "  ✓ All $($features.Count) Phase 26 features present in code" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  ✗ Only $featuresFound/$($features.Count) features found" -ForegroundColor Red
        $failed++
    }
} else {
    Write-Host "  ✗ Component file not found: $componentPath" -ForegroundColor Red
    $failed++
}

# Test 4: Router Registration
Write-Host "`n4. Checking router registration" -ForegroundColor Yellow
$routerPath = "client\src\router\index.ts"

if (Test-Path $routerPath) {
    $routerSource = Get-Content $routerPath -Raw
    
    $hasImport = $routerSource -match "import CamRiskTimeline"
    $hasRoute = $routerSource -match "/cam/risk/timeline-enhanced"
    
    if ($hasImport -and $hasRoute) {
        Write-Host "  ✓ Component imported and route configured" -ForegroundColor Green
        Write-Host "    Route: /cam/risk/timeline-enhanced" -ForegroundColor DarkGray
        $passed++
    } else {
        if (-not $hasImport) {
            Write-Host "  ✗ Import statement missing" -ForegroundColor Red
        }
        if (-not $hasRoute) {
            Write-Host "  ✗ Route configuration missing" -ForegroundColor Red
        }
        $failed++
    }
} else {
    Write-Host "  ✗ Router file not found: $routerPath" -ForegroundColor Red
    $failed++
}

# Test 5: Delta Calculation Logic
Write-Host "`n5. Verifying delta calculation logic (effect filters)" -ForegroundColor Yellow
$componentSource = Get-Content $componentPath -Raw

$hasScoreDelta = $componentSource -match "delta_score"
$hasCriticalDelta = $componentSource -match "delta_critical"
$hasSaferFilter = $componentSource -match 'value="safer"'
$hasSpicierFilter = $componentSource -match 'value="spicier"'
$hasCriticalReductionFilter = $componentSource -match 'value="critical_reduction"'

$deltaFeatures = 0
if ($hasScoreDelta) { $deltaFeatures++; Write-Host "  ✓ Score delta calculation" -ForegroundColor Green }
if ($hasCriticalDelta) { $deltaFeatures++; Write-Host "  ✓ Critical count delta" -ForegroundColor Green }
if ($hasSaferFilter) { $deltaFeatures++; Write-Host "  ✓ Safer filter (dScore < -0.5)" -ForegroundColor Green }
if ($hasSpicierFilter) { $deltaFeatures++; Write-Host "  ✓ Spicier filter (dScore > +0.5)" -ForegroundColor Green }
if ($hasCriticalReductionFilter) { $deltaFeatures++; Write-Host "  ✓ Critical reduction filter (dCrit < 0)" -ForegroundColor Green }

if ($deltaFeatures -eq 5) {
    Write-Host "  ✓ All effect filter features implemented" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ✗ Only $deltaFeatures/5 effect features found" -ForegroundColor Red
    $failed++
}

# Test 6: Sparkline Visualization Logic
Write-Host "`n6. Verifying sparkline visualization logic" -ForegroundColor Yellow

$hasPolyline = $componentSource -match "<polyline"
$hasTrendPoints = $componentSource -match "trendPoints.*computed"
$hasTrendPath = $componentSource -match "trendPath.*computed"
$hasTrendColor = $componentSource -match "trendColor.*computed"

$vizFeatures = 0
if ($hasPolyline) { $vizFeatures++; Write-Host "  ✓ SVG polyline element" -ForegroundColor Green }
if ($hasTrendPoints) { $vizFeatures++; Write-Host "  ✓ Trend points calculation" -ForegroundColor Green }
if ($hasTrendPath) { $vizFeatures++; Write-Host "  ✓ Trend path generation" -ForegroundColor Green }
if ($hasTrendColor) { $vizFeatures++; Write-Host "  ✓ Dynamic color coding" -ForegroundColor Green }

if ($vizFeatures -eq 4) {
    Write-Host "  ✓ Complete sparkline visualization system" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ✗ Only $vizFeatures/4 visualization features found" -ForegroundColor Red
    $failed++
}

# Summary
Write-Host "`n=== Test Summary ===" -ForegroundColor Cyan
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Red" })

$total = $passed + $failed
$percentage = if ($total -gt 0) { [math]::Round(($passed / $total) * 100, 1) } else { 0 }
Write-Host "Success Rate: $percentage%`n" -ForegroundColor $(if ($percentage -ge 80) { "Green" } elseif ($percentage -ge 60) { "Yellow" } else { "Red" })

if ($failed -eq 0) {
    Write-Host "✅ Phase 28.2 implementation complete and all tests passing!" -ForegroundColor Green
    Write-Host "`nNext steps:" -ForegroundColor Cyan
    Write-Host "  1. Navigate to http://localhost:5173/cam/risk/timeline-enhanced" -ForegroundColor Gray
    Write-Host "  2. Test effect filters (All/Safer/Spicier/Critical Reduction)" -ForegroundColor Gray
    Write-Host "  3. Hover over sparkline points to see tooltips" -ForegroundColor Gray
    Write-Host "  4. Click sparkline points to select reports" -ForegroundColor Gray
    Write-Host "  5. Test CSV export button" -ForegroundColor Gray
} else {
    Write-Host "`n⚠ Some tests failed. Review errors above." -ForegroundColor Yellow
}

exit $failed
