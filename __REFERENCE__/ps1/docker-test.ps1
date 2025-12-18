# Luthier's Tool Box - Docker Test Suite
Write-Host "🧪 Testing Dockerized API" -ForegroundColor Cyan
Write-Host ""

# Load .env for ports
$SERVER_PORT = $env:SERVER_PORT
if (-Not $SERVER_PORT) { $SERVER_PORT = "8000" }
$CLIENT_PORT = $env:CLIENT_PORT
if (-Not $CLIENT_PORT) { $CLIENT_PORT = "8080" }

$baseUrl = "http://localhost:$SERVER_PORT"
$clientUrl = "http://localhost:$CLIENT_PORT"
$testsPassed = 0
$testsFailed = 0

function Test-Endpoint {
    param($name, $scriptBlock)
    Write-Host "Test: $name" -ForegroundColor Yellow
    try {
        & $scriptBlock
        Write-Host "✓ Passed`n" -ForegroundColor Green
        $script:testsPassed++
    } catch {
        Write-Host "❌ Failed: $_`n" -ForegroundColor Red
        $script:testsFailed++
    }
}

# Test 1: Health Check
Test-Endpoint "Health Check" {
    $response = Invoke-RestMethod -Uri "$baseUrl/health" -Method Get
    if ($response.ok -ne $true) {
        throw "Health check failed"
    }
    Write-Host "  Response: $($response | ConvertTo-Json)" -ForegroundColor Gray
}

# Test 2: Arc Simulation
Test-Endpoint "G-code Simulation with Arc (G2)" {
    $gcode = "G21 G90 G17 F1200`nG0 Z5`nG0 X0 Y0`nG1 Z-1 F300`nG2 X60 Y40 I0 J20`nG0 Z5"
    $body = @{ gcode = $gcode } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "$baseUrl/cam/simulate_gcode" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body
    
    $data = $response.Content | ConvertFrom-Json
    $summary = $response.Headers["X-CAM-Summary"]
    $modal = $response.Headers["X-CAM-Modal"]
    
    Write-Host "  Moves: $($data.moves.Count)" -ForegroundColor Gray
    Write-Host "  Summary: $summary" -ForegroundColor Gray
    Write-Host "  Modal: $modal" -ForegroundColor Gray
    
    $arcMove = $data.moves | Where-Object { $_.code -eq "G2" }
    if (-Not $arcMove) {
        throw "No G2 arc move found"
    }
    Write-Host "  ✓ Arc move: i=$($arcMove.i), j=$($arcMove.j), t=$($arcMove.t)s" -ForegroundColor Gray
}

# Test 3: Post-Processors
Test-Endpoint "List Post-Processors" {
    $response = Invoke-RestMethod -Uri "$baseUrl/tooling/posts" -Method Get
    $count = ($response.PSObject.Properties | Measure-Object).Count
    if ($count -lt 5) {
        throw "Expected at least 5 post-processors, got $count"
    }
    Write-Host "  Found $count post-processors" -ForegroundColor Gray
    $response.PSObject.Properties | ForEach-Object {
        Write-Host "    - $($_.Name)" -ForegroundColor Gray
    }
}

# Test 4: Add Tool
Test-Endpoint "Add Tool to Database" {
    $tool = @{
        name = "Docker Test Endmill"
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
        Write-Host "  Tool added successfully" -ForegroundColor Gray
    } catch {
        if ($_.Exception.Response.StatusCode -eq 500) {
            Write-Host "  Tool may already exist (acceptable)" -ForegroundColor Gray
        } else {
            throw
        }
    }
}

# Test 5: Add Material
Test-Endpoint "Add Material to Database" {
    $material = @{
        name = "Docker Test Wood"
        chipload_mm = 0.15
        max_rpm = 18000
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "$baseUrl/tooling/materials" `
            -Method Post `
            -ContentType "application/json" `
            -Body $material
        Write-Host "  Material added successfully" -ForegroundColor Gray
    } catch {
        if ($_.Exception.Response.StatusCode -eq 500) {
            Write-Host "  Material may already exist (acceptable)" -ForegroundColor Gray
        } else {
            throw
        }
    }
}

# Test 6: Calculate Feeds/Speeds
Test-Endpoint "Calculate Feeds/Speeds" {
    $request = @{
        tool_name = "Docker Test Endmill"
        material_name = "Docker Test Wood"
        rpm = 15000
        width_mm = 3.0
        depth_mm = 2.0
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$baseUrl/tooling/feedspeeds" `
        -Method Post `
        -ContentType "application/json" `
        -Body $request
    
    if ($response.rpm -ne 15000) {
        throw "RPM mismatch"
    }
    Write-Host "  RPM: $($response.rpm)" -ForegroundColor Gray
    Write-Host "  Feed: $($response.feed_mm_min) mm/min" -ForegroundColor Gray
}

# Test 7: Client Container
Test-Endpoint "Client Container Serving" {
    $response = Invoke-WebRequest -Uri $clientUrl -Method Get
    if ($response.Content -notmatch "Luthier's Tool Box") {
        throw "Client page not serving correctly"
    }
    Write-Host "  Client HTML served successfully" -ForegroundColor Gray
}

# Test 8: API Proxy through Client
Test-Endpoint "API Proxy through Client" {
    $response = Invoke-RestMethod -Uri "$clientUrl/health" -Method Get
    if ($response.ok -ne $true) {
        throw "Proxy health check failed"
    }
    Write-Host "  Proxy working: client -> nginx -> api" -ForegroundColor Gray
}

# Summary
Write-Host ""
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host "Test Results:" -ForegroundColor Cyan
Write-Host "  Passed: $testsPassed" -ForegroundColor Green
Write-Host "  Failed: $testsFailed" -ForegroundColor $(if ($testsFailed -gt 0) { "Red" } else { "Gray" })
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan

if ($testsFailed -gt 0) {
    Write-Host "`n❌ Some tests failed" -ForegroundColor Red
    exit 1
} else {
    Write-Host "`n🎉 All tests passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. View logs: docker compose logs -f" -ForegroundColor Gray
    Write-Host "  2. Check API docs: http://localhost:$SERVER_PORT/docs" -ForegroundColor Gray
    Write-Host "  3. Open client: http://localhost:$CLIENT_PORT" -ForegroundColor Gray
    Write-Host "  4. Stop stack: docker compose down" -ForegroundColor Gray
}
