# Product Repository Validation Script
# Tests all 9 product repositories after creation
# Validates: venv, dependencies, server startup, edition flags

<#
.SYNOPSIS
Validates all product repositories after creation.

.DESCRIPTION
This script tests:
1. Python venv exists and is functional
2. Dependencies installed (fastapi, uvicorn, pydantic, python-dotenv)
3. Server starts and responds on unique ports
4. Edition flags are correct
5. Directory structure is valid

.PARAMETER RepoNames
Array of repository names to test. Defaults to all 9 products.

.PARAMETER Quick
If specified, only tests server startup without dependency checks.

.EXAMPLE
.\Test-ProductRepos.ps1
Tests all 9 repositories.

.EXAMPLE
.\Test-ProductRepos.ps1 -RepoNames @("ltb-express", "ltb-pro")
Tests only Express and Pro editions.

.EXAMPLE
.\Test-ProductRepos.ps1 -Quick
Fast validation (startup only).
#>

param(
    [string[]]$RepoNames = @(
        "ltb-express",
        "ltb-pro", 
        "ltb-enterprise",
        "ltb-parametric-guitar",
        "ltb-neck-designer",
        "ltb-headstock-designer",
        "ltb-bridge-designer",
        "ltb-fingerboard-designer",
        "blueprint-reader"
    ),
    [switch]$Quick
)

$ErrorActionPreference = "Continue"
$ProductsBasePath = Split-Path $PSScriptRoot -Parent
$TestResults = @()

# Expected editions for validation
$EditionMap = @{
    "ltb-express" = "EXPRESS"
    "ltb-pro" = "PRO"
    "ltb-enterprise" = "ENTERPRISE"
    "ltb-parametric-guitar" = "PARAMETRIC"
    "ltb-neck-designer" = "NECK_DESIGNER"
    "ltb-headstock-designer" = "HEADSTOCK_DESIGNER"
    "ltb-bridge-designer" = "BRIDGE_DESIGNER"
    "ltb-fingerboard-designer" = "FINGERBOARD_DESIGNER"
    "blueprint-reader" = "BLUEPRINT_READER"
}

function Write-TestHeader {
    param([string]$RepoName)
    Write-Host "`n╔═══════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║  Testing: $($RepoName.PadRight(56)) ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
}

function Write-TestResult {
    param([string]$Test, [bool]$Passed, [string]$Message = "")
    $icon = if ($Passed) { "✓" } else { "✗" }
    $color = if ($Passed) { "Green" } else { "Red" }
    $output = "  $icon $Test"
    if ($Message) { $output += " - $Message" }
    Write-Host $output -ForegroundColor $color
}

function Test-ProductRepo {
    param(
        [string]$RepoName,
        [int]$PortOffset
    )
    
    Write-TestHeader -RepoName $RepoName
    
    $repoPath = Join-Path $ProductsBasePath $RepoName
    $result = @{
        RepoName = $RepoName
        DirectoryExists = $false
        VenvExists = $false
        DependenciesInstalled = $false
        ServerStarts = $false
        EditionCorrect = $false
        Port = 8000 + $PortOffset
        Errors = @()
    }
    
    # Test 1: Directory exists
    if (Test-Path $repoPath) {
        $result.DirectoryExists = $true
        Write-TestResult "Repository directory exists" $true
    } else {
        $result.DirectoryExists = $false
        $result.Errors += "Repository directory not found at $repoPath"
        Write-TestResult "Repository directory exists" $false $repoPath
        return $result
    }
    
    $serverPath = Join-Path $repoPath "server"
    
    # Test 2: Venv exists
    $venvPath = Join-Path $serverPath ".venv\Scripts\Activate.ps1"
    if (Test-Path $venvPath) {
        $result.VenvExists = $true
        Write-TestResult "Python venv exists" $true
    } else {
        $result.VenvExists = $false
        $result.Errors += "Venv not found at $venvPath"
        Write-TestResult "Python venv exists" $false
        return $result
    }
    
    # Test 3: Dependencies installed (skip if Quick mode)
    if (-not $Quick) {
        Push-Location $serverPath
        try {
            & ".venv\Scripts\Activate.ps1"
            $pipList = pip list 2>&1 | Out-String
            
            $requiredPackages = @("fastapi", "uvicorn", "pydantic", "python-dotenv")
            $allInstalled = $true
            $missingPackages = @()
            
            foreach ($package in $requiredPackages) {
                if ($pipList -notmatch $package) {
                    $allInstalled = $false
                    $missingPackages += $package
                }
            }
            
            if ($allInstalled) {
                $result.DependenciesInstalled = $true
                Write-TestResult "Dependencies installed" $true "fastapi, uvicorn, pydantic, python-dotenv"
            } else {
                $result.DependenciesInstalled = $false
                $result.Errors += "Missing packages: $($missingPackages -join ', ')"
                Write-TestResult "Dependencies installed" $false "Missing: $($missingPackages -join ', ')"
            }
            
            # Check requirements.txt exists
            if (Test-Path "requirements.txt") {
                Write-TestResult "requirements.txt generated" $true
            } else {
                Write-TestResult "requirements.txt generated" $false
            }
            
        } catch {
            $result.DependenciesInstalled = $false
            $result.Errors += "Failed to check dependencies: $($_.Exception.Message)"
            Write-TestResult "Dependencies installed" $false $_.Exception.Message
        } finally {
            Pop-Location
        }
    }
    
    # Test 4: Server starts and responds
    Push-Location $serverPath
    try {
        # Start server in background
        $port = $result.Port
        $serverProcess = Start-Process pwsh -ArgumentList "-Command", "& '.venv\Scripts\Activate.ps1'; uvicorn app.main:app --port $port" -PassThru -WindowStyle Hidden
        
        # Wait for server to start
        Start-Sleep -Seconds 3
        
        # Test endpoint
        try {
            $response = Invoke-RestMethod "http://localhost:$port/" -ErrorAction Stop
            
            if ($response.status -eq "ready") {
                $result.ServerStarts = $true
                Write-TestResult "Server starts and responds" $true "http://localhost:$port/"
                
                # Test 5: Edition correct
                $expectedEdition = $EditionMap[$RepoName]
                if ($response.edition -eq $expectedEdition) {
                    $result.EditionCorrect = $true
                    Write-TestResult "Edition flag correct" $true "$($response.edition)"
                } else {
                    $result.EditionCorrect = $false
                    $result.Errors += "Edition mismatch: expected $expectedEdition, got $($response.edition)"
                    Write-TestResult "Edition flag correct" $false "Expected: $expectedEdition, Got: $($response.edition)"
                }
            } else {
                $result.ServerStarts = $false
                $result.Errors += "Server responded but status not 'ready'"
                Write-TestResult "Server starts and responds" $false "Status: $($response.status)"
            }
        } catch {
            $result.ServerStarts = $false
            $result.Errors += "Failed to connect to server: $($_.Exception.Message)"
            Write-TestResult "Server starts and responds" $false $_.Exception.Message
        }
        
        # Stop server
        Stop-Process -Id $serverProcess.Id -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
        
    } catch {
        $result.ServerStarts = $false
        $result.Errors += "Failed to start server: $($_.Exception.Message)"
        Write-TestResult "Server starts and responds" $false $_.Exception.Message
    } finally {
        Pop-Location
    }
    
    return $result
}

# -----------------------------------------------------------------------------
# Main Execution
# -----------------------------------------------------------------------------

Write-Host @"

╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   Product Repository Validation Suite                            ║
║                                                                   ║
║   Testing $($RepoNames.Count) repositories                                            ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

if ($Quick) {
    Write-Host "QUICK MODE: Skipping dependency checks`n" -ForegroundColor Yellow
}

Write-Host "Base path: $ProductsBasePath`n" -ForegroundColor Gray

# Test each repository
$portOffset = 0
foreach ($repoName in $RepoNames) {
    $result = Test-ProductRepo -RepoName $repoName -PortOffset $portOffset
    $TestResults += $result
    $portOffset++
}

# Summary
Write-Host "`n╔═══════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Test Summary                                                     ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

$totalTests = $TestResults.Count
$passedRepos = ($TestResults | Where-Object { $_.ServerStarts -and $_.EditionCorrect }).Count
$failedRepos = $totalTests - $passedRepos

Write-Host "`nRepositories Tested: $totalTests" -ForegroundColor White
Write-Host "Passed (Server + Edition): $passedRepos" -ForegroundColor Green
Write-Host "Failed: $failedRepos" -ForegroundColor $(if ($failedRepos -eq 0) { "Gray" } else { "Red" })

# Detailed results table
Write-Host "`nDetailed Results:" -ForegroundColor Yellow
Write-Host ("─" * 100) -ForegroundColor Gray
Write-Host $("{0,-30} {1,-8} {2,-8} {3,-12} {4,-10} {5,-10}" -f "Repository", "Dir", "Venv", "Dependencies", "Server", "Edition") -ForegroundColor White
Write-Host ("─" * 100) -ForegroundColor Gray

foreach ($result in $TestResults) {
    $dirIcon = if ($result.DirectoryExists) { "✓" } else { "✗" }
    $venvIcon = if ($result.VenvExists) { "✓" } else { "✗" }
    $depsIcon = if ($Quick) { "-" } elseif ($result.DependenciesInstalled) { "✓" } else { "✗" }
    $serverIcon = if ($result.ServerStarts) { "✓" } else { "✗" }
    $editionIcon = if ($result.EditionCorrect) { "✓" } else { "✗" }
    
    $color = if ($result.ServerStarts -and $result.EditionCorrect) { "Green" } else { "Red" }
    
    Write-Host $("{0,-30} {1,-8} {2,-8} {3,-12} {4,-10} {5,-10}" -f `
        $result.RepoName, $dirIcon, $venvIcon, $depsIcon, $serverIcon, $editionIcon) -ForegroundColor $color
}

Write-Host ("─" * 100) -ForegroundColor Gray

# Errors
$totalErrors = ($TestResults | ForEach-Object { $_.Errors.Count } | Measure-Object -Sum).Sum
if ($totalErrors -gt 0) {
    Write-Host "`n⚠ Errors Encountered: $totalErrors" -ForegroundColor Red
    foreach ($result in $TestResults) {
        if ($result.Errors.Count -gt 0) {
            Write-Host "`n$($result.RepoName):" -ForegroundColor Yellow
            foreach ($error in $result.Errors) {
                Write-Host "  • $error" -ForegroundColor Red
            }
        }
    }
}

# Final verdict
Write-Host ""
if ($failedRepos -eq 0) {
    Write-Host "✅ ALL REPOSITORIES PASSED VALIDATION" -ForegroundColor Green
    Write-Host "Ready to proceed with feature extraction (Phase 1 Week 1)" -ForegroundColor Gray
    exit 0
} else {
    Write-Host "❌ $failedRepos REPOSITORIES FAILED VALIDATION" -ForegroundColor Red
    Write-Host "Review errors above and fix before proceeding" -ForegroundColor Yellow
    exit 1
}
