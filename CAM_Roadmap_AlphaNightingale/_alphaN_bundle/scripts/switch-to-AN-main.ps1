
Param(
  [Parameter(Mandatory=$false)][string]$Branch = "A_N_main",
  [Parameter(Mandatory=$false)][string]$Remote = "origin"
)
$ErrorActionPreference = "Stop"
git checkout -b $Branch
git push $Remote $Branch --set-upstream
Write-Host "Created and switched to $Branch. Consider merging feature branches into this integration branch." -ForegroundColor Green
