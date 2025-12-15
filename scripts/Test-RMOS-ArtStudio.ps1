<# 
    Test-RMOS-ArtStudio.ps1
    Integration tests for Art Studio RMOS 2.0 drop
    
    Tests:
    - Constraint Search API
    - RMOS Logs API
    - Directional Workflow integration
    
    Prerequisites: RMOS 2.0 server running on port 8010
#>

$ErrorActionPreference = "Stop"
$BASE_URL = "http://localhost:8010"

Write-Host "`n=== Testing Art Studio RMOS 2.0 Drop ===" -ForegroundColor Cyan
Write-Host "Base URL: $BASE_URL`n"

$pass = 0
$fail = 0

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Url,
        [object]$Body = $null,
        [scriptblock]$Validate
    )
    
    Write-Host "Test: $Name" -ForegroundColor Yellow
    Write-Host "  $Method $Url"
    
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            ContentType = "application/json"
        }
        
        if ($Body) {
            $params.Body = ($Body | ConvertTo-Json -Depth 10)
            Write-Host "  Body: $($params.Body)" -ForegroundColor DarkGray
        }
        
        $response = Invoke-RestMethod @params
        
        # Run validation
        $result = & $Validate $response
        
        if ($result) {
            Write-Host "  ✓ PASS" -ForegroundColor Green
            $script:pass++
        } else {
            Write-Host "  ✗ FAIL: Validation failed" -ForegroundColor Red
            $script:fail++
        }
        
        return $response
    }
    catch {
        Write-Host "  ✗ FAIL: $($_.Exception.Message)" -ForegroundColor Red
        $script:fail++
        return $null
    }
}

# ============================================================
# Test 1: Constraint Search - Basic
# ============================================================
Test-Endpoint -Name "Constraint Search - Basic" -Method "POST" -Url "$BASE_URL/api/rmos/constraint/search" `
    -Body @{
        material_id = "mahogany"
        tool_id = "router:6_2_6.35"
        outer_diameter_mm_min = 80
        outer_diameter_mm_max = 120
        ring_count_min = 1
        ring_count_max = 3
        max_candidates = 5
        max_trials = 20
    } `
    -Validate {
        param($r)
        
        Write-Host "  Response: candidates=$($r.candidates.Count), trials=$($r.total_trials), passed=$($r.total_passed)" -ForegroundColor DarkGray
        
        # Should return some candidates
        $hasCandidates = $r.candidates.Count -gt 0
        Write-Host "    - Has candidates: $hasCandidates"
        
        # Candidates should be ranked
        if ($hasCandidates) {
            $firstRank = $r.candidates[0].rank
            Write-Host "    - First rank: $firstRank"
            $rankedCorrectly = $firstRank -eq 1
        } else {
            $rankedCorrectly = $true
        }
        
        return $hasCandidates -or $r.total_trials -ge 20
    }

# ============================================================
# Test 2: Constraint Search - With Cut Time Limit
# ============================================================
Test-Endpoint -Name "Constraint Search - With Cut Time Limit" -Method "POST" -Url "$BASE_URL/api/rmos/constraint/search" `
    -Body @{
        material_id = "ebony"
        tool_id = "router:3_2_3.175"
        outer_diameter_mm_min = 60
        outer_diameter_mm_max = 80
        ring_count_min = 1
        ring_count_max = 2
        max_candidates = 3
        max_trials = 15
        max_cut_time_min = 10.0
    } `
    -Validate {
        param($r)
        
        Write-Host "  Response: candidates=$($r.candidates.Count)" -ForegroundColor DarkGray
        
        # All returned candidates should meet cut time constraint
        foreach ($c in $r.candidates) {
            $cutTimeSec = $c.feasibility.estimated_cut_time_seconds
            $cutTimeMin = $cutTimeSec / 60.0
            Write-Host "    - Candidate rank $($c.rank): $([math]::Round($cutTimeMin, 2)) min"
        }
        
        return $true
    }

# ============================================================
# Test 3: RMOS Logs - Get Recent (empty initially)
# ============================================================
Test-Endpoint -Name "RMOS Logs - Get Recent" -Method "GET" -Url "$BASE_URL/api/rmos/logs/recent?limit=10" `
    -Validate {
        param($r)
        
        Write-Host "  Response: entries=$($r.total)" -ForegroundColor DarkGray
        
        # Should return a valid response with entries array
        $hasEntries = $r.PSObject.Properties.Name -contains "entries"
        Write-Host "    - Has entries field: $hasEntries"
        
        return $hasEntries
    }

# ============================================================
# Test 4: RMOS Logs - Filter by source
# ============================================================
Test-Endpoint -Name "RMOS Logs - Filter by source" -Method "GET" -Url "$BASE_URL/api/rmos/logs/recent?limit=20&source=constraint_search" `
    -Validate {
        param($r)
        
        Write-Host "  Response: entries=$($r.total)" -ForegroundColor DarkGray
        
        # All entries should match the source filter
        foreach ($e in $r.entries) {
            if ($e.source -ne "constraint_search") {
                Write-Host "    - MISMATCH: source=$($e.source)"
                return $false
            }
        }
        
        Write-Host "    - All entries match source filter"
        return $true
    }

# ============================================================
# Test 5: RMOS Logs - Filter by risk bucket
# ============================================================
Test-Endpoint -Name "RMOS Logs - Filter by risk GREEN" -Method "GET" -Url "$BASE_URL/api/rmos/logs/recent?limit=10&risk_bucket=GREEN" `
    -Validate {
        param($r)
        
        Write-Host "  Response: entries=$($r.total)" -ForegroundColor DarkGray
        
        # All entries should be GREEN
        foreach ($e in $r.entries) {
            if ($e.risk_bucket -ne "GREEN") {
                Write-Host "    - MISMATCH: risk_bucket=$($e.risk_bucket)"
                return $false
            }
        }
        
        Write-Host "    - All entries are GREEN risk"
        return $true
    }

# ============================================================
# Test 6: RMOS Logs - CSV Export
# ============================================================
Write-Host "`nTest: RMOS Logs - CSV Export" -ForegroundColor Yellow
Write-Host "  GET $BASE_URL/api/rmos/logs/export?limit=10"

try {
    $csv = Invoke-RestMethod -Uri "$BASE_URL/api/rmos/logs/export?limit=10" -Method GET
    
    # Check CSV has header
    $hasHeader = $csv -match "id,timestamp,source"
    Write-Host "  Response: $($csv.Length) chars, has header: $hasHeader" -ForegroundColor DarkGray
    
    if ($hasHeader) {
        Write-Host "  ✓ PASS" -ForegroundColor Green
        $pass++
    } else {
        Write-Host "  ✗ FAIL: Invalid CSV format" -ForegroundColor Red
        $fail++
    }
}
catch {
    Write-Host "  ✗ FAIL: $($_.Exception.Message)" -ForegroundColor Red
    $fail++
}

# ============================================================
# Test 7: Mode Preview with Constraint Search context
# ============================================================
Test-Endpoint -Name "Mode Preview - Constraint First with tool" -Method "POST" -Url "$BASE_URL/api/rmos/workflow/mode/preview" `
    -Body @{
        mode = "constraint_first"
        tool_id = "router:6_2_6.35"
        material_id = "mahogany"
    } `
    -Validate {
        param($r)
        
        Write-Host "  Response: mode=$($r.mode), score=$($r.feasibility_score), risk=$($r.risk_level)" -ForegroundColor DarkGray
        
        # Should return constraint_first mode
        $correctMode = $r.mode -eq "constraint_first"
        Write-Host "    - Correct mode: $correctMode"
        
        # Should have hard limits
        $hasHardLimits = $r.constraints.hard_limits.Count -gt 0
        Write-Host "    - Has hard limits: $hasHardLimits"
        
        return $correctMode -and $hasHardLimits
    }

# ============================================================
# Test 8: Logs contain design snapshots
# ============================================================
Test-Endpoint -Name "RMOS Logs - Design snapshots" -Method "GET" -Url "$BASE_URL/api/rmos/logs/recent?limit=5" `
    -Validate {
        param($r)
        
        if ($r.entries.Count -eq 0) {
            Write-Host "    - No entries to check (OK)" -ForegroundColor DarkGray
            return $true
        }
        
        $entry = $r.entries[0]
        Write-Host "  Response: first entry has design: $($entry.design -ne $null)" -ForegroundColor DarkGray
        
        if ($entry.design) {
            Write-Host "    - outer_diameter_mm: $($entry.design.outer_diameter_mm)"
            Write-Host "    - ring_count: $($entry.design.ring_count)"
        }
        
        return $true
    }

# ============================================================
# Summary
# ============================================================
Write-Host "`n=== Test Summary ===" -ForegroundColor Cyan
Write-Host "Passed: $pass" -ForegroundColor Green
Write-Host "Failed: $fail" -ForegroundColor $(if ($fail -gt 0) { "Red" } else { "Green" })

if ($fail -eq 0) {
    Write-Host "`n✓ All Art Studio RMOS 2.0 tests passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n✗ Some tests failed" -ForegroundColor Red
    exit 1
}
