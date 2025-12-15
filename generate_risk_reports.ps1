#!/usr/bin/env pwsh
# Generate sample risk reports for Phase 28.2 timeline testing

Write-Host "`n=== Generating Sample Risk Reports ===" -ForegroundColor Cyan
Write-Host "Creating 20 sample reports with varying risk profiles...`n" -ForegroundColor Gray

$baseUrl = "http://localhost:8000"
$jobTypes = @("adaptive", "relief", "rosette", "helical", "pipeline")
$machines = @("GRBL", "Mach4", "LinuxCNC", "PathPilot", "MASSO")
$operations = @("pocket", "engrave", "drill", "contour", "profile")

# Generate 20 reports with realistic progression
$reports = @()
$baseTime = [DateTime]::Now.AddHours(-10)

for ($i = 1; $i -le 20; $i++) {
    $jobType = $jobTypes[$i % $jobTypes.Count]
    $machine = $machines[$i % $machines.Count]
    $operation = $operations[$i % $operations.Count]
    
    # Create variation in risk scores (trending down overall)
    $baseRisk = 15 - ($i * 0.5)  # Decreasing trend
    $variation = Get-Random -Minimum -3 -Maximum 3
    $riskScore = [Math]::Max(1, $baseRisk + $variation)
    
    # Vary severity counts based on risk score
    $criticalCount = [Math]::Floor($riskScore / 3)
    $highCount = [Math]::Floor($riskScore / 2)
    $mediumCount = [Math]::Floor($riskScore * 0.8)
    $lowCount = [Math]::Floor($riskScore * 1.5)
    
    # Extra time correlates with risk
    $extraTime = $riskScore * (Get-Random -Minimum 2 -Maximum 8)
    
    $report = @{
        job_id = "$jobType`_$operation`_$($i.ToString('000'))"
        pipeline_id = $jobType
        op_id = $operation
        machine_profile_id = $machine
        post_preset = $machine
        design_source = "parametric"
        analytics = @{
            total_issues = $criticalCount + $highCount + $mediumCount + $lowCount
            severity_counts = @{
                critical = $criticalCount
                high = $highCount
                medium = $mediumCount
                low = $lowCount
                info = 0
            }
            risk_score = [Math]::Round($riskScore, 2)
            total_extra_time_s = [Math]::Round($extraTime, 1)
            total_extra_time_human = "$([Math]::Floor($extraTime / 60))m $([Math]::Round($extraTime % 60))s"
        }
        issues = @()  # Empty issues array for test data
    }
    
    $reports += $report
}

Write-Host "Sample report distribution:" -ForegroundColor Yellow
Write-Host "  Job types: $($jobTypes -join ', ')" -ForegroundColor Gray
Write-Host "  Machines: $($machines -join ', ')" -ForegroundColor Gray
Write-Host "  Risk scores: $(($reports | Select-Object -First 1).risk_score) → $(($reports | Select-Object -Last 1).risk_score) (trending safer)" -ForegroundColor Gray
Write-Host ""

# Post each report to the API
$successCount = 0
$failCount = 0

foreach ($report in $reports) {
    try {
        $json = $report | ConvertTo-Json -Compress -Depth 10
        $response = Invoke-RestMethod -Uri "$baseUrl/cam/jobs/risk_report" -Method Post -Body $json -ContentType "application/json"
        Write-Host "  ✓ Created: $($report.job_id) (risk: $($report.risk_score))" -ForegroundColor Green
        $successCount++
        Start-Sleep -Milliseconds 100  # Small delay to avoid overwhelming the API
    } catch {
        Write-Host "  ✗ Failed: $($report.job_id) - $($_.Exception.Message)" -ForegroundColor Red
        $failCount++
    }
}

Write-Host "`n=== Generation Complete ===" -ForegroundColor Cyan
Write-Host "Success: $successCount reports" -ForegroundColor Green
Write-Host "Failed: $failCount reports" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Red" })

if ($successCount -gt 0) {
    Write-Host "`n✨ Timeline Features to Test:" -ForegroundColor Yellow
    Write-Host "  1. Navigate to: http://localhost:5173/cam/risk/timeline-enhanced" -ForegroundColor Gray
    Write-Host "  2. View sparkline showing risk trend (should show decrease)" -ForegroundColor Gray
    Write-Host "  3. Hover over sparkline points for tooltips" -ForegroundColor Gray
    Write-Host "  4. Click points to select reports in table" -ForegroundColor Gray
    Write-Host "  5. Try effect filters:" -ForegroundColor Gray
    Write-Host "     • Safer: Shows reports with decreasing risk" -ForegroundColor Gray
    Write-Host "     • Spicier: Shows reports with increasing risk" -ForegroundColor Gray
    Write-Host "     • Critical Reduction: Shows reports with fewer critical issues" -ForegroundColor Gray
    Write-Host "  6. Export to CSV to see all data" -ForegroundColor Gray
    Write-Host ""
}

# Verify the reports
Write-Host "Verifying data..." -ForegroundColor Yellow
try {
    $verify = Invoke-RestMethod -Uri "$baseUrl/cam/jobs/recent?limit=25"
    Write-Host "  ✓ API returns $($verify.Count) reports" -ForegroundColor Green
    Write-Host ""
    Write-Host "🚀 Open the timeline now to see the data!" -ForegroundColor Cyan
} catch {
    Write-Host "  ✗ Verification failed: $($_.Exception.Message)" -ForegroundColor Red
}
