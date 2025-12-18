# Art Studio v16.0 Smoke Test
# Tests: SVG Editor + Relief Mapper endpoints

$BASE = "http://localhost:8000"

Write-Host "`n=== Testing Art Studio v16.0 (SVG Editor + Relief Mapper) ===" -ForegroundColor Cyan

# Test 1: SVG Health Check
Write-Host "`n1. Testing GET /api/art/svg/health" -ForegroundColor Yellow
try {
    $res = Invoke-RestMethod -Uri "$BASE/api/art/svg/health" -Method GET
    if ($res.ok -and $res.service -eq "svg_v160" -and $res.version -eq "16.0") {
        Write-Host "  ✓ SVG service health OK" -ForegroundColor Green
        Write-Host "    Service: $($res.service), Version: $($res.version)" -ForegroundColor Gray
    } else {
        Write-Host "  ✗ SVG health check failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  ✗ SVG health endpoint error: $_" -ForegroundColor Red
    exit 1
}

# Test 2: Relief Health Check
Write-Host "`n2. Testing GET /api/art/relief/health" -ForegroundColor Yellow
try {
    $res = Invoke-RestMethod -Uri "$BASE/api/art/relief/health" -Method GET
    if ($res.ok -and $res.service -eq "relief_v160" -and $res.version -eq "16.0") {
        Write-Host "  ✓ Relief service health OK" -ForegroundColor Green
        Write-Host "    Service: $($res.service), Version: $($res.version)" -ForegroundColor Gray
    } else {
        Write-Host "  ✗ Relief health check failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  ✗ Relief health endpoint error: $_" -ForegroundColor Red
    exit 1
}

# Test 3: SVG Normalize
Write-Host "`n3. Testing POST /api/art/svg/normalize" -ForegroundColor Yellow
$svgText = @'
<svg xmlns="http://www.w3.org/2000/svg" width="120" height="60">
    <rect x="4" y="4" width="112" height="52" fill="none" stroke="black"/>
</svg>
'@

try {
    $body = @{ svg_text = $svgText } | ConvertTo-Json
    $res = Invoke-RestMethod -Uri "$BASE/api/art/svg/normalize" -Method POST -Body $body -ContentType "application/json"
    if ($res.ok -and $res.svg_text) {
        Write-Host "  ✓ SVG normalize successful" -ForegroundColor Green
        Write-Host "    Normalized length: $($res.svg_text.Length) chars" -ForegroundColor Gray
    } else {
        Write-Host "  ✗ SVG normalize failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  ✗ SVG normalize error: $_" -ForegroundColor Red
    exit 1
}

# Test 4: SVG Stroke to Outline
Write-Host "`n4. Testing POST /api/art/svg/outline" -ForegroundColor Yellow
try {
    $body = @{
        svg_text = $svgText
        stroke_width_mm = 0.4
    } | ConvertTo-Json
    $res = Invoke-RestMethod -Uri "$BASE/api/art/svg/outline" -Method POST -Body $body -ContentType "application/json"
    if ($res.ok -and $res.polylines) {
        Write-Host "  ✓ SVG stroke-to-outline successful" -ForegroundColor Green
        Write-Host "    Polylines: $($res.polylines.Count), Stroke width: $($res.stroke_width_mm) mm" -ForegroundColor Gray
    } else {
        Write-Host "  ✗ SVG outline failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  ✗ SVG outline error: $_" -ForegroundColor Red
    exit 1
}

# Test 5: SVG Save
Write-Host "`n5. Testing POST /api/art/svg/save" -ForegroundColor Yellow
try {
    $body = @{
        svg_text = $svgText
        name = "demo_v16"
    } | ConvertTo-Json
    $res = Invoke-RestMethod -Uri "$BASE/api/art/svg/save" -Method POST -Body $body -ContentType "application/json"
    if ($res.ok -and $res.bytes_b64) {
        Write-Host "  ✓ SVG save successful" -ForegroundColor Green
        Write-Host "    Name: $($res.name), Base64 length: $($res.bytes_b64.Length)" -ForegroundColor Gray
    } else {
        Write-Host "  ✗ SVG save failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  ✗ SVG save error: $_" -ForegroundColor Red
    exit 1
}

# Test 6: Relief Heightmap Preview
Write-Host "`n6. Testing POST /api/art/relief/heightmap_preview" -ForegroundColor Yellow
try {
    $body = @{
        grayscale = @(
            @(0.0, 0.5, 1.0),
            @(0.2, 0.4, 0.8),
            @(0.0, 0.3, 0.6)
        )
        z_min_mm = 0.0
        z_max_mm = 1.2
        scale_xy_mm = 1.0
    } | ConvertTo-Json -Depth 10
    $res = Invoke-RestMethod -Uri "$BASE/api/art/relief/heightmap_preview" -Method POST -Body $body -ContentType "application/json"
    if ($res.ok -and $res.verts) {
        Write-Host "  ✓ Relief heightmap preview successful" -ForegroundColor Green
        Write-Host "    Rows: $($res.rows), Cols: $($res.cols), Vertices: $($res.rows * $res.cols)" -ForegroundColor Gray
        Write-Host "    Sample Z values: $($res.verts[0][0][2]), $($res.verts[1][1][2]), $($res.verts[2][2][2])" -ForegroundColor Gray
    } else {
        Write-Host "  ✗ Relief heightmap preview failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  ✗ Relief heightmap preview error: $_" -ForegroundColor Red
    exit 1
}

# Validate specific Z calculations
Write-Host "`n7. Validating heightmap Z calculations" -ForegroundColor Yellow
$expectedZ = @(
    @(0.0, 0.6, 1.2),  # Z = z_min + grayscale * (z_max - z_min)
    @(0.24, 0.48, 0.96),
    @(0.0, 0.36, 0.72)
)
$tolerance = 0.01
$allCorrect = $true

for ($j = 0; $j -lt 3; $j++) {
    for ($i = 0; $i -lt 3; $i++) {
        $actualZ = $res.verts[$j][$i][2]
        $expected = $expectedZ[$j][$i]
        if ([Math]::Abs($actualZ - $expected) -gt $tolerance) {
            Write-Host "  ✗ Z calculation mismatch at [$j][$i]: expected $expected, got $actualZ" -ForegroundColor Red
            $allCorrect = $false
        }
    }
}

if ($allCorrect) {
    Write-Host "  ✓ All Z calculations correct" -ForegroundColor Green
} else {
    Write-Host "  ✗ Some Z calculations incorrect" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== All Art Studio v16.0 Tests Passed ===" -ForegroundColor Green
Write-Host "`nIntegration Status:" -ForegroundColor Cyan
Write-Host "  ✓ Backend: cam_svg_v160_router.py" -ForegroundColor Green
Write-Host "  ✓ Backend: cam_relief_v160_router.py" -ForegroundColor Green
Write-Host "  ✓ API: /api/art/svg/* (4 endpoints)" -ForegroundColor Green
Write-Host "  ✓ API: /api/art/relief/* (2 endpoints)" -ForegroundColor Green
Write-Host "`nFrontend files ready:" -ForegroundColor Cyan
Write-Host "  - packages/client/src/api/v16.ts" -ForegroundColor Gray
Write-Host "  - packages/client/src/views/ArtStudioV16.vue" -ForegroundColor Gray
Write-Host "  - packages/client/src/components/SvgCanvas.vue" -ForegroundColor Gray
Write-Host "  - packages/client/src/components/ReliefGrid.vue" -ForegroundColor Gray
Write-Host "`nNext: Add route in packages/client/src/router/index.ts" -ForegroundColor Yellow
Write-Host "  { path: '/art-studio-v16', name: 'ArtStudioV16', component: () => import('@/views/ArtStudioV16.vue') }" -ForegroundColor Gray
