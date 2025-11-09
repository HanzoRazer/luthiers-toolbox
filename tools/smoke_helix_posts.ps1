# smoke_helix_posts.ps1
# Smoke test for helical ramping with all post-processor presets
# Tests: GRBL, Mach3, Haas, Marlin

$ErrorActionPreference = "Stop"

$ApiBase = "http://127.0.0.1:8000"
$Presets = @("GRBL", "Mach3", "Haas", "Marlin")

Write-Host "=== Helical Post-Processor Presets Smoke Test ===" -ForegroundColor Cyan
Write-Host "Testing against: $ApiBase" -ForegroundColor Gray
Write-Host ""

# Base request body (shared across all presets)
$BodyBase = @{
    cx = 0
    cy = 0
    radius_mm = 6.0
    direction = "CCW"
    plane_z_mm = 5.0
    start_z_mm = 0.0
    z_target_mm = -3.0
    pitch_mm_per_rev = 1.5
    feed_xy_mm_min = 600
    ij_mode = $true
    absolute = $true
    units_mm = $true
    safe_rapid = $true
    dwell_ms = 0
    max_arc_degrees = 180
}

$AllPassed = $true
$Results = @{}

foreach ($preset in $Presets) {
    Write-Host "[Testing] $preset..." -ForegroundColor Yellow -NoNewline
    
    # Clone base body and add preset
    $body = $BodyBase.Clone()
    $body["post_preset"] = $preset
    
    try {
        $response = Invoke-RestMethod -Method Post `
            -Uri "$ApiBase/api/cam/toolpath/helical_entry" `
            -Body ($body | ConvertTo-Json -Depth 5) `
            -ContentType "application/json" `
            -TimeoutSec 10
        
        $gcode = $response.gcode
        $stats = $response.stats
        
        if ([string]::IsNullOrWhiteSpace($gcode)) {
            Write-Host " [FAIL] Empty gcode" -ForegroundColor Red
            $AllPassed = $false
            continue
        }
        
        # Validate preset-specific features
        $valid = $true
        
        if ($preset -eq "Haas") {
            # Haas should use R-mode arcs and G4 S (seconds)
            if ($gcode -notmatch "R\d+\.") {
                Write-Host " [WARN] Expected R-mode arcs for Haas" -ForegroundColor Yellow
            }
            if ($body["dwell_ms"] -gt 0 -and $gcode -notmatch "G4 S") {
                Write-Host " [WARN] Expected G4 S (seconds) for Haas" -ForegroundColor Yellow
            }
        } else {
            # GRBL, Mach3, Marlin should use I,J mode
            if ($gcode -notmatch "[IJ]-?\d+\.") {
                Write-Host " [WARN] Expected I,J arcs for $preset" -ForegroundColor Yellow
            }
        }
        
        # Check for post preset comment
        if ($gcode -notmatch "Post preset: $preset") {
            Write-Host " [WARN] Missing post preset comment" -ForegroundColor Yellow
        }
        
        # Success
        $segments = $stats.segments
        $arcMode = $stats.arc_mode
        $bytes = $gcode.Length
        
        # Store result for badge generation
        $Results[$preset] = @{
            bytes = $bytes
            segments = $segments
            arc_mode = $arcMode
        }
        
        Write-Host " [OK] $bytes bytes, $segments segments, arc_mode=$arcMode" -ForegroundColor Green
        
    } catch {
        Write-Host " [ERR] $($_.Exception.Message)" -ForegroundColor Red
        $AllPassed = $false
    }
}

Write-Host ""

# Save results to JSON for badge generation
if ($Results.Count -gt 0) {
    $ReportsDir = "reports"
    if (-not (Test-Path $ReportsDir)) {
        New-Item -ItemType Directory -Path $ReportsDir | Out-Null
    }
    
    $ResultsPath = Join-Path $ReportsDir "helical_smoke_posts.json"
    $Results | ConvertTo-Json -Depth 3 | Set-Content $ResultsPath -Encoding UTF8
    Write-Host "✅ Saved smoke results to $ResultsPath" -ForegroundColor Cyan
    Write-Host ""
}

if ($AllPassed) {
    Write-Host "=== All presets passed ===" -ForegroundColor Green
    exit 0
} else {
    Write-Host "=== Some presets failed ===" -ForegroundColor Red
    exit 2
}
