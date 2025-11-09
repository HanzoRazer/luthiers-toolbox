# Test OM Module Integration
# Tests all OM acoustic guitar template endpoints

$API_URL = "http://localhost:8000"
$passed = 0
$failed = 0

Write-Host "`n=== Testing OM Module Integration ===" -ForegroundColor Cyan

# Test 1: Health Check
Write-Host "`n1. Testing GET /cam/om/health" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$API_URL/cam/om/health" -Method Get
    if ($response.ok -eq $true -and $response.module -eq "om") {
        Write-Host "  ✓ Health check passed" -ForegroundColor Green
        Write-Host "    Templates: $($response.templates_available)" -ForegroundColor Gray
        Write-Host "    Graduation Maps: $($response.graduation_maps_available)" -ForegroundColor Gray
        Write-Host "    Kits: $($response.kits_available)" -ForegroundColor Gray
        $passed++
    } else {
        Write-Host "  ✗ Health check failed" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ✗ Error: $_" -ForegroundColor Red
    $failed++
}

# Test 2: List Templates
Write-Host "`n2. Testing GET /cam/om/templates" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$API_URL/cam/om/templates" -Method Get
    if ($response -is [Array] -and $response.Count -gt 0) {
        Write-Host "  ✓ Templates listed: $($response.Count) found" -ForegroundColor Green
        $response | ForEach-Object {
            Write-Host "    - $($_.name) ($($_.type), $($_.format))" -ForegroundColor Gray
        }
        $passed++
    } else {
        Write-Host "  ✗ No templates found" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ✗ Error: $_" -ForegroundColor Red
    $failed++
}

# Test 3: Get Specs
Write-Host "`n3. Testing GET /cam/om/specs" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$API_URL/cam/om/specs" -Method Get
    if ($response.model -eq "OM (Orchestra Model)") {
        Write-Host "  ✓ Specs retrieved successfully" -ForegroundColor Green
        Write-Host "    Model: $($response.model)" -ForegroundColor Gray
        Write-Host "    Scale: $($response.scale_length_mm)mm ($($response.scale_length_inches)\")" -ForegroundColor Gray
        Write-Host "    Nut Width: $($response.nut_width_mm)mm" -ForegroundColor Gray
        Write-Host "    End Width: $($response.end_width_mm)mm" -ForegroundColor Gray
        $passed++
    } else {
        Write-Host "  ✗ Invalid specs data" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ✗ Error: $_" -ForegroundColor Red
    $failed++
}

# Test 4: List Graduation Maps
Write-Host "`n4. Testing GET /cam/om/graduation-maps" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$API_URL/cam/om/graduation-maps" -Method Get
    if ($response -is [Array] -and $response.Count -gt 0) {
        Write-Host "  ✓ Graduation maps listed: $($response.Count) found" -ForegroundColor Green
        $response | ForEach-Object {
            $gridStr = if ($_.grid) { "grid" } else { "plain" }
            Write-Host "    - $($_.name) ($($_.surface), $($_.format), $gridStr)" -ForegroundColor Gray
        }
        $passed++
    } else {
        Write-Host "  ✗ No graduation maps found" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ✗ Error: $_" -ForegroundColor Red
    $failed++
}

# Test 5: List Kits
Write-Host "`n5. Testing GET /cam/om/kits" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$API_URL/cam/om/kits" -Method Get
    if ($response -is [Array] -and $response.Count -gt 0) {
        Write-Host "  ✓ Kits listed: $($response.Count) found" -ForegroundColor Green
        $response | ForEach-Object {
            $zipStr = if ($_.zip_available) { "ZIP available" } else { "No ZIP" }
            Write-Host "    - $($_.name) ($zipStr)" -ForegroundColor Gray
            Write-Host "      Files: $($_.files.Count)" -ForegroundColor Gray
        }
        $passed++
    } else {
        Write-Host "  ✗ No kits found" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ✗ Error: $_" -ForegroundColor Red
    $failed++
}

# Test 6: List Resources
Write-Host "`n6. Testing GET /cam/om/resources" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$API_URL/cam/om/resources" -Method Get
    if ($response -is [Array] -and $response.Count -gt 0) {
        Write-Host "  ✓ Resources listed: $($response.Count) found" -ForegroundColor Green
        $response | ForEach-Object {
            Write-Host "    - $($_.name) ($($_.type), $($_.category))" -ForegroundColor Gray
        }
        $passed++
    } else {
        Write-Host "  ✗ No resources found" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ✗ Error: $_" -ForegroundColor Red
    $failed++
}

# Test 7: Download Template (outline)
Write-Host "`n7. Testing GET /cam/om/templates/outline/download" -ForegroundColor Yellow
try {
    $outFile = "$env:TEMP\om_outline_test.dxf"
    Invoke-WebRequest -Uri "$API_URL/cam/om/templates/outline/download" -OutFile $outFile
    if (Test-Path $outFile) {
        $size = (Get-Item $outFile).Length
        Write-Host "  ✓ Outline template downloaded ($size bytes)" -ForegroundColor Green
        Remove-Item $outFile -ErrorAction SilentlyContinue
        $passed++
    } else {
        Write-Host "  ✗ Download failed" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ✗ Error: $_" -ForegroundColor Red
    $failed++
}

# Test 8: Download Graduation Map (top, svg, grid)
Write-Host "`n8. Testing GET /cam/om/graduation-maps/top/svg/download?grid=true" -ForegroundColor Yellow
try {
    $outFile = "$env:TEMP\om_top_grad_test.svg"
    Invoke-WebRequest -Uri "$API_URL/cam/om/graduation-maps/top/svg/download?grid=true" -OutFile $outFile
    if (Test-Path $outFile) {
        $size = (Get-Item $outFile).Length
        Write-Host "  ✓ Top graduation map downloaded ($size bytes)" -ForegroundColor Green
        Remove-Item $outFile -ErrorAction SilentlyContinue
        $passed++
    } else {
        Write-Host "  ✗ Download failed" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ✗ Error: $_" -ForegroundColor Red
    $failed++
}

# Summary
Write-Host "`n=== Test Summary ===" -ForegroundColor Cyan
Write-Host "  Passed: $passed" -ForegroundColor Green
Write-Host "  Failed: $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })

if ($failed -eq 0) {
    Write-Host "`n✓ All OM module tests passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n✗ Some tests failed" -ForegroundColor Red
    exit 1
}
