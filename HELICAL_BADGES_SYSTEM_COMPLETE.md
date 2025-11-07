# ✅ Helical Smoke Badge System - Complete

**Date:** November 7, 2025  
**Feature:** Automated badge generation for helical post-processor smoke tests  
**Status:** Implementation Complete

---

## 🎯 What Was Implemented

A complete **badge generation system** that:
1. Runs smoke tests for all 4 CNC controller presets
2. Generates SVG badges showing G-code size
3. Auto-publishes to GitHub Pages
4. Provides visual dashboard for status monitoring

---

## 📦 Files Created (7 Total)

### **1. Badge Generator Script**
**File:** `services/api/tools/gen_helical_badge.py` (100 lines)

Generates:
- `reports/badges/badges.json` - Badge metadata
- `reports/badges/GRBL.svg` - GRBL badge
- `reports/badges/Mach3.svg` - Mach3 badge
- `reports/badges/Haas.svg` - Haas badge
- `reports/badges/Marlin.svg` - Marlin badge

**Color Scheme:**
- 🟢 **Green (#28a745)**: 5-19 segments (typical)
- 🔵 **Blue (#0366d6)**: 20+ segments (complex)
- 🟡 **Yellow (#dbab09)**: < 5 segments (minimal)
- 🔴 **Red (#d73a4a)**: Error or no output

---

### **2. Smoke Test Runner**
**File:** `tools/run_helical_smoke.py` (120 lines)

Cross-platform Python script that:
- Tests all 4 presets against API
- Saves results to `reports/helical_smoke_posts.json`
- Validates G-code output
- Returns exit code 0 (pass) or 2 (fail)

**Usage:**
```bash
python tools/run_helical_smoke.py --api-base http://localhost:8000
```

---

### **3. PowerShell Smoke Test (Enhanced)**
**File:** `tools/smoke_helix_posts.ps1` (Updated)

Now saves results to JSON:
```json
{
  "GRBL": {
    "bytes": 1247,
    "segments": 8,
    "arc_mode": "IJ"
  },
  "Haas": {
    "bytes": 1203,
    "segments": 8,
    "arc_mode": "R"
  }
}
```

---

### **4. Makefile Target (Enhanced)**
**File:** `Makefile` (Updated)

```bash
make smoke-helix-posts
```

Now:
- Runs smoke tests
- Saves results to `reports/helical_smoke_posts.json`
- Ready for badge generation

---

### **5. GitHub Actions Workflow**
**File:** `.github/workflows/helical_badges.yml` (150 lines)

Auto-runs on:
- Push to `main` branch
- Changes to helical router/presets
- Manual trigger
- Nightly at 2 AM UTC

**Workflow Steps:**
1. Start API server
2. Run smoke tests
3. Generate badges
4. Upload artifacts
5. Deploy to GitHub Pages
6. Comment on PRs with results

---

### **6. Badge README**
**File:** `reports/HELICAL_BADGES_README.md` (100 lines)

Documentation for:
- Badge status table
- Color legend
- Local testing instructions
- CI/CD integration

---

### **7. HTML Dashboard**
**File:** `reports/helical-badges.html` (300 lines)

**Live dashboard** showing:
- Status cards for each preset
- Badge images
- Detailed results table
- Real-time data from `badges.json`

**Preview URL:** `https://<username>.github.io/luthiers-toolbox/reports/helical-badges.html`

---

## 🎨 Badge Examples

### **Sample SVG Badge** (shields.io style)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="120" height="20">
  <path fill="#555" d="M0 0h70v20H0z"/>
  <path fill="#28a745" d="M70 0h50v20H70z"/>
  <text x="35" y="14">GRBL</text>
  <text x="95" y="14">1247b</text>
</svg>
```

---

## 🔄 Workflow

### **Local Development**
```powershell
# 1. Start API
cd services/api
uvicorn app.main:app --reload --port 8000

# 2. Run smoke test
python tools/run_helical_smoke.py

# 3. Generate badges
python services/api/tools/gen_helical_badge.py

# 4. View dashboard
# Open reports/helical-badges.html in browser
```

### **CI/CD Automation**
```
Push to main
    ↓
GitHub Actions triggered
    ↓
Start API server
    ↓
Run smoke tests → reports/helical_smoke_posts.json
    ↓
Generate badges → reports/badges/*.svg + badges.json
    ↓
Deploy to GitHub Pages
    ↓
Badges visible at:
  https://github.com/<user>/<repo>/blob/main/reports/badges/GRBL.svg
```

---

## 📊 Example Output

### **badges.json**
```json
{
  "GRBL": {
    "bytes": 1247,
    "segments": 8,
    "arc_mode": "IJ",
    "color": "#28a745"
  },
  "Mach3": {
    "bytes": 1248,
    "segments": 8,
    "arc_mode": "IJ",
    "color": "#28a745"
  },
  "Haas": {
    "bytes": 1203,
    "segments": 8,
    "arc_mode": "R",
    "color": "#28a745"
  },
  "Marlin": {
    "bytes": 1249,
    "segments": 8,
    "arc_mode": "IJ",
    "color": "#28a745"
  }
}
```

### **Console Output**
```
=== Helical Post-Processor Smoke Test ===

[Testing] GRBL... [OK] 1247b, 8 segs, IJ mode
[Testing] Mach3... [OK] 1248b, 8 segs, IJ mode
[Testing] Haas... [OK] 1203b, 8 segs, R mode
[Testing] Marlin... [OK] 1249b, 8 segs, IJ mode

✅ Saved results to reports/helical_smoke_posts.json
```

---

## 🎯 Usage in Documentation

### **README.md (Add to any doc)**
```markdown
## 🌀 Helical Smoke Status

| Preset | Badge |
|--------|-------|
| GRBL | ![GRBL](https://raw.githubusercontent.com/HanzoRazer/luthiers-toolbox/main/reports/badges/GRBL.svg) |
| Mach3 | ![Mach3](https://raw.githubusercontent.com/HanzoRazer/luthiers-toolbox/main/reports/badges/Mach3.svg) |
| Haas | ![Haas](https://raw.githubusercontent.com/HanzoRazer/luthiers-toolbox/main/reports/badges/Haas.svg) |
| Marlin | ![Marlin](https://raw.githubusercontent.com/HanzoRazer/luthiers-toolbox/main/reports/badges/Marlin.svg) |
```

### **Embedded in HTML**
```html
<img src="https://raw.githubusercontent.com/HanzoRazer/luthiers-toolbox/main/reports/badges/GRBL.svg">
```

---

## 🚀 Next Steps

### **Immediate**
1. ✅ Enable GitHub Pages (Settings → Pages → Source: gh-pages branch)
2. ✅ Run first manual workflow (Actions → Helical Badges → Run workflow)
3. ✅ Verify badges appear at: `https://<user>.github.io/<repo>/reports/badges/`

### **Integration**
1. Add badge table to main README.md
2. Add badge table to HELICAL_POST_PRESETS.md
3. Add badge table to ART_STUDIO_V16_1_HELICAL_INTEGRATION.md
4. Link to HTML dashboard in docs

### **Enhancement**
1. Add more presets (LinuxCNC, PathPilot, Fanuc)
2. Add historical trend graphs
3. Add badge for total test suite status
4. Add Slack/Discord notifications on failures

---

## 📁 File Structure

```
Luthiers ToolBox/
├── .github/
│   └── workflows/
│       └── helical_badges.yml          # ← NEW: CI workflow
├── services/api/tools/
│   └── gen_helical_badge.py            # ← NEW: Badge generator
├── tools/
│   ├── run_helical_smoke.py            # ← NEW: Smoke test runner
│   └── smoke_helix_posts.ps1           # ← UPDATED: Now saves JSON
├── reports/
│   ├── HELICAL_BADGES_README.md        # ← NEW: Badge documentation
│   ├── helical-badges.html             # ← NEW: Dashboard page
│   ├── helical_smoke_posts.json        # ← Generated by smoke test
│   └── badges/
│       ├── badges.json                 # ← Generated by gen_helical_badge.py
│       ├── GRBL.svg                    # ← Generated badge
│       ├── Mach3.svg                   # ← Generated badge
│       ├── Haas.svg                    # ← Generated badge
│       └── Marlin.svg                  # ← Generated badge
└── Makefile                            # ← UPDATED: Saves JSON
```

---

## ✅ Success Criteria

- [x] Badge generator script created
- [x] Smoke test runner created
- [x] PowerShell smoke test saves JSON
- [x] Makefile target saves JSON
- [x] GitHub Actions workflow created
- [x] HTML dashboard created
- [x] Badge README created
- [ ] GitHub Pages enabled (manual step)
- [ ] First workflow run successful
- [ ] Badges visible in README

---

## 🎉 Summary

**Complete badge system** ready for deployment:
- 7 files created/modified
- 4 SVG badges auto-generated
- Live HTML dashboard
- CI/CD automation
- GitHub Pages integration

**Next:** Enable GitHub Pages and run first workflow.

---

**Authored by:** GitHub Copilot  
**Date:** November 7, 2025  
**Ready for:** GitHub Pages deployment
