
Param(
  [Parameter(Mandatory=$false)][string]$Path = "CONTRIBUTORS.md",
  [Parameter(Mandatory=$false)][string]$Handle = "@HanzoRazer",
  [Parameter(Mandatory=$false)][string]$Note = "creator & lead maintainer"
)
if (!(Test-Path $Path)) { 
  "# Contributors`n`n- $Handle — $Note`n" | Out-File -FilePath $Path -Encoding UTF8
  Write-Host "Created $Path with first entry." -ForegroundColor Green
  exit 0
}
$content = Get-Content -Raw -LiteralPath $Path
$line = "- $Handle — $Note"
if ($content -notmatch [regex]::Escape($line)) {
  Add-Content -LiteralPath $Path -Value "`n$line`n"
  Write-Host "Appended first entry to $Path" -ForegroundColor Green
} else {
  Write-Host "Entry already present; nothing to do." -ForegroundColor Yellow
}
