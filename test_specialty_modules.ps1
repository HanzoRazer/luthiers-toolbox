#!/usr/bin/env pwsh
# Test Specialty Modules Integration (Archtop, Stratocaster, Smart Guitar)

Write-Host "`n=== Testing Specialty Modules Integration ===" -ForegroundColor Cyan
Write-Host "Testing: Archtop, Stratocaster, Smart Guitar routers" -ForegroundColor Gray

$API_URL = "http://localhost:8000"
$success_count = 0
$fail_count = 0

function Test-Endpoint {
    param($Name, $Endpoint, $ExpectedKeys = @())
    
    Write-Host "`nTesting: $Name" -ForegroundColor Yellow
    Write-Host "  GET $Endpoint" -ForegroundColor Gray
    
    try {
        $response = Invoke-RestMethod -Uri "$API_URL$Endpoint" -Method Get -ErrorAction Stop
        
        if ($response.ok -eq $true) {
            Write-Host "  ✓ Success" -ForegroundColor Green
            
            # Check for expected keys
            foreach ($key in $ExpectedKeys) {
                if ($response.PSObject.Properties.Name -contains $key) {
                    Write-Host "    - Found key: $key" -ForegroundColor Gray
                } else {
                    Write-Host "    ⚠ Missing key: $key" -ForegroundColor Yellow
                }
            }
            
            $script:success_count++
            return $true
        } else {
            Write-Host "  ✗ Response ok=false" -ForegroundColor Red
            $script:fail_count++
            return $false
        }
    }
    catch {
        Write-Host "  ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
        $script:fail_count++
        return $false
    }
}

# Test main health endpoint
Write-Host "`n1. Testing Main API Health" -ForegroundColor Cyan
Test-Endpoint "Main Health Check" "/health"

# Test Archtop Module
Write-Host "`n2. Testing Archtop Module" -ForegroundColor Cyan
Test-Endpoint "Archtop Health" "/cam/archtop/health" @("module", "contour_generator")
Test-Endpoint "Archtop Kits List" "/cam/archtop/kits" @("kits")

# Test Stratocaster Module
Write-Host "`n3. Testing Stratocaster Module" -ForegroundColor Cyan
Test-Endpoint "Stratocaster Health" "/cam/stratocaster/health" @("module", "templates_dir_exists")
Test-Endpoint "Stratocaster Templates" "/cam/stratocaster/templates" @("templates", "total_count")
Test-Endpoint "Stratocaster BOM" "/cam/stratocaster/bom?series=Player II" @("items", "total_low", "total_high")
Test-Endpoint "Stratocaster Specs" "/cam/stratocaster/specs" @("specs", "model")
Test-Endpoint "Stratocaster Presets" "/cam/stratocaster/presets" @("presets", "model")
Test-Endpoint "Stratocaster Resources" "/cam/stratocaster/resources" @("resources")

# Test Smart Guitar Module
Write-Host "`n4. Testing Smart Guitar Module" -ForegroundColor Cyan
Test-Endpoint "Smart Guitar Health" "/cam/smart-guitar/health" @("module", "bundle_exists")
Test-Endpoint "Smart Guitar Info" "/cam/smart-guitar/info" @("bundle_version", "resources")
Test-Endpoint "Smart Guitar Overview" "/cam/smart-guitar/overview" @("overview", "concept")
Test-Endpoint "Smart Guitar Resources" "/cam/smart-guitar/resources" @("resources")
Test-Endpoint "Smart Guitar Integration Notes" "/cam/smart-guitar/integration-notes" @("integration_notes")

# Summary
Write-Host "`n=== Test Summary ===" -ForegroundColor Cyan
Write-Host "Passed: $success_count" -ForegroundColor Green
Write-Host "Failed: $fail_count" -ForegroundColor $(if ($fail_count -gt 0) { "Red" } else { "Green" })

if ($fail_count -eq 0) {
    Write-Host "`n✓ All specialty modules integrated successfully!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n⚠ Some tests failed. Check the output above." -ForegroundColor Yellow
    exit 1
}
