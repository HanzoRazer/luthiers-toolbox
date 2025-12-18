# test_data_registry.ps1
# Phase 7: Data Registry Smoke Tests
# Tests registry API endpoints and edition-based entitlements

Write-Host "🧪 Data Registry Smoke Tests" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"
$passed = 0
$failed = 0

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Method = "GET",
        [hashtable]$Headers = @{},
        [int]$ExpectedStatus = 200,
        [scriptblock]$Validate = $null
    )
    
    Write-Host "Test: $Name" -ForegroundColor Yellow
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            ContentType = "application/json"
        }
        if ($Headers.Count -gt 0) {
            $params.Headers = $Headers
        }
        
        $response = Invoke-WebRequest @params -ErrorAction Stop
        $data = $response.Content | ConvertFrom-Json
        
        if ($response.StatusCode -eq $ExpectedStatus) {
            if ($Validate) {
                $result = & $Validate $data
                if ($result) {
                    Write-Host "  ✓ Passed" -ForegroundColor Green
                    $script:passed++
                } else {
                    Write-Host "  ❌ Validation failed" -ForegroundColor Red
                    $script:failed++
                }
            } else {
                Write-Host "  ✓ Passed (status $($response.StatusCode))" -ForegroundColor Green
                $script:passed++
            }
        } else {
            Write-Host "  ❌ Expected $ExpectedStatus, got $($response.StatusCode)" -ForegroundColor Red
            $script:failed++
        }
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        if ($statusCode -eq $ExpectedStatus) {
            Write-Host "  ✓ Passed (expected $ExpectedStatus)" -ForegroundColor Green
            $script:passed++
        } else {
            Write-Host "  ❌ Error: $_" -ForegroundColor Red
            $script:failed++
        }
    }
    Write-Host ""
}

# ============================================================================
# Test 1: Registry Info (Express)
# ============================================================================
Test-Endpoint -Name "Registry Info (Express)" `
    -Url "$baseUrl/api/registry/info?edition=express" `
    -Validate {
        param($data)
        $data.edition -eq "express" -and $data.edition_datasets.Count -eq 0
    }

# ============================================================================
# Test 2: Registry Info (Pro)
# ============================================================================
Test-Endpoint -Name "Registry Info (Pro)" `
    -Url "$baseUrl/api/registry/info?edition=pro" `
    -Validate {
        param($data)
        $data.edition -eq "pro" -and $data.edition_datasets.Count -gt 0
    }

# ============================================================================
# Test 3: Scale Lengths (System Tier - All Editions)
# ============================================================================
Test-Endpoint -Name "Scale Lengths (Express)" `
    -Url "$baseUrl/api/registry/scale_lengths?edition=express" `
    -Validate {
        param($data)
        $data.count -gt 0 -and $data.scales -ne $null
    }

# ============================================================================
# Test 4: Wood Species (System Tier)
# ============================================================================
Test-Endpoint -Name "Wood Species (Express)" `
    -Url "$baseUrl/api/registry/wood_species?edition=express" `
    -Validate {
        param($data)
        $data.count -gt 0 -and $data.species -ne $null
    }

# ============================================================================
# Test 5: Fret Formulas (System Tier)
# ============================================================================
Test-Endpoint -Name "Fret Formulas (Express)" `
    -Url "$baseUrl/api/registry/fret_formulas?edition=express" `
    -Validate {
        param($data)
        $data.formulas -ne $null
    }

# ============================================================================
# Test 6: Empirical Limits - Express (Should 403)
# ============================================================================
Test-Endpoint -Name "Empirical Limits (Express - Should 403)" `
    -Url "$baseUrl/api/registry/empirical_limits" `
    -Headers @{ "X-Edition" = "express" } `
    -ExpectedStatus 403

# ============================================================================
# Test 7: Empirical Limits - Pro (Should 200)
# ============================================================================
Test-Endpoint -Name "Empirical Limits (Pro - Should 200)" `
    -Url "$baseUrl/api/registry/empirical_limits" `
    -Headers @{ "X-Edition" = "pro" } `
    -Validate {
        param($data)
        $data.count -gt 0 -and $data.limits -ne $null
    }

# ============================================================================
# Test 8: Empirical Limits - Enterprise (Should 200)
# ============================================================================
Test-Endpoint -Name "Empirical Limits (Enterprise - Should 200)" `
    -Url "$baseUrl/api/registry/empirical_limits" `
    -Headers @{ "X-Edition" = "enterprise" } `
    -Validate {
        param($data)
        $data.count -gt 0
    }

# ============================================================================
# Test 9: Registry Health
# ============================================================================
Test-Endpoint -Name "Registry Health" `
    -Url "$baseUrl/api/registry/health" `
    -Validate {
        param($data)
        $data.status -in @("healthy", "degraded") -and $data.checks -ne $null
    }

# ============================================================================
# Test 10: Specific Wood Empirical Limit (Pro)
# ============================================================================
Test-Endpoint -Name "Empirical Limit by Wood (Pro)" `
    -Url "$baseUrl/api/registry/empirical_limits/maple_hard" `
    -Headers @{ "X-Edition" = "pro" } `
    -Validate {
        param($data)
        $data.wood_id -eq "maple_hard" -and $data.limits -ne $null
    }

# ============================================================================
# Summary
# ============================================================================
Write-Host "=============================" -ForegroundColor Cyan
Write-Host "Results: $passed passed, $failed failed" -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Red" })
Write-Host ""

if ($failed -eq 0) {
    Write-Host "✅ All Data Registry tests passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "❌ Some tests failed. Check output above." -ForegroundColor Red
    exit 1
}
