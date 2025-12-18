#!/usr/bin/env pwsh
# Test script for Neck Generator API (Les Paul neck generation and DXF export)
# Requires API server running on http://localhost:8000

$ErrorActionPreference = 'Stop'
$base = "http://localhost:8000"

Write-Host "`n=== Testing Neck Generator API ===" -ForegroundColor Cyan

# Test 1: Generate neck geometry (default Les Paul parameters)
Write-Host "`n1. Testing POST /api/neck/generate (default Les Paul)" -ForegroundColor Yellow

$bodyGenerate = @{
    scale_length = 24.75
    nut_width = 1.695
    heel_width = 2.25
    neck_length = 17.0
    neck_angle = 4.0
    fretboard_radius = 12.0
    include_fretboard = $true
    num_frets = 22
    thickness_1st_fret = 0.82
    thickness_12th_fret = 0.92
    radius_at_1st = 0.85
    radius_at_12th = 0.90
    headstock_angle = 14.0
    headstock_length = 7.0
    headstock_thickness = 0.625
    tuner_layout = 2.5
    tuner_diameter = 0.375
    alignment_pin_holes = $false
    units = "in"
    blank_length = 28.0
    blank_width = 3.5
    blank_thickness = 1.0
    fretboard_offset = 0.0
} | ConvertTo-Json -Compress

try {
    $resp = Invoke-RestMethod -Uri "$base/api/neck/generate" -Method Post `
        -ContentType "application/json" -Body $bodyGenerate

    Write-Host "  ✓ Geometry generated:" -ForegroundColor Green
    Write-Host "    Units: $($resp.units)"
    Write-Host "    Scale Length: $($resp.scale_length) in"
    Write-Host "    Profile Points: $($resp.profile_points.Count)"
    Write-Host "    Fret Positions: $($resp.fret_positions.Count)"
    Write-Host "    Headstock Points: $($resp.headstock_points.Count)"
    Write-Host "    Tuner Holes: $($resp.tuner_holes.Count)"

    if ($resp.fret_positions.Count -ne 22) {
        Write-Host "  ✗ Expected 22 frets, got $($resp.fret_positions.Count)" -ForegroundColor Red
        exit 1
    }

    # Verify FretFind2D formula (12th fret should be at half scale length)
    $fret12 = $resp.fret_positions[11]  # 0-indexed
    $expectedFret12 = 24.75 / 2
    $tolerance = 0.1
    if ([Math]::Abs($fret12 - $expectedFret12) -gt $tolerance) {
        Write-Host "  ✗ Fret 12 position incorrect: $fret12 (expected ~$expectedFret12)" -ForegroundColor Red
        exit 1
    } else {
        Write-Host "    ✓ Fret 12 @ $($fret12.ToString('F2'))in (correct octave position)" -ForegroundColor Green
    }

} catch {
    Write-Host "  ✗ Generate failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 2: Export DXF
Write-Host "`n2. Testing POST /api/neck/export_dxf" -ForegroundColor Yellow

$outFile = "test_neck_output.dxf"
try {
    # Use same body as generate endpoint
    $headers = @{
        "Content-Type" = "application/json"
    }
    
    Invoke-WebRequest -Uri "$base/api/neck/export_dxf" -Method Post `
        -Headers $headers -Body $bodyGenerate -OutFile $outFile

    if (Test-Path $outFile) {
        $size = (Get-Item $outFile).Length
        Write-Host "  ✓ DXF exported: $outFile ($size bytes)" -ForegroundColor Green

        # Check DXF content for required layers
        $content = Get-Content $outFile -Raw
        $requiredLayers = @("NECK_PROFILE", "FRETBOARD", "FRET_SLOTS", "HEADSTOCK", "TUNER_HOLES", "CENTERLINE")
        $missingLayers = @()

        foreach ($layer in $requiredLayers) {
            if ($content -notmatch $layer) {
                $missingLayers += $layer
            }
        }

        if ($missingLayers.Count -eq 0) {
            Write-Host "    ✓ All required layers found" -ForegroundColor Green
        } else {
            Write-Host "    ✗ Missing layers: $($missingLayers -join ', ')" -ForegroundColor Red
            exit 1
        }

        # Check for Les Paul metadata
        if ($content -match "Les Paul Neck") {
            Write-Host "    ✓ Metadata comment found" -ForegroundColor Green
        }

        # Cleanup
        Remove-Item $outFile -ErrorAction SilentlyContinue

    } else {
        Write-Host "  ✗ DXF file not created" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  ✗ DXF export failed: $($_.Exception.Message)" -ForegroundColor Red
    Remove-Item $outFile -ErrorAction SilentlyContinue
    exit 1
}

# Test 3: Generate with mm units
Write-Host "`n3. Testing POST /api/neck/generate (millimeters)" -ForegroundColor Yellow

$bodyMM = @{
    scale_length = 24.75
    nut_width = 1.695
    heel_width = 2.25
    neck_length = 17.0
    units = "mm"  # Convert to mm
    include_fretboard = $true
    num_frets = 22
    thickness_1st_fret = 0.82
    thickness_12th_fret = 0.92
    headstock_angle = 14.0
    headstock_length = 7.0
    tuner_diameter = 0.375
    blank_length = 28.0
    blank_width = 3.5
    blank_thickness = 1.0
    fretboard_radius = 12.0
    fretboard_offset = 0.0
    neck_angle = 4.0
    radius_at_1st = 0.85
    radius_at_12th = 0.90
    headstock_thickness = 0.625
    tuner_layout = 2.5
    alignment_pin_holes = $false
} | ConvertTo-Json -Compress

try {
    $resp = Invoke-RestMethod -Uri "$base/api/neck/generate" -Method Post `
        -ContentType "application/json" -Body $bodyMM

    Write-Host "  ✓ MM geometry generated:" -ForegroundColor Green
    Write-Host "    Units: $($resp.units)"
    Write-Host "    Scale Length: $($resp.scale_length.ToString('F1')) mm"

    # Verify conversion (24.75" = 628.65mm)
    $expectedScaleMM = 24.75 * 25.4
    if ([Math]::Abs($resp.scale_length - $expectedScaleMM) -gt 1.0) {
        Write-Host "  ✗ Unit conversion incorrect" -ForegroundColor Red
        exit 1
    } else {
        Write-Host "    ✓ Unit conversion correct (~628.65mm)" -ForegroundColor Green
    }

} catch {
    Write-Host "  ✗ MM generate failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 4: Get presets
Write-Host "`n4. Testing GET /api/neck/presets" -ForegroundColor Yellow

try {
    $resp = Invoke-RestMethod -Uri "$base/api/neck/presets" -Method Get

    if ($resp.presets.Count -ge 3) {
        Write-Host "  ✓ Presets loaded: $($resp.presets.Count) configurations" -ForegroundColor Green
        foreach ($preset in $resp.presets) {
            Write-Host "    - $($preset.name)"
        }
    } else {
        Write-Host "  ✗ Expected at least 3 presets" -ForegroundColor Red
        exit 1
    }

} catch {
    Write-Host "  ✗ Presets failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== All Neck Generator Tests Completed Successfully ===" -ForegroundColor Green
Write-Host ""
