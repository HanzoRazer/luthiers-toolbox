# GitHub Repository Creation Script
# Automates creation of all 9 product repositories for Luthier's ToolBox ecosystem
# Requires: GitHub CLI (gh) installed and authenticated

<#
.SYNOPSIS
Creates all 9 product repositories with initial scaffolding.

.DESCRIPTION
This script automates:
1. GitHub repository creation (public repos)
2. Local cloning
3. Directory structure setup
4. Minimal file generation (lean extraction strategy)
5. Python venv creation and dependency installation
6. Requirements.txt generation
7. Initial commit and push

.PARAMETER DryRun
If specified, shows what would be created without actually creating repos.

.EXAMPLE
.\Create-ProductRepos.ps1
Creates all 9 repos with scaffolding.

.EXAMPLE
.\Create-ProductRepos.ps1 -DryRun
Shows what would be created without making changes.
#>

param(
    [switch]$DryRun
)

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

$ErrorActionPreference = "Stop"
$OwnerOrg = "HanzoRazer"
$GoldenMasterPath = $PSScriptRoot
$ProductsBasePath = Split-Path $PSScriptRoot -Parent

# Product definitions
$Products = @(
    @{
        Name = "ltb-express"
        Description = "Luthier's ToolBox Express Edition - Design-focused tools for hobbyists and guitar players"
        Edition = "EXPRESS"
        Template = "express"
        Topics = @("guitar", "luthier", "cad", "design-tools", "express-edition")
    },
    @{
        Name = "ltb-pro"
        Description = "Luthier's ToolBox Pro Edition - Full CAM workstation for professional luthiers"
        Edition = "PRO"
        Template = "pro"
        Topics = @("guitar", "luthier", "cam", "cnc", "pro-edition")
    },
    @{
        Name = "ltb-enterprise"
        Description = "Luthier's ToolBox Enterprise Edition - Complete shop operating system for guitar businesses"
        Edition = "ENTERPRISE"
        Template = "enterprise"
        Topics = @("guitar", "luthier", "erp", "business", "enterprise")
    },
    @{
        Name = "ltb-parametric-guitar"
        Description = "LTB Parametric Guitar Designer - Body shape generator and template exporter"
        Edition = "PARAMETRIC"
        Template = "parametric"
        Topics = @("guitar", "parametric-design", "templates", "etsy")
    },
    @{
        Name = "ltb-neck-designer"
        Description = "LTB Neck Designer - Parametric neck profile generator with Fender/Gibson presets"
        Edition = "NECK_DESIGNER"
        Template = "neck"
        Topics = @("guitar", "neck-design", "parametric", "templates")
    },
    @{
        Name = "ltb-headstock-designer"
        Description = "LTB Headstock Designer - Headstock layout tool with tuner positioning"
        Edition = "HEADSTOCK_DESIGNER"
        Template = "headstock"
        Topics = @("guitar", "headstock", "design-tools", "templates")
    },
    @{
        Name = "ltb-bridge-designer"
        Description = "LTB Bridge Designer - Bridge geometry and string spacing calculator"
        Edition = "BRIDGE_DESIGNER"
        Template = "bridge"
        Topics = @("guitar", "bridge-design", "templates", "cnc")
    },
    @{
        Name = "ltb-fingerboard-designer"
        Description = "LTB Fingerboard Designer - Fingerboard radius, scale, and multiscale calculator"
        Edition = "FINGERBOARD_DESIGNER"
        Template = "fingerboard"
        Topics = @("guitar", "fingerboard", "fretboard", "templates")
    },
    @{
        Name = "blueprint-reader"
        Description = "Blueprint Reader - Blueprint import, vectorization, and CAM integration"
        Edition = "BLUEPRINT_READER"
        Template = "blueprint"
        Topics = @("blueprint", "vectorization", "image-processing", "cam")
    }
)

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

function Write-Status {
    param([string]$Message, [string]$Color = "Cyan")
    Write-Host "`n===> $Message" -ForegroundColor $Color
}

function Write-Info {
    param([string]$Message)
    Write-Host "     $Message" -ForegroundColor Gray
}

function Write-Success {
    param([string]$Message)
    Write-Host "     ✓ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "     ⚠ $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "     ✗ $Message" -ForegroundColor Red
}

function Test-GitHubCLI {
    try {
        $ghVersion = gh --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "GitHub CLI installed: $($ghVersion[0])"
            return $true
        }
    } catch {
        Write-Error "GitHub CLI (gh) not found"
        Write-Info "Install with: winget install --id GitHub.cli"
        return $false
    }
}

function Test-GitHubAuth {
    try {
        $authStatus = gh auth status 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "GitHub CLI authenticated"
            return $true
        }
    } catch {
        Write-Error "GitHub CLI not authenticated"
        Write-Info "Authenticate with: gh auth login"
        return $false
    }
}

function Test-RepoExists {
    param([string]$RepoName)
    
    try {
        $result = gh repo view "$OwnerOrg/$RepoName" 2>&1
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function New-ProductRepository {
    param(
        [hashtable]$Product,
        [switch]$DryRun
    )
    
    $repoName = $Product.Name
    $fullRepoName = "$OwnerOrg/$repoName"
    
    Write-Status "Processing: $repoName"
    
    # Check if repo already exists
    if (Test-RepoExists -RepoName $repoName) {
        Write-Warning "Repository $fullRepoName already exists - skipping"
        return
    }
    
    if ($DryRun) {
        Write-Info "[DRY RUN] Would create repo: $fullRepoName"
        Write-Info "[DRY RUN] Description: $($Product.Description)"
        Write-Info "[DRY RUN] Topics: $($Product.Topics -join ', ')"
        return
    }
    
    # Create GitHub repository
    Write-Info "Creating GitHub repository..."
    $topicsArg = $Product.Topics -join ","
    
    try {
        gh repo create $fullRepoName `
            --public `
            --description $Product.Description `
            --clone
        
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to create repository"
        }
        
        Write-Success "Repository created and cloned"
        
        # Navigate to repo directory
        $repoPath = Join-Path $ProductsBasePath $repoName
        Push-Location $repoPath
        
        try {
            # Add topics (GitHub CLI doesn't support topics in create command)
            Write-Info "Adding topics..."
            foreach ($topic in $Product.Topics) {
                gh repo edit --add-topic $topic 2>&1 | Out-Null
            }
            
            # Create minimal directory structure
            Write-Info "Creating minimal directory structure..."
            New-Item -ItemType Directory -Force -Path "client/src" | Out-Null
            New-Item -ItemType Directory -Force -Path "server/app" | Out-Null
            New-Item -ItemType Directory -Force -Path "docs" | Out-Null
            
            # Create minimal placeholder files (no template copying)
            Write-Info "Creating minimal placeholder files..."
            
            # Server: Minimal main.py placeholder
            $minimalServerContent = @"
# $($Product.Name) - Server Entry Point
# Extract features from golden master as needed
# Golden Master: https://github.com/$OwnerOrg/luthiers-toolbox

from fastapi import FastAPI

app = FastAPI(
    title=""$($Product.Description)"",
    version=""0.1.0""
)

@app.get("/")
def read_root():
    return {"status": "ready", "edition": "$($Product.Edition)"}
"@
            $minimalServerContent | Out-File -FilePath "server/app/main.py" -Encoding UTF8
            
            # Client: Minimal index.html placeholder
            $minimalClientContent = @"
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>$($Product.Name)</title>
  </head>
  <body>
    <div id="app">
      <h1>$($Product.Description)</h1>
      <p>Extract features from golden master as needed.</p>
    </div>
  </body>
</html>
"@
            $minimalClientContent | Out-File -FilePath "client/index.html" -Encoding UTF8
            
            # Create minimal .env.example
            $envContent = @"
# Environment configuration for $($Product.Name)
# Copy to .env and customize

PORT=8000
ENVIRONMENT=development
EDITION=$($Product.Edition)
"@
            $envContent | Out-File -FilePath "server/.env.example" -Encoding UTF8
            
            # Install server dependencies
            Write-Info "Installing Python dependencies..."
            Push-Location "server"
            try {
                # Create virtual environment
                python -m venv .venv
                
                # Activate and install dependencies
                & ".venv\Scripts\Activate.ps1"
                pip install --quiet fastapi uvicorn pydantic python-dotenv
                
                # Generate requirements.txt
                pip freeze > requirements.txt
                
                Write-Success "Python environment ready (fastapi, uvicorn, pydantic, python-dotenv)"
            } catch {
                Write-Warning "Failed to install Python dependencies: $($_.Exception.Message)"
                Write-Info "You can install manually later with: pip install fastapi uvicorn pydantic python-dotenv"
            } finally {
                Pop-Location
            }
            
            # Create README.md
            Write-Info "Creating README.md..."
            $readmeContent = @"
# $($Product.Name)

$($Product.Description)

## Status

🚧 **Minimal Skeleton** - Features extracted from golden master as needed.

**Strategy:** Lean extraction (no template stubs)  
**Approach:** Clean slate → Extract specific features incrementally  
**Benefit:** Only includes code that's actually implemented

## Quick Start

### Server (FastAPI)

**Dependencies already installed!** Just activate and run:

``````powershell
cd server
.\.venv\Scripts\Activate.ps1
copy .env.example .env
uvicorn app.main:app --reload
``````

**If you need to reinstall:**

``````powershell
cd server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
``````

### Client Setup

``````powershell
cd client
npm create vite@latest . -- --template vue-ts
npm install
npm run dev
``````

## Extracting Features

1. Identify feature in [Golden Master](https://github.com/$OwnerOrg/luthiers-toolbox)
2. Copy specific files/components needed
3. Strip unnecessary features (downgrade to edition tier)
4. Test extraction
5. Commit with clear feature description

## Documentation

- [Product Segmentation Strategy](https://github.com/$OwnerOrg/luthiers-toolbox/blob/main/docs/products/MASTER_SEGMENTATION_STRATEGY.md)
- [Setup Guide](https://github.com/$OwnerOrg/luthiers-toolbox/blob/main/PRODUCT_REPO_SETUP.md)

## Related Repositories

- [Golden Master](https://github.com/$OwnerOrg/luthiers-toolbox) - Main repository with templates and documentation
- [Express Edition](https://github.com/$OwnerOrg/ltb-express)
- [Pro Edition](https://github.com/$OwnerOrg/ltb-pro)
- [Enterprise Edition](https://github.com/$OwnerOrg/ltb-enterprise)

## License

Copyright © 2025 Luthier's ToolBox Project
"@
            
            $readmeContent | Out-File -FilePath "README.md" -Encoding UTF8
            
            # Create .gitignore
            Write-Info "Creating .gitignore..."
            $gitignoreContent = @"
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
ENV/
env/
*.egg-info/
dist/
build/

# Node
node_modules/
dist/
*.log
.DS_Store

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# Database
*.db
*.sqlite
*.sqlite3

# OS
Thumbs.db
.DS_Store
"@
            
            $gitignoreContent | Out-File -FilePath ".gitignore" -Encoding UTF8
            
            # Initial commit
            Write-Info "Creating initial commit..."
            git add .
            git commit -m "Initial repository structure (lean extraction strategy)

- Minimal server skeleton (FastAPI entry point)
- Minimal client skeleton (HTML placeholder)
- Environment configuration template
- Directory structure for feature extraction
- Documentation

NOTE: Features will be extracted from golden master as needed.
No template stubs copied - clean slate for incremental growth.

Generated by: Create-ProductRepos.ps1
Golden Master: https://github.com/$OwnerOrg/luthiers-toolbox"
            
            # Push to GitHub
            Write-Info "Pushing to GitHub..."
            git push -u origin main
            
            Write-Success "Repository $repoName complete!"
            
        } finally {
            Pop-Location
        }
        
    } catch {
        Write-Error "Failed to create ${repoName}: $($_.Exception.Message)"
    }
}

# -----------------------------------------------------------------------------
# Main Script
# -----------------------------------------------------------------------------

Write-Host @"

╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   Luthier's ToolBox Product Repository Creator                   ║
║                                                                   ║
║   Creates 9 product repositories with initial scaffolding        ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

# Pre-flight checks
Write-Status "Pre-flight checks" -Color Yellow

if (-not (Test-GitHubCLI)) {
    Write-Error "GitHub CLI is required. Install with: winget install --id GitHub.cli"
    exit 1
}

if (-not (Test-GitHubAuth)) {
    Write-Error "GitHub CLI authentication required. Run: gh auth login"
    exit 1
}

Write-Success "All pre-flight checks passed"

# Show summary
Write-Status "Repository Plan" -Color Yellow
Write-Info "Owner/Org: $OwnerOrg"
Write-Info "Products to create: $($Products.Count)"
Write-Info "Golden master path: $GoldenMasterPath"
Write-Info "Products base path: $ProductsBasePath"

if ($DryRun) {
    Write-Warning "DRY RUN MODE - No repositories will be created"
}

# Confirm unless dry run
if (-not $DryRun) {
    Write-Host "`n"
    $confirmation = Read-Host "Create $($Products.Count) repositories? (yes/no)"
    if ($confirmation -ne "yes") {
        Write-Warning "Operation cancelled by user"
        exit 0
    }
}

# Create repositories
Write-Status "Creating Repositories" -Color Yellow

$successCount = 0
$skipCount = 0
$failCount = 0

foreach ($product in $Products) {
    try {
        New-ProductRepository -Product $product -DryRun:$DryRun
        
        if ($DryRun) {
            $successCount++
        } elseif (Test-RepoExists -RepoName $product.Name) {
            if ((Get-Item (Join-Path $ProductsBasePath $product.Name) -ErrorAction SilentlyContinue)) {
                $successCount++
            } else {
                $skipCount++
            }
        }
    } catch {
        $failCount++
        Write-Error "Failed to process $($product.Name): $_"
    }
}

# Summary
Write-Status "Summary" -Color Yellow
Write-Info "Total products: $($Products.Count)"
Write-Success "Created: $successCount"
if ($skipCount -gt 0) {
    Write-Warning "Skipped: $skipCount"
}
if ($failCount -gt 0) {
    Write-Error "Failed: $failCount"
}

if ($DryRun) {
    Write-Host "`n"
    Write-Warning "This was a DRY RUN - no repositories were created"
    Write-Info "Run without -DryRun to actually create repositories"
} else {
    Write-Host "`n"
    Write-Success "Repository creation complete!"
    Write-Info "Next steps:"
    Write-Info "  1. Navigate to each repo and complete setup"
    Write-Info "  2. Install dependencies (npm install, pip install)"
    Write-Info "  3. Configure .env files"
    Write-Info "  4. Begin Phase 1 implementation"
}

Write-Host ""
