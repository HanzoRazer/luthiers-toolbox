# Luthier's Tool Box - API Test Script
Write-Host "🧪 Testing Monorepo API Endpoints" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"

# Test 1: Health Check
Write-Host "Test 1: Health Check" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/health" -Method Get
    Write-Host "✓ Health check passed: $($response | ConvertTo-Json)" -ForegroundColor Green
} catch {
    Write-Host "❌ Health check failed: $_" -ForegroundColor Red
    Write-Host "Make sure API is running: .\start_api.ps1"
    exit 1
}
Write-Host ""

# Test 2: Simulate G-code with Arcs
Write-Host "Test 2: G-code Simulation (with G2 arc)" -ForegroundColor Yellow
$gcode = "G21 G90 G17 F1200`nG0 Z5`nG0 X0 Y0`nG1 Z-1 F300`nG2 X60 Y40 I0 J20`nG0 Z5"
$body = @{
    gcode = $gcode
    as_csv = $false
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri "$baseUrl/cam/simulate_gcode" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body
    
    $data = $response.Content | ConvertFrom-Json
    $summary = $response.Headers["X-CAM-Summary"]
    $modal = $response.Headers["X-CAM-Modal"]
    
    Write-Host "✓ Simulation passed" -ForegroundColor Green
    Write-Host "  Moves: $($data.moves.Count)" -ForegroundColor Gray
    Write-Host "  Summary: $summary" -ForegroundColor Gray
    Write-Host "  Modal: $modal" -ForegroundColor Gray
    
    # Check for arc move
    $arcMove = $data.moves | Where-Object { $_.code -eq "G2" }
    if ($arcMove) {
        Write-Host "  ✓ Arc move detected (G2) with i=$($arcMove.i), j=$($arcMove.j)" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Simulation failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 3: List Post-Processors
Write-Host "Test 3: List Post-Processors" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/tooling/posts" -Method Get
    $count = ($response.PSObject.Properties | Measure-Object).Count
    Write-Host "✓ Found $count post-processors:" -ForegroundColor Green
    $response.PSObject.Properties | ForEach-Object {
        Write-Host "  - $($_.Name)" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ Post-processor list failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 4: Add a Tool
Write-Host "Test 4: Add Tool to Database" -ForegroundColor Yellow
$tool = @{
    name = "Test Endmill 6mm"
    type = "flat"
    diameter_mm = 6.0
    flute_count = 2
    helix_deg = 30.0
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/tooling/tools" `
        -Method Post `
        -ContentType "application/json" `
        -Body $tool
    Write-Host "✓ Tool added successfully" -ForegroundColor Green
} catch {
    Write-Host "⚠ Tool add failed (may already exist): $_" -ForegroundColor Yellow
}
Write-Host ""

# Test 5: List Tools
Write-Host "Test 5: List Tools" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/tooling/tools" -Method Get
    Write-Host "✓ Found $($response.Count) tools in database" -ForegroundColor Green
    if ($response.Count -gt 0) {
        $response | ForEach-Object {
            Write-Host "  - $($_.name) ($($_.type), $($_.diameter_mm)mm)" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "❌ Tool list failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 6: Add Material
Write-Host "Test 6: Add Material to Database" -ForegroundColor Yellow
$material = @{
    name = "Test Hardwood"
    chipload_mm = 0.15
    max_rpm = 18000
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/tooling/materials" `
        -Method Post `
        -ContentType "application/json" `
        -Body $material
    Write-Host "✓ Material added successfully" -ForegroundColor Green
} catch {
    Write-Host "⚠ Material add failed (may already exist): $_" -ForegroundColor Yellow
}
Write-Host ""

# Test 7: Calculate Feeds/Speeds
Write-Host "Test 7: Calculate Feeds/Speeds" -ForegroundColor Yellow
$feedRequest = @{
    tool_name = "Test Endmill 6mm"
    material_name = "Test Hardwood"
    rpm = 15000
    width_mm = 3.0
    depth_mm = 2.0
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/tooling/feedspeeds" `
        -Method Post `
        -ContentType "application/json" `
        -Body $feedRequest
    Write-Host "✓ Feeds/speeds calculated:" -ForegroundColor Green
    Write-Host "  RPM: $($response.rpm)" -ForegroundColor Gray
    Write-Host "  Feed: $($response.feed_mm_min) mm/min" -ForegroundColor Gray
} catch {
    Write-Host "❌ Feeds/speeds calculation failed: $_" -ForegroundColor Red
}
Write-Host ""

Write-Host "🎉 All tests completed!" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Check API docs: http://localhost:8000/docs"
Write-Host "  2. View OpenAPI spec: http://localhost:8000/openapi.json"
Write-Host "  3. Read MONOREPO_SETUP.md for detailed documentation"
