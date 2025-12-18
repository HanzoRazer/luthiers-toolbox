# Luthier's Tool Box - Monorepo Quick Start
Write-Host "🚀 Luthier's Tool Box - Monorepo Quick Start" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
if (-Not (Test-Path "pnpm-workspace.yaml")) {
    Write-Host "❌ Error: pnpm-workspace.yaml not found" -ForegroundColor Red
    Write-Host "Please run this script from the repository root"
    exit 1
}

Write-Host "📦 Step 1: Installing API dependencies..." -ForegroundColor Yellow
Set-Location services\api

if (-Not (Test-Path ".venv")) {
    Write-Host "   Creating virtual environment..."
    python -m venv .venv
}

Write-Host "   Activating virtual environment..."
.\.venv\Scripts\Activate.ps1

Write-Host "   Installing requirements..."
pip install -q -r requirements.txt

Write-Host ""
Write-Host "✓ API dependencies installed" -ForegroundColor Green
Write-Host ""
Write-Host "🎯 Step 2: Starting API server..." -ForegroundColor Yellow
Write-Host "   Server will run at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "   API docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "   Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

uvicorn app.main:app --reload --port 8000
