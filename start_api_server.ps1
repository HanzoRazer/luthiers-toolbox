# Simple API Server Startup Script
$ErrorActionPreference = "Stop"

Write-Host "Starting Luthier's Tool Box API Server..." -ForegroundColor Cyan

Push-Location "c:\Users\thepr\Downloads\Luthiers ToolBox\services\api"

# Activate venv
& .\.venv\Scripts\Activate.ps1

# Start server
Write-Host "Server will start on http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

python -m uvicorn app.main:app --reload --port 8000 --host 127.0.0.1

Pop-Location
