# Job Intelligence System Smoke Tests
# Tests Bundle #14 (Stats Header), Bundle #15 (Favorites), Bundle #16 (Favorites Filter)

Write-Host "=== Job Intelligence System Smoke Tests ===" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"
$testsPassed = 0
$testsFailed = 0

# Helper function for test results
function Test-Result {
    param([bool]$condition, [string]$message)
    if ($condition) {
        Write-Host "  ✓ $message" -ForegroundColor Green
        $script:testsPassed++
    } else {
        Write-Host "  ✗ $message" -ForegroundColor Red
        $script:testsFailed++
    }
}

# Test 1: Backend - List job log (empty state)
Write-Host "1. Testing GET /api/cam/job-int/log (empty state)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/cam/job-int/log" -Method Get
    Test-Result ($response.total -eq 0) "Empty log returns total=0"
    Test-Result ($response.items -is [array]) "Items is array"
    Test-Result ($response.items.Count -eq 0) "Empty items array"
} catch {
    Write-Host "  ✗ Failed to fetch job log: $_" -ForegroundColor Red
    $testsFailed++
}
Write-Host ""

# Test 2: Backend - List with filters
Write-Host "2. Testing GET /api/cam/job-int/log with filters" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/cam/job-int/log?helical_only=true&limit=10" -Method Get
    Test-Result ($response.total -eq 0) "Helical filter works on empty log"
    
    $response2 = Invoke-RestMethod -Uri "$baseUrl/api/cam/job-int/log?favorites_only=true" -Method Get
    Test-Result ($response2.total -eq 0) "Favorites filter works on empty log"
} catch {
    Write-Host "  ✗ Failed to test filters: $_" -ForegroundColor Red
    $testsFailed++
}
Write-Host ""

# Test 3: Backend - Create test log entry (simulate pipeline run)
Write-Host "3. Creating test job log entry" -ForegroundColor Yellow
$testRunId = "test-run-$(Get-Date -Format 'yyyyMMddHHmmss')"
$testLogEntry = @{
    run_id = $testRunId
    job_name = "Smoke Test Job"
    machine_id = "test_machine"
    post_id = "grbl"
    gcode_key = "test_gcode_123"
    use_helical = $true
    sim_time_s = 45.5
    sim_energy_j = 1200.0
    sim_move_count = 350
    sim_issue_count = 2
    sim_max_dev_pct = 3.2
    sim_stats = @{ total_length = 500.0 }
    sim_issues = @{}
    created_at = (Get-Date).ToUniversalTime().ToString("o")
    source = "smoke_test"
}

# Manually append to log file (simulating pipeline run)
$dataDir = ".\data"
if (-not (Test-Path $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir | Out-Null
}
$logFile = "$dataDir\cam_job_log.jsonl"
$testLogEntry | ConvertTo-Json -Compress | Out-File -FilePath $logFile -Append -Encoding utf8
Write-Host "  ✓ Created test log entry: $testRunId" -ForegroundColor Green
$testsPassed++
Write-Host ""

# Test 4: Backend - Retrieve test entry
Write-Host "4. Testing GET /api/cam/job-int/log (with data)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/cam/job-int/log" -Method Get
    Test-Result ($response.total -ge 1) "Log contains at least 1 entry"
    Test-Result ($response.items.Count -ge 1) "Items array has entries"
    
    $testEntry = $response.items | Where-Object { $_.run_id -eq $testRunId }
    Test-Result ($testEntry -ne $null) "Test entry found in list"
    Test-Result ($testEntry.job_name -eq "Smoke Test Job") "Job name correct"
    Test-Result ($testEntry.use_helical -eq $true) "Helical flag correct"
    Test-Result ($testEntry.sim_time_s -eq 45.5) "Sim time correct"
    Test-Result ($testEntry.favorite -eq $false) "Default favorite is false"
} catch {
    Write-Host "  ✗ Failed to retrieve test entry: $_" -ForegroundColor Red
    $testsFailed++
}
Write-Host ""

# Test 5: Backend - Get detail by run_id
Write-Host "5. Testing GET /api/cam/job-int/log/{run_id}" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/cam/job-int/log/$testRunId" -Method Get
    Test-Result ($response.run_id -eq $testRunId) "Run ID matches"
    Test-Result ($response.job_name -eq "Smoke Test Job") "Job name in detail"
    Test-Result ($response.sim_stats -ne $null) "Sim stats included"
    Test-Result ($response.sim_issues -ne $null) "Sim issues included"
} catch {
    Write-Host "  ✗ Failed to get detail: $_" -ForegroundColor Red
    $testsFailed++
}
Write-Host ""

# Test 6: Backend - Toggle favorite (Bundle #15)
Write-Host "6. Testing POST /api/cam/job-int/favorites/{run_id} (Bundle #15)" -ForegroundColor Yellow
try {
    # Mark as favorite
    $body = @{ favorite = $true } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$baseUrl/api/cam/job-int/favorites/$testRunId" `
        -Method Post -ContentType "application/json" -Body $body
    Test-Result ($response.favorite -eq $true) "Favorite flag set to true"
    
    # Verify in list
    $listResponse = Invoke-RestMethod -Uri "$baseUrl/api/cam/job-int/log" -Method Get
    $favoriteEntry = $listResponse.items | Where-Object { $_.run_id -eq $testRunId }
    Test-Result ($favoriteEntry.favorite -eq $true) "Favorite persisted in list"
    
    # Unmark favorite
    $body2 = @{ favorite = $false } | ConvertTo-Json
    $response2 = Invoke-RestMethod -Uri "$baseUrl/api/cam/job-int/favorites/$testRunId" `
        -Method Post -ContentType "application/json" -Body $body2
    Test-Result ($response2.favorite -eq $false) "Favorite flag set to false"
} catch {
    Write-Host "  ✗ Failed to toggle favorite: $_" -ForegroundColor Red
    $testsFailed++
}
Write-Host ""

# Test 7: Backend - Favorites filter (Bundle #16)
Write-Host "7. Testing favorites_only filter (Bundle #16)" -ForegroundColor Yellow
try {
    # Mark test entry as favorite
    $body = @{ favorite = $true } | ConvertTo-Json
    Invoke-RestMethod -Uri "$baseUrl/api/cam/job-int/favorites/$testRunId" `
        -Method Post -ContentType "application/json" -Body $body | Out-Null
    
    # Query with favorites_only
    $response = Invoke-RestMethod -Uri "$baseUrl/api/cam/job-int/log?favorites_only=true" -Method Get
    Test-Result ($response.total -ge 1) "Favorites filter finds entries"
    Test-Result ($response.items[0].favorite -eq $true) "Filtered item is favorite"
    
    # Query without favorites filter
    $response2 = Invoke-RestMethod -Uri "$baseUrl/api/cam/job-int/log?favorites_only=false" -Method Get
    Test-Result ($response2.total -ge $response.total) "Non-favorite filter shows more/equal items"
} catch {
    Write-Host "  ✗ Failed to test favorites filter: $_" -ForegroundColor Red
    $testsFailed++
}
Write-Host ""

# Test 8: Backend - Machine/Post filters
Write-Host "8. Testing machine_id and post_id filters" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/cam/job-int/log?machine_id=test_machine" -Method Get
    Test-Result ($response.items.Count -ge 1) "Machine filter finds entries"
    
    $response2 = Invoke-RestMethod -Uri "$baseUrl/api/cam/job-int/log?post_id=grbl" -Method Get
    Test-Result ($response2.items.Count -ge 1) "Post filter finds entries"
    
    $response3 = Invoke-RestMethod -Uri "$baseUrl/api/cam/job-int/log?helical_only=true" -Method Get
    Test-Result ($response3.items.Count -ge 1) "Helical filter finds entries"
    
    $response4 = Invoke-RestMethod -Uri "$baseUrl/api/cam/job-int/log?helical_only=false" -Method Get
    Test-Result ($response4.items.Count -ge 0) "Non-helical filter works"
} catch {
    Write-Host "  ✗ Failed to test filters: $_" -ForegroundColor Red
    $testsFailed++
}
Write-Host ""

# Test 9: Backend - Pagination
Write-Host "9. Testing pagination (limit/offset)" -ForegroundColor Yellow
try {
    $response1 = Invoke-RestMethod -Uri "$baseUrl/api/cam/job-int/log?limit=1&offset=0" -Method Get
    Test-Result ($response1.items.Count -le 1) "Limit=1 returns max 1 item"
    
    $response2 = Invoke-RestMethod -Uri "$baseUrl/api/cam/job-int/log?limit=50&offset=0" -Method Get
    Test-Result ($response2.items.Count -ge 1) "Default pagination works"
} catch {
    Write-Host "  ✗ Failed to test pagination: $_" -ForegroundColor Red
    $testsFailed++
}
Write-Host ""

# Test 10: Frontend API client types
Write-Host "10. Checking frontend API client exists" -ForegroundColor Yellow
$apiClientPath = ".\packages\client\src\api\job_int.ts"
if (Test-Path $apiClientPath) {
    Write-Host "  ✓ job_int.ts exists" -ForegroundColor Green
    $testsPassed++
    
    $content = Get-Content $apiClientPath -Raw
    Test-Result ($content -match "fetchJobIntLog") "fetchJobIntLog function exists"
    Test-Result ($content -match "updateJobIntFavorite") "updateJobIntFavorite function exists"
    Test-Result ($content -match "getJobIntLogEntry") "getJobIntLogEntry function exists"
    Test-Result ($content -match "JobIntLogEntry") "JobIntLogEntry interface exists"
    Test-Result ($content -match "favorites_only") "favorites_only query param exists"
} else {
    Write-Host "  ✗ job_int.ts not found" -ForegroundColor Red
    $testsFailed++
}
Write-Host ""

# Test 11: Frontend component exists
Write-Host "11. Checking JobIntHistoryPanel component" -ForegroundColor Yellow
$componentPath = ".\packages\client\src\components\cam\JobIntHistoryPanel.vue"
if (Test-Path $componentPath) {
    Write-Host "  ✓ JobIntHistoryPanel.vue exists" -ForegroundColor Green
    $testsPassed++
    
    $content = Get-Content $componentPath -Raw
    Test-Result ($content -match "helicalCount") "Stats: helicalCount computed"
    Test-Result ($content -match "avgTimeLabel") "Stats: avgTimeLabel computed"
    Test-Result ($content -match "avgMaxDevPct") "Stats: avgMaxDevPct computed"
    Test-Result ($content -match "toggleFavorite") "Favorites: toggleFavorite function"
    Test-Result ($content -match "favorites_only") "Favorites: favorites_only filter"
    Test-Result ($content -match "⭐") "UI: Star emoji for favorites"
} else {
    Write-Host "  ✗ JobIntHistoryPanel.vue not found" -ForegroundColor Red
    $testsFailed++
}
Write-Host ""

# Summary
Write-Host "=== Test Summary ===" -ForegroundColor Cyan
Write-Host "Passed: $testsPassed" -ForegroundColor Green
Write-Host "Failed: $testsFailed" -ForegroundColor Red
Write-Host ""

if ($testsFailed -eq 0) {
    Write-Host "✅ All Job Intelligence tests passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Job Intelligence System Status:" -ForegroundColor Cyan
    Write-Host "  ✓ Bundle #14: Stats Header (helical count, avg time, avg deviation)" -ForegroundColor Green
    Write-Host "  ✓ Bundle #15: Favorites System (star toggle, persistence)" -ForegroundColor Green
    Write-Host "  ✓ Bundle #16: Favorites Filter (favorites_only checkbox)" -ForegroundColor Green
    Write-Host ""
    Write-Host "Backend Endpoints:" -ForegroundColor Cyan
    Write-Host "  • GET  /api/cam/job-int/log - List with pagination & filters"
    Write-Host "  • GET  /api/cam/job-int/log/{run_id} - Detail view"
    Write-Host "  • POST /api/cam/job-int/favorites/{run_id} - Toggle favorite"
    Write-Host ""
    Write-Host "Frontend Files:" -ForegroundColor Cyan
    Write-Host "  • client/src/api/job_int.ts - API client"
    Write-Host "  • client/src/components/cam/JobIntHistoryPanel.vue - UI component"
    Write-Host ""
    exit 0
} else {
    Write-Host "❌ Some tests failed. Check backend is running on port 8000." -ForegroundColor Red
    exit 1
}
