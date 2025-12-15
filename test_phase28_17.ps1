# Test Phase 28.17 Cross-Lab Risk Dashboard
# This script helps you quickly test the new component

Write-Host "`n=== Phase 28.17 Testing Script ===" -ForegroundColor Cyan

# Check if file exists
if (Test-Path "packages\client\src\views\art\RiskDashboardCrossLab.vue") {
    Write-Host "✓ Component file exists" -ForegroundColor Green
} else {
    Write-Host "✗ Component file not found!" -ForegroundColor Red
    exit 1
}

# Check if router is updated
$routerContent = Get-Content "client\src\router\index.ts" -Raw
if ($routerContent -match "RiskDashboardCrossLab") {
    Write-Host "✓ Router updated" -ForegroundColor Green
} else {
    Write-Host "✗ Router not updated!" -ForegroundColor Red
    exit 1
}

Write-Host "`n--- Backend Check ---" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/docs" -Method GET -TimeoutSec 2 -ErrorAction Stop
    Write-Host "✓ Backend API is running on port 8000" -ForegroundColor Green
    
    Write-Host "`nTesting API endpoints:" -ForegroundColor Cyan
    try {
        $aggResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/compare/risk_aggregate" -Method GET
        Write-Host "  ✓ /api/compare/risk_aggregate - OK" -ForegroundColor Green
        Write-Host "    Returns: $($aggResponse.Count) buckets" -ForegroundColor Gray
    } catch {
        Write-Host "  ✗ /api/compare/risk_aggregate - Failed: $($_.Exception.Message)" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Backend API not running" -ForegroundColor Red
    Write-Host "`nTo start backend:" -ForegroundColor Yellow
    Write-Host "  cd services\api" -ForegroundColor White
    Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host "  uvicorn app.main:app --reload --port 8000" -ForegroundColor White
}

Write-Host "`n--- Frontend Check ---" -ForegroundColor Yellow
try {
    $frontendResponse = Invoke-WebRequest -Uri "http://localhost:5173" -Method GET -TimeoutSec 2 -ErrorAction Stop
    Write-Host "✓ Frontend dev server is running on port 5173" -ForegroundColor Green
    Write-Host "`nOpen in browser:" -ForegroundColor Cyan
    Write-Host "  http://localhost:5173/cam/risk/crosslab" -ForegroundColor White
} catch {
    Write-Host "✗ Frontend dev server not running" -ForegroundColor Red
    Write-Host "`nTo start frontend:" -ForegroundColor Yellow
    Write-Host "  cd packages\client" -ForegroundColor White
    Write-Host "  npm install  # if first time" -ForegroundColor White
    Write-Host "  npm run dev" -ForegroundColor White
}

Write-Host "`n--- Manual Testing Checklist ---" -ForegroundColor Yellow
Write-Host "Once both servers are running, test these features:" -ForegroundColor Cyan
Write-Host "  [ ] Lane filter works (Rosette, Adaptive, Relief, Pipeline)" -ForegroundColor White
Write-Host "  [ ] Preset filter works (Safe, Standard, Aggressive)" -ForegroundColor White
Write-Host "  [ ] Quick time range chips work (All, 7d, 30d, 90d, year)" -ForegroundColor White
Write-Host "  [ ] Lane preset chips work (one-click filters)" -ForegroundColor White
Write-Host "  [ ] Save view with name/description/tags" -ForegroundColor White
Write-Host "  [ ] Load saved view by clicking name" -ForegroundColor White
Write-Host "  [ ] Search saved views" -ForegroundColor White
Write-Host "  [ ] Filter by tag" -ForegroundColor White
Write-Host "  [ ] Export views to JSON" -ForegroundColor White
Write-Host "  [ ] Import views from JSON" -ForegroundColor White
Write-Host "  [ ] URL updates when filters change" -ForegroundColor White
Write-Host "  [ ] Refresh button reloads data" -ForegroundColor White
Write-Host "  [ ] Clear filters button works" -ForegroundColor White
Write-Host "  [ ] Risk buckets table displays" -ForegroundColor White
Write-Host "  [ ] Sparklines render correctly" -ForegroundColor White
Write-Host "  [ ] Click 'Details' shows bucket entries" -ForegroundColor White
Write-Host "  [ ] Export CSV for aggregates" -ForegroundColor White
Write-Host "  [ ] Export CSV for bucket details" -ForegroundColor White
Write-Host "  [ ] Download JSON snapshot" -ForegroundColor White
Write-Host "  [ ] Recently used views show up" -ForegroundColor White
Write-Host "  [ ] Set default view works" -ForegroundColor White
Write-Host "  [ ] Rename/duplicate/delete views work" -ForegroundColor White

Write-Host "`n--- Quick Start Commands ---" -ForegroundColor Yellow
Write-Host "# Terminal 1 (Backend):" -ForegroundColor Cyan
Write-Host "cd services\api && .\.venv\Scripts\Activate.ps1 && uvicorn app.main:app --reload" -ForegroundColor White
Write-Host "`n# Terminal 2 (Frontend):" -ForegroundColor Cyan
Write-Host "cd packages\client && npm run dev" -ForegroundColor White
Write-Host "`n# Browser:" -ForegroundColor Cyan
Write-Host "http://localhost:5173/cam/risk/crosslab" -ForegroundColor White

Write-Host ""
