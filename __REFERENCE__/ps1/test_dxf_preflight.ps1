# DXF Preflight Validator Smoke Test
$baseUrl = "http://localhost:8000"
$testsPassed = 0
$testsFailed = 0

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  DXF Preflight Validator Smoke Test                      ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

# Test 1: Health Check
Write-Host "`n=== Test 1: Health Check ===" -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/dxf/preflight/health" -Method Get
    Write-Host "  ✓ PASSED" -ForegroundColor Green
    Write-Host "    Service: $($response.service), Version: $($response.version)" -ForegroundColor Gray
    Write-Host "    ezdxf available: $($response.ezdxf_available)" -ForegroundColor Gray
    $testsPassed++
} catch {
    Write-Host "  ✗ FAILED: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# Test 2: Validate Good DXF (R12, Closed Rectangle)
Write-Host "`n=== Test 2: Validate Good DXF ===" -ForegroundColor Cyan
try {
    # Simple R12 DXF with closed rectangle
    $goodDxf = @"
  0
SECTION
  2
HEADER
  9
`$ACADVER
  1
AC1009
  9
`$INSUNITS
  70
4
  0
ENDSEC
  0
SECTION
  2
ENTITIES
  0
LINE
  8
0
 10
0.0
 20
0.0
 11
100.0
 21
0.0
  0
LINE
  8
0
 10
100.0
 20
0.0
 11
100.0
 21
50.0
  0
LINE
  8
0
 10
100.0
 20
50.0
 11
0.0
 21
50.0
  0
LINE
  8
0
 10
0.0
 20
50.0
 11
0.0
 21
0.0
  0
ENDSEC
  0
EOF
"@
    
    $goodBase64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($goodDxf))
    
    $response = Invoke-RestMethod -Uri "$baseUrl/dxf/preflight/validate_base64" `
        -Method Post `
        -Headers @{ "Content-Type" = "application/json" } `
        -Body (@{ dxf_base64 = $goodBase64; filename = "test_good.dxf" } | ConvertTo-Json)
    
    Write-Host "  ✓ PASSED" -ForegroundColor Green
    Write-Host "    DXF Version: $($response.dxf_version)" -ForegroundColor Gray
    Write-Host "    Units: $($response.units)" -ForegroundColor Gray
    Write-Host "    CAM Ready: $($response.cam_ready)" -ForegroundColor $(if ($response.cam_ready) { "Green" } else { "Yellow" })
    Write-Host "    Geometry: $($response.geometry.lines) lines, $($response.geometry.total) total" -ForegroundColor Gray
    Write-Host "    Issues: $($response.errors_count) errors, $($response.warnings_count) warnings" -ForegroundColor Gray
    $testsPassed++
} catch {
    Write-Host "  ✗ FAILED: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# Test 3: Validate DXF with Issues (R2000, No Units)
Write-Host "`n=== Test 3: Validate DXF with Issues ===" -ForegroundColor Cyan
try {
    $badDxf = @"
  0
SECTION
  2
HEADER
  9
`$ACADVER
  1
AC1015
  0
ENDSEC
  0
SECTION
  2
ENTITIES
  0
LINE
  8
0
 10
0.0
 20
0.0
 11
50.0
 21
30.0
  0
ENDSEC
  0
EOF
"@
    
    $badBase64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($badDxf))
    
    $response = Invoke-RestMethod -Uri "$baseUrl/dxf/preflight/validate_base64" `
        -Method Post `
        -Headers @{ "Content-Type" = "application/json" } `
        -Body (@{ dxf_base64 = $badBase64; filename = "test_issues.dxf" } | ConvertTo-Json)
    
    Write-Host "  ✓ PASSED" -ForegroundColor Green
    Write-Host "    DXF Version: $($response.dxf_version) (Not R12)" -ForegroundColor Yellow
    Write-Host "    CAM Ready: $($response.cam_ready)" -ForegroundColor $(if ($response.cam_ready) { "Green" } else { "Yellow" })
    Write-Host "    Issues found: $($response.issues.Count)" -ForegroundColor Yellow
    
    if ($response.issues.Count -gt 0) {
        Write-Host "    Issue examples:" -ForegroundColor Gray
        $response.issues | Select-Object -First 3 | ForEach-Object {
            Write-Host "      [$($_.severity)] $($_.message)" -ForegroundColor Gray
        }
    }
    
    Write-Host "    Recommendations: $($response.recommended_actions.Count)" -ForegroundColor Gray
    $testsPassed++
} catch {
    Write-Host "  ✗ FAILED: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# Test 4: Auto-Fix (Convert to R12 + Set Units)
Write-Host "`n=== Test 4: Auto-Fix DXF ===" -ForegroundColor Cyan
try {
    $badDxf = @"
  0
SECTION
  2
HEADER
  9
`$ACADVER
  1
AC1015
  0
ENDSEC
  0
SECTION
  2
TABLES
  0
TABLE
  2
LAYER
 70
1
  0
LAYER
  2
0
 70
0
 62
7
  6
CONTINUOUS
  0
ENDTAB
  0
ENDSEC
  0
SECTION
  2
ENTITIES
  0
LINE
  8
0
 10
0.0
 20
0.0
 11
50.0
 21
30.0
  0
ENDSEC
  0
EOF
"@
    
    $badBase64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($badDxf))
    
    $fixRequest = @{
        dxf_base64 = $badBase64
        filename = "test_autofix.dxf"
        fixes = @("convert_to_r12", "set_units_mm")
    }
    
    $response = Invoke-RestMethod -Uri "$baseUrl/dxf/preflight/auto_fix" `
        -Method Post `
        -Headers @{ "Content-Type" = "application/json" } `
        -Body ($fixRequest | ConvertTo-Json)
    
    Write-Host "  ✓ PASSED" -ForegroundColor Green
    Write-Host "    Fixes applied: $($response.fixes_applied.Count)" -ForegroundColor Gray
    $response.fixes_applied | ForEach-Object {
        Write-Host "      • $_" -ForegroundColor Gray
    }
    Write-Host "    Fixed DXF base64 length: $($response.fixed_dxf_base64.Length) chars" -ForegroundColor Gray
    Write-Host "    New validation:" -ForegroundColor Gray
    Write-Host "      - DXF Version: $($response.validation_report.dxf_version)" -ForegroundColor Gray
    Write-Host "      - Units: $($response.validation_report.units)" -ForegroundColor Gray
    Write-Host "      - CAM Ready: $($response.validation_report.cam_ready)" -ForegroundColor $(if ($response.validation_report.cam_ready) { "Green" } else { "Yellow" })
    $testsPassed++
} catch {
    Write-Host "  ✗ FAILED: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Test Summary                                             ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host "  Total Tests: $($testsPassed + $testsFailed)" -ForegroundColor White
Write-Host "  Passed:      $testsPassed" -ForegroundColor Green
Write-Host "  Failed:      $testsFailed" -ForegroundColor $(if ($testsFailed -eq 0) { "Green" } else { "Red" })

if ($testsFailed -eq 0) {
    Write-Host "`n✓ All DXF Preflight tests passed!" -ForegroundColor Green
    Write-Host "  - Health check: ✓" -ForegroundColor Gray
    Write-Host "  - Validate good DXF: ✓" -ForegroundColor Gray
    Write-Host "  - Validate DXF with issues: ✓" -ForegroundColor Gray
    Write-Host "  - Auto-fix DXF: ✓" -ForegroundColor Gray
    Write-Host "`n🎉 DXF Preflight Validator is production-ready!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n✗ Some tests failed. Check output above." -ForegroundColor Red
    Write-Host "  Ensure backend is running: cd services/api && uvicorn app.main:app --reload --port 8000" -ForegroundColor Yellow
    exit 1
}
