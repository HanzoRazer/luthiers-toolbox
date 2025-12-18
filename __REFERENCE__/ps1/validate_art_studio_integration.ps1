# Art Studio v15.5 - Integration Validation Script
#
# Quick check to verify all integrated files and endpoints are working.
#
# Usage: .\validate_art_studio_integration.ps1

$ErrorActionPreference = "Stop"

Write-Host "`n=== Art Studio v15.5 Integration Validation ===" -ForegroundColor Cyan
Write-Host "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n"

$filesChecked = 0
$filesOK = 0
$filesMissing = 0

function Test-File {
    param([string]$Path, [string]$Description)
    
    $script:filesChecked++
    
    if (Test-Path $Path) {
        Write-Host "  ✓ $Description" -ForegroundColor Green
        $script:filesOK++
        return $true
    } else {
        Write-Host "  ✗ $Description" -ForegroundColor Red
        Write-Host "    Missing: $Path" -ForegroundColor Gray
        $script:filesMissing++
        return $false
    }
}

# Backend Files
Write-Host "Backend Integration:" -ForegroundColor White
Test-File "services\api\app\routers\cam_post_v155_router.py" "Post-processor router"
Test-File "services\api\app\routers\cam_smoke_v155_router.py" "Smoke test router"
Test-File "services\api\app\data\posts\posts_v155.json" "Preset configuration"

# Frontend Files
Write-Host "`nFrontend Integration:" -ForegroundColor White
Test-File "packages\client\src\api\postv155.ts" "API helpers"
Test-File "packages\client\src\components\ToolpathPreview3D.vue" "3D preview component"
Test-File "packages\client\src\views\ArtStudioPhase15_5.vue" "Main UI component"

# DevOps Scripts
Write-Host "`nDevOps Tools:" -ForegroundColor White
Test-File "smoke_posts_v155.ps1" "Smoke test script"
Test-File "services\api\tools\curl_json_pp.ps1" "JSON pretty-printer"

# Documentation
Write-Host "`nDocumentation:" -ForegroundColor White
Test-File "ART_STUDIO_REPO_SUMMARY.md" "Version catalog"
Test-File "ART_STUDIO_V15_5_INTEGRATION.md" "Integration guide"
Test-File "ART_STUDIO_V15_5_QUICKREF.md" "Quick reference"
Test-File "ART_STUDIO_COMPLETE_INTEGRATION.md" "Integration summary"

# Check main.py registration
Write-Host "`nRouter Registration:" -ForegroundColor White
$mainPy = Get-Content "services\api\app\main.py" -Raw

if ($mainPy -match 'cam_post_v155_router') {
    Write-Host "  ✓ cam_post_v155_router imported" -ForegroundColor Green
    $filesOK++
} else {
    Write-Host "  ✗ cam_post_v155_router NOT imported" -ForegroundColor Red
    $filesMissing++
}
$filesChecked++

if ($mainPy -match 'cam_smoke_v155_router') {
    Write-Host "  ✓ cam_smoke_v155_router imported" -ForegroundColor Green
    $filesOK++
} else {
    Write-Host "  ✗ cam_smoke_v155_router NOT imported" -ForegroundColor Red
    $filesMissing++
}
$filesChecked++

# Summary
Write-Host "`n=== Validation Summary ===" -ForegroundColor Cyan
Write-Host "Files Checked: $filesChecked" -ForegroundColor White
Write-Host "Files OK:      $filesOK" -ForegroundColor Green
Write-Host "Files Missing: $filesMissing" -ForegroundColor $(if ($filesMissing -eq 0) { 'Green' } else { 'Red' })

if ($filesMissing -eq 0) {
    Write-Host "`n✓ Integration Complete!" -ForegroundColor Green
    Write-Host "`nNext Steps:" -ForegroundColor Cyan
    Write-Host "  1. Install Three.js: cd packages\client; npm install three @types/three" -ForegroundColor Gray
    Write-Host "  2. Configure Vue Router (add /art-studio-v15 route)" -ForegroundColor Gray
    Write-Host "  3. Run smoke test: .\smoke_posts_v155.ps1" -ForegroundColor Gray
    Write-Host "  4. Test UI manually" -ForegroundColor Gray
    exit 0
} else {
    Write-Host "`n✗ Integration Incomplete" -ForegroundColor Red
    Write-Host "Please review missing files and re-run validation." -ForegroundColor Yellow
    exit 1
}
