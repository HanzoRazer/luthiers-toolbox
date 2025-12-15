# ============================================
# LUTHIER'S TOOLBOX - GITIGNORE RECOVERY PATCH
# Run from repository root
# ============================================

$ErrorActionPreference = "Stop"

function Write-Header($text) {
    Write-Host "`n$("=" * 60)" -ForegroundColor Cyan
    Write-Host " $text" -ForegroundColor Cyan
    Write-Host "$("=" * 60)" -ForegroundColor Cyan
}

function Confirm-Step($message) {
    $response = Read-Host "$message (y/N)"
    return ($response -eq 'y' -or $response -eq 'Y')
}

# ══════════════════════════════════════════════════════════════
# WAVE 0 — Commit .gitignore fix
# ══════════════════════════════════════════════════════════════
Write-Header "WAVE 0: Commit .gitignore Fix"

$gitignoreStaged = git diff --cached --name-only | Select-String "\.gitignore"
if ($gitignoreStaged) {
    Write-Host "  .gitignore is staged and ready" -ForegroundColor Green
    if (Confirm-Step "  Commit .gitignore fix now?") {
        git commit -m "fix(gitignore): Anchor patterns to prevent blocking nested app code

- Changed /data/ instead of data/
- Changed /tools/ instead of tools/
- Changed /Calculators/ instead of Calculators/
- Changed /schemas_logs_ai.py instead of schemas_logs_ai.py

Fixes 136+ files in services/api/app/ being incorrectly ignored."
        Write-Host "  [OK] Wave 0 committed" -ForegroundColor Green
    }
} else {
    Write-Host "  [SKIP] .gitignore not staged or already committed" -ForegroundColor Yellow
}

# ══════════════════════════════════════════════════════════════
# CLEANUP — Verify and delete app/app/
# ══════════════════════════════════════════════════════════════
Write-Header "CLEANUP: Remove app/app/ Namespace Collision"

$appAppPath = "services/api/app/app"
if (Test-Path $appAppPath) {
    Write-Host "  Found suspect directory: $appAppPath" -ForegroundColor Yellow
    
    # Check for duplicates
    $sawRunsAppApp = "services/api/app/app/data/cnc_production/saw_runs.json"
    $sawRunsCnc = "services/api/app/cnc_production/saw_runs.json"
    
    if ((Test-Path $sawRunsAppApp) -and (Test-Path $sawRunsCnc)) {
        $hash1 = (Get-FileHash $sawRunsAppApp).Hash
        $hash2 = (Get-FileHash $sawRunsCnc).Hash
        if ($hash1 -eq $hash2) {
            Write-Host "  [VERIFIED] Files are identical duplicates" -ForegroundColor Green
        } else {
            Write-Host "  [WARN] Files differ - manual merge needed" -ForegroundColor Red
            Write-Host "  Skipping deletion. Review manually." -ForegroundColor Red
            $skipAppAppDelete = $true
        }
    } elseif (Test-Path $sawRunsAppApp) {
        Write-Host "  [INFO] Files exist only in app/app/ - will preserve by copying" -ForegroundColor Yellow
        if (Confirm-Step "  Copy unique files to cnc_production/ before deleting?") {
            New-Item -ItemType Directory -Path "services/api/app/cnc_production" -Force | Out-Null
            Copy-Item -Path "services/api/app/app/data/cnc_production/*" -Destination "services/api/app/cnc_production/" -Recurse -Force
            Write-Host "  [OK] Files copied" -ForegroundColor Green
        }
    }
    
    if (-not $skipAppAppDelete) {
        if (Confirm-Step "  Delete app/app/ directory?") {
            Remove-Item -Recurse -Force $appAppPath
            Write-Host "  [OK] app/app/ deleted" -ForegroundColor Green
        }
    }
} else {
    Write-Host "  [SKIP] app/app/ does not exist" -ForegroundColor Gray
}

# ══════════════════════════════════════════════════════════════
# WAVE 0.5 — Modified files only
# ══════════════════════════════════════════════════════════════
Write-Header "WAVE 0.5: Commit Modified Files"

$modifiedFiles = @(
    "services/api/app/instrument_geometry/body/__init__.py",
    "services/api/app/instrument_geometry/body/outlines.py",
    "services/api/app/main.py",
    "services/api/app/rmos/__init__.py",
    "services/api/app/routers/rmos_patterns_router.py"
)

$modifiedCount = 0
foreach ($file in $modifiedFiles) {
    if (Test-Path $file) {
        $status = git status --porcelain $file 2>$null
        if ($status -match "^ M|^M") {
            $modifiedCount++
            Write-Host "  [M] $file" -ForegroundColor Yellow
        }
    }
}

if ($modifiedCount -gt 0) {
    if (Confirm-Step "  Stage and commit $modifiedCount modified files?") {
        foreach ($file in $modifiedFiles) {
            if (Test-Path $file) { git add $file 2>$null }
        }
        git commit -m "fix: Update modified files after gitignore recovery"
        Write-Host "  [OK] Wave 0.5 committed" -ForegroundColor Green
    }
} else {
    Write-Host "  [SKIP] No modified files to commit" -ForegroundColor Gray
}

# ══════════════════════════════════════════════════════════════
# WAVE 1 — Core Spine
# ══════════════════════════════════════════════════════════════
Write-Header "WAVE 1: Core Spine Recovery"

$wave1Dirs = @(
    "services/api/app/calculators/",
    "services/api/app/ltb_calculators/",
    "services/api/app/data/",
    "services/api/app/tools/",
    "services/api/app/core/",
    "services/api/app/util/",
    "services/api/app/config/",
    "services/api/app/schemas/",
    "services/api/app/stores/",
    "services/api/app/services/",
    "services/api/app/api/"
)

$wave1Exists = @()
foreach ($dir in $wave1Dirs) {
    if (Test-Path $dir) {
        $wave1Exists += $dir
        Write-Host "  [+] $dir" -ForegroundColor Green
    } else {
        Write-Host "  [-] $dir (not found)" -ForegroundColor Gray
    }
}

if ($wave1Exists.Count -gt 0) {
    if (Confirm-Step "  Stage and commit $($wave1Exists.Count) core directories?") {
        foreach ($dir in $wave1Exists) { git add $dir }
        git commit -m "feat: Recover core spine (calculators, ltb_calculators, data, tools, services, schemas)"
        Write-Host "  [OK] Wave 1 committed" -ForegroundColor Green
    }
}

# ══════════════════════════════════════════════════════════════
# WAVE 2 — RMOS Complete
# ══════════════════════════════════════════════════════════════
Write-Header "WAVE 2: RMOS Subsystem"

if (Test-Path "services/api/app/rmos/") {
    Write-Host "  [+] services/api/app/rmos/" -ForegroundColor Green
    if (Confirm-Step "  Stage and commit RMOS subsystem?") {
        git add services/api/app/rmos/
        git commit -m "feat: Recover RMOS subsystem (api, models, services, ai_search)"
        Write-Host "  [OK] Wave 2 committed" -ForegroundColor Green
    }
} else {
    Write-Host "  [SKIP] RMOS directory not found" -ForegroundColor Gray
}

# ══════════════════════════════════════════════════════════════
# WAVE 3 — CAD/CAM
# ══════════════════════════════════════════════════════════════
Write-Header "WAVE 3: CAD/CAM Modules"

$wave3Dirs = @(
    "services/api/app/cad/",
    "services/api/app/cam_core/",
    "services/api/app/toolpath/",
    "services/api/app/art_studio/",
    "services/api/app/generators/"
)

$wave3Exists = @()
foreach ($dir in $wave3Dirs) {
    if (Test-Path $dir) {
        $wave3Exists += $dir
        Write-Host "  [+] $dir" -ForegroundColor Green
    } else {
        Write-Host "  [-] $dir (not found)" -ForegroundColor Gray
    }
}

if ($wave3Exists.Count -gt 0) {
    if (Confirm-Step "  Stage and commit $($wave3Exists.Count) CAD/CAM directories?") {
        foreach ($dir in $wave3Exists) { git add $dir }
        git commit -m "feat: Recover CAD/CAM modules (cad, cam_core, toolpath, art_studio, generators)"
        Write-Host "  [OK] Wave 3 committed" -ForegroundColor Green
    }
}

# ══════════════════════════════════════════════════════════════
# WAVE 4 — Active Features
# ══════════════════════════════════════════════════════════════
Write-Header "WAVE 4: Active Features"

$wave4Dirs = @(
    "services/api/app/websocket/",
    "services/api/app/workflow/",
    "services/api/app/pipelines/",
    "services/api/app/tests/"
)

$wave4Exists = @()
foreach ($dir in $wave4Dirs) {
    if (Test-Path $dir) {
        $wave4Exists += $dir
        Write-Host "  [+] $dir" -ForegroundColor Green
    } else {
        Write-Host "  [-] $dir (not found)" -ForegroundColor Gray
    }
}

if ($wave4Exists.Count -gt 0) {
    if (Confirm-Step "  Stage and commit $($wave4Exists.Count) feature directories?") {
        foreach ($dir in $wave4Exists) { git add $dir }
        git commit -m "feat: Recover feature modules (websocket, workflow, pipelines, tests)"
        Write-Host "  [OK] Wave 4 committed" -ForegroundColor Green
    }
}

# ══════════════════════════════════════════════════════════════
# WAVE 5 — Isolate Experimental
# ══════════════════════════════════════════════════════════════
Write-Header "WAVE 5: Isolate Experimental Modules"

$experimentalDirs = @(
    "services/api/app/ai_cam",
    "services/api/app/ai_core",
    "services/api/app/ai_graphics",
    "services/api/app/analytics",
    "services/api/app/cnc_production",
    "services/api/app/infra"
)

$expExists = @()
foreach ($dir in $experimentalDirs) {
    if (Test-Path $dir) {
        $expExists += $dir
        Write-Host "  [+] $dir" -ForegroundColor Yellow
    }
}

if ($expExists.Count -gt 0) {
    if (Confirm-Step "  Move $($expExists.Count) directories to _experimental/?") {
        $expTarget = "services/api/app/_experimental"
        New-Item -ItemType Directory -Path $expTarget -Force | Out-Null
        
        foreach ($dir in $expExists) {
            $dirName = Split-Path $dir -Leaf
            git mv $dir "$expTarget/$dirName" 2>$null
            if (-not $?) {
                # If git mv fails (untracked), use regular move then add
                Move-Item -Path $dir -Destination "$expTarget/$dirName" -Force
                git add "$expTarget/$dirName"
            }
            Write-Host "  [MOVED] $dirName -> _experimental/" -ForegroundColor Green
        }
        
        git commit -m "chore: Isolate experimental modules to _experimental/"
        Write-Host "  [OK] Wave 5 committed" -ForegroundColor Green
    }
}

# ══════════════════════════════════════════════════════════════
# FINAL VERIFICATION
# ══════════════════════════════════════════════════════════════
Write-Header "FINAL VERIFICATION"

Write-Host "`n  Checking for remaining untracked files in services/api/app/..." -ForegroundColor Yellow
$remaining = git status --porcelain services/api/app/ 2>$null | Select-String "^\?\?" | Select-String -NotMatch "__pycache__|\.pyc|\.db|\.jsonl|\.backup"

if ($remaining) {
    Write-Host "  [WARN] $($remaining.Count) untracked files remain:" -ForegroundColor Yellow
    $remaining | Select-Object -First 15 | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkYellow }
    if ($remaining.Count -gt 15) {
        Write-Host "    ... and $($remaining.Count - 15) more" -ForegroundColor DarkYellow
    }
} else {
    Write-Host "  [OK] No significant untracked files remain" -ForegroundColor Green
}

Write-Host "`n  Running syntax check..." -ForegroundColor Yellow
$syntaxResult = python -m compileall services/api/app -q 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Syntax check passed" -ForegroundColor Green
} else {
    Write-Host "  [WARN] Syntax errors detected:" -ForegroundColor Red
    Write-Host $syntaxResult -ForegroundColor DarkRed
}

Write-Host "`n  Commit summary:" -ForegroundColor Cyan
git log --oneline -10

Write-Header "COMPLETE"
Write-Host "  Run 'uvicorn app.main:app' from services/api/ to verify boot.`n" -ForegroundColor Cyan
