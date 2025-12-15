# ============================================
# Navigation Consolidation Test Suite
# Tests the new 5-button navigation structure
# ============================================

Write-Host "`n=== NAVIGATION CONSOLIDATION TEST SUITE ===" -ForegroundColor Cyan
Write-Host "Testing new 5-button navigation structure`n" -ForegroundColor Gray

$baseUrl = "http://localhost:5173"
$testsPassed = 0
$testsFailed = 0

# Helper function to test endpoint
function Test-Endpoint {
    param(
        [string]$Url,
        [string]$TestName,
        [string]$ExpectedContent = $null
    )
    
    Write-Host "Testing: $TestName" -ForegroundColor Yellow
    
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
        
        if ($response.StatusCode -eq 200) {
            if ($ExpectedContent) {
                if ($response.Content -match [regex]::Escape($ExpectedContent)) {
                    Write-Host "  ✓ PASS - Status 200, Content verified" -ForegroundColor Green
                    return $true
                } else {
                    Write-Host "  ✗ FAIL - Expected content not found: $ExpectedContent" -ForegroundColor Red
                    return $false
                }
            } else {
                Write-Host "  ✓ PASS - Status 200" -ForegroundColor Green
                return $true
            }
        } else {
            Write-Host "  ✗ FAIL - Status $($response.StatusCode)" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "  ✗ FAIL - Error: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# ============================================
# Test 1: Main Page Loads
# ============================================
Write-Host "`n1. Testing Main Page" -ForegroundColor Cyan
if (Test-Endpoint "$baseUrl" "Main page loads" "Luthier's Tool Box") {
    $testsPassed++
} else {
    $testsFailed++
}

# ============================================
# Test 2: Check for 5 Main Navigation Buttons
# ============================================
Write-Host "`n2. Testing 5-Button Navigation Structure" -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri $baseUrl -UseBasicParsing
    
    $buttons = @(
        "Guitar Design Tools",
        "Art Studio",
        "CAM Tools",
        "Calculators",
        "CNC Business"
    )
    
    $allFound = $true
    foreach ($button in $buttons) {
        if ($response.Content -match [regex]::Escape($button)) {
            Write-Host "  ✓ Found: $button" -ForegroundColor Green
        } else {
            Write-Host "  ✗ Missing: $button" -ForegroundColor Red
            $allFound = $false
        }
    }
    
    if ($allFound) {
        $testsPassed++
    } else {
        $testsFailed++
    }
} catch {
    Write-Host "  ✗ FAIL - Error checking navigation: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# ============================================
# Test 3: Old Individual Buttons Removed
# ============================================
Write-Host "`n3. Verifying Old Buttons Removed" -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri $baseUrl -UseBasicParsing
    
    $oldButtons = @(
        "Body Outline",
        "Neck Gen",
        "Scale Length",
        "Radius Dish",
        "Enhanced Dish",
        "Compound Radius",
        "Hardware",
        "Wiring",
        "Rosette",
        "Helical Ramp",
        "Art Studio v16",
        "DXF Clean",
        "DXF Preflight",
        "G-code"
    )
    
    $allRemoved = $true
    foreach ($button in $oldButtons) {
        # Check if button exists as standalone navigation item (not just in content)
        if ($response.Content -match "label[^>]*>.*?$button") {
            Write-Host "  ✗ Still exists: $button" -ForegroundColor Red
            $allRemoved = $false
        }
    }
    
    if ($allRemoved) {
        Write-Host "  ✓ All old navigation buttons removed" -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "  ✗ Some old buttons still present" -ForegroundColor Red
        $testsFailed++
    }
} catch {
    Write-Host "  ✗ FAIL - Error: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# ============================================
# Test 4: Art Studio Dashboard with Blueprint Lab
# ============================================
Write-Host "`n4. Testing Art Studio Dashboard" -ForegroundColor Cyan
if (Test-Endpoint "$baseUrl/art-studio-dashboard" "Art Studio Dashboard loads" "Blueprint Lab") {
    Write-Host "  ✓ Blueprint Lab found in Art Studio" -ForegroundColor Green
    $testsPassed++
} else {
    $testsFailed++
}

# ============================================
# Test 5: Blueprint Lab Route
# ============================================
Write-Host "`n5. Testing Blueprint Lab Route" -ForegroundColor Cyan
if (Test-Endpoint "$baseUrl/blueprint-lab" "Blueprint Lab page loads" "Blueprint Lab") {
    $testsPassed++
} else {
    $testsFailed++
}

# ============================================
# Test 6: Body Outline Generator API (Backend)
# ============================================
Write-Host "`n6. Testing Body Outline Generator API" -ForegroundColor Cyan
try {
    $body = @{
        guitar_type = "acoustic"
        body_length = 505
        body_width = 390
        upper_bout = 280
        lower_bout = 380
        waist = 240
        resolution = 32
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/guitar/design/parametric" `
                                  -Method Post `
                                  -ContentType "application/json" `
                                  -Body $body `
                                  -TimeoutSec 5
    
    if ($response.points -and $response.points.Count -gt 0) {
        Write-Host "  ✓ PASS - Generated $($response.points.Count) points" -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "  ✗ FAIL - No points generated" -ForegroundColor Red
        $testsFailed++
    }
} catch {
    Write-Host "  ✗ FAIL - API Error: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# ============================================
# Test 7: Body Outline DXF Export
# ============================================
Write-Host "`n7. Testing Body Outline DXF Export" -ForegroundColor Cyan
try {
    $body = @{
        guitar_type = "electric"
        body_length = 480
        body_width = 350
        upper_bout = 260
        lower_bout = 340
        waist = 220
        resolution = 32
        format = "dxf"
    } | ConvertTo-Json

    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/guitar/design/parametric/export" `
                                   -Method Post `
                                   -ContentType "application/json" `
                                   -Body $body `
                                   -TimeoutSec 10

    if ($response.StatusCode -eq 200 -and $response.Headers.'Content-Type' -match 'dxf') {
        $dxfContent = $response.Content
        if ($dxfContent -match 'LWPOLYLINE' -and $dxfContent -match 'AcDbEntity') {
            Write-Host "  ✓ PASS - Valid DXF R12 format" -ForegroundColor Green
            Write-Host "  ✓ Size: $($dxfContent.Length) bytes" -ForegroundColor Green
            $testsPassed++
        } else {
            Write-Host "  ✗ FAIL - Invalid DXF structure" -ForegroundColor Red
            $testsFailed++
        }
    } else {
        Write-Host "  ✗ FAIL - Wrong content type or status" -ForegroundColor Red
        $testsFailed++
    }
} catch {
    Write-Host "  ✗ FAIL - Export Error: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# ============================================
# Test 8: Body Outline SVG Export
# ============================================
Write-Host "`n8. Testing Body Outline SVG Export" -ForegroundColor Cyan
try {
    $body = @{
        guitar_type = "classical"
        body_length = 490
        body_width = 360
        upper_bout = 270
        lower_bout = 360
        waist = 250
        resolution = 32
        format = "svg"
    } | ConvertTo-Json

    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/guitar/design/parametric/export" `
                                   -Method Post `
                                   -ContentType "application/json" `
                                   -Body $body `
                                   -TimeoutSec 10

    if ($response.StatusCode -eq 200) {
        $svgContent = $response.Content
        if ($svgContent -match '<svg' -and $svgContent -match '<path' -and $svgContent -match 'viewBox') {
            Write-Host "  ✓ PASS - Valid SVG format" -ForegroundColor Green
            Write-Host "  ✓ Size: $($svgContent.Length) bytes" -ForegroundColor Green
            $testsPassed++
        } else {
            Write-Host "  ✗ FAIL - Invalid SVG structure" -ForegroundColor Red
            $testsFailed++
        }
    } else {
        Write-Host "  ✗ FAIL - Wrong status code" -ForegroundColor Red
        $testsFailed++
    }
} catch {
    Write-Host "  ✗ FAIL - Export Error: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# ============================================
# Test 9: CAM Dashboard Route
# ============================================
Write-Host "`n9. Testing CAM Tools Dashboard" -ForegroundColor Cyan
if (Test-Endpoint "$baseUrl/cam-dashboard" "CAM Dashboard loads") {
    $testsPassed++
} else {
    $testsFailed++
}

# ============================================
# Test 10: Welcome Screen Content
# ============================================
Write-Host "`n10. Testing Welcome Screen Content" -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri $baseUrl -UseBasicParsing
    
    $expectedSections = @(
        "Guitar Design Tools",
        "Art Studio",
        "CAM Tools",
        "Calculators",
        "CNC Business",
        "Blueprint Lab"
    )
    
    $allFound = $true
    foreach ($section in $expectedSections) {
        if ($response.Content -match [regex]::Escape($section)) {
            Write-Host "  ✓ Found section: $section" -ForegroundColor Green
        } else {
            Write-Host "  ✗ Missing section: $section" -ForegroundColor Red
            $allFound = $false
        }
    }
    
    if ($allFound) {
        $testsPassed++
    } else {
        $testsFailed++
    }
} catch {
    Write-Host "  ✗ FAIL - Error: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# ============================================
# SUMMARY
# ============================================
Write-Host "`n=== TEST SUMMARY ===" -ForegroundColor Cyan
Write-Host "Tests Passed: $testsPassed" -ForegroundColor Green
Write-Host "Tests Failed: $testsFailed" -ForegroundColor Red
Write-Host "Total Tests:  $($testsPassed + $testsFailed)" -ForegroundColor White

if ($testsFailed -eq 0) {
    Write-Host "`n✅ ALL TESTS PASSED! Navigation consolidation successful!" -ForegroundColor Green
    Write-Host "`n🎉 NEW NAVIGATION STRUCTURE:" -ForegroundColor Cyan
    Write-Host "   1. 🎸 Guitar Design Tools (14 tools across 6 phases)" -ForegroundColor White
    Write-Host "   2. 🎨 Art Studio (with Blueprint Lab + design tools)" -ForegroundColor White
    Write-Host "   3. ⚙️ CAM Tools (production dashboard + utilities)" -ForegroundColor White
    Write-Host "   4. 🧮 Calculators (4 pure math/business tools)" -ForegroundColor White
    Write-Host "   5. 💼 CNC Business (complete business planning)" -ForegroundColor White
} else {
    Write-Host "`n⚠️ SOME TESTS FAILED - Review errors above" -ForegroundColor Yellow
}

Write-Host "`n"
