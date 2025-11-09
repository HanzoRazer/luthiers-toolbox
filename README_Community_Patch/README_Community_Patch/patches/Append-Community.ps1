
Param(
  [Parameter(Mandatory=$false)][string]$ReadmePath = "README.md"
)
$marker = "## 🌟 Project Milestones & Community"
if (!(Test-Path $ReadmePath)) { Write-Error "README not found at $ReadmePath"; exit 1 }
$content = Get-Content -Raw -LiteralPath $ReadmePath -ErrorAction Stop
if ($content -match [regex]::Escape($marker)) {
  Write-Host "Community section already present; nothing to do." -ForegroundColor Yellow
  exit 0
}
$block = @"
---

## 🌟 Project Milestones & Community

**⭐ First GitHub Star!**  
We’re officially on the map — our first star marks the start of our journey toward a world‑class open‑source CAM/CAD platform for luthiers, makers, and educators.  
Huge thanks to everyone who explored, forked, or contributed ideas!

We welcome:
- 🧩 **Pull requests** that improve functionality, documentation, or testing.
- 💬 **Issues** and discussions to shape new modules.
- 🎥 **Showcases** of your own builds powered by Luthier’s Tool Box.

If you’d like to contribute:
1. Fork this repo.
2. Create a feature branch:
   ```bash
   git checkout -b feature/my-improvement
   ```
3. Commit your changes and push the branch.
4. Open a Pull Request describing your change and screenshots (if UI-related).

> Every star, fork, and suggestion helps make the Tool Box better for everyone.  
> Thank you for being part of the early community!
"@
Add-Content -LiteralPath $ReadmePath -Value "`r`n$block`r`n"
Write-Host "Community section appended to $ReadmePath" -ForegroundColor Green
