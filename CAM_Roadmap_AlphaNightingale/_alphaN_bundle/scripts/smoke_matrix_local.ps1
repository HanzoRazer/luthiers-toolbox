
Param(
  [Parameter(Mandatory=$false)][string]$Base = "http://127.0.0.1:8000"
)
$env:TB_BASE = $Base
Write-Host "Running local smoke against $Base" -ForegroundColor Cyan
python scripts\smoke_cam_essentials.py
python scripts\smoke_n18_g2g3.py
