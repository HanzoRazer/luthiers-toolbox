# Test Dummy Repository Creation Script
# Creates a single test repository to validate the creation workflow
# Run this BEFORE creating all 9 production repos

<#
.SYNOPSIS
Creates a test dummy repository to validate repo creation workflow.

.DESCRIPTION
This script creates a single "ltb-test-dummy" repository with the same
process as the production script, allowing safe validation before
creating all 9 real product repositories.

.PARAMETER CleanupAfter
If specified, deletes the test repo after validation.

.EXAMPLE
.\Create-TestDummy.ps1
Creates test dummy repo.

.EXAMPLE
.\Create-TestDummy.ps1 -CleanupAfter
Creates, tests, then deletes the dummy repo.
#>

param(
    [switch]$CleanupAfter
)

$ErrorActionPreference = "Stop"
$OwnerOrg = "HanzoRazer"
$GoldenMasterPath = $PSScriptRoot
$ProductsBasePath = Split-Path $PSScriptRoot -Parent
$RepoName = "ltb-test-dummy"
$FullRepoName = "$OwnerOrg/$RepoName"

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

function Write-Error {
    param([string]$Message)
    Write-Host "     ✗ $Message" -ForegroundColor Red
}

Write-Host @"

╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   Test Dummy Repository Creator                                  ║
║                                                                   ║
║   Validates repo creation workflow before production run         ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

# Pre-flight checks
Write-Status "Pre-flight checks" -Color Yellow

try {
    $ghVersion = gh --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "GitHub CLI installed: $($ghVersion[0])"
    }
} catch {
    Write-Error "GitHub CLI (gh) not found"
    Write-Info "Install with: winget install --id GitHub.cli"
    exit 1
}

try {
    $authStatus = gh auth status 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "GitHub CLI authenticated"
    }
} catch {
    Write-Error "GitHub CLI not authenticated"
    Write-Info "Authenticate with: gh auth login"
    exit 1
}

Write-Success "All pre-flight checks passed"

# Check if dummy already exists
Write-Status "Checking for existing test dummy" -Color Yellow
try {
    $result = gh repo view $FullRepoName 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Info "Test dummy repository already exists: $FullRepoName"
        $response = Read-Host "Delete and recreate? (yes/no)"
        if ($response -eq "yes") {
            Write-Info "Deleting existing repository..."
            gh repo delete $FullRepoName --yes
            Start-Sleep -Seconds 2
            Write-Success "Existing repository deleted"
        } else {
            Write-Info "Exiting without changes"
            exit 0
        }
    }
} catch {
    Write-Info "No existing test dummy found (good)"
}

# Create test dummy repository
Write-Status "Creating test dummy repository" -Color Yellow

try {
    # Create GitHub repository
    Write-Info "Creating GitHub repository: $FullRepoName"
    gh repo create $FullRepoName `
        --public `
        --description "Test dummy for validating Luthier's ToolBox repo creation workflow" `
        --clone
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create repository"
    }
    
    Write-Success "Repository created and cloned"
    
    # Navigate to repo
    $repoPath = Join-Path $ProductsBasePath $RepoName
    Push-Location $repoPath
    
    try {
        # Add topics
        Write-Info "Adding topics..."
        gh repo edit --add-topic "test" --add-topic "luthier" 2>&1 | Out-Null
        
        # Create minimal directory structure
        Write-Info "Creating minimal directory structure..."
        New-Item -ItemType Directory -Force -Path "client/src" | Out-Null
        New-Item -ItemType Directory -Force -Path "server/app" | Out-Null
        New-Item -ItemType Directory -Force -Path "docs" | Out-Null
        
        # Create minimal server main.py
        Write-Info "Creating minimal placeholder files..."
        $minimalServerContent = @"
# ltb-test-dummy - Server Entry Point
# Test dummy for validation

from fastapi import FastAPI

app = FastAPI(
    title="LTB Test Dummy",
    version="0.1.0"
)

@app.get("/")
def read_root():
    return {"status": "ready", "edition": "TEST_DUMMY"}
"@
        $minimalServerContent | Out-File -FilePath "server/app/main.py" -Encoding UTF8
        
        # Create minimal client index.html
        $minimalClientContent = @"
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>LTB Test Dummy</title>
  </head>
  <body>
    <div id="app">
      <h1>LTB Test Dummy</h1>
      <p>Test repository for validation workflow.</p>
    </div>
  </body>
</html>
"@
        $minimalClientContent | Out-File -FilePath "client/index.html" -Encoding UTF8
        
        # Create .env.example
        $envContent = @"
# Environment configuration for ltb-test-dummy
PORT=8000
ENVIRONMENT=development
EDITION=TEST_DUMMY
"@
        $envContent | Out-File -FilePath "server/.env.example" -Encoding UTF8
        
        # Install Python dependencies
        Write-Info "Installing Python dependencies (this may take 2-3 minutes)..."
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
            Write-Error "Failed to install Python dependencies: $($_.Exception.Message)"
            Write-Info "You can install manually later"
        } finally {
            Pop-Location
        }
        
        # Create README
        Write-Info "Creating README.md..."
        $readmeContent = @"
# ltb-test-dummy

Test dummy repository for validating Luthier's ToolBox repo creation workflow.

## Purpose

This repository tests the automated creation process before running it on all 9 production repositories.

## Quick Test

### Server
``````powershell
cd server
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
``````

Visit: http://localhost:8000/

Expected response:
``````json
{"status": "ready", "edition": "TEST_DUMMY"}
``````

## Validation Checklist

- [ ] Repository created on GitHub
- [ ] Cloned locally
- [ ] Directory structure correct
- [ ] Python venv created
- [ ] Dependencies installed
- [ ] requirements.txt generated
- [ ] Server starts successfully
- [ ] Edition flag correct

## Cleanup

After validation, delete this repository:
``````powershell
gh repo delete $FullRepoName --yes
``````
"@
        $readmeContent | Out-File -FilePath "README.md" -Encoding UTF8
        
        # Create .gitignore
        Write-Info "Creating .gitignore..."
        $gitignoreContent = @"
# Python
__pycache__/
*.py[cod]
.venv/
*.egg-info/

# Node
node_modules/
dist/

# Environment
.env

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
"@
        $gitignoreContent | Out-File -FilePath ".gitignore" -Encoding UTF8
        
        # Initial commit
        Write-Info "Creating initial commit..."
        git add .
        git commit -m "Initial test dummy structure

- Minimal server skeleton (FastAPI)
- Minimal client placeholder (HTML)
- Python venv + dependencies
- Environment configuration
- Documentation

Generated by: Create-TestDummy.ps1"
        
        # Push to GitHub
        Write-Info "Pushing to GitHub..."
        git push -u origin main
        
        Write-Success "Test dummy repository complete!"
        
    } finally {
        Pop-Location
    }
    
} catch {
    Write-Error "Failed to create test dummy: $($_.Exception.Message)"
    exit 1
}

# Test the repository
Write-Status "Testing repository" -Color Yellow

Push-Location (Join-Path $ProductsBasePath $RepoName "server")
try {
    Write-Info "Starting test server..."
    $serverProcess = Start-Process pwsh -ArgumentList "-Command", "& '.venv\Scripts\Activate.ps1'; uvicorn app.main:app --port 8000" -PassThru -WindowStyle Hidden
    
    Start-Sleep -Seconds 3
    
    try {
        $response = Invoke-RestMethod "http://localhost:8000/" -ErrorAction Stop
        
        if ($response.status -eq "ready" -and $response.edition -eq "TEST_DUMMY") {
            Write-Success "Server responds correctly"
            Write-Info "Response: $($response | ConvertTo-Json -Compress)"
        } else {
            Write-Error "Server response unexpected: $($response | ConvertTo-Json)"
        }
    } catch {
        Write-Error "Failed to connect to server: $($_.Exception.Message)"
    }
    
    Stop-Process -Id $serverProcess.Id -Force -ErrorAction SilentlyContinue
    
} finally {
    Pop-Location
}

# Summary
Write-Status "Validation Complete" -Color Green
Write-Host ""
Write-Host "✅ Test dummy repository created and validated" -ForegroundColor Green
Write-Host ""
Write-Host "Location: $ProductsBasePath\$RepoName" -ForegroundColor Gray
Write-Host "GitHub: https://github.com/$FullRepoName" -ForegroundColor Gray
Write-Host ""

if ($CleanupAfter) {
    Write-Status "Cleanup" -Color Yellow
    $response = Read-Host "Delete test dummy repository? (yes/no)"
    if ($response -eq "yes") {
        Write-Info "Deleting test dummy..."
        gh repo delete $FullRepoName --yes
        Remove-Item -Path (Join-Path $ProductsBasePath $RepoName) -Recurse -Force
        Write-Success "Test dummy deleted"
    }
} else {
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Review the test dummy repo manually" -ForegroundColor Gray
    Write-Host "  2. If satisfied, delete it: gh repo delete $FullRepoName --yes" -ForegroundColor Gray
    Write-Host "  3. Run production script: .\scripts\Create-ProductRepos.ps1" -ForegroundColor Gray
}

Write-Host ""
