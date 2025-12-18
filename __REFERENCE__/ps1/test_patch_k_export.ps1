# Patch K Export Enhancement – Local Test Script
# Run this script to verify all endpoints work correctly

Write-Host "🧪 Patch K Export Enhancement Test Suite" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$API_BASE = "http://localhost:8000"
$PROXY_BASE = "http://localhost:8088/api"

# Test data
$geometry = @{
    units = "mm"
    paths = @(
        @{
            type = "line"
            x1 = 0
            y1 = 0
            x2 = 60
            y2 = 0
        },
        @{
            type = "arc"
            cx = 30
            cy = 20
            r = 20
            start = 180
            end = 0
            cw = $false
        }
    )
} | ConvertTo-Json -Depth 10 -Compress

$gcode = "G21 G90 G17 F1200`nG0 Z5`nG0 X0 Y0`nG1 Z-1 F300`nG1 X60 Y0`nG3 X60 Y40 I0 J20`nG3 X0 Y40 I-30 J0`nG3 X0 Y0 I0 J-20`nG0 Z5`n"

# Helper function
function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Body,
        [string]$ExpectedPattern,
        [string]$OutputFile
    )
    
    Write-Host "Testing: $Name" -ForegroundColor Yellow
    
    try {
        if ($OutputFile) {
            Invoke-RestMethod -Uri $Url -Method POST -ContentType "application/json" -Body $Body -OutFile $OutputFile
            $content = Get-Content $OutputFile -Raw
            if ($content -match $ExpectedPattern) {
                Write-Host "  ✅ PASS: Output saved to $OutputFile" -ForegroundColor Green
                return $true
            } else {
                Write-Host "  ❌ FAIL: Pattern not found in output" -ForegroundColor Red
                return $false
            }
        } else {
            $response = Invoke-RestMethod -Uri $Url -Method POST -ContentType "application/json" -Body $Body
            $responseJson = $response | ConvertTo-Json -Depth 10
            if ($responseJson -match $ExpectedPattern) {
                Write-Host "  ✅ PASS: $responseJson" -ForegroundColor Green
                return $true
            } else {
                Write-Host "  ❌ FAIL: Expected pattern not found" -ForegroundColor Red
                Write-Host "  Response: $responseJson" -ForegroundColor Gray
                return $false
            }
        }
    } catch {
        Write-Host "  ❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Check if API is running
Write-Host "Checking API availability..." -ForegroundColor Cyan
try {
    $health = Invoke-RestMethod -Uri "$API_BASE/health"
    if ($health.ok) {
        Write-Host "✅ API is running at $API_BASE" -ForegroundColor Green
    } else {
        Write-Host "❌ API health check failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ API is not running. Start with: uvicorn services.api.app.main:app --reload" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Running Tests..." -ForegroundColor Cyan
Write-Host "=================" -ForegroundColor Cyan
Write-Host ""

$results = @()

# Test 1: Import JSON
$importBody = @{
    geometry = @{
        units = "mm"
        paths = @(
            @{
                type = "line"
                x1 = 0
                y1 = 0
                x2 = 60
                y2 = 0
            }
        )
    }
} | ConvertTo-Json -Depth 10
$results += Test-Endpoint -Name "1. Import JSON Geometry" -Url "$API_BASE/geometry/import" -Body $importBody -ExpectedPattern "units.*mm"

# Test 2: Parity Check
$parityBody = @{
    geometry = @{
        units = "mm"
        paths = @(
            @{
                type = "line"
                x1 = 0
                y1 = 0
                x2 = 60
                y2 = 0
            }
        )
    }
    gcode = "G21 G90`nG0 X0 Y0`nG1 X60 Y0`n"
    tolerance_mm = 0.1
} | ConvertTo-Json -Depth 10
$results += Test-Endpoint -Name "2. Parity Check" -Url "$API_BASE/geometry/parity" -Body $parityBody -ExpectedPattern "rms_error_mm"

# Test 3: Export DXF
$exportBody = @{
    geometry = @{
        units = "mm"
        paths = @(
            @{
                type = "line"
                x1 = 0
                y1 = 0
                x2 = 60
                y2 = 0
            }
        )
    }
} | ConvertTo-Json -Depth 10
$results += Test-Endpoint -Name "3. Export DXF" -Url "$API_BASE/geometry/export?fmt=dxf" -Body $exportBody -ExpectedPattern "0\nSECTION" -OutputFile "test_export.dxf"

# Test 4: Export SVG
$results += Test-Endpoint -Name "4. Export SVG" -Url "$API_BASE/geometry/export?fmt=svg" -Body $exportBody -ExpectedPattern "<svg" -OutputFile "test_export.svg"

# Test 5: Export G-code
$gcodeBody = @{
    gcode = "G21`nG90`nM30`n"
} | ConvertTo-Json -Depth 10
$results += Test-Endpoint -Name "5. Export G-code" -Url "$API_BASE/geometry/export_gcode" -Body $gcodeBody -ExpectedPattern "G21" -OutputFile "test_program.nc"

# Summary
Write-Host ""
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "============" -ForegroundColor Cyan
$passed = ($results | Where-Object { $_ -eq $true }).Count
$total = $results.Count
$percentage = [math]::Round(($passed / $total) * 100, 1)

Write-Host "Passed: $passed / $total ($percentage%)" -ForegroundColor $(if ($passed -eq $total) { "Green" } else { "Yellow" })

if ($passed -eq $total) {
    Write-Host ""
    Write-Host "🎉 All tests passed! Export enhancement is working correctly." -ForegroundColor Green
    Write-Host ""
    Write-Host "Generated Files:" -ForegroundColor Cyan
    Write-Host "  - test_export.dxf (DXF R12 format)" -ForegroundColor Gray
    Write-Host "  - test_export.svg (SVG markup)" -ForegroundColor Gray
    Write-Host "  - test_program.nc (G-code file)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "  1. Open test_export.svg in browser to verify" -ForegroundColor Gray
    Write-Host "  2. Import test_export.dxf in CAD software" -ForegroundColor Gray
    Write-Host "  3. Push to GitHub and verify CI passes" -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "⚠️  Some tests failed. Check output above for details." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Test script complete." -ForegroundColor Cyan
