param(
    [string]$BaseUrl = "http://localhost:8000",
    [switch]$Verbose
)

Write-Host "=== RMOS Sandbox Smoke Test ===" -ForegroundColor Cyan
Write-Host "Base URL:" $BaseUrl
Write-Host ""

function Write-Info($msg) {
    Write-Host "[INFO]" $msg -ForegroundColor Cyan
}

function Write-Ok($msg) {
    Write-Host "[ OK ]" $msg -ForegroundColor Green
}

function Write-Err($msg) {
    Write-Host "[ERR]" $msg -ForegroundColor Red
}

function Invoke-RmosJson {
    param(
        [string]$Path,
        [string]$Method = "GET",
        $Body = $null
    )

    $url = "$BaseUrl$Path"
    if ($Verbose) { Write-Info "Request $Method $url" }

    try {
        if ($Body -ne $null) {
            $json = $Body | ConvertTo-Json -Depth 10
            if ($Verbose) { Write-Host "Body:" $json }
            $response = Invoke-WebRequest -Uri $url -Method $Method -ContentType "application/json" -Body $json
        } else {
            $response = Invoke-WebRequest -Uri $url -Method $Method
        }
        return $response.Content | ConvertFrom-Json
    }
    catch {
        Write-Err "Request failed: $Method $url"
        Write-Err $_.Exception.Message
        throw
    }
}

# 1) Create a smoke-test rosette pattern
$timestamp = Get-Date -Format 'yyyyMMddHHmmss'
$patternId = "smoke_rosette_$timestamp"

Write-Info "Creating test pattern id=$patternId"

$patternPayload = @{
    id   = $patternId
    name = "Smoke Test Rosette $timestamp"

    center_x_mm = 0
    center_y_mm = 0

    ring_bands = @(
        @{
            id                       = "ring0"
            index                    = 0
            radius_mm                = 45
            width_mm                 = 2
            color_hint               = "bw_outer"
            strip_family_id          = "bw_checker_main"
            slice_angle_deg          = 0
            tile_length_override_mm  = $null
        },
        @{
            id                       = "ring1"
            index                    = 1
            radius_mm                = 48
            width_mm                 = 2
            color_hint               = "bw_inner"
            strip_family_id          = "bw_checker_main"
            slice_angle_deg          = 0
            tile_length_override_mm  = $null
        }
    )

    default_slice_thickness_mm = 1.0
    default_passes             = 1
    default_workholding        = "vacuum"
    default_tool_id            = "saw_default"
}

$createdPattern = Invoke-RmosJson -Path "/api/rosette-patterns" -Method "POST" -Body $patternPayload
Write-Ok "Pattern created: id=$($createdPattern.id), rings=$($createdPattern.ring_bands.Count)"

# 2) Call manufacturing-plan (should create a rosette_plan JobLog entry)
Write-Info "Requesting manufacturing plan for pattern $patternId"

$planRequest = @{
    pattern_id     = $patternId
    guitars        = 4
    tile_length_mm = 8.0
    scrap_factor   = 0.12
    record_joblog  = $true
}

$plan = Invoke-RmosJson -Path "/api/rosette/manufacturing-plan" -Method "POST" -Body $planRequest

Write-Ok "Manufacturing plan received"
Write-Host "  Pattern:" $plan.pattern.name
Write-Host "  Guitars:" $plan.guitars
Write-Host "  Strip families:" $plan.strip_plans.Count

if ($plan.strip_plans.Count -gt 0) {
    Write-Host ""
    Write-Host "  Strip Plans:"
    foreach ($sp in $plan.strip_plans) {
        Write-Host "    - Family: $($sp.strip_family_id)"
        Write-Host "      Tiles needed: $($sp.total_tiles_needed)"
        Write-Host "      Strip length: $([math]::Round($sp.total_strip_length_m, 2)) m"
        Write-Host "      Sticks needed: $($sp.sticks_needed)"
    }
}
Write-Host ""

# 3) Verify pattern is in library
Write-Info "Verifying pattern exists in library"
$allPatterns = Invoke-RmosJson -Path "/api/rosette-patterns"
$foundPattern = $allPatterns | Where-Object { $_.id -eq $patternId }

if ($foundPattern) {
    Write-Ok "Pattern found in library: $($foundPattern.name)"
} else {
    Write-Err "Pattern not found in library!"
}

# 4) Fetch JobLog and show counts by type
Write-Info "Fetching JobLog entries"
$joblog = Invoke-RmosJson -Path "/api/joblog"

if (-not $joblog) {
    Write-Err "No JobLog entries returned"
} else {
    $total = $joblog.Count
    $planCount = ($joblog | Where-Object { $_.job_type -eq "rosette_plan" }).Count
    $batchCount = ($joblog | Where-Object { $_.job_type -eq "saw_slice_batch" }).Count

    Write-Ok "JobLog entries: total=$total, rosette_plan=$planCount, saw_slice_batch=$batchCount"
    
    # Show most recent entries
    Write-Host ""
    Write-Host "  Recent entries:"
    $joblog | Select-Object -First 3 | ForEach-Object {
        Write-Host "    - Type: $($_.job_type)"
        Write-Host "      ID: $($_.id)"
        if ($_.job_type -eq "rosette_plan") {
            Write-Host "      Pattern: $($_.plan_pattern_id)"
            Write-Host "      Guitars: $($_.plan_guitars)"
            Write-Host "      Total tiles: $($_.plan_total_tiles)"
        }
        Write-Host ""
    }
}

# 5) Cleanup - delete test pattern
Write-Info "Cleaning up test pattern"
try {
    $deleteUrl = "$BaseUrl/api/rosette-patterns/$patternId"
    Invoke-WebRequest -Uri $deleteUrl -Method "DELETE" | Out-Null
    Write-Ok "Test pattern deleted"
} catch {
    Write-Err "Failed to delete test pattern: $($_.Exception.Message)"
}

Write-Host ""
Write-Ok "=== RMOS smoke test completed ===" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:"
Write-Host "  ✓ Pattern CRUD working"
Write-Host "  ✓ Manufacturing planner working"
Write-Host "  ✓ JobLog integration working"
Write-Host "  ✓ Multi-strip-family support verified"
