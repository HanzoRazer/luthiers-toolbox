# Test Pipeline Preset Validation
# Verifies the pipeline spec validator prevents bad presets

Write-Host "`n=== Testing Pipeline Preset Validation ===" -ForegroundColor Cyan

# Test 1: Valid preset with proper spec
Write-Host "`n1. Testing valid preset creation..." -ForegroundColor Yellow
$validPreset = @{
    name = "Test Valid Preset"
    description = "Valid pipeline spec"
    units = "mm"
    machine_id = "haas_mini"
    post_id = "GRBL"
    spec = @{
        ops = @(
            @{ kind = "dxf_preflight"; params = @{} }
            @{ kind = "adaptive_plan"; params = @{} }
            @{ kind = "adaptive_plan_run"; params = @{} }
        )
        tool_d = 6.0
        units = "mm"
        geometry_layer = "GEOMETRY"
    }
} | ConvertTo-Json -Depth 10

try {
    $response = curl -X POST http://localhost:8000/cam/pipeline/presets `
        -H "Content-Type: application/json" `
        -d $validPreset `
        2>&1 | Out-String
    
    if ($response -match '"id"' -and $response -match '"name"') {
        Write-Host "  ✓ Valid preset created successfully" -ForegroundColor Green
        # Clean up - extract ID and delete
        if ($response -match '"id":\s*"([^"]+)"') {
            $presetId = $matches[1]
            curl -X DELETE "http://localhost:8000/cam/pipeline/presets/$presetId" 2>&1 | Out-Null
            Write-Host "  ✓ Cleanup: Deleted test preset" -ForegroundColor Gray
        }
    } else {
        Write-Host "  ✗ Unexpected response: $response" -ForegroundColor Red
    }
} catch {
    Write-Host "  ✗ Request failed: $_" -ForegroundColor Red
}

# Test 2: Invalid preset - bad ops kind
Write-Host "`n2. Testing invalid preset (bad op kind)..." -ForegroundColor Yellow
$invalidPreset = @{
    name = "Test Invalid Preset"
    description = "Invalid op kind"
    units = "mm"
    spec = @{
        ops = @(
            @{ kind = "invalid_operation"; params = @{} }
        )
        tool_d = 6.0
        units = "mm"
    }
} | ConvertTo-Json -Depth 10

try {
    $response = curl -X POST http://localhost:8000/cam/pipeline/presets `
        -H "Content-Type: application/json" `
        -d $invalidPreset `
        2>&1 | Out-String
    
    if ($response -match '422' -or $response -match 'Unknown op kind') {
        Write-Host "  ✓ Validation correctly rejected bad op kind" -ForegroundColor Green
        if ($response -match '"errors"') {
            Write-Host "  ✓ Detailed errors returned" -ForegroundColor Green
        }
    } else {
        Write-Host "  ✗ Should have rejected invalid kind: $response" -ForegroundColor Red
    }
} catch {
    Write-Host "  ✗ Request failed: $_" -ForegroundColor Red
}

# Test 3: Invalid preset - missing required params
Write-Host "`n3. Testing invalid preset (export_post without endpoint)..." -ForegroundColor Yellow
$invalidExport = @{
    name = "Test Invalid Export"
    description = "export_post without endpoint"
    units = "mm"
    spec = @{
        ops = @(
            @{ kind = "adaptive_plan_run"; params = @{} }
            @{ kind = "export_post"; params = @{} }  # Missing endpoint
        )
        tool_d = 6.0
        units = "mm"
    }
} | ConvertTo-Json -Depth 10

try {
    $response = curl -X POST http://localhost:8000/cam/pipeline/presets `
        -H "Content-Type: application/json" `
        -d $invalidExport `
        2>&1 | Out-String
    
    if ($response -match '422' -or $response -match 'endpoint') {
        Write-Host "  ✓ Validation correctly rejected export_post without endpoint" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Should have rejected missing endpoint: $response" -ForegroundColor Red
    }
} catch {
    Write-Host "  ✗ Request failed: $_" -ForegroundColor Red
}

# Test 4: Invalid preset - bad tool_d
Write-Host "`n4. Testing invalid preset (negative tool_d)..." -ForegroundColor Yellow
$invalidToolD = @{
    name = "Test Invalid ToolD"
    description = "Negative tool diameter"
    units = "mm"
    spec = @{
        ops = @(
            @{ kind = "adaptive_plan_run"; params = @{} }
        )
        tool_d = -6.0  # Negative!
        units = "mm"
    }
} | ConvertTo-Json -Depth 10

try {
    $response = curl -X POST http://localhost:8000/cam/pipeline/presets `
        -H "Content-Type: application/json" `
        -d $invalidToolD `
        2>&1 | Out-String
    
    if ($response -match '422' -or $response -match 'tool_d') {
        Write-Host "  ✓ Validation correctly rejected negative tool_d" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Should have rejected negative tool_d: $response" -ForegroundColor Red
    }
} catch {
    Write-Host "  ✗ Request failed: $_" -ForegroundColor Red
}

# Test 5: Valid preset without spec (legacy support)
Write-Host "`n5. Testing valid preset without spec (legacy)..." -ForegroundColor Yellow
$legacyPreset = @{
    name = "Test Legacy Preset"
    description = "No spec field (backward compatible)"
    units = "mm"
    machine_id = "haas_mini"
    post_id = "GRBL"
} | ConvertTo-Json -Depth 10

try {
    $response = curl -X POST http://localhost:8000/cam/pipeline/presets `
        -H "Content-Type: application/json" `
        -d $legacyPreset `
        2>&1 | Out-String
    
    if ($response -match '"id"' -and $response -match '"name"') {
        Write-Host "  ✓ Legacy preset (no spec) created successfully" -ForegroundColor Green
        # Clean up
        if ($response -match '"id":\s*"([^"]+)"') {
            $presetId = $matches[1]
            curl -X DELETE "http://localhost:8000/cam/pipeline/presets/$presetId" 2>&1 | Out-Null
            Write-Host "  ✓ Cleanup: Deleted legacy preset" -ForegroundColor Gray
        }
    } else {
        Write-Host "  ✗ Unexpected response: $response" -ForegroundColor Red
    }
} catch {
    Write-Host "  ✗ Request failed: $_" -ForegroundColor Red
}

Write-Host "`n=== Pipeline Validation Tests Complete ===" -ForegroundColor Cyan
Write-Host ""
