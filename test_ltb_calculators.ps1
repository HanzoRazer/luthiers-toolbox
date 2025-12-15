# Test LTB Calculator API Endpoints
# Run this with the server already running on port 8000

Write-Host "`n=== Testing LTB Calculator API Endpoints ===`n" -ForegroundColor Cyan

# Test 1: Basic evaluate
Write-Host "Test 1: POST /api/calculators/evaluate (5+3)" -ForegroundColor Yellow
try {
    $body = @{ expression = '5+3' } | ConvertTo-Json
    $result = Invoke-RestMethod -Method POST -Uri 'http://localhost:8000/api/calculators/evaluate' -Body $body -ContentType 'application/json'
    Write-Host "✓ Result: $($result.result)" -ForegroundColor Green
} catch {
    Write-Host "✗ Error: $_" -ForegroundColor Red
}

# Test 2: Fraction convert
Write-Host "`nTest 2: POST /api/calculators/fraction/convert (0.375 to fraction)" -ForegroundColor Yellow
try {
    $body = @{ decimal = 0.375 } | ConvertTo-Json
    $result = Invoke-RestMethod -Method POST -Uri 'http://localhost:8000/api/calculators/fraction/convert' -Body $body -ContentType 'application/json'
    Write-Host "✓ Result: $($result.fraction)" -ForegroundColor Green
} catch {
    Write-Host "✗ Error: $_" -ForegroundColor Red
}

# Test 3: Fret table
Write-Host "`nTest 3: POST /api/calculators/fret/table (scale_length=650mm, 12 frets)" -ForegroundColor Yellow
try {
    $body = @{ scale_length_mm = 650; num_frets = 12 } | ConvertTo-Json
    $result = Invoke-RestMethod -Method POST -Uri 'http://localhost:8000/api/calculators/fret/table' -Body $body -ContentType 'application/json'
    Write-Host "✓ Fret count: $($result.frets.Count)" -ForegroundColor Green
    Write-Host "  Fret 12: $($result.frets[11].distance_from_nut_mm) mm" -ForegroundColor Gray
} catch {
    Write-Host "✗ Error: $_" -ForegroundColor Red
}

# Test 4: TVM
Write-Host "`nTest 4: POST /api/calculators/tvm (PV=-10000, rate=5%, periods=10)" -ForegroundColor Yellow
try {
    $body = @{
        present_value = -10000
        annual_rate_pct = 5.0
        periods_years = 10
    } | ConvertTo-Json
    $result = Invoke-RestMethod -Method POST -Uri 'http://localhost:8000/api/calculators/tvm' -Body $body -ContentType 'application/json'
    Write-Host "✓ Future Value: `$$($result.future_value)" -ForegroundColor Green
} catch {
    Write-Host "✗ Error: $_" -ForegroundColor Red
}

# Test 5: Radius from 3 points
Write-Host "`nTest 5: POST /api/calculators/radius/from-3-points" -ForegroundColor Yellow
try {
    $body = @{
        points = @(
            @{ x = 0; y = 0 },
            @{ x = 10; y = 5 },
            @{ x = 20; y = 0 }
        )
    } | ConvertTo-Json -Depth 3
    $result = Invoke-RestMethod -Method POST -Uri 'http://localhost:8000/api/calculators/radius/from-3-points' -Body $body -ContentType 'application/json'
    Write-Host "✓ Radius: $($result.radius_mm) mm" -ForegroundColor Green
} catch {
    Write-Host "✗ Error: $_" -ForegroundColor Red
}

Write-Host "`n=== All Tests Complete ===`n" -ForegroundColor Cyan
