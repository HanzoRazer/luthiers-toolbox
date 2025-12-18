#!/usr/bin/env pwsh
# Patch W: Design → CAM Workflow Integration Script
# Automates setup of geometry store and toolbar

$ErrorActionPreference = 'Stop'

Write-Host "`n=== Patch W: Design → CAM Workflow Integration ===" -ForegroundColor Cyan

# Step 1: Install Pinia
Write-Host "`n[1/5] Installing Pinia..." -ForegroundColor Yellow
Set-Location "packages\client"
try {
    npm install pinia
    Write-Host "  ✓ Pinia installed" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Pinia installation failed: $_" -ForegroundColor Red
    exit 1
}

# Step 2: Check if main.ts needs Pinia registration
Write-Host "`n[2/5] Checking main.ts for Pinia registration..." -ForegroundColor Yellow
$mainTsPath = "src\main.ts"
if (Test-Path $mainTsPath) {
    $mainTsContent = Get-Content $mainTsPath -Raw
    
    if ($mainTsContent -match "createPinia") {
        Write-Host "  ✓ Pinia already registered in main.ts" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Pinia not registered - manual update required" -ForegroundColor Yellow
        Write-Host "    Add to main.ts:" -ForegroundColor Gray
        Write-Host "      import { createPinia } from 'pinia'" -ForegroundColor Gray
        Write-Host "      const pinia = createPinia()" -ForegroundColor Gray
        Write-Host "      app.use(pinia)" -ForegroundColor Gray
    }
} else {
    Write-Host "  ⚠ main.ts not found at expected path" -ForegroundColor Yellow
}

# Step 3: Check if GeometryToolbar needs to be added to App.vue
Write-Host "`n[3/5] Checking App.vue for GeometryToolbar..." -ForegroundColor Yellow
Set-Location "..\..\"  # Back to root
$appVuePath = "client\src\App.vue"
if (Test-Path $appVuePath) {
    $appVueContent = Get-Content $appVuePath -Raw
    
    if ($appVueContent -match "GeometryToolbar") {
        Write-Host "  ✓ GeometryToolbar already in App.vue" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ GeometryToolbar not in App.vue - manual update required" -ForegroundColor Yellow
        Write-Host "    Add import:" -ForegroundColor Gray
        Write-Host "      import GeometryToolbar from '../packages/client/src/components/GeometryToolbar.vue'" -ForegroundColor Gray
        Write-Host "    Add to template:" -ForegroundColor Gray
        Write-Host "      <GeometryToolbar />" -ForegroundColor Gray
    }
} else {
    Write-Host "  ⚠ App.vue not found at expected path" -ForegroundColor Yellow
}

# Step 4: Verify created files exist
Write-Host "`n[4/5] Verifying Patch W files..." -ForegroundColor Yellow
$patchFiles = @(
    "packages\client\src\stores\geometry.ts",
    "packages\client\src\components\GeometryToolbar.vue",
    "packages\client\src\composables\useCAMIntegration.ts",
    "PATCH_W_DESIGN_CAM_WORKFLOW.md"
)

$allFilesExist = $true
foreach ($file in $patchFiles) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Missing: $file" -ForegroundColor Red
        $allFilesExist = $false
    }
}

if (-not $allFilesExist) {
    Write-Host "`n  ⚠ Some Patch W files are missing" -ForegroundColor Yellow
    exit 1
}

# Step 5: Summary and next steps
Write-Host "`n[5/5] Integration Summary" -ForegroundColor Yellow
Write-Host "`n✅ Patch W Core Files Created:" -ForegroundColor Green
Write-Host "  - Pinia geometry store (350 lines)" -ForegroundColor Gray
Write-Host "  - Geometry toolbar component (250 lines)" -ForegroundColor Gray
Write-Host "  - CAM integration composable (150 lines)" -ForegroundColor Gray
Write-Host "  - Documentation (750+ lines)" -ForegroundColor Gray

Write-Host "`n📋 Manual Steps Required:" -ForegroundColor Cyan
Write-Host "  1. Register Pinia in packages/client/src/main.ts:" -ForegroundColor White
Write-Host "     import { createPinia } from 'pinia'" -ForegroundColor Gray
Write-Host "     const pinia = createPinia()" -ForegroundColor Gray
Write-Host "     app.use(pinia)" -ForegroundColor Gray

Write-Host "`n  2. Add GeometryToolbar to client/src/App.vue:" -ForegroundColor White
Write-Host "     <GeometryToolbar /> (inside <div class='app'>)" -ForegroundColor Gray

Write-Host "`n  3. Test the workflow:" -ForegroundColor White
Write-Host "     cd packages\client" -ForegroundColor Gray
Write-Host "     npm run dev" -ForegroundColor Gray
Write-Host "     # Open http://localhost:5173" -ForegroundColor Gray
Write-Host "     # Test Bridge Calculator → Send to CAM → Helical Ramping" -ForegroundColor Gray

Write-Host "`n📖 Documentation: PATCH_W_DESIGN_CAM_WORKFLOW.md" -ForegroundColor Cyan

Write-Host "`n=== Patch W Integration Script Complete ===" -ForegroundColor Green
exit 0
