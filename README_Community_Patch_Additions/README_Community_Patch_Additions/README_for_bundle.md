
# README_Community_Patch_Additions — Apply Guide

Adds:
- `.github/PULL_REQUEST_TEMPLATE.md`
- Ensures `CONTRIBUTORS.md` includes `@HanzoRazer — creator & lead maintainer`:
  - `patches/contributors_add_hanzorazer.diff` (preferred)
  - `patches/Add-Contributor.ps1` (fallback append)

## Apply
```bash
git apply --reject --whitespace=fix patches/contributors_add_hanzorazer.diff
# or
powershell -ExecutionPolicy Bypass -File patches\Add-Contributor.ps1 -Path CONTRIBUTORS.md -Handle "@HanzoRazer" -Note "creator & lead maintainer"
git add -A && git commit -m "docs: PR template + first contributor entry" && git push
```
