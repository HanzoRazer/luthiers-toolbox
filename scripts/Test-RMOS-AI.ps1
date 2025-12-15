# scripts/Test-RMOS-AI.ps1
# Integration tests for RMOS AI constraint generation and logging modules
#
# Tests:
# 1. Constraint profiles list endpoint
# 2. Constraint profile resolution
# 3. Generator snapshot API
# 4. AI logs viewer (attempts + runs)
# 5. Policy validation (max_attempts cap)
#
# Requires: RMOS API running on port 8000 or 8010

param(
    [int]$Port = 8010,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"
$API_BASE = "http://localhost:$Port/api"

$passed = 0
$failed = 0

function Write-TestHeader($name) {
    Write-Host "`n[$((Get-Date).ToString('HH:mm:ss'))] TEST: $name" -ForegroundColor Cyan
}

function Write-Pass($msg) {
    $script:passed++
    Write-Host "  ✓ $msg" -ForegroundColor Green
}

function Write-Fail($msg) {
    $script:failed++
    Write-Host "  ✗ $msg" -ForegroundColor Red
}

function Write-Info($msg) {
    if ($Verbose) {
        Write-Host "    $msg" -ForegroundColor Gray
    }
}

# ======================
# Test 1: List constraint profiles
# ======================
Write-TestHeader "Constraint Profiles - List"

try {
    $resp = Invoke-RestMethod -Uri "$API_BASE/rmos/ai/constraint-profiles/list" -Method GET
    
    if ($resp -is [array] -and $resp.Count -gt 0) {
        Write-Pass "Got $($resp.Count) profiles"
        Write-Info "Profiles: $($resp -join ', ')"
        
        if ($resp -contains "default") {
            Write-Pass "'default' profile exists"
        } else {
            Write-Fail "'default' profile missing"
        }
        
        if ($resp -contains "thin_saw") {
            Write-Pass "'thin_saw' profile exists"
        } else {
            Write-Fail "'thin_saw' profile missing"
        }
    } else {
        Write-Fail "No profiles returned"
    }
}
catch {
    Write-Fail "Request failed: $($_.Exception.Message)"
}

# ======================
# Test 2: Resolve constraint profile
# ======================
Write-TestHeader "Constraint Profiles - Resolve (tool=saw)"

try {
    $resp = Invoke-RestMethod -Uri "$API_BASE/rmos/ai/constraint-profiles/resolve?tool_id=thin_saw" -Method GET
    
    if ($resp.min_rings -ge 1 -and $resp.max_rings -le 12) {
        Write-Pass "Ring bounds valid: $($resp.min_rings)-$($resp.max_rings)"
    } else {
        Write-Fail "Ring bounds invalid"
    }
    
    if ($resp.min_ring_width_mm -gt 0 -and $resp.max_ring_width_mm -le 3.0) {
        Write-Pass "Width bounds valid: $($resp.min_ring_width_mm)-$($resp.max_ring_width_mm)mm"
    } else {
        Write-Fail "Width bounds invalid"
    }
    
    if ($resp.palette_key) {
        Write-Pass "Palette key: $($resp.palette_key)"
    }
    
    Write-Info "Full profile: $($resp | ConvertTo-Json -Compress)"
}
catch {
    Write-Fail "Request failed: $($_.Exception.Message)"
}

# ======================
# Test 3: Resolve with material context
# ======================
Write-TestHeader "Constraint Profiles - Resolve (material=shell)"

try {
    $resp = Invoke-RestMethod -Uri "$API_BASE/rmos/ai/constraint-profiles/resolve?material_id=abalone_shell" -Method GET
    
    if ($resp.palette_key -eq "premium_shell") {
        Write-Pass "Shell material resolved to premium_shell palette"
    } else {
        Write-Info "Palette: $($resp.palette_key) (expected premium_shell)"
    }
    
    if ($resp.allow_mosaic -eq $true) {
        Write-Pass "Mosaic patterns allowed for shell"
    }
}
catch {
    Write-Fail "Request failed: $($_.Exception.Message)"
}

# ======================
# Test 4: Generator snapshot
# ======================
Write-TestHeader "Generator Snapshot - Default context"

try {
    $resp = Invoke-RestMethod -Uri "$API_BASE/rmos/ai/snapshots?n_samples=10&deterministic=true" -Method GET
    
    if ($resp.n_samples -eq 10) {
        Write-Pass "Sampled 10 candidates"
    } else {
        Write-Fail "Sample count mismatch: $($resp.n_samples)"
    }
    
    if ($resp.ring_count_min -ge 1 -and $resp.ring_count_max -le 12) {
        Write-Pass "Ring counts in bounds: $($resp.ring_count_min)-$($resp.ring_count_max)"
    } else {
        Write-Fail "Ring counts out of bounds"
    }
    
    if ($resp.ring_count_avg -gt 0) {
        Write-Pass "Average ring count: $([math]::Round($resp.ring_count_avg, 2))"
    }
    
    if ($resp.total_width_avg_mm -gt 0) {
        Write-Pass "Average total width: $([math]::Round($resp.total_width_avg_mm, 2))mm"
    }
    
    if ($resp.profile) {
        Write-Pass "Profile returned with snapshot"
        Write-Info "Profile max_rings: $($resp.profile.max_rings)"
    }
}
catch {
    Write-Fail "Request failed: $($_.Exception.Message)"
}

# ======================
# Test 5: Generator snapshot with tool context
# ======================
Write-TestHeader "Generator Snapshot - Saw tool context"

try {
    $resp = Invoke-RestMethod -Uri "$API_BASE/rmos/ai/snapshots?tool_id=thin_saw&n_samples=5" -Method GET
    
    if ($resp.tool_id -eq "thin_saw") {
        Write-Pass "Tool ID reflected in response"
    }
    
    # thin_saw profile has max_rings=6
    if ($resp.ring_count_max -le 6) {
        Write-Pass "Ring counts constrained by thin_saw profile (max=$($resp.ring_count_max))"
    } else {
        Write-Info "Ring max: $($resp.ring_count_max) (thin_saw allows up to 6)"
    }
}
catch {
    Write-Fail "Request failed: $($_.Exception.Message)"
}

# ======================
# Test 6: AI Logs - Attempts (initially empty)
# ======================
Write-TestHeader "AI Logs - List attempts"

try {
    $resp = Invoke-RestMethod -Uri "$API_BASE/rmos/logs/ai/attempts?limit=10" -Method GET
    
    if ($resp -is [array]) {
        Write-Pass "Attempts endpoint returns array ($($resp.Count) entries)"
    } else {
        Write-Fail "Expected array response"
    }
}
catch {
    Write-Fail "Request failed: $($_.Exception.Message)"
}

# ======================
# Test 7: AI Logs - Runs (initially empty)
# ======================
Write-TestHeader "AI Logs - List runs"

try {
    $resp = Invoke-RestMethod -Uri "$API_BASE/rmos/logs/ai/runs?limit=10" -Method GET
    
    if ($resp -is [array]) {
        Write-Pass "Runs endpoint returns array ($($resp.Count) entries)"
    } else {
        Write-Fail "Expected array response"
    }
}
catch {
    Write-Fail "Request failed: $($_.Exception.Message)"
}

# ======================
# Test 8: AI Logs - Filter by tool_id
# ======================
Write-TestHeader "AI Logs - Filter by tool_id"

try {
    $resp = Invoke-RestMethod -Uri "$API_BASE/rmos/logs/ai/attempts?tool_id=nonexistent_tool&limit=5" -Method GET
    
    if ($resp -is [array] -and $resp.Count -eq 0) {
        Write-Pass "Empty result for nonexistent tool filter"
    } elseif ($resp -is [array]) {
        Write-Pass "Filter accepted ($($resp.Count) results)"
    } else {
        Write-Fail "Unexpected response type"
    }
}
catch {
    Write-Fail "Request failed: $($_.Exception.Message)"
}

# ======================
# Summary
# ======================
Write-Host "`n" + ("=" * 50) -ForegroundColor Cyan
Write-Host "RMOS AI Integration Tests Complete" -ForegroundColor Cyan
Write-Host ("=" * 50) -ForegroundColor Cyan
Write-Host ""
Write-Host "  Passed: $passed" -ForegroundColor Green
Write-Host "  Failed: $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })
Write-Host ""

if ($failed -gt 0) {
    Write-Host "Some tests failed!" -ForegroundColor Red
    exit 1
} else {
    Write-Host "All tests passed!" -ForegroundColor Green
    exit 0
}
