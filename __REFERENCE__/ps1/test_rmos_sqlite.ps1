# RMOS SQLite Stores Test Suite (N8.6)
# Tests CRUD operations for patterns, joblogs, and strip families

Write-Host "=== Testing RMOS SQLite Stores (N8.6) ===" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000/api"
$testsRun = 0
$testsPassed = 0
$testsFailed = 0

function Test-Response {
    param($response, $testName)
    $global:testsRun++
    if ($response.success -eq $true) {
        Write-Host "✓ $testName" -ForegroundColor Green
        $global:testsPassed++
        return $true
    } else {
        Write-Host "✗ $testName" -ForegroundColor Red
        Write-Host "  Response: $($response | ConvertTo-Json -Depth 2)" -ForegroundColor Yellow
        $global:testsFailed++
        return $false
    }
}

# ========== Pattern Store Tests ==========

Write-Host "1. Testing Pattern Store" -ForegroundColor Yellow

# Create pattern
$patternBody = @{
    name = "Celtic Knot Test"
    ring_count = 3
    geometry = @{
        rings = @(
            @{ radius = 50; segments = 8 },
            @{ radius = 75; segments = 12 },
            @{ radius = 100; segments = 16 }
        )
    }
    metadata = @{
        created_by = "test_script"
        tags = @("celtic", "test")
    }
} | ConvertTo-Json -Depth 5

try {
    $createResponse = Invoke-RestMethod -Uri "$baseUrl/rmos/stores/patterns" -Method Post -Body $patternBody -ContentType "application/json"
    Test-Response $createResponse "Create pattern"
    $patternId = $createResponse.pattern.id
    Write-Host "  Pattern ID: $patternId" -ForegroundColor Gray
} catch {
    Write-Host "✗ Create pattern failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
    exit 1
}

# Get pattern by ID
try {
    $getResponse = Invoke-RestMethod -Uri "$baseUrl/rmos/stores/patterns/$patternId" -Method Get
    Test-Response $getResponse "Get pattern by ID"
    
    if ($getResponse.pattern.name -eq "Celtic Knot Test" -and $getResponse.pattern.ring_count -eq 3) {
        Write-Host "  ✓ Pattern data correct" -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ Get pattern failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# Update pattern
$updateBody = @{
    name = "Celtic Knot Updated"
    ring_count = 4
} | ConvertTo-Json

try {
    $updateResponse = Invoke-RestMethod -Uri "$baseUrl/rmos/stores/patterns/$patternId" -Method Put -Body $updateBody -ContentType "application/json"
    Test-Response $updateResponse "Update pattern"
    
    if ($updateResponse.pattern.name -eq "Celtic Knot Updated" -and $updateResponse.pattern.ring_count -eq 4) {
        Write-Host "  ✓ Update applied correctly" -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ Update pattern failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# List patterns
try {
    $listResponse = Invoke-RestMethod -Uri "$baseUrl/rmos/stores/patterns?limit=10" -Method Get
    Test-Response $listResponse "List patterns"
    Write-Host "  Total patterns: $($listResponse.total)" -ForegroundColor Gray
} catch {
    Write-Host "✗ List patterns failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# Search patterns by name
try {
    $searchResponse = Invoke-RestMethod -Uri "$baseUrl/rmos/stores/patterns/search/name/%celtic%" -Method Get
    Test-Response $searchResponse "Search patterns by name"
    Write-Host "  Found: $($searchResponse.count) patterns" -ForegroundColor Gray
} catch {
    Write-Host "✗ Search patterns failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# Get pattern statistics
try {
    $statsResponse = Invoke-RestMethod -Uri "$baseUrl/rmos/stores/patterns/statistics" -Method Get
    Test-Response $statsResponse "Get pattern statistics"
    Write-Host "  Total: $($statsResponse.statistics.total_count)" -ForegroundColor Gray
    Write-Host "  Avg rings: $($statsResponse.statistics.avg_ring_count)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Pattern statistics failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

Write-Host ""

# ========== JobLog Store Tests ==========

Write-Host "2. Testing JobLog Store" -ForegroundColor Yellow

# Create joblog
$joblogBody = @{
    job_type = "slice"
    pattern_id = $patternId
    status = "pending"
    parameters = @{
        blade_id = "blade-test-01"
        cut_depth_mm = 5.0
        feed_rate = 1200
    }
} | ConvertTo-Json -Depth 5

try {
    $createJobResponse = Invoke-RestMethod -Uri "$baseUrl/rmos/stores/joblogs" -Method Post -Body $joblogBody -ContentType "application/json"
    Test-Response $createJobResponse "Create joblog"
    $joblogId = $createJobResponse.joblog.id
    Write-Host "  JobLog ID: $joblogId" -ForegroundColor Gray
} catch {
    Write-Host "✗ Create joblog failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
    exit 1
}

# Get joblog by ID
try {
    $getJobResponse = Invoke-RestMethod -Uri "$baseUrl/rmos/stores/joblogs/$joblogId" -Method Get
    Test-Response $getJobResponse "Get joblog by ID"
    
    if ($getJobResponse.joblog.job_type -eq "slice" -and $getJobResponse.joblog.status -eq "pending") {
        Write-Host "  ✓ JobLog data correct" -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ Get joblog failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# Update joblog status
$updateJobBody = @{
    status = "completed"
    end_time = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    duration_seconds = 45.2
    results = @{
        cuts = 120
        length_mm = 5000
    }
} | ConvertTo-Json -Depth 3

try {
    $updateJobResponse = Invoke-RestMethod -Uri "$baseUrl/rmos/stores/joblogs/$joblogId" -Method Put -Body $updateJobBody -ContentType "application/json"
    Test-Response $updateJobResponse "Update joblog status"
    
    if ($updateJobResponse.joblog.status -eq "completed" -and $updateJobResponse.joblog.duration_seconds -eq 45.2) {
        Write-Host "  ✓ Status update applied correctly" -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ Update joblog failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# Filter joblogs by status
try {
    $filterResponse = Invoke-RestMethod -Uri "$baseUrl/rmos/stores/joblogs/filter/status/completed" -Method Get
    Test-Response $filterResponse "Filter joblogs by status"
    Write-Host "  Completed jobs: $($filterResponse.count)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Filter joblogs failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# Get joblogs for pattern
try {
    $patternJobsResponse = Invoke-RestMethod -Uri "$baseUrl/rmos/stores/joblogs/filter/pattern/$patternId" -Method Get
    Test-Response $patternJobsResponse "Get joblogs for pattern"
    Write-Host "  Jobs for pattern: $($patternJobsResponse.count)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Get pattern jobs failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# Get joblog statistics
try {
    $jobStatsResponse = Invoke-RestMethod -Uri "$baseUrl/rmos/stores/joblogs/statistics" -Method Get
    Test-Response $jobStatsResponse "Get joblog statistics"
    Write-Host "  Total jobs: $($jobStatsResponse.statistics.total_count)" -ForegroundColor Gray
    Write-Host "  Success rate: $($jobStatsResponse.statistics.success_rate)%" -ForegroundColor Gray
} catch {
    Write-Host "✗ JobLog statistics failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

Write-Host ""

# ========== Strip Family Store Tests ==========

Write-Host "3. Testing Strip Family Store" -ForegroundColor Yellow

# Create strip family
$familyBody = @{
    name = "Maple Contrast Test"
    strip_width_mm = 3.0
    strip_thickness_mm = 1.5
    material_type = "maple"
    strips = @(
        @{ id = "strip-1"; color = "light"; position = 0 },
        @{ id = "strip-2"; color = "dark"; position = 1 },
        @{ id = "strip-3"; color = "light"; position = 2 }
    )
    metadata = @{
        supplier = "test_supplier"
        batch = "2025-11"
    }
} | ConvertTo-Json -Depth 5

try {
    $createFamilyResponse = Invoke-RestMethod -Uri "$baseUrl/rmos/stores/strip-families" -Method Post -Body $familyBody -ContentType "application/json"
    Test-Response $createFamilyResponse "Create strip family"
    $familyId = $createFamilyResponse.strip_family.id
    Write-Host "  Strip Family ID: $familyId" -ForegroundColor Gray
} catch {
    Write-Host "✗ Create strip family failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
    exit 1
}

# Get strip family by ID
try {
    $getFamilyResponse = Invoke-RestMethod -Uri "$baseUrl/rmos/stores/strip-families/$familyId" -Method Get
    Test-Response $getFamilyResponse "Get strip family by ID"
    
    if ($getFamilyResponse.strip_family.name -eq "Maple Contrast Test" -and $getFamilyResponse.strip_family.material_type -eq "maple") {
        Write-Host "  ✓ Strip family data correct" -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ Get strip family failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# Update strip family
$updateFamilyBody = @{
    name = "Maple Contrast Updated"
    strip_width_mm = 3.2
} | ConvertTo-Json

try {
    $updateFamilyResponse = Invoke-RestMethod -Uri "$baseUrl/rmos/stores/strip-families/$familyId" -Method Put -Body $updateFamilyBody -ContentType "application/json"
    Test-Response $updateFamilyResponse "Update strip family"
    
    if ($updateFamilyResponse.strip_family.name -eq "Maple Contrast Updated" -and $updateFamilyResponse.strip_family.strip_width_mm -eq 3.2) {
        Write-Host "  ✓ Update applied correctly" -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ Update strip family failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# Filter by material type
try {
    $materialResponse = Invoke-RestMethod -Uri "$baseUrl/rmos/stores/strip-families/filter/material/maple" -Method Get
    Test-Response $materialResponse "Filter by material type"
    Write-Host "  Maple families: $($materialResponse.count)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Filter by material failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# Search by name
try {
    $searchFamilyResponse = Invoke-RestMethod -Uri "$baseUrl/rmos/stores/strip-families/search/name/%maple%" -Method Get
    Test-Response $searchFamilyResponse "Search strip families by name"
    Write-Host "  Found: $($searchFamilyResponse.count) families" -ForegroundColor Gray
} catch {
    Write-Host "✗ Search strip families failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# Get strip family statistics
try {
    $familyStatsResponse = Invoke-RestMethod -Uri "$baseUrl/rmos/stores/strip-families/statistics" -Method Get
    Test-Response $familyStatsResponse "Get strip family statistics"
    Write-Host "  Total families: $($familyStatsResponse.statistics.total_count)" -ForegroundColor Gray
    Write-Host "  Unique materials: $($familyStatsResponse.statistics.unique_materials)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Strip family statistics failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

Write-Host ""

# ========== Cleanup Tests ==========

Write-Host "4. Testing Cleanup Operations" -ForegroundColor Yellow

# Delete joblog (must delete before pattern due to foreign key)
try {
    $deleteJobResponse = Invoke-RestMethod -Uri "$baseUrl/rmos/stores/joblogs/$joblogId" -Method Delete
    Test-Response $deleteJobResponse "Delete joblog"
} catch {
    Write-Host "✗ Delete joblog failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# Delete pattern
try {
    $deleteResponse = Invoke-RestMethod -Uri "$baseUrl/rmos/stores/patterns/$patternId" -Method Delete
    Test-Response $deleteResponse "Delete pattern"
} catch {
    Write-Host "✗ Delete pattern failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# Delete strip family
try {
    $deleteFamilyResponse = Invoke-RestMethod -Uri "$baseUrl/rmos/stores/strip-families/$familyId" -Method Delete
    Test-Response $deleteFamilyResponse "Delete strip family"
} catch {
    Write-Host "✗ Delete strip family failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

Write-Host ""
Write-Host "=== Test Summary ===" -ForegroundColor Cyan
Write-Host "Tests run: $testsRun" -ForegroundColor White
Write-Host "Passed: $testsPassed" -ForegroundColor Green
Write-Host "Failed: $testsFailed" -ForegroundColor $(if ($testsFailed -gt 0) { "Red" } else { "Green" })

if ($testsFailed -gt 0) {
    Write-Host ""
    Write-Host "❌ RMOS SQLite Tests FAILED" -ForegroundColor Red
    exit 1
} else {
    Write-Host ""
    Write-Host "✅ All RMOS SQLite Tests PASSED" -ForegroundColor Green
    exit 0
}
