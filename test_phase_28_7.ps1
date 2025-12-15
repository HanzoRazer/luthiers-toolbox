# Phase 28.7: Time-Windowed Risk View Smoke Test
# Tests time-window filtering on all three endpoints

Write-Host "=== Phase 28.7: Time-Windowed Risk View Test ===" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8001"
$passed = 0
$failed = 0

# Test 1: Aggregate with since filter
Write-Host "1. Testing aggregate with since filter..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/compare/risk_aggregate?since=2025-11-12T00:00:00" -Method GET
    $rosetteBucket = $response | Where-Object { $_.lane -eq "rosette" -and $_.preset -eq "GRBL" }
    if ($rosetteBucket -and $rosetteBucket.count -eq 4) {
        Write-Host "   ✓ Filtered to $($rosetteBucket.count) entries (j1 excluded)" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "   ✗ Expected 4 entries, got $($rosetteBucket.count)" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "   ✗ Failed: $_" -ForegroundColor Red
    $failed++
}

# Test 2: Aggregate with time window
Write-Host "2. Testing aggregate with time window (since + until)..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/compare/risk_aggregate?since=2025-11-12T00:00:00&until=2025-11-13T00:00:00" -Method GET
    $rosetteBucket = $response | Where-Object { $_.lane -eq "rosette" -and $_.preset -eq "GRBL" }
    if ($rosetteBucket -and $rosetteBucket.count -eq 2) {
        Write-Host "   ✓ Window contains exactly $($rosetteBucket.count) entries" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "   ✗ Expected 2 entries, got $($rosetteBucket.count)" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "   ✗ Failed: $_" -ForegroundColor Red
    $failed++
}

# Test 3: Bucket detail with since filter
Write-Host "3. Testing bucket detail with since filter..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/compare/risk_bucket_detail?lane=rosette&preset=GRBL&since=2025-11-12T08:00:00" -Method GET
    if ($response.Count -eq 4) {
        Write-Host "   ✓ Detail filtered to $($response.Count) entries" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "   ✗ Expected 4 entries, got $($response.Count)" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "   ✗ Failed: $_" -ForegroundColor Red
    $failed++
}

# Test 4: CSV export with time window
Write-Host "4. Testing CSV export with time window..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/api/compare/risk_bucket_export?lane=adaptive&preset=GRBL&since=2025-11-12T12:00:00&format=csv" -Method GET
    if ($response.StatusCode -eq 200) {
        $lineCount = ($response.Content -split "`n").Count - 1  # Exclude header
        Write-Host "   ✓ CSV export with time filter ($lineCount data rows)" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "   ✗ CSV export failed" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "   ✗ Failed: $_" -ForegroundColor Red
    $failed++
}

# Test 5: JSON export with until filter
Write-Host "5. Testing JSON export with until filter..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/compare/risk_bucket_export?lane=rosette&until=2025-11-12T14:00:00&format=json" -Method GET
    if ($response.Count -gt 0) {
        Write-Host "   ✓ JSON export with until filter ($($response.Count) entries)" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "   ✗ JSON export returned empty" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "   ✗ Failed: $_" -ForegroundColor Red
    $failed++
}

# Test 6: Empty window (future dates)
Write-Host "6. Testing empty time window..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/compare/risk_aggregate?since=2025-12-01T00:00:00" -Method GET
    if ($response.Count -eq 0) {
        Write-Host "   ✓ Empty window returns no results (as expected)" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "   ✗ Expected empty array, got $($response.Count) entries" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "   ✗ Failed: $_" -ForegroundColor Red
    $failed++
}

# Summary
Write-Host ""
Write-Host "=== Test Summary ===" -ForegroundColor Cyan
Write-Host "Passed: $passed/6" -ForegroundColor Green
Write-Host "Failed: $failed/6" -ForegroundColor Red

if ($failed -eq 0) {
    Write-Host ""
    Write-Host "✅ Phase 28.7 Complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Time-Window Filtering Capabilities:" -ForegroundColor Cyan
    Write-Host "  • Aggregate endpoint: ?since=ISO&until=ISO" -ForegroundColor White
    Write-Host "  • Bucket detail endpoint: ?since=ISO&until=ISO" -ForegroundColor White
    Write-Host "  • Export endpoints: ?since=ISO&until=ISO&format=csv|json" -ForegroundColor White
    Write-Host ""
    Write-Host "Example Queries:" -ForegroundColor Cyan
    Write-Host "  GET /api/compare/risk_aggregate?since=2025-11-12T00:00:00" -ForegroundColor White
    Write-Host "  GET /api/compare/risk_bucket_detail?lane=rosette&since=2025-11-10T00:00:00&until=2025-11-15T00:00:00" -ForegroundColor White
    Write-Host "  GET /api/compare/risk_bucket_export?preset=GRBL&since=2025-11-12T00:00:00&format=csv" -ForegroundColor White
    Write-Host ""
    Write-Host "Frontend Support:" -ForegroundColor Cyan
    Write-Host "  • Dashboard already has since/until filters in UI" -ForegroundColor White
    Write-Host "  • Frontend uses these parameters when refreshing data" -ForegroundColor White
    Write-Host "  • Time ranges can be saved as named views" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "❌ Some tests failed. Check errors above." -ForegroundColor Red
}
