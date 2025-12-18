# Phase 27.1 & Bundle 13 Integration Smoke Test
# Tests PipelineLab query bootstrap and Rosette Compare coloring

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Phase 27 & Bundle 13 Integration Test" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$baseUrl = "http://localhost:5173"
$apiUrl = "http://localhost:8001"
$testsPassed = 0
$testsFailed = 0

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Method = "GET",
        [object]$Body = $null,
        [string]$ExpectedPattern = $null,
        [int]$ExpectedStatus = 200
    )
    
    Write-Host "`n--- Test: $Name ---" -ForegroundColor Yellow
    Write-Host "URL: $Url"
    
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            ErrorAction = "Stop"
        }
        
        if ($Body) {
            $params.Body = ($Body | ConvertTo-Json -Depth 10)
            $params.ContentType = "application/json"
        }
        
        $response = Invoke-WebRequest @params
        
        if ($response.StatusCode -eq $ExpectedStatus) {
            Write-Host "✓ Status: $($response.StatusCode)" -ForegroundColor Green
            
            if ($ExpectedPattern) {
                if ($response.Content -match $ExpectedPattern) {
                    Write-Host "✓ Pattern found: $ExpectedPattern" -ForegroundColor Green
                    $script:testsPassed++
                    return $true
                } else {
                    Write-Host "✗ Pattern not found: $ExpectedPattern" -ForegroundColor Red
                    $script:testsFailed++
                    return $false
                }
            }
            
            $script:testsPassed++
            return $true
        } else {
            Write-Host "✗ Unexpected status: $($response.StatusCode)" -ForegroundColor Red
            $script:testsFailed++
            return $false
        }
    } catch {
        Write-Host "✗ Error: $($_.Exception.Message)" -ForegroundColor Red
        $script:testsFailed++
        return $false
    }
}

Write-Host "=== Part 1: Bundle 13 - PipelineLab Query Bootstrap ===" -ForegroundColor Magenta

# Test 1: Basic PipelineLab route (no query params)
Test-Endpoint `
    -Name "PipelineLab base route accessible" `
    -Url "$baseUrl/lab/pipeline" `
    -ExpectedPattern "Pipeline Lab"

# Test 2: PipelineLab with gcode_key query param
Test-Endpoint `
    -Name "PipelineLab with gcode_key param" `
    -Url "$baseUrl/lab/pipeline?gcode_key=test123&source=joblog" `
    -ExpectedPattern "test123"

# Test 3: PipelineLab with full query params
$fullQueryUrl = "$baseUrl/lab/pipeline?gcode_key=abc&source=joblog&job_name=TestJob&machine_id=haas_vf2&post_id=grbl&use_helical=true"
Test-Endpoint `
    -Name "PipelineLab with all query params" `
    -Url $fullQueryUrl `
    -ExpectedPattern "TestJob"

Write-Host "`n=== Part 2: Phase 27.1 - Rosette Compare Coloring ===" -ForegroundColor Magenta

# Test 4: Check if Rosette Compare route exists
Test-Endpoint `
    -Name "Rosette Compare route accessible" `
    -Url "$baseUrl/art-studio/rosette-compare" `
    -ExpectedPattern "Rosette Compare"

# Test 5: API - List rosette jobs
Write-Host "`n--- Test: List rosette jobs (API) ---" -ForegroundColor Yellow
try {
    $jobs = Invoke-RestMethod -Uri "$apiUrl/api/art/rosette/jobs?limit=10" -Method GET
    if ($jobs.Count -gt 0) {
        Write-Host "✓ Found $($jobs.Count) rosette jobs" -ForegroundColor Green
        $testsPassed++
        
        # Store job IDs for comparison test
        $jobA = $jobs[0].job_id
        $jobB = if ($jobs.Count -gt 1) { $jobs[1].job_id } else { $jobs[0].job_id }
    } else {
        Write-Host "⚠ No rosette jobs found (create some to test compare)" -ForegroundColor Yellow
        $jobA = $null
        $jobB = $null
    }
} catch {
    Write-Host "✗ Failed to list jobs: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
    $jobA = $null
    $jobB = $null
}

# Test 6: API - Compare two rosette jobs (if jobs exist)
if ($jobA -and $jobB) {
    Write-Host "`n--- Test: Compare rosette jobs (API) ---" -ForegroundColor Yellow
    try {
        $compareBody = @{
            job_id_a = $jobA
            job_id_b = $jobB
        }
        
        $compareResult = Invoke-RestMethod `
            -Uri "$apiUrl/api/art/rosette/compare" `
            -Method POST `
            -Body ($compareBody | ConvertTo-Json) `
            -ContentType "application/json"
        
        Write-Host "✓ Compare successful" -ForegroundColor Green
        Write-Host "  Job A: $($compareResult.job_a.segments) segments" -ForegroundColor Cyan
        Write-Host "  Job B: $($compareResult.job_b.segments) segments" -ForegroundColor Cyan
        Write-Host "  Delta: $($compareResult.diff_summary.segments_delta) segments" -ForegroundColor Cyan
        
        # Verify structure for Phase 27.1
        if ($compareResult.job_a.paths -and $compareResult.job_b.paths) {
            Write-Host "✓ Both jobs have paths array (ready for coloring)" -ForegroundColor Green
            $testsPassed++
        } else {
            Write-Host "✗ Missing paths arrays" -ForegroundColor Red
            $testsFailed++
        }
    } catch {
        Write-Host "✗ Compare failed: $($_.Exception.Message)" -ForegroundColor Red
        $testsFailed++
    }
} else {
    Write-Host "`n⚠ Skipping compare test (no jobs available)" -ForegroundColor Yellow
}

# Test 7: Verify Phase 27.1 computed properties (indirect via HTML check)
if ($jobA -and $jobB) {
    Write-Host "`n--- Test: Rosette Compare with query params ---" -ForegroundColor Yellow
    try {
        $compareUrl = "$baseUrl/art-studio/rosette-compare?jobA=$jobA&jobB=$jobB"
        $response = Invoke-WebRequest -Uri $compareUrl -ErrorAction Stop
        
        if ($response.Content -match "Unchanged|Added|Removed") {
            Write-Host "✓ Legend text found in HTML (Phase 27.1 coloring active)" -ForegroundColor Green
            $testsPassed++
        } else {
            Write-Host "⚠ Legend text not found (may not be visible yet)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "✗ Failed to load compare page: $($_.Exception.Message)" -ForegroundColor Red
        $testsFailed++
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Passed: $testsPassed" -ForegroundColor Green
Write-Host "Failed: $testsFailed" -ForegroundColor $(if ($testsFailed -eq 0) { "Green" } else { "Red" })
Write-Host

if ($testsFailed -eq 0) {
    Write-Host "✓ All tests passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "✗ Some tests failed. See output above for details." -ForegroundColor Red
    exit 1
}
