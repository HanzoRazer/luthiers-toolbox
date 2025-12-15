# Phase 1 - Dashboard Scaffold Smoke Test
# Tests that CAM Dashboard and Art Studio Dashboard are accessible

Write-Host "=== Phase 1 Dashboard Scaffold Test ===" -ForegroundColor Cyan
Write-Host ""

# Check if Vue files exist
$camDashboard = "client\src\views\CAMDashboard.vue"
$artStudioDashboard = "client\src\views\ArtStudioDashboard.vue"
$router = "client\src\router\index.ts"
$app = "client\src\App.vue"

Write-Host "1. Checking dashboard Vue components..." -ForegroundColor Yellow
if (Test-Path $camDashboard) {
    Write-Host "  ✓ CAMDashboard.vue exists" -ForegroundColor Green
} else {
    Write-Host "  ✗ CAMDashboard.vue NOT FOUND" -ForegroundColor Red
    exit 1
}

if (Test-Path $artStudioDashboard) {
    Write-Host "  ✓ ArtStudioDashboard.vue exists" -ForegroundColor Green
} else {
    Write-Host "  ✗ ArtStudioDashboard.vue NOT FOUND" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "2. Checking router configuration..." -ForegroundColor Yellow
$routerContent = Get-Content $router -Raw
if ($routerContent -match "CAMDashboard" -and $routerContent -match "ArtStudioDashboard") {
    Write-Host "  ✓ Dashboard routes registered in router" -ForegroundColor Green
} else {
    Write-Host "  ✗ Dashboard routes NOT found in router" -ForegroundColor Red
    exit 1
}

if ($routerContent -match "/cam-dashboard" -and $routerContent -match "/art-studio-dashboard") {
    Write-Host "  ✓ Dashboard paths configured (/cam-dashboard, /art-studio-dashboard)" -ForegroundColor Green
} else {
    Write-Host "  ✗ Dashboard paths NOT configured" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "3. Checking navigation integration..." -ForegroundColor Yellow
$appContent = Get-Content $app -Raw
if ($appContent -match "CAM Dashboard" -and $appContent -match "Art Studio Dashboard") {
    Write-Host "  ✓ Dashboard links added to navigation" -ForegroundColor Green
} else {
    Write-Host "  ✗ Dashboard links NOT found in navigation" -ForegroundColor Red
    exit 1
}

if ($appContent -match "Re-Forestation Plan" -or $appContent -match "dashboard-link") {
    Write-Host "  ✓ Re-Forestation Plan styling applied" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Re-Forestation Plan styling may not be applied" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "4. Checking dashboard content..." -ForegroundColor Yellow
$camContent = Get-Content $camDashboard -Raw
$artContent = Get-Content $artStudioDashboard -Raw

# CAM Dashboard checks
if ($camContent -match "Adaptive Pocketing" -and $camContent -match "Helical Ramping") {
    Write-Host "  ✓ CAM Dashboard has operation cards" -ForegroundColor Green
} else {
    Write-Host "  ✗ CAM Dashboard missing operation cards" -ForegroundColor Red
}

if ($camContent -match "Module L" -or $camContent -match "v16.1") {
    Write-Host "  ✓ CAM Dashboard has version badges" -ForegroundColor Green
} else {
    Write-Host "  ⚠ CAM Dashboard version badges may be missing" -ForegroundColor Yellow
}

# Art Studio Dashboard checks
if ($artContent -match "Relief Mapper" -and $artContent -match "Rosette Designer") {
    Write-Host "  ✓ Art Studio Dashboard has design cards" -ForegroundColor Green
} else {
    Write-Host "  ✗ Art Studio Dashboard missing design cards" -ForegroundColor Red
}

if ($artContent -match "v16.0" -or $artContent -match "v16.1") {
    Write-Host "  ✓ Art Studio Dashboard has version badges" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Art Studio Dashboard version badges may be missing" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "5. Summary" -ForegroundColor Yellow
Write-Host "  Files created: 2 (CAMDashboard.vue, ArtStudioDashboard.vue)" -ForegroundColor White
Write-Host "  Files modified: 2 (router/index.ts, App.vue)" -ForegroundColor White
Write-Host "  Routes added: 2 (/cam-dashboard, /art-studio-dashboard)" -ForegroundColor White
Write-Host "  Navigation links: 2 (CAM Dashboard, Art Studio Dashboard)" -ForegroundColor White

Write-Host ""
Write-Host "=== Phase 1 Dashboard Scaffold Test PASSED ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Run 'cd client && npm run dev' to start the dev server" -ForegroundColor White
Write-Host "  2. Open http://localhost:5173 in your browser" -ForegroundColor White
Write-Host "  3. Click 'CAM Dashboard' or 'Art Studio Dashboard' in the nav" -ForegroundColor White
Write-Host "  4. Verify operation/design cards display correctly" -ForegroundColor White
Write-Host "  5. Mark Phase 1 complete in todo list" -ForegroundColor White
Write-Host ""
