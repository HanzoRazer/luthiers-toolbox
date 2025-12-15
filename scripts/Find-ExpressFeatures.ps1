# Find Express Edition Feature Files
# Identifies exact files to extract for Rosette, Curve Lab, and Fretboard Designer

<#
.SYNOPSIS
Finds all files needed for Express Edition feature extraction.

.DESCRIPTION
Scans the golden master repository and identifies:
- Backend routers
- Frontend views
- Components
- Utilities
- Stores

For each of the 3 Express features.
#>

$GoldenMaster = "c:\Users\thepr\Downloads\Luthiers ToolBox"

Write-Host "`n╔═══════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                                                                   ║" -ForegroundColor Cyan
Write-Host "║   Express Edition Feature File Finder                            ║" -ForegroundColor Cyan
Write-Host "║                                                                   ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# ============================================================================
# Feature 1: Rosette Designer
# ============================================================================

Write-Host "=== FEATURE 1: ROSETTE DESIGNER ===" -ForegroundColor Yellow
Write-Host ""

Write-Host "Backend Files:" -ForegroundColor White
$rosetteBackend = @(
    Get-ChildItem -Path "$GoldenMaster\services\api\app\routers" -Recurse -Filter "*rosette*.py" -ErrorAction SilentlyContinue
    Get-ChildItem -Path "$GoldenMaster\services\api\app" -Recurse -Filter "*rosette*store*.py" -ErrorAction SilentlyContinue
)

foreach ($file in $rosetteBackend) {
    Write-Host "  ✓ $($file.FullName)" -ForegroundColor Green
}

Write-Host "`nFrontend Views:" -ForegroundColor White
$rosetteFrontend = @(
    Get-ChildItem -Path "$GoldenMaster\client\src\views" -Recurse -Filter "*Rosette*.vue" -ErrorAction SilentlyContinue
    Get-ChildItem -Path "$GoldenMaster\packages\client\src\views" -Recurse -Filter "*Rosette*.vue" -ErrorAction SilentlyContinue
)

foreach ($file in $rosetteFrontend) {
    Write-Host "  ✓ $($file.FullName)" -ForegroundColor Green
}

Write-Host "`nComponents:" -ForegroundColor White
$rosetteComponents = @(
    Get-ChildItem -Path "$GoldenMaster\client\src\components\rosette" -Recurse -Filter "*.vue" -ErrorAction SilentlyContinue
    Get-ChildItem -Path "$GoldenMaster\packages\client\src\components\rosette" -Recurse -Filter "*.vue" -ErrorAction SilentlyContinue
)

foreach ($file in $rosetteComponents) {
    Write-Host "  ✓ $($file.FullName)" -ForegroundColor Green
}

# ============================================================================
# Feature 2: Curve Lab
# ============================================================================

Write-Host "`n=== FEATURE 2: CURVE LAB ===" -ForegroundColor Yellow
Write-Host ""

Write-Host "Backend Files:" -ForegroundColor White
$curveBackend = @(
    Get-ChildItem -Path "$GoldenMaster\services\api\app\routers" -Recurse -Filter "*curve*.py" -ErrorAction SilentlyContinue
    Get-ChildItem -Path "$GoldenMaster\services\api\app\routers" -Recurse -Filter "*bezier*.py" -ErrorAction SilentlyContinue
)

if ($curveBackend.Count -eq 0) {
    Write-Host "  ℹ No dedicated curve router found - may be in geometry_router.py" -ForegroundColor Gray
    $geometryRouter = Get-ChildItem -Path "$GoldenMaster\services\api\app\routers" -Recurse -Filter "geometry*.py" -ErrorAction SilentlyContinue
    foreach ($file in $geometryRouter) {
        Write-Host "  ? Check: $($file.FullName)" -ForegroundColor Yellow
    }
} else {
    foreach ($file in $curveBackend) {
        Write-Host "  ✓ $($file.FullName)" -ForegroundColor Green
    }
}

Write-Host "`nFrontend Views:" -ForegroundColor White
$curveFrontend = @(
    Get-ChildItem -Path "$GoldenMaster\client\src\views" -Recurse -Filter "*Curve*.vue" -ErrorAction SilentlyContinue
    Get-ChildItem -Path "$GoldenMaster\packages\client\src\views" -Recurse -Filter "*Curve*.vue" -ErrorAction SilentlyContinue
)

if ($curveFrontend.Count -eq 0) {
    Write-Host "  ℹ No dedicated Curve view found - may be in ArtStudio*.vue" -ForegroundColor Gray
} else {
    foreach ($file in $curveFrontend) {
        Write-Host "  ✓ $($file.FullName)" -ForegroundColor Green
    }
}

# ============================================================================
# Feature 3: Fretboard Designer
# ============================================================================

Write-Host "`n=== FEATURE 3: FRETBOARD DESIGNER ===" -ForegroundColor Yellow
Write-Host ""

Write-Host "Backend Files:" -ForegroundColor White
$fretboardBackend = @(
    Get-ChildItem -Path "$GoldenMaster\services\api\app\routers" -Recurse -Filter "*fret*.py" -ErrorAction SilentlyContinue
    Get-ChildItem -Path "$GoldenMaster\services\api\app\routers" -Recurse -Filter "*fingerboard*.py" -ErrorAction SilentlyContinue
)

if ($fretboardBackend.Count -eq 0) {
    Write-Host "  ℹ No dedicated fretboard router found - searching broader..." -ForegroundColor Gray
    $boardRouters = Get-ChildItem -Path "$GoldenMaster\services\api\app\routers" -Recurse -Filter "*board*.py" -ErrorAction SilentlyContinue
    foreach ($file in $boardRouters) {
        Write-Host "  ? Check: $($file.FullName)" -ForegroundColor Yellow
    }
} else {
    foreach ($file in $fretboardBackend) {
        Write-Host "  ✓ $($file.FullName)" -ForegroundColor Green
    }
}

Write-Host "`nFrontend Views:" -ForegroundColor White
$fretboardFrontend = @(
    Get-ChildItem -Path "$GoldenMaster\client\src\views" -Recurse -Filter "*Fret*.vue" -ErrorAction SilentlyContinue
    Get-ChildItem -Path "$GoldenMaster\packages\client\src\views" -Recurse -Filter "*Fingerboard*.vue" -ErrorAction SilentlyContinue
    Get-ChildItem -Path "$GoldenMaster\packages\client\src\views" -Recurse -Filter "*Fret*.vue" -ErrorAction SilentlyContinue
)

if ($fretboardFrontend.Count -eq 0) {
    Write-Host "  ℹ No dedicated Fretboard view found - searching broader..." -ForegroundColor Gray
    $boardViews = Get-ChildItem -Path "$GoldenMaster\packages\client\src\views" -Recurse -Filter "*board*.vue" -ErrorAction SilentlyContinue
    foreach ($file in $boardViews) {
        Write-Host "  ? Check: $($file.FullName)" -ForegroundColor Yellow
    }
} else {
    foreach ($file in $fretboardFrontend) {
        Write-Host "  ✓ $($file.FullName)" -ForegroundColor Green
    }
}

# ============================================================================
# Summary
# ============================================================================

Write-Host "`n╔═══════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Summary                                                          ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

$totalFiles = $rosetteBackend.Count + $rosetteFrontend.Count + $rosetteComponents.Count + `
              $curveBackend.Count + $curveFrontend.Count + `
              $fretboardBackend.Count + $fretboardFrontend.Count

Write-Host "Files Found: $totalFiles" -ForegroundColor White
Write-Host ""
Write-Host "Rosette Designer:" -ForegroundColor Yellow
Write-Host "  Backend: $($rosetteBackend.Count) files" -ForegroundColor Gray
Write-Host "  Frontend: $($rosetteFrontend.Count) views" -ForegroundColor Gray
Write-Host "  Components: $($rosetteComponents.Count) components" -ForegroundColor Gray

Write-Host "`nCurve Lab:" -ForegroundColor Yellow
Write-Host "  Backend: $($curveBackend.Count) files" -ForegroundColor Gray
Write-Host "  Frontend: $($curveFrontend.Count) views" -ForegroundColor Gray

Write-Host "`nFretboard Designer:" -ForegroundColor Yellow
Write-Host "  Backend: $($fretboardBackend.Count) files" -ForegroundColor Gray
Write-Host "  Frontend: $($fretboardFrontend.Count) views" -ForegroundColor Gray

Write-Host "`n📝 Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Review files listed above" -ForegroundColor Gray
Write-Host "  2. Read EXPRESS_EXTRACTION_GUIDE.md for extraction steps" -ForegroundColor Gray
Write-Host "  3. Start with Rosette Designer (most complete feature)" -ForegroundColor Gray
Write-Host "  4. Copy files manually or use extraction scripts" -ForegroundColor Gray
Write-Host ""
