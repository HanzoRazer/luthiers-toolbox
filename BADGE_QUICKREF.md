# 🚀 Badge System - Quick Reference Card

**One-Page Guide for GitHub Pages Setup**

---

## ⚡ 60-Second Setup

### 1️⃣ Enable Pages (30 sec)
```
URL: https://github.com/HanzoRazer/luthiers-toolbox/settings/pages

Settings:
  Source: Deploy from a branch
  Branch: gh-pages
  Folder: / (root)
  
[Save]
```

### 2️⃣ Check Workflow (15 sec)
```
URL: https://github.com/HanzoRazer/luthiers-toolbox/actions

Look for: "Helical Badges" workflow
Status: Green ✅ (wait 5 min if running)
```

### 3️⃣ Test Dashboard (15 sec)
```
URL: https://HanzoRazer.github.io/luthiers-toolbox/reports/helical-badges.html

Expected: 4 status cards (GRBL, Mach3, Haas, Marlin)
```

---

## 🎨 Badge URLs (After Setup)

### Raw SVG URLs
```
GRBL:   https://raw.githubusercontent.com/HanzoRazer/luthiers-toolbox/gh-pages/reports/badges/GRBL.svg
Mach3:  https://raw.githubusercontent.com/HanzoRazer/luthiers-toolbox/gh-pages/reports/badges/Mach3.svg
Haas:   https://raw.githubusercontent.com/HanzoRazer/luthiers-toolbox/gh-pages/reports/badges/Haas.svg
Marlin: https://raw.githubusercontent.com/HanzoRazer/luthiers-toolbox/gh-pages/reports/badges/Marlin.svg
```

### Metadata
```
JSON: https://raw.githubusercontent.com/HanzoRazer/luthiers-toolbox/gh-pages/reports/badges/badges.json
```

---

## 📝 Add to README.md

### Copy-Paste Ready
```markdown
## 🌀 Helical Post-Processor Status

| Preset | Status | Details |
|--------|--------|---------|
| **GRBL** | ![GRBL](https://raw.githubusercontent.com/HanzoRazer/luthiers-toolbox/gh-pages/reports/badges/GRBL.svg) | Standard hobby CNC |
| **Mach3** | ![Mach3](https://raw.githubusercontent.com/HanzoRazer/luthiers-toolbox/gh-pages/reports/badges/Mach3.svg) | Industrial CNC |
| **Haas** | ![Haas](https://raw.githubusercontent.com/HanzoRazer/luthiers-toolbox/gh-pages/reports/badges/Haas.svg) | Haas machines |
| **Marlin** | ![Marlin](https://raw.githubusercontent.com/HanzoRazer/luthiers-toolbox/gh-pages/reports/badges/Marlin.svg) | 3D printer firmware |

📊 **[View Dashboard](https://HanzoRazer.github.io/luthiers-toolbox/reports/helical-badges.html)**

*Badges updated nightly via GitHub Actions*
```

---

## 🎨 Badge Colors

| Color | Range | Meaning |
|-------|-------|---------|
| 🟢 Green | 5-19 segs | Typical (optimal) |
| 🔵 Blue | 20+ segs | Complex (advanced) |
| 🟡 Yellow | <5 segs | Minimal (basic) |
| 🔴 Red | 0 bytes | Error (needs fix) |

---

## 🔧 Local Commands

### Test Badge Generator
```powershell
python test_badge_generator.py
```

### Run Smoke Tests
```powershell
# PowerShell
.\tools\smoke_helix_posts.ps1

# Python (cross-platform)
python tools/run_helical_smoke.py --api-base http://localhost:8000

# Make (Unix/Linux)
make smoke-helix-posts
```

### View Dashboard Locally
```powershell
start reports/helical-badges.html
```

---

## 📚 Full Documentation

| Document | Purpose |
|----------|---------|
| `GITHUB_PAGES_SETUP_CHECKLIST.md` | 5-min quick start |
| `GITHUB_PAGES_SETUP_GUIDE.md` | Comprehensive guide |
| `BADGE_SYSTEM_DEPLOYMENT_SUMMARY.md` | What was deployed |
| `HELICAL_BADGES_SYSTEM_COMPLETE.md` | Implementation details |
| `reports/HELICAL_BADGES_README.md` | User documentation |

---

## 🐛 Quick Troubleshooting

### Problem: 404 on badge URLs
**Fix:** Wait 2-3 min after workflow completes

### Problem: Dashboard won't load
**Fix:** 
1. Check Pages is enabled (Settings → Pages)
2. Verify `gh-pages` branch exists
3. Wait 5 min after first deployment

### Problem: Workflow fails
**Fix:** Check logs at https://github.com/HanzoRazer/luthiers-toolbox/actions

---

## ✅ Deployment Checklist

- [x] Badge system pushed (commit: 2468310)
- [x] Setup guides pushed (commit: 401b379)
- [x] Deployment summary pushed (commit: 16b48d0)
- [ ] GitHub Pages enabled
- [ ] Workflow executed
- [ ] Badges accessible
- [ ] Dashboard live
- [ ] README updated

---

## 🔗 Quick Links

| Link | URL |
|------|-----|
| **Pages Settings** | https://github.com/HanzoRazer/luthiers-toolbox/settings/pages |
| **Actions** | https://github.com/HanzoRazer/luthiers-toolbox/actions |
| **Dashboard** | https://HanzoRazer.github.io/luthiers-toolbox/reports/helical-badges.html |
| **Repository** | https://github.com/HanzoRazer/luthiers-toolbox |

---

## 📊 Stats

- **Files Created:** 16
- **Lines of Code:** 1,735+
- **Documentation:** 1,150+ lines
- **Commits:** 3
- **Setup Time:** ~5 minutes
- **Automation:** 100% (after setup)

---

**Status:** ✅ Ready for GitHub Pages  
**Last Updated:** November 7, 2025  
**Quick Start:** GITHUB_PAGES_SETUP_CHECKLIST.md
