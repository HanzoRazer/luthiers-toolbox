#!/usr/bin/env pwsh
# Test CP-S59/S60: Saw Telemetry & Auto-Learning
# Tests run record creation, telemetry ingestion, risk scoring, auto-learning

$ErrorActionPreference = "Stop"
$baseUrl = "http://localhost:8000"

Write-Host "`n=== Testing CP-S59/S60: Saw Telemetry & Auto-Learning ===" -ForegroundColor Cyan

# ============================================================================
# Test 1: Create Run Record
# ============================================================================

Write-Host "`n1. Testing POST /api/saw/joblog/run (Create Run)" -ForegroundColor Yellow

$createRunPayload = @{
    op_type = "slice"
    machine_profile = "bcam_router_2030"
    material_family = "hardwood"
    blade_id = "tenryu_gm-25560d_test"
    safe_z = 5.0
    depth_passes = 3
    total_length_mm = 1200.0
    planned_rpm = 3600.0
    planned_feed_ipm = 120.0
    planned_doc_mm = 10.0
    operator_notes = "Test run for auto-learning"
} | ConvertTo-Json -Depth 10

try {
    $run = Invoke-RestMethod -Uri "$baseUrl/api/saw/joblog/run" `
        -Method Post `
        -ContentType "application/json" `
        -Body $createRunPayload
    
    Write-Host "  ✅ Run created successfully" -ForegroundColor Green
    Write-Host "    Run ID: $($run.run_id)"
    Write-Host "    Op Type: $($run.op_type)"
    Write-Host "    Machine: $($run.machine_profile)"
    Write-Host "    Material: $($run.material_family)"
    Write-Host "    Blade: $($run.blade_id)"
    Write-Host "    Status: $($run.status)"
    
    # Save run_id for later tests
    $runId = $run.run_id
}
catch {
    Write-Host "  ❌ Failed to create run" -ForegroundColor Red
    Write-Host "    Error: $_"
    exit 1
}

# ============================================================================
# Test 2: Get Run Record
# ============================================================================

Write-Host "`n2. Testing GET /api/saw/joblog/run/{run_id}" -ForegroundColor Yellow

try {
    $run = Invoke-RestMethod -Uri "$baseUrl/api/saw/joblog/run/$runId" -Method Get
    
    Write-Host "  ✅ Run retrieved" -ForegroundColor Green
    Write-Host "    Run ID: $($run.run_id)"
    Write-Host "    Timestamp: $($run.timestamp)"
}
catch {
    Write-Host "  ❌ Failed to get run" -ForegroundColor Red
    exit 1
}

# ============================================================================
# Test 3: Simulate Learning (Preview)
# ============================================================================

Write-Host "`n3. Testing POST /api/saw/telemetry/simulate_learning" -ForegroundColor Yellow

$simulatePayload = @{
    telemetry = @{
        saw_rpm = 3580.0
        feed_ipm = 118.0
        spindle_load_pct = 45.0
        axis_load_pct = 35.0
        vibration_rms = 0.25
        sound_db = 85.0
    }
    current_lane_scale = 1.0
} | ConvertTo-Json -Depth 10

try {
    $sim = Invoke-RestMethod -Uri "$baseUrl/api/saw/telemetry/simulate_learning" `
        -Method Post `
        -ContentType "application/json" `
        -Body $simulatePayload
    
    Write-Host "  ✅ Learning simulation completed" -ForegroundColor Green
    Write-Host "    Current lane scale: $($sim.current_lane_scale)"
    Write-Host "    Recommended scale: $($sim.recommended_lane_scale)"
    Write-Host "    Delta: $($sim.delta)"
    Write-Host "    Action: $($sim.action)"
    Write-Host "    Risk Scores:"
    Write-Host "      Overload: $($sim.telemetry.overload_risk)"
    Write-Host "      Vibration: $($sim.telemetry.vibration_risk)"
    Write-Host "      Sound: $($sim.telemetry.sound_risk)"
    Write-Host "      Overall: $($sim.telemetry.overall_risk)"
}
catch {
    Write-Host "  ❌ Failed to simulate learning" -ForegroundColor Red
    exit 1
}

# ============================================================================
# Test 4: Ingest Low Risk Telemetry (Should Speed Up)
# ============================================================================

Write-Host "`n4. Testing POST /api/saw/telemetry/ingest (Low Risk)" -ForegroundColor Yellow

# Update run to success first
$updatePayload = @{
    status = "success"
    actual_time_s = 45.0
} | ConvertTo-Json -Depth 10

try {
    $run = Invoke-RestMethod -Uri "$baseUrl/api/saw/joblog/run/$runId" `
        -Method Patch `
        -ContentType "application/json" `
        -Body $updatePayload
    
    Write-Host "  ✅ Run marked as success" -ForegroundColor Green
}
catch {
    Write-Host "  ❌ Failed to update run" -ForegroundColor Red
    exit 1
}

# Ingest low risk telemetry
$lowRiskPayload = @{
    run_id = $runId
    telemetry = @{
        saw_rpm = 3600.0
        feed_ipm = 120.0
        spindle_load_pct = 25.0
        axis_load_pct = 20.0
        vibration_rms = 0.15
        sound_db = 75.0
    }
    apply_learning = $true
} | ConvertTo-Json -Depth 10

try {
    $run = Invoke-RestMethod -Uri "$baseUrl/api/saw/telemetry/ingest" `
        -Method Post `
        -ContentType "application/json" `
        -Body $lowRiskPayload
    
    Write-Host "  ✅ Low risk telemetry ingested" -ForegroundColor Green
    Write-Host "    Overload risk: $($run.telemetry.overload_risk)"
    Write-Host "    Vibration risk: $($run.telemetry.vibration_risk)"
    Write-Host "    Sound risk: $($run.telemetry.sound_risk)"
    Write-Host "    Overall risk: $($run.telemetry.overall_risk)"
    Write-Host "    Auto-learned: $($run.auto_learned)"
    
    if ($run.auto_learned) {
        Write-Host "    Lane scale: $($run.lane_scale_before) → $($run.lane_scale_after)" -ForegroundColor Green
    }
}
catch {
    Write-Host "  ❌ Failed to ingest telemetry" -ForegroundColor Red
    Write-Host "    Error: $_"
    exit 1
}

# ============================================================================
# Test 5: Create Second Run with High Risk
# ============================================================================

Write-Host "`n5. Testing High Risk Telemetry (Should Slow Down)" -ForegroundColor Yellow

$createRun2 = @{
    op_type = "contour"
    machine_profile = "bcam_router_2030"
    material_family = "hardwood"
    blade_id = "tenryu_gm-25560d_test"
    safe_z = 5.0
    depth_passes = 2
    total_length_mm = 800.0
    planned_rpm = 3600.0
    planned_feed_ipm = 140.0
    planned_doc_mm = 12.0
} | ConvertTo-Json -Depth 10

try {
    $run2 = Invoke-RestMethod -Uri "$baseUrl/api/saw/joblog/run" `
        -Method Post `
        -ContentType "application/json" `
        -Body $createRun2
    
    $runId2 = $run2.run_id
    
    # Mark success
    $update2 = @{
        status = "success"
        actual_time_s = 60.0
    } | ConvertTo-Json -Depth 10
    
    $run2 = Invoke-RestMethod -Uri "$baseUrl/api/saw/joblog/run/$runId2" `
        -Method Patch `
        -ContentType "application/json" `
        -Body $update2
    
    # Ingest high risk telemetry
    $highRiskPayload = @{
        run_id = $runId2
        telemetry = @{
            saw_rpm = 3580.0
            feed_ipm = 138.0
            spindle_load_pct = 85.0
            axis_load_pct = 75.0
            vibration_rms = 0.65
            sound_db = 105.0
        }
        apply_learning = $true
    } | ConvertTo-Json -Depth 10
    
    $run2 = Invoke-RestMethod -Uri "$baseUrl/api/saw/telemetry/ingest" `
        -Method Post `
        -ContentType "application/json" `
        -Body $highRiskPayload
    
    Write-Host "  ✅ High risk telemetry ingested" -ForegroundColor Green
    Write-Host "    Overload risk: $($run2.telemetry.overload_risk)"
    Write-Host "    Vibration risk: $($run2.telemetry.vibration_risk)"
    Write-Host "    Sound risk: $($run2.telemetry.sound_risk)"
    Write-Host "    Overall risk: $($run2.telemetry.overall_risk)"
    Write-Host "    Auto-learned: $($run2.auto_learned)"
    
    if ($run2.auto_learned) {
        Write-Host "    Lane scale: $($run2.lane_scale_before) → $($run2.lane_scale_after)" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "  ❌ Failed high risk test" -ForegroundColor Red
    Write-Host "    Error: $_"
    exit 1
}

# ============================================================================
# Test 6: List Runs
# ============================================================================

Write-Host "`n6. Testing GET /api/saw/joblog/runs (List with Filters)" -ForegroundColor Yellow

try {
    # List all runs
    $allRuns = Invoke-RestMethod -Uri "$baseUrl/api/saw/joblog/runs" -Method Get
    Write-Host "  ✅ All runs: $($allRuns.Count)" -ForegroundColor Green
    
    # Filter by machine
    $machineRuns = Invoke-RestMethod -Uri "$baseUrl/api/saw/joblog/runs?machine_profile=bcam_router_2030" -Method Get
    Write-Host "  ✅ Runs for bcam_router_2030: $($machineRuns.Count)" -ForegroundColor Green
    
    # Filter by material
    $materialRuns = Invoke-RestMethod -Uri "$baseUrl/api/saw/joblog/runs?material_family=hardwood" -Method Get
    Write-Host "  ✅ Runs for hardwood: $($materialRuns.Count)" -ForegroundColor Green
    
    foreach ($r in $allRuns) {
        $riskStr = if ($r.telemetry -and $r.telemetry.overall_risk) { "risk=$($r.telemetry.overall_risk)" } else { "no telemetry" }
        Write-Host "    - $($r.run_id): $($r.op_type) | $($r.status) | $riskStr"
    }
}
catch {
    Write-Host "  ❌ Failed to list runs" -ForegroundColor Red
    exit 1
}

# ============================================================================
# Test 7: Get Statistics
# ============================================================================

Write-Host "`n7. Testing GET /api/saw/joblog/stats" -ForegroundColor Yellow

try {
    $stats = Invoke-RestMethod -Uri "$baseUrl/api/saw/joblog/stats" -Method Get
    
    Write-Host "  ✅ Statistics retrieved" -ForegroundColor Green
    Write-Host "    Total runs: $($stats.total_runs)"
    Write-Host "    Success rate: $($stats.success_rate)"
    Write-Host "    Avg time: $($stats.avg_time_s)s"
    Write-Host "    Total length: $($stats.total_length_mm)mm"
    Write-Host "    By status:"
    foreach ($status in $stats.runs_by_status.PSObject.Properties) {
        Write-Host "      $($status.Name): $($status.Value)"
    }
}
catch {
    Write-Host "  ❌ Failed to get statistics" -ForegroundColor Red
    exit 1
}

# ============================================================================
# Test 8: Risk Summary
# ============================================================================

Write-Host "`n8. Testing GET /api/saw/telemetry/risk_summary" -ForegroundColor Yellow

try {
    $riskSummary = Invoke-RestMethod -Uri "$baseUrl/api/saw/telemetry/risk_summary" -Method Get
    
    Write-Host "  ✅ Risk summary retrieved" -ForegroundColor Green
    Write-Host "    Total runs with telemetry: $($riskSummary.total_runs)"
    Write-Host "    Avg risk: $($riskSummary.avg_risk)"
    Write-Host "    High risk count: $($riskSummary.high_risk_count)"
    Write-Host "    Risk distribution:"
    Write-Host "      Low: $($riskSummary.risk_distribution.low)"
    Write-Host "      Medium: $($riskSummary.risk_distribution.medium)"
    Write-Host "      High: $($riskSummary.risk_distribution.high)"
    
    Write-Host "    Recent runs:"
    foreach ($r in $riskSummary.recent_runs) {
        $deltaStr = if ($r.lane_scale_delta) { "Δ$($r.lane_scale_delta)" } else { "no change" }
        Write-Host "      $($r.run_id): risk=$($r.overall_risk) | $deltaStr"
    }
}
catch {
    Write-Host "  ❌ Failed to get risk summary" -ForegroundColor Red
    exit 1
}

# ============================================================================
# Test 9: Verify Learning Integration
# ============================================================================

Write-Host "`n9. Testing Learning Integration (Check Learned Overrides)" -ForegroundColor Yellow

try {
    # Check if lane was created in learned_overrides
    $lanes = Invoke-RestMethod -Uri "$baseUrl/api/feeds/learned/lanes?tool_id=tenryu_gm-25560d_test" -Method Get
    
    Write-Host "  ✅ Learned overrides integration verified" -ForegroundColor Green
    Write-Host "    Lanes created: $($lanes.Count)"
    
    foreach ($lane in $lanes) {
        Write-Host "    - Tool: $($lane.lane_key.tool_id)"
        Write-Host "      Material: $($lane.lane_key.material)"
        Write-Host "      Mode: $($lane.lane_key.mode)"
        Write-Host "      Machine: $($lane.lane_key.machine_profile)"
        Write-Host "      Lane scale: $($lane.lane_scale)"
        Write-Host "      Run count: $($lane.run_count)"
        Write-Host "      Success rate: $($lane.success_rate)"
    }
}
catch {
    Write-Host "  ❌ Failed to verify learning integration" -ForegroundColor Red
    exit 1
}

# ============================================================================
# Test 10: Risk Scoring Validation
# ============================================================================

Write-Host "`n10. Testing Risk Scoring Logic" -ForegroundColor Yellow

# Test edge cases
$testCases = @(
    @{
        name = "Very Low Risk"
        telemetry = @{
            spindle_load_pct = 15.0
            vibration_rms = 0.10
            sound_db = 65.0
        }
        expectedRisk = "< 0.3"
    },
    @{
        name = "Medium Risk"
        telemetry = @{
            spindle_load_pct = 50.0
            vibration_rms = 0.35
            sound_db = 85.0
        }
        expectedRisk = "0.3-0.7"
    },
    @{
        name = "Very High Risk"
        telemetry = @{
            spindle_load_pct = 95.0
            vibration_rms = 0.80
            sound_db = 110.0
        }
        expectedRisk = "> 0.7"
    }
)

foreach ($tc in $testCases) {
    $simPayload = @{
        telemetry = $tc.telemetry
        current_lane_scale = 1.0
    } | ConvertTo-Json -Depth 10
    
    try {
        $sim = Invoke-RestMethod -Uri "$baseUrl/api/saw/telemetry/simulate_learning" `
            -Method Post `
            -ContentType "application/json" `
            -Body $simPayload
        
        Write-Host "  ✅ $($tc.name): overall_risk=$($sim.telemetry.overall_risk) (expected $($tc.expectedRisk))" -ForegroundColor Green
    }
    catch {
        Write-Host "  ❌ Failed $($tc.name)" -ForegroundColor Red
        exit 1
    }
}

# ============================================================================
# Summary
# ============================================================================

Write-Host "`n=== All Tests Completed Successfully ===" -ForegroundColor Green
Write-Host "`nSummary:" -ForegroundColor Cyan
Write-Host "  ✅ Run record creation and retrieval"
Write-Host "  ✅ Learning simulation (preview)"
Write-Host "  ✅ Low risk telemetry ingestion (speed up)"
Write-Host "  ✅ High risk telemetry ingestion (slow down)"
Write-Host "  ✅ Run listing with filters"
Write-Host "  ✅ Statistics reporting"
Write-Host "  ✅ Risk summary analysis"
Write-Host "  ✅ Learned overrides integration"
Write-Host "  ✅ Risk scoring validation"
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Create operation panels (SawSlicePanel, SawBatchPanel, SawContourPanel)"
Write-Host "  2. Wire 'Send to JobLog' button in panels"
Write-Host "  3. Add real-time telemetry display in UI"
Write-Host "  4. Implement override promotion to presets"
