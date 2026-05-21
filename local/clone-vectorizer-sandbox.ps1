# Clone vectorizer-sandbox as a sibling of luthiers-toolbox (../vectorizer-sandbox).
# Run from anywhere:  .\local\clone-vectorizer-sandbox.ps1

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Dest = Join-Path (Split-Path $RepoRoot -Parent) "vectorizer-sandbox"
$Remote = "https://github.com/HanzoRazer/vectorizer-sandbox.git"

if (Test-Path (Join-Path $Dest ".git")) {
    Write-Host "Already cloned: $Dest"
    exit 0
}

if (Test-Path $Dest) {
    Write-Error "Path exists but is not a git clone: $Dest"
}

Write-Host "Cloning $Remote -> $Dest"
git clone $Remote $Dest
Write-Host "Done. Open cognition layer at: $Dest"
