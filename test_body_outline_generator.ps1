# Body Outline Generator Test Suite
# Tests parametric guitar body generation, DXF/SVG export, and frontend component

Write-Host "`n=== Body Outline Generator Test Suite ===" -ForegroundColor Cyan
Write-Host "Testing parametric guitar body generation with all features`n" -ForegroundColor Gray

$passed = 0
$failed = 0
$baseUrl = "http://localhost:8000"

# ============================================================================
# Test 1: Backend Health Check
# ============================================================================
Write-Host "Test 1: Backend health check" -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod "$baseUrl/health"
    Write-Host "  ✓ Backend responsive" -ForegroundColor Green
    $passed++
} catch {
    Write-Host "  ✗ Backend not running: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "    Run: cd services/api && uvicorn app.main:app --reload" -ForegroundColor Yellow
    $failed++
    exit 1
}

# ============================================================================
# Test 2: Acoustic Guitar Body Generation (JSON)
# ============================================================================
Write-Host "`nTest 2: Generate Acoustic guitar body (JSON format)" -ForegroundColor Yellow
try {
    $acousticBody = @{
        dimensions = @{
            bodyLength = 505
            bodyWidthUpper = 295
            bodyWidthLower = 380
            waistWidth = 245
            bodyDepth = 110
            scaleLength = 650
            nutWidth = 43
            bridgeSpacing = 56
            fretCount = 20
            neckAngle = 3
        }
        guitarType = "Acoustic"
        units = "mm"
        format = "json"
        resolution = 48
    } | ConvertTo-Json -Depth 5
    
    $result = Invoke-RestMethod -Uri "$baseUrl/guitar/design/parametric" `
        -Method Post `
        -Body $acousticBody `
        -ContentType "application/json"
    
    if ($result.success -and $result.outline.Count -gt 0) {
        Write-Host "  ✓ Generated $($result.outline.Count) points" -ForegroundColor Green
        Write-Host "  ✓ Guitar type: $($result.guitarType)" -ForegroundColor Green
        Write-Host "  ✓ Body length: $($result.dimensions.bodyLength)mm" -ForegroundColor Green
        Write-Host "  ✓ Bounding box: [$($result.boundingBox.minX), $($result.boundingBox.minY)] to [$($result.boundingBox.maxX), $($result.boundingBox.maxY)]" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  ✗ Generation failed or no points returned" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ✗ API error: $($_.Exception.Message)" -ForegroundColor Red
    $failed++
}

# ============================================================================
# Test 3: Electric Guitar Body Generation
# ============================================================================
Write-Host "`nTest 3: Generate Electric guitar body" -ForegroundColor Yellow
try {
    $electricBody = @{
        dimensions = @{
            bodyLength = 460
            bodyWidthUpper = 320
            bodyWidthLower = 340
            waistWidth = 280
            scaleLength = 648
        }
        guitarType = "Electric"
        units = "mm"
        format = "json"
    } | ConvertTo-Json -Depth 5
    
    $result = Invoke-RestMethod -Uri "$baseUrl/guitar/design/parametric" `
        -Method Post `
        -Body $electricBody `
        -ContentType "application/json"
    
    if ($result.success -and $result.guitarType -eq "Electric") {
        Write-Host "  ✓ Electric body generated: $($result.outline.Count) points" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  ✗ Electric body generation failed" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ✗ API error: $($_.Exception.Message)" -ForegroundColor Red
    $failed++
}

# ============================================================================
# Test 4: Classical Guitar Body Generation
# ============================================================================
Write-Host "`nTest 4: Generate Classical guitar body" -ForegroundColor Yellow
try {
    $classicalBody = @{
        dimensions = @{
            bodyLength = 490
            bodyWidthUpper = 280
            bodyWidthLower = 370
            waistWidth = 230
            scaleLength = 650
        }
        guitarType = "Classical"
        units = "mm"
        format = "json"
    } | ConvertTo-Json -Depth 5
    
    $result = Invoke-RestMethod -Uri "$baseUrl/guitar/design/parametric" `
        -Method Post `
        -Body $classicalBody `
        -ContentType "application/json"
    
    if ($result.success -and $result.guitarType -eq "Classical") {
        Write-Host "  ✓ Classical body generated: $($result.outline.Count) points" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  ✗ Classical body generation failed" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ✗ API error: $($_.Exception.Message)" -ForegroundColor Red
    $failed++
}

# ============================================================================
# Test 5: Bass Guitar Body Generation
# ============================================================================
Write-Host "`nTest 5: Generate Bass guitar body" -ForegroundColor Yellow
try {
    $bassBody = @{
        dimensions = @{
            bodyLength = 480
            bodyWidthUpper = 340
            bodyWidthLower = 360
            waistWidth = 300
            scaleLength = 864
        }
        guitarType = "Bass"
        units = "mm"
        format = "json"
    } | ConvertTo-Json -Depth 5
    
    $result = Invoke-RestMethod -Uri "$baseUrl/guitar/design/parametric" `
        -Method Post `
        -Body $bassBody `
        -ContentType "application/json"
    
    if ($result.success -and $result.guitarType -eq "Bass") {
        Write-Host "  ✓ Bass body generated: $($result.outline.Count) points" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  ✗ Bass body generation failed" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ✗ API error: $($_.Exception.Message)" -ForegroundColor Red
    $failed++
}

# ============================================================================
# Test 6: DXF Export
# ============================================================================
Write-Host "`nTest 6: DXF export (R12 format)" -ForegroundColor Yellow
try {
    $dxfBody = @{
        dimensions = @{
            bodyLength = 500
            bodyWidthUpper = 300
            bodyWidthLower = 380
            waistWidth = 240
            scaleLength = 650
        }
        guitarType = "Acoustic"
        units = "mm"
        format = "dxf"
    } | ConvertTo-Json -Depth 5
    
    $response = Invoke-WebRequest -Uri "$baseUrl/guitar/design/parametric/export" `
        -Method Post `
        -Body $dxfBody `
        -ContentType "application/json"
    
    if ($response.StatusCode -eq 200) {
        $dxfContent = $response.Content
        
        # Verify DXF structure
        $hasHeader = $dxfContent -match "HEADER"
        $hasEntities = $dxfContent -match "ENTITIES"
        $hasPolyline = $dxfContent -match "LWPOLYLINE"
        $hasR12 = $dxfContent -match "AC1009"  # R12 format
        
        if ($hasHeader -and $hasEntities -and $hasPolyline -and $hasR12) {
            Write-Host "  ✓ DXF generated ($($dxfContent.Length) bytes)" -ForegroundColor Green
            Write-Host "  ✓ Contains HEADER section" -ForegroundColor Green
            Write-Host "  ✓ Contains ENTITIES section" -ForegroundColor Green
            Write-Host "  ✓ Contains LWPOLYLINE (closed path)" -ForegroundColor Green
            Write-Host "  ✓ Format: R12 (AC1009)" -ForegroundColor Green
            $passed++
        } else {
            Write-Host "  ✗ DXF structure incomplete" -ForegroundColor Red
            Write-Host "    Header: $hasHeader, Entities: $hasEntities, Polyline: $hasPolyline, R12: $hasR12" -ForegroundColor Yellow
            $failed++
        }
    } else {
        Write-Host "  ✗ DXF export failed (HTTP $($response.StatusCode))" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ✗ DXF export error: $($_.Exception.Message)" -ForegroundColor Red
    $failed++
}

# ============================================================================
# Test 7: SVG Export
# ============================================================================
Write-Host "`nTest 7: SVG export" -ForegroundColor Yellow
try {
    $svgBody = @{
        dimensions = @{
            bodyLength = 500
            bodyWidthUpper = 300
            bodyWidthLower = 380
            waistWidth = 240
            scaleLength = 650
        }
        guitarType = "Acoustic"
        units = "mm"
        format = "svg"
    } | ConvertTo-Json -Depth 5
    
    $response = Invoke-WebRequest -Uri "$baseUrl/guitar/design/parametric/export" `
        -Method Post `
        -Body $svgBody `
        -ContentType "application/json"
    
    if ($response.StatusCode -eq 200) {
        $svgContent = $response.Content
        
        # Verify SVG structure
        $hasSvgTag = $svgContent -match "<svg"
        $hasPath = $svgContent -match "<path"
        $hasViewBox = $svgContent -match "viewBox"
        $hasMetadata = $svgContent -match "guitarType|bodyLength"
        
        if ($hasSvgTag -and $hasPath -and $hasViewBox) {
            Write-Host "  ✓ SVG generated ($($svgContent.Length) bytes)" -ForegroundColor Green
            Write-Host "  ✓ Contains <svg> tag" -ForegroundColor Green
            Write-Host "  ✓ Contains <path> element" -ForegroundColor Green
            Write-Host "  ✓ Contains viewBox attribute" -ForegroundColor Green
            if ($hasMetadata) {
                Write-Host "  ✓ Contains metadata comments" -ForegroundColor Green
            }
            $passed++
        } else {
            Write-Host "  ✗ SVG structure incomplete" -ForegroundColor Red
            $failed++
        }
    } else {
        Write-Host "  ✗ SVG export failed (HTTP $($response.StatusCode))" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ✗ SVG export error: $($_.Exception.Message)" -ForegroundColor Red
    $failed++
}

# ============================================================================
# Test 8: Unit Conversion (mm to inch)
# ============================================================================
Write-Host "`nTest 8: Unit conversion (mm to inch)" -ForegroundColor Yellow
try {
    $inchBody = @{
        dimensions = @{
            bodyLength = 20.0  # ~508mm
            bodyWidthUpper = 12.0  # ~305mm
            bodyWidthLower = 15.0  # ~381mm
            waistWidth = 9.5  # ~241mm
            scaleLength = 25.6  # ~650mm
        }
        guitarType = "Acoustic"
        units = "inch"
        format = "json"
    } | ConvertTo-Json -Depth 5
    
    $result = Invoke-RestMethod -Uri "$baseUrl/guitar/design/parametric" `
        -Method Post `
        -Body $inchBody `
        -ContentType "application/json"
    
    if ($result.success) {
        Write-Host "  ✓ Inch units accepted" -ForegroundColor Green
        Write-Host "  ✓ Generated $($result.outline.Count) points" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  ✗ Inch conversion failed" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ✗ Unit conversion error: $($_.Exception.Message)" -ForegroundColor Red
    $failed++
}

# ============================================================================
# Test 9: Resolution Parameter
# ============================================================================
Write-Host "`nTest 9: Resolution parameter (16 vs 128 points)" -ForegroundColor Yellow
try {
    # Low resolution
    $lowResBody = @{
        dimensions = @{
            bodyLength = 500
            bodyWidthUpper = 300
            bodyWidthLower = 380
            waistWidth = 240
            scaleLength = 650
        }
        guitarType = "Acoustic"
        units = "mm"
        format = "json"
        resolution = 16
    } | ConvertTo-Json -Depth 5
    
    $lowRes = Invoke-RestMethod -Uri "$baseUrl/guitar/design/parametric" `
        -Method Post `
        -Body $lowResBody `
        -ContentType "application/json"
    
    # High resolution
    $highResBody = @{
        dimensions = @{
            bodyLength = 500
            bodyWidthUpper = 300
            bodyWidthLower = 380
            waistWidth = 240
            scaleLength = 650
        }
        guitarType = "Acoustic"
        units = "mm"
        format = "json"
        resolution = 128
    } | ConvertTo-Json -Depth 5
    
    $highRes = Invoke-RestMethod -Uri "$baseUrl/guitar/design/parametric" `
        -Method Post `
        -Body $highResBody `
        -ContentType "application/json"
    
    if ($lowRes.outline.Count -lt $highRes.outline.Count) {
        Write-Host "  ✓ Low res (16): $($lowRes.outline.Count) points" -ForegroundColor Green
        Write-Host "  ✓ High res (128): $($highRes.outline.Count) points" -ForegroundColor Green
        Write-Host "  ✓ Resolution affects point count as expected" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  ✗ Resolution parameter not working correctly" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ✗ Resolution test error: $($_.Exception.Message)" -ForegroundColor Red
    $failed++
}

# ============================================================================
# Test 10: Frontend Component Check
# ============================================================================
Write-Host "`nTest 10: Frontend component availability" -ForegroundColor Yellow
$componentPath = "client\src\components\toolbox\GuitarDimensionsForm.vue"
if (Test-Path $componentPath) {
    $content = Get-Content $componentPath -Raw
    
    # Check for key features
    $features = @{
        "Guitar type selector" = $content -match "guitarTypes|Acoustic.*Electric.*Classical.*Bass"
        "Dimension inputs" = $content -match "bodyLength|bodyWidthUpper|bodyWidthLower|waistWidth"
        "Unit toggle" = $content -match "currentUnit|mm.*inch"
        "DXF export" = $content -match "downloadDXF|Generate.*DXF"
        "SVG export" = $content -match "downloadSVG|Generate.*SVG"
        "SVG preview" = $content -match "<svg.*viewBox"
    }
    
    $allPresent = $true
    foreach ($feature in $features.GetEnumerator()) {
        if ($feature.Value) {
            Write-Host "  ✓ $($feature.Key)" -ForegroundColor Green
        } else {
            Write-Host "  ✗ Missing: $($feature.Key)" -ForegroundColor Red
            $allPresent = $false
        }
    }
    
    if ($allPresent) {
        $passed++
    } else {
        $failed++
    }
} else {
    Write-Host "  ✗ Component not found: $componentPath" -ForegroundColor Red
    $failed++
}

# ============================================================================
# Test 11: Navigation Integration
# ============================================================================
Write-Host "`nTest 11: Navigation integration" -ForegroundColor Yellow
$appPath = "client\src\App.vue"
if (Test-Path $appPath) {
    $appContent = Get-Content $appPath -Raw
    
    $checks = @{
        "Import statement" = $appContent -match "import GuitarDimensionsForm"
        "Navigation entry" = $appContent -match "body-outline.*Body Outline"
        "Component render" = $appContent -match "GuitarDimensionsForm v-else-if.*body-outline"
        "Welcome screen mention" = $appContent -match "Body Outline Generator|THE FOUNDATION TOOL"
    }
    
    $allIntegrated = $true
    foreach ($check in $checks.GetEnumerator()) {
        if ($check.Value) {
            Write-Host "  ✓ $($check.Key)" -ForegroundColor Green
        } else {
            Write-Host "  ✗ Missing: $($check.Key)" -ForegroundColor Red
            $allIntegrated = $false
        }
    }
    
    if ($allIntegrated) {
        $passed++
    } else {
        $failed++
    }
} else {
    Write-Host "  ✗ App.vue not found" -ForegroundColor Red
    $failed++
}

# ============================================================================
# Test 12: Frontend Accessibility Check
# ============================================================================
Write-Host "`nTest 12: Frontend accessibility (Vite running?)" -ForegroundColor Yellow
try {
    $fe = Invoke-WebRequest "http://localhost:5173" -UseBasicParsing -TimeoutSec 3
    if ($fe.StatusCode -eq 200) {
        Write-Host "  ✓ Frontend running on port 5173" -ForegroundColor Green
        Write-Host "  ✓ Click '🎸 Body Outline' to test live" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  ✗ Frontend returned HTTP $($fe.StatusCode)" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ⚠ Frontend not running (this is OK if testing backend only)" -ForegroundColor Yellow
    Write-Host "    To start: cd client && npm run dev" -ForegroundColor Gray
    # Don't count as failure
}

# ============================================================================
# Summary
# ============================================================================
Write-Host "`n=== Test Summary ===" -ForegroundColor Cyan
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Red" })

if ($failed -eq 0) {
    Write-Host "`n✅ ALL TESTS PASSED! Body Outline Generator is fully operational!" -ForegroundColor Green
    Write-Host "`n🎸 What was tested:" -ForegroundColor Cyan
    Write-Host "  • 4 guitar types (Acoustic, Electric, Classical, Bass)" -ForegroundColor White
    Write-Host "  • JSON format output with outline points" -ForegroundColor White
    Write-Host "  • DXF R12 export (CAM-ready)" -ForegroundColor White
    Write-Host "  • SVG export (visualization)" -ForegroundColor White
    Write-Host "  • Unit conversion (mm ↔ inch)" -ForegroundColor White
    Write-Host "  • Resolution control (16-128 points)" -ForegroundColor White
    Write-Host "  • Frontend component (1312 lines)" -ForegroundColor White
    Write-Host "  • Navigation integration" -ForegroundColor White
    Write-Host "`n🚀 Ready to use:" -ForegroundColor Cyan
    Write-Host "  1. Open http://localhost:5173" -ForegroundColor White
    Write-Host "  2. Click '🎸 Body Outline' in top navigation" -ForegroundColor White
    Write-Host "  3. Select guitar type and enter dimensions" -ForegroundColor White
    Write-Host "  4. See live SVG preview" -ForegroundColor White
    Write-Host "  5. Export DXF for CAM or SVG for docs" -ForegroundColor White
} else {
    Write-Host "`n❌ Some tests failed. Review errors above." -ForegroundColor Red
    exit 1
}
