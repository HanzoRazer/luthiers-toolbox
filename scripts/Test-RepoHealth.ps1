param(
    [string]$BaseUrl = "http://localhost:8000",
    [switch]$IncludeDiagnostics
)

function Write-Info($msg) { Write-Host $msg -ForegroundColor Cyan }
function Write-Success($msg) { Write-Host $msg -ForegroundColor Green }
function Write-ErrorMsg($msg) { Write-Host $msg -ForegroundColor Red }

Write-Info "=== Repo Health Smoke Test ==="
if ($IncludeDiagnostics) {
    $healthUri = "$BaseUrl/health?include_diagnostics=true"
} else {
    $healthUri = "$BaseUrl/health"
}

Write-Info "Target: $healthUri"

try {
    $response = Invoke-RestMethod -Uri $healthUri -Method GET -TimeoutSec 10
} catch {
    Write-ErrorMsg "Request failed: $_"
    exit 1
}

if (-not $response.status) {
    Write-ErrorMsg "Response did not contain a status field."
    exit 1
}

Write-Info "Status: $($response.status)"
Write-Info "Timestamp: $($response.timestamp)"

if ($response.status -ne "ok") {
    Write-ErrorMsg "Reported status is $($response.status)."
    exit 1
}

$pathFailures = @()
foreach ($property in $response.paths.PSObject.Properties) {
    if (-not $property.Value) {
        $pathFailures += $property.Name
    }
}

if ($pathFailures.Count -gt 0) {
    Write-ErrorMsg "Missing critical paths: $($pathFailures -join ', ')"
    exit 1
}

if ($IncludeDiagnostics) {
    if (-not $response.diagnostics) {
        Write-ErrorMsg "Diagnostics missing despite IncludeDiagnostics flag."
        exit 1
    }

    $dependencies = $response.diagnostics.dependencies
    if (-not $dependencies) {
        Write-ErrorMsg "Dependency versions section missing."
        exit 1
    }

    foreach ($prop in $dependencies.PSObject.Properties) {
        if (-not $prop.Value) {
            Write-ErrorMsg "Dependency $($prop.Name) does not report a version."
            exit 1
        }
    }

    foreach ($component in @("queue", "cache")) {
        $componentStatus = $response.diagnostics.$component
        if (-not $componentStatus) {
            Write-ErrorMsg "Diagnostics missing $component status."
            exit 1
        }
        if (-not $componentStatus.status) {
            Write-ErrorMsg "$component status does not include a status field."
            exit 1
        }
    }
}

Write-Success "Repo health check passed."
exit 0
