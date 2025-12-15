# B19 Clone as Preset - Smoke Test
# Tests the JobInt → Preset cloning workflow

Write-Host "=== B19 Clone as Preset Smoke Test ===" -ForegroundColor Cyan
Write-Host ""

$API_BASE = "http://localhost:8000"
$errors = 0

# Test 1: Verify JobInt log endpoint exists
Write-Host "1. Testing JobInt log endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$API_BASE/api/cam/job-int/log?limit=1" -Method GET -ErrorAction Stop
    if ($response.total -ge 0 -and $response.items) {
        Write-Host "  ✓ JobInt log endpoint working (Total: $($response.total))" -ForegroundColor Green
        
        if ($response.items.Count -gt 0) {
            $sampleRun = $response.items[0]
            Write-Host "  ✓ Sample run found: $($sampleRun.job_name) ($($sampleRun.run_id.Substring(0,8))...)" -ForegroundColor Green
            $testRunId = $sampleRun.run_id
        } else {
            Write-Host "  ⚠ No job runs found in log (create test run first)" -ForegroundColor Yellow
            $testRunId = $null
        }
    } else {
        Write-Host "  ✗ Unexpected response format" -ForegroundColor Red
        $errors++
    }
} catch {
    Write-Host "  ✗ Failed to fetch JobInt log: $_" -ForegroundColor Red
    $errors++
}

Write-Host ""

# Test 2: Verify job detail endpoint (if we have a run)
if ($testRunId) {
    Write-Host "2. Testing JobInt detail endpoint..." -ForegroundColor Yellow
    try {
        $detailResponse = Invoke-RestMethod -Uri "$API_BASE/api/cam/job-int/log/$testRunId" -Method GET -ErrorAction Stop
        if ($detailResponse.run_id -eq $testRunId) {
            Write-Host "  ✓ Job detail retrieved successfully" -ForegroundColor Green
            Write-Host "    Machine: $($detailResponse.machine_id)" -ForegroundColor Gray
            Write-Host "    Post: $($detailResponse.post_id)" -ForegroundColor Gray
            Write-Host "    Helical: $($detailResponse.use_helical)" -ForegroundColor Gray
            Write-Host "    Time: $($detailResponse.sim_time_s)s" -ForegroundColor Gray
            
            if ($detailResponse.sim_stats) {
                Write-Host "  ✓ sim_stats present (needed for CAM params)" -ForegroundColor Green
            } else {
                Write-Host "  ⚠ sim_stats missing" -ForegroundColor Yellow
            }
        } else {
            Write-Host "  ✗ Unexpected run_id in response" -ForegroundColor Red
            $errors++
        }
    } catch {
        Write-Host "  ✗ Failed to fetch job detail: $_" -ForegroundColor Red
        $errors++
    }
} else {
    Write-Host "2. Skipping job detail test (no runs available)" -ForegroundColor Yellow
}

Write-Host ""

# Test 3: Verify preset creation endpoint
Write-Host "3. Testing preset creation endpoint (dry run)..." -ForegroundColor Yellow
try {
    $presetPayload = @{
        name = "B19 Smoke Test Preset"
        kind = "cam"
        description = "Test preset created by B19 smoke test"
        tags = @("test", "b19", "smoke")
        machine_id = "test_machine"
        post_id = "test_post"
        units = "mm"
        job_source_id = if ($testRunId) { $testRunId } else { "test-run-id" }
        cam_params = @{
            strategy = "Spiral"
            use_helical = $true
            stepover = 0.45
        }
    } | ConvertTo-Json -Depth 10
    
    $createResponse = Invoke-RestMethod -Uri "$API_BASE/api/presets" `
        -Method POST `
        -ContentType "application/json" `
        -Body $presetPayload `
        -ErrorAction Stop
    
    if ($createResponse.id -and $createResponse.name -eq "B19 Smoke Test Preset") {
        Write-Host "  ✓ Preset created successfully" -ForegroundColor Green
        Write-Host "    ID: $($createResponse.id)" -ForegroundColor Gray
        Write-Host "    Name: $($createResponse.name)" -ForegroundColor Gray
        Write-Host "    Kind: $($createResponse.kind)" -ForegroundColor Gray
        
        if ($createResponse.job_source_id) {
            Write-Host "  ✓ job_source_id field populated (B19 lineage tracking)" -ForegroundColor Green
        } else {
            Write-Host "  ⚠ job_source_id field missing" -ForegroundColor Yellow
        }
        
        # Cleanup: Delete test preset
        try {
            $deleteResponse = Invoke-RestMethod -Uri "$API_BASE/api/presets/$($createResponse.id)" `
                -Method DELETE `
                -ErrorAction Stop
            Write-Host "  ✓ Test preset cleaned up" -ForegroundColor Green
        } catch {
            Write-Host "  ⚠ Failed to cleanup test preset: $_" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ✗ Unexpected response format" -ForegroundColor Red
        $errors++
    }
} catch {
    Write-Host "  ✗ Failed to create preset: $_" -ForegroundColor Red
    $errors++
}

Write-Host ""

# Test 4: Verify preset list includes job_source_id
Write-Host "4. Testing preset list with job_source_id filter..." -ForegroundColor Yellow
try {
    $presetsResponse = Invoke-RestMethod -Uri "$API_BASE/api/presets?kind=cam" -Method GET -ErrorAction Stop
    
    if ($presetsResponse -is [Array]) {
        $presetsWithSource = $presetsResponse | Where-Object { $_.job_source_id }
        Write-Host "  ✓ Preset list retrieved" -ForegroundColor Green
        Write-Host "    Total CAM presets: $($presetsResponse.Count)" -ForegroundColor Gray
        Write-Host "    Presets with job_source_id: $($presetsWithSource.Count)" -ForegroundColor Gray
        
        if ($presetsWithSource.Count -gt 0) {
            Write-Host "  ✓ Found presets with job lineage (B19 working)" -ForegroundColor Green
        } else {
            Write-Host "  ℹ No presets with job_source_id yet (expected if no clones created)" -ForegroundColor Cyan
        }
    } else {
        Write-Host "  ✗ Unexpected response format" -ForegroundColor Red
        $errors++
    }
} catch {
    Write-Host "  ✗ Failed to fetch presets: $_" -ForegroundColor Red
    $errors++
}

Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan

if ($errors -eq 0) {
    Write-Host "✅ All B19 smoke tests passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "  1. Start frontend: cd packages/client && npm run dev" -ForegroundColor Gray
    Write-Host "  2. Open CAM Essentials or PipelineLab" -ForegroundColor Gray
    Write-Host "  3. Find JobInt History panel" -ForegroundColor Gray
    Write-Host "  4. Click '📋 Clone' button on any job" -ForegroundColor Gray
    Write-Host "  5. Fill preset name and click 'Create Preset'" -ForegroundColor Gray
    Write-Host "  6. Verify preset appears in Preset Hub" -ForegroundColor Gray
    exit 0
} else {
    Write-Host "❌ $errors test(s) failed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  - Ensure API server is running: uvicorn app.main:app --reload" -ForegroundColor Gray
    Write-Host "  - Check API logs for errors" -ForegroundColor Gray
    Write-Host "  - Verify presets.json file exists in services/api/data/presets/" -ForegroundColor Gray
    Write-Host "  - Run pipeline to generate test JobInt entries" -ForegroundColor Gray
    exit 1
}
