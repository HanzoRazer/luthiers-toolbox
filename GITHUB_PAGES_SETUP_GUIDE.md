# 🚀 GitHub Pages Setup Guide for Badge System

**Status:** Badge system pushed ✅ | Pages setup required ⏳  
**Date:** November 7, 2025

---

## 📋 Quick Start (5 Minutes)

### Step 1: Enable GitHub Pages

1. **Go to repository settings:**
   ```
   https://github.com/HanzoRazer/luthiers-toolbox/settings/pages
   ```

2. **Configure Pages:**
   - **Source:** Deploy from a branch
   - **Branch:** `gh-pages` (will be created automatically by workflow)
   - **Folder:** `/ (root)`
   - Click **Save**

3. **Wait for automatic deployment:**
   - GitHub Actions will create `gh-pages` branch on first workflow run
   - Initial deployment takes ~2-3 minutes

### Step 2: Trigger First Workflow Run

**Option A: Automatic (Recommended)**
The workflow will run automatically on:
- ✅ Push to main (already happened!)
- ⏰ Nightly at 2 AM UTC
- 📝 Changes to `cam_helical_v161_router.py` or `post_presets.py`

**Option B: Manual Trigger**
1. Go to: https://github.com/HanzoRazer/luthiers-toolbox/actions
2. Click **Helical Badges** workflow
3. Click **Run workflow** → **Run workflow**
4. Wait ~5 minutes for completion

### Step 3: Verify Badge Deployment

After workflow completes (green checkmark ✅):

1. **Check raw badge URLs:**
   ```
   https://raw.githubusercontent.com/HanzoRazer/luthiers-toolbox/gh-pages/reports/badges/GRBL.svg
   https://raw.githubusercontent.com/HanzoRazer/luthiers-toolbox/gh-pages/reports/badges/Mach3.svg
   https://raw.githubusercontent.com/HanzoRazer/luthiers-toolbox/gh-pages/reports/badges/Haas.svg
   https://raw.githubusercontent.com/HanzoRazer/luthiers-toolbox/gh-pages/reports/badges/Marlin.svg
   ```

2. **View interactive dashboard:**
   ```
   https://HanzoRazer.github.io/luthiers-toolbox/reports/helical-badges.html
   ```

3. **Check workflow artifacts:**
   - Go to Actions → Latest run → Artifacts
   - Download `helical-badges` artifact (5 files, 90-day retention)

---

## 🎨 Step 4: Add Badges to README

Once badges are deployed, add this section to your `README.md`:

### **Option A: Badge Table (Recommended)**

```markdown
## 🌀 Helical Post-Processor Status

| Preset | Status | Details |
|--------|--------|---------|
| **GRBL** | ![GRBL](https://raw.githubusercontent.com/HanzoRazer/luthiers-toolbox/gh-pages/reports/badges/GRBL.svg) | Standard hobby CNC (I,J arcs, G4 P ms) |
| **Mach3** | ![Mach3](https://raw.githubusercontent.com/HanzoRazer/luthiers-toolbox/gh-pages/reports/badges/Mach3.svg) | Industrial CNC (I,J arcs, G4 P ms) |
| **Haas** | ![Haas](https://raw.githubusercontent.com/HanzoRazer/luthiers-toolbox/gh-pages/reports/badges/Haas.svg) | Haas machines (R arcs, G4 S sec) |
| **Marlin** | ![Marlin](https://raw.githubusercontent.com/HanzoRazer/luthiers-toolbox/gh-pages/reports/badges/Marlin.svg) | 3D printer firmware (I,J arcs, G4 P ms) |

📊 **[View Live Dashboard](https://HanzoRazer.github.io/luthiers-toolbox/reports/helical-badges.html)** | 📖 **[Badge Documentation](./reports/HELICAL_BADGES_README.md)**

### Badge Colors
- 🟢 **Green**: Typical complexity (5-19 segments, optimal)
- 🔵 **Blue**: Complex path (20+ segments, advanced)
- 🟡 **Yellow**: Minimal path (<5 segments, basic)
- 🔴 **Red**: Error or no output (needs attention)

*Badges updated nightly via GitHub Actions*
```

### **Option B: Inline Badges (Compact)**

```markdown
## 🌀 Helical Post-Processors

![GRBL](https://raw.githubusercontent.com/HanzoRazer/luthiers-toolbox/gh-pages/reports/badges/GRBL.svg)
![Mach3](https://raw.githubusercontent.com/HanzoRazer/luthiers-toolbox/gh-pages/reports/badges/Mach3.svg)
![Haas](https://raw.githubusercontent.com/HanzoRazer/luthiers-toolbox/gh-pages/reports/badges/Haas.svg)
![Marlin](https://raw.githubusercontent.com/HanzoRazer/luthiers-toolbox/gh-pages/reports/badges/Marlin.svg)

📊 [View Dashboard](https://HanzoRazer.github.io/luthiers-toolbox/reports/helical-badges.html)
```

---

## 🔍 Verification Checklist

### GitHub Pages Settings
- [ ] Pages source set to `gh-pages` branch
- [ ] Folder set to `/ (root)`
- [ ] Pages status shows "Your site is live at..."

### Workflow Execution
- [ ] Workflow completed successfully (green checkmark)
- [ ] `helical-badges` artifact uploaded (5 files)
- [ ] `gh-pages` branch created automatically
- [ ] Deployment to Pages successful

### Badge Accessibility
- [ ] GRBL.svg accessible via raw.githubusercontent.com
- [ ] Mach3.svg accessible via raw.githubusercontent.com
- [ ] Haas.svg accessible via raw.githubusercontent.com
- [ ] Marlin.svg accessible via raw.githubusercontent.com
- [ ] badges.json contains all 4 presets

### Dashboard Functionality
- [ ] Dashboard loads at github.io URL
- [ ] 4 status cards displayed
- [ ] Results table populated
- [ ] Badge images render correctly
- [ ] Timestamp shows last update

### README Integration
- [ ] Badge table added to README.md
- [ ] All 4 badges render inline
- [ ] Dashboard link works
- [ ] Color legend included

---

## 🛠️ Troubleshooting

### Issue: "404 Not Found" for badge URLs

**Cause:** `gh-pages` branch not created yet or Pages not enabled

**Solution:**
1. Check if workflow ran successfully
2. Verify `gh-pages` branch exists: https://github.com/HanzoRazer/luthiers-toolbox/tree/gh-pages
3. Re-run workflow manually if needed

### Issue: Dashboard shows "Failed to fetch badges.json"

**Cause:** Pages deployment pending or badges.json missing

**Solution:**
1. Wait 2-3 minutes after workflow completes
2. Check artifact contains `badges.json`
3. Verify Pages deployment status in Settings → Pages

### Issue: Workflow fails on "Start API server" step

**Cause:** API dependencies not installed or syntax error

**Solution:**
1. Check workflow logs for error details
2. Verify `requirements.txt` is up to date
3. Test locally: `python tools/run_helical_smoke.py --api-base http://localhost:8000`

### Issue: Badges show wrong colors

**Cause:** Smoke test generated unexpected segment counts

**Solution:**
1. Check `reports/helical_smoke_posts.json` for actual values
2. Review color thresholds in `gen_helical_badge.py`:
   - Green: 5-19 segments
   - Blue: 20+ segments
   - Yellow: <5 segments
3. Adjust thresholds if needed for your use case

---

## 📊 Badge System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions Workflow                  │
│                  (.github/workflows/helical_badges.yml)     │
└──────────────┬──────────────────────────────────────────────┘
               │
               ├─ 1. Start API server (uvicorn)
               │
               ├─ 2. Run smoke tests (run_helical_smoke.py)
               │    │
               │    ├─ Test GRBL preset
               │    ├─ Test Mach3 preset
               │    ├─ Test Haas preset
               │    └─ Test Marlin preset
               │    │
               │    └─ Save: reports/helical_smoke_posts.json
               │
               ├─ 3. Generate badges (gen_helical_badge.py)
               │    │
               │    ├─ Read: helical_smoke_posts.json
               │    ├─ Apply color rules
               │    └─ Output:
               │         ├─ badges.json (metadata)
               │         ├─ GRBL.svg
               │         ├─ Mach3.svg
               │         ├─ Haas.svg
               │         └─ Marlin.svg
               │
               ├─ 4. Upload artifacts (90-day retention)
               │
               └─ 5. Deploy to GitHub Pages (gh-pages branch)
                    │
                    └─ Live at: HanzoRazer.github.io/luthiers-toolbox
```

---

## 🎯 Next Steps After Setup

### Immediate (Today)
1. ✅ Enable GitHub Pages
2. ✅ Verify first workflow run
3. ✅ Add badge table to README.md
4. ✅ Test dashboard URL

### Short-term (This Week)
- [ ] Add badge section to `HELICAL_POST_PRESETS.md`
- [ ] Add badge section to `ART_STUDIO_V16_1_HELICAL_INTEGRATION.md`
- [ ] Update `A_N_BUILD_ROADMAP.md` with badge milestone
- [ ] Create video tutorial: "Badge System Overview"

### Long-term (Next Month)
- [ ] Add historical trend graphs (badge size over time)
- [ ] Add composite badge (all presets status)
- [ ] Add Slack/Discord webhook notifications on failures
- [ ] Add more presets (LinuxCNC, PathPilot, Fanuc)

---

## 📚 Related Documentation

- **Badge README**: [reports/HELICAL_BADGES_README.md](./reports/HELICAL_BADGES_README.md)
- **Implementation Summary**: [HELICAL_BADGES_SYSTEM_COMPLETE.md](./HELICAL_BADGES_SYSTEM_COMPLETE.md)
- **Helical Post-Processor Presets**: [HELICAL_POST_PRESETS_COMPLETE.md](./HELICAL_POST_PRESETS_COMPLETE.md)
- **Art Studio v16.1 Integration**: [ART_STUDIO_V16_1_HELICAL_INTEGRATION.md](./ART_STUDIO_V16_1_HELICAL_INTEGRATION.md)

---

## 🤝 Support

If you encounter issues:
1. Check [Troubleshooting](#-troubleshooting) section above
2. Review workflow logs: https://github.com/HanzoRazer/luthiers-toolbox/actions
3. Test locally: `python test_badge_generator.py`
4. Create GitHub issue with error details

---

**Last Updated:** November 7, 2025  
**Status:** Ready for deployment ✅  
**Estimated Setup Time:** 5-10 minutes
