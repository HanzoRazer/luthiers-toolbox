# Test Parametric Guitar Design API
# Validates dimension-driven body outline generation

Write-Host "=== Testing Parametric Guitar Design API ===" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"

# Test 1: Health check
Write-Host "1. Testing GET /guitar/design/health" -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$baseUrl/guitar/design/health" -Method GET
    Write-Host "   ✅ Health check:" -ForegroundColor Green
    Write-Host "      Status: $($health.status)"
    Write-Host "      Service: $($health.service)"
    Write-Host "      Version: $($health.version)"
} catch {
    Write-Host "   ❌ Health check failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 2: Generate Dreadnought body (JSON response)
Write-Host "2. Testing POST /guitar/design/parametric (Dreadnought)" -ForegroundColor Yellow
$dreadnoughtBody = @{
    dimensions = @{
        bodyLength = 505
        bodyWidthUpper = 280
        bodyWidthLower = 390
        waistWidth = 270
        bodyDepth = 120
        scaleLength = 648
        nutWidth = 43
        bridgeSpacing = 56
        fretCount = 20
        neckAngle = 0
    }
    guitarType = "Acoustic"
    units = "mm"
    format = "json"
    resolution = 48
}

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/guitar/design/parametric" -Method POST -Body ($dreadnoughtBody | ConvertTo-Json -Depth 5) -ContentType "application/json"
    Write-Host "   ✅ Parametric generation successful:" -ForegroundColor Green
    Write-Host "      Guitar Type: $($response.guitarType)"
    Write-Host "      Outline Points: $($response.outline.Count)"
    Write-Host "      Bounding Box: $($response.boundingBox.width)mm × $($response.boundingBox.height)mm"
    Write-Host "      Message: $($response.message)"
} catch {
    Write-Host "   ❌ Parametric generation failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 3: Export Les Paul body as DXF
Write-Host "3. Testing POST /guitar/design/parametric/export (Les Paul DXF)" -ForegroundColor Yellow
$lesPaulBody = @{
    dimensions = @{
        bodyLength = 475
        bodyWidthUpper = 330
        bodyWidthLower = 330
        waistWidth = 280
        bodyDepth = 55
        scaleLength = 628
        nutWidth = 43
        bridgeSpacing = 52
        fretCount = 22
        neckAngle = 4
    }
    guitarType = "Electric"
    units = "mm"
    format = "dxf"
    resolution = 48
}

try {
    $dxfFile = "test_les_paul_body.dxf"
    Invoke-WebRequest -Uri "$baseUrl/guitar/design/parametric/export" -Method POST -Body ($lesPaulBody | ConvertTo-Json -Depth 5) -ContentType "application/json" -OutFile $dxfFile
    
    if (Test-Path $dxfFile) {
        $fileSize = (Get-Item $dxfFile).Length
        Write-Host "   ✅ DXF export successful:" -ForegroundColor Green
        Write-Host "      File: $dxfFile"
        Write-Host "      Size: $fileSize bytes"
        
        # Validate DXF content
        $dxfContent = Get-Content $dxfFile -Raw
        if ($dxfContent -match "AC1009" -and $dxfContent -match "LWPOLYLINE" -and $dxfContent -match "BODY_OUTLINE") {
            Write-Host "      ✅ DXF format: R12 (AC1009)" -ForegroundColor Green
            Write-Host "      ✅ Contains LWPOLYLINE" -ForegroundColor Green
            Write-Host "      ✅ Layer: BODY_OUTLINE" -ForegroundColor Green
        } else {
            Write-Host "      ⚠️ DXF content validation failed" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ❌ DXF file not created" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "   ❌ DXF export failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 4: Export Stratocaster as SVG
Write-Host "4. Testing POST /guitar/design/parametric/export (Stratocaster SVG)" -ForegroundColor Yellow
$stratBody = @{
    dimensions = @{
        bodyLength = 460
        bodyWidthUpper = 320
        bodyWidthLower = 320
        waistWidth = 280
        bodyDepth = 45
        scaleLength = 648
        nutWidth = 42
        bridgeSpacing = 52
        fretCount = 22
        neckAngle = 0
    }
    guitarType = "Electric"
    units = "mm"
    format = "svg"
    resolution = 48
}

try {
    $svgFile = "test_stratocaster_body.svg"
    Invoke-WebRequest -Uri "$baseUrl/guitar/design/parametric/export" -Method POST -Body ($stratBody | ConvertTo-Json -Depth 5) -ContentType "application/json" -OutFile $svgFile
    
    if (Test-Path $svgFile) {
        $fileSize = (Get-Item $svgFile).Length
        Write-Host "   ✅ SVG export successful:" -ForegroundColor Green
        Write-Host "      File: $svgFile"
        Write-Host "      Size: $fileSize bytes"
        
        # Validate SVG content
        $svgContent = Get-Content $svgFile -Raw
        if ($svgContent -match '<svg' -and $svgContent -match '<path' -and $svgContent -match 'Parametric Design') {
            Write-Host "      ✅ SVG format valid" -ForegroundColor Green
            Write-Host "      ✅ Contains path element" -ForegroundColor Green
            Write-Host "      ✅ Contains metadata" -ForegroundColor Green
        } else {
            Write-Host "      ⚠️ SVG content validation failed" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ❌ SVG file not created" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "   ❌ SVG export failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== All Tests Completed Successfully ===" -ForegroundColor Green
Write-Host ""
Write-Host "📁 Generated files:" -ForegroundColor Cyan
Write-Host "   - $dxfFile (DXF R12 format for CAM software)"
Write-Host "   - $svgFile (SVG preview)"
Write-Host ""
Write-Host "🎯 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Import test_les_paul_body.dxf into Fusion 360 or VCarve"
Write-Host "   2. Verify closed LWPOLYLINE on BODY_OUTLINE layer"
Write-Host "   3. Test with GuitarDimensionsForm.vue component in browser"
Write-Host "   4. Connect to CAM pipeline (adaptive pocketing)"
