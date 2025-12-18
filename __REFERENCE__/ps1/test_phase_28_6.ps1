# Phase 28.6: Frontend Integration Smoke Test
# Tests that frontend can call Phase 28.4 and 28.5 endpoints

Write-Host "=== Phase 28.6: Frontend Integration Test ===" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8001"
$passed = 0
$failed = 0

# Test 1: Bucket detail endpoint (Phase 28.4)
Write-Host "1. Testing bucket detail endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/compare/risk_bucket_detail?lane=rosette&preset=GRBL" -Method GET
    if ($response.Count -gt 0) {
        Write-Host "   ✓ Bucket detail returns $($response.Count) entries" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "   ✗ Bucket detail returned empty array" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "   ✗ Failed: $_" -ForegroundColor Red
    $failed++
}

# Test 2: CSV export endpoint (Phase 28.5)
Write-Host "2. Testing CSV export endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/api/compare/risk_bucket_export?lane=rosette&preset=GRBL&format=csv" -Method GET
    if ($response.StatusCode -eq 200 -and $response.Headers['Content-Type'] -like '*csv*') {
        Write-Host "   ✓ CSV export successful ($(($response.Content -split "`n").Count) lines)" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "   ✗ CSV export returned wrong content type" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "   ✗ Failed: $_" -ForegroundColor Red
    $failed++
}

# Test 3: JSON export endpoint (Phase 28.5)
Write-Host "3. Testing JSON export endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/compare/risk_bucket_export?lane=adaptive&preset=GRBL&format=json" -Method GET
    if ($response.Count -gt 0) {
        Write-Host "   ✓ JSON export returns $($response.Count) entries" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "   ✗ JSON export returned empty array" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "   ✗ Failed: $_" -ForegroundColor Red
    $failed++
}

# Test 4: Frontend accessibility
Write-Host "4. Testing frontend is accessible..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5173/lab/risk-dashboard" -Method GET -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✓ Frontend dashboard accessible" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "   ✗ Frontend returned status $($response.StatusCode)" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "   ✗ Failed: $_" -ForegroundColor Red
    $failed++
}

# Summary
Write-Host ""
Write-Host "=== Test Summary ===" -ForegroundColor Cyan
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor Red

if ($failed -eq 0) {
    Write-Host ""
    Write-Host "✅ Phase 28.6 Integration Complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Frontend Changes:" -ForegroundColor Cyan
    Write-Host "  • Updated endpoint: /api/compare/risk_bucket_detail" -ForegroundColor White
    Write-Host "  • Added Export Bucket CSV button" -ForegroundColor White
    Write-Host "  • Added Export Bucket JSON button" -ForegroundColor White
    Write-Host "  • Export functions use Phase 28.5 endpoint" -ForegroundColor White
    Write-Host ""
    Write-Host "Next: Visit http://localhost:5173/lab/risk-dashboard" -ForegroundColor Yellow
    Write-Host "  1. Click a bucket row to view details" -ForegroundColor White
    Write-Host "  2. Use 'Export Bucket CSV' button" -ForegroundColor White
    Write-Host "  3. Use 'Export Bucket JSON' button" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "❌ Some tests failed. Check errors above." -ForegroundColor Red
}
