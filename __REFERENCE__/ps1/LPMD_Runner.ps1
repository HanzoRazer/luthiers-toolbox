/LPMD_Runner.ps1
# LPMD_Runner.ps1
Param(
    [string]$RootDir = "."
)

Write-Host "=== LPMD Runner: Legacy Pipeline Inventory ==="
Write-Host "RootDir: $RootDir"
Write-Host ""

$serverPipelines = Join-Path $RootDir "server\pipelines"
$apiRoot         = Join-Path $RootDir "services\api\app"

if (-not (Test-Path $serverPipelines)) {
    Write-Host "ERROR: $serverPipelines not found. Are you in the repo root?"
    exit 1
}
if (-not (Test-Path $apiRoot)) {
    Write-Host "ERROR: $apiRoot not found. Are you in the repo root?"
    exit 1
}

# -----------------------------------------------------------------------------
# 1) Python module inventory
# -----------------------------------------------------------------------------
Write-Host "Scanning Python modules in server/pipelines..."
$pythonReportPath = Join-Path $RootDir "lpmd_python_inventory.txt"

Get-ChildItem -Path $serverPipelines -Recurse -Filter "*.py" | ForEach-Object {
    $fullPath = $_.FullName
    $name = $_.Name  # filename with extension

    $relativePath = $fullPath.Substring($serverPipelines.Length).TrimStart('\','/')
    $apiMatches = Get-ChildItem -Path $apiRoot -Recurse -Filter $name -ErrorAction SilentlyContinue

    if (-not $apiMatches) {
        "MISSING IN services/api/app: $relativePath" | Out-File -FilePath $pythonReportPath -Append -Encoding UTF8
    }
    else {
        "EXISTS: $relativePath" | Out-File -FilePath $pythonReportPath -Append -Encoding UTF8
    }
}

Write-Host "Python inventory written to $pythonReportPath"

# -----------------------------------------------------------------------------
# 2) Data file inventory (json, csv, yaml/yml)
# -----------------------------------------------------------------------------
Write-Host "Scanning data files in server/pipelines..."
$dataReportPath = Join-Path $RootDir "lpmd_data_inventory.txt"

Get-ChildItem -Path $serverPipelines -Recurse -Include *.json,*.csv,*.yml,*.yaml -File |
    ForEach-Object {
        $fullPath = $_.FullName
        $name = $_.Name
        $relativePath = $fullPath.Substring($serverPipelines.Length).TrimStart('\','/')

        $apiMatches = Get-ChildItem -Path $apiRoot -Recurse -Filter $name -ErrorAction SilentlyContinue

        if (-not $apiMatches) {
            "MISSING DATA IN services/api/app: $relativePath" | Out-File -FilePath $dataReportPath -Append -Encoding UTF8
        }
        else {
            "DATA EXISTS: $relativePath" | Out-File -FilePath $dataReportPath -Append -Encoding UTF8
        }
    }

Write-Host "Data inventory written to $dataReportPath"

Write-Host ""
Write-Host "=== LPMD Runner complete ==="
Write-Host "Review:"
Write-Host "  - $pythonReportPath"
Write-Host "  - $dataReportPath"
