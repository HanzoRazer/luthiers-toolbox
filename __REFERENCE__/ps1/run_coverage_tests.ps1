# Test Coverage Push - Run All Tests
# Part of P3.1 - Test Coverage to 80% (A_N roadmap requirement)

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  Test Coverage Push - Router Tests" -ForegroundColor Cyan
Write-Host "  Target: 80% coverage" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
cd services\api
& .\.venv\Scripts\Activate.ps1

# Run tests with coverage
Write-Host "`nRunning test suite with coverage analysis..." -ForegroundColor Yellow
Write-Host ""

# Run all router tests
pytest tests/ `
    --verbose `
    --cov=app.routers `
    --cov-report=term-missing `
    --cov-report=html:htmlcov `
    --cov-report=json:coverage.json `
    --cov-branch `
    -m "router or integration"

# Check exit code
if ($LASTEXITCODE -eq 0) {
    Write-Host "`n=========================================" -ForegroundColor Green
    Write-Host "  ✓ All tests passed!" -ForegroundColor Green
    Write-Host "=========================================" -ForegroundColor Green
    
    # Display coverage summary
    Write-Host "`nCoverage report generated:" -ForegroundColor Cyan
    Write-Host "  - Terminal: See above" -ForegroundColor Gray
    Write-Host "  - HTML: services/api/htmlcov/index.html" -ForegroundColor Gray
    Write-Host "  - JSON: services/api/coverage.json" -ForegroundColor Gray
    
    # Parse coverage percentage from JSON
    if (Test-Path "coverage.json") {
        $coverage = Get-Content "coverage.json" | ConvertFrom-Json
        $percent = [math]::Round($coverage.totals.percent_covered, 1)
        
        Write-Host "`nOverall Coverage: $percent%" -ForegroundColor Cyan
        
        if ($percent -ge 80.0) {
            Write-Host "🎉 TARGET ACHIEVED: 80%+ coverage!" -ForegroundColor Green
        } elseif ($percent -ge 70.0) {
            Write-Host "⚠️  Close to target: $([math]::Round(80 - $percent, 1))% remaining" -ForegroundColor Yellow
        } else {
            Write-Host "❌ Below target: $([math]::Round(80 - $percent, 1))% remaining" -ForegroundColor Red
        }
    }
    
    exit 0
} else {
    Write-Host "`n=========================================" -ForegroundColor Red
    Write-Host "  ✗ Some tests failed" -ForegroundColor Red
    Write-Host "=========================================" -ForegroundColor Red
    Write-Host "Check output above for details" -ForegroundColor Yellow
    exit 1
}
