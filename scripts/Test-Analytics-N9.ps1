#!/usr/bin/env pwsh
# Test-Analytics-N9.ps1 — N9.0 RMOS Analytics Engine Test Suite
#
# Tests all pattern, material, and job analytics endpoints.
#
# Prerequisites:
#   - API running at http://localhost:8000
#   - RMOS stores initialized with test data (N8.6)
#
# Usage:
#   .\Test-Analytics-N9.ps1

$API = "http://localhost:8000"
$PASSED = 0
$FAILED = 0

Write-Host "=== N9.0 RMOS Analytics Engine Test Suite ===" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# PATTERN ANALYTICS TESTS
# ============================================================================

Write-Host "=== Pattern Analytics ===" -ForegroundColor Yellow

Write-Host "1. Testing GET /api/analytics/patterns/complexity" -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$API/api/analytics/patterns/complexity" -Method GET
    if ($response.categories) {
        Write-Host "  ✓ Complexity distribution retrieved" -ForegroundColor Green
        Write-Host "    Total patterns: $($response.total_patterns)" -ForegroundColor Gray
        Write-Host "    Categories: $($response.categories.Keys -join ', ')" -ForegroundColor Gray
        $PASSED++
    } else {
        Write-Host "  ✗ Missing categories field" -ForegroundColor Red
        $FAILED++
    }
} catch {
    Write-Host "  ✗ Failed: $_" -ForegroundColor Red
    $FAILED++
}

Write-Host "2. Testing GET /api/analytics/patterns/rings" -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$API/api/analytics/patterns/rings" -Method GET
    if ($null -ne $response.min_rings) {
        Write-Host "  ✓ Ring statistics retrieved" -ForegroundColor Green
        Write-Host "    Ring range: $($response.min_rings) - $($response.max_rings)" -ForegroundColor Gray
        Write-Host "    Average: $($response.avg_rings)" -ForegroundColor Gray
        $PASSED++
    } else {
        Write-Host "  ✗ Missing min_rings field" -ForegroundColor Red
        $FAILED++
    }
} catch {
    Write-Host "  ✗ Failed: $_" -ForegroundColor Red
    $FAILED++
}

Write-Host "3. Testing GET /api/analytics/patterns/geometry" -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$API/api/analytics/patterns/geometry" -Method GET
    if ($response.radius) {
        Write-Host "  ✓ Geometry metrics retrieved" -ForegroundColor Green
        Write-Host "    Radius range: $($response.radius.min_mm) - $($response.radius.max_mm) mm" -ForegroundColor Gray
        Write-Host "    Total segments: $($response.segments.total_segments)" -ForegroundColor Gray
        $PASSED++
    } else {
        Write-Host "  ✗ Missing radius field" -ForegroundColor Red
        $FAILED++
    }
} catch {
    Write-Host "  ✗ Failed: $_" -ForegroundColor Red
    $FAILED++
}

Write-Host "4. Testing GET /api/analytics/patterns/families" -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$API/api/analytics/patterns/families" -Method GET
    if ($response.usage) {
        Write-Host "  ✓ Strip family usage retrieved" -ForegroundColor Green
        Write-Host "    Families tracked: $($response.usage.Count)" -ForegroundColor Gray
        $PASSED++
    } else {
        Write-Host "  ✗ Missing usage field" -ForegroundColor Red
        $FAILED++
    }
} catch {
    Write-Host "  ✗ Failed: $_" -ForegroundColor Red
    $FAILED++
}

Write-Host "5. Testing GET /api/analytics/patterns/popularity?limit=5" -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$API/api/analytics/patterns/popularity?limit=5" -Method GET
    if ($response.top_patterns) {
        Write-Host "  ✓ Pattern popularity retrieved" -ForegroundColor Green
        Write-Host "    Top patterns: $($response.top_patterns.Count)" -ForegroundColor Gray
        $PASSED++
    } else {
        Write-Host "  ✗ Missing top_patterns field" -ForegroundColor Red
        $FAILED++
    }
} catch {
    Write-Host "  ✗ Failed: $_" -ForegroundColor Red
    $FAILED++
}

# ============================================================================
# MATERIAL ANALYTICS TESTS
# ============================================================================

Write-Host ""
Write-Host "=== Material Analytics ===" -ForegroundColor Yellow

Write-Host "6. Testing GET /api/analytics/materials/distribution" -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$API/api/analytics/materials/distribution" -Method GET
    if ($response.distribution) {
        Write-Host "  ✓ Material distribution retrieved" -ForegroundColor Green
        Write-Host "    Total materials: $($response.total_materials)" -ForegroundColor Gray
        Write-Host "    Materials: $($response.distribution.Keys -join ', ')" -ForegroundColor Gray
        $PASSED++
    } else {
        Write-Host "  ✗ Missing distribution field" -ForegroundColor Red
        $FAILED++
    }
} catch {
    Write-Host "  ✗ Failed: $_" -ForegroundColor Red
    $FAILED++
}

Write-Host "7. Testing GET /api/analytics/materials/consumption" -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$API/api/analytics/materials/consumption" -Method GET
    if ($response.by_material) {
        Write-Host "  ✓ Material consumption retrieved" -ForegroundColor Green
        Write-Host "    Materials tracked: $($response.by_material.Count)" -ForegroundColor Gray
        $PASSED++
    } else {
        Write-Host "  ✗ Missing by_material field" -ForegroundColor Red
        $FAILED++
    }
} catch {
    Write-Host "  ✗ Failed: $_" -ForegroundColor Red
    $FAILED++
}

Write-Host "8. Testing GET /api/analytics/materials/efficiency" -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$API/api/analytics/materials/efficiency" -Method GET
    if ($response.by_material) {
        Write-Host "  ✓ Material efficiency retrieved" -ForegroundColor Green
        Write-Host "    Efficiency data: $($response.by_material.Count) materials" -ForegroundColor Gray
        $PASSED++
    } else {
        Write-Host "  ✗ Missing by_material field" -ForegroundColor Red
        $FAILED++
    }
} catch {
    Write-Host "  ✗ Failed: $_" -ForegroundColor Red
    $FAILED++
}

Write-Host "9. Testing GET /api/analytics/materials/dimensions" -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$API/api/analytics/materials/dimensions" -Method GET
    if ($response.width) {
        Write-Host "  ✓ Dimensional analysis retrieved" -ForegroundColor Green
        Write-Host "    Width range: $($response.width.min_mm) - $($response.width.max_mm) mm" -ForegroundColor Gray
        $PASSED++
    } else {
        Write-Host "  ✗ Missing width field" -ForegroundColor Red
        $FAILED++
    }
} catch {
    Write-Host "  ✗ Failed: $_" -ForegroundColor Red
    $FAILED++
}

Write-Host "10. Testing GET /api/analytics/materials/suppliers" -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$API/api/analytics/materials/suppliers" -Method GET
    if ($response.suppliers) {
        Write-Host "  ✓ Supplier analytics retrieved" -ForegroundColor Green
        Write-Host "    Suppliers tracked: $($response.suppliers.Count)" -ForegroundColor Gray
        $PASSED++
    } else {
        Write-Host "  ✗ Missing suppliers field" -ForegroundColor Red
        $FAILED++
    }
} catch {
    Write-Host "  ✗ Failed: $_" -ForegroundColor Red
    $FAILED++
}

Write-Host "11. Testing GET /api/analytics/materials/inventory" -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$API/api/analytics/materials/inventory" -Method GET
    if ($null -ne $response.total_strips) {
        Write-Host "  ✓ Inventory status retrieved" -ForegroundColor Green
        Write-Host "    Total strips: $($response.total_strips)" -ForegroundColor Gray
        Write-Host "    Total length: $($response.total_length_mm) mm" -ForegroundColor Gray
        $PASSED++
    } else {
        Write-Host "  ✗ Missing total_strips field" -ForegroundColor Red
        $FAILED++
    }
} catch {
    Write-Host "  ✗ Failed: $_" -ForegroundColor Red
    $FAILED++
}

# ============================================================================
# JOB ANALYTICS TESTS
# ============================================================================

Write-Host ""
Write-Host "=== Job Analytics ===" -ForegroundColor Yellow

Write-Host "12. Testing GET /api/analytics/jobs/success-trends?days=30" -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$API/api/analytics/jobs/success-trends?days=30" -Method GET
    if ($response.daily_trends) {
        Write-Host "  ✓ Success trends retrieved" -ForegroundColor Green
        Write-Host "    Period: $($response.period_days) days" -ForegroundColor Gray
        Write-Host "    Overall success rate: $($response.overall_success_rate)%" -ForegroundColor Gray
        $PASSED++
    } else {
        Write-Host "  ✗ Missing daily_trends field" -ForegroundColor Red
        $FAILED++
    }
} catch {
    Write-Host "  ✗ Failed: $_" -ForegroundColor Red
    $FAILED++
}

Write-Host "13. Testing GET /api/analytics/jobs/duration" -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$API/api/analytics/jobs/duration" -Method GET
    if ($response.by_job_type) {
        Write-Host "  ✓ Duration analysis retrieved" -ForegroundColor Green
        Write-Host "    Job types: $($response.total_job_types)" -ForegroundColor Gray
        $PASSED++
    } else {
        Write-Host "  ✗ Missing by_job_type field" -ForegroundColor Red
        $FAILED++
    }
} catch {
    Write-Host "  ✗ Failed: $_" -ForegroundColor Red
    $FAILED++
}

Write-Host "14. Testing GET /api/analytics/jobs/status" -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$API/api/analytics/jobs/status" -Method GET
    if ($response.distribution) {
        Write-Host "  ✓ Status distribution retrieved" -ForegroundColor Green
        Write-Host "    Total jobs: $($response.total_jobs)" -ForegroundColor Gray
        Write-Host "    Statuses: $($response.distribution.Keys -join ', ')" -ForegroundColor Gray
        $PASSED++
    } else {
        Write-Host "  ✗ Missing distribution field" -ForegroundColor Red
        $FAILED++
    }
} catch {
    Write-Host "  ✗ Failed: $_" -ForegroundColor Red
    $FAILED++
}

Write-Host "15. Testing GET /api/analytics/jobs/throughput" -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$API/api/analytics/jobs/throughput" -Method GET
    if ($null -ne $response.avg_jobs_per_day) {
        Write-Host "  ✓ Throughput metrics retrieved" -ForegroundColor Green
        Write-Host "    Avg jobs/day: $($response.avg_jobs_per_day)" -ForegroundColor Gray
        Write-Host "    Avg jobs/week: $($response.avg_jobs_per_week)" -ForegroundColor Gray
        $PASSED++
    } else {
        Write-Host "  ✗ Missing avg_jobs_per_day field" -ForegroundColor Red
        $FAILED++
    }
} catch {
    Write-Host "  ✗ Failed: $_" -ForegroundColor Red
    $FAILED++
}

Write-Host "16. Testing GET /api/analytics/jobs/failures" -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$API/api/analytics/jobs/failures" -Method GET
    if ($response.by_job_type) {
        Write-Host "  ✓ Failure analysis retrieved" -ForegroundColor Green
        Write-Host "    Total failures: $($response.total_failures)" -ForegroundColor Gray
        $PASSED++
    } else {
        Write-Host "  ✗ Missing by_job_type field" -ForegroundColor Red
        $FAILED++
    }
} catch {
    Write-Host "  ✗ Failed: $_" -ForegroundColor Red
    $FAILED++
}

Write-Host "17. Testing GET /api/analytics/jobs/types" -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$API/api/analytics/jobs/types" -Method GET
    if ($response.distribution) {
        Write-Host "  ✓ Job type distribution retrieved" -ForegroundColor Green
        Write-Host "    Job types: $($response.job_type_count)" -ForegroundColor Gray
        $PASSED++
    } else {
        Write-Host "  ✗ Missing distribution field" -ForegroundColor Red
        $FAILED++
    }
} catch {
    Write-Host "  ✗ Failed: $_" -ForegroundColor Red
    $FAILED++
}

Write-Host "18. Testing GET /api/analytics/jobs/recent?limit=10" -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$API/api/analytics/jobs/recent?limit=10" -Method GET
    if ($response.recent_jobs) {
        Write-Host "  ✓ Recent jobs retrieved" -ForegroundColor Green
        Write-Host "    Jobs returned: $($response.count)" -ForegroundColor Gray
        $PASSED++
    } else {
        Write-Host "  ✗ Missing recent_jobs field" -ForegroundColor Red
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
    Write-Host "✓ All N9.0 Analytics Engine tests passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host ""
    Write-Host "✗ Some tests failed. Review output above." -ForegroundColor Red
    exit 1
}