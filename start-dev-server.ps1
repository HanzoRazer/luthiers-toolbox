# Luthier's Tool Box - Start Development Server
# This script starts the Vite dev server for frontend development

Write-Host "`n=== Luthier's Tool Box Development Server ===" -ForegroundColor Cyan
Write-Host ""

# Check if Node.js is installed
try {
    $nodeVersion = node --version 2>$null
    $npmVersion = npm --version 2>$null
    
    if ($nodeVersion -and $npmVersion) {
        Write-Host "✅ Node.js: $nodeVersion" -ForegroundColor Green
        Write-Host "✅ npm: $npmVersion" -ForegroundColor Green
    } else {
        throw "Node.js or npm not found"
    }
} catch {
    Write-Host "❌ Node.js is not installed or not in PATH" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Node.js from: https://nodejs.org" -ForegroundColor Yellow
    Write-Host "Then open a NEW PowerShell window and run this script again." -ForegroundColor Yellow
    Write-Host ""
    pause
    exit 1
}

Write-Host ""

# Navigate to client directory
$clientPath = Join-Path $PSScriptRoot "client"
if (-not (Test-Path $clientPath)) {
    Write-Host "❌ Client directory not found: $clientPath" -ForegroundColor Red
    pause
    exit 1
}

Set-Location $clientPath
Write-Host "📁 Working directory: $clientPath" -ForegroundColor Gray
Write-Host ""

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Installing dependencies (first time setup)..." -ForegroundColor Yellow
    npm install
    Write-Host ""
}

# Start Vite dev server
Write-Host "🚀 Starting Vite Development Server..." -ForegroundColor Green
Write-Host ""
Write-Host "   Frontend: " -NoNewline -ForegroundColor White
Write-Host "http://localhost:5173" -ForegroundColor Cyan
Write-Host "   Backend:  " -NoNewline -ForegroundColor White
Write-Host "http://localhost:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "   Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

npm run dev
