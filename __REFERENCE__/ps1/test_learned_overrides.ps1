#!/usr/bin/env pwsh
# Test CP-S52: Learned Overrides (4-tuple lane learning)
# Tests lane creation, override management, merge logic, audit trail

$ErrorActionPreference = "Stop"
$baseUrl = "http://localhost:8000"

Write-Host "`n=== Testing CP-S52: Learned Overrides ===" -ForegroundColor Cyan

# ============================================================================
# Test 1: Create Lane and Set Override
# ============================================================================

Write-Host "`n1. Testing POST /api/feeds/learned/override (Set Feed Override)" -ForegroundColor Yellow

$laneKey1 = @{
    tool_id = "tenryu_gm-25560d_test"
    material = "hardwood"
    mode = "crosscut"
    machine_profile = "bcam_router_2030"
}

$overridePayload = @{
    lane_key = $laneKey1
    param_name = "feed_ipm"
    value = 150.0
    source = "manual"
    scale = 1.25
    confidence = 0.9
    operator = "test_operator"
    notes = "Increased feed for better finish"
    reason = "Previous feed too slow, caused burning"
} | ConvertTo-Json -Depth 10

try {
    $override = Invoke-RestMethod -Uri "$baseUrl/api/feeds/learned/override" `
        -Method Post `
        -ContentType "application/json" `
        -Body $overridePayload
    
    Write-Host "  ✅ Override created successfully" -ForegroundColor Green
    Write-Host "    Param: $($override.param_name)"
    Write-Host "    Value: $($override.value)"
    Write-Host "    Scale: $($override.scale)"
    Write-Host "    Source: $($override.source)"
    Write-Host "    Confidence: $($override.confidence)"
}
catch {
    Write-Host "  ❌ Failed to set override" -ForegroundColor Red
    Write-Host "    Error: $_"
    exit 1
}

# ============================================================================
# Test 2: Get Lane
# ============================================================================

Write-Host "`n2. Testing GET /api/feeds/learned/lanes/{lane_id}" -ForegroundColor Yellow

$laneUrl = "$baseUrl/api/feeds/learned/lanes/$($laneKey1.tool_id)/$($laneKey1.material)/$($laneKey1.mode)/$($laneKey1.machine_profile)"

try {
    $lane = Invoke-RestMethod -Uri $laneUrl -Method Get
    
    Write-Host "  ✅ Lane retrieved successfully" -ForegroundColor Green
    Write-Host "    Tool: $($lane.lane_key.tool_id)"
    Write-Host "    Material: $($lane.lane_key.material)"
    Write-Host "    Mode: $($lane.lane_key.mode)"
    Write-Host "    Machine: $($lane.lane_key.machine_profile)"
    Write-Host "    Overrides: $($lane.overrides.Count)"
    Write-Host "    Lane Scale: $($lane.lane_scale)"
    Write-Host "    Run Count: $($lane.run_count)"
}
catch {
    Write-Host "  ❌ Failed to get lane" -ForegroundColor Red
    exit 1
}

# ============================================================================
# Test 3: Set Multiple Overrides
# ============================================================================

Write-Host "`n3. Testing Multiple Parameter Overrides" -ForegroundColor Yellow

$rpmOverride = @{
    lane_key = $laneKey1
    param_name = "rpm"
    value = 3800.0
    source = "auto_learn"
    scale = 1.05
    confidence = 0.95
    reason = "Learned from successful runs"
} | ConvertTo-Json -Depth 10

$docOverride = @{
    lane_key = $laneKey1
    param_name = "doc_mm"
    value = 12.0
    source = "auto_learn"
    scale = 1.2
    confidence = 0.85
    reason = "Increased DOC based on telemetry"
} | ConvertTo-Json -Depth 10

try {
    $rpm = Invoke-RestMethod -Uri "$baseUrl/api/feeds/learned/override" `
        -Method Post `
        -ContentType "application/json" `
        -Body $rpmOverride
    
    $doc = Invoke-RestMethod -Uri "$baseUrl/api/feeds/learned/override" `
        -Method Post `
        -ContentType "application/json" `
        -Body $docOverride
    
    Write-Host "  ✅ Multiple overrides created" -ForegroundColor Green
    Write-Host "    RPM: $($rpm.value) (scale $($rpm.scale))"
    Write-Host "    DOC: $($doc.value)mm (scale $($doc.scale))"
}
catch {
    Write-Host "  ❌ Failed to set overrides" -ForegroundColor Red
    exit 1
}

# ============================================================================
# Test 4: Update Lane Scale
# ============================================================================

Write-Host "`n4. Testing POST /api/feeds/learned/lane_scale" -ForegroundColor Yellow

$laneScalePayload = @{
    lane_key = $laneKey1
    lane_scale = 1.1
    source = "auto_learn"
    operator = "system"
    reason = "Overall improvement based on success rate"
} | ConvertTo-Json -Depth 10

try {
    $result = Invoke-RestMethod -Uri "$baseUrl/api/feeds/learned/lane_scale" `
        -Method Post `
        -ContentType "application/json" `
        -Body $laneScalePayload
    
    Write-Host "  ✅ Lane scale updated" -ForegroundColor Green
    Write-Host "    Message: $($result.message)"
}
catch {
    Write-Host "  ❌ Failed to update lane scale" -ForegroundColor Red
    exit 1
}

# ============================================================================
# Test 5: Merge Parameters
# ============================================================================

Write-Host "`n5. Testing POST /api/feeds/learned/merge (Merge Logic)" -ForegroundColor Yellow

$mergePayload = @{
    baseline = @{
        feed_ipm = 120.0
        rpm = 3600.0
        doc_mm = 10.0
        safe_z = 5.0
    }
    lane_key = $laneKey1
} | ConvertTo-Json -Depth 10

try {
    $merge = Invoke-RestMethod -Uri "$baseUrl/api/feeds/learned/merge" `
        -Method Post `
        -ContentType "application/json" `
        -Body $mergePayload
    
    Write-Host "  ✅ Parameters merged successfully" -ForegroundColor Green
    Write-Host "    Baseline feed_ipm: $($merge.baseline.feed_ipm)"
    Write-Host "    Merged feed_ipm: $($merge.merged.feed_ipm)"
    Write-Host "    Baseline rpm: $($merge.baseline.rpm)"
    Write-Host "    Merged rpm: $($merge.merged.rpm)"
    Write-Host "    Baseline doc_mm: $($merge.baseline.doc_mm)"
    Write-Host "    Merged doc_mm: $($merge.merged.doc_mm)"
    Write-Host "    Lane scale: $($merge.lane_scale)"
    Write-Host "    Overrides applied: $($merge.overrides_applied -join ', ')"
}
catch {
    Write-Host "  ❌ Failed to merge parameters" -ForegroundColor Red
    exit 1
}

# ============================================================================
# Test 6: Record Successful Run
# ============================================================================

Write-Host "`n6. Testing POST /api/feeds/learned/record_run" -ForegroundColor Yellow

$recordRunPayload = @{
    lane_key = $laneKey1
    success = $true
} | ConvertTo-Json -Depth 10

try {
    $result = Invoke-RestMethod -Uri "$baseUrl/api/feeds/learned/record_run" `
        -Method Post `
        -ContentType "application/json" `
        -Body $recordRunPayload
    
    Write-Host "  ✅ Run recorded" -ForegroundColor Green
    Write-Host "    Message: $($result.message)"
    
    # Verify run count increased
    $lane = Invoke-RestMethod -Uri $laneUrl -Method Get
    Write-Host "    Run count: $($lane.run_count)"
    Write-Host "    Success rate: $($lane.success_rate)"
}
catch {
    Write-Host "  ❌ Failed to record run" -ForegroundColor Red
    exit 1
}

# ============================================================================
# Test 7: Create Second Lane (Different Machine)
# ============================================================================

Write-Host "`n7. Testing Second Lane (Different Machine)" -ForegroundColor Yellow

$laneKey2 = @{
    tool_id = "tenryu_gm-25560d_test"
    material = "hardwood"
    mode = "crosscut"
    machine_profile = "syil_x7"
}

$override2 = @{
    lane_key = $laneKey2
    param_name = "feed_ipm"
    value = 140.0
    source = "manual"
    scale = 1.17
    confidence = 0.8
    reason = "Different machine characteristics"
} | ConvertTo-Json -Depth 10

try {
    $result = Invoke-RestMethod -Uri "$baseUrl/api/feeds/learned/override" `
        -Method Post `
        -ContentType "application/json" `
        -Body $override2
    
    Write-Host "  ✅ Second lane created" -ForegroundColor Green
    Write-Host "    Machine: $($laneKey2.machine_profile)"
}
catch {
    Write-Host "  ❌ Failed to create second lane" -ForegroundColor Red
    exit 1
}

# ============================================================================
# Test 8: List Lanes with Filters
# ============================================================================

Write-Host "`n8. Testing GET /api/feeds/learned/lanes (List with Filters)" -ForegroundColor Yellow

try {
    # List all lanes
    $allLanes = Invoke-RestMethod -Uri "$baseUrl/api/feeds/learned/lanes" -Method Get
    Write-Host "  ✅ All lanes: $($allLanes.Count)" -ForegroundColor Green
    
    # Filter by tool
    $toolLanes = Invoke-RestMethod -Uri "$baseUrl/api/feeds/learned/lanes?tool_id=tenryu_gm-25560d_test" -Method Get
    Write-Host "  ✅ Lanes for tool: $($toolLanes.Count)" -ForegroundColor Green
    
    # Filter by machine
    $machineLanes = Invoke-RestMethod -Uri "$baseUrl/api/feeds/learned/lanes?machine_profile=bcam_router_2030" -Method Get
    Write-Host "  ✅ Lanes for bcam_router_2030: $($machineLanes.Count)" -ForegroundColor Green
    
    foreach ($lane in $allLanes) {
        Write-Host "    - $($lane.lane_key.tool_id) | $($lane.lane_key.material) | $($lane.lane_key.mode) | $($lane.lane_key.machine_profile)"
    }
}
catch {
    Write-Host "  ❌ Failed to list lanes" -ForegroundColor Red
    exit 1
}

# ============================================================================
# Test 9: Get Audit Trail
# ============================================================================

Write-Host "`n9. Testing GET /api/feeds/learned/audit (Audit Trail)" -ForegroundColor Yellow

try {
    $audit = Invoke-RestMethod -Uri "$baseUrl/api/feeds/learned/audit?limit=10" -Method Get
    
    Write-Host "  ✅ Audit entries retrieved: $($audit.Count)" -ForegroundColor Green
    
    foreach ($entry in $audit | Select-Object -First 3) {
        Write-Host "    [$($entry.timestamp)] $($entry.param_name): $($entry.prev_value) → $($entry.new_value) (source: $($entry.source))"
        if ($entry.reason) {
            Write-Host "      Reason: $($entry.reason)"
        }
    }
}
catch {
    Write-Host "  ❌ Failed to get audit trail" -ForegroundColor Red
    exit 1
}

# ============================================================================
# Test 10: Get Statistics
# ============================================================================

Write-Host "`n10. Testing GET /api/feeds/learned/stats" -ForegroundColor Yellow

try {
    $stats = Invoke-RestMethod -Uri "$baseUrl/api/feeds/learned/stats" -Method Get
    
    Write-Host "  ✅ Statistics retrieved" -ForegroundColor Green
    Write-Host "    Total lanes: $($stats.total_lanes)"
    Write-Host "    Total audit entries: $($stats.total_audit_entries)"
    Write-Host "    Overrides by source:"
    foreach ($source in $stats.overrides_by_source.PSObject.Properties) {
        Write-Host "      $($source.Name): $($source.Value)"
    }
    Write-Host "    Lanes by machine:"
    foreach ($machine in $stats.lanes_by_machine.PSObject.Properties) {
        Write-Host "      $($machine.Name): $($machine.Value)"
    }
}
catch {
    Write-Host "  ❌ Failed to get statistics" -ForegroundColor Red
    exit 1
}

# ============================================================================
# Test 11: Verify Merge Formula
# ============================================================================

Write-Host "`n11. Testing Merge Formula (baseline + override) * lane_scale" -ForegroundColor Yellow

# Expected calculation:
# feed_ipm: baseline=120.0, override_scale=1.25, lane_scale=1.1
#   → 120.0 * 1.25 * 1.1 = 165.0
# rpm: baseline=3600.0, override_scale=1.05, lane_scale=1.1
#   → 3600.0 * 1.05 * 1.1 = 4158.0
# doc_mm: baseline=10.0, override_scale=1.2, lane_scale=1.1
#   → 10.0 * 1.2 * 1.1 = 13.2

$expectedFeed = 120.0 * 1.25 * 1.1
$expectedRPM = 3600.0 * 1.05 * 1.1
$expectedDOC = 10.0 * 1.2 * 1.1

$tolerance = 0.01

if ([Math]::Abs($merge.merged.feed_ipm - $expectedFeed) -lt $tolerance) {
    Write-Host "  ✅ Feed merge correct: $($merge.merged.feed_ipm) ≈ $expectedFeed" -ForegroundColor Green
}
else {
    Write-Host "  ❌ Feed merge incorrect: $($merge.merged.feed_ipm) != $expectedFeed" -ForegroundColor Red
    exit 1
}

if ([Math]::Abs($merge.merged.rpm - $expectedRPM) -lt $tolerance) {
    Write-Host "  ✅ RPM merge correct: $($merge.merged.rpm) ≈ $expectedRPM" -ForegroundColor Green
}
else {
    Write-Host "  ❌ RPM merge incorrect: $($merge.merged.rpm) != $expectedRPM" -ForegroundColor Red
    exit 1
}

if ([Math]::Abs($merge.merged.doc_mm - $expectedDOC) -lt $tolerance) {
    Write-Host "  ✅ DOC merge correct: $($merge.merged.doc_mm) ≈ $expectedDOC" -ForegroundColor Green
}
else {
    Write-Host "  ❌ DOC merge incorrect: $($merge.merged.doc_mm) != $expectedDOC" -ForegroundColor Red
    exit 1
}

# ============================================================================
# Summary
# ============================================================================

Write-Host "`n=== All Tests Completed Successfully ===" -ForegroundColor Green
Write-Host "`nSummary:" -ForegroundColor Cyan
Write-Host "  ✅ Lane creation and override management"
Write-Host "  ✅ Multiple parameter overrides"
Write-Host "  ✅ Lane scale updates"
Write-Host "  ✅ Parameter merge logic verified"
Write-Host "  ✅ Run recording"
Write-Host "  ✅ Multi-machine support"
Write-Host "  ✅ Lane filtering"
Write-Host "  ✅ Audit trail tracking"
Write-Host "  ✅ Statistics reporting"
Write-Host "  ✅ Merge formula validation"
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Wire to CP-S60 Live Learn Ingestor"
Write-Host "  2. Add telemetry-based auto-learning"
Write-Host "  3. Implement override promotion to presets"
Write-Host "  4. Create UI for viewing/managing overrides"
