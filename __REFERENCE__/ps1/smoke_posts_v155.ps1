# Art Studio v15.5 - Smoke Test Script
# 
# Tests all 4 post-processor presets (GRBL, Mach3, Haas, Marlin)
# by generating G-code for a standard 60x25mm rectangle contour.
#
# Usage:
#   .\smoke_posts_v155.ps1                    # Default: localhost:8000
#   .\smoke_posts_v155.ps1 -Port 8135         # Custom port
#   .\smoke_posts_v155.ps1 -SkipStart         # Use existing API server

Param(
    [string]$HostName = "127.0.0.1",
    [int]$Port = 8000,
    [switch]$SkipStart
)

$base = "http://${HostName}:${Port}"
$proc = $null

try {
    # Start API server (unless skipped)
    if (-not $SkipStart) {
        Write-Host "Starting API on port $Port..." -ForegroundColor Cyan
        Push-Location "$PSScriptRoot\services\api"
        $proc = Start-Process pwsh -ArgumentList @(
            '-NoExit',
            '-Command',
            "& {.\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port $Port}"
        ) -PassThru -WindowStyle Hidden
        Pop-Location
        
        Write-Host "Waiting for API to start..." -ForegroundColor Yellow
        Start-Sleep -Seconds 3
        
        # Health check
        try {
            $null = Invoke-RestMethod -Uri "$base/health" -Method GET -TimeoutSec 2
            Write-Host "✓ API is running" -ForegroundColor Green
        } catch {
            Write-Host "⚠ API health check failed, continuing anyway..." -ForegroundColor Yellow
        }
    } else {
        Write-Host "Using existing API at $base" -ForegroundColor Cyan
    }
    
    # Run smoke test
    Write-Host "`n=== Art Studio v15.5 Smoke Test ===" -ForegroundColor Cyan
    Write-Host "Testing endpoint: $base/api/cam_gcode/smoke/posts`n"
    
    $resp = Invoke-RestMethod -Uri "$base/api/cam_gcode/smoke/posts" -Method GET -TimeoutSec 10
    
    # Display results
    Write-Host "Results:" -ForegroundColor White
    $resp.results.PSObject.Properties | ForEach-Object {
        $name = $_.Name
        $result = $_.Value
        
        if ($result.ok) {
            Write-Host "  ✓ $name" -ForegroundColor Green -NoNewline
            Write-Host " - $($result.bytes) bytes"
        } else {
            Write-Host "  ✗ $name" -ForegroundColor Red -NoNewline
            if ($result.error) {
                Write-Host " - Error: $($result.error)"
            } else {
                Write-Host " - Failed"
            }
        }
    }
    
    # Overall status
    Write-Host "`nOverall Status:" -ForegroundColor White
    if ($resp.ok) {
        Write-Host "✓ All presets passed" -ForegroundColor Green
        exit 0
    } else {
        Write-Host "✗ Some presets failed" -ForegroundColor Red
        Write-Host "`nErrors:" -ForegroundColor Yellow
        $resp.errors | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
        exit 1
    }
    
} catch {
    Write-Host "`n✗ Smoke test failed:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    
    if ($_.Exception.InnerException) {
        Write-Host "`nInner Exception:" -ForegroundColor Yellow
        Write-Host $_.Exception.InnerException.Message -ForegroundColor Red
    }
    
    exit 1
    
} finally {
    # Cleanup
    if ($proc -and !$proc.HasExited) {
        Write-Host "`nStopping API server..." -ForegroundColor Yellow
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
}
