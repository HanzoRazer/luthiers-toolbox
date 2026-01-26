<#
.SYNOPSIS
    Extracts a standalone designer product from the Golden Master.

.DESCRIPTION
    This script automates feature extraction from luthiers-toolbox to a spin-off repo.
    It copies source files, adapts imports, and sets up the project structure.

.PARAMETER Product
    The product to extract: neck, headstock, fingerboard, bridge, blueprint

.PARAMETER TargetPath
    Path to the target repository (e.g., C:\Users\thepr\Downloads\ltb-neck-designer)

.PARAMETER GoldenMasterPath
    Path to the Golden Master repo (defaults to current directory's parent)

.EXAMPLE
    .\Extract-Designer.ps1 -Product neck -TargetPath "C:\repos\ltb-neck-designer"

.NOTES
    Run from the Golden Master repository root.
#>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("neck", "headstock", "fingerboard", "bridge", "blueprint")]
    [string]$Product,
    
    [Parameter(Mandatory=$true)]
    [string]$TargetPath,
    
    [string]$GoldenMasterPath = (Get-Location).Path
)

$ErrorActionPreference = "Stop"

# =============================================================================
# PRODUCT CONFIGURATIONS
# =============================================================================

$Products = @{
    "neck" = @{
        Name = "Luthier's ToolBox Neck Designer"
        Edition = "NECK_DESIGNER"
        RepoName = "ltb-neck-designer"
        Description = "Parametric neck profile generator with Fender/Gibson presets"
        BackendFiles = @(
            @{ Source = "services/api/app/routers/neck_router.py"; Dest = "server/app/routers/neck_router.py" }
            @{ Source = "services/api/app/routers/neck_generator_router.py"; Dest = "server/app/routers/neck_generator_router.py" }
            @{ Source = "services/api/app/generators/neck_headstock_generator.py"; Dest = "server/app/generators/neck_generator.py" }
            @{ Source = "services/api/app/instrument_geometry/neck/neck_profiles.py"; Dest = "server/app/geometry/neck_profiles.py" }
            @{ Source = "services/api/app/instrument_geometry/neck/fret_math.py"; Dest = "server/app/geometry/fret_math.py" }
            @{ Source = "services/api/app/instrument_geometry/neck/radius_profiles.py"; Dest = "server/app/geometry/radius_profiles.py" }
            @{ Source = "services/api/app/instrument_geometry/body/fretboard_geometry.py"; Dest = "server/app/geometry/fretboard_geometry.py" }
        )
        FrontendFiles = @(
            # Add frontend components as needed
        )
        Dependencies = @("fastapi", "uvicorn", "pydantic", "ezdxf")
    }
    
    "headstock" = @{
        Name = "Luthier's ToolBox Headstock Designer"
        Edition = "HEADSTOCK_DESIGNER"
        RepoName = "ltb-headstock-designer"
        Description = "Headstock outline and tuner layout generator"
        BackendFiles = @(
            @{ Source = "services/api/app/generators/neck_headstock_generator.py"; Dest = "server/app/generators/headstock_generator.py" }
            @{ Source = "services/api/app/instrument_geometry/dxf_registry.py"; Dest = "server/app/geometry/dxf_registry.py" }
        )
        FrontendFiles = @()
        Dependencies = @("fastapi", "uvicorn", "pydantic", "ezdxf")
    }
    
    "fingerboard" = @{
        Name = "Luthier's ToolBox Fingerboard Designer"
        Edition = "FINGERBOARD_DESIGNER"
        RepoName = "ltb-fingerboard-designer"
        Description = "Fret position calculator with temperament systems"
        BackendFiles = @(
            @{ Source = "services/api/app/instrument_geometry/neck/fret_math.py"; Dest = "server/app/geometry/fret_math.py" }
            @{ Source = "services/api/app/instrument_geometry/body/fretboard_geometry.py"; Dest = "server/app/geometry/fretboard_geometry.py" }
            @{ Source = "services/api/app/routers/music/temperament_router.py"; Dest = "server/app/routers/temperament_router.py" }
            @{ Source = "services/api/app/routers/fret_router.py"; Dest = "server/app/routers/fret_router.py" }
            @{ Source = "services/api/app/calculators/alternative_temperaments.py"; Dest = "server/app/calculators/temperaments.py" }
            @{ Source = "services/api/app/calculators/fret_slots_export.py"; Dest = "server/app/calculators/fret_export.py" }
        )
        FrontendFiles = @()
        Dependencies = @("fastapi", "uvicorn", "pydantic", "ezdxf")
    }
    
    "bridge" = @{
        Name = "Luthier's ToolBox Bridge Designer"
        Edition = "BRIDGE_DESIGNER"
        RepoName = "ltb-bridge-designer"
        Description = "Bridge geometry and saddle compensation calculator"
        BackendFiles = @(
            @{ Source = "services/api/app/routers/bridge_router.py"; Dest = "server/app/routers/bridge_router.py" }
            @{ Source = "services/api/app/instrument_geometry/bridge/geometry.py"; Dest = "server/app/geometry/bridge_geometry.py" }
            @{ Source = "services/api/app/instrument_geometry/bridge/compensation.py"; Dest = "server/app/geometry/compensation.py" }
            @{ Source = "services/api/app/instrument_geometry/bridge/placement.py"; Dest = "server/app/geometry/placement.py" }
            @{ Source = "services/api/app/pipelines/bridge/bridge_to_dxf.py"; Dest = "server/app/export/bridge_dxf.py" }
        )
        FrontendFiles = @()
        Dependencies = @("fastapi", "uvicorn", "pydantic", "ezdxf")
    }
    
    "blueprint" = @{
        Name = "Blueprint Reader"
        Edition = "BLUEPRINT_READER"
        RepoName = "blueprint-reader"
        Description = "AI-powered blueprint digitization system"
        BackendFiles = @(
            @{ Source = "services/api/app/routers/blueprint_router.py"; Dest = "server/app/routers/blueprint_router.py" }
            @{ Source = "services/api/app/routers/blueprint_cam_bridge.py"; Dest = "server/app/routers/blueprint_bridge.py" }
            @{ Source = "services/api/app/services/vision_service.py"; Dest = "server/app/services/vision_service.py" }
        )
        FrontendFiles = @()
        Dependencies = @("fastapi", "uvicorn", "pydantic", "ezdxf", "opencv-python", "pdf2image", "anthropic")
    }
}

$Config = $Products[$Product]

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

function Write-Step {
    param([string]$Message)
    Write-Host "`n=== $Message ===" -ForegroundColor Cyan
}

function Write-Info {
    param([string]$Message)
    Write-Host "  → $Message" -ForegroundColor Gray
}

function Write-Success {
    param([string]$Message)
    Write-Host "  ✓ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "  ⚠ $Message" -ForegroundColor Yellow
}

function Ensure-Directory {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
        Write-Info "Created directory: $Path"
    }
}

function Adapt-Imports {
    param([string]$FilePath)
    
    $content = Get-Content $FilePath -Raw
    
    # Common import adaptations
    $replacements = @(
        @{ Old = "from \.\.instrument_geometry\."; New = "from app.geometry." }
        @{ Old = "from \.\.calculators\."; New = "from app.calculators." }
        @{ Old = "from \.\.routers\."; New = "from app.routers." }
        @{ Old = "from \.\.generators\."; New = "from app.generators." }
        @{ Old = "from \.\.services\."; New = "from app.services." }
        @{ Old = "from app\.instrument_geometry\."; New = "from app.geometry." }
        @{ Old = "from app\.calculators\."; New = "from app.calculators." }
        @{ Old = "from \.\.rmos\."; New = "# REMOVED: " }  # Flag RMOS imports for manual review
        @{ Old = "from app\.rmos\."; New = "# REMOVED: " }
    )
    
    foreach ($r in $replacements) {
        $content = $content -replace $r.Old, $r.New
    }
    
    Set-Content -Path $FilePath -Value $content
}

# =============================================================================
# MAIN EXTRACTION
# =============================================================================

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║  Luthier's ToolBox Feature Extractor                        ║" -ForegroundColor Magenta
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Magenta

Write-Host "`nExtracting: " -NoNewline
Write-Host $Config.Name -ForegroundColor Yellow
Write-Host "Target: $TargetPath"
Write-Host "Golden Master: $GoldenMasterPath"

# -----------------------------------------------------------------------------
# Step 1: Create directory structure
# -----------------------------------------------------------------------------

Write-Step "Creating directory structure"

$directories = @(
    "$TargetPath/server/app/routers",
    "$TargetPath/server/app/geometry",
    "$TargetPath/server/app/calculators",
    "$TargetPath/server/app/generators",
    "$TargetPath/server/app/services",
    "$TargetPath/server/app/export",
    "$TargetPath/server/tests",
    "$TargetPath/client/src/components",
    "$TargetPath/client/src/views",
    "$TargetPath/client/src/stores",
    "$TargetPath/.github/workflows"
)

foreach ($dir in $directories) {
    Ensure-Directory $dir
}

Write-Success "Directory structure created"

# -----------------------------------------------------------------------------
# Step 2: Copy backend files
# -----------------------------------------------------------------------------

Write-Step "Copying backend files"

foreach ($file in $Config.BackendFiles) {
    $sourcePath = Join-Path $GoldenMasterPath $file.Source
    $destPath = Join-Path $TargetPath $file.Dest
    
    if (Test-Path $sourcePath) {
        $destDir = Split-Path $destPath -Parent
        Ensure-Directory $destDir
        
        Copy-Item $sourcePath $destPath -Force
        Write-Success "Copied: $($file.Source)"
        
        # Adapt imports
        Adapt-Imports $destPath
        Write-Info "Adapted imports in: $($file.Dest)"
    } else {
        Write-Warning "Source not found: $($file.Source)"
    }
}

# -----------------------------------------------------------------------------
# Step 3: Create __init__.py files
# -----------------------------------------------------------------------------

Write-Step "Creating __init__.py files"

$initDirs = @(
    "$TargetPath/server/app",
    "$TargetPath/server/app/routers",
    "$TargetPath/server/app/geometry",
    "$TargetPath/server/app/calculators",
    "$TargetPath/server/app/generators",
    "$TargetPath/server/app/services",
    "$TargetPath/server/app/export",
    "$TargetPath/server/tests"
)

foreach ($dir in $initDirs) {
    if (Test-Path $dir) {
        $initPath = Join-Path $dir "__init__.py"
        if (-not (Test-Path $initPath)) {
            "" | Out-File -FilePath $initPath -Encoding utf8
            Write-Info "Created: $initPath"
        }
    }
}

Write-Success "__init__.py files created"

# -----------------------------------------------------------------------------
# Step 4: Create main.py from template
# -----------------------------------------------------------------------------

Write-Step "Creating main.py"

$mainPyPath = Join-Path $TargetPath "server/app/main.py"

$mainPyContent = @"
"""
$($Config.Name) - Standalone API Server

Edition: $($Config.Edition)
Extracted from: Luthier's ToolBox Golden Master
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

APP_NAME = "$($Config.Name)"
APP_EDITION = "$($Config.Edition)"
APP_VERSION = "1.0.0"

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="$($Config.Description)"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# Mount routers
# =============================================================================

# TODO: Import and mount your routers here
# Example:
# from app.routers.neck_router import router as neck_router
# app.include_router(neck_router, prefix="/api/neck", tags=["Neck"])

# =============================================================================
# Health endpoint (REQUIRED for all spin-offs)
# =============================================================================

@app.get("/health")
def health():
    """Health check with edition tag."""
    return {
        "status": "ok",
        "edition": APP_EDITION,
        "version": APP_VERSION
    }

@app.get("/")
def root():
    """Root endpoint."""
    return {
        "app": APP_NAME,
        "edition": APP_EDITION,
        "docs": "/docs"
    }
"@

Set-Content -Path $mainPyPath -Value $mainPyContent
Write-Success "Created main.py"

# -----------------------------------------------------------------------------
# Step 5: Create requirements.txt
# -----------------------------------------------------------------------------

Write-Step "Creating requirements.txt"

$requirementsPath = Join-Path $TargetPath "server/requirements.txt"
$requirementsContent = $Config.Dependencies -join "`n"

Set-Content -Path $requirementsPath -Value $requirementsContent
Write-Success "Created requirements.txt"

# -----------------------------------------------------------------------------
# Step 6: Create .env template
# -----------------------------------------------------------------------------

Write-Step "Creating .env template"

$envPath = Join-Path $TargetPath "server/.env.example"
$envContent = @"
# $($Config.Name) Configuration

APP_NAME=$($Config.Name)
APP_EDITION=$($Config.Edition)
APP_VERSION=1.0.0

# Data directory
DATA_DIR=./data

# Feature flags (set to true/false)
FEATURE_CAM=false
FEATURE_RISK_MODEL=false
"@

Set-Content -Path $envPath -Value $envContent
Write-Success "Created .env.example"

# -----------------------------------------------------------------------------
# Step 7: Copy copilot-instructions.md template
# -----------------------------------------------------------------------------

Write-Step "Setting up AI agent instructions"

$templatePath = Join-Path $GoldenMasterPath "templates/.github/copilot-instructions.md"
$destPath = Join-Path $TargetPath ".github/copilot-instructions.md"

if (Test-Path $templatePath) {
    Copy-Item $templatePath $destPath -Force
    
    # Replace placeholders
    $content = Get-Content $destPath -Raw
    $content = $content -replace "\{\{PRODUCT_NAME\}\}", $Config.Name
    $content = $content -replace "\{\{REPO_NAME\}\}", $Config.RepoName
    $content = $content -replace "\{\{EDITION\}\}", $Config.Edition
    $content = $content -replace "\{\{DATE\}\}", (Get-Date -Format "yyyy-MM-dd")
    Set-Content -Path $destPath -Value $content
    
    Write-Success "Created .github/copilot-instructions.md"
} else {
    Write-Warning "Template not found: $templatePath"
}

# -----------------------------------------------------------------------------
# Step 8: Create test file
# -----------------------------------------------------------------------------

Write-Step "Creating test file"

$testPath = Join-Path $TargetPath "server/tests/test_health.py"
$testContent = @"
"""
Health endpoint tests - REQUIRED for all spin-offs.

Verifies edition tag is correctly set.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    """Health endpoint returns 200."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_edition_tag():
    """Health endpoint returns correct edition tag."""
    response = client.get("/health")
    data = response.json()
    
    assert "edition" in data
    assert data["edition"] == "$($Config.Edition)"
    assert data["status"] == "ok"


def test_root_returns_app_info():
    """Root endpoint returns app information."""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert "app" in data
    assert "edition" in data
"@

Set-Content -Path $testPath -Value $testContent
Write-Success "Created test_health.py"

# -----------------------------------------------------------------------------
# Step 9: Create pytest.ini
# -----------------------------------------------------------------------------

$pytestIniPath = Join-Path $TargetPath "server/pytest.ini"
$pytestIniContent = @"
[pytest]
python_files = test_*.py
python_classes = Test*
python_functions = test_*
testpaths = tests
addopts = -v
"@

Set-Content -Path $pytestIniPath -Value $pytestIniContent
Write-Success "Created pytest.ini"

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  Extraction Complete!                                        ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Green

Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "  1. cd $TargetPath/server"
Write-Host "  2. python -m venv venv"
Write-Host "  3. .\venv\Scripts\Activate.ps1"
Write-Host "  4. pip install -r requirements.txt"
Write-Host "  5. Review and fix any '# REMOVED:' comments in source files"
Write-Host "  6. Update main.py to import and mount your routers"
Write-Host "  7. pytest tests/ -v"
Write-Host "  8. uvicorn app.main:app --reload"

Write-Host "`nFiles requiring manual review:" -ForegroundColor Yellow
Get-ChildItem -Path $TargetPath -Recurse -Include "*.py" | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    if ($content -match "# REMOVED:") {
        Write-Host "  - $($_.FullName)" -ForegroundColor Red
    }
}
