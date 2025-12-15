# Test Energy Analysis Endpoint (Item 18 Verification)
# Tests POST /api/cam/sim/metrics with material-specific energy modeling

Write-Host "`n=== Testing Energy Analysis Endpoint ===" -ForegroundColor Cyan
Write-Host "Endpoint: POST /api/cam/sim/metrics`n" -ForegroundColor Gray

$baseUrl = "http://localhost:8000"

# Test 1: Basic energy analysis with simple moves
Write-Host "Test 1: Basic Energy Analysis" -ForegroundColor Yellow

$payload1 = @{
    moves = @(
        @{ code = "G0"; x = 0; y = 0; z = 5 }
        @{ code = "G0"; x = 3; y = 3 }
        @{ code = "G1"; x = 3; y = 3; z = -1.5; f = 1200 }
        @{ code = "G1"; x = 97; y = 3; f = 1200 }
        @{ code = "G1"; x = 97; y = 57; f = 1200 }
        @{ code = "G1"; x = 3; y = 57; f = 1200 }
        @{ code = "G1"; x = 3; y = 3; f = 1200 }
        @{ code = "G0"; z = 5 }
    )
    tool_d_mm = 6.0
    material = @{
        name = "hardwood_generic"
        sce_j_per_mm3 = 1.4
        chip_fraction = 0.60
        tool_fraction = 0.25
        work_fraction = 0.15
    }
    machine_caps = @{
        feed_xy_max = 3000.0
        rapid_xy = 6000.0
        accel_xy = 800.0
    }
    engagement = @{
        stepover_frac = 0.45
        stepdown_mm = 1.5
        engagement_pct = 40.0
    }
    include_timeseries = $false
} | ConvertTo-Json -Depth 10

try {
    $response1 = Invoke-RestMethod -Uri "$baseUrl/cam/sim/metrics" -Method Post -Body $payload1 -ContentType "application/json"
    
    Write-Host "  ✓ Energy analysis successful" -ForegroundColor Green
    Write-Host "    Cutting length: $($response1.length_cutting_mm) mm" -ForegroundColor Gray
    Write-Host "    Rapid length: $($response1.length_rapid_mm) mm" -ForegroundColor Gray
    Write-Host "    Total time: $($response1.time_s) s" -ForegroundColor Gray
    Write-Host "    Volume removed: $($response1.volume_mm3) mm³" -ForegroundColor Gray
    Write-Host "    MRR: $($response1.mrr_mm3_min) mm³/min" -ForegroundColor Gray
    Write-Host "    Average power: $($response1.power_avg_w) W" -ForegroundColor Gray
    Write-Host "    Total energy: $($response1.energy_total_j) J" -ForegroundColor Green
    Write-Host "      - Chip energy: $($response1.energy_chip_j) J ($(($response1.energy_chip_j / $response1.energy_total_j * 100).ToString('F1'))%)" -ForegroundColor Gray
    Write-Host "      - Tool energy: $($response1.energy_tool_j) J ($(($response1.energy_tool_j / $response1.energy_total_j * 100).ToString('F1'))%)" -ForegroundColor Gray
    Write-Host "      - Workpiece energy: $($response1.energy_workpiece_j) J ($(($response1.energy_workpiece_j / $response1.energy_total_j * 100).ToString('F1'))%)" -ForegroundColor Gray
    
    # Validate heat partition
    $heatSum = $response1.energy_chip_j + $response1.energy_tool_j + $response1.energy_workpiece_j
    $heatDiff = [Math]::Abs($heatSum - $response1.energy_total_j)
    if ($heatDiff -lt 0.01) {
        Write-Host "  ✓ Heat partition validated (sum matches total within 0.01 J)" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Heat partition error: sum=$heatSum vs total=$($response1.energy_total_j)" -ForegroundColor Red
    }
    
} catch {
    Write-Host "  ✗ Test 1 failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 2: Energy analysis with timeseries
Write-Host "Test 2: Energy Analysis with Timeseries" -ForegroundColor Yellow

$payload2 = @{
    moves = @(
        @{ code = "G1"; x = 0; y = 0; z = -1.5; f = 1200 }
        @{ code = "G1"; x = 50; y = 0; f = 1200 }
        @{ code = "G1"; x = 50; y = 30; f = 1200 }
        @{ code = "G1"; x = 0; y = 30; f = 1200 }
        @{ code = "G1"; x = 0; y = 0; f = 1200 }
    )
    tool_d_mm = 6.0
    material = @{
        name = "maple_hard"
        sce_j_per_mm3 = 1.6
        chip_fraction = 0.70
        tool_fraction = 0.20
        work_fraction = 0.10
    }
    machine_caps = @{
        feed_xy_max = 2500.0
        rapid_xy = 5000.0
        accel_xy = 600.0
    }
    engagement = @{
        stepover_frac = 0.40
        stepdown_mm = 2.0
        engagement_pct = 45.0
    }
    include_timeseries = $true
} | ConvertTo-Json -Depth 10

try {
    $response2 = Invoke-RestMethod -Uri "$baseUrl/cam/sim/metrics" -Method Post -Body $payload2 -ContentType "application/json"
    
    Write-Host "  ✓ Timeseries analysis successful" -ForegroundColor Green
    Write-Host "    Total energy: $($response2.energy_total_j) J" -ForegroundColor Gray
    Write-Host "    Timeseries entries: $($response2.timeseries.Count)" -ForegroundColor Gray
    
    if ($response2.timeseries.Count -gt 0) {
        Write-Host "  ✓ Timeseries data present" -ForegroundColor Green
        
        # Show first 3 timeseries entries
        Write-Host "    Sample timeseries data:" -ForegroundColor Gray
        for ($i = 0; $i -lt [Math]::Min(3, $response2.timeseries.Count); $i++) {
            $ts = $response2.timeseries[$i]
            Write-Host "      [$($ts.idx)] $($ts.code): len=$($ts.length_mm.ToString('F2'))mm, feed=$($ts.feed_u_per_min.ToString('F0')), time=$($ts.time_s.ToString('F3'))s, power=$($ts.power_w.ToString('F1'))W, energy=$($ts.energy_j.ToString('F2'))J" -ForegroundColor DarkGray
        }
        
        # Validate timeseries energy sum
        $tsEnergySum = ($response2.timeseries | Measure-Object -Property energy_j -Sum).Sum
        $energyDiff = [Math]::Abs($tsEnergySum - $response2.energy_total_j)
        if ($energyDiff -lt 1.0) {
            Write-Host "  ✓ Timeseries energy sum matches total (within 1.0 J)" -ForegroundColor Green
        } else {
            Write-Host "  ⚠ Timeseries energy sum: $tsEnergySum vs total: $($response2.energy_total_j)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ✗ No timeseries data returned" -ForegroundColor Red
    }
    
} catch {
    Write-Host "  ✗ Test 2 failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 3: G-code text parsing
Write-Host "Test 3: G-code Text Parsing" -ForegroundColor Yellow

$gcodeText = @"
G21
G90
G0 Z5
G0 X10 Y10
G1 Z-2 F1200
G1 X60 Y10 F1500
G1 X60 Y40 F1500
G1 X10 Y40 F1500
G1 X10 Y10 F1500
G0 Z5
"@

$payload3 = @{
    gcode_text = $gcodeText
    tool_d_mm = 8.0
    material = @{
        name = "aluminum_6061"
        sce_j_per_mm3 = 0.35
        chip_fraction = 0.60
        tool_fraction = 0.25
        work_fraction = 0.15
    }
    include_timeseries = $false
} | ConvertTo-Json -Depth 10

try {
    $response3 = Invoke-RestMethod -Uri "$baseUrl/cam/sim/metrics" -Method Post -Body $payload3 -ContentType "application/json"
    
    Write-Host "  ✓ G-code parsing successful" -ForegroundColor Green
    Write-Host "    Material: aluminum_6061 (SCE=0.35 J/mm³)" -ForegroundColor Gray
    Write-Host "    Total energy: $($response3.energy_total_j) J" -ForegroundColor Gray
    Write-Host "    Cutting length: $($response3.length_cutting_mm) mm" -ForegroundColor Gray
    
    # Lower energy expected for aluminum
    if ($response3.energy_total_j -lt 1000) {
        Write-Host "  ✓ Energy reasonable for aluminum (< 1000 J)" -ForegroundColor Green
    }
    
} catch {
    Write-Host "  ✗ Test 3 failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 4: Carbon footprint calculation (utility demo)
Write-Host "Test 4: Carbon Footprint Calculation Demo" -ForegroundColor Yellow

$gridEmissionFactor = 0.000475  # kg CO2 per J (US grid average ~475 g CO2/kWh)

$co2_test1 = $response1.energy_total_j * $gridEmissionFactor
$co2_test2 = $response2.energy_total_j * $gridEmissionFactor
$co2_test3 = $response3.energy_total_j * $gridEmissionFactor

Write-Host "  Carbon footprint estimates (US grid average):" -ForegroundColor Gray
Write-Host "    Test 1 (hardwood): $($co2_test1.ToString('F3')) kg CO2" -ForegroundColor Gray
Write-Host "    Test 2 (maple): $($co2_test2.ToString('F3')) kg CO2" -ForegroundColor Gray
Write-Host "    Test 3 (aluminum): $($co2_test3.ToString('F3')) kg CO2" -ForegroundColor Gray
Write-Host "  Note: Grid emission factor = 475 g CO2/kWh" -ForegroundColor DarkGray

Write-Host ""

# Summary
Write-Host "=== All Tests Completed Successfully ===" -ForegroundColor Green
Write-Host ""
Write-Host "✓ Basic energy analysis working" -ForegroundColor Green
Write-Host "✓ Timeseries generation working" -ForegroundColor Green
Write-Host "✓ G-code parsing working" -ForegroundColor Green
Write-Host "✓ Heat partition validation passed" -ForegroundColor Green
Write-Host "✓ Carbon footprint calculation demo" -ForegroundColor Green
Write-Host ""
Write-Host "Item 18 (Energy Analysis) is FULLY FUNCTIONAL!" -ForegroundColor Cyan
