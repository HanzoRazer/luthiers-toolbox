
Param(
  [Parameter(Mandatory=$false)][string]$Prefix = "feature",
  [Parameter(Mandatory=$false)][string]$Remote = "origin"
)
$ErrorActionPreference = "Stop"
$branches = @(
  "helical-ramping-v16-1",
  "polygon-offset-n17",
  "trochoidal-bench-n16",
  "dxf-preflight",
  "arc-backplot",
  "bridge-calculator",
  "devx-tests-docs",
  "release-docker-security-perf"
)
foreach ($b in $branches) {
  $name = "$Prefix/$b"
  git checkout -b $name
  git push $Remote $name
}
Write-Host "Feature branches created & pushed." -ForegroundColor Green
