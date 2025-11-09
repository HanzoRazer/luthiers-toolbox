# Test Adaptive Pocketing Engine
# Run this after starting the API server to verify all endpoints work

Write-Host "`n=== Testing Adaptive Pocketing Engine ===" -ForegroundColor Cyan

$baseUrl = "http://localhost:8000"

# Test 1: Plan adaptive pocket
Write-Host "`n1. Testing POST /api/cam/pocket/adaptive/plan" -ForegroundColor Yellow
try {
    $body = @{
        loops = @(
            @{ pts = @(@(0,0), @(100,0), @(100,60), @(0,60)) }
        )
        units = "mm"
        tool_d = 6.0
        stepover = 0.45
        stepdown = 1.5
        margin = 0.5
        strategy = "Spiral"
        smoothing = 0.8
        climb = $true
        feed_xy = 1200
        safe_z = 5
        z_rough = -1.5
    } | ConvertTo-Json -Depth 10

    $result = Invoke-RestMethod -Uri "$baseUrl/cam/pocket/adaptive/plan" -Method Post -Body $body -ContentType "application/json"
    Write-Host "✓ Plan successful:" -ForegroundColor Green
    Write-Host "  Length: $($result.stats.length_mm) mm"
    Write-Host "  Area: $($result.stats.area_mm2) mm²"
    Write-Host "  Time: $($result.stats.time_s) s ($([math]::Round($result.stats.time_s/60, 2)) min)"
    Write-Host "  Moves: $($result.stats.move_count)"
    Write-Host "  Volume: $($result.stats.volume_mm3) mm³"
} catch {
    Write-Host "✗ Failed to plan pocket: $_" -ForegroundColor Red
}

# Test 2: Generate G-code with post-processor
Write-Host "`n2. Testing POST /api/cam/pocket/adaptive/gcode" -ForegroundColor Yellow
try {
    $body = @{
        loops = @(
            @{ pts = @(@(0,0), @(50,0), @(50,30), @(0,30)) }
        )
        units = "mm"
        tool_d = 6.0
        stepover = 0.45
        stepdown = 1.5
        margin = 0.5
        strategy = "Spiral"
        smoothing = 0.8
        climb = $true
        feed_xy = 1200
        safe_z = 5
        z_rough = -1.5
        post_id = "GRBL"
    } | ConvertTo-Json -Depth 10

    $result = Invoke-WebRequest -Uri "$baseUrl/cam/pocket/adaptive/gcode" -Method Post -Body $body -ContentType "application/json"
    $gcode = $result.Content
    
    Write-Host "✓ G-code generated (first 10 lines):" -ForegroundColor Green
    ($gcode -split "`n")[0..9] | ForEach-Object { Write-Host "  $_" }
    
    # Verify G-code structure
    if ($gcode -match "G21") {
        Write-Host "  ✓ G21 (mm units) found" -ForegroundColor Green
    }
    if ($gcode -match "G90") {
        Write-Host "  ✓ G90 (absolute mode) found" -ForegroundColor Green
    }
    if ($gcode -match "POST=GRBL") {
        Write-Host "  ✓ GRBL metadata found" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ Failed to generate G-code: $_" -ForegroundColor Red
}

# Test 3: Simulate pocket
Write-Host "`n3. Testing POST /api/cam/pocket/adaptive/sim" -ForegroundColor Yellow
try {
    $body = @{
        loops = @(
            @{ pts = @(@(0,0), @(80,0), @(80,50), @(0,50)) }
        )
        units = "mm"
        tool_d = 8.0
        stepover = 0.50
        stepdown = 2.0
        margin = 0.5
        strategy = "Lanes"
        smoothing = 0.8
        climb = $false
        feed_xy = 1500
        safe_z = 5
        z_rough = -2.0
    } | ConvertTo-Json -Depth 10

    $result = Invoke-RestMethod -Uri "$baseUrl/cam/pocket/adaptive/sim" -Method Post -Body $body -ContentType "application/json"
    Write-Host "✓ Simulation successful:" -ForegroundColor Green
    Write-Host "  Success: $($result.success)"
    Write-Host "  Stats: $($result.stats | ConvertTo-Json -Compress)"
} catch {
    Write-Host "✗ Failed to simulate pocket: $_" -ForegroundColor Red
}

# Test 4: Test with island (future enhancement)
Write-Host "`n4. Testing pocket with island (basic)" -ForegroundColor Yellow
try {
    $body = @{
        loops = @(
            @{ pts = @(@(0,0), @(100,0), @(100,60), @(0,60)) },
            @{ pts = @(@(40,20), @(60,20), @(60,40), @(40,40)) }  # Island
        )
        units = "mm"
        tool_d = 6.0
        stepover = 0.45
        stepdown = 1.5
        margin = 0.5
        strategy = "Spiral"
        smoothing = 0.8
        climb = $true
        feed_xy = 1200
        safe_z = 5
        z_rough = -1.5
    } | ConvertTo-Json -Depth 10

    $result = Invoke-RestMethod -Uri "$baseUrl/cam/pocket/adaptive/plan" -Method Post -Body $body -ContentType "application/json"
    Write-Host "✓ Pocket with island planned:" -ForegroundColor Green
    Write-Host "  Length: $($result.stats.length_mm) mm"
    Write-Host "  Moves: $($result.stats.move_count)"
} catch {
    Write-Host "✗ Failed to plan pocket with island: $_" -ForegroundColor Red
}

Write-Host "`n=== All Tests Complete ===" -ForegroundColor Cyan
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Start the client: cd packages/client && npm run dev"
Write-Host "  2. Open http://localhost:5173 in browser"
Write-Host "  3. Test the AdaptivePocketLab component"
Write-Host "  4. Adjust parameters (stepover, strategy, climb milling)"
Write-Host "  5. Export G-code for your CNC machine`n"
