<#
.SYNOPSIS
  Test script for Saw Lab 2.0 integration with RMOS

.DESCRIPTION
  Tests the Saw Lab 2.0 module integration:
  - Saw mode detection (tool_id prefix)
  - Saw calculators (heat, deflection, rim speed, bite load, kickback)
  - Saw toolpath generation
  - RMOS endpoint branching

.EXAMPLE
  ./test_saw_lab_2_0.ps1

.NOTES
  Requires server running on port 8010
#>

$BASE_URL = "http://localhost:8010"

Write-Host "=" * 60
Write-Host "Saw Lab 2.0 Integration Tests"
Write-Host "=" * 60
Write-Host ""

# Test 1: Router mode (default - no saw: prefix)
Write-Host "=== Test 1: Router Mode (default) ==="
$routerBody = @{
    design = @{
        outer_diameter_mm = 100.0
        inner_diameter_mm = 20.0
        ring_count = 3
        pattern_type = "herringbone"
    }
    context = @{
        material_id = "maple"
        tool_id = "end_mill_6mm"  # Router tool (no saw: prefix)
        use_shapely_geometry = $true
    }
} | ConvertTo-Json -Depth 5

try {
    $result = Invoke-RestMethod -Uri "$BASE_URL/api/rmos/feasibility" -Method POST -Body $routerBody -ContentType "application/json"
    Write-Host "  Score: $($result.score)"
    Write-Host "  Risk: $($result.risk_bucket)"
    Write-Host "  Calculator keys: $($result.calculator_results.PSObject.Properties.Name -join ', ')"
    
    # Should have router calculators
    if ($result.calculator_results.chipload) {
        Write-Host "  ✓ Router mode confirmed (chipload calculator present)" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Router mode test failed" -ForegroundColor Red
    }
} catch {
    Write-Host "  ✗ Router mode test failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 2: Saw mode detection
Write-Host "=== Test 2: Saw Mode Detection ==="
$sawBody = @{
    design = @{
        outer_diameter_mm = 300.0
        inner_diameter_mm = 0.0
        ring_count = 1
        pattern_type = "crosscut"
    }
    context = @{
        material_id = "maple"
        tool_id = "saw:10_24_3.0"  # Saw tool: 10" blade, 24 teeth, 3mm kerf
        use_shapely_geometry = $true
    }
} | ConvertTo-Json -Depth 5

try {
    $result = Invoke-RestMethod -Uri "$BASE_URL/api/rmos/feasibility" -Method POST -Body $sawBody -ContentType "application/json"
    Write-Host "  Score: $($result.score)"
    Write-Host "  Risk: $($result.risk_bucket)"
    Write-Host "  Calculator keys: $($result.calculator_results.PSObject.Properties.Name -join ', ')"
    
    # Should have saw calculators
    if ($result.calculator_results.heat -or $result.calculator_results.kickback) {
        Write-Host "  ✓ Saw mode detected (saw calculators present)" -ForegroundColor Green
    } else {
        Write-Host "  ? Saw mode may not be fully active (check calculator keys)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ✗ Saw mode test failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 3: Saw toolpath generation
Write-Host "=== Test 3: Saw Toolpath Generation ==="
try {
    $result = Invoke-RestMethod -Uri "$BASE_URL/api/rmos/toolpaths" -Method POST -Body $sawBody -ContentType "application/json"
    Write-Host "  Total length: $($result.total_length_mm) mm"
    Write-Host "  Estimated time: $($result.estimated_time_seconds) seconds"
    Write-Host "  Toolpath count: $($result.toolpaths.Count)"
    
    if ($result.toolpaths.Count -gt 0) {
        $firstMove = $result.toolpaths[0]
        Write-Host "  First move: $($firstMove.code)"
        Write-Host "  ✓ Saw toolpaths generated" -ForegroundColor Green
    } else {
        Write-Host "  ? No toolpaths generated (check warnings)" -ForegroundColor Yellow
    }
    
    if ($result.warnings.Count -gt 0) {
        Write-Host "  Warnings: $($result.warnings -join '; ')" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ✗ Saw toolpath test failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 4: Saw BOM generation
Write-Host "=== Test 4: Saw BOM Generation ==="
try {
    $result = Invoke-RestMethod -Uri "$BASE_URL/api/rmos/bom" -Method POST -Body $sawBody -ContentType "application/json"
    Write-Host "  Material required: $($result.material_required_mm2) mm²"
    Write-Host "  Tools: $($result.tool_ids -join ', ')"
    Write-Host "  Waste estimate: $($result.estimated_waste_percent)%"
    Write-Host "  ✓ BOM generated" -ForegroundColor Green
} catch {
    Write-Host "  ✗ BOM test failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 5: Multiple saw configurations
Write-Host "=== Test 5: Different Saw Configurations ==="
$sawConfigs = @(
    @{ id = "saw:8_40_2.5"; desc = "8 inch, 40 teeth, 2.5mm kerf" },
    @{ id = "saw:12_60_3.5"; desc = "12 inch, 60 teeth, 3.5mm kerf" },
    @{ id = "saw:10_24_3.0"; desc = "10 inch, 24 teeth, 3.0mm kerf" }
)

foreach ($config in $sawConfigs) {
    $testBody = @{
        design = @{
            outer_diameter_mm = 250.0
            inner_diameter_mm = 0.0
            ring_count = 1
            pattern_type = "rip"
        }
        context = @{
            material_id = "hardwood_oak"
            tool_id = $config.id
            use_shapely_geometry = $true
        }
    } | ConvertTo-Json -Depth 5
    
    try {
        $result = Invoke-RestMethod -Uri "$BASE_URL/api/rmos/feasibility" -Method POST -Body $testBody -ContentType "application/json"
        Write-Host "  $($config.desc): Score=$($result.score), Risk=$($result.risk_bucket)" -ForegroundColor Cyan
    } catch {
        Write-Host "  $($config.desc): FAILED - $_" -ForegroundColor Red
    }
}
Write-Host ""

# Summary
Write-Host "=" * 60
Write-Host "Saw Lab 2.0 Tests Complete"
Write-Host "=" * 60
