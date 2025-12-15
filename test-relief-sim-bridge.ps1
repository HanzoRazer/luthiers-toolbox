# Test Relief Sim Bridge endpoint
# Requires: uvicorn app.main:app --reload --port 8000

Write-Host "=== Testing Relief Sim Bridge Endpoint ===" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"

# Test 1: Simple relief finishing moves with sim bridge
Write-Host "Test 1: Relief sim bridge with sample finishing moves" -ForegroundColor Yellow

$payload1 = @{
    moves = @(
        @{ code = "G0"; z = 5.0 }
        @{ code = "G0"; x = 0.0; y = 0.0 }
        @{ code = "G1"; z = -1.5; f = 600.0 }
        @{ code = "G1"; x = 50.0; y = 0.0; f = 600.0 }
        @{ code = "G1"; z = -2.0; f = 600.0 }
        @{ code = "G1"; x = 50.0; y = 10.0; f = 600.0 }
        @{ code = "G1"; z = -2.5; f = 600.0 }
        @{ code = "G1"; x = 0.0; y = 10.0; f = 600.0 }
        @{ code = "G1"; z = -3.0; f = 600.0 }
        @{ code = "G1"; x = 0.0; y = 20.0; f = 600.0 }
        @{ code = "G0"; z = 5.0 }
    )
    stock_thickness = 5.0
    origin_x = 0.0
    origin_y = 0.0
    cell_size_xy = 0.5
    units = "mm"
    min_floor_thickness = 0.6
    high_load_index = 2.0
    med_load_index = 1.0
} | ConvertTo-Json -Depth 10

try {
    $response1 = Invoke-RestMethod -Uri "$baseUrl/cam/relief/sim_bridge" `
        -Method POST `
        -ContentType "application/json" `
        -Body $payload1
    
    Write-Host "  ✓ Sim bridge successful" -ForegroundColor Green
    Write-Host "    Cell count: $($response1.stats.cell_count)" -ForegroundColor Gray
    Write-Host "    Avg floor thickness: $($response1.stats.avg_floor_thickness.ToString('F2')) mm" -ForegroundColor Gray
    Write-Host "    Min floor thickness: $($response1.stats.min_floor_thickness.ToString('F2')) mm" -ForegroundColor Gray
    Write-Host "    Max load index: $($response1.stats.max_load_index.ToString('F2'))" -ForegroundColor Gray
    Write-Host "    Avg load index: $($response1.stats.avg_load_index.ToString('F2'))" -ForegroundColor Gray
    Write-Host "    Removed volume: $($response1.stats.total_removed_volume.ToString('F2')) mm³" -ForegroundColor Gray
    Write-Host "    Issues count: $($response1.issues.Count)" -ForegroundColor Gray
    Write-Host "    Overlays count: $($response1.overlays.Count)" -ForegroundColor Gray
    
    # Check for thin floor issues
    $thinFloorIssues = $response1.issues | Where-Object { $_.type -eq "thin_floor" }
    Write-Host "    Thin floor issues: $($thinFloorIssues.Count)" -ForegroundColor $(if ($thinFloorIssues.Count -gt 0) { "Yellow" } else { "Gray" })
    
    # Check for high load issues
    $highLoadIssues = $response1.issues | Where-Object { $_.type -eq "high_load" }
    Write-Host "    High load issues: $($highLoadIssues.Count)" -ForegroundColor $(if ($highLoadIssues.Count -gt 0) { "Yellow" } else { "Gray" })
    
    # Check overlay types
    $loadHotspots = $response1.overlays | Where-Object { $_.type -eq "load_hotspot" }
    $thinFloorZones = $response1.overlays | Where-Object { $_.type -eq "thin_floor_zone" }
    Write-Host "    Load hotspots: $($loadHotspots.Count)" -ForegroundColor Gray
    Write-Host "    Thin floor zones: $($thinFloorZones.Count)" -ForegroundColor Gray
    
} catch {
    Write-Host "  ✗ Sim bridge failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "    Response: $($_.ErrorDetails.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 2: Deep cut scenario (should trigger thin floor warnings)
Write-Host "Test 2: Deep cut scenario (thin floor detection)" -ForegroundColor Yellow

$payload2 = @{
    moves = @(
        @{ code = "G0"; z = 5.0 }
        @{ code = "G0"; x = 0.0; y = 0.0 }
        @{ code = "G1"; z = -4.5; f = 600.0 }  # Very deep cut
        @{ code = "G1"; x = 30.0; y = 0.0; f = 600.0 }
        @{ code = "G1"; z = -4.8; f = 600.0 }  # Even deeper
        @{ code = "G1"; x = 30.0; y = 15.0; f = 600.0 }
        @{ code = "G0"; z = 5.0 }
    )
    stock_thickness = 5.0  # 5mm stock with 4.8mm cut = 0.2mm floor
    origin_x = 0.0
    origin_y = 0.0
    cell_size_xy = 0.5
    units = "mm"
    min_floor_thickness = 0.6  # Threshold
    high_load_index = 2.0
    med_load_index = 1.0
} | ConvertTo-Json -Depth 10

try {
    $response2 = Invoke-RestMethod -Uri "$baseUrl/cam/relief/sim_bridge" `
        -Method POST `
        -ContentType "application/json" `
        -Body $payload2
    
    Write-Host "  ✓ Deep cut sim successful" -ForegroundColor Green
    Write-Host "    Min floor thickness: $($response2.stats.min_floor_thickness.ToString('F2')) mm" -ForegroundColor Gray
    Write-Host "    Total issues: $($response2.issues.Count)" -ForegroundColor Gray
    
    $thinFloorIssues = $response2.issues | Where-Object { $_.type -eq "thin_floor" }
    if ($thinFloorIssues.Count -gt 0) {
        Write-Host "    ✓ Thin floor detection working ($($thinFloorIssues.Count) issues)" -ForegroundColor Green
        $criticalIssues = $thinFloorIssues | Where-Object { $_.severity -eq "high" }
        $mediumIssues = $thinFloorIssues | Where-Object { $_.severity -eq "medium" }
        Write-Host "      High severity: $($criticalIssues.Count)" -ForegroundColor Red
        Write-Host "      Medium severity: $($mediumIssues.Count)" -ForegroundColor Yellow
    } else {
        Write-Host "    ✗ Expected thin floor issues but got none" -ForegroundColor Red
    }
    
} catch {
    Write-Host "  ✗ Deep cut test failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 3: Empty moves (edge case)
Write-Host "Test 3: Empty moves (edge case)" -ForegroundColor Yellow

$payload3 = @{
    moves = @()
    stock_thickness = 5.0
    origin_x = 0.0
    origin_y = 0.0
    cell_size_xy = 0.5
    units = "mm"
    min_floor_thickness = 0.6
    high_load_index = 2.0
    med_load_index = 1.0
} | ConvertTo-Json -Depth 10

try {
    $response3 = Invoke-RestMethod -Uri "$baseUrl/cam/relief/sim_bridge" `
        -Method POST `
        -ContentType "application/json" `
        -Body $payload3
    
    Write-Host "  ✓ Empty moves handled gracefully" -ForegroundColor Green
    Write-Host "    Cell count: $($response3.stats.cell_count)" -ForegroundColor Gray
    Write-Host "    Issues: $($response3.issues.Count)" -ForegroundColor Gray
    Write-Host "    Overlays: $($response3.overlays.Count)" -ForegroundColor Gray
    
    if ($response3.stats.cell_count -eq 0 -and $response3.issues.Count -eq 0) {
        Write-Host "    ✓ Edge case validation passed" -ForegroundColor Green
    }
    
} catch {
    Write-Host "  ✗ Empty moves test failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== All Relief Sim Bridge Tests Complete ===" -ForegroundColor Cyan
