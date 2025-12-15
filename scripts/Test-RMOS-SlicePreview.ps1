param(
    [string]$BaseUrl = "http://localhost:8000/rmos",
    [switch]$Verbose
)

Write-Host "=== RMOS SINGLE-SLICE PREVIEW TEST ==="
Write-Host "Base URL:" $BaseUrl
Write-Host ""

function Write-Info($msg) { Write-Host "[INFO]" $msg }
function Write-Ok($msg)  { Write-Host "[ OK ]" $msg -ForegroundColor Green }
function Write-Err($msg) { Write-Host "[ERR]" $msg -ForegroundColor Red }

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

# ----------------------------------------------------------------------
# 1) SIMPLE CIRCLE SLICE PREVIEW
# ----------------------------------------------------------------------

Write-Info "Testing circle slice preview..."

$circleOp = @{
    id = "slice_circle_test_$(Get-Random)"
    op_type = "saw_slice"
    tool_id = "saw_default"
    geometry_source = "circle_param"

    # Circle geometry
    circle = @{
        center_x_mm = 0
        center_y_mm = 0
        radius_mm   = 50
    }
    line = $null
    dxf_path = $null

    slice_thickness_mm = 1.0
    passes = 1
    material = "hardwood"
    workholding = "vacuum"

    risk_options = @{
        allow_aggressive = $false
        machine_gantry_span_mm = 1200
    }
}

$circleResult = Invoke-RmosJson -Path "/saw-ops/slice/preview" -Method "POST" -Body $circleOp

Write-Ok "Circle preview OK"
Write-Host "  Risk grade:" $circleResult.risk.risk_grade
Write-Host "  Rim speed: " $circleResult.risk.rim_speed_m_min
Write-Host ""

# ----------------------------------------------------------------------
# 2) SIMPLE LINE SLICE PREVIEW
# ----------------------------------------------------------------------

Write-Info "Testing line slice preview..."

$lineOp = @{
    id = "slice_line_test_$(Get-Random)"
    op_type = "saw_slice"
    tool_id = "saw_default"
    geometry_source = "line_param"

    # Line geometry
    line = @{
        x1_mm = 0
        y1_mm = 0
        x2_mm = 100
        y2_mm = 0
    }
    circle = $null
    dxf_path = $null

    slice_thickness_mm = 1.0
    passes = 1
    material = "hardwood"
    workholding = "vacuum"

    risk_options = @{
        allow_aggressive = $false
        machine_gantry_span_mm = 1200
    }
}

$lineResult = Invoke-RmosJson -Path "/saw-ops/slice/preview" -Method "POST" -Body $lineOp

Write-Ok "Line preview OK"
Write-Host "  Risk grade:" $lineResult.risk.risk_grade
Write-Host "  Rim speed: " $lineResult.risk.rim_speed_m_min
Write-Host ""

# ----------------------------------------------------------------------
Write-Ok "Single-slice preview smoke test completed successfully!"
