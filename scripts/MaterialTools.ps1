<#
.SYNOPSIS
  PowerShell helper to convert Saw Lab materials CSV <-> JSON and validate round-trips.

.DESCRIPTION
  Provides three commands:
      materials-json          : Convert CSV → JSON
      materials-csv           : Convert JSON → CSV
      materials-roundtrip-test: CSV → JSON → CSV and compare

.EXAMPLE
  ./MaterialTools.ps1 materials-json

.EXAMPLE
  ./MaterialTools.ps1 materials-csv

.EXAMPLE
  ./MaterialTools.ps1 materials-roundtrip-test
#>

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("materials-json", "materials-csv", "materials-roundtrip-test")]
    [string]$Command
)

# --- Configure input / output paths ----
$csvPath  = "tests/data/saw_lab_materials.csv"
$jsonPath = "tests/data/saw_lab_materials.json"

# Temp files for roundtrip validation
$tempJsonPath = "tests/data/_materials_roundtrip.json"
$tempCsvPath  = "tests/data/_materials_roundtrip.csv"

$convertCsvToJson = {
    Write-Host ">>> Converting CSV → JSON"
    if (-not (Test-Path $csvPath)) {
        Write-Host "ERROR: CSV file not found: $csvPath" -ForegroundColor Red
        exit 1
    }

    python scripts/materials_csv_to_json.py $csvPath $jsonPath
    if ($LASTEXITCODE -eq 0) {
        Write-Host "SUCCESS: Wrote JSON to $jsonPath" -ForegroundColor Green
    } else {
        Write-Host "Failed to convert CSV to JSON." -ForegroundColor Red
        exit 1
    }
}

$convertJsonToCsv = {
    Write-Host ">>> Converting JSON → CSV"
    if (-not (Test-Path $jsonPath)) {
        Write-Host "ERROR: JSON file not found: $jsonPath" -ForegroundColor Red
        exit 1
    }

    python scripts/materials_json_to_csv.py $jsonPath $csvPath
    if ($LASTEXITCODE -eq 0) {
        Write-Host "SUCCESS: Wrote CSV to $csvPath" -ForegroundColor Green
    } else {
        Write-Host "Failed to convert JSON to CSV." -ForegroundColor Red
        exit 1
    }
}

$roundtripTest = {
    Write-Host ">>> Round-trip test: CSV → JSON → CSV"

    if (-not (Test-Path $csvPath)) {
        Write-Host "ERROR: CSV file not found: $csvPath" -ForegroundColor Red
        exit 1
    }

    # Step 1: CSV → temp JSON
    Write-Host "Step 1/3: CSV → temp JSON"
    python scripts/materials_csv_to_json.py $csvPath $tempJsonPath
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: CSV → JSON step failed." -ForegroundColor Red
        exit 1
    }

    # Step 2: temp JSON → temp CSV
    Write-Host "Step 2/3: temp JSON → temp CSV"
    python scripts/materials_json_to_csv.py $tempJsonPath $tempCsvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: JSON → CSV step failed." -ForegroundColor Red
        exit 1
    }

    # Step 3: Compare original CSV vs round-tripped CSV
    Write-Host "Step 3/3: Comparing original CSV vs roundtrip CSV"
    $origLines = Get-Content $csvPath | Where-Object { $_.Trim().Length -gt 0 }
    $roundLines = Get-Content $tempCsvPath | Where-Object { $_.Trim().Length -gt 0 }

    $origText = ($origLines -join "`n").Trim()
    $roundText = ($roundLines -join "`n").Trim()

    if ($origText -eq $roundText) {
        Write-Host "ROUNDTRIP OK: CSV → JSON → CSV is stable." -ForegroundColor Green
    } else {
        Write-Host "ROUNDTRIP MISMATCH:" -ForegroundColor Yellow
        Write-Host "The round-tripped CSV differs from the original." -ForegroundColor Yellow
        Write-Host "You may want to inspect:" -ForegroundColor Yellow
        Write-Host "  Original:   $csvPath" -ForegroundColor Yellow
        Write-Host "  Roundtrip:  $tempCsvPath" -ForegroundColor Yellow
        # Non-zero exit so CI can fail on mismatch
        exit 1
    }

    # Cleanup temp files (optional; comment out if you want to inspect them)
    if (Test-Path $tempJsonPath) {
        Remove-Item $tempJsonPath -Force
    }
    if (Test-Path $tempCsvPath) {
        Remove-Item $tempCsvPath -Force
    }
}

switch ($Command) {

    "materials-json" {
        & $convertCsvToJson
    }

    "materials-csv" {
        & $convertJsonToCsv
    }

    "materials-roundtrip-test" {
        & $roundtripTest
    }
}

Write-Host "Done."
