# ✅ GitHub Pages Setup Checklist

**Quick 5-Minute Setup for Badge System**

---

## 🎯 Phase 1: Enable GitHub Pages (2 minutes)

### Step 1.1: Navigate to Pages Settings
- [ ] Open: https://github.com/HanzoRazer/luthiers-toolbox/settings/pages

### Step 1.2: Configure Source
- [ ] **Source:** Deploy from a branch
- [ ] **Branch:** `gh-pages`
- [ ] **Folder:** `/ (root)`
- [ ] Click **Save**

### Step 1.3: Note Your Pages URL
```
https://HanzoRazer.github.io/luthiers-toolbox/
```

---

## 🚀 Phase 2: Trigger Workflow (3 minutes)

### Option A: Wait for Automatic Run ⏰
The workflow runs automatically when:
- ✅ Code is pushed to `main` (already happened!)
- ⏰ Every night at 2 AM UTC
- 📝 Files change: `cam_helical_v161_router.py` or `post_presets.py`

### Option B: Manual Trigger Now 🔨
- [ ] Go to: https://github.com/HanzoRazer/luthiers-toolbox/actions
- [ ] Click **"Helical Badges"** workflow
- [ ] Click **"Run workflow"** button (top right)
- [ ] Click **"Run workflow"** in dropdown
- [ ] Wait ~5 minutes for completion (green ✅)

---

## 🔍 Phase 3: Verify Deployment (2 minutes)

### Step 3.1: Check Workflow Status
- [ ] Workflow shows green checkmark ✅
- [ ] All steps completed successfully
- [ ] Artifact uploaded: `helical-badges` (5 files)

### Step 3.2: Verify gh-pages Branch Created
- [ ] Check: https://github.com/HanzoRazer/luthiers-toolbox/tree/gh-pages
- [ ] Contains `reports/badges/` directory
- [ ] Contains 4 SVG files + badges.json

### Step 3.3: Test Badge URLs
Copy these URLs into browser (replace after deployment):

```
https://raw.githubusercontent.com/HanzoRazer/luthiers-toolbox/gh-pages/reports/badges/GRBL.svg
https://raw.githubusercontent.com/HanzoRazer/luthiers-toolbox/gh-pages/reports/badges/Mach3.svg
https://raw.githubusercontent.com/HanzoRazer/luthiers-toolbox/gh-pages/reports/badges/Haas.svg
https://raw.githubusercontent.com/HanzoRazer/luthiers-toolbox/gh-pages/reports/badges/Marlin.svg
```

Expected: SVG badges display with green color

### Step 3.4: Test Dashboard
- [ ] Open: https://HanzoRazer.github.io/luthiers-toolbox/reports/helical-badges.html
- [ ] See 4 status cards (GRBL, Mach3, Haas, Marlin)
- [ ] See results table with bytes/segments
- [ ] Timestamp shows recent date

---

## 📝 Phase 4: Update README (1 minute)

### Add Badge Table to README.md

```bash
# Open README.md and add this section:
```

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

### Commit and Push
```powershell
git add README.md
git commit -m "docs: Add helical badge status table to README"
git push origin main
```

---

## 🎉 Success Criteria

### All Systems Green ✅
- [x] Code pushed to GitHub (commit: 2468310)
- [ ] GitHub Pages enabled
- [ ] Workflow ran successfully
- [ ] `gh-pages` branch exists
- [ ] Badges accessible via raw URLs
- [ ] Dashboard loads correctly
- [ ] README updated with badge table

---

## 🐛 Quick Troubleshooting

### Problem: "404 Not Found" on badge URLs
**Solution:** Wait 2-3 minutes after workflow completes, then refresh

### Problem: Workflow fails
**Solution:** Check logs at https://github.com/HanzoRazer/luthiers-toolbox/actions

### Problem: Dashboard won't load
**Solution:** 
1. Verify Pages is enabled in Settings → Pages
2. Check if `gh-pages` branch exists
3. Wait 5 minutes after first deployment

---

## 📊 Current Status

- ✅ Badge system code complete
- ✅ Workflow file created
- ✅ Files pushed to GitHub (13 files, 1245+ lines)
- ✅ Commit hash: `2468310`
- ⏳ **NEXT:** Enable GitHub Pages (you are here!)

---

## 🔗 Quick Links

- **Repository:** https://github.com/HanzoRazer/luthiers-toolbox
- **Pages Settings:** https://github.com/HanzoRazer/luthiers-toolbox/settings/pages
- **Actions:** https://github.com/HanzoRazer/luthiers-toolbox/actions
- **Dashboard (after setup):** https://HanzoRazer.github.io/luthiers-toolbox/reports/helical-badges.html

---

**Estimated Total Time:** 5-10 minutes  
**Last Updated:** November 7, 2025  
**Ready to Deploy:** ✅
