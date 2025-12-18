#!/usr/bin/env pwsh
# Quick Test Runner - Execute Passing Tests Only
# Shows current test coverage progress

Write-Host "`n🧪 Test Coverage Quick Run" -ForegroundColor Cyan
Write-Host "==========================`n" -ForegroundColor Cyan

$API_DIR = "services/api"

# Check if in correct directory
if (-not (Test-Path $API_DIR)) {
    Write-Host "❌ Error: Must run from project root" -ForegroundColor Red
    Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow
    exit 1
}

Set-Location $API_DIR

# Activate venv if exists
if (Test-Path ".venv/Scripts/Activate.ps1") {
    Write-Host "📦 Activating virtual environment..." -ForegroundColor Yellow
    & .\.venv\Scripts\Activate.ps1
}

Write-Host "`n✅ Running Passing Tests Only" -ForegroundColor Green
Write-Host "===============================`n" -ForegroundColor Green

# Run passing test categories
$testSets = @(
    @{
        Name = "Parity Checking (3 tests)"
        Path = "tests/test_geometry_router.py::TestParityChecking"
        Marker = "geometry"
    },
    @{
        Name = "Geometry Export (2 tests)"
        Path = "tests/test_geometry_router.py::TestGeometryExport::test_export_dxf tests/test_geometry_router.py::TestGeometryExport::test_export_svg"
        Marker = "export"
    },
    @{
        Name = "Adaptive Statistics (4 tests)"
        Path = "tests/test_adaptive_router.py::TestAdaptiveStatistics"
        Marker = "adaptive"
    },
    @{
        Name = "Adaptive Validation (3 tests)"
        Path = "tests/test_adaptive_router.py::TestAdaptiveValidation::test_missing_loops tests/test_adaptive_router.py::TestAdaptiveValidation::test_invalid_strategy"
        Marker = "adaptive"
    },
    @{
        Name = "Bridge Presets (4 tests)"
        Path = "tests/test_bridge_router.py::TestBridgePresets"
        Marker = "bridge"
    }
)

$totalPassed = 0
$totalFailed = 0

foreach ($testSet in $testSets) {
    Write-Host "`n📋 $($testSet.Name)" -ForegroundColor Cyan
    Write-Host ("─" * 60) -ForegroundColor DarkGray
    
    $result = pytest $testSet.Path -v --tb=line --no-cov -q 2>&1 | Out-String
    
    if ($result -match "(\d+) passed") {
        $passed = [int]$matches[1]
        $totalPassed += $passed
        Write-Host "  ✅ $passed passed" -ForegroundColor Green
    }
    
    if ($result -match "(\d+) failed") {
        $failed = [int]$matches[1]
        $totalFailed += $failed
        Write-Host "  ❌ $failed failed" -ForegroundColor Red
    }
}

# Summary
Write-Host "`n" + ("=" * 60) -ForegroundColor Cyan
Write-Host "📊 Summary" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "  Passed:  $totalPassed ✅" -ForegroundColor Green
if ($totalFailed -gt 0) {
    Write-Host "  Failed:  $totalFailed ❌" -ForegroundColor Red
}
Write-Host "`n"

# Run full coverage report on target routers
Write-Host "📈 Coverage Report (Target Routers)" -ForegroundColor Yellow
Write-Host ("=" * 60) -ForegroundColor DarkGray

pytest tests/test_geometry_router.py tests/test_adaptive_router.py tests/test_bridge_router.py `
    --cov=app.routers.geometry_router `
    --cov=app.routers.adaptive_router `
    --cov=app.routers.bridge_router `
    --cov-report=term-missing `
    --tb=no `
    -q 2>&1 | Select-String -Pattern "geometry_router|adaptive_router|bridge_router|TOTAL"

Write-Host "`n✅ Test run complete!" -ForegroundColor Green
Write-Host "📄 See TEST_COVERAGE_SESSION_RESULTS.md for detailed report" -ForegroundColor Cyan

Set-Location ../..
