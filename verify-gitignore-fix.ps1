# ============================================
# GITIGNORE FIX VERIFICATION & MIGRATION SCRIPT
# Run from repository root after Option A fix
# ============================================

Write-Host "`n========== PHASE 1: VERIFY FIX WORKED ==========" -ForegroundColor Cyan

$criticalFiles = @(
    "services/api/app/calculators/__init__.py",
    "services/api/app/data/__init__.py",
    "services/api/app/tools/__init__.py",
    "services/api/app/rmos/schemas_logs_ai.py"
)

$fixWorked = $true
foreach ($file in $criticalFiles) {
    $result = git check-ignore -v $file 2>$null
    if ($result) {
        Write-Host "  [FAIL] Still ignored: $file" -ForegroundColor Red
        Write-Host "         Rule: $result" -ForegroundColor DarkRed
        $fixWorked = $false
    } else {
        Write-Host "  [OK] Now trackable: $file" -ForegroundColor Green
    }
}

if (-not $fixWorked) {
    Write-Host "`n[ABORT] Fix incomplete. Please verify .gitignore changes." -ForegroundColor Red
    exit 1
}

Write-Host "`n========== PHASE 2: AUDIT OTHER UNANCHORED PATTERNS ==========" -ForegroundColor Cyan

Write-Host "  Scanning .gitignore for risky unanchored directory patterns..." -ForegroundColor Yellow
$riskyPatterns = Get-Content .gitignore | ForEach-Object { $_.Trim() } | Where-Object { 
    $_ -match "^[a-zA-Z].*/$" -and $_ -notmatch "^\*" -and $_ -notmatch "^\!" -and $_ -notmatch "^#"
}

if ($riskyPatterns) {
    Write-Host "  [WARN] Found unanchored patterns that may cause future issues:" -ForegroundColor Yellow
    $riskyPatterns | ForEach-Object { Write-Host "         $_" -ForegroundColor DarkYellow }
} else {
    Write-Host "  [OK] No risky unanchored patterns found" -ForegroundColor Green
}

Write-Host "`n========== PHASE 3: FILES NOW TRACKABLE ==========" -ForegroundColor Cyan

Write-Host "  Scanning services/api/app for newly trackable files..." -ForegroundColor Yellow
$newFiles = git status --short | Select-String "services/api/app" | Select-String -NotMatch "__pycache__"

if ($newFiles) {
    Write-Host "  Found $($newFiles.Count) files ready to stage:" -ForegroundColor Green
    $newFiles | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGreen }
} else {
    Write-Host "  [INFO] No new untracked files in services/api/app" -ForegroundColor Gray
}

Write-Host "`n========== PHASE 4: STAGE FILES ==========" -ForegroundColor Cyan

$response = Read-Host "  Stage all newly trackable files? (y/N)"
if ($response -eq 'y' -or $response -eq 'Y') {
    git add services/api/app/calculators/
    git add services/api/app/data/
    git add services/api/app/tools/
    git add services/api/app/rmos/schemas_logs_ai.py 2>$null
    git add services/api/app/workflow/mode_preview_routes.py 2>$null
    git add services/api/app/services/cam_backup_service.py 2>$null
    
    Write-Host "  [DONE] Files staged. Run 'git status' to review." -ForegroundColor Green
} else {
    Write-Host "  [SKIP] No files staged." -ForegroundColor Gray
}

Write-Host "`n========== PHASE 5: SUMMARY ==========" -ForegroundColor Cyan

$stagedCount = (git diff --cached --name-only | Measure-Object).Count
$ignoredInApp = git status --ignored --short | Select-String "services/api/app" | Select-String -NotMatch "__pycache__"

Write-Host "  Staged files:        $stagedCount" -ForegroundColor White
Write-Host "  Still ignored:       $($ignoredInApp.Count) (should be 0)" -ForegroundColor $(if($ignoredInApp.Count -eq 0){"Green"}else{"Red"})

if ($ignoredInApp.Count -gt 0) {
    Write-Host "`n  [WARN] These are still being ignored:" -ForegroundColor Red
    $ignoredInApp | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkRed }
}

Write-Host "`n[COMPLETE] Run 'git diff --cached --stat' to review staged changes.`n" -ForegroundColor Cyan