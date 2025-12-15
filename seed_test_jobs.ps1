# Seed test job data for B21 CompareRunsPanel testing

$logPath = "services\api\data\cam_job_log.jsonl"
$logDir = Split-Path $logPath -Parent

# Ensure directory exists
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# Create 4 sample jobs with varying metrics
$jobs = @(
    @{
        run_id = "test-job-001"
        job_name = "Aggressive Stepover Test"
        machine_id = "Haas VF-2"
        post_id = "GRBL"
        material = "Ebony"
        sim_time_s = 420.5
        sim_energy_j = 15200.0
        sim_move_count = 856
        sim_issue_count = 2
        sim_max_dev_pct = 0.05
        notes = "40% stepover, fast but issues"
        tags = @("test", "aggressive")
        created_at = (Get-Date).AddHours(-2).ToString("o")
        source = "test_seed"
    },
    @{
        run_id = "test-job-002"
        job_name = "Balanced Stepover Test"
        machine_id = "Haas VF-2"
        post_id = "GRBL"
        material = "Ebony"
        sim_time_s = 380.2
        sim_energy_j = 14100.0
        sim_move_count = 712
        sim_issue_count = 0
        sim_max_dev_pct = 0.02
        notes = "50% stepover, optimal balance"
        tags = @("test", "optimal")
        created_at = (Get-Date).AddHours(-1).ToString("o")
        source = "test_seed"
    },
    @{
        run_id = "test-job-003"
        job_name = "Conservative Stepover Test"
        machine_id = "Haas VF-2"
        post_id = "GRBL"
        material = "Ebony"
        sim_time_s = 450.8
        sim_energy_j = 16500.0
        sim_move_count = 920
        sim_issue_count = 1
        sim_max_dev_pct = 0.01
        notes = "60% stepover, slow but safe"
        tags = @("test", "safe")
        created_at = (Get-Date).AddMinutes(-30).ToString("o")
        source = "test_seed"
    },
    @{
        run_id = "test-job-004"
        job_name = "Different Machine Test"
        machine_id = "ShopBot PRSalpha"
        post_id = "Mach4"
        material = "Walnut"
        sim_time_s = 395.0
        sim_energy_j = 13800.0
        sim_move_count = 780
        sim_issue_count = 3
        sim_max_dev_pct = 0.08
        notes = "Different setup for comparison"
        tags = @("test", "walnut")
        created_at = (Get-Date).ToString("o")
        source = "test_seed"
    }
)

# Append each job as JSONL
foreach ($job in $jobs) {
    $json = $job | ConvertTo-Json -Compress -Depth 10
    Add-Content -Path $logPath -Value $json -Encoding UTF8
}

Write-Host "✓ Seeded 4 test jobs to $logPath" -ForegroundColor Green
Write-Host ""
Write-Host "Test jobs created:" -ForegroundColor Cyan
Write-Host "  1. test-job-001 - Aggressive (2 issues, 420s)"
Write-Host "  2. test-job-002 - Balanced (0 issues, 380s) ← Winner"
Write-Host "  3. test-job-003 - Conservative (1 issue, 450s)"
Write-Host "  4. test-job-004 - Different Machine (3 issues, 395s)"
Write-Host ""
Write-Host "Refresh http://localhost:5173/cam to see Compare Runs panel populate" -ForegroundColor Yellow
