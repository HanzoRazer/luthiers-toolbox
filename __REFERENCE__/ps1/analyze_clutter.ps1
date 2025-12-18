# Repository Clutter Analysis
# Shows what files and folders need organization

$ErrorActionPreference = "SilentlyContinue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "REPOSITORY CLUTTER ANALYSIS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Exclusions
$excludeDirs = @("node_modules", ".git", "__pycache__", ".venv", "venv")

function ShouldExclude($path) {
    foreach ($dir in $excludeDirs) {
        if ($path -like "*\$dir\*" -or $path -like "*/$dir/*") {
            return $true
        }
    }
    return $false
}

# Count by file type
Write-Host "[FILE TYPES IN REPO]" -ForegroundColor Yellow
$allFiles = Get-ChildItem -Recurse -File | Where-Object { -not (ShouldExclude $_.FullName) }

$byExt = $allFiles | Group-Object Extension | Sort-Object Count -Descending | Select-Object -First 15
foreach ($g in $byExt) {
    $ext = if ($g.Name -eq "") { "(no ext)" } else { $g.Name }
    Write-Host ("  {0,-12} {1,5} files" -f $ext, $g.Count)
}
Write-Host ""

# Root level folders
Write-Host "[TOP-LEVEL FOLDERS]" -ForegroundColor Yellow
$rootDirs = Get-ChildItem -Directory | Where-Object { $_.Name -notlike ".*" }
foreach ($dir in $rootDirs) {
    $fileCount = (Get-ChildItem -Path $dir.FullName -Recurse -File -ErrorAction SilentlyContinue |
                  Where-Object { -not (ShouldExclude $_.FullName) }).Count

    # Categorize
    $category = switch -Regex ($dir.Name) {
        "^(services|packages|docs|scripts)$" { "[CORE]" }
        "^(node_modules|\.git|\.venv|dist|build)$" { "[BUILD]" }
        "^(Governance_Code_Bundle)$" { "[PENDING]" }
        default { "[REVIEW]" }
    }

    $color = switch ($category) {
        "[CORE]" { "Green" }
        "[BUILD]" { "DarkGray" }
        "[PENDING]" { "Yellow" }
        default { "Red" }
    }

    Write-Host ("  {0,-10} {1,-45} ({2,4} files)" -f $category, $dir.Name, $fileCount) -ForegroundColor $color
}
Write-Host ""

# Root level loose files (not in folders)
Write-Host "[ROOT-LEVEL LOOSE FILES]" -ForegroundColor Yellow
$rootFiles = Get-ChildItem -File | Where-Object { $_.Name -notlike ".*" }
Write-Host "  Total: $($rootFiles.Count) files"
Write-Host ""

$rootByExt = $rootFiles | Group-Object Extension | Sort-Object Count -Descending
foreach ($g in $rootByExt) {
    $ext = if ($g.Name -eq "") { "(no ext)" } else { $g.Name }
    Write-Host ("  {0,-8} {1,3} files" -f $ext, $g.Count)

    # Show first few of each type
    $g.Group | Select-Object -First 3 | ForEach-Object {
        Write-Host "           - $($_.Name)" -ForegroundColor DarkGray
    }
    if ($g.Count -gt 3) {
        Write-Host "           ... and $($g.Count - 3) more" -ForegroundColor DarkGray
    }
}
Write-Host ""

# Identify likely archive candidates
Write-Host "[LIKELY ARCHIVE CANDIDATES]" -ForegroundColor Yellow
Write-Host "  Folders with version numbers, dates, or 'old'/'backup' in name:" -ForegroundColor Gray

$archiveCandidates = $rootDirs | Where-Object {
    $_.Name -match "v\d|Build|Patch|bundle|files.*\d|old|backup|temp|MVP|Feature_" -or
    $_.Name -match "^\d{2}" -or  # Starts with numbers
    $_.Name -match "Guitar Design" -or
    $_.Name -match "Luthiers Tool Box" -or
    $_.Name -match "Archtop|Stratocaster"
}

foreach ($dir in $archiveCandidates) {
    $fileCount = (Get-ChildItem -Path $dir.FullName -Recurse -File -ErrorAction SilentlyContinue).Count
    Write-Host "    $($dir.Name)/ ($fileCount files)" -ForegroundColor DarkYellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RECOMMENDED ACTIONS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. ARCHIVE legacy folders    -> Move to 'archive/' or delete" -ForegroundColor Yellow
Write-Host "2. ROOT .md files            -> Run: .\audit_docs.ps1 -Fix" -ForegroundColor Yellow
Write-Host "3. ROOT .txt files           -> Convert to .md or archive" -ForegroundColor Yellow
Write-Host "4. ROOT .py/.ps1 scripts     -> Move to 'scripts/' or delete" -ForegroundColor Yellow
Write-Host "5. Governance_Code_Bundle    -> Already integrated, can delete" -ForegroundColor Yellow
Write-Host ""
