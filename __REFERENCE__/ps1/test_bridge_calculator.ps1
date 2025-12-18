# Bridge Calculator Integration Smoke Test
# Tests API endpoints and end-to-end DXF export

$baseUrl = "http://localhost:8000"
$testsPassed = 0
$testsFailed = 0

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Endpoint,
        [hashtable]$Body,
        [string]$ExpectedContent,
        [string]$ResponseType = "json"
    )
    
    Write-Host "`n=== Test: $Name ===" -ForegroundColor Cyan
    
    try {
        $headers = @{ "Content-Type" = "application/json" }
        
        if ($Method -eq "POST") {
            if ($Body) {
                $bodyJson = $Body | ConvertTo-Json -Depth 10
                $response = Invoke-RestMethod -Uri "$baseUrl$Endpoint" -Method Post -Headers $headers -Body $bodyJson
            } else {
                $response = Invoke-RestMethod -Uri "$baseUrl$Endpoint" -Method Post -Headers $headers
            }
        } else {
            $response = Invoke-RestMethod -Uri "$baseUrl$Endpoint" -Method Get
        }
        
        # Check response content
        if ($ResponseType -eq "json") {
            $content = $response | ConvertTo-Json
        } else {
            $content = $response
        }
        
        if ($ExpectedContent -and ($content -match $ExpectedContent)) {
            Write-Host "  ✓ PASSED" -ForegroundColor Green
            Write-Host "    - Found expected: $ExpectedContent" -ForegroundColor Gray
            $script:testsPassed++
            return $true
        } elseif (-not $ExpectedContent) {
            Write-Host "  ✓ PASSED" -ForegroundColor Green
            $script:testsPassed++
            return $true
        } else {
            Write-Host "  ✗ FAILED: Expected content not found" -ForegroundColor Red
            Write-Host "    - Looking for: $ExpectedContent" -ForegroundColor Yellow
            Write-Host "    - Got: $($content.Substring(0, [Math]::Min(200, $content.Length)))..." -ForegroundColor Yellow
            $script:testsFailed++
            return $false
        }
    }
    catch {
        Write-Host "  ✗ FAILED: $($_.Exception.Message)" -ForegroundColor Red
        $script:testsFailed++
        return $false
    }
}

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Bridge Calculator Integration Smoke Test                ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

# Test 1: Health Check
Test-Endpoint `
    -Name "Bridge Calculator Health Check" `
    -Method "GET" `
    -Endpoint "/cam/bridge/health" `
    -ExpectedContent "bridge_calculator" `
    -ResponseType "json"

# Test 2: Get Presets
Test-Endpoint `
    -Name "Get Bridge Presets" `
    -Method "GET" `
    -Endpoint "/cam/bridge/presets" `
    -ExpectedContent "families" `
    -ResponseType "json"

# Test 3: Export DXF (Strat/Tele 25.5" in inches)
Write-Host "`n=== Test: Export DXF (Strat/Tele 25.5`" inch) ===" -ForegroundColor Cyan
try {
    $bridgeGeometry = @{
        geometry = @{
            units = "in"
            scaleLength = 25.5
            stringSpread = 2.067
            compTreble = 0.079
            compBass = 0.138
            slotWidth = 0.118
            slotLength = 2.953
            angleDeg = 1.636
            endpoints = @{
                treble = @{ x = 25.579; y = -1.034 }
                bass = @{ x = 25.638; y = 1.034 }
            }
            slotPolygon = @(
                @{ x = 24.011; y = -1.093 }
                @{ x = 27.206; y = -0.974 }
                @{ x = 27.206; y = 0.974 }
                @{ x = 24.011; y = 1.093 }
            )
        }
        filename = "test_strat_bridge"
    } | ConvertTo-Json -Depth 10
    
    $response = Invoke-WebRequest -Uri "$baseUrl/cam/bridge/export_dxf" -Method Post -Headers @{ "Content-Type" = "application/json" } -Body $bridgeGeometry
    
    if ($response.StatusCode -eq 200 -and $response.Headers.'Content-Type' -match 'dxf') {
        $dxfContent = [System.Text.Encoding]::UTF8.GetString($response.Content)
        
        # Verify DXF structure
        $hasSaddleLine = $dxfContent -match 'SADDLE_LINE'
        $hasSlotRect = $dxfContent -match 'SLOT_RECTANGLE'
        $hasAC1009 = $dxfContent -match 'AC1009'  # R12 format
        
        if ($hasSaddleLine -and $hasSlotRect -and $hasAC1009) {
            Write-Host "  ✓ PASSED" -ForegroundColor Green
            Write-Host "    - DXF file generated ($(($response.Content.Length / 1024).ToString('F2')) KB)" -ForegroundColor Gray
            Write-Host "    - Contains SADDLE_LINE layer: ✓" -ForegroundColor Gray
            Write-Host "    - Contains SLOT_RECTANGLE layer: ✓" -ForegroundColor Gray
            Write-Host "    - R12 format (AC1009): ✓" -ForegroundColor Gray
            $script:testsPassed++
        } else {
            Write-Host "  ✗ FAILED: DXF structure incomplete" -ForegroundColor Red
            Write-Host "    - SADDLE_LINE: $hasSaddleLine" -ForegroundColor Yellow
            Write-Host "    - SLOT_RECTANGLE: $hasSlotRect" -ForegroundColor Yellow
            Write-Host "    - AC1009 (R12): $hasAC1009" -ForegroundColor Yellow
            $script:testsFailed++
        }
    } else {
        Write-Host "  ✗ FAILED: Response not DXF" -ForegroundColor Red
        $script:testsFailed++
    }
}
catch {
    Write-Host "  ✗ FAILED: $($_.Exception.Message)" -ForegroundColor Red
    $script:testsFailed++
}

# Test 4: Export DXF (OM Acoustic in mm)
Write-Host "`n=== Test: Export DXF (OM Acoustic 25.4`" mm) ===" -ForegroundColor Cyan
try {
    $bridgeGeometry = @{
        geometry = @{
            units = "mm"
            scaleLength = 645.16
            stringSpread = 52.5
            compTreble = 2.0
            compBass = 3.5
            slotWidth = 3.0
            slotLength = 75.0
            angleDeg = 1.636
            endpoints = @{
                treble = @{ x = 647.16; y = -26.25 }
                bass = @{ x = 648.66; y = 26.25 }
            }
            slotPolygon = @(
                @{ x = 609.91; y = -27.75 }
                @{ x = 684.91; y = -24.75 }
                @{ x = 684.91; y = 24.75 }
                @{ x = 609.91; y = 27.75 }
            )
        }
    } | ConvertTo-Json -Depth 10
    
    $response = Invoke-WebRequest -Uri "$baseUrl/cam/bridge/export_dxf" -Method Post -Headers @{ "Content-Type" = "application/json" } -Body $bridgeGeometry
    
    if ($response.StatusCode -eq 200) {
        $dxfContent = [System.Text.Encoding]::UTF8.GetString($response.Content)
        $hasUnits = $dxfContent -match 'mm' -or $dxfContent -match '645'
        
        if ($hasUnits) {
            Write-Host "  ✓ PASSED" -ForegroundColor Green
            Write-Host "    - DXF file generated ($(($response.Content.Length / 1024).ToString('F2')) KB)" -ForegroundColor Gray
            $script:testsPassed++
        } else {
            Write-Host "  ✗ FAILED: Units not found in DXF" -ForegroundColor Red
            $script:testsFailed++
        }
    }
}
catch {
    Write-Host "  ✗ FAILED: $($_.Exception.Message)" -ForegroundColor Red
    $script:testsFailed++
}

# Summary
Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Test Summary                                             ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host "  Total Tests: $($testsPassed + $testsFailed)" -ForegroundColor White
Write-Host "  Passed:      $testsPassed" -ForegroundColor Green
Write-Host "  Failed:      $testsFailed" -ForegroundColor $(if ($testsFailed -eq 0) { "Green" } else { "Red" })

if ($testsFailed -eq 0) {
    Write-Host "`n✓ All Bridge Calculator tests passed!" -ForegroundColor Green
    Write-Host "  - Health check: ✓" -ForegroundColor Gray
    Write-Host "  - Presets API: ✓" -ForegroundColor Gray
    Write-Host "  - DXF export (inch): ✓" -ForegroundColor Gray
    Write-Host "  - DXF export (mm): ✓" -ForegroundColor Gray
    Write-Host "`nBridge Calculator integration is production-ready!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n✗ Some tests failed. Check output above for details." -ForegroundColor Red
    Write-Host "  Ensure backend is running: uvicorn app.main:app --reload --port 8000" -ForegroundColor Yellow
    exit 1
}
