# Test N11.1 — Rosette Pattern Scaffolding
# Validates: SQL migration, PatternStore extensions, JobLog extensions, API endpoints

param(
    [string]$BaseUrl = "http://localhost:8000"
)

$ErrorActionPreference = "Continue"
$TestsPassed = 0
$TestsFailed = 0

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  N11.1 Rosette Scaffolding Smoke Test  " -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Helper: Test result logging
function Test-Result {
    param([bool]$Condition, [string]$TestName)
    if ($Condition) {
        Write-Host "✓ $TestName" -ForegroundColor Green
        $script:TestsPassed++
    } else {
        Write-Host "✗ $TestName" -ForegroundColor Red
        $script:TestsFailed++
    }
}

# ========== Test 1: Create Rosette Pattern ==========
Write-Host "[Test 1] Create Rosette Pattern via API" -ForegroundColor Yellow

$rosettePayload = @{
    pattern_id = "rosette_test_001"
    name = "Test Spanish 5-Ring Rosette"
    rosette_geometry = @{
        rings = @(
            @{
                ring_id = 1
                radius_mm = 40.0
                width_mm = 3.0
                tile_length_mm = 2.5
                twist_angle_deg = 0.0
                slice_angle_deg = 0.0
                column = @{
                    strips = @(
                        @{
                            width_mm = 1.0
                            color = "maple"
                            material_id = "wood_maple_001"
                        }
                    )
                }
            },
            @{
                ring_id = 2
                radius_mm = 43.0
                width_mm = 2.0
                tile_length_mm = 2.0
                twist_angle_deg = 5.0
                slice_angle_deg = 0.0
                column = @{
                    strips = @(
                        @{
                            width_mm = 1.0
                            color = "walnut"
                            material_id = "wood_walnut_001"
                        }
                    )
                }
            }
        )
        segmentation = @{
            tile_count_total = 94
        }
    }
    metadata = @{
        complexity = "medium"
        fragility_score = 0.42
        rosette_type = "traditional_spanish"
    }
} | ConvertTo-Json -Depth 10

try {
    $createResponse = Invoke-RestMethod `
        -Uri "$BaseUrl/api/rmos/patterns/rosette" `
        -Method POST `
        -ContentType "application/json" `
        -Body $rosettePayload
    
    Test-Result ($createResponse.pattern_id -eq "rosette_test_001") "Pattern created with correct ID"
    Test-Result ($createResponse.pattern_type -eq "rosette") "Pattern type set to 'rosette'"
    Test-Result ($createResponse.ring_count -eq 2) "Ring count correct (2 rings)"
    Test-Result ($null -ne $createResponse.rosette_geometry) "rosette_geometry field present"
    Test-Result ($createResponse.rosette_geometry.rings.Count -eq 2) "Geometry rings array preserved"
    
    Write-Host "  Pattern ID: $($createResponse.pattern_id)" -ForegroundColor Gray
    Write-Host "  Pattern Type: $($createResponse.pattern_type)" -ForegroundColor Gray
    Write-Host "  Ring Count: $($createResponse.ring_count)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Failed to create rosette pattern: $_" -ForegroundColor Red
    $script:TestsFailed++
}

# ========== Test 2: List Rosette Patterns ==========
Write-Host "`n[Test 2] List Rosette Patterns" -ForegroundColor Yellow

try {
    $listResponse = Invoke-RestMethod `
        -Uri "$BaseUrl/api/rmos/patterns/rosette" `
        -Method GET
    
    Test-Result ($listResponse -is [Array]) "List endpoint returns array"
    Test-Result ($listResponse.Count -ge 1) "At least one rosette pattern exists"
    
    $testPattern = $listResponse | Where-Object { $_.pattern_id -eq "rosette_test_001" }
    Test-Result ($null -ne $testPattern) "Test pattern found in list"
    Test-Result ($testPattern.pattern_type -eq "rosette") "List filters by pattern_type='rosette'"
    
    Write-Host "  Total rosette patterns: $($listResponse.Count)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Failed to list rosette patterns: $_" -ForegroundColor Red
    $script:TestsFailed++
}

# ========== Test 3: Get Specific Rosette Pattern ==========
Write-Host "`n[Test 3] Get Rosette Pattern by ID" -ForegroundColor Yellow

try {
    $getResponse = Invoke-RestMethod `
        -Uri "$BaseUrl/api/rmos/patterns/rosette/rosette_test_001" `
        -Method GET
    
    Test-Result ($getResponse.pattern_id -eq "rosette_test_001") "GET returns correct pattern"
    Test-Result ($getResponse.pattern_type -eq "rosette") "Pattern type verified"
    Test-Result ($null -ne $getResponse.rosette_geometry) "Geometry field present"
    Test-Result ($getResponse.metadata.complexity -eq "medium") "Metadata preserved"
    
    Write-Host "  Pattern Name: $($getResponse.name)" -ForegroundColor Gray
    Write-Host "  Complexity: $($getResponse.metadata.complexity)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Failed to get rosette pattern: $_" -ForegroundColor Red
    $script:TestsFailed++
}

# ========== Test 4: Get Rosette Geometry Only ==========
Write-Host "`n[Test 4] Get Rosette Geometry (geometry-only endpoint)" -ForegroundColor Yellow

try {
    $geomResponse = Invoke-RestMethod `
        -Uri "$BaseUrl/api/rmos/patterns/rosette/rosette_test_001/geometry" `
        -Method GET
    
    Test-Result ($null -ne $geomResponse.rings) "Geometry has rings array"
    Test-Result ($geomResponse.rings.Count -eq 2) "Correct number of rings"
    Test-Result ($geomResponse.rings[0].radius_mm -eq 40.0) "Ring 1 radius correct"
    Test-Result ($geomResponse.rings[1].radius_mm -eq 43.0) "Ring 2 radius correct"
    Test-Result ($null -ne $geomResponse.segmentation) "Segmentation field present"
    
    Write-Host "  Ring 1 Radius: $($geomResponse.rings[0].radius_mm) mm" -ForegroundColor Gray
    Write-Host "  Ring 2 Radius: $($geomResponse.rings[1].radius_mm) mm" -ForegroundColor Gray
} catch {
    Write-Host "✗ Failed to get rosette geometry: $_" -ForegroundColor Red
    $script:TestsFailed++
}

# ========== Test 5: Update Rosette Geometry ==========
Write-Host "`n[Test 5] Update Rosette Geometry (PATCH)" -ForegroundColor Yellow

$updatedGeometry = @{
    rosette_geometry = @{
        rings = @(
            @{
                ring_id = 1
                radius_mm = 45.0  # Changed from 40.0
                width_mm = 3.5    # Changed from 3.0
                tile_length_mm = 2.5
                twist_angle_deg = 0.0
                slice_angle_deg = 0.0
                column = @{
                    strips = @(
                        @{
                            width_mm = 1.5  # Changed
                            color = "maple"
                            material_id = "wood_maple_001"
                        }
                    )
                }
            }
        )
        segmentation = @{
            tile_count_total = 88  # Changed from 94
        }
    }
} | ConvertTo-Json -Depth 10

try {
    $patchResponse = Invoke-RestMethod `
        -Uri "$BaseUrl/api/rmos/patterns/rosette/rosette_test_001/geometry" `
        -Method PATCH `
        -ContentType "application/json" `
        -Body $updatedGeometry
    
    Test-Result ($patchResponse.rosette_geometry.rings[0].radius_mm -eq 45.0) "Geometry updated (radius)"
    Test-Result ($patchResponse.rosette_geometry.rings[0].width_mm -eq 3.5) "Geometry updated (width)"
    Test-Result ($patchResponse.rosette_geometry.segmentation.tile_count_total -eq 88) "Segmentation updated"
    
    Write-Host "  New Ring 1 Radius: $($patchResponse.rosette_geometry.rings[0].radius_mm) mm" -ForegroundColor Gray
    Write-Host "  New Tile Count: $($patchResponse.rosette_geometry.segmentation.tile_count_total)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Failed to update rosette geometry: $_" -ForegroundColor Red
    $script:TestsFailed++
}

# ========== Test 6: Validate Pattern Type Filter ==========
Write-Host "`n[Test 6] Validate Pattern Type Filtering" -ForegroundColor Yellow

# Create a generic (non-rosette) pattern for comparison
$genericPayload = @{
    pattern_id = "generic_test_001"
    name = "Test Generic Pattern"
    metadata = @{
        type = "generic"
    }
} | ConvertTo-Json -Depth 5

try {
    # Create generic pattern using base patterns endpoint (not rosette endpoint)
    $genericCreate = Invoke-RestMethod `
        -Uri "$BaseUrl/api/rmos/patterns" `
        -Method POST `
        -ContentType "application/json" `
        -Body $genericPayload
    
    # List rosette patterns - should NOT include generic_test_001
    $rosetteList = Invoke-RestMethod `
        -Uri "$BaseUrl/api/rmos/patterns/rosette" `
        -Method GET
    
    $genericInRosetteList = $rosetteList | Where-Object { $_.pattern_id -eq "generic_test_001" }
    Test-Result ($null -eq $genericInRosetteList) "Generic pattern NOT in rosette list"
    
    $rosetteInList = $rosetteList | Where-Object { $_.pattern_id -eq "rosette_test_001" }
    Test-Result ($null -ne $rosetteInList) "Rosette pattern IS in rosette list"
    
    Write-Host "  Generic patterns excluded from rosette list: ✓" -ForegroundColor Gray
} catch {
    Write-Host "✗ Failed pattern type filtering test: $_" -ForegroundColor Red
    $script:TestsFailed++
}

# ========== Test 7: Error Handling - Duplicate Pattern ID ==========
Write-Host "`n[Test 7] Error Handling - Duplicate Pattern ID (HTTP 409)" -ForegroundColor Yellow

try {
    $duplicateResponse = Invoke-RestMethod `
        -Uri "$BaseUrl/api/rmos/patterns/rosette" `
        -Method POST `
        -ContentType "application/json" `
        -Body $rosettePayload `
        -ErrorAction Stop
    
    Write-Host "✗ Should have returned HTTP 409 for duplicate ID" -ForegroundColor Red
    $script:TestsFailed++
} catch {
    if ($_.Exception.Response.StatusCode -eq 409) {
        Write-Host "✓ HTTP 409 returned for duplicate pattern ID" -ForegroundColor Green
        $script:TestsPassed++
    } else {
        Write-Host "✗ Unexpected error code: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
        $script:TestsFailed++
    }
}

# ========== Test 8: Error Handling - Invalid Geometry Structure ==========
Write-Host "`n[Test 8] Error Handling - Invalid Geometry Structure (HTTP 400)" -ForegroundColor Yellow

$invalidGeometry = @{
    pattern_id = "rosette_invalid_001"
    name = "Invalid Rosette"
    rosette_geometry = @{
        # Missing 'rings' array
        segmentation = @{ tile_count_total = 50 }
    }
} | ConvertTo-Json -Depth 5

try {
    $invalidResponse = Invoke-RestMethod `
        -Uri "$BaseUrl/api/rmos/patterns/rosette" `
        -Method POST `
        -ContentType "application/json" `
        -Body $invalidGeometry `
        -ErrorAction Stop
    
    Write-Host "✗ Should have returned HTTP 400 for missing 'rings' array" -ForegroundColor Red
    $script:TestsFailed++
} catch {
    if ($_.Exception.Response.StatusCode -eq 400) {
        Write-Host "✓ HTTP 400 returned for invalid geometry structure" -ForegroundColor Green
        $script:TestsPassed++
    } else {
        Write-Host "✗ Unexpected error code: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
        $script:TestsFailed++
    }
}

# ========== Test 9: Error Handling - Pattern Not Found ==========
Write-Host "`n[Test 9] Error Handling - Pattern Not Found (HTTP 404)" -ForegroundColor Yellow

try {
    $notFoundResponse = Invoke-RestMethod `
        -Uri "$BaseUrl/api/rmos/patterns/rosette/nonexistent_pattern_999" `
        -Method GET `
        -ErrorAction Stop
    
    Write-Host "✗ Should have returned HTTP 404 for nonexistent pattern" -ForegroundColor Red
    $script:TestsFailed++
} catch {
    if ($_.Exception.Response.StatusCode -eq 404) {
        Write-Host "✓ HTTP 404 returned for nonexistent pattern" -ForegroundColor Green
        $script:TestsPassed++
    } else {
        Write-Host "✗ Unexpected error code: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
        $script:TestsFailed++
    }
}

# ========== Test 10: JobLog Integration (Rosette Job Creation) ==========
Write-Host "`n[Test 10] JobLog Integration - Rosette Job Created" -ForegroundColor Yellow

try {
    # Query JobLog for rosette pattern generation jobs
    $jobLogResponse = Invoke-RestMethod `
        -Uri "$BaseUrl/api/rmos/joblogs?pattern_id=rosette_test_001" `
        -Method GET
    
    if ($jobLogResponse.Count -gt 0) {
        $rosetteJob = $jobLogResponse | Where-Object { 
            $_.job_type -eq "rosette_pattern_generation" 
        }
        
        Test-Result ($null -ne $rosetteJob) "Rosette job created in JobLog"
        Test-Result ($rosetteJob.pattern_id -eq "rosette_test_001") "Job linked to correct pattern"
        Test-Result ($rosetteJob.status -eq "completed") "Job status is 'completed'"
        
        Write-Host "  Job ID: $($rosetteJob.job_id)" -ForegroundColor Gray
        Write-Host "  Job Type: $($rosetteJob.job_type)" -ForegroundColor Gray
    } else {
        Write-Host "✗ No jobs found for rosette_test_001 (JobLog integration issue)" -ForegroundColor Red
        $script:TestsFailed++
    }
} catch {
    Write-Host "✗ Failed to query JobLog: $_" -ForegroundColor Red
    $script:TestsFailed++
}

# ========== Summary ==========
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Test Results Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Passed: $TestsPassed" -ForegroundColor Green
Write-Host "  Failed: $TestsFailed" -ForegroundColor Red
Write-Host "  Total:  $($TestsPassed + $TestsFailed)`n" -ForegroundColor White

if ($TestsFailed -eq 0) {
    Write-Host "✓ All N11.1 scaffolding tests passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "✗ Some tests failed. Check API server logs." -ForegroundColor Red
    exit 1
}
