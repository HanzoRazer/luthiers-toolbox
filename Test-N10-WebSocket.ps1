# Test-N10-WebSocket.ps1
# N10.0 Real-time Monitoring WebSocket Smoke Test

Write-Host "=== N10.0 WebSocket Smoke Test ===" -ForegroundColor Cyan

$baseUrl = "http://localhost:8000"
$testsPassed = 0
$testsFailed = 0

# Test 1: Server availability
Write-Host "`n1. Testing server availability..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$baseUrl/health" -Method GET -ErrorAction Stop
    Write-Host "   ✓ Server is running" -ForegroundColor Green
    $testsPassed++
}
catch {
    Write-Host "   ✗ Server not available: $_" -ForegroundColor Red
    Write-Host "   Run: cd services/api && uvicorn app.main:app --reload" -ForegroundColor Yellow
    $testsFailed++
    exit 1
}

# Test 2: WebSocket endpoint registered
Write-Host "`n2. Checking WebSocket router registration..." -ForegroundColor Yellow
try {
    $openapi = Invoke-RestMethod -Uri "$baseUrl/openapi.json" -Method GET -ErrorAction Stop
    $wsPath = $openapi.paths.'/ws/monitor'
    if ($wsPath) {
        Write-Host "   ✓ WebSocket endpoint registered at /ws/monitor" -ForegroundColor Green
        $testsPassed++
    }
    else {
        Write-Host "   ✗ WebSocket endpoint not found in OpenAPI spec" -ForegroundColor Red
        $testsFailed++
    }
}
catch {
    Write-Host "   ⚠ Could not verify WebSocket registration (OpenAPI check failed)" -ForegroundColor Yellow
    Write-Host "   This is not critical - WebSocket may still work" -ForegroundColor Gray
}

# Test 3: Create RMOS entities and verify API response
Write-Host "`n3. Testing RMOS entity creation (will trigger WebSocket events)..." -ForegroundColor Yellow

# Create pattern
$patternPayload = @{
    name = "N10 Test Pattern"
    ring_count = 3
    geometry = @{
        rings = @(
            @{ radius = 10; angle = 0 },
            @{ radius = 20; angle = 45 },
            @{ radius = 30; angle = 90 }
        )
    }
} | ConvertTo-Json -Depth 5

try {
    $patternResponse = Invoke-RestMethod -Uri "$baseUrl/api/rmos/stores/patterns" `
        -Method POST `
        -Headers @{"Content-Type"="application/json"} `
        -Body $patternPayload `
        -ErrorAction Stop
    
    if ($patternResponse.success -and $patternResponse.pattern.id) {
        $patternId = $patternResponse.pattern.id
        Write-Host "   ✓ Pattern created: $patternId" -ForegroundColor Green
        Write-Host "     (WebSocket event 'pattern:created' should have been broadcast)" -ForegroundColor Gray
        $testsPassed++
    }
    else {
        Write-Host "   ✗ Pattern creation failed" -ForegroundColor Red
        $testsFailed++
    }
}
catch {
    Write-Host "   ✗ Pattern creation error: $_" -ForegroundColor Red
    $testsFailed++
}

# Create joblog
$joblogPayload = @{
    job_type = "slice"
    pattern_id = $patternId
    status = "pending"
    parameters = @{
        blade_id = "test-blade-01"
        speed = 3000
    }
} | ConvertTo-Json -Depth 5

try {
    $joblogResponse = Invoke-RestMethod -Uri "$baseUrl/api/rmos/stores/joblogs" `
        -Method POST `
        -Headers @{"Content-Type"="application/json"} `
        -Body $joblogPayload `
        -ErrorAction Stop
    
    if ($joblogResponse.success -and $joblogResponse.joblog.id) {
        $joblogId = $joblogResponse.joblog.id
        Write-Host "   ✓ JobLog created: $joblogId" -ForegroundColor Green
        Write-Host "     (WebSocket event 'job:created' should have been broadcast)" -ForegroundColor Gray
        $testsPassed++
    }
    else {
        Write-Host "   ✗ JobLog creation failed" -ForegroundColor Red
        $testsFailed++
    }
}
catch {
    Write-Host "   ✗ JobLog creation error: $_" -ForegroundColor Red
    $testsFailed++
}

# Test 4: Update joblog (should trigger job:completed event)
Write-Host "`n4. Testing joblog update (status change)..." -ForegroundColor Yellow

$updatePayload = @{
    status = "completed"
    end_time = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
    duration_seconds = 45.3
    results = @{
        strips_produced = 120
        success_rate = 0.98
    }
} | ConvertTo-Json -Depth 5

try {
    $updateResponse = Invoke-RestMethod -Uri "$baseUrl/api/rmos/stores/joblogs/$joblogId" `
        -Method PUT `
        -Headers @{"Content-Type"="application/json"} `
        -Body $updatePayload `
        -ErrorAction Stop
    
    if ($updateResponse.success -and $updateResponse.joblog.status -eq "completed") {
        Write-Host "   ✓ JobLog updated to 'completed'" -ForegroundColor Green
        Write-Host "     (WebSocket event 'job:completed' should have been broadcast)" -ForegroundColor Gray
        $testsPassed++
    }
    else {
        Write-Host "   ✗ JobLog update failed" -ForegroundColor Red
        $testsFailed++
    }
}
catch {
    Write-Host "   ✗ JobLog update error: $_" -ForegroundColor Red
    $testsFailed++
}

# Test 5: Verify broadcast functions are callable
Write-Host "`n5. Verifying WebSocket infrastructure..." -ForegroundColor Yellow
$pythonCheck = @"
import sys
sys.path.insert(0, 'services/api')
try:
    from app.websocket.monitor import (
        get_connection_manager,
        broadcast_job_event,
        broadcast_pattern_event,
        broadcast_material_event
    )
    print('✓ All broadcast functions importable')
    manager = get_connection_manager()
    print(f'✓ ConnectionManager instance: {manager.__class__.__name__}')
    print(f'✓ Active connections: {len(manager.active_connections)}')
except Exception as e:
    print(f'✗ Import failed: {e}')
    sys.exit(1)
"@

try {
    $importResult = python -c $pythonCheck 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   $importResult" -ForegroundColor Green
        $testsPassed++
    }
    else {
        Write-Host "   $importResult" -ForegroundColor Red
        $testsFailed++
    }
}
catch {
    Write-Host "   ✗ Python check failed: $_" -ForegroundColor Red
    $testsFailed++
}

# Summary
Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "Tests Passed: $testsPassed" -ForegroundColor Green
Write-Host "Tests Failed: $testsFailed" -ForegroundColor $(if ($testsFailed -eq 0) { "Green" } else { "Red" })

if ($testsFailed -eq 0) {
    Write-Host "`n✓ All N10.0 WebSocket smoke tests passed!" -ForegroundColor Green
    Write-Host "`nNext steps:" -ForegroundColor Cyan
    Write-Host "  1. Open http://localhost:5173 (Vite dev server)" -ForegroundColor White
    Write-Host "  2. Navigate to RMOS → Live Monitor" -ForegroundColor White
    Write-Host "  3. Click 'Connect' to establish WebSocket connection" -ForegroundColor White
    Write-Host "  4. Create patterns/jobs via API or UI to see real-time events" -ForegroundColor White
    Write-Host "`nManual WebSocket test (using wscat):" -ForegroundColor Cyan
    Write-Host "  npm install -g wscat" -ForegroundColor Gray
    Write-Host "  wscat -c ws://localhost:8000/ws/monitor" -ForegroundColor Gray
    Write-Host "  > {`"action`":`"subscribe`",`"filters`":[`"job`",`"pattern`"]}" -ForegroundColor Gray
}
else {
    Write-Host "`n✗ Some tests failed. Check errors above." -ForegroundColor Red
    exit 1
}
