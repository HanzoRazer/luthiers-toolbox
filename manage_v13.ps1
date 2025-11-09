# Art Studio v13 Management Script
# Provides easy commands to pin dependencies, revert integration, or verify installation

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('pin', 'revert', 'verify', 'help')]
    [string]$Action = 'help'
)

$ErrorActionPreference = 'Stop'
$RepoRoot = "C:\Users\thepr\Downloads\Luthiers ToolBox"

function Show-Help {
    Write-Host @"

Art Studio v13 Management Script
=================================

Usage: .\manage_v13.ps1 [action]

Actions:
  pin       Pin dependencies to stable versions (prevents breaking upgrades)
  revert    Remove Art Studio v13 integration (restore pre-v13 state)
  verify    Check if Art Studio v13 is properly installed
  help      Show this help message

Examples:
  .\manage_v13.ps1 pin          # Pin numpy, shapely versions
  .\manage_v13.ps1 revert       # Remove Art Studio v13
  .\manage_v13.ps1 verify       # Check installation status

"@
}

function Test-FileExists {
    param([string]$Path)
    Test-Path (Join-Path $RepoRoot $Path)
}

function Verify-Installation {
    Write-Host "`n=== Art Studio v13 Installation Status ===`n"
    
    $files = @{
        "Backend Router"    = "services\api\app\routers\cam_vcarve_router.py"
        "API - Infill"      = "packages\client\src\api\infill.ts"
        "API - VCarve"      = "packages\client\src\api\vcarve.ts"
        "Component - Toast" = "packages\client\src\components\Toast.vue"
        "View - ArtStudio"  = "packages\client\src\views\ArtStudio.vue"
    }
    
    $allPresent = $true
    foreach ($item in $files.GetEnumerator()) {
        $exists = Test-FileExists $item.Value
        $status = if ($exists) { "✓" } else { "✗"; $allPresent = $false }
        Write-Host "$status $($item.Key): $($item.Value)"
    }
    
    Write-Host "`n=== Dependencies ===`n"
    & "$RepoRoot\.venv\Scripts\python" -c @"
try:
    import shapely; print('✓ shapely:', shapely.__version__)
except: print('✗ shapely: not installed')
try:
    import fastapi; print('✓ fastapi: installed')
except: print('✗ fastapi: not installed')
try:
    import pyclipper; print('✓ pyclipper:', pyclipper.__version__)
except: print('⚠ pyclipper: not installed (contour mode unavailable)')
"@
    
    Write-Host "`n=== Router Registration ===`n"
    $mainPy = Get-Content (Join-Path $RepoRoot "services\api\app\main.py") -Raw
    if ($mainPy -match 'cam_vcarve_router') {
        Write-Host "✓ Router registered in main.py"
    } else {
        Write-Host "✗ Router NOT registered in main.py"
    }
    
    Write-Host "`n=== Overall Status ===`n"
    if ($allPresent) {
        Write-Host "✓ Art Studio v13 is INSTALLED and ready" -ForegroundColor Green
    } else {
        Write-Host "⚠ Art Studio v13 is PARTIALLY installed or missing" -ForegroundColor Yellow
    }
}

function Pin-Dependencies {
    Write-Host "`n=== Pinning Dependencies ===`n"
    
    $reqFile = Join-Path $RepoRoot "services\api\requirements.txt"
    $lockFile = Join-Path $RepoRoot "services\api\requirements.lock"
    
    # Update requirements.txt with pinned versions
    $requirements = @"
fastapi
uvicorn
pydantic
jinja2
sqlalchemy
sqlite-utils

# Geometry stack (pinned for toolpath stability)
numpy~=2.3.0
shapely~=2.1.0
# pyclipper requires Python 3.11 or manual wheel for 3.13

# CAD/DXF
ezdxf
"@
    
    Set-Content -Path $reqFile -Value $requirements -Encoding UTF8
    Write-Host "✓ Updated requirements.txt with pinned versions"
    
    # Create lock file
    $lockContent = @"
#
# Luthier's Tool Box Pinned Environment (v13 Geometry Stack)
# Generated for Art Studio / CAM V-carve Preview stability
# Last updated: $(Get-Date -Format "yyyy-MM-dd")
#
# Install with: pip install -r requirements.lock
#

# Core framework
fastapi==0.121.0
uvicorn==0.38.0
pydantic==2.12.4
starlette==0.49.3

# Geometry stack (critical for toolpath reproducibility)
numpy==2.3.4
shapely==2.1.2

# CAD/DXF
ezdxf==1.4.3

# Database
sqlalchemy==2.0.44
sqlite-utils==3.38
"@
    
    Set-Content -Path $lockFile -Value $lockContent -Encoding UTF8
    Write-Host "✓ Created requirements.lock for frozen installs"
    
    Write-Host "`n✅ Dependencies pinned successfully!"
    Write-Host "   To reinstall with pinned versions: pip install -r services\api\requirements.lock"
}

function Revert-Integration {
    Write-Host "`n=== Reverting Art Studio v13 Integration ===`n"
    
    $confirm = Read-Host "This will remove all Art Studio v13 files. Continue? (y/N)"
    if ($confirm -ne 'y' -and $confirm -ne 'Y') {
        Write-Host "Cancelled." -ForegroundColor Yellow
        return
    }
    
    # Remove files
    $filesToRemove = @(
        "services\api\app\routers\cam_vcarve_router.py",
        "packages\client\src\api\infill.ts",
        "packages\client\src\api\vcarve.ts",
        "packages\client\src\components\Toast.vue",
        "packages\client\src\views\ArtStudio.vue"
    )
    
    foreach ($file in $filesToRemove) {
        $fullPath = Join-Path $RepoRoot $file
        if (Test-Path $fullPath) {
            Remove-Item $fullPath -Force
            Write-Host "✓ Removed: $file"
        } else {
            Write-Host "⊘ Not found: $file" -ForegroundColor Gray
        }
    }
    
    # Update main.py
    $mainPyPath = Join-Path $RepoRoot "services\api\app\main.py"
    $mainPyContent = Get-Content $mainPyPath -Raw
    
    # Remove router import
    $mainPyContent = $mainPyContent -replace '(?ms)# Art Studio preview router \(v13\).*?cam_vcarve_router = None\r?\n\r?\n', ''
    
    # Remove router registration
    $mainPyContent = $mainPyContent -replace '(?ms)# v13: Art Studio preview infill endpoint.*?app\.include_router\(cam_vcarve_router\)\r?\n\r?\n', ''
    
    Set-Content -Path $mainPyPath -Value $mainPyContent -NoNewline -Encoding UTF8
    Write-Host "✓ Updated main.py (removed router registration)"
    
    Write-Host "`n✅ Art Studio v13 integration reverted successfully!"
    Write-Host "   Your repository is now in pre-v13 state."
    Write-Host "   Note: Dependencies (shapely, etc.) are still installed in venv."
}

# Main execution
Set-Location $RepoRoot

switch ($Action) {
    'pin' {
        Pin-Dependencies
    }
    'revert' {
        Revert-Integration
    }
    'verify' {
        Verify-Installation
    }
    'help' {
        Show-Help
    }
}
