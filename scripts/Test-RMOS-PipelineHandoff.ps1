param(
    [string]$BaseUrl = "http://localhost:8000/rmos",
    [switch]$Verbose
)

Write-Host "=== RMOS PIPELINE HANDOFF TEST ==="
Write-Host "Base URL:" $BaseUrl
Write-Host ""

function Invoke-RmosJson {
    param(
        [string]$Path,
        [string]$Method = "POST",
        $Body = $null
    )
    $url = "$BaseUrl$Path"
    if ($Verbose) { Write-Host "[INFO] $Method $url" }
    $json = $Body | ConvertTo-Json -Depth 10
    $response = Invoke-WebRequest -Uri $url -Method $Method -ContentType "application/json" -Body $json
    return $response.Content | ConvertFrom-Json
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$patternId = "ci_pattern_$timestamp"

$batchOp = @{
    id = "ci_batch_$timestamp"
    op_type = "saw_slice_batch"
    tool_id = "saw_default"
    geometry_source = "circle_param"
    base_circle = @{ center_x_mm = 0; center_y_mm = 0; radius_mm = 45 }
    num_rings = 2
    radial_step_mm = 3
    radial_sign = 1
    slice_thickness_mm = 1.0
    passes = 1
    material = "hardwood"
    workholding = "vacuum"
}

$handoffRequest = @{
    pattern_id = $patternId
    batch_op = $batchOp
    manufacturing_plan = $null
    lane = "rosette"
    machine_profile = "default_saw_rig"
    priority = "normal"
    notes = "CI handoff smoke test"
}

$result = Invoke-RmosJson -Path "/pipeline/handoff" -Method "POST" -Body $handoffRequest

Write-Host "Success:" $result.success
Write-Host "Mode:   " $result.handoff_mode
Write-Host "Job id: " $result.job_id
Write-Host "Message:" $result.message
if ($result.payload_path) {
    Write-Host "Path:   " $result.payload_path
}

Write-Host "[ OK ] Pipeline handoff smoke test complete."
