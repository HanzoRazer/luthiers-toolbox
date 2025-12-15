# CAM Settings Roundtrip Smoke Test
# Tests export → import → import with overwrite

param(
  [string]$BaseUrl = "http://localhost:8000"
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CAM Settings Roundtrip Smoke Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$temp = New-TemporaryFile

try {
  # Test 1: Export settings
  Write-Host "[1/4] Exporting CAM settings..." -ForegroundColor Yellow
  $export = Invoke-WebRequest -Uri "$BaseUrl/api/cam/settings/export" -UseBasicParsing
  if ($export.StatusCode -ne 200) {
    throw "Export failed with status $($export.StatusCode)"
  }
  $export.Content | Out-File -FilePath $temp -Encoding utf8
  $exportData = $export.Content | ConvertFrom-Json
  Write-Host "      ✓ Exported: $($exportData.machines.Length) machines, $($exportData.posts.Length) posts, $($exportData.pipeline_presets.Length) presets" -ForegroundColor Green
  Write-Host ""

  # Test 2: Import without overwrite (should skip existing)
  Write-Host "[2/4] Importing with overwrite=false..." -ForegroundColor Yellow
  $resp1 = Invoke-WebRequest -Uri "$BaseUrl/api/cam/settings/import?overwrite=false" `
    -Method POST `
    -ContentType "application/json" `
    -Body (Get-Content $temp -Raw) `
    -UseBasicParsing
  
  $result1 = $resp1.Content | ConvertFrom-Json
  Write-Host "      Imported: machines=$($result1.imported.machines), posts=$($result1.imported.posts), presets=$($result1.imported.pipeline_presets)" -ForegroundColor Gray
  Write-Host "      Skipped:  machines=$($result1.skipped.machines), posts=$($result1.skipped.posts), presets=$($result1.skipped.pipeline_presets)" -ForegroundColor Gray
  if ($result1.errors.Length -gt 0) {
    Write-Host "      Errors: $($result1.errors.Length)" -ForegroundColor Red
    $result1.errors | ForEach-Object { Write-Host "        - $($_.kind) '$($_.id)': $($_.error)" -ForegroundColor Red }
  }
  Write-Host "      ✓ Import without overwrite completed" -ForegroundColor Green
  Write-Host ""

  # Test 3: Import with overwrite (should replace existing)
  Write-Host "[3/4] Importing with overwrite=true..." -ForegroundColor Yellow
  $resp2 = Invoke-WebRequest -Uri "$BaseUrl/api/cam/settings/import?overwrite=true" `
    -Method POST `
    -ContentType "application/json" `
    -Body (Get-Content $temp -Raw) `
    -UseBasicParsing
  
  $result2 = $resp2.Content | ConvertFrom-Json
  Write-Host "      Imported: machines=$($result2.imported.machines), posts=$($result2.imported.posts), presets=$($result2.imported.pipeline_presets)" -ForegroundColor Gray
  Write-Host "      Skipped:  machines=$($result2.skipped.machines), posts=$($result2.skipped.posts), presets=$($result2.skipped.pipeline_presets)" -ForegroundColor Gray
  if ($result2.errors.Length -gt 0) {
    Write-Host "      Errors: $($result2.errors.Length)" -ForegroundColor Red
    $result2.errors | ForEach-Object { Write-Host "        - $($_.kind) '$($_.id)': $($_.error)" -ForegroundColor Red }
  }
  Write-Host "      ✓ Import with overwrite completed" -ForegroundColor Green
  Write-Host ""

  # Test 4: Verify summary endpoint
  Write-Host "[4/4] Verifying summary endpoint..." -ForegroundColor Yellow
  $summary = Invoke-WebRequest -Uri "$BaseUrl/api/cam/settings/summary" -UseBasicParsing
  $summaryData = $summary.Content | ConvertFrom-Json
  Write-Host "      Current counts: machines=$($summaryData.machines_count), posts=$($summaryData.posts_count), presets=$($summaryData.pipeline_presets_count)" -ForegroundColor Gray
  Write-Host "      ✓ Summary endpoint working" -ForegroundColor Green
  Write-Host ""

  Write-Host "========================================" -ForegroundColor Green
  Write-Host "All tests PASSED ✓" -ForegroundColor Green
  Write-Host "========================================" -ForegroundColor Green
  
} catch {
  Write-Host ""
  Write-Host "========================================" -ForegroundColor Red
  Write-Host "Test FAILED: $($_.Exception.Message)" -ForegroundColor Red
  Write-Host "========================================" -ForegroundColor Red
  exit 1
  
} finally {
  if (Test-Path $temp) {
    Remove-Item -Force $temp | Out-Null
  }
}
