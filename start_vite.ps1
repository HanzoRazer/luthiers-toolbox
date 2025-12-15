#!/usr/bin/env pwsh
# Start Vite dev server and keep it running

Write-Host "Starting Vite dev server..." -ForegroundColor Cyan
Set-Location "C:\Users\thepr\Downloads\Luthiers ToolBox\client"

try {
    npm run dev
} catch {
    Write-Host "Error starting Vite: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
}
