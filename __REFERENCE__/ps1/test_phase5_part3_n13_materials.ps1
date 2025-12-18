# Phase 5 Part 3 - N.13 Material Library Validation
# Tests material database CRUD operations for Module M.3 Energy & Heat Model
#
# Test Coverage:
# - Group 1: API Availability (4 tests)
# - Group 2: Get Specific Material (4 tests)
# - Group 3: Error Handling (1 test)
# - Group 4: Create New Material (6 tests)
# - Group 5: Update Existing Material (5 tests)
# - Group 6: Material Structure Validation (8 tests)
# - Group 7: Heat Partition Validation (6 tests)
# - Group 8: SCE Value Ranges (5 tests)
# - Group 9: List After CRUD (2 tests)
# - Group 10: Multiple Materials (4 tests)
#
# Total: 45 tests across 10 groups

Param(
    [string]$BaseUrl = "http://localhost:8000"
)

$ErrorActionPreference = "Stop"
$passCount = 0
$failCount = 0
$testNumber = 0

function Test-Assert {
    param($Condition, $Message)
    $script:testNumber++
    if ($Condition) {
        Write-Host "  ✓ Test $testNumber`: $Message" -ForegroundColor Green
        $script:passCount++
    } else {
        Write-Host "  ✗ Test $testNumber`: $Message" -ForegroundColor Red
        $script:failCount++
    }
}

Write-Host "`n╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     Phase 5 Part 3 - N.13 Material Library Validation       ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

$api = "$BaseUrl/material"

# ============================================================================
# GROUP 1: API AVAILABILITY (4 tests)
# ============================================================================
Write-Host "`n=== Group 1: API Availability (4 tests) ===" -ForegroundColor Yellow

try {
    $materials = Invoke-RestMethod -Uri "$api/list" -Method GET -TimeoutSec 5
    Test-Assert ($materials -is [array]) "GET /material/list returns array"
    Test-Assert ($materials.Count -ge 4) "Material list has at least 4 defaults (found: $($materials.Count))"
    
    # Check for default materials
    $ids = $materials | ForEach-Object { $_.id }
    Test-Assert ($ids -contains "maple_hard") "Default material 'maple_hard' exists"
    Test-Assert ($ids -contains "mahogany") "Default material 'mahogany' exists"
} catch {
    Write-Host "  ✗ API availability check failed: $_" -ForegroundColor Red
    Write-Host "`nℹ️  Make sure FastAPI server is running on port 8000" -ForegroundColor Yellow
    Write-Host "   cd services/api" -ForegroundColor Gray
    Write-Host "   .\.venv\Scripts\Activate.ps1" -ForegroundColor Gray
    Write-Host "   uvicorn app.main:app --reload --port 8000`n" -ForegroundColor Gray
    exit 1
}

# ============================================================================
# GROUP 2: GET SPECIFIC MATERIAL (4 tests)
# ============================================================================
Write-Host "`n=== Group 2: Get Specific Material (4 tests) ===" -ForegroundColor Yellow

$maple = Invoke-RestMethod -Uri "$api/get/maple_hard" -Method GET
Test-Assert ($maple.id -eq "maple_hard") "Maple ID correct"
Test-Assert ($maple.title -eq "Maple (hard)") "Maple title correct"
Test-Assert ($maple.sce_j_per_mm3 -eq 0.55) "Maple SCE value correct (0.55 J/mm³)"
Test-Assert ($null -ne $maple.heat_partition) "Maple has heat_partition object"

# ============================================================================
# GROUP 3: ERROR HANDLING (1 test)
# ============================================================================
Write-Host "`n=== Group 3: Error Handling (1 test) ===" -ForegroundColor Yellow

try {
    $notFound = Invoke-RestMethod -Uri "$api/get/nonexistent_material" -Method GET -ErrorAction Stop
    Test-Assert $false "Should return 404 for non-existent material"
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Test-Assert ($statusCode -eq 404) "GET non-existent material returns 404 (got: $statusCode)"
}

# ============================================================================
# GROUP 4: CREATE NEW MATERIAL (6 tests)
# ============================================================================
Write-Host "`n=== Group 4: Create New Material (6 tests) ===" -ForegroundColor Yellow

$newMaterial = @{
    id = "test_walnut"
    title = "Black Walnut (Test)"
    sce_j_per_mm3 = 0.48
    heat_partition = @{
        chip = 0.7
        tool = 0.2
        work = 0.1
    }
} | ConvertTo-Json -Depth 5

$createResult = Invoke-RestMethod -Uri "$api/upsert" -Method POST -Body $newMaterial -ContentType "application/json"
Test-Assert ($createResult.status -eq "created") "Create returns 'created' status"
Test-Assert ($createResult.id -eq "test_walnut") "Create returns correct ID"

# Verify material was created
$walnut = Invoke-RestMethod -Uri "$api/get/test_walnut" -Method GET
Test-Assert ($walnut.id -eq "test_walnut") "Created material retrievable"
Test-Assert ($walnut.title -eq "Black Walnut (Test)") "Created material title correct"
Test-Assert ($walnut.sce_j_per_mm3 -eq 0.48) "Created material SCE correct"
Test-Assert ($walnut.heat_partition.chip -eq 0.7) "Created material heat partition correct"

# ============================================================================
# GROUP 5: UPDATE EXISTING MATERIAL (5 tests)
# ============================================================================
Write-Host "`n=== Group 5: Update Existing Material (5 tests) ===" -ForegroundColor Yellow

$updatedMaterial = @{
    id = "test_walnut"
    title = "Black Walnut (Updated)"
    sce_j_per_mm3 = 0.52
    heat_partition = @{
        chip = 0.68
        tool = 0.22
        work = 0.10
    }
} | ConvertTo-Json -Depth 5

$updateResult = Invoke-RestMethod -Uri "$api/upsert" -Method POST -Body $updatedMaterial -ContentType "application/json"
Test-Assert ($updateResult.status -eq "updated") "Update returns 'updated' status"
Test-Assert ($updateResult.id -eq "test_walnut") "Update returns correct ID"

# Verify material was updated
$walnutUpdated = Invoke-RestMethod -Uri "$api/get/test_walnut" -Method GET
Test-Assert ($walnutUpdated.title -eq "Black Walnut (Updated)") "Updated material title changed"
Test-Assert ($walnutUpdated.sce_j_per_mm3 -eq 0.52) "Updated material SCE changed (0.48 → 0.52)"
Test-Assert ($walnutUpdated.heat_partition.chip -eq 0.68) "Updated material heat partition changed (0.7 → 0.68)"

# ============================================================================
# GROUP 6: MATERIAL STRUCTURE VALIDATION (8 tests)
# ============================================================================
Write-Host "`n=== Group 6: Material Structure Validation (8 tests) ===" -ForegroundColor Yellow

$al6061 = Invoke-RestMethod -Uri "$api/get/al_6061" -Method GET

# Required fields
Test-Assert ($null -ne $al6061.id) "Material has 'id' field"
Test-Assert ($null -ne $al6061.title) "Material has 'title' field"
Test-Assert ($null -ne $al6061.sce_j_per_mm3) "Material has 'sce_j_per_mm3' field"
Test-Assert ($null -ne $al6061.heat_partition) "Material has 'heat_partition' field"

# Heat partition structure
Test-Assert ($null -ne $al6061.heat_partition.chip) "Heat partition has 'chip' field"
Test-Assert ($null -ne $al6061.heat_partition.tool) "Heat partition has 'tool' field"
Test-Assert ($null -ne $al6061.heat_partition.work) "Heat partition has 'work' field"

# Type validation
Test-Assert ($al6061.sce_j_per_mm3 -is [double]) "SCE is numeric type"

# ============================================================================
# GROUP 7: HEAT PARTITION VALIDATION (6 tests)
# ============================================================================
Write-Host "`n=== Group 7: Heat Partition Validation (6 tests) ===" -ForegroundColor Yellow

# Sum should equal 1.0 (or very close)
$mapleSum = $maple.heat_partition.chip + $maple.heat_partition.tool + $maple.heat_partition.work
Test-Assert ([Math]::Abs($mapleSum - 1.0) -lt 0.01) "Maple heat partition sums to 1.0 (got: $([Math]::Round($mapleSum, 3)))"

$al6061Sum = $al6061.heat_partition.chip + $al6061.heat_partition.tool + $al6061.heat_partition.work
Test-Assert ([Math]::Abs($al6061Sum - 1.0) -lt 0.01) "Al6061 heat partition sums to 1.0 (got: $([Math]::Round($al6061Sum, 3)))"

# Range validation (0.0 to 1.0)
Test-Assert ($maple.heat_partition.chip -ge 0 -and $maple.heat_partition.chip -le 1) "Maple chip partition in valid range [0,1]"
Test-Assert ($maple.heat_partition.tool -ge 0 -and $maple.heat_partition.tool -le 1) "Maple tool partition in valid range [0,1]"
Test-Assert ($maple.heat_partition.work -ge 0 -and $maple.heat_partition.work -le 1) "Maple work partition in valid range [0,1]"

# Aluminum should have higher tool fraction (harder material)
Test-Assert ($al6061.heat_partition.tool -gt $maple.heat_partition.tool) "Aluminum has higher tool heat than wood (0.25 > 0.20)"

# ============================================================================
# GROUP 8: SCE VALUE RANGES (5 tests)
# ============================================================================
Write-Host "`n=== Group 8: SCE Value Ranges (5 tests) ===" -ForegroundColor Yellow

# Typical SCE ranges (J/mm³):
# - Softwoods: 0.3-0.5
# - Hardwoods: 0.45-0.7
# - Aluminum: 0.3-0.5
# - Plastics: 0.1-0.3

Test-Assert ($maple.sce_j_per_mm3 -gt 0.4 -and $maple.sce_j_per_mm3 -lt 0.8) "Maple SCE in hardwood range (0.4-0.8 J/mm³)"

$mahogany = Invoke-RestMethod -Uri "$api/get/mahogany" -Method GET
Test-Assert ($mahogany.sce_j_per_mm3 -gt 0.4 -and $mahogany.sce_j_per_mm3 -lt 0.8) "Mahogany SCE in hardwood range"

Test-Assert ($al6061.sce_j_per_mm3 -gt 0.2 -and $al6061.sce_j_per_mm3 -lt 0.6) "Aluminum SCE in typical range (0.2-0.6 J/mm³)"

# Relative comparison: Hardwoods typically > Softwoods > Aluminum
Test-Assert ($maple.sce_j_per_mm3 -gt $al6061.sce_j_per_mm3) "Hardwood SCE > Aluminum SCE (0.55 > 0.35)"

# All materials should have positive SCE
$allMaterials = Invoke-RestMethod -Uri "$api/list" -Method GET
$allPositive = $true
foreach ($mat in $allMaterials) {
    if ($mat.sce_j_per_mm3 -le 0) {
        $allPositive = $false
        break
    }
}
Test-Assert $allPositive "All materials have positive SCE values"

# ============================================================================
# GROUP 9: LIST AFTER CRUD (2 tests)
# ============================================================================
Write-Host "`n=== Group 9: List After CRUD (2 tests) ===" -ForegroundColor Yellow

$materialsAfterCreate = Invoke-RestMethod -Uri "$api/list" -Method GET
Test-Assert ($materialsAfterCreate.Count -ge 5) "Material count increased after create (at least 5 now)"

$idsAfterCreate = $materialsAfterCreate | ForEach-Object { $_.id }
Test-Assert ($idsAfterCreate -contains "test_walnut") "New material appears in list"

# ============================================================================
# GROUP 10: MULTIPLE MATERIALS (4 tests)
# ============================================================================
Write-Host "`n=== Group 10: Multiple Materials (4 tests) ===" -ForegroundColor Yellow

# Create second test material
$testMDF = @{
    id = "test_mdf"
    title = "MDF (Test)"
    sce_j_per_mm3 = 0.42
    heat_partition = @{
        chip = 0.72
        tool = 0.18
        work = 0.10
    }
} | ConvertTo-Json -Depth 5

$mdfResult = Invoke-RestMethod -Uri "$api/upsert" -Method POST -Body $testMDF -ContentType "application/json"
Test-Assert ($mdfResult.status -eq "created") "Second test material created"

# Create third test material
$testOak = @{
    id = "test_oak"
    title = "Red Oak (Test)"
    sce_j_per_mm3 = 0.53
    heat_partition = @{
        chip = 0.70
        tool = 0.20
        work = 0.10
    }
} | ConvertTo-Json -Depth 5

$oakResult = Invoke-RestMethod -Uri "$api/upsert" -Method POST -Body $testOak -ContentType "application/json"
Test-Assert ($oakResult.status -eq "created") "Third test material created"

# Verify all test materials retrievable
$finalMaterials = Invoke-RestMethod -Uri "$api/list" -Method GET
$finalIds = $finalMaterials | ForEach-Object { $_.id }
Test-Assert ($finalIds -contains "test_walnut") "test_walnut in final list"
Test-Assert ($finalIds -contains "test_mdf") "test_mdf in final list"

# ============================================================================
# CLEANUP (Remove test materials for next run)
# ============================================================================
Write-Host "`n=== Cleanup ===" -ForegroundColor Yellow

# Note: material_router.py doesn't have DELETE endpoint
# Test materials will persist in material_db.json
# This is acceptable for validation - real cleanup would need manual edit or DELETE endpoint
Write-Host "  ℹ️  Test materials (test_walnut, test_mdf, test_oak) created" -ForegroundColor Cyan
Write-Host "  ℹ️  No DELETE endpoint - materials persist in material_db.json" -ForegroundColor Cyan
Write-Host "  ℹ️  Manual cleanup: Edit services/api/app/assets/material_db.json" -ForegroundColor Gray

# ============================================================================
# FINAL RESULTS
# ============================================================================
Write-Host "`n╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                    📊 TEST RESULTS 📊                        ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

$total = $passCount + $failCount
$percentage = if ($total -gt 0) { [math]::Round(($passCount / $total) * 100, 1) } else { 0 }

Write-Host "Tests Passed:  " -NoNewline -ForegroundColor White
Write-Host "$passCount" -ForegroundColor Green
Write-Host "Tests Failed:  " -NoNewline -ForegroundColor White
Write-Host "$failCount" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Red" })
Write-Host "Total Tests:   " -NoNewline -ForegroundColor White
Write-Host "$total" -ForegroundColor Cyan
Write-Host "Pass Rate:     " -NoNewline -ForegroundColor White
Write-Host "$percentage%" -ForegroundColor $(if ($percentage -eq 100) { "Green" } elseif ($percentage -ge 90) { "Yellow" } else { "Red" })

if ($failCount -eq 0) {
    Write-Host "`n✅ All tests passed! N.13 Material Library validation complete.`n" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n⚠️  Some tests failed. Review output above for details.`n" -ForegroundColor Yellow
    exit 1
}
