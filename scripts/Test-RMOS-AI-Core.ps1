# Test-RMOS-AI-Core.ps1
# Integration tests for RMOS AI Core: Constraint Profiles, Generator, Snapshots, Logging

param(
    [string]$BaseUrl = "http://localhost:8010"
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

Write-Host "`n=== RMOS AI Core Integration Tests ===" -ForegroundColor Cyan
Write-Host "Target: $BaseUrl`n" -ForegroundColor Gray

$passed = 0
$failed = 0

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Url,
        [object]$Body = $null,
        [scriptblock]$Validate
    )
    
    Write-Host "[$($passed + $failed + 1)] $Name... " -NoNewline
    
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            ContentType = "application/json"
        }
        
        if ($Body) {
            $params.Body = ($Body | ConvertTo-Json -Depth 10)
        }
        
        $response = Invoke-RestMethod @params
        
        if ($Validate) {
            $result = & $Validate $response
            if ($result -eq $true) {
                Write-Host "PASS" -ForegroundColor Green
                $script:passed++
            } else {
                Write-Host "FAIL - $result" -ForegroundColor Red
                $script:failed++
            }
        } else {
            Write-Host "PASS" -ForegroundColor Green
            $script:passed++
        }
        
        return $response
    }
    catch {
        Write-Host "FAIL - $($_.Exception.Message)" -ForegroundColor Red
        $script:failed++
        return $null
    }
}

# =====================
# Constraint Profiles API
# =====================

Write-Host "`n--- Constraint Profiles API ---" -ForegroundColor Yellow

# Test 1: List constraint profiles
Test-Endpoint -Name "List constraint profiles" -Method "GET" `
    -Url "$BaseUrl/api/rmos/ai/constraint-profiles/list" `
    -Validate {
        param($r)
        if ($r -is [array] -and $r.Count -ge 5) {
            if ($r -contains "default" -and $r -contains "thin_saw") {
                return $true
            }
            return "Missing expected profiles"
        }
        return "Expected array with 5+ profiles"
    }

# Test 2: Resolve default profile
Test-Endpoint -Name "Resolve default profile (no context)" -Method "GET" `
    -Url "$BaseUrl/api/rmos/ai/constraint-profiles/resolve" `
    -Validate {
        param($r)
        if ($r.min_rings -eq 1 -and $r.max_rings -le 12 -and $r.palette_key) {
            return $true
        }
        return "Invalid profile structure"
    }

# Test 3: Resolve profile with saw tool
Test-Endpoint -Name "Resolve profile (saw tool)" -Method "GET" `
    -Url "$BaseUrl/api/rmos/ai/constraint-profiles/resolve?tool_id=Thin_Saw_1mm" `
    -Validate {
        param($r)
        # Should pick thin_saw profile with max_rings <= 6
        if ($r.max_rings -le 6 -and $r.min_ring_width_mm -ge 0.4) {
            return $true
        }
        return "Expected thin_saw profile constraints"
    }

# Test 4: Resolve profile with shell material
Test-Endpoint -Name "Resolve profile (shell material)" -Method "GET" `
    -Url "$BaseUrl/api/rmos/ai/constraint-profiles/resolve?material_id=Abalone_Shell" `
    -Validate {
        param($r)
        if ($r.palette_key -eq "premium_shell" -or $r.allow_mosaic -eq $true) {
            return $true
        }
        return "Expected premium_shell profile"
    }

# =====================
# Generator Snapshots API
# =====================

Write-Host "`n--- Generator Snapshots API ---" -ForegroundColor Yellow

# Test 5: Default snapshot
Test-Endpoint -Name "Generator snapshot (default)" -Method "GET" `
    -Url "$BaseUrl/api/rmos/ai/snapshots?n_samples=10&deterministic=true" `
    -Validate {
        param($r)
        if ($r.n_samples -eq 10 -and $r.ring_count_min -ge 0 -and $r.ring_count_max -le 12) {
            return $true
        }
        return "Invalid snapshot stats"
    }

# Test 6: Snapshot with saw tool context
Test-Endpoint -Name "Generator snapshot (saw context)" -Method "GET" `
    -Url "$BaseUrl/api/rmos/ai/snapshots?tool_id=Saw_Thin&n_samples=5" `
    -Validate {
        param($r)
        if ($r.n_samples -eq 5 -and $r.profile) {
            # thin_saw profile should limit to 6 rings max
            if ($r.profile.max_rings -le 6) {
                return $true
            }
            return "Expected thin_saw profile"
        }
        return "Invalid snapshot structure"
    }

# Test 7: Snapshot respects policy caps
Test-Endpoint -Name "Generator snapshot (respects policy caps)" -Method "GET" `
    -Url "$BaseUrl/api/rmos/ai/snapshots?n_samples=5" `
    -Validate {
        param($r)
        # Global cap: max_rings <= 12, max_total_width <= 12.0
        if ($r.profile.max_rings -le 12 -and $r.profile.max_total_width_mm -le 12.0) {
            return $true
        }
        return "Profile exceeds global caps"
    }

# =====================
# AI Logs Viewer API
# =====================

Write-Host "`n--- AI Logs Viewer API ---" -ForegroundColor Yellow

# Test 8: List AI attempts (may be empty)
Test-Endpoint -Name "List AI attempts" -Method "GET" `
    -Url "$BaseUrl/api/rmos/logs/ai/attempts?limit=10" `
    -Validate {
        param($r)
        if ($r -is [array]) {
            return $true
        }
        return "Expected array"
    }

# Test 9: List AI runs (may be empty)
Test-Endpoint -Name "List AI runs" -Method "GET" `
    -Url "$BaseUrl/api/rmos/logs/ai/runs?limit=10" `
    -Validate {
        param($r)
        if ($r -is [array]) {
            return $true
        }
        return "Expected array"
    }

# Test 10: Filtered attempts query
Test-Endpoint -Name "Filtered AI attempts (tool_id)" -Method "GET" `
    -Url "$BaseUrl/api/rmos/logs/ai/attempts?tool_id=Test_Tool&limit=5" `
    -Validate {
        param($r)
        if ($r -is [array]) {
            return $true
        }
        return "Expected array"
    }

# =====================
# Summary
# =====================

Write-Host "`n=== Test Summary ===" -ForegroundColor Cyan
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Gray" })

if ($failed -gt 0) {
    Write-Host "`nSome tests failed!" -ForegroundColor Red
    exit 1
} else {
    Write-Host "`nAll tests passed!" -ForegroundColor Green
    exit 0
}
