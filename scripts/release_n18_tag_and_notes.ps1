# N18 Release Helper Script
# Creates git tag and prepares GitHub release for N.18 Spiral PolyCut

Param(
    [string]$VersionTag = "v0.18.0-n18_spiral_poly",
    [string]$ReleaseName = "N.18 – Spiral PolyCut",
    [string]$NotesPath = "docs/releases/N18_SPIRAL_POLYCUT_RELEASE_NOTES.md",
    [switch]$Push
)

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "                N.18 Release Helper                              " -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Tag      : $VersionTag" -ForegroundColor Yellow
Write-Host "Name     : $ReleaseName" -ForegroundColor Yellow
Write-Host "Notes    : $NotesPath" -ForegroundColor Yellow
Write-Host ""

# 1) Ensure we are in a git repo
Write-Host "[1/5] Checking git repository..." -ForegroundColor Cyan
git rev-parse --is-inside-work-tree 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ FAIL: Not inside a git repository" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Git repository detected" -ForegroundColor Green

# 2) Confirm working tree is clean
Write-Host "[2/5] Checking working tree status..." -ForegroundColor Cyan
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Host "⚠️  WARNING: Working tree is not clean" -ForegroundColor Yellow
    Write-Host "   Uncommitted changes:" -ForegroundColor Yellow
    Write-Host $gitStatus
    Write-Host ""
    Write-Host "   Commit or stash changes before tagging." -ForegroundColor Yellow
    exit 1
}
Write-Host "✓ Working tree is clean" -ForegroundColor Green

# 3) Check notes file exists
Write-Host "[3/5] Checking release notes..." -ForegroundColor Cyan
if (-not (Test-Path $NotesPath)) {
    Write-Host "❌ FAIL: Release notes file not found: $NotesPath" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Release notes found" -ForegroundColor Green

# 4) Create annotated tag
Write-Host "[4/5] Creating annotated git tag..." -ForegroundColor Cyan
$notesContent = Get-Content $NotesPath -Raw
git tag -a $VersionTag -m "$ReleaseName`n`n$notesContent"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ FAIL: Failed to create git tag" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Tag $VersionTag created successfully" -ForegroundColor Green

# 5) Push tag (if requested)
if ($Push) {
    Write-Host "[5/5] Pushing tag to origin..." -ForegroundColor Cyan
    git push origin $VersionTag

    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ FAIL: Failed to push tag" -ForegroundColor Red
        exit 1
    }

    Write-Host "✓ Tag pushed to origin" -ForegroundColor Green
    Write-Host ""
    Write-Host "==================================================================" -ForegroundColor Green
    Write-Host "                    ✅ RELEASE COMPLETE                          " -ForegroundColor Green
    Write-Host "==================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Go to GitHub repository" -ForegroundColor White
    Write-Host "  2. Navigate to 'Releases' section" -ForegroundColor White
    Write-Host "  3. Click 'Draft a new release'" -ForegroundColor White
    Write-Host "  4. Select tag: $VersionTag" -ForegroundColor Yellow
    Write-Host "  5. Title: $ReleaseName" -ForegroundColor Yellow
    Write-Host "  6. Copy release notes from: $NotesPath" -ForegroundColor Yellow
    Write-Host "  7. Publish release" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "[5/5] Skipping push (--Push flag not provided)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "==================================================================" -ForegroundColor Yellow
    Write-Host "             TAG CREATED LOCALLY (NOT PUSHED)                    " -ForegroundColor Yellow
    Write-Host "==================================================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To push the tag later, run:" -ForegroundColor Cyan
    Write-Host "    git push origin $VersionTag" -ForegroundColor White
    Write-Host ""
}

Write-Host "GitHub Release Instructions:" -ForegroundColor Cyan
Write-Host "  Tag    : $VersionTag" -ForegroundColor Yellow
Write-Host "  Title  : $ReleaseName" -ForegroundColor Yellow
Write-Host "  Body   : Copy from $NotesPath" -ForegroundColor Yellow
Write-Host ""
