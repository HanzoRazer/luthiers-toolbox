# test_pipeline_integration_phase1.ps1
# Test new CAM pipeline integration endpoints

$baseUrl = "http://localhost:8000"
Write-Host "=== Testing CAM Pipeline Integration - Phase 1 ===" -ForegroundColor Cyan
Write-Host ""

# Test 1: Health check
Write-Host "1. Testing Health Check" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/health" -Method Get
    if ($response.ok) {
        Write-Host "  ✓ Server is running" -ForegroundColor Green
    }
} catch {
    Write-Host "  ✗ Server not responding. Start with: uvicorn app.main:app --reload --port 8000" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Test 2: Pipeline Presets - List (should be empty initially)
Write-Host "2. Testing GET /cam/pipeline/presets" -ForegroundColor Yellow
try {
    $presets = Invoke-RestMethod -Uri "$baseUrl/cam/pipeline/presets" -Method Get
    Write-Host "  ✓ Presets endpoint working" -ForegroundColor Green
    Write-Host "  Found $($presets.Count) preset(s)" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Failed to fetch presets: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 3: Pipeline Presets - Create
Write-Host "3. Testing POST /cam/pipeline/presets" -ForegroundColor Yellow
$newPreset = @{
    name = "Test_GRBL_6mm"
    description = "Test preset for GRBL with 6mm endmill"
    units = "mm"
    machine_id = "GUITAR_CNC_01"
    post_id = "GRBL"
} | ConvertTo-Json

try {
    $created = Invoke-RestMethod -Uri "$baseUrl/cam/pipeline/presets" `
        -Method Post `
        -ContentType "application/json" `
        -Body $newPreset
    
    Write-Host "  ✓ Created preset: $($created.name)" -ForegroundColor Green
    Write-Host "    ID: $($created.id)" -ForegroundColor Gray
    Write-Host "    Units: $($created.units)" -ForegroundColor Gray
    Write-Host "    Machine: $($created.machine_id)" -ForegroundColor Gray
    Write-Host "    Post: $($created.post_id)" -ForegroundColor Gray
    
    $testPresetId = $created.id
} catch {
    Write-Host "  ✗ Failed to create preset: $($_.Exception.Message)" -ForegroundColor Red
    $testPresetId = $null
}
Write-Host ""

# Test 4: Pipeline Presets - Get by ID
if ($testPresetId) {
    Write-Host "4. Testing GET /cam/pipeline/presets/{id}" -ForegroundColor Yellow
    try {
        $preset = Invoke-RestMethod -Uri "$baseUrl/cam/pipeline/presets/$testPresetId" -Method Get
        Write-Host "  ✓ Retrieved preset: $($preset.name)" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ Failed to get preset: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""
}

# Test 5: DXF Plan endpoint (needs a DXF file)
Write-Host "5. Testing POST /cam/plan_from_dxf" -ForegroundColor Yellow

# Create a minimal test DXF
$testDxf = @"
0
SECTION
2
HEADER
9
`$ACADVER
1
AC1009
0
ENDSEC
0
SECTION
2
ENTITIES
0
LWPOLYLINE
8
GEOMETRY
90
4
70
1
10
0.0
20
0.0
10
100.0
20
0.0
10
100.0
20
60.0
10
0.0
20
60.0
0
ENDSEC
0
EOF
"@

$testDxfPath = [System.IO.Path]::GetTempFileName()
$testDxfPath = $testDxfPath -replace '\.tmp$', '.dxf'
[System.IO.File]::WriteAllText($testDxfPath, $testDxf)

try {
    # Create multipart form
    $boundary = [System.Guid]::NewGuid().ToString()
    $LF = "`r`n"
    
    $bodyLines = @(
        "--$boundary",
        "Content-Disposition: form-data; name=`"file`"; filename=`"test.dxf`"",
        "Content-Type: application/dxf",
        "",
        $testDxf,
        "--$boundary",
        "Content-Disposition: form-data; name=`"tool_d`"",
        "",
        "6.0",
        "--$boundary",
        "Content-Disposition: form-data; name=`"units`"",
        "",
        "mm",
        "--$boundary--"
    )
    
    $body = $bodyLines -join $LF
    
    $response = Invoke-RestMethod -Uri "$baseUrl/cam/plan_from_dxf" `
        -Method Post `
        -ContentType "multipart/form-data; boundary=$boundary" `
        -Body $body
    
    Write-Host "  ✓ DXF plan extraction successful" -ForegroundColor Green
    Write-Host "    Loops found: $($response.plan.loops.Count)" -ForegroundColor Gray
    Write-Host "    Layer: $($response.debug.layer)" -ForegroundColor Gray
    Write-Host "    Tool diameter: $($response.plan.tool_d) mm" -ForegroundColor Gray
    Write-Host "    Stepover: $($response.plan.stepover)" -ForegroundColor Gray
    
    # Show first loop points (first 3 points)
    if ($response.plan.loops.Count -gt 0) {
        $firstLoop = $response.plan.loops[0]
        Write-Host "    First loop points (preview):" -ForegroundColor Gray
        $firstLoop.pts[0..2] | ForEach-Object {
            Write-Host "      [$($_[0]), $($_[1])]" -ForegroundColor DarkGray
        }
    }
} catch {
    Write-Host "  ✗ Failed to extract plan from DXF: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "    Response: $($_.ErrorDetails.Message)" -ForegroundColor DarkRed
} finally {
    Remove-Item $testDxfPath -ErrorAction SilentlyContinue
}
Write-Host ""

# Test 6: Cleanup - Delete test preset
if ($testPresetId) {
    Write-Host "6. Testing DELETE /cam/pipeline/presets/{id}" -ForegroundColor Yellow
    try {
        Invoke-RestMethod -Uri "$baseUrl/cam/pipeline/presets/$testPresetId" -Method Delete
        Write-Host "  ✓ Deleted test preset" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ Failed to delete preset: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""
}

Write-Host "=== Phase 1 Backend Tests Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Create CamPipelineRunner.vue component" -ForegroundColor Gray
Write-Host "  2. Create AdaptiveLabView.vue view" -ForegroundColor Gray
Write-Host "  3. Add routes to Vue router" -ForegroundColor Gray
Write-Host "  4. Test full workflow: DXF → Adaptive Lab → Pipeline Lab" -ForegroundColor Gray
