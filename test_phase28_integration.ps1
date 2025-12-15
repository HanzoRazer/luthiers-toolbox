# Phase 28.1: Risk Dashboard Integration Test
# Verify Phase 27 snapshots flow into cross-lab dashboard

Write-Host "`n=== Phase 28.1: Risk Dashboard Integration Test ===`n" -ForegroundColor Cyan

$ErrorActionPreference = "Stop"
$baseUrl = "http://localhost:8000"

# Test counters
$passed = 0
$failed = 0

function Test-Endpoint {
    param($Name, $Url, $Checks)
    Write-Host "`n$Name" -ForegroundColor Yellow
    Write-Host "URL: $Url" -ForegroundColor Gray
    
    try {
        $response = Invoke-RestMethod -Uri $Url -Method Get -ErrorAction Stop
        
        foreach ($check in $Checks) {
            try {
                $result = & $check $response
                $checkName = "Check passed"
                if ($result) {
                    Write-Host "  ✓ $checkName" -ForegroundColor Green
                    $script:passed++
                } else {
                    Write-Host "  ✗ $checkName" -ForegroundColor Red
                    $script:failed++
                }
            } catch {
                Write-Host "  ✗ Check error: $($_.Exception.Message)" -ForegroundColor Red
                $script:failed++
            }
        }
    } catch {
        Write-Host "  ✗ Request failed: $($_.Exception.Message)" -ForegroundColor Red
        $script:failed++
    }
}

Write-Host "=== Test 1: Phase 27 Snapshot Data ===" -ForegroundColor Cyan

# Get Phase 27 rosette comparison snapshots
Write-Host "`nTest 1.1: Get rosette snapshots from Phase 27" -ForegroundColor Yellow
try {
    $snapshots = Invoke-RestMethod -Uri "$baseUrl/api/art/rosette/compare/snapshots?limit=10" -Method Get
    Write-Host "  Found $($snapshots.Length) snapshots" -ForegroundColor Gray
    
    if ($snapshots.Length -gt 0) {
        Write-Host "  ✓ Phase 27 snapshots exist in database" -ForegroundColor Green
        $passed++
        
        # Show sample snapshot
        $sample = $snapshots[0]
        Write-Host "`n  Sample snapshot:" -ForegroundColor Gray
        Write-Host "    snapshot_id: $($sample.snapshot_id)" -ForegroundColor Gray
        Write-Host "    lane: $($sample.lane)" -ForegroundColor Gray
        Write-Host "    preset_a: $($sample.preset_a)" -ForegroundColor Gray
        Write-Host "    preset_b: $($sample.preset_b)" -ForegroundColor Gray
        Write-Host "    risk_score: $($sample.risk_score)%" -ForegroundColor Gray
        Write-Host "    created_at: $($sample.created_at)" -ForegroundColor Gray
    } else {
        Write-Host "  ✗ No Phase 27 snapshots found - run Phase 27 tests first" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ✗ Failed to get snapshots: $($_.Exception.Message)" -ForegroundColor Red
    $failed++
}

Write-Host "`n=== Test 2: Compare Risk Log (Legacy System) ===" -ForegroundColor Cyan

# Check if compare_risk_log.json exists
$logPath = "services\api\app\data\compare_risk_log.json"
Write-Host "`nTest 2.1: Check compare_risk_log.json" -ForegroundColor Yellow
if (Test-Path $logPath) {
    $logData = Get-Content $logPath | ConvertFrom-Json
    $entryCount = $logData.entries.Length
    Write-Host "  Found $entryCount entries in compare_risk_log.json" -ForegroundColor Gray
    
    if ($entryCount -gt 0) {
        Write-Host "  ✓ Legacy log system has data" -ForegroundColor Green
        $passed++
        
        # Show sample entry
        $sample = $logData.entries[0]
        Write-Host "`n  Sample entry:" -ForegroundColor Gray
        Write-Host "    ts: $($sample.ts)" -ForegroundColor Gray
        Write-Host "    lane: $($sample.lane)" -ForegroundColor Gray
        Write-Host "    preset: $($sample.preset)" -ForegroundColor Gray
        Write-Host "    added_paths: $($sample.added_paths)" -ForegroundColor Gray
        Write-Host "    removed_paths: $($sample.removed_paths)" -ForegroundColor Gray
    } else {
        Write-Host "  ⚠ Legacy log exists but is empty" -ForegroundColor Yellow
        $passed++
    }
} else {
    Write-Host "  ⚠ compare_risk_log.json does not exist (will be created)" -ForegroundColor Yellow
    $passed++
}

Write-Host "`n=== Test 3: Risk Aggregation Endpoints ===" -ForegroundColor Cyan

# Test compare risk aggregate endpoint
Write-Host "`nTest 3.1: GET /api/compare/risk_aggregate" -ForegroundColor Yellow
try {
    $aggregates = Invoke-RestMethod -Uri "$baseUrl/api/compare/risk_aggregate" -Method Get
    Write-Host "  ✓ Endpoint returned $($aggregates.Length) buckets" -ForegroundColor Green
    $passed++
    
    if ($aggregates.Length -gt 0) {
        Write-Host "  ✓ Has aggregated data" -ForegroundColor Green
        $passed++
    }
} catch {
    Write-Host "  ✗ Request failed: $($_.Exception.Message)" -ForegroundColor Red
    $failed++
}

# Test with lane filter
Write-Host "`nTest 3.2: GET /api/compare/risk_aggregate (time filtered)" -ForegroundColor Yellow
try {
    $filtered = Invoke-RestMethod -Uri "$baseUrl/api/compare/risk_aggregate?since=2025-11-01T00:00:00" -Method Get
    Write-Host "  ✓ Endpoint returned $($filtered.Length) filtered buckets" -ForegroundColor Green
    $passed++
} catch {
    Write-Host "  ✗ Request failed: $($_.Exception.Message)" -ForegroundColor Red
    $failed++
}

# Test bucket detail endpoint
Write-Host "`nTest 3.3: GET /api/compare/risk_bucket_detail" -ForegroundColor Yellow
try {
    $details = Invoke-RestMethod -Uri "$baseUrl/api/compare/risk_bucket_detail" -Method Get
    Write-Host "  ✓ Endpoint returned $($details.Length) detail entries" -ForegroundColor Green
    $passed++
} catch {
    Write-Host "  ✗ Request failed: $($_.Exception.Message)" -ForegroundColor Red
    $failed++
}

Write-Host "`n=== Test 4: Integration Analysis ===" -ForegroundColor Cyan

Write-Host "`nTest 4.1: Data Source Analysis" -ForegroundColor Yellow

# Check if risk_aggregate is reading from log or database
try {
    $aggregates = Invoke-RestMethod -Uri "$baseUrl/api/compare/risk_aggregate" -Method Get
    $rosetteBuckets = $aggregates | Where-Object { $_.lane -eq "rosette" }
    
    if ($rosetteBuckets) {
        Write-Host "  ✓ Found $($rosetteBuckets.Length) rosette lane buckets in aggregation" -ForegroundColor Green
        $passed++
        
        foreach ($bucket in $rosetteBuckets) {
            Write-Host "`n  Rosette bucket:" -ForegroundColor Gray
            Write-Host "    preset: $($bucket.preset)" -ForegroundColor Gray
            Write-Host "    count: $($bucket.count)" -ForegroundColor Gray
            Write-Host "    risk_score: $($bucket.risk_score)" -ForegroundColor Gray
            Write-Host "    risk_label: $($bucket.risk_label)" -ForegroundColor Gray
        }
    } else {
        Write-Host "  ⚠ No rosette lane data in aggregation" -ForegroundColor Yellow
        Write-Host "    This means Phase 27 snapshots are NOT flowing to dashboard" -ForegroundColor Yellow
        Write-Host "    Integration needed: Sync rosette_compare_risk table → compare_risk_log.json" -ForegroundColor Yellow
        $failed++
    }
} catch {
    Write-Host "  ✗ Failed to analyze aggregation: $($_.Exception.Message)" -ForegroundColor Red
    $failed++
}

Write-Host "`n=== Test 5: Frontend Dashboard Check ===" -ForegroundColor Cyan

Write-Host "`nTest 5.1: Check if RiskDashboardCrossLab route exists" -ForegroundColor Yellow
# This test requires the frontend to be running
Write-Host "  ⚠ Manual test: Open http://localhost:5173/risk-dashboard" -ForegroundColor Yellow
Write-Host "  Expected: Cross-Lab Preset Risk Dashboard should display" -ForegroundColor Gray
Write-Host "  Should show: Lane/preset buckets with risk scores" -ForegroundColor Gray

Write-Host "`n=== Test Results Summary ===" -ForegroundColor Cyan
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor Red

if ($failed -eq 0) {
    Write-Host "`n✓ All tests passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n✗ Some tests failed - see output above" -ForegroundColor Red
    exit 1
}
