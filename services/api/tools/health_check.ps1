# Health Check Script for Art Studio v13 API
# Tests the /api/cam_vcarve/preview_infill endpoint
#
# Usage:
#   pwsh -File services/api/tools/health_check.ps1
#   pwsh -File services/api/tools/health_check.ps1 -Port 9000
#   pwsh -File services/api/tools/health_check.ps1 -EnvName .venv

Param(
    [int]$Port = 8088,
    [string]$EnvName = ".venv311"
)

$ErrorActionPreference = "Stop"
$WarningPreference = "SilentlyContinue"

# Resolve paths
$scriptDir = $PSScriptRoot
$apiDir = Split-Path $scriptDir -Parent
$venvPath = Join-Path $apiDir $EnvName
$pythonExe = Join-Path $venvPath "Scripts\python.exe"

Write-Host "==> Art Studio v13 Health Check" -ForegroundColor Cyan
Write-Host ""

# Verify venv exists
if (-not (Test-Path $pythonExe)) {
    Write-Host "❌ ERROR: No venv found at $venvPath" -ForegroundColor Red
    Write-Host "   Run reinstall_api_env.ps1 first:" -ForegroundColor Yellow
    Write-Host "   & `"$scriptDir\reinstall_api_env.ps1`" -Force"
    exit 1
}

Write-Host "✓ Found Python: $pythonExe" -ForegroundColor Green

# Change to API directory (required for uvicorn to find app.main)
Push-Location $apiDir

try {
    Write-Host "==> Starting FastAPI server on port $Port" -ForegroundColor Cyan
    
    # Start uvicorn in background
    $serverJob = Start-Job -ScriptBlock {
        param($pythonPath, $port)
        & $pythonPath -m uvicorn app.main:app --port $port --log-level warning
    } -ArgumentList $pythonExe, $Port
    
    Write-Host "   Server PID: $($serverJob.Id)" -ForegroundColor Gray
    Write-Host "   Waiting 3 seconds for startup..." -ForegroundColor Gray
    Start-Sleep -Seconds 3
    
    # Check if server is still running
    if ($serverJob.State -ne "Running") {
        Write-Host "❌ ERROR: Server failed to start" -ForegroundColor Red
        Receive-Job $serverJob -ErrorAction SilentlyContinue
        exit 1
    }
    
    Write-Host "✓ Server started successfully" -ForegroundColor Green
    Write-Host ""
    
    # Test endpoint
    Write-Host "==> Testing POST /api/cam_vcarve/preview_infill" -ForegroundColor Cyan
    
    $uri = "http://127.0.0.1:$Port/api/cam_vcarve/preview_infill"
    $body = @{
        mode = "raster"
        approx_stroke_width_mm = 1.2
        raster_angle_deg = 45
        flat_stepover_mm = 1.0
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri $uri `
            -Method POST `
            -ContentType "application/json" `
            -Body $body `
            -TimeoutSec 10
        
        Write-Host "✓ Endpoint responded successfully" -ForegroundColor Green
        Write-Host ""
        Write-Host "==> Response Preview:" -ForegroundColor Cyan
        
        # Pretty print first 500 chars of response
        $responseJson = $response | ConvertTo-Json -Depth 3 -Compress
        $preview = if ($responseJson.Length -gt 500) { 
            $responseJson.Substring(0, 500) + "..."
        } else { 
            $responseJson 
        }
        Write-Host $preview -ForegroundColor White
        
        # Check for expected fields
        Write-Host ""
        Write-Host "==> Response Validation:" -ForegroundColor Cyan
        
        $validationPassed = $true
        
        if ($response.PSObject.Properties.Name -contains "svg") {
            Write-Host "  ✓ svg field present" -ForegroundColor Green
        } else {
            Write-Host "  ❌ svg field missing" -ForegroundColor Red
            $validationPassed = $false
        }
        
        if ($response.PSObject.Properties.Name -contains "stats") {
            Write-Host "  ✓ stats field present" -ForegroundColor Green
            
            if ($response.stats.mode -eq "raster") {
                Write-Host "  ✓ mode = raster" -ForegroundColor Green
            } else {
                Write-Host "  ⚠ mode = $($response.stats.mode)" -ForegroundColor Yellow
            }
            
            if ($response.stats.PSObject.Properties.Name -contains "total_len") {
                Write-Host "  ✓ total_len = $($response.stats.total_len)" -ForegroundColor Green
            }
        } else {
            Write-Host "  ❌ stats field missing" -ForegroundColor Red
            $validationPassed = $false
        }
        
        Write-Host ""
        if ($validationPassed) {
            Write-Host "✅ HEALTH CHECK PASSED" -ForegroundColor Green
        } else {
            Write-Host "⚠️ HEALTH CHECK PASSED WITH WARNINGS" -ForegroundColor Yellow
        }
        
    } catch {
        Write-Host "❌ ERROR: Endpoint request failed" -ForegroundColor Red
        Write-Host "   $($_.Exception.Message)" -ForegroundColor Red
        
        # Try to get more details from server job
        Write-Host ""
        Write-Host "==> Server Output:" -ForegroundColor Yellow
        $serverOutput = Receive-Job $serverJob -ErrorAction SilentlyContinue
        if ($serverOutput) {
            Write-Host $serverOutput -ForegroundColor Gray
        } else {
            Write-Host "   (no output captured)" -ForegroundColor Gray
        }
        
        exit 1
    }
    
} finally {
    Write-Host ""
    Write-Host "==> Shutting down server..." -ForegroundColor Cyan
    
    # Stop the job
    if ($serverJob) {
        Stop-Job $serverJob -ErrorAction SilentlyContinue
        Remove-Job $serverJob -Force -ErrorAction SilentlyContinue
    }
    
    # Kill any stray uvicorn processes on this port
    Get-Process | Where-Object { 
        $_.ProcessName -like "python*" -and 
        $_.Path -like "*$EnvName*"
    } | ForEach-Object {
        Write-Host "   Stopping PID $($_.Id)" -ForegroundColor Gray
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    
    # Return to original directory
    Pop-Location
    
    Write-Host "✓ Cleanup complete" -ForegroundColor Green
}

Write-Host ""
Write-Host "==> Health check complete." -ForegroundColor Cyan
