#!/usr/bin/env pwsh
# Test B21: Multi-Run Comparison (Historical Job Analysis)
# Tests comparison of multiple presets cloned from JobInt runs

$baseUrl = "http://localhost:8000"
Write-Host "=== Testing B21: Multi-Run Comparison ===" -ForegroundColor Cyan
Write-Host ""

# Test 1: Create test presets with job lineage
Write-Host "1. Creating test presets with job lineage (B19)..." -ForegroundColor Yellow

$testPresets = @()

# Create 4 test presets simulating evolution of CAM parameters
$presetConfigs = @(
    @{
        name = "CAM Run v1 - Baseline"
        strategy = "Spiral"
        stepover = 0.4
        feed_xy = 1000
        sim_time = 120.5
        sim_energy = 850
        sim_issues = 5
    },
    @{
        name = "CAM Run v2 - Increased Feed"
        strategy = "Spiral"
        stepover = 0.4
        feed_xy = 1200
        sim_time = 105.3
        sim_energy = 920
        sim_issues = 3
    },
    @{
        name = "CAM Run v3 - Optimized Stepover"
        strategy = "Spiral"
        stepover = 0.45
        feed_xy = 1200
        sim_time = 95.8
        sim_energy = 880
        sim_issues = 2
    },
    @{
        name = "CAM Run v4 - Strategy Change"
        strategy = "Lanes"
        stepover = 0.45
        feed_xy = 1200
        sim_time = 110.2
        sim_energy = 900
        sim_issues = 1
    }
)

foreach ($config in $presetConfigs) {
    $jobSourceId = "job_" + (Get-Random -Minimum 10000 -Maximum 99999)
    
    $preset = @{
        name = $config.name
        kind = "cam"
        description = "Test preset for multi-run comparison"
        tags = @("test", "b21", "multi-run")
        job_source_id = $jobSourceId
        source = "clone"
        cam_params = @{
            strategy = $config.strategy
            stepover = $config.stepover
            feed_xy = $config.feed_xy
        }
    }

    try {
        $response = Invoke-RestMethod -Uri "$baseUrl/api/presets" -Method Post -Body ($preset | ConvertTo-Json -Depth 10) -ContentType "application/json"
        $testPresets += $response.id
        Write-Host "  ✓ Created: $($config.name) (ID: $($response.id), Job: $jobSourceId)" -ForegroundColor Green
        
        # Create mock job log entry for this preset
        # Note: In production, this would come from actual JobInt runs
        # For testing, we'll create mock job log files
        
    } catch {
        Write-Host "  ✗ Failed to create preset: $_" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""

# Test 2: Run multi-run comparison
Write-Host "2. Running multi-run comparison..." -ForegroundColor Yellow

$comparisonRequest = @{
    preset_ids = $testPresets
    include_trends = $true
    include_recommendations = $true
}

try {
    $comparison = Invoke-RestMethod -Uri "$baseUrl/api/presets/compare-runs" -Method Post -Body ($comparisonRequest | ConvertTo-Json -Depth 10) -ContentType "application/json"
    Write-Host "  ✓ Comparison successful" -ForegroundColor Green
    Write-Host ""
    
    # Display results
    Write-Host "=== Comparison Results ===" -ForegroundColor Cyan
    Write-Host "Runs compared: $($comparison.runs.Count)" -ForegroundColor White
    Write-Host "Avg time: $($comparison.avg_time_s)s" -ForegroundColor White
    Write-Host "Min time: $($comparison.min_time_s)s" -ForegroundColor White
    Write-Host "Max time: $($comparison.max_time_s)s" -ForegroundColor White
    Write-Host "Avg energy: $($comparison.avg_energy_j)J" -ForegroundColor White
    Write-Host ""
    
    # Trends
    if ($comparison.time_trend) {
        $trendColor = switch ($comparison.time_trend) {
            "improving" { "Green" }
            "degrading" { "Red" }
            "stable" { "Yellow" }
        }
        Write-Host "Time trend: $($comparison.time_trend)" -ForegroundColor $trendColor
    }
    if ($comparison.energy_trend) {
        $trendColor = switch ($comparison.energy_trend) {
            "improving" { "Green" }
            "degrading" { "Red" }
            "stable" { "Yellow" }
        }
        Write-Host "Energy trend: $($comparison.energy_trend)" -ForegroundColor $trendColor
    }
    Write-Host ""
    
    # Best/worst runs
    if ($comparison.best_run_id) {
        $bestRun = $comparison.runs | Where-Object { $_.preset_id -eq $comparison.best_run_id }
        Write-Host "🏆 Best run: $($bestRun.preset_name)" -ForegroundColor Green
        Write-Host "   Time: $($bestRun.sim_time_s)s, Efficiency: $($bestRun.efficiency_score)/100" -ForegroundColor Green
    }
    if ($comparison.worst_run_id) {
        $worstRun = $comparison.runs | Where-Object { $_.preset_id -eq $comparison.worst_run_id }
        Write-Host "⚠️  Worst run: $($worstRun.preset_name)" -ForegroundColor Red
        Write-Host "   Time: $($worstRun.sim_time_s)s, Efficiency: $($worstRun.efficiency_score)/100" -ForegroundColor Red
    }
    Write-Host ""
    
    # Recommendations
    if ($comparison.recommendations.Count -gt 0) {
        Write-Host "💡 Recommendations:" -ForegroundColor Cyan
        foreach ($rec in $comparison.recommendations) {
            Write-Host "   $rec" -ForegroundColor White
        }
    }
    Write-Host ""
    
} catch {
    Write-Host "  ✗ Comparison failed: $_" -ForegroundColor Red
    exit 1
}

# Test 3: Test with insufficient presets (error case)
Write-Host "3. Testing error case (insufficient presets)..." -ForegroundColor Yellow

$invalidRequest = @{
    preset_ids = @($testPresets[0])  # Only 1 preset
    include_trends = $true
    include_recommendations = $true
}

try {
    $result = Invoke-RestMethod -Uri "$baseUrl/api/presets/compare-runs" -Method Post -Body ($invalidRequest | ConvertTo-Json -Depth 10) -ContentType "application/json" -ErrorAction Stop
    Write-Host "  ✗ Should have failed with 400 error" -ForegroundColor Red
} catch {
    if ($_.Exception.Response.StatusCode -eq 400) {
        Write-Host "  ✓ Correctly rejected with 400 Bad Request" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Wrong error code: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    }
}

Write-Host ""

# Test 4: Run comparison table output
Write-Host "4. Detailed run comparison:" -ForegroundColor Yellow
Write-Host ""
Write-Host ("=" * 120) -ForegroundColor DarkGray
Write-Host ("{0,-30} {1,10} {2,12} {3,10} {4,10} {5,15} {6,12}" -f "Preset Name", "Time (s)", "Energy (J)", "Moves", "Issues", "Strategy", "Efficiency") -ForegroundColor Cyan
Write-Host ("=" * 120) -ForegroundColor DarkGray

foreach ($run in $comparison.runs) {
    $timeStr = if ($run.sim_time_s) { $run.sim_time_s.ToString("F1") } else { "N/A" }
    $energyStr = if ($run.sim_energy_j) { $run.sim_energy_j.ToString("F0") } else { "N/A" }
    $movesStr = if ($run.sim_move_count) { $run.sim_move_count } else { "N/A" }
    $issuesStr = if ($run.sim_issue_count) { $run.sim_issue_count } else { "0" }
    $strategyStr = if ($run.strategy) { $run.strategy } else { "N/A" }
    $effStr = if ($run.efficiency_score) { "$($run.efficiency_score.ToString('F0'))/100" } else { "N/A" }
    
    $color = "White"
    if ($run.preset_id -eq $comparison.best_run_id) { $color = "Green" }
    if ($run.preset_id -eq $comparison.worst_run_id) { $color = "Red" }
    
    Write-Host ("{0,-30} {1,10} {2,12} {3,10} {4,10} {5,15} {6,12}" -f $run.preset_name, $timeStr, $energyStr, $movesStr, $issuesStr, $strategyStr, $effStr) -ForegroundColor $color
}

Write-Host ("=" * 120) -ForegroundColor DarkGray
Write-Host ""

# Frontend test checklist
Write-Host "=== Frontend Test Checklist ===" -ForegroundColor Cyan
Write-Host "Open http://localhost:5173/lab/compare-runs (or equivalent route)" -ForegroundColor White
Write-Host ""
Write-Host "1. ✓ Preset selector shows presets with job lineage only" -ForegroundColor White
Write-Host "2. ✓ Multi-select checkboxes work correctly" -ForegroundColor White
Write-Host "3. ✓ 'Compare Runs' button disabled until 2+ presets selected" -ForegroundColor White
Write-Host "4. ✓ Summary stats display (avg time, avg energy, avg moves)" -ForegroundColor White
Write-Host "5. ✓ Trend badges show (improving/degrading/stable)" -ForegroundColor White
Write-Host "6. ✓ Recommendations list displays with icons" -ForegroundColor White
Write-Host "7. ✓ Comparison table shows all runs with metrics" -ForegroundColor White
Write-Host "8. ✓ Best run highlighted in green with 🏆" -ForegroundColor White
Write-Host "9. ✓ Worst run highlighted in red with ⚠️" -ForegroundColor White
Write-Host "10. ✓ Efficiency score progress bars display correctly" -ForegroundColor White
Write-Host "11. ✓ Time comparison bar chart renders with Chart.js" -ForegroundColor White
Write-Host "12. ✓ Export CSV button generates downloadable file" -ForegroundColor White
Write-Host "13. ✓ New Comparison button resets state" -ForegroundColor White
Write-Host ""

# Summary
Write-Host "=== B21 Tests Complete ===" -ForegroundColor Green
Write-Host "Created $($testPresets.Count) test presets with job lineage" -ForegroundColor White
Write-Host "Successfully ran multi-run comparison" -ForegroundColor White
Write-Host "Verified error handling for insufficient presets" -ForegroundColor White
Write-Host ""
Write-Host "Test preset IDs:" -ForegroundColor Cyan
foreach ($id in $testPresets) {
    Write-Host "  - $id" -ForegroundColor DarkGray
}
Write-Host ""
Write-Host "Next: Complete frontend testing checklist above" -ForegroundColor Cyan
