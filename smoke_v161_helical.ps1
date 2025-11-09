#!/usr/bin/env pwsh
# Smoke Test: Art Studio v16.1 - Helical Z-Ramping
# Tests both helical endpoints with G2/G3 validation

$ErrorActionPreference = 'Stop'
$API_BASE = "http://localhost:8000"

Write-Host "`n=== Art Studio v16.1 Helical Z-Ramping Smoke Test ===" -ForegroundColor Cyan

# Test 1: Health check
Write-Host "`n[1/7] Testing GET /api/cam/toolpath/helical_health..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$API_BASE/api/cam/toolpath/helical_health" -Method Get
    if ($health.status -eq "ok" -and $health.module -eq "helical_v161") {
        Write-Host "  ✓ Health check passed" -ForegroundColor Green
        Write-Host "    Module: $($health.module)" -ForegroundColor Gray
        Write-Host "    Status: $($health.status)" -ForegroundColor Gray
    } else {
        throw "Invalid health response: $($health | ConvertTo-Json -Compress)"
    }
} catch {
    Write-Host "  ✗ Health check failed: $_" -ForegroundColor Red
    exit 1
}

# Test 2: Basic helical entry (CW, G2)
Write-Host "`n[2/7] Testing POST /api/cam/toolpath/helical_entry (CW/G2)..." -ForegroundColor Yellow
$body = @{
    cx = 50.0
    cy = 50.0
    radius = 10.0
    direction = "CW"
    z_plane = 5.0
    z_start = 0.0
    z_target = -6.0
    pitch = 2.0
    feed_xy = 1200
    feed_z = 600
    ij_mode = $true
    safe_rapid = $true
    max_arc_deg = 90
} | ConvertTo-Json

try {
    $result = Invoke-RestMethod -Uri "$API_BASE/api/cam/toolpath/helical_entry" -Method Post `
        -ContentType "application/json" -Body $body
    
    if ($result.gcode -and $result.stats) {
        Write-Host "  ✓ CW helical entry generated" -ForegroundColor Green
        Write-Host "    Revolutions: $($result.stats.revs)" -ForegroundColor Gray
        Write-Host "    Segments: $($result.stats.segments)" -ForegroundColor Gray
        Write-Host "    G-code length: $($result.gcode.Length) chars" -ForegroundColor Gray
        
        # Validate G2 arc commands present
        if ($result.gcode -match "G2") {
            Write-Host "    ✓ G2 (CW) arc commands found" -ForegroundColor Green
        } else {
            throw "No G2 commands in CW helical output"
        }
        
        # Validate Z interpolation
        if ($result.gcode -match "Z-") {
            Write-Host "    ✓ Z descent interpolation found" -ForegroundColor Green
        } else {
            throw "No Z interpolation in helical output"
        }
    } else {
        throw "Invalid response: missing gcode or stats"
    }
} catch {
    Write-Host "  ✗ CW helical entry failed: $_" -ForegroundColor Red
    exit 1
}

# Test 3: CCW helical entry (G3)
Write-Host "`n[3/7] Testing POST /api/cam/toolpath/helical_entry (CCW/G3)..." -ForegroundColor Yellow
$body_ccw = @{
    cx = 60.0
    cy = 60.0
    radius = 8.0
    direction = "CCW"
    z_plane = 5.0
    z_start = 0.0
    z_target = -4.0
    pitch = 1.5
    feed_xy = 1000
    feed_z = 500
    ij_mode = $true
    safe_rapid = $true
    max_arc_deg = 60
} | ConvertTo-Json

try {
    $result_ccw = Invoke-RestMethod -Uri "$API_BASE/api/cam/toolpath/helical_entry" -Method Post `
        -ContentType "application/json" -Body $body_ccw
    
    if ($result_ccw.gcode -and $result_ccw.stats) {
        Write-Host "  ✓ CCW helical entry generated" -ForegroundColor Green
        Write-Host "    Revolutions: $($result_ccw.stats.revs)" -ForegroundColor Gray
        Write-Host "    Segments: $($result_ccw.stats.segments)" -ForegroundColor Gray
        
        # Validate G3 arc commands
        if ($result_ccw.gcode -match "G3") {
            Write-Host "    ✓ G3 (CCW) arc commands found" -ForegroundColor Green
        } else {
            throw "No G3 commands in CCW helical output"
        }
    } else {
        throw "Invalid CCW response: missing gcode or stats"
    }
} catch {
    Write-Host "  ✗ CCW helical entry failed: $_" -ForegroundColor Red
    exit 1
}

# Test 4: IJ mode validation
Write-Host "`n[4/7] Testing IJ mode (I,J center offsets)..." -ForegroundColor Yellow
$body_ij = @{
    cx = 40.0
    cy = 40.0
    radius = 12.0
    direction = "CW"
    z_plane = 3.0
    z_start = 0.0
    z_target = -5.0
    pitch = 2.5
    feed_xy = 1500
    ij_mode = $true
    safe_rapid = $false
    max_arc_deg = 45
} | ConvertTo-Json

try {
    $result_ij = Invoke-RestMethod -Uri "$API_BASE/api/cam/toolpath/helical_entry" -Method Post `
        -ContentType "application/json" -Body $body_ij
    
    # Validate I and J parameters present
    if ($result_ij.gcode -match "I[-\d]" -and $result_ij.gcode -match "J[-\d]") {
        Write-Host "  ✓ IJ mode validated (I,J offset params found)" -ForegroundColor Green
    } else {
        throw "IJ mode enabled but no I,J parameters in G-code"
    }
} catch {
    Write-Host "  ✗ IJ mode test failed: $_" -ForegroundColor Red
    exit 1
}

# Test 5: R word mode validation
Write-Host "`n[5/7] Testing R word mode (arc radius)..." -ForegroundColor Yellow
$body_r = @{
    cx = 70.0
    cy = 30.0
    radius = 15.0
    direction = "CCW"
    z_plane = 4.0
    z_start = 0.0
    z_target = -8.0
    pitch = 3.0
    feed_xy = 1300
    ij_mode = $false
    safe_rapid = $true
    max_arc_deg = 90
} | ConvertTo-Json

try {
    $result_r = Invoke-RestMethod -Uri "$API_BASE/api/cam/toolpath/helical_entry" -Method Post `
        -ContentType "application/json" -Body $body_r
    
    # Validate R parameter present (not I,J)
    if ($result_r.gcode -match "R\d") {
        Write-Host "  ✓ R word mode validated (R radius param found)" -ForegroundColor Green
    } else {
        throw "R word mode enabled but no R parameter in G-code"
    }
    
    # Ensure no I,J parameters leak through
    if ($result_r.gcode -match "I[-\d]" -or $result_r.gcode -match "J[-\d]") {
        throw "R word mode but I,J parameters present (mode leak)"
    }
} catch {
    Write-Host "  ✗ R word mode test failed: $_" -ForegroundColor Red
    exit 1
}

# Test 6: Safe rapid validation
Write-Host "`n[6/7] Testing safe rapid to clearance plane..." -ForegroundColor Yellow
$body_rapid = @{
    cx = 30.0
    cy = 70.0
    radius = 6.0
    direction = "CW"
    z_plane = 10.0
    z_start = 0.0
    z_target = -3.0
    pitch = 1.0
    feed_xy = 800
    safe_rapid = $true
    ij_mode = $true
    max_arc_deg = 60
} | ConvertTo-Json

try {
    $result_rapid = Invoke-RestMethod -Uri "$API_BASE/api/cam/toolpath/helical_entry" -Method Post `
        -ContentType "application/json" -Body $body_rapid
    
    # Validate G0 rapid to Z plane at start
    if ($result_rapid.gcode -match "G0.*Z10\.0") {
        Write-Host "  ✓ Safe rapid to clearance plane found (G0 Z10.0)" -ForegroundColor Green
    } else {
        throw "Safe rapid enabled but no G0 to Z plane in output"
    }
} catch {
    Write-Host "  ✗ Safe rapid test failed: $_" -ForegroundColor Red
    exit 1
}

# Test 7: Arc segmentation validation
Write-Host "`n[7/7] Testing arc segmentation (max_arc_deg)..." -ForegroundColor Yellow
$body_seg = @{
    cx = 55.0
    cy = 45.0
    radius = 10.0
    direction = "CW"
    z_plane = 5.0
    z_start = 0.0
    z_target = -6.0
    pitch = 2.0
    feed_xy = 1200
    ij_mode = $true
    safe_rapid = $true
    max_arc_deg = 30  # Force smaller segments
} | ConvertTo-Json

try {
    $result_seg = Invoke-RestMethod -Uri "$API_BASE/api/cam/toolpath/helical_entry" -Method Post `
        -ContentType "application/json" -Body $body_seg
    
    # Count arc commands (G2/G3)
    $arc_count = ([regex]::Matches($result_seg.gcode, "G[23]")).Count
    
    if ($arc_count -ge 12) {  # 360°/30° = 12 segs/rev, 3 revs = 36 total
        Write-Host "  ✓ Arc segmentation validated ($arc_count arc commands)" -ForegroundColor Green
        Write-Host "    Expected ~36 segments (3 revs × 12 segs/rev)" -ForegroundColor Gray
    } else {
        throw "Arc segmentation failed: only $arc_count arcs (expected ≥12)"
    }
} catch {
    Write-Host "  ✗ Arc segmentation test failed: $_" -ForegroundColor Red
    exit 1
}

# Summary
Write-Host "`n=== All Art Studio v16.1 Helical Tests Passed ===" -ForegroundColor Green
Write-Host "Validated:" -ForegroundColor Cyan
Write-Host "  ✓ Health check endpoint" -ForegroundColor Gray
Write-Host "  ✓ CW helical entry (G2)" -ForegroundColor Gray
Write-Host "  ✓ CCW helical entry (G3)" -ForegroundColor Gray
Write-Host "  ✓ IJ mode (I,J center offsets)" -ForegroundColor Gray
Write-Host "  ✓ R word mode (arc radius)" -ForegroundColor Gray
Write-Host "  ✓ Safe rapid to clearance plane" -ForegroundColor Gray
Write-Host "  ✓ Arc segmentation (max_arc_deg)" -ForegroundColor Gray

Write-Host "`nModule Status: Ready for production" -ForegroundColor Green
exit 0
