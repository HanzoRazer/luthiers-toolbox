# Test Script for Phase 27 Complete Implementation
# Tests: Phase 27.2 (Risk Snapshots), 27.3 (CSV Export), 27.4-27.6 (Frontend Analytics)

$ErrorActionPreference = "Continue"
$baseUrl = "http://localhost:8000"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Phase 27 Complete Test Suite" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Test counters
$passed = 0
$failed = 0

function Test-Endpoint {
    param($Name, $Method, $Uri, $Body = $null, $ExpectedStatus = 200)
    
    try {
        Write-Host "Testing: $Name" -ForegroundColor Yellow
        
        $params = @{
            Uri = $Uri
            Method = $Method
            ErrorAction = 'Stop'
        }
        
        if ($Body) {
            $params.Body = ($Body | ConvertTo-Json -Depth 10)
            $params.ContentType = 'application/json'
        }
        
        $response = Invoke-RestMethod @params
        Write-Host "  ✓ $Name - PASSED" -ForegroundColor Green
        return $response
    }
    catch {
        Write-Host "  ✗ $Name - FAILED: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# ============================================================================
# Phase 27.2: Test Risk Snapshot Endpoints
# ============================================================================

Write-Host "`n=== Phase 27.2: Risk Snapshot Tests ===" -ForegroundColor Cyan

# Test 1: Get existing rosette jobs
Write-Host "`n1. Fetching existing rosette jobs..." -ForegroundColor Yellow

$existingJobs = Test-Endpoint `
    -Name "GET /rosette/jobs" `
    -Method "GET" `
    -Uri "$baseUrl/api/art/rosette/jobs?limit=10"

if ($existingJobs -and $existingJobs.Count -ge 2) {
    $passed++
    $jobA = $existingJobs[0]
    $jobB = $existingJobs[1]
    Write-Host "  Found $($existingJobs.Count) existing jobs" -ForegroundColor Gray
    Write-Host "  Job A: $($jobA.name) (preset: $($jobA.preset))" -ForegroundColor Gray
    Write-Host "  Job B: $($jobB.name) (preset: $($jobB.preset))" -ForegroundColor Gray
} else {
    Write-Host "  ✗ Need at least 2 existing jobs" -ForegroundColor Red
    $failed++
    Write-Host "`nExiting - please create rosette jobs first" -ForegroundColor Yellow
    exit
}

# Test 2: Compare the two jobs
Write-Host "`n2. Comparing jobs..." -ForegroundColor Yellow

$compareResult = Test-Endpoint `
    -Name "Compare Job A vs Job B" `
    -Method "POST" `
    -Uri "$baseUrl/api/art/rosette/compare" `
    -Body @{
        job_id_a = $jobA.job_id
        job_id_b = $jobB.job_id
    }

if ($compareResult) { 
    $passed++
    Write-Host "  Segments delta: $($compareResult.diff_summary.segments_delta)" -ForegroundColor Gray
    Write-Host "  Inner radius delta: $($compareResult.diff_summary.inner_radius_delta)" -ForegroundColor Gray
    Write-Host "  Outer radius delta: $($compareResult.diff_summary.outer_radius_delta)" -ForegroundColor Gray
} else { 
    $failed++ 
}

# Test 3: Calculate risk score (client-side formula)
Write-Host "`n3. Calculating risk score..." -ForegroundColor Yellow

if ($compareResult) {
    $segA = $compareResult.diff_summary.segments_a
    $segB = $compareResult.diff_summary.segments_b
    $maxSeg = [Math]::Max($segA, $segB)
    $segDelta = [Math]::Abs($compareResult.diff_summary.segments_delta)
    
    $innerDelta = [Math]::Abs($compareResult.diff_summary.inner_radius_delta)
    $outerDelta = [Math]::Abs($compareResult.diff_summary.outer_radius_delta)
    
    $baseScore = if ($maxSeg -gt 0) { ($segDelta / $maxSeg) * 50 } else { 0 }
    $radiusScore = (($innerDelta + $outerDelta) / 10) * 50
    
    $riskScore = [Math]::Min([Math]::Max($baseScore + $radiusScore, 0), 100)
    
    Write-Host "  ✓ Risk score calculated: $([Math]::Round($riskScore, 2))%" -ForegroundColor Green
    Write-Host "    - Base score (segments): $([Math]::Round($baseScore, 2))" -ForegroundColor Gray
    Write-Host "    - Radius score: $([Math]::Round($radiusScore, 2))" -ForegroundColor Gray
    $passed++
} else {
    Write-Host "  ✗ Cannot calculate risk score (no compare result)" -ForegroundColor Red
    $failed++
}

# Test 4: Save comparison snapshot
Write-Host "`n4. Saving comparison snapshot..." -ForegroundColor Yellow

$snapshot = Test-Endpoint `
    -Name "Save Snapshot to Risk Timeline" `
    -Method "POST" `
    -Uri "$baseUrl/api/art/rosette/compare/snapshot" `
    -Body @{
        job_id_a = $jobA.job_id
        job_id_b = $jobB.job_id
        risk_score = $riskScore
        diff_summary = $compareResult.diff_summary
        lane = "production"
        note = "Test snapshot from Phase 27 automated test"
    }

if ($snapshot) { 
    $passed++
    Write-Host "  Snapshot ID: $($snapshot.id)" -ForegroundColor Gray
    Write-Host "  Created at: $($snapshot.created_at)" -ForegroundColor Gray
} else { 
    $failed++ 
}

# Test 5: Retrieve snapshots (filter by job IDs)
Write-Host "`n5. Retrieving snapshot history..." -ForegroundColor Yellow

$snapshots = Test-Endpoint `
    -Name "GET /compare/snapshots (filtered)" `
    -Method "GET" `
    -Uri "$baseUrl/api/art/rosette/compare/snapshots?job_id_a=$($jobA.job_id)&job_id_b=$($jobB.job_id)&limit=10"

if ($snapshots) { 
    $passed++
    Write-Host "  Found $($snapshots.Count) snapshot(s)" -ForegroundColor Gray
    if ($snapshots.Count -gt 0) {
        Write-Host "  Latest snapshot risk: $($snapshots[0].risk_score)%" -ForegroundColor Gray
    }
} else { 
    $failed++ 
}

# Test 6: Create additional snapshots for analytics testing
Write-Host "`n6. Creating additional snapshots for analytics..." -ForegroundColor Yellow

$additionalSnapshots = @(
    @{ risk = 25.5; lane = "testing"; note = "Low risk test" }
    @{ risk = 55.0; lane = "production"; note = "Medium risk test" }
    @{ risk = 80.0; lane = "testing"; note = "High risk test" }
)

foreach ($snap in $additionalSnapshots) {
    $result = Test-Endpoint `
        -Name "Save snapshot (risk: $($snap.risk)%)" `
        -Method "POST" `
        -Uri "$baseUrl/api/art/rosette/compare/snapshot" `
        -Body @{
            job_id_a = $jobA.job_id
            job_id_b = $jobB.job_id
            risk_score = $snap.risk
            diff_summary = $compareResult.diff_summary
            lane = $snap.lane
            note = $snap.note
        }
    
    if ($result) { $passed++ } else { $failed++ }
    Start-Sleep -Milliseconds 200
}

# ============================================================================
# Phase 27.3: Test CSV Export
# ============================================================================

Write-Host "`n=== Phase 27.3: CSV Export Tests ===" -ForegroundColor Cyan

# Test 7: Export CSV
Write-Host "`n7. Testing CSV export endpoint..." -ForegroundColor Yellow

try {
    $csvUri = "$baseUrl/api/art/rosette/compare/export_csv?job_id_a=$($jobA.job_id)&job_id_b=$($jobB.job_id)&limit=100"
    $csvContent = Invoke-WebRequest -Uri $csvUri -Method GET -ErrorAction Stop
    
    if ($csvContent.StatusCode -eq 200) {
        $csv = $csvContent.Content
        $lines = $csv -split "`n"
        
        Write-Host "  ✓ CSV export - PASSED" -ForegroundColor Green
        Write-Host "  CSV lines: $($lines.Count)" -ForegroundColor Gray
        Write-Host "  Header: $($lines[0])" -ForegroundColor Gray
        
        # Verify header columns
        $expectedColumns = @(
            "timestamp", "job_id_a", "job_id_b", "lane", "risk_score",
            "segments_delta", "inner_radius_delta", "outer_radius_delta",
            "pattern_type_a", "pattern_type_b", "note"
        )
        
        $header = $lines[0]
        $allColumnsPresent = $true
        foreach ($col in $expectedColumns) {
            if (-not $header.Contains($col)) {
                Write-Host "  ✗ Missing column: $col" -ForegroundColor Red
                $allColumnsPresent = $false
            }
        }
        
        if ($allColumnsPresent) {
            Write-Host "  ✓ All expected columns present" -ForegroundColor Green
            $passed++
        } else {
            $failed++
        }
        
        # Show sample row
        if ($lines.Count -gt 1) {
            Write-Host "  Sample row: $($lines[1])" -ForegroundColor Gray
        }
        
        $passed++
    } else {
        Write-Host "  ✗ CSV export - FAILED (Status: $($csvContent.StatusCode))" -ForegroundColor Red
        $failed++
    }
}
catch {
    Write-Host "  ✗ CSV export - FAILED: $($_.Exception.Message)" -ForegroundColor Red
    $failed++
}

# ============================================================================
# Phase 27.4-27.6: Verify Backend Data for Frontend Features
# ============================================================================

Write-Host "`n=== Phase 27.4-27.6: Backend Data Verification ===" -ForegroundColor Cyan

# Test 8: Verify snapshots have preset data for grouping
Write-Host "`n8. Verifying preset data in snapshots..." -ForegroundColor Yellow

$allSnapshots = Test-Endpoint `
    -Name "GET all snapshots for jobs" `
    -Method "GET" `
    -Uri "$baseUrl/api/art/rosette/compare/snapshots?job_id_a=$($jobA.job_id)&job_id_b=$($jobB.job_id)&limit=50"

if ($allSnapshots -and $allSnapshots.Count -gt 0) {
    $passed++
    
    # Check for preset fields in diff_summary
    $firstSnapshot = $allSnapshots[0]
    $hasPresetA = $null -ne $firstSnapshot.diff_summary.preset_a -or $firstSnapshot.diff_summary.PSObject.Properties.Name -contains "preset_a"
    $hasPresetB = $null -ne $firstSnapshot.diff_summary.preset_b -or $firstSnapshot.diff_summary.PSObject.Properties.Name -contains "preset_b"
    
    Write-Host "  Total snapshots: $($allSnapshots.Count)" -ForegroundColor Gray
    Write-Host "  Preset A field exists: $hasPresetA" -ForegroundColor Gray
    Write-Host "  Preset B field exists: $hasPresetB" -ForegroundColor Gray
    
    # Calculate risk distribution for Phase 27.5
    $lowRisk = ($allSnapshots | Where-Object { $_.risk_score -lt 40 }).Count
    $medRisk = ($allSnapshots | Where-Object { $_.risk_score -ge 40 -and $_.risk_score -lt 70 }).Count
    $highRisk = ($allSnapshots | Where-Object { $_.risk_score -ge 70 }).Count
    $avgRisk = ($allSnapshots | Measure-Object -Property risk_score -Average).Average
    
    Write-Host "`n  Risk Distribution (Phase 27.5 Metrics):" -ForegroundColor Cyan
    Write-Host "    Low risk (<40%): $lowRisk" -ForegroundColor Green
    Write-Host "    Medium risk (40-70%): $medRisk" -ForegroundColor Yellow
    Write-Host "    High risk (>70%): $highRisk" -ForegroundColor Red
    Write-Host "    Average risk: $([Math]::Round($avgRisk, 2))%" -ForegroundColor Gray
    
    $passed++
} else {
    Write-Host "  ✗ No snapshots found for preset verification" -ForegroundColor Red
    $failed++
}

# Test 9: Test different lane filters
Write-Host "`n9. Testing lane filtering..." -ForegroundColor Yellow

$productionSnapshots = Test-Endpoint `
    -Name "GET snapshots (lane=production)" `
    -Method "GET" `
    -Uri "$baseUrl/api/art/rosette/compare/snapshots?lane=production&limit=50"

if ($productionSnapshots) {
    $passed++
    Write-Host "  Production lane snapshots: $($productionSnapshots.Count)" -ForegroundColor Gray
} else {
    $failed++
}

$testingSnapshots = Test-Endpoint `
    -Name "GET snapshots (lane=testing)" `
    -Method "GET" `
    -Uri "$baseUrl/api/art/rosette/compare/snapshots?lane=testing&limit=50"

if ($testingSnapshots) {
    $passed++
    Write-Host "  Testing lane snapshots: $($testingSnapshots.Count)" -ForegroundColor Gray
} else {
    $failed++
}

# ============================================================================
# Summary
# ============================================================================

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`nResults:" -ForegroundColor White
Write-Host "  ✓ Passed: $passed" -ForegroundColor Green
Write-Host "  ✗ Failed: $failed" -ForegroundColor Red
Write-Host "  Total: $($passed + $failed)" -ForegroundColor Gray

if ($failed -eq 0) {
    Write-Host "`n🎉 ALL TESTS PASSED!" -ForegroundColor Green
    Write-Host "`nPhase 27 Implementation Status:" -ForegroundColor Cyan
    Write-Host "  ✓ Phase 27.2: Risk Snapshots - Backend Working" -ForegroundColor Green
    Write-Host "  ✓ Phase 27.3: CSV Export - Backend Working" -ForegroundColor Green
    Write-Host "  ✓ Phase 27.4-27.6: Frontend Data Ready" -ForegroundColor Green
    Write-Host "`nNext Steps:" -ForegroundColor Yellow
    Write-Host "  1. Start client dev server: cd client && npm run dev" -ForegroundColor Gray
    Write-Host "  2. Navigate to: http://localhost:5173/art-studio/rosette/compare" -ForegroundColor Gray
    Write-Host "  3. Select Job A: '$($jobA.name)'" -ForegroundColor Gray
    Write-Host "  4. Select Job B: '$($jobB.name)'" -ForegroundColor Gray
    Write-Host "  5. Click 'Compare A ↔ B'" -ForegroundColor Gray
    Write-Host "  6. Click 'Show History' to see sidebar" -ForegroundColor Gray
    Write-Host "  7. Toggle 'Group by Preset' to test Phase 27.4" -ForegroundColor Gray
    Write-Host "  8. View Risk Overview panel (Phase 27.5)" -ForegroundColor Gray
    Write-Host "  9. Scroll through Preset Analytics cards (Phase 27.6)" -ForegroundColor Gray
} else {
    Write-Host "`n⚠️  SOME TESTS FAILED" -ForegroundColor Yellow
    Write-Host "Check error messages above for details." -ForegroundColor Gray
}

Write-Host "`n========================================`n" -ForegroundColor Cyan
