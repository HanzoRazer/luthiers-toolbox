# Extract Rosette Designer to ltb-express
# Copies all necessary files and sets up the feature

<#
.SYNOPSIS
Extracts Rosette Designer Lite from golden master to ltb-express.

.DESCRIPTION
Complete extraction workflow:
1. Copy backend files (router + store)
2. Copy frontend files (views + components)
3. Setup client dependencies if needed
4. Create extraction log
#>

param(
    [switch]$DryRun  # Show what would be copied without actually copying
)

$GoldenMaster = "c:\Users\thepr\Downloads\Luthiers ToolBox"
$ExpressRepo = "c:\Users\thepr\Downloads\ltb-express"
$LogFile = "$ExpressRepo\EXTRACTION_LOG.txt"

Write-Host "`n╔═══════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                                                                   ║" -ForegroundColor Cyan
Write-Host "║   Rosette Designer Lite Extraction                               ║" -ForegroundColor Cyan
Write-Host "║   Express Edition Feature 1                                       ║" -ForegroundColor Cyan
Write-Host "║                                                                   ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "🔍 DRY RUN MODE - No files will be copied`n" -ForegroundColor Yellow
}

# ============================================================================
# Step 1: Verify Source Files Exist
# ============================================================================

Write-Host "Step 1: Verifying source files..." -ForegroundColor Yellow

$sourceFiles = @{
    "Backend Router" = "$GoldenMaster\services\api\app\routers\art_studio_rosette_router.py"
    "Backend Store" = "$GoldenMaster\services\api\app\art_studio_rosette_store.py"
    "Frontend View" = "$GoldenMaster\client\src\views\ArtStudioRosette.vue"
    "Component 1" = "$GoldenMaster\client\src\components\rosette\RosetteCanvas.vue"
    "Component 2" = "$GoldenMaster\client\src\components\rosette\PatternTemplates.vue"
    "Component 3" = "$GoldenMaster\client\src\components\rosette\MaterialPalette.vue"
}

$allFound = $true
foreach ($key in $sourceFiles.Keys) {
    $path = $sourceFiles[$key]
    if (Test-Path $path) {
        Write-Host "  ✓ $key found" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $key NOT FOUND: $path" -ForegroundColor Red
        $allFound = $false
    }
}

if (-not $allFound) {
    Write-Host "`n❌ Some source files are missing. Aborting extraction." -ForegroundColor Red
    exit 1
}

Write-Host ""

# ============================================================================
# Step 2: Create Target Directories
# ============================================================================

Write-Host "Step 2: Creating target directories..." -ForegroundColor Yellow

$targetDirs = @(
    "$ExpressRepo\server\app\routers"
    "$ExpressRepo\server\app\stores"
    "$ExpressRepo\client\src\views"
    "$ExpressRepo\client\src\components\rosette"
)

foreach ($dir in $targetDirs) {
    if (-not (Test-Path $dir)) {
        if (-not $DryRun) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
        Write-Host "  ✓ Created: $dir" -ForegroundColor Green
    } else {
        Write-Host "  ℹ Exists: $dir" -ForegroundColor Gray
    }
}

Write-Host ""

# ============================================================================
# Step 3: Copy Backend Files
# ============================================================================

Write-Host "Step 3: Copying backend files..." -ForegroundColor Yellow

$backendCopies = @(
    @{
        Source = "$GoldenMaster\services\api\app\routers\art_studio_rosette_router.py"
        Target = "$ExpressRepo\server\app\routers\rosette_router.py"
        Description = "Backend Router"
    },
    @{
        Source = "$GoldenMaster\services\api\app\art_studio_rosette_store.py"
        Target = "$ExpressRepo\server\app\stores\rosette_store.py"
        Description = "Backend Store"
    }
)

foreach ($copy in $backendCopies) {
    if (-not $DryRun) {
        Copy-Item $copy.Source $copy.Target -Force
    }
    Write-Host "  ✓ $($copy.Description): $($copy.Target)" -ForegroundColor Green
}

Write-Host ""

# ============================================================================
# Step 4: Copy Frontend Files
# ============================================================================

Write-Host "Step 4: Copying frontend files..." -ForegroundColor Yellow

$frontendCopies = @(
    @{
        Source = "$GoldenMaster\client\src\views\ArtStudioRosette.vue"
        Target = "$ExpressRepo\client\src\views\RosetteDesigner.vue"
        Description = "Frontend View"
    },
    @{
        Source = "$GoldenMaster\client\src\components\rosette\RosetteCanvas.vue"
        Target = "$ExpressRepo\client\src\components\rosette\RosetteCanvas.vue"
        Description = "Canvas Component"
    },
    @{
        Source = "$GoldenMaster\client\src\components\rosette\PatternTemplates.vue"
        Target = "$ExpressRepo\client\src\components\rosette\PatternTemplates.vue"
        Description = "Pattern Templates"
    },
    @{
        Source = "$GoldenMaster\client\src\components\rosette\MaterialPalette.vue"
        Target = "$ExpressRepo\client\src\components\rosette\MaterialPalette.vue"
        Description = "Material Palette"
    }
)

foreach ($copy in $frontendCopies) {
    if (-not $DryRun) {
        Copy-Item $copy.Source $copy.Target -Force
    }
    Write-Host "  ✓ $($copy.Description): $($copy.Target)" -ForegroundColor Green
}

Write-Host ""

# ============================================================================
# Step 5: Log Extraction
# ============================================================================

if (-not $DryRun) {
    Write-Host "Step 5: Creating extraction log..." -ForegroundColor Yellow
    
    $logContent = @"
Rosette Designer Lite - Extraction Log
======================================

Extraction Date: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Source: $GoldenMaster
Target: $ExpressRepo

Backend Files Extracted:
- art_studio_rosette_router.py → server/app/routers/rosette_router.py
- art_studio_rosette_store.py → server/app/stores/rosette_store.py

Frontend Files Extracted:
- ArtStudioRosette.vue → client/src/views/RosetteDesigner.vue
- RosetteCanvas.vue → client/src/components/rosette/RosetteCanvas.vue
- PatternTemplates.vue → client/src/components/rosette/PatternTemplates.vue
- MaterialPalette.vue → client/src/components/rosette/MaterialPalette.vue

Next Steps:
1. Strip Pro/Enterprise features from backend files
2. Strip Pro/Enterprise UI from frontend files
3. Register router in server/app/main.py
4. Setup Vue client if not done already
5. Test feature end-to-end

Pro/Enterprise Features to Remove:
- Backend: /compare endpoints, risk scoring, audit logging
- Frontend: Compare mode button, risk analysis panel, advanced exports
"@

    $logContent | Out-File -FilePath $LogFile -Encoding UTF8
    Write-Host "  ✓ Log created: $LogFile" -ForegroundColor Green
    Write-Host ""
}

# ============================================================================
# Summary
# ============================================================================

Write-Host "╔═══════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Extraction Complete                                              ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "🔍 DRY RUN: No files were actually copied" -ForegroundColor Yellow
    Write-Host "   Run without -DryRun to perform actual extraction`n" -ForegroundColor Yellow
} else {
    Write-Host "✅ Files Copied:" -ForegroundColor Green
    Write-Host "   Backend: 2 files" -ForegroundColor Gray
    Write-Host "   Frontend: 4 files" -ForegroundColor Gray
    Write-Host ""
    Write-Host "📋 Next Manual Steps:" -ForegroundColor Yellow
    Write-Host "   1. Edit server/app/routers/rosette_router.py:" -ForegroundColor White
    Write-Host "      - Remove /compare/* endpoints" -ForegroundColor Gray
    Write-Host "      - Remove risk scoring code" -ForegroundColor Gray
    Write-Host "      - Keep: /preview, /save, /jobs, /presets" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   2. Edit server/app/stores/rosette_store.py:" -ForegroundColor White
    Write-Host "      - Remove compare_history table" -ForegroundColor Gray
    Write-Host "      - Remove risk_analysis table" -ForegroundColor Gray
    Write-Host "      - Remove audit_log table" -ForegroundColor Gray
    Write-Host "      - Keep: jobs, presets tables" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   3. Edit client/src/views/RosetteDesigner.vue:" -ForegroundColor White
    Write-Host "      - Remove 'Compare Mode' button" -ForegroundColor Gray
    Write-Host "      - Remove risk analysis panel" -ForegroundColor Gray
    Write-Host "      - Remove advanced export options (DWG, STEP)" -ForegroundColor Gray
    Write-Host "      - Keep: Basic preview, DXF/SVG export" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   4. Register router in server/app/main.py:" -ForegroundColor White
    Write-Host "      from app.routers.rosette_router import router as rosette_router" -ForegroundColor Gray
    Write-Host "      app.include_router(rosette_router, prefix='/api/rosette')" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   5. Test the feature:" -ForegroundColor White
    Write-Host "      cd $ExpressRepo\server" -ForegroundColor Gray
    Write-Host "      .\.venv\Scripts\Activate.ps1" -ForegroundColor Gray
    Write-Host "      uvicorn app.main:app --reload" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   6. Setup Vue client (if not done):" -ForegroundColor White
    Write-Host "      cd $ExpressRepo\client" -ForegroundColor Gray
    Write-Host "      npm create vite@latest . -- --template vue-ts" -ForegroundColor Gray
    Write-Host "      npm install" -ForegroundColor Gray
    Write-Host "      npm run dev" -ForegroundColor Gray
    Write-Host ""
    Write-Host "📖 See: EXPRESS_EXTRACTION_GUIDE.md for detailed stripping instructions`n" -ForegroundColor Cyan
}
