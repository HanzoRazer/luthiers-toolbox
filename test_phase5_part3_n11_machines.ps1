# ============================================================================
# TEST SCRIPT: Phase 5 Part 3 - N.11 Machine Profiles CRUD Validation
# ============================================================================
# Purpose: Validate existing Machine Profiles API implementation
# Expected: All tests pass (N.11 already complete, needs validation)
# Endpoints: GET/POST/DELETE /api/machine/profiles, POST /profiles/clone
# ============================================================================

$baseUrl = "http://localhost:8000"
$api = "$baseUrl/machine"

$totalTests = 0
$passedTests = 0

function Test-Assert {
    param($condition, $testName)
    $script:totalTests++
    if ($condition) {
        Write-Host "  ✓ $testName" -ForegroundColor Green
        $script:passedTests++
    } else {
        Write-Host "  ✗ $testName" -ForegroundColor Red
    }
}

Write-Host "`n╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     PHASE 5 PART 3 - N.11 MACHINE PROFILES VALIDATION        ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# ============================================================================
# GROUP 1: API Availability & List Profiles (5 tests)
# ============================================================================
Write-Host "`n=== GROUP 1: API Availability & List Profiles ===" -ForegroundColor Yellow

try {
    $profiles = Invoke-RestMethod -Uri "$api/profiles" -Method GET
    Test-Assert ($profiles -is [array]) "GET /profiles returns array"
    Test-Assert ($profiles.Count -ge 1) "At least 1 default profile exists"
    
    # Check first profile structure (no "default" id, but GRBL_3018_Default)
    $firstProfile = $profiles[0]
    Test-Assert ($null -ne $firstProfile) "First profile exists"
    Test-Assert ($firstProfile.controller -ne $null) "First profile has controller field"
    Test-Assert ($firstProfile.limits -ne $null) "First profile has limits field"
    
    Write-Host "  📊 Found $($profiles.Count) machine profiles" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ API request failed: $_" -ForegroundColor Red
    Test-Assert $false "GET /profiles API available"
}

# ============================================================================
# GROUP 2: Get Specific Profile (4 tests)
# ============================================================================
Write-Host "`n=== GROUP 2: Get Specific Profile ===" -ForegroundColor Yellow

try {
    $profile = Invoke-RestMethod -Uri "$api/profiles/GRBL_3018_Default" -Method GET
    Test-Assert ($profile.id -eq "GRBL_3018_Default") "Profile ID matches 'GRBL_3018_Default'"
    Test-Assert ($profile.title -ne $null) "Profile has title"
    Test-Assert ($profile.axes -ne $null) "Profile has axes config"
    Test-Assert ($profile.limits.accel -gt 0) "Profile has accel limit"
    
    Write-Host "  📊 Profile: $($profile.title) | Controller: $($profile.controller)" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ GET profile by ID failed: $_" -ForegroundColor Red
    Test-Assert $false "GET /profiles/{id} works"
}

# ============================================================================
# GROUP 3: Get Non-Existent Profile (1 test)
# ============================================================================
Write-Host "`n=== GROUP 3: Error Handling - Non-Existent Profile ===" -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "$api/profiles/this_machine_does_not_exist_xyz" -Method GET -ErrorAction Stop
    Test-Assert $false "Should return 404 for non-existent profile"
} catch {
    $errorCode = $_.Exception.Response.StatusCode.value__
    Test-Assert ($errorCode -eq 404) "Returns 404 for non-existent profile"
}

# ============================================================================
# GROUP 4: Create New Profile (6 tests)
# ============================================================================
Write-Host "`n=== GROUP 4: Create New Profile ===" -ForegroundColor Yellow

$testProfile = @{
    id = "test_grbl_router"
    title = "Test GRBL Router"
    controller = "GRBL"
    axes = @{
        travel_mm = @(300, 400, 100)
    }
    limits = @{
        accel = 800
        jerk = 2000
        feed_xy = 1200
        rapid = 3000
        corner_tol_mm = 0.2
    }
    spindle = @{
        max_rpm = 24000
        min_rpm = 8000
    }
    post_id_default = "GRBL"
} | ConvertTo-Json -Depth 5

try {
    $createResult = Invoke-RestMethod -Uri "$api/profiles" -Method POST `
        -ContentType "application/json" -Body $testProfile
    Test-Assert ($createResult.status -eq "created") "Create new profile status=created"
    Test-Assert ($createResult.id -eq "test_grbl_router") "Created profile ID matches"
    
    # Verify profile was actually created
    $verifyProfile = Invoke-RestMethod -Uri "$api/profiles/test_grbl_router" -Method GET
    Test-Assert ($verifyProfile.id -eq "test_grbl_router") "Created profile can be retrieved"
    Test-Assert ($verifyProfile.title -eq "Test GRBL Router") "Created profile has correct title"
    Test-Assert ($verifyProfile.controller -eq "GRBL") "Created profile has correct controller"
    Test-Assert ($verifyProfile.limits.accel -eq 800) "Created profile has correct accel"
    
    Write-Host "  📊 Created: $($verifyProfile.title) | Accel: $($verifyProfile.limits.accel_mm_s2) mm/s²" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Create profile failed: $_" -ForegroundColor Red
    Test-Assert $false "POST /profiles creates new profile"
}

# ============================================================================
# GROUP 5: Update Existing Profile (5 tests)
# ============================================================================
Write-Host "`n=== GROUP 5: Update Existing Profile ===" -ForegroundColor Yellow

$updateProfile = @{
    id = "test_grbl_router"
    title = "Test GRBL Router (Updated)"
    controller = "GRBL"
    axes = @{
        travel_mm = @(350, 450, 120)  # Changed from (300, 400, 100)
    }
    limits = @{
        accel = 1000  # Changed from 800
        jerk = 2500   # Changed from 2000
        feed_xy = 1500  # Changed from 1200
        rapid = 3500  # Changed from 3000
        corner_tol_mm = 0.25  # Changed from 0.2
    }
    spindle = @{
        max_rpm = 30000  # Changed from 24000
        min_rpm = 10000  # Changed from 8000
    }
    post_id_default = "GRBL"
} | ConvertTo-Json -Depth 5

try {
    $updateResult = Invoke-RestMethod -Uri "$api/profiles" -Method POST `
        -ContentType "application/json" -Body $updateProfile
    Test-Assert ($updateResult.status -eq "updated") "Update existing profile status=updated"
    Test-Assert ($updateResult.id -eq "test_grbl_router") "Updated profile ID matches"
    
    # Verify updates were applied
    $verifyUpdate = Invoke-RestMethod -Uri "$api/profiles/test_grbl_router" -Method GET
    Test-Assert ($verifyUpdate.title -eq "Test GRBL Router (Updated)") "Title was updated"
    Test-Assert ($verifyUpdate.limits.accel -eq 1000) "Accel was updated"
    Test-Assert ($verifyUpdate.axes.travel_mm[0] -eq 350) "X travel was updated"
    
    Write-Host "  📊 Updated: Accel $($verifyUpdate.limits.accel) mm/s² | Travel X: $($verifyUpdate.axes.travel_mm[0]) mm" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Update profile failed: $_" -ForegroundColor Red
    Test-Assert $false "POST /profiles updates existing profile"
}

# ============================================================================
# GROUP 6: Clone Profile (7 tests)
# ============================================================================
Write-Host "`n=== GROUP 6: Clone Profile ===" -ForegroundColor Yellow

try {
    # Clone test_grbl_router to test_grbl_router_clone
    # Note: API uses query params, not JSON body
    $cloneResult = Invoke-RestMethod -Uri "$api/profiles/clone/test_grbl_router?new_id=test_grbl_router_clone&new_title=Cloned%20GRBL%20Router" -Method POST
    Test-Assert ($cloneResult.status -eq "cloned") "Clone profile status=cloned"
    Test-Assert ($cloneResult.id -eq "test_grbl_router_clone") "Cloned profile ID matches"
    
    # Verify clone exists with new ID and title
    $clonedProfile = Invoke-RestMethod -Uri "$api/profiles/test_grbl_router_clone" -Method GET
    Test-Assert ($clonedProfile.id -eq "test_grbl_router_clone") "Cloned profile has new ID"
    Test-Assert ($clonedProfile.title -eq "Cloned GRBL Router") "Cloned profile has new title"
    
    # Verify clone inherited all other properties
    Test-Assert ($clonedProfile.controller -eq "GRBL") "Cloned profile inherited controller"
    Test-Assert ($clonedProfile.limits.accel -eq 1000) "Cloned profile inherited accel"
    Test-Assert ($clonedProfile.axes.travel_mm[0] -eq 350) "Cloned profile inherited X travel"
    
    Write-Host "  📊 Cloned: $($clonedProfile.title) from test_grbl_router" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Clone profile failed: $_" -ForegroundColor Red
    Test-Assert $false "POST /profiles/clone works"
}

# ============================================================================
# GROUP 7: Clone Error Handling (2 tests)
# ============================================================================
Write-Host "`n=== GROUP 7: Clone Error Handling ===" -ForegroundColor Yellow

# Test cloning non-existent source
try {
    # Use query params
    $response = Invoke-RestMethod -Uri "$api/profiles/clone/machine_that_does_not_exist?new_id=test_clone_from_nowhere&new_title=Should%20Fail" -Method POST -ErrorAction Stop
    Test-Assert $false "Should return 404 when cloning non-existent source"
} catch {
    $errorCode = $_.Exception.Response.StatusCode.value__
    Test-Assert ($errorCode -eq 404) "Returns 404 when cloning non-existent source"
}

# Test cloning with duplicate new_id
try {
    # Use query params
    $response = Invoke-RestMethod -Uri "$api/profiles/clone/test_grbl_router?new_id=test_grbl_router&new_title=Should%20Fail" -Method POST -ErrorAction Stop
    Test-Assert $false "Should return 400 when new_id already exists"
} catch {
    $errorCode = $_.Exception.Response.StatusCode.value__
    Test-Assert ($errorCode -eq 400) "Returns 400 when new_id already exists"
}

# ============================================================================
# GROUP 8: List Profiles After Operations (2 tests)
# ============================================================================
Write-Host "`n=== GROUP 8: List Profiles After CRUD ===" -ForegroundColor Yellow

try {
    $allProfiles = Invoke-RestMethod -Uri "$api/profiles" -Method GET
    $testProfiles = $allProfiles | Where-Object { $_.id -like "test_*" }
    
    Test-Assert ($testProfiles.Count -ge 2) "At least 2 test profiles exist after CRUD"
    Test-Assert ($allProfiles.Count -ge 3) "Total profiles count increased"
    
    Write-Host "  📊 Total profiles: $($allProfiles.Count) | Test profiles: $($testProfiles.Count)" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ List profiles failed: $_" -ForegroundColor Red
    Test-Assert $false "GET /profiles lists all profiles"
}

# ============================================================================
# GROUP 9: Delete Profile (4 tests)
# ============================================================================
Write-Host "`n=== GROUP 9: Delete Profile ===" -ForegroundColor Yellow

try {
    # Delete test_grbl_router_clone first
    $deleteResult1 = Invoke-RestMethod -Uri "$api/profiles/test_grbl_router_clone" -Method DELETE
    Test-Assert ($deleteResult1.status -eq "deleted") "Delete clone profile status=deleted"
    Test-Assert ($deleteResult1.id -eq "test_grbl_router_clone") "Deleted profile ID matches"
    
    # Delete test_grbl_router
    $deleteResult2 = Invoke-RestMethod -Uri "$api/profiles/test_grbl_router" -Method DELETE
    Test-Assert ($deleteResult2.status -eq "deleted") "Delete original profile status=deleted"
    
    # Verify both profiles are gone
    try {
        $verify = Invoke-RestMethod -Uri "$api/profiles/test_grbl_router" -Method GET -ErrorAction Stop
        Test-Assert $false "Deleted profile should return 404"
    } catch {
        $errorCode = $_.Exception.Response.StatusCode.value__
        Test-Assert ($errorCode -eq 404) "Deleted profile returns 404"
    }
    
    Write-Host "  📊 Cleaned up 2 test profiles" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Delete profile failed: $_" -ForegroundColor Red
    Test-Assert $false "DELETE /profiles/{id} works"
}

# ============================================================================
# GROUP 10: Delete Error Handling (1 test)
# ============================================================================
Write-Host "`n=== GROUP 10: Delete Error Handling ===" -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "$api/profiles/profile_that_never_existed" -Method DELETE -ErrorAction Stop
    Test-Assert $false "Should return 404 when deleting non-existent profile"
} catch {
    $errorCode = $_.Exception.Response.StatusCode.value__
    Test-Assert ($errorCode -eq 404) "Returns 404 when deleting non-existent profile"
}

# ============================================================================
# GROUP 11: Profile Structure Validation (8 tests)
# ============================================================================
Write-Host "`n=== GROUP 11: Profile Structure Validation ===" -ForegroundColor Yellow

try {
    $profile = Invoke-RestMethod -Uri "$api/profiles/GRBL_3018_Default" -Method GET
    
    # Required fields
    Test-Assert ($profile.id -ne $null) "Profile has 'id' field"
    Test-Assert ($profile.title -ne $null) "Profile has 'title' field"
    Test-Assert ($profile.controller -ne $null) "Profile has 'controller' field"
    Test-Assert ($profile.axes -ne $null) "Profile has 'axes' field"
    Test-Assert ($profile.limits -ne $null) "Profile has 'limits' field"
    
    # Axes structure (array format)
    Test-Assert ($profile.axes.travel_mm -ne $null) "Profile has axes.travel_mm"
    
    # Limits structure
    Test-Assert ($profile.limits.accel -ne $null) "Profile has limits.accel"
    Test-Assert ($profile.limits.rapid -ne $null) "Profile has limits.rapid"
    
    Write-Host "  📊 Profile structure valid: $($profile.title)" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Profile structure validation failed: $_" -ForegroundColor Red
    Test-Assert $false "Profile structure is valid"
}

# ============================================================================
# FINAL RESULTS
# ============================================================================
Write-Host "`n╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                    TEST RESULTS SUMMARY                       ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

$passRate = [math]::Round(($passedTests / $totalTests) * 100, 1)

Write-Host "Total Tests:  $totalTests" -ForegroundColor White
Write-Host "Passed:       $passedTests" -ForegroundColor Green
Write-Host "Failed:       $($totalTests - $passedTests)" -ForegroundColor $(if ($passedTests -eq $totalTests) { "Green" } else { "Red" })
Write-Host "Pass Rate:    $passRate%" -ForegroundColor $(if ($passedTests -eq $totalTests) { "Green" } else { "Yellow" })

if ($passedTests -eq $totalTests) {
    Write-Host "`n✅ ALL N.11 MACHINE PROFILES TESTS PASSED!" -ForegroundColor Green -BackgroundColor Black
    Write-Host "   Machine Profiles CRUD is production-ready." -ForegroundColor Green
} else {
    Write-Host "`n⚠️  Some tests failed. Review output above." -ForegroundColor Yellow
}

Write-Host "`n" 
