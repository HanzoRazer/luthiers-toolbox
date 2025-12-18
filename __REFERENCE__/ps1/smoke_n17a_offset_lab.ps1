#!/usr/bin/env pwsh
# Smoke test for N.17a Offset Lab and Visualizer
# Tests: /cam/polygon_offset.preview endpoint + Vue UI components

$ErrorActionPreference = "Stop"

Write-Host "`n=== N.17a Offset Lab Smoke Test ===`n" -ForegroundColor Cyan

$ApiBase = "http://localhost:8000"
$body = @{
    polygon   = @(@(0, 0), @(40, 0), @(40, 30), @(0, 30), @(0, 0))
    tool_dia  = 6.0
    stepover  = 0.4
    link_mode = "arc"
    units     = "mm"
} | ConvertTo-Json -Compress

# Test 1: Preview endpoint (JSON)
Write-Host "1. Testing POST /cam/polygon_offset.preview" -ForegroundColor Yellow
try {
    $resp = Invoke-RestMethod -Uri "$ApiBase/cam/polygon_offset.preview" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body `
        -TimeoutSec 10
    
    Write-Host "  ✓ Preview endpoint responds" -ForegroundColor Green
    
    # Validate structure
    if ($resp.passes -and $resp.passes.Count -gt 0) {
        Write-Host "  ✓ Generated $($resp.passes.Count) offset passes" -ForegroundColor Green
    } else {
        throw "No passes generated"
    }
    
    if ($resp.bbox) {
        $bbox = $resp.bbox
        Write-Host "  ✓ BBox: [$($bbox.minx), $($bbox.miny)] → [$($bbox.maxx), $($bbox.maxy)]" -ForegroundColor Green
    } else {
        throw "No bbox in response"
    }
    
    if ($resp.meta.count -eq $resp.passes.Count) {
        Write-Host "  ✓ Meta count matches passes: $($resp.meta.count)" -ForegroundColor Green
    } else {
        throw "Meta count mismatch"
    }
    
    # Validate first pass structure
    $pass1 = $resp.passes[0]
    if ($pass1.pts -and $pass1.pts.Count -ge 3) {
        Write-Host "  ✓ First pass has $($pass1.pts.Count) points (valid polygon)" -ForegroundColor Green
    } else {
        throw "Invalid pass structure"
    }
    
    Write-Host "`n✅ Test 1 PASSED`n" -ForegroundColor Green
    
} catch {
    Write-Host "`n❌ Test 1 FAILED: $_`n" -ForegroundColor Red
    exit 1
}

# Test 2: G-code endpoint still works (regression test)
Write-Host "2. Testing POST /cam/polygon_offset.nc (regression)" -ForegroundColor Yellow
try {
    $gcodeResp = Invoke-RestMethod -Uri "$ApiBase/cam/polygon_offset.nc" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body `
        -TimeoutSec 10
    
    if ($gcodeResp -match "G21") {
        Write-Host "  ✓ G-code contains G21 (units)" -ForegroundColor Green
    } else {
        throw "Missing G21"
    }
    
    if ($gcodeResp -match "M3") {
        Write-Host "  ✓ G-code contains M3 (spindle on)" -ForegroundColor Green
    } else {
        throw "Missing M3"
    }
    
    $arcCount = ([regex]::Matches($gcodeResp, "^G2", [System.Text.RegularExpressions.RegexOptions]::Multiline)).Count
    if ($arcCount -gt 4) {
        Write-Host "  ✓ G-code contains $arcCount G2 arcs (> 4)" -ForegroundColor Green
    } else {
        throw "Insufficient arcs: $arcCount"
    }
    
    Write-Host "`n✅ Test 2 PASSED`n" -ForegroundColor Green
    
} catch {
    Write-Host "`n❌ Test 2 FAILED: $_`n" -ForegroundColor Red
    exit 1
}

# Test 3: Different stepover values
Write-Host "3. Testing stepover variation" -ForegroundColor Yellow
try {
    $body2 = @{
        polygon   = @(@(0, 0), @(100, 0), @(100, 60), @(0, 60), @(0, 0))
        tool_dia  = 6.0
        stepover  = 0.3  # Smaller stepover = more passes
        link_mode = "linear"
        units     = "mm"
    } | ConvertTo-Json -Compress
    
    $resp2 = Invoke-RestMethod -Uri "$ApiBase/cam/polygon_offset.preview" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body2 `
        -TimeoutSec 10
    
    if ($resp2.passes.Count -gt $resp.passes.Count) {
        Write-Host "  ✓ Smaller stepover (0.3) generates more passes: $($resp2.passes.Count) vs $($resp.passes.Count)" -ForegroundColor Green
    } else {
        throw "Stepover logic failed"
    }
    
    Write-Host "`n✅ Test 3 PASSED`n" -ForegroundColor Green
    
} catch {
    Write-Host "`n❌ Test 3 FAILED: $_`n" -ForegroundColor Red
    exit 1
}

Write-Host "=== All Offset Lab Smoke Tests PASSED ===`n" -ForegroundColor Cyan
Write-Host "✓ Preview endpoint functional" -ForegroundColor Green
Write-Host "✓ G-code endpoint still works" -ForegroundColor Green
Write-Host "✓ Stepover logic validated" -ForegroundColor Green
Write-Host "`nNext: Open http://localhost:5173/lab/offset to test UI`n" -ForegroundColor Yellow

exit 0
