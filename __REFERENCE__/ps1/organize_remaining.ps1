# Organize remaining loose files into __REFERENCE__/ subfolders
# Preserves essential config files at root
$ErrorActionPreference = "Stop"

# Files to KEEP at root (essential configs)
$keepAtRoot = @(
    ".gitignore",
    ".env.example",
    ".pre-commit-config.yaml",
    "pnpm-workspace.yaml",
    "docker-compose.yml",
    "docker-compose.production.yml",
    "Makefile",
    "luthiers-toolbox.code-workspace",
    "README.md",
    "CHANGELOG.md",
    "docker-start.sh",
    "start_api.sh",
    "rmos_pytest.ini"
)

# Extension to folder mapping
$extMap = @{
    ".pdf" = "pdf"
    ".csv" = "csv"
    ".md" = "md"
    ".json" = "json"
    ".zip" = "zip"
    ".vue" = "vue"
    ".ts" = "ts"
    ".docx" = "docx"
    ".html" = "html"
    ".yaml" = "yaml"
    ".yml" = "yml"
    ".dxf" = "dxf"
    ".svg" = "svg"
    ".xml" = "xml"
    ".patch" = "patch"
    ".nc" = "nc"
    ".sh" = "sh"
    ".puml" = "puml"
    ".inp" = "inp"
    ".f3d" = "f3d"
    ".tool" = "tool"
    ".xlsx" = "xlsx"
    ".vtdb" = "vtdb"
}

$moved = @{}
$kept = @()

# Get all files at root
$files = Get-ChildItem -File

foreach ($f in $files) {
    # Skip files that should stay at root
    if ($keepAtRoot -contains $f.Name) {
        $kept += $f.Name
        continue
    }

    # Skip the script itself
    if ($f.Name -eq "organize_remaining.ps1" -or $f.Name -eq "show_remaining.ps1") {
        continue
    }

    # Determine target folder
    $ext = $f.Extension.ToLower()
    if ($extMap.ContainsKey($ext)) {
        $targetFolder = "__REFERENCE__\" + $extMap[$ext]
    } else {
        $targetFolder = "__REFERENCE__\misc"
    }

    # Create folder if needed
    if (-not (Test-Path $targetFolder)) {
        New-Item -ItemType Directory -Path $targetFolder | Out-Null
        Write-Host "Created $targetFolder/" -ForegroundColor Cyan
    }

    # Move file
    Move-Item -Path $f.FullName -Destination "$targetFolder\" -Force

    # Track counts
    if (-not $moved.ContainsKey($targetFolder)) {
        $moved[$targetFolder] = 0
    }
    $moved[$targetFolder]++
}

# Also move the helper scripts we created
$helperScripts = @("organize_remaining.ps1", "show_remaining.ps1")
foreach ($script in $helperScripts) {
    if (Test-Path $script) {
        Move-Item -Path $script -Destination "__REFERENCE__\ps1\" -Force
        Write-Host "[MOVED] $script to __REFERENCE__/ps1/" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "FILES ORGANIZED" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
$total = 0
foreach ($folder in $moved.Keys | Sort-Object) {
    Write-Host ("  {0,-30} {1,3} files" -f $folder, $moved[$folder]) -ForegroundColor Green
    $total += $moved[$folder]
}
Write-Host ""
Write-Host "  Total moved: $total" -ForegroundColor Yellow

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "FILES KEPT AT ROOT" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
foreach ($k in $kept | Sort-Object) {
    Write-Host "  $k" -ForegroundColor Gray
}
