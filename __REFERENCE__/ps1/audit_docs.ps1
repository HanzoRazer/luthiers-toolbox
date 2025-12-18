# ============================================================
# DOCUMENTATION AUDIT SCRIPT
# ============================================================
# Purpose: Find stray markdown files not in the docs/ hierarchy
# Usage: Run periodically to maintain documentation organization
#
#   cd C:\Users\thepr\Downloads\luthiers-toolbox
#   .\audit_docs.ps1
#
# Safe to run repeatedly - only reports, never moves files
# ============================================================

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DOCUMENTATION AUDIT" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Validate working directory
$requiredMarkers = @(".git", "services", "packages", "docs")
foreach ($marker in $requiredMarkers) {
    if (-not (Test-Path $marker)) {
        Write-Host "ERROR: Not in repository root! Missing: $marker" -ForegroundColor Red
        Write-Host "Run from: C:\Users\thepr\Downloads\luthiers-toolbox" -ForegroundColor Yellow
        exit 1
    }
}
Write-Host "Working directory: $(Get-Location)" -ForegroundColor Green
Write-Host ""

# ============================================================
# CONFIGURATION
# ============================================================

# Files that are ALLOWED in root (exceptions)
$allowedRootFiles = @(
    "README.md",
    "CHANGELOG.md",
    "LICENSE.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CODE_OF_CONDUCT.md",
    "CANONICAL_GOVERNANCE_INDEX.md"
)

# Directories to skip entirely
$skipDirs = @(
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    "Governance_Code_Bundle"
)

# Classification rules (pattern -> suggested location)
$classificationRules = @(
    @{pattern="GOVERNANCE"; dest="docs/canonical/governance/"; tier="CANONICAL"},
    @{pattern="SAFETY"; dest="docs/canonical/governance/"; tier="CANONICAL"},
    @{pattern="POLICY"; dest="docs/canonical/governance/"; tier="CANONICAL"},
    @{pattern="SPEC"; dest="docs/canonical/"; tier="CANONICAL"},
    @{pattern="ARCHITECTURE"; dest="docs/canonical/"; tier="CANONICAL"},
    @{pattern="QUICKREF"; dest="docs/quickref/general/"; tier="QUICKREF"},
    @{pattern="QUICKSTART"; dest="docs/quickref/general/"; tier="QUICKREF"},
    @{pattern="ROADMAP"; dest="docs/quickref/general/"; tier="QUICKREF"},
    @{pattern="HANDOFF"; dest="docs/archive/2025-12/handoffs/"; tier="ARCHIVE"},
    @{pattern="SESSION"; dest="docs/archive/2025-12/sessions/"; tier="ARCHIVE"},
    @{pattern="BUNDLE"; dest="docs/archive/2025-12/bundles/"; tier="ARCHIVE"},
    @{pattern="INTEGRATION"; dest="docs/archive/2025-12/integration/"; tier="ARCHIVE"},
    @{pattern="REPORT"; dest="docs/archive/2025-12/reports/"; tier="ARCHIVE"},
    @{pattern="PATCH"; dest="docs/archive/2025-12/patches/"; tier="ARCHIVE"},
    @{pattern="WAVE"; dest="docs/archive/2025-12/waves/"; tier="ARCHIVE"},
    @{pattern="PHASE"; dest="docs/archive/2025-12/phases/"; tier="ARCHIVE"},
    @{pattern="COMPLETE"; dest="docs/archive/2025-12/misc/"; tier="ARCHIVE"},
    @{pattern="EXECUTIVE"; dest="docs/archive/2025-12/reports/"; tier="ARCHIVE"}
)

# ============================================================
# FIND STRAY MARKDOWN FILES
# ============================================================

Write-Host "[PHASE 1] Scanning for stray markdown files..." -ForegroundColor Yellow
Write-Host ""

$strayFiles = @()
$properFiles = @()

# Get all .md files recursively
$allMdFiles = Get-ChildItem -Path . -Filter "*.md" -Recurse -File -ErrorAction SilentlyContinue

foreach ($file in $allMdFiles) {
    $relativePath = $file.FullName.Replace((Get-Location).Path + "\", "")

    # Skip files in excluded directories
    $skip = $false
    foreach ($skipDir in $skipDirs) {
        if ($relativePath -like "$skipDir\*" -or $relativePath -like "*\$skipDir\*") {
            $skip = $true
            break
        }
    }
    if ($skip) { continue }

    # Check if file is in docs/ hierarchy
    if ($relativePath -like "docs\*") {
        $properFiles += $relativePath
        continue
    }

    # Check if it's an allowed root file
    if ($allowedRootFiles -contains $file.Name) {
        continue
    }

    # Check if it's in packages/ or services/ (code documentation - OK)
    if ($relativePath -like "packages\*" -or $relativePath -like "services\*") {
        # These are code-level docs (like README.md in a package) - OK
        continue
    }

    # This is a stray file
    $strayFiles += $relativePath
}

# ============================================================
# CLASSIFY STRAY FILES
# ============================================================

if ($strayFiles.Count -eq 0) {
    Write-Host "[OK] No stray markdown files found!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Documentation is properly organized." -ForegroundColor Green
    Write-Host "  docs/canonical/governance/  - Binding governance docs"
    Write-Host "  docs/canonical/             - Authoritative specs"
    Write-Host "  docs/advisory/              - Pending promotion"
    Write-Host "  docs/quickref/              - Operational guides"
    Write-Host "  docs/archive/               - Historical docs"
    Write-Host ""
    exit 0
}

Write-Host "[WARNING] Found $($strayFiles.Count) stray markdown file(s)" -ForegroundColor Yellow
Write-Host ""

Write-Host "========================================" -ForegroundColor Yellow
Write-Host "STRAY FILES - Need Organization" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

$classified = @()

foreach ($file in $strayFiles) {
    $fileName = Split-Path $file -Leaf
    $fileNameUpper = $fileName.ToUpper()

    # Try to classify based on patterns
    $suggestion = $null
    $tier = "UNKNOWN"

    foreach ($rule in $classificationRules) {
        if ($fileNameUpper -like "*$($rule.pattern)*") {
            $suggestion = $rule.dest
            $tier = $rule.tier
            break
        }
    }

    if (-not $suggestion) {
        $suggestion = "docs/archive/2025-12/misc/"
        $tier = "ARCHIVE"
    }

    $classified += @{
        file = $file
        suggestion = $suggestion
        tier = $tier
    }

    # Color based on tier
    $color = switch ($tier) {
        "CANONICAL" { "Magenta" }
        "QUICKREF" { "Cyan" }
        "ARCHIVE" { "DarkGray" }
        default { "White" }
    }

    Write-Host "  [$tier]" -ForegroundColor $color -NoNewline
    Write-Host " $file"
    Write-Host "       -> $suggestion" -ForegroundColor DarkGray
}

Write-Host ""

# ============================================================
# GENERATE MOVE COMMANDS
# ============================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SUGGESTED ACTIONS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "To organize these files, run:" -ForegroundColor Yellow
Write-Host ""

foreach ($item in $classified) {
    $destDir = $item.suggestion
    $fileName = Split-Path $item.file -Leaf
    Write-Host "Move-Item -Path `"$($item.file)`" -Destination `"$destDir$fileName`" -Force"
}

Write-Host ""
Write-Host "Or run with -Fix flag to auto-organize:" -ForegroundColor Yellow
Write-Host "  .\audit_docs.ps1 -Fix" -ForegroundColor Cyan
Write-Host ""

# ============================================================
# AUTO-FIX MODE (if -Fix parameter passed)
# ============================================================

if ($args -contains "-Fix") {
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "AUTO-FIX MODE" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""

    foreach ($item in $classified) {
        $destDir = $item.suggestion
        $fileName = Split-Path $item.file -Leaf
        $destPath = "$destDir$fileName"

        # Ensure destination directory exists
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
            Write-Host "  Created: $destDir" -ForegroundColor DarkGray
        }

        # Move file
        if (Test-Path $item.file) {
            Move-Item -Path $item.file -Destination $destPath -Force
            Write-Host "  [MOVED] $($item.file)" -ForegroundColor Green
            Write-Host "       -> $destPath" -ForegroundColor DarkGray
        }
    }

    Write-Host ""
    Write-Host "Done! Review changes with: git status" -ForegroundColor Green
    Write-Host "Commit with: git add -A && git commit -m 'docs: organize stray documentation'" -ForegroundColor Cyan
}

# ============================================================
# SUMMARY
# ============================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Properly organized:  $($properFiles.Count) files in docs/" -ForegroundColor Green
Write-Host "  Stray files found:   $($strayFiles.Count)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Governance Hierarchy:" -ForegroundColor Cyan
Write-Host "  CANONICAL  = Binding, enforced in code" -ForegroundColor Magenta
Write-Host "  ADVISORY   = Guidance, pending promotion" -ForegroundColor Yellow
Write-Host "  QUICKREF   = Operational guides" -ForegroundColor Cyan
Write-Host "  ARCHIVE    = Historical reference only" -ForegroundColor DarkGray
Write-Host ""
