# CAM Dashboard - Local Test Script
#
# Starts a local web server and opens the dashboard in your browser.
# Tests the dashboard with sample data.
#
# Usage: .\test_dashboard.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== CAM Dashboard Local Test ===" -ForegroundColor Cyan
Write-Host "Starting local web server...`n"

# Check if Python is available
try {
    $pythonCmd = Get-Command python -ErrorAction Stop
} catch {
    Write-Host "✗ Python not found. Please install Python 3.x" -ForegroundColor Red
    exit 1
}

# Navigate to dashboard directory
$dashboardPath = Join-Path $PSScriptRoot "public_badges"

if (-not (Test-Path $dashboardPath)) {
    Write-Host "✗ Dashboard directory not found: $dashboardPath" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path (Join-Path $dashboardPath "index.html"))) {
    Write-Host "✗ index.html not found in $dashboardPath" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path (Join-Path $dashboardPath "badges.json"))) {
    Write-Host "⚠ badges.json not found, dashboard will show error" -ForegroundColor Yellow
    Write-Host "  (This is OK for testing dashboard error handling)`n" -ForegroundColor Gray
}

Push-Location $dashboardPath

try {
    Write-Host "Dashboard location: $dashboardPath" -ForegroundColor Green
    Write-Host "Server URL: http://localhost:8080`n" -ForegroundColor Green
    
    Write-Host "Features to test:" -ForegroundColor White
    Write-Host "  ✓ Status pills (Smoke/SizeGate)" -ForegroundColor Gray
    Write-Host "  ✓ Color chips (green/orange/yellow/red)" -ForegroundColor Gray
    Write-Host "  ✓ Sortable columns (click headers)" -ForegroundColor Gray
    Write-Host "  ✓ Filter presets (type in search box)" -ForegroundColor Gray
    Write-Host "  ✓ Delta bars (visual % change)" -ForegroundColor Gray
    Write-Host "  ✓ Export CSV button" -ForegroundColor Gray
    Write-Host "  ✓ Refresh button`n" -ForegroundColor Gray
    
    Write-Host "Opening browser..." -ForegroundColor Cyan
    Start-Sleep -Seconds 1
    Start-Process "http://localhost:8080"
    
    Write-Host "`nServer running. Press Ctrl+C to stop." -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Gray
    
    # Start HTTP server
    python -m http.server 8080
    
} catch {
    Write-Host "`n✗ Server failed:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
    
} finally {
    Pop-Location
}
