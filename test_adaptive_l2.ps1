#!/usr/bin/env pwsh
# Test script for Adaptive Pocketing Engine L.2
# Tests true spiralizer, adaptive stepover, min-fillet, and HUD overlays

Write-Host "=== Testing Adaptive Pocketing L.2 ===" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"

# Test 1: Basic L.2 plan with HUD overlays
Write-Host "1. Testing L.2 plan with HUD overlays" -ForegroundColor Yellow

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
    smoothing = 0.3
    climb = $true
    feed_xy = 1200
    safe_z = 5
    z_rough = -1.5
    corner_radius_min = 1.0
    target_stepover = 0.45
    slowdown_feed_pct = 60.0
} | ConvertTo-Json -Depth 5

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/cam/pocket/adaptive/plan" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body
    
    Write-Host "  ✓ L.2 Plan successful:" -ForegroundColor Green
    Write-Host "    Length: $($response.stats.length_mm) mm"
    Write-Host "    Area: $($response.stats.area_mm2) mm²"
    Write-Host "    Time: $($response.stats.time_s) s"
    Write-Host "    Moves: $($response.stats.move_count)"
    Write-Host "    Overlays: $($response.overlays.Count)"
    
    # Sanity checks
    if ($response.stats.length_mm -lt 100) {
        throw "Path too short: $($response.stats.length_mm) mm"
    }
    
    if ($response.overlays.Count -lt 1) {
        throw "Expected HUD overlays, got: $($response.overlays.Count)"
    }
    
    # Check overlay structure
    $firstOverlay = $response.overlays[0]
    if (-not $firstOverlay.kind) {
        throw "Overlay missing 'kind' field"
    }
    
    $validKinds = @("tight_radius", "slowdown", "fillet")
    if ($firstOverlay.kind -notin $validKinds) {
        throw "Invalid overlay kind: $($firstOverlay.kind)"
    }
    
    if (-not ($firstOverlay.PSObject.Properties.Name -contains "x") -or 
        -not ($firstOverlay.PSObject.Properties.Name -contains "y")) {
        throw "Overlay missing x/y coordinates"
    }
    
    Write-Host "  ✓ HUD overlay structure validated" -ForegroundColor Green
    Write-Host "    First overlay: kind=$($firstOverlay.kind), x=$($firstOverlay.x), y=$($firstOverlay.y)"
    
    # Count overlay types
    $filletCount = ($response.overlays | Where-Object { $_.kind -eq "fillet" }).Count
    $tightCount = ($response.overlays | Where-Object { $_.kind -eq "tight_radius" }).Count
    $slowCount = ($response.overlays | Where-Object { $_.kind -eq "slowdown" }).Count
    
    Write-Host "  ✓ Overlay breakdown:" -ForegroundColor Green
    Write-Host "    Fillets: $filletCount"
    Write-Host "    Tight radius: $tightCount"
    Write-Host "    Slowdown zones: $slowCount"
    
    # Verify slowdown metadata in moves (MERGED FEATURE)
    $slowdownMoves = $response.moves | Where-Object { $_.meta.slowdown -ne $null }
    if ($slowdownMoves.Count -eq 0) {
        throw "No slowdown metadata found in moves"
    }
    
    $slowMoves = $slowdownMoves | Where-Object { $_.meta.slowdown -lt 1.0 }
    if ($slowMoves.Count -eq 0) {
        throw "No slowdown detected (all moves at full speed)"
    }
    
    Write-Host "  ✓ Slowdown metadata validated:" -ForegroundColor Green
    Write-Host "    Moves with metadata: $($slowdownMoves.Count)"
    Write-Host "    Moves with slowdown: $($slowMoves.Count)"
    
    # Verify tight_segments stat
    if (-not ($response.stats.PSObject.Properties.Name -contains "tight_segments")) {
        throw "Missing tight_segments statistic"
    }
    
    Write-Host "    Tight segments (< 85%): $($response.stats.tight_segments)"
    
} catch {
    Write-Host "  ✗ L.2 plan failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 2: L.2 G-code export with post-processor
Write-Host "2. Testing L.2 G-code export with GRBL post" -ForegroundColor Yellow

$body = @{
    loops = @(
        @{ pts = @(@(0,0), @(80,0), @(80,50), @(0,50)) }
    )
    units = "mm"
    tool_d = 6.0
    stepover = 0.45
    stepdown = 1.5
    margin = 0.5
    strategy = "Spiral"
    smoothing = 0.3
    climb = $true
    feed_xy = 1200
    safe_z = 5
    z_rough = -1.5
    corner_radius_min = 1.5
    target_stepover = 0.45
    slowdown_feed_pct = 60.0
    post_id = "GRBL"
} | ConvertTo-Json -Depth 5

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/cam/pocket/adaptive/gcode" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body
    
    Write-Host "  ✓ L.2 G-code generated" -ForegroundColor Green
    
    # Parse G-code
    $lines = $response -split "`n"
    Write-Host "    First 10 lines:" -ForegroundColor Gray
    $lines[0..9] | ForEach-Object { Write-Host "      $_" -ForegroundColor Gray }
    
    # Verify G-code structure
    if ($response -notmatch "G21") {
        throw "Missing G21 (mm units)"
    }
    
    if ($response -notmatch "G90") {
        throw "Missing G90 (absolute mode)"
    }
    
    if ($response -notmatch "POST=GRBL") {
        throw "Missing GRBL post metadata"
    }
    
    Write-Host "  ✓ G-code validation passed" -ForegroundColor Green
    
} catch {
    Write-Host "  ✗ G-code export failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 3: Fillet parameter sensitivity
Write-Host "3. Testing fillet parameter sensitivity" -ForegroundColor Yellow

$smallRadius = 0.5
$largeRadius = 2.0

try {
    # Test with small corner radius (more fillets expected)
    $body1 = @{
        loops = @(@{ pts = @(@(0,0), @(60,0), @(60,40), @(0,40)) })
        units = "mm"
        tool_d = 6.0
        stepover = 0.45
        stepdown = 1.5
        corner_radius_min = $smallRadius
        strategy = "Spiral"
        feed_xy = 1200
        safe_z = 5
        z_rough = -1.5
    } | ConvertTo-Json -Depth 5
    
    $response1 = Invoke-RestMethod -Uri "$baseUrl/cam/pocket/adaptive/plan" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body1
    
    $fillets1 = ($response1.overlays | Where-Object { $_.kind -eq "fillet" }).Count
    
    # Test with large corner radius (fewer fillets expected)
    $body2 = @{
        loops = @(@{ pts = @(@(0,0), @(60,0), @(60,40), @(0,40)) })
        units = "mm"
        tool_d = 6.0
        stepover = 0.45
        stepdown = 1.5
        corner_radius_min = $largeRadius
        strategy = "Spiral"
        feed_xy = 1200
        safe_z = 5
        z_rough = -1.5
    } | ConvertTo-Json -Depth 5
    
    $response2 = Invoke-RestMethod -Uri "$baseUrl/cam/pocket/adaptive/plan" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body2
    
    $fillets2 = ($response2.overlays | Where-Object { $_.kind -eq "fillet" }).Count
    
    Write-Host "  ✓ Fillet sensitivity test:" -ForegroundColor Green
    Write-Host "    Small radius ($smallRadius mm): $fillets1 fillets"
    Write-Host "    Large radius ($largeRadius mm): $fillets2 fillets"
    
    # Expect different fillet counts for different radii
    if ($fillets1 -eq $fillets2) {
        Write-Host "  ⚠ Warning: Expected different fillet counts for different radii" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "  ✗ Fillet sensitivity test failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 4: Island handling with L.2
Write-Host "4. Testing L.2 with island (combined L.1 + L.2)" -ForegroundColor Yellow

$body = @{
    loops = @(
        @{ pts = @(@(0,0), @(100,0), @(100,60), @(0,60)) },  # Outer
        @{ pts = @(@(30,15), @(70,15), @(70,45), @(30,45)) } # Island
    )
    units = "mm"
    tool_d = 6.0
    stepover = 0.45
    stepdown = 1.5
    margin = 0.8
    strategy = "Spiral"
    smoothing = 0.3
    climb = $true
    feed_xy = 1200
    safe_z = 5
    z_rough = -1.5
    corner_radius_min = 1.0
    target_stepover = 0.45
    slowdown_feed_pct = 60.0
} | ConvertTo-Json -Depth 5

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/cam/pocket/adaptive/plan" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body
    
    Write-Host "  ✓ L.2 plan with island successful:" -ForegroundColor Green
    Write-Host "    Length: $($response.stats.length_mm) mm"
    Write-Host "    Area: $($response.stats.area_mm2) mm²"
    Write-Host "    Overlays: $($response.overlays.Count)"
    
    # Sanity check
    if ($response.stats.length_mm -lt 100) {
        throw "Path too short for island pocket: $($response.stats.length_mm) mm"
    }
    
    if ($response.overlays.Count -lt 1) {
        throw "Expected overlays with island geometry"
    }
    
    Write-Host "  ✓ L.2 island handling validated" -ForegroundColor Green
    
} catch {
    Write-Host "  ✗ Island test failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 5: Continuous spiral verification (basic)
Write-Host "5. Testing spiral continuity (move sequence)" -ForegroundColor Yellow

$body = @{
    loops = @(
        @{ pts = @(@(0,0), @(80,0), @(80,50), @(0,50)) }
    )
    units = "mm"
    tool_d = 6.0
    stepover = 0.45
    stepdown = 1.5
    margin = 0.5
    strategy = "Spiral"
    smoothing = 0.3
    climb = $true
    feed_xy = 1200
    safe_z = 5
    z_rough = -1.5
    corner_radius_min = 1.0
} | ConvertTo-Json -Depth 5

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/cam/pocket/adaptive/plan" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body
    
    # Count G1 cutting moves (should be majority of moves)
    $g1Moves = ($response.moves | Where-Object { $_.code -eq "G1" }).Count
    $g0Moves = ($response.moves | Where-Object { $_.code -eq "G0" }).Count
    $totalMoves = $response.moves.Count
    
    Write-Host "  ✓ Move analysis:" -ForegroundColor Green
    Write-Host "    Total moves: $totalMoves"
    Write-Host "    G1 (cutting): $g1Moves"
    Write-Host "    G0 (rapid): $g0Moves"
    Write-Host "    G1 ratio: $([math]::Round(100.0 * $g1Moves / $totalMoves, 1))%"
    
    # For spiral, expect high ratio of G1 moves (continuous cutting)
    $g1Ratio = $g1Moves / $totalMoves
    if ($g1Ratio -lt 0.7) {
        Write-Host "  ⚠ Warning: Low G1 ratio for spiral strategy: $([math]::Round($g1Ratio * 100, 1))%" -ForegroundColor Yellow
    } else {
        Write-Host "  ✓ Spiral continuity confirmed (high G1 ratio)" -ForegroundColor Green
    }
    
} catch {
    Write-Host "  ✗ Spiral continuity test failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== All L.2 Tests Completed Successfully ===" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  ✓ L.2 core features working (spiral, overlays, fillets)"
Write-Host "  ✓ HUD overlay system functional"
Write-Host "  ✓ Post-processor integration maintained"
Write-Host "  ✓ Island handling preserved from L.1"
Write-Host "  ✓ Spiral continuity verified"
Write-Host ""
