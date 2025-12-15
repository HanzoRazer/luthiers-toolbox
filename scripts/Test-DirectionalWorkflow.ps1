<# 
    Test-DirectionalWorkflow.ps1
    Integration tests for Directional Workflow 2.0
    
    Prerequisites: RMOS 2.0 server running on port 8010
#>

$ErrorActionPreference = "Stop"
$BASE_URL = "http://localhost:8010"

Write-Host "`n=== Testing Directional Workflow 2.0 ===" -ForegroundColor Cyan
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
# Test 1: List workflow modes
# ============================================================
Test-Endpoint -Name "List workflow modes" -Method "GET" -Url "$BASE_URL/api/rmos/workflow/modes" -Validate {
    param($r)
    
    Write-Host "  Response: $($r | ConvertTo-Json -Depth 3 -Compress)" -ForegroundColor DarkGray
    
    $hasDesignFirst = $r.modes | Where-Object { $_.id -eq "design_first" }
    $hasConstraintFirst = $r.modes | Where-Object { $_.id -eq "constraint_first" }
    $hasAiAssisted = $r.modes | Where-Object { $_.id -eq "ai_assisted" }
    
    Write-Host "    - design_first: $($hasDesignFirst -ne $null)"
    Write-Host "    - constraint_first: $($hasConstraintFirst -ne $null)"
    Write-Host "    - ai_assisted: $($hasAiAssisted -ne $null)"
    Write-Host "    - default_mode: $($r.default_mode)"
    
    return ($hasDesignFirst -and $hasConstraintFirst -and $hasAiAssisted -and $r.default_mode -eq "design_first")
}

# ============================================================
# Test 2: Design-first mode preview
# ============================================================
Test-Endpoint -Name "Design-first mode preview" -Method "POST" -Url "$BASE_URL/api/rmos/workflow/mode/preview" `
    -Body @{
        mode = "design_first"
        tool_id = "router:6_2_6.35"
    } `
    -Validate {
        param($r)
        
        Write-Host "  Response: $($r | ConvertTo-Json -Depth 3 -Compress)" -ForegroundColor DarkGray
        
        Write-Host "    - mode: $($r.mode)"
        Write-Host "    - hard_limits: $($r.constraints.hard_limits | ConvertTo-Json -Compress)"
        Write-Host "    - warnings: $($r.warnings -join '; ')"
        
        # Design-first should have no hard limits (empty dict or null)
        $hardLimitsJson = $r.constraints.hard_limits | ConvertTo-Json -Compress
        $noHardLimits = ($hardLimitsJson -eq "{}" -or $hardLimitsJson -eq "null" -or $r.constraints.hard_limits.PSObject.Properties.Count -eq 0)
        Write-Host "    - No hard limits: $noHardLimits"
        
        return ($r.mode -eq "design_first" -and $noHardLimits)
    }

# ============================================================
# Test 3: Constraint-first mode preview
# ============================================================
Test-Endpoint -Name "Constraint-first mode preview" -Method "POST" -Url "$BASE_URL/api/rmos/workflow/mode/preview" `
    -Body @{
        mode = "constraint_first"
        tool_id = "router:6_2_6.35"
        material_id = "mahogany"
    } `
    -Validate {
        param($r)
        
        Write-Host "  Response: $($r | ConvertTo-Json -Depth 3 -Compress)" -ForegroundColor DarkGray
        
        Write-Host "    - mode: $($r.mode)"
        Write-Host "    - hard_limits: $($r.constraints.hard_limits | ConvertTo-Json -Compress)"
        Write-Host "    - feasibility_score: $($r.feasibility_score)"
        Write-Host "    - risk_level: $($r.risk_level)"
        
        # Constraint-first should have hard limits
        $hasHardLimits = ($r.constraints.hard_limits.Count -gt 0)
        Write-Host "    - Has hard limits: $hasHardLimits"
        
        return ($r.mode -eq "constraint_first" -and $hasHardLimits -and $r.risk_level -eq "GREEN")
    }

# ============================================================
# Test 4: AI-assisted mode preview with goal weights
# ============================================================
Test-Endpoint -Name "AI-assisted mode preview" -Method "POST" -Url "$BASE_URL/api/rmos/workflow/mode/preview" `
    -Body @{
        mode = "ai_assisted"
        goal_speed = 0.8
        goal_quality = 0.4
        goal_tool_life = 0.3
    } `
    -Validate {
        param($r)
        
        Write-Host "  Response: $($r | ConvertTo-Json -Depth 3 -Compress)" -ForegroundColor DarkGray
        
        Write-Host "    - mode: $($r.mode)"
        Write-Host "    - feasibility_score: $($r.feasibility_score)"
        Write-Host "    - risk_level: $($r.risk_level)"
        Write-Host "    - recommendations: $($r.recommendations.Count) items"
        
        foreach ($rec in $r.recommendations) {
            Write-Host "      • $rec" -ForegroundColor DarkGray
        }
        
        # AI-assisted should have recommendations
        $hasRecommendations = ($r.recommendations.Count -gt 0)
        Write-Host "    - Has recommendations: $hasRecommendations"
        
        return ($r.mode -eq "ai_assisted" -and $hasRecommendations)
    }

# ============================================================
# Test 5: Get constraints for specific mode
# ============================================================
Test-Endpoint -Name "Get constraint_first constraints" -Method "GET" `
    -Url "$BASE_URL/api/rmos/workflow/mode/constraint_first/constraints" `
    -Validate {
        param($r)
        
        Write-Host "  Response: $($r | ConvertTo-Json -Depth 3 -Compress)" -ForegroundColor DarkGray
        
        Write-Host "    - mode: $($r.mode)"
        Write-Host "    - max_rpm: $($r.hard_limits.max_rpm)"
        Write-Host "    - max_feed: $($r.hard_limits.max_feed_mm_min)"
        Write-Host "    - suggestions: $($r.suggestions.Count) items"
        
        return ($r.mode -eq "constraint_first" -and $r.hard_limits.max_rpm -eq 18000)
    }

# ============================================================
# Test 6: Saw tool mode detection in preview
# ============================================================
Test-Endpoint -Name "Saw tool mode in preview" -Method "POST" -Url "$BASE_URL/api/rmos/workflow/mode/preview" `
    -Body @{
        mode = "constraint_first"
        tool_id = "saw:10_24_3.0"
    } `
    -Validate {
        param($r)
        
        Write-Host "  Response: $($r | ConvertTo-Json -Depth 3 -Compress)" -ForegroundColor DarkGray
        
        Write-Host "    - mode: $($r.mode)"
        Write-Host "    - max_rpm (saw): $($r.constraints.hard_limits.max_rpm)"
        
        # Saw mode should have lower RPM limit (6000)
        $sawRpmLimit = $r.constraints.hard_limits.max_rpm -le 6000
        Write-Host "    - Saw RPM limit applied: $sawRpmLimit"
        
        $hasSawSuggestion = $r.constraints.suggestions -match "Saw mode"
        Write-Host "    - Saw mode suggestion: $hasSawSuggestion"
        
        return ($sawRpmLimit -and $hasSawSuggestion)
    }

# ============================================================
# Test 7: Invalid mode handling
# ============================================================
Write-Host "`nTest: Invalid mode handling" -ForegroundColor Yellow
Write-Host "  GET $BASE_URL/api/rmos/workflow/mode/invalid_mode/constraints"

try {
    Invoke-RestMethod -Uri "$BASE_URL/api/rmos/workflow/mode/invalid_mode/constraints" -Method GET
    Write-Host "  ✗ FAIL: Should have returned error" -ForegroundColor Red
    $fail++
}
catch {
    if ($_.Exception.Response.StatusCode -eq 400) {
        Write-Host "  ✓ PASS: Correctly returned 400 Bad Request" -ForegroundColor Green
        $pass++
    } else {
        Write-Host "  ✗ FAIL: Wrong error status: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
        $fail++
    }
}

# ============================================================
# Summary
# ============================================================
Write-Host "`n=== Test Summary ===" -ForegroundColor Cyan
Write-Host "Passed: $pass" -ForegroundColor Green
Write-Host "Failed: $fail" -ForegroundColor $(if ($fail -gt 0) { "Red" } else { "Green" })

if ($fail -eq 0) {
    Write-Host "`n✓ All Directional Workflow 2.0 tests passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n✗ Some tests failed" -ForegroundColor Red
    exit 1
}
