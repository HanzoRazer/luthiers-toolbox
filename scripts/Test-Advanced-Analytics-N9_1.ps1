#!/usr/bin/env pwsh
# Test-Advanced-Analytics-N9_1.ps1 — N9.1 Advanced Analytics Test Suite
#
# Tests correlation, anomaly detection, and prediction endpoints.
#
# Prerequisites:
#   - API running at http://localhost:8000
#   - RMOS stores with job data (N8.6)
#
# Usage:
#   .\scripts\Test-Advanced-Analytics-N9_1.ps1

$API = "http://localhost:8000"
$PASSED = 0
$FAILED = 0

Write-Host "=== N9.1 Advanced Analytics Test Suite ===" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# CORRELATION TESTS
# ============================================================================

Write-Host "=== Correlation Analysis ===" -ForegroundColor Yellow

Write-Host "1. Testing GET /api/analytics/advanced/correlation (missing params)" -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$API/api/analytics/advanced/correlation" -Method GET -ErrorAction Stop
    Write-Host "  ✗ Should have failed with 400 for missing params" -ForegroundColor Red
    $FAILED++
} catch {
    if ($_.Exception.Response.StatusCode -eq 400) {
        Write-Host "  ✓ Correctly returned 400 for missing parameters" -ForegroundColor Green
        $PASSED++
    } else {
        Write-Host "  ✗ Unexpected error: $_" -ForegroundColor Red
        $FAILED++
    }
}

Write-Host "2. Testing GET /api/analytics/advanced/correlation?x=job.duration_seconds&y=job.status" -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$API/api/analytics/advanced/correlation?x=job.duration_seconds&y=job.status" -Method GET
    if ($null -ne $response.r -and $null -ne $response.n) {
        Write-Host "  ✓ Correlation computed" -ForegroundColor Green
        Write-Host "    r=$($response.r), n=$($response.n)" -ForegroundColor Gray
        $PASSED++
    } else {
        Write-Host "  ✗ Missing r or n field" -ForegroundColor Red
        $FAILED++
    }
} catch {
    Write-Host "  ✗ Failed: $_" -ForegroundColor Red
    $FAILED++
}

# ============================================================================
# DURATION ANOMALY TESTS
# ============================================================================

Write-Host ""
Write-Host "=== Duration Anomaly Detection ===" -ForegroundColor Yellow

Write-Host "3. Testing GET /api/analytics/advanced/anomalies/durations (default z=3.0)" -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$API/api/analytics/advanced/anomalies/durations" -Method GET
    if ($null -ne $response.anomalies) {
        Write-Host "  ✓ Duration anomalies retrieved" -ForegroundColor Green
        Write-Host "    Anomalies found: $($response.anomalies.Count)" -ForegroundColor Gray
        Write-Host "    Mean: $($response.mean_seconds)s, StDev: $($response.stdev_seconds)s" -ForegroundColor Gray
        $PASSED++
    } else {
        Write-Host "  ✗ Missing anomalies field" -ForegroundColor Red
        $FAILED++
    }
} catch {
    Write-Host "  ✗ Failed: $_" -ForegroundColor Red
    $FAILED++
}

Write-Host "4. Testing GET /api/analytics/advanced/anomalies/durations?z=2.0 (lower threshold)" -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$API/api/analytics/advanced/anomalies/durations?z=2.0" -Method GET
    if ($null -ne $response.anomalies) {
        Write-Host "  ✓ Duration anomalies with z=2.0 retrieved" -ForegroundColor Green
        Write-Host "    Anomalies found: $($response.anomalies.Count)" -ForegroundColor Gray
        $PASSED++
    } else {
        Write-Host "  ✗ Missing anomalies field" -ForegroundColor Red
        $FAILED++
    }
} catch {
    Write-Host "  ✗ Failed: $_" -ForegroundColor Red
    $FAILED++
}

# ============================================================================
# SUCCESS RATE ANOMALY TESTS
# ============================================================================

Write-Host ""
Write-Host "=== Success Rate Anomaly Detection ===" -ForegroundColor Yellow

Write-Host "5. Testing GET /api/analytics/advanced/anomalies/success (default params)" -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$API/api/analytics/advanced/anomalies/success" -Method GET
    if ($null -ne $response.anomalies) {
        Write-Host "  ✓ Success rate anomalies retrieved" -ForegroundColor Green
        Write-Host "    Anomalies found: $($response.anomalies.Count)" -ForegroundColor Gray
        Write-Host "    Mean: $($response.mean)%, StDev: $($response.stdev)%" -ForegroundColor Gray
        $PASSED++
    } else {
        Write-Host "  ✗ Missing anomalies field" -ForegroundColor Red
        $FAILED++
    }
} catch {
    Write-Host "  ✗ Failed: $_" -ForegroundColor Red
    $FAILED++
}

Write-Host "6. Testing GET /api/analytics/advanced/anomalies/success?z=2.5&window_days=7" -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$API/api/analytics/advanced/anomalies/success?z=2.5&window_days=7" -Method GET
    if ($null -ne $response.anomalies) {
        Write-Host "  ✓ Success rate anomalies with custom params retrieved" -ForegroundColor Green
        Write-Host "    Anomalies found: $($response.anomalies.Count)" -ForegroundColor Gray
        $PASSED++
    } else {
        Write-Host "  ✗ Missing anomalies field" -ForegroundColor Red
        $FAILED++
    }
} catch {
    Write-Host "  ✗ Failed: $_" -ForegroundColor Red
    $FAILED++
}

# ============================================================================
# PREDICTION TESTS
# ============================================================================

Write-Host ""
Write-Host "=== Failure Risk Prediction ===" -ForegroundColor Yellow

Write-Host "7. Testing POST /api/analytics/advanced/predict (heuristic model)" -ForegroundColor Cyan
try {
    $body = @{
        pattern_complexity = 75
        material_efficiency = 60
        duration_seconds = 1800
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$API/api/analytics/advanced/predict" -Method POST -Body $body -ContentType "application/json"
    if ($null -ne $response.risk_percent) {
        Write-Host "  ✓ Failure risk predicted" -ForegroundColor Green
        Write-Host "    Risk: $($response.risk_percent)%" -ForegroundColor Gray
        Write-Host "    Explanation: $($response.explanation)" -ForegroundColor Gray
        $PASSED++
    } else {
        Write-Host "  ✗ Missing risk_percent field" -ForegroundColor Red
        $FAILED++
    }
} catch {
    Write-Host "  ✗ Failed: $_" -ForegroundColor Red
    $FAILED++
}

Write-Host "8. Testing POST /api/analytics/advanced/predict (low risk scenario)" -ForegroundColor Cyan
try {
    $body = @{
        pattern_complexity = 20
        material_efficiency = 90
        duration_seconds = 600
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$API/api/analytics/advanced/predict" -Method POST -Body $body -ContentType "application/json"
    if ($null -ne $response.risk_percent) {
        Write-Host "  ✓ Low risk prediction retrieved" -ForegroundColor Green
        Write-Host "    Risk: $($response.risk_percent)%" -ForegroundColor Gray
        $PASSED++
    } else {
        Write-Host "  ✗ Missing risk_percent field" -ForegroundColor Red
        $FAILED++
    }
} catch {
    Write-Host "  ✗ Failed: $_" -ForegroundColor Red
    $FAILED++
}

# ============================================================================
# SUMMARY
# ============================================================================

Write-Host ""
Write-Host "=== Test Summary ===" -ForegroundColor Cyan
Write-Host "  Passed: $PASSED" -ForegroundColor Green
Write-Host "  Failed: $FAILED" -ForegroundColor $(if ($FAILED -eq 0) { "Green" } else { "Red" })

if ($FAILED -eq 0) {
    Write-Host ""
    Write-Host "✓ All N9.1 Advanced Analytics tests passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host ""
    Write-Host "✗ Some tests failed. Review output above." -ForegroundColor Red
    exit 1
}
