# Phase 1 Execution Plan
### Express Edition MVP + Parametric Guitar Designer

**Created:** December 3, 2025  
**Timeline:** 4 weeks (68-102 hours)  
**Goal:** Launch first two products with revenue generation capability

---

## 🎯 Phase 1 Overview

**Primary Deliverables:**
1. **Express Edition MVP** ($49) - Design-focused entry-tier product
2. **Parametric Guitar Designer** ($39-$59) - Etsy/Gumroad product

**Success Metrics:**
- ✅ 2 products live and generating revenue
- ✅ First 10 paying customers
- ✅ Clean separation from golden master repo
- ✅ Validated product-market fit for Express tier

---

## 📋 Pre-Phase 1 Checklist (Complete Before Starting)

### ✅ **Lean Extraction Strategy** ✅ IMPLEMENTED
- [x] Strategic documentation complete
- [x] Lean extraction approach documented ([LEAN_EXTRACTION_STRATEGY.md](./LEAN_EXTRACTION_STRATEGY.md))
- [x] Automation script ready (`scripts/Create-ProductRepos.ps1`)
- [x] Test dummy script ready (`scripts/Create-TestDummy.ps1`) 🆕
- [x] Validation script ready (`scripts/Test-ProductRepos.ps1`) 🆕
- [x] Complete testing strategy documented ([COMPLETE_TESTING_STRATEGY.md](./COMPLETE_TESTING_STRATEGY.md)) 🆕

### 🧪 **Testing Infrastructure** 🆕
- [x] **Test Dummy Script:** Validates workflow before production repos
- [x] **Automated Validation:** Tests all 9 repos (venv, deps, server, edition)
- [x] **Quick Mode:** Fast smoke tests without dependency checks
- [x] **Selective Testing:** Test specific repos after fixes
- [x] **Integration Tests:** Feature-specific tests for Week 1-2

### 🔴 **Critical Pre-Flight Tasks** (Do These First!)

#### **Task P0.1: Wire B22.12 UI Export** ✅ COMPLETE
**Priority:** Must complete before repo creation  
**Why:** Express Edition needs working export functionality  
**Status:** ✅ Implementation complete - Ready for testing

**Implementation Summary:**
- ✅ Backend: `services/api/app/api/routes/b22_diff_export_routes.py` created
- ✅ Backend: Router registered in `main.py` at `/export/diff-report`
- ✅ Frontend: Export button added to `CompareSvgDualViewer.vue`
- ✅ Frontend: SVG → PNG capture via canvas
- ✅ Frontend: ZIP download with 3 screenshots + metadata.json
- ✅ Test script: `Test-B22-Export-P0.1.ps1` created

**Testing:**
```powershell
# Backend test
cd services\api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload

# In another terminal
.\Test-B22-Export-P0.1.ps1

# Frontend test
cd packages\client
npm run dev
# Navigate to Compare Lab → Load geometry → Click "📦 Export Diff Report"
```

**Validation Checklist:** See [P0_1_COMPLETION_CHECKLIST.md](./P0_1_COMPLETION_CHECKLIST.md)

**Estimated Time:** 1 hour ✅ (Actual: ~1 hour with drop-in bundle)

---

## 🚀 Phase 1 Execution Steps

### **Week 1: Repository Creation & Express Foundation**

**Total Time:** 24-36 hours (with lean extraction strategy)

#### **Step 0: Pre-Production Validation** (20 minutes) 🆕

**Test workflow before creating production repos:**

```powershell
# Create test dummy repository
.\scripts\Create-TestDummy.ps1

# Manual validation
cd ..\ltb-test-dummy\server
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
# Visit http://localhost:8000/ - should show {"status": "ready", "edition": "TEST_DUMMY"}

# If validation passes, cleanup
gh repo delete HanzoRazer/ltb-test-dummy --yes
Remove-Item "..\ltb-test-dummy" -Recurse -Force
```

**🚨 DO NOT PROCEED TO STEP 1.1 UNTIL TEST DUMMY PASSES**

See [COMPLETE_TESTING_STRATEGY.md](./COMPLETE_TESTING_STRATEGY.md) for full testing workflow.

#### **Step 1.1: Create Product Repositories** (2-3 hours)

**Lean Extraction Strategy** ✅ Implemented

Create **minimal skeleton repos** with automated dependency installation. Extract features from golden master only when building that specific product.

**Pre-flight:**
```powershell
# Authenticate GitHub CLI first
gh auth login

# Optional: Test with dry run
.\scripts\Create-ProductRepos.ps1 -DryRun
```

**Execute:**
```powershell
# Creates all 9 repos with automated Python setup
.\scripts\Create-ProductRepos.ps1
```

**What Gets Created Per Repo:**
- ✅ Directory structure: `client/src/`, `server/app/`, `docs/`
- ✅ Minimal `server/app/main.py` (5-line FastAPI skeleton)
- ✅ Minimal `client/index.html` (HTML placeholder)
- ✅ Python venv created and activated **automatically**
- ✅ Dependencies installed: `fastapi`, `uvicorn`, `pydantic`, `python-dotenv`
- ✅ `requirements.txt` generated **automatically**
- ✅ `.env.example` with edition flag
- ✅ README with extraction instructions
- ✅ .gitignore for Python + Node
- ❌ NO stub views (extract when building that product)
- ❌ NO boilerplate App.vue/router (add incrementally)

**Time Savings:**
- Template approach: 8-12 hours
- Lean approach: 2-3 hours (script runtime ~20-30 min)
- **Saved: 6-9 hours in Week 1**

**Why This Approach:**
1. **Leaner repos** - No unused code
2. **Cleaner extraction** - Copy only what's needed from golden master
3. **Easier updates** - Less drift between repos
4. **Faster creation** - Less copying overhead

**Deliverables:**
- ✅ 9 GitHub repositories created with minimal skeletons
- ✅ Python dependencies installed automatically
- ✅ Requirements.txt generated for each repo
- ✅ Each repo immediately runnable (minimal FastAPI endpoint)
- ⏳ Feature implementation happens in Steps 1.3-1.5

---

#### **Step 1.2: Validate All Repositories** (30 minutes)

**Automated Testing:** ✅ Script created

After repo creation, validate all 9 repos with automated test suite:

```powershell
# Full validation (tests dependencies + server startup)
.\scripts\Test-ProductRepos.ps1

# Quick validation (server startup only, faster)
.\scripts\Test-ProductRepos.ps1 -Quick

# Test specific repos
.\scripts\Test-ProductRepos.ps1 -RepoNames @("ltb-express", "ltb-pro")
```

**What Gets Tested:**
- ✅ Repository directory exists
- ✅ Python venv created successfully
- ✅ Dependencies installed (fastapi, uvicorn, pydantic, python-dotenv)
- ✅ `requirements.txt` generated
- ✅ Server starts and responds (HTTP 200)
- ✅ Edition flag correct in JSON response
- ✅ Each repo gets unique port (8000-8008)

**Expected Output:**
```
╔═══════════════════════════════════════╗
║  Test Summary                         ║
╚═══════════════════════════════════════╝

Repositories Tested: 9
Passed (Server + Edition): 9
Failed: 0

Detailed Results:
────────────────────────────────────────
Repository                     Dir      Venv     Dependencies  Server    Edition   
────────────────────────────────────────
ltb-express                    ✓        ✓        ✓             ✓         ✓
ltb-pro                        ✓        ✓        ✓             ✓         ✓
ltb-enterprise                 ✓        ✓        ✓             ✓         ✓
...

✅ ALL REPOSITORIES PASSED VALIDATION
Ready to proceed with feature extraction
```

**If Tests Fail:**
1. Check error messages in test output
2. Manually test failed repo:
   ```powershell
   cd ..\<repo-name>\server
   .\.venv\Scripts\Activate.ps1
   uvicorn app.main:app --reload
   # Visit http://localhost:8000/
   ```
3. Re-run creation for that specific repo if needed

**Validation Complete = Green Light for Feature Extraction**

---

#### **Step 1.3: Setup Express Edition Foundation** (4-6 hours)

**Approach: Extract from Golden Master, Don't Copy Stubs**

```powershell
cd ltb-express

# Server: Copy only what we need
mkdir -p server/app/api/routes
mkdir -p server/app/models
mkdir -p server/app/schemas

# Start with minimal main.py (not template - write fresh)
# Only include routes we're actually using
```

**Create Minimal `server/app/main.py`:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Luthier's ToolBox Express", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes will be added as we extract features
# from ..api.routes.rosette_routes import router as rosette_router
# app.include_router(rosette_router, prefix="/api/rosette", tags=["Rosette"])

@app.get("/")
def root():
    return {"edition": "EXPRESS", "version": "1.0.0"}
```

**Client: Fresh Vite Setup**
```powershell
cd client
npm create vite@latest . -- --template vue-ts
npm install vue-router pinia

# Create minimal App.vue (not from template)
# Add router as features are extracted
```

**Create Minimal `client/src/App.vue`:**
```vue
<template>
  <div id="app">
    <header>
      <h1>Luthier's ToolBox - Express Edition</h1>
    </header>
    <router-view />
  </div>
</template>

<script setup lang="ts">
// Minimal setup - features added during extraction
</script>

<style>
/* Basic styling - expand as features are added */
</style>
```

**Why This Approach:**
- ✅ **Clean slate** - Only add code you actually use
- ✅ **No stub bloat** - Empty views that never get filled in
- ✅ **Easier debugging** - Less code to wade through
- ✅ **Natural growth** - Repo grows with features, not templates

**Validation:**
- ✅ Server runs: `uvicorn app.main:app --reload`
- ✅ Returns: `{"edition": "EXPRESS", "version": "1.0.0"}`
- ✅ Client runs: `npm run dev`
- ✅ Shows: "Luthier's ToolBox - Express Edition" header

---

#### **Step 1.3: Extract Rosette Designer Lite** (12-18 hours)

**Source:** Golden master repo  
**Target:** `ltb-express/client/src/components/rosette/`

**Extraction Plan:**
1. **Identify source files:**
   ```powershell
   # In golden master repo
   cd "c:\Users\thepr\Downloads\Luthiers ToolBox\packages\client\src"
   
   # Find rosette-related files
   Get-ChildItem -Recurse -Filter "*rosette*" -File
   Get-ChildItem -Recurse -Filter "*Rosette*" -File
   ```

2. **Copy core rosette components:**
   ```powershell
   # Example files (adjust based on actual structure)
   $rosetteFiles = @(
     'components/rosette/RosetteDesigner.vue',
     'components/rosette/RingControl.vue',
     'components/rosette/PatternPresets.vue',
     'utils/rosetteGeometry.ts',
     'models/rosetteTypes.ts'
   )
   
   foreach ($file in $rosetteFiles) {
     Copy-Item ".\$file" "..\..\..\ltb-express\client\src\$file" -Force
   }
   ```

3. **Strip out Pro features:**
   - Remove CAM export buttons
   - Remove machine profile integrations
   - Keep: DXF, SVG, PDF export only
   - Keep: Basic presets and manual control

4. **Test rosette functionality:**
   ```powershell
   cd ltb-express\client
   npm run dev
   # Navigate to rosette designer, create a pattern, export DXF
   ```

**Deliverables:**
- ✅ Rosette designer renders correctly
- ✅ Pattern presets work
- ✅ Ring controls functional
- ✅ DXF/SVG/PDF export works
- ❌ No CAM features visible

---

#### **Step 1.4: Extract Curve Lab Mini** (10-15 hours)

**Source:** Golden master repo  
**Target:** `ltb-express/client/src/components/curves/`

**Similar extraction process:**
1. Find curve-related files in golden master
2. Copy core curve editing components
3. Strip Pro features (adaptive pocketing, G-code export)
4. Keep basic curve editing and DXF/SVG export
5. Test curve creation and export

**Deliverables:**
- ✅ Curve editor works
- ✅ Bezier/arc tools functional
- ✅ DXF/SVG export works
- ❌ No CAM features

---

#### **Step 1.5: Extract Fretboard Designer** (8-12 hours)

**Source:** Golden master repo  
**Target:** `ltb-express/client/src/components/fretboard/`

**Extraction focus:**
1. Fret spacing calculator
2. Scale length tools
3. Radius calculator
4. Basic inlay guide
5. DXF/SVG export

**Deliverables:**
- ✅ Fret calculator works
- ✅ Radius templates available
- ✅ Export functional

---

### **Week 2: Express Polish & Parametric Guitar Foundation**

#### **Step 2.1: Express Edition Polish** (8-12 hours)

**UI Improvements:**
- Replace stub dashboard with real feature navigation
- Add welcome screen with feature tour
- Implement recent files list
- Add export history panel

**Documentation:**
- Create user guide (PDF)
- Record demo videos (3-5 minutes each)
- Write feature comparison table (Express vs Pro)

**Testing:**
- Manual test all workflows
- Verify exports in Fusion 360/FreeCAD
- Check DXF compatibility

---

#### **Step 2.2: Setup Parametric Guitar Repo** (4-6 hours)

```powershell
cd ltb-parametric-guitar

# Server setup (same as Express)
cd server
Copy-Item ..\..\templates\server\main.py .\app\main.py
Copy-Item ..\..\templates\env\.env.parametric .\.env
# ... (install dependencies)

# Client setup
cd ..\client
npm create vite@latest . -- --template vue-ts
npm install vue-router pinia
Copy-Item ..\..\templates\client\App.vue .\src\App.vue
Copy-Item ..\..\templates\client\main.ts .\src\main.ts
Copy-Item ..\..\templates\client\router\index.ts .\src\router\index.ts
mkdir src\views
Copy-Item ..\..\templates\client\views\ParametricBodyDesigner.vue .\src\views\MainView.vue
```

---

#### **Step 2.3: Implement Body Shape Generator** (15-20 hours)

**Core Features:**
1. **Preset Shapes:**
   - Stratocaster (offset double-cutaway)
   - Telecaster (single-cutaway slab)
   - Les Paul (single-cutaway carved)
   - SG (double-cutaway)

2. **Parametric Controls:**
   ```typescript
   interface BodyParams {
     shape: 'strat' | 'tele' | 'lp' | 'sg'
     scaleLength: number  // mm
     stringCount: 6 | 7 | 8
     bridgeType: 'tremolo' | 'hardtail' | 'tom'
     neckPocketWidth: number
     neckPocketDepth: number
   }
   ```

3. **Geometry Generation:**
   - Use shapely/bezier libraries for curves
   - Generate boundary paths programmatically
   - Calculate bridge placement from scale length
   - Position neck pocket correctly

4. **Export Pipeline:**
   - DXF R12 format (CAM-ready)
   - SVG with dimensions
   - PDF with cut list

**Implementation Steps:**
```typescript
// src/utils/bodyShapes.ts
export function generateStratBody(params: BodyParams): BodyGeometry {
  const { scaleLength, bridgeType } = params
  
  // Calculate bridge position (2/3 of scale from nut)
  const bridgeX = (scaleLength * 2) / 3
  
  // Generate body outline
  const outline = [
    // Lower horn
    bezierCurve([...]),
    // Upper bout
    bezierCurve([...]),
    // Upper horn
    bezierCurve([...]),
    // ... etc
  ]
  
  return {
    outline,
    neckPocket: calculateNeckPocket(params),
    bridgeHoles: calculateBridgeHoles(bridgeType, bridgeX),
    controlCavity: generateControlCavity('strat')
  }
}
```

**Deliverables:**
- ✅ 4 body shapes working
- ✅ Parametric adjustments functional
- ✅ Bridge placement calculated correctly
- ✅ Neck pocket dimensions accurate
- ✅ DXF/SVG/PDF export validated

---

### **Week 3: Packaging & Distribution**

#### **Step 3.1: Desktop Packaging (Express)** (6-8 hours)

**Electron Integration:**
```powershell
cd ltb-express\client

# Install Electron
npm install --save-dev electron electron-builder

# Create main process
New-Item -Path electron\main.js -ItemType File
```

**main.js:**
```javascript
const { app, BrowserWindow } = require('electron')
const path = require('path')

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  })
  
  // Load from Vite dev server or built files
  if (process.env.NODE_ENV === 'development') {
    win.loadURL('http://localhost:5173')
  } else {
    win.loadFile(path.join(__dirname, '../dist/index.html'))
  }
}

app.whenReady().then(createWindow)
```

**package.json scripts:**
```json
{
  "scripts": {
    "electron:dev": "concurrently \"npm run dev\" \"electron .\"",
    "electron:build": "npm run build && electron-builder"
  }
}
```

**Build Configuration:**
```json
{
  "build": {
    "appId": "com.luthierstoolbox.express",
    "productName": "Luthier's ToolBox Express",
    "win": {
      "target": ["nsis", "zip"],
      "icon": "assets/icon.ico"
    },
    "mac": {
      "target": ["dmg", "zip"],
      "icon": "assets/icon.icns"
    }
  }
}
```

**Test Build:**
```powershell
npm run electron:build
# Test installer in dist/ folder
```

---

#### **Step 3.2: Etsy/Gumroad Setup** (8-12 hours)

**Etsy Shop Setup:**
1. Create Etsy seller account
2. Shop name: "LuthiersToolBox" or similar
3. Create product listings:

**Product 1: Parametric Guitar Designer**
- **Title:** "Guitar Body Design Software - Strat, Tele, Les Paul CAD Tool"
- **Price:** $39
- **Description:**
  ```
  Professional guitar body designer for luthiers and woodworkers.
  
  ✓ 4 Classic Body Shapes (Strat, Tele, LP, SG)
  ✓ Parametric Adjustments (scale, string count, bridge type)
  ✓ Automatic Bridge Placement & Neck Pocket
  ✓ Export DXF (CNC-ready) + SVG + PDF
  ✓ Instant Digital Download
  
  Perfect for CNC cutting, laser engraving, or hand routing templates.
  Windows & macOS compatible.
  ```
- **Photos:** 5-8 images (UI screenshots, example designs, finished guitars)
- **Tags:** guitar design, CAD software, lutherie, CNC, woodworking, luthier tools
- **Files:** Upload Windows + macOS installers

**Product 2: Express Edition (Future)**
- Similar listing structure
- Price: $49
- Focus on design suite capabilities

**Gumroad Setup:**
1. Create Gumroad account (backup platform)
2. Mirror Etsy listings
3. Set up automated delivery

**Payment Processing:**
- Etsy handles payments
- Gumroad uses Stripe
- Both deliver files automatically

---

### **Week 4: Launch & Validation**

#### **Step 4.1: Beta Testing** (4-6 hours)

**Beta Group:**
- 5-10 trusted users from existing user base
- Mix of hobbyists and professionals
- Diverse OS/hardware configurations

**Feedback Collection:**
```markdown
## Beta Test Checklist
- [ ] Installation successful (Windows/Mac)
- [ ] All features accessible
- [ ] Exports work in your CAM software
- [ ] No crashes or major bugs
- [ ] UI intuitive and clear
- [ ] Documentation helpful

## Feedback Questions:
1. Would you pay $39-49 for this?
2. What features are missing?
3. What would make this a "must-have"?
4. How does it compare to alternatives?
```

---

#### **Step 4.2: Launch Preparation** (6-8 hours)

**Marketing Materials:**
1. **Demo Videos:** (Record with OBS Studio)
   - Express Edition overview (3 min)
   - Parametric Guitar walkthrough (5 min)
   - Export workflow (2 min)

2. **Screenshots:** High-quality UI captures
   - Feature highlights
   - Before/after designs
   - Export examples

3. **Social Media Posts:**
   ```
   🎸 NEW: Luthier's ToolBox Express Edition!
   
   Professional guitar design tools for hobbyists & pros:
   ✓ Rosette Designer
   ✓ Curve Lab
   ✓ Fretboard Calculator
   ✓ CAD Export (DXF/SVG/PDF)
   
   $49 one-time. No subscription.
   Download now: [link]
   ```

4. **Blog Post/Website:**
   - Feature announcement
   - Pricing justification
   - Comparison table (Express vs Pro vs Enterprise)

---

#### **Step 4.3: Soft Launch** (1 day)

**Launch Sequence:**
1. **Day 1 Morning:** Publish Etsy listings
2. **Day 1 Afternoon:** Share with beta testers
3. **Day 2:** Post to relevant forums:
   - Reddit: r/Luthier, r/Lutherie
   - Forum.mimf.com (Musical Instrument Makers Forum)
   - Facebook lutherie groups
4. **Day 3-7:** Monitor feedback, fix critical bugs

**Success Metrics (Week 1):**
- 🎯 5 sales (validates pricing)
- 🎯 10 downloads (validates interest)
- 🎯 3 positive reviews
- 🎯 No major bug reports

---

#### **Step 4.4: Iterate Based on Feedback** (8-12 hours)

**Common Expected Feedback:**
1. "Missing feature X" → Evaluate for Pro tier or future update
2. "Price too high" → Consider early-bird discount
3. "Bug in workflow Y" → Hot-fix immediately
4. "Need tutorial for Z" → Create quick video

**Update Cycle:**
- Fix critical bugs within 24 hours
- Ship point releases (v1.0.1, v1.0.2) weekly
- Plan v1.1 features based on feedback

---

## 📊 Success Criteria

### **Minimum Viable Success:**
- ✅ 2 products published (Express + Parametric)
- ✅ 10 total sales ($390+ revenue)
- ✅ No critical bugs reported
- ✅ Positive feedback from beta testers

### **Target Success:**
- ✅ 50 total sales ($1,950+ revenue)
- ✅ 5+ five-star reviews
- ✅ Organic social media shares
- ✅ Requests for Pro Edition features

### **Stretch Goals:**
- ✅ 100 sales ($3,900+ revenue)
- ✅ Featured in lutherie newsletter/blog
- ✅ Request for bulk/education licenses
- ✅ Competitor acknowledgment

---

## 🚨 Risk Mitigation

### **Technical Risks:**
| Risk | Mitigation | Owner |
|------|-----------|-------|
| Extraction breaks features | Comprehensive testing before launch | Dev |
| Export format incompatibility | Validate with multiple CAM tools | Beta testers |
| Desktop packaging issues | Test on clean VM installations | Dev |

### **Market Risks:**
| Risk | Mitigation | Owner |
|------|-----------|-------|
| No sales first week | Lower price temporarily, expand promotion | Marketing |
| Clone appears quickly | Already built into strategy (Express is decoy) | Strategy |
| Negative reviews | Respond quickly, fix issues, offer refunds | Support |

### **Operational Risks:**
| Risk | Mitigation | Owner |
|------|-----------|-------|
| Support overwhelm | Create FAQ, video tutorials, automate common questions | Support |
| Update distribution | Use auto-update in Electron, notify Etsy buyers | Dev |
| Payment disputes | Clear refund policy, good documentation | Finance |

---

## 📅 Timeline Summary

| Week | Focus | Hours | Deliverables |
|------|-------|-------|--------------|
| 1 | Repos + Express Foundation | 24-36 | Repos created, Express skeleton, Rosette extracted |
| 2 | Express features + Parametric start | 20-30 | Curve/Fretboard extracted, Parametric foundation |
| 3 | Packaging + Distribution | 14-20 | Desktop builds, Etsy setup |
| 4 | Launch + Iterate | 10-16 | Live products, first sales, feedback integration |
| **Total** | | **68-102** | **2 revenue-generating products** |

---

## 🎯 Next Immediate Actions

**TODAY:**
1. ✅ Read this plan ← You're here
2. ✅ P0.1 Complete (B22.12 UI export wired) ← **DONE!**
3. 🧪 Test P0.1 implementation:
   ```powershell
   # Backend test
   .\Test-B22-Export-P0.1.ps1
   
   # Frontend test
   cd packages\client
   npm run dev
   # → Navigate to Compare Lab → Test export button
   ```
4. 📝 Commit P0.1 if tests pass

**TOMORROW:**
1. Run `Create-ProductRepos.ps1` (dry-run first)
2. Create actual GitHub repos
3. Setup ltb-express skeleton (server + client)

**THIS WEEK:**
1. Complete P0.1 testing and commit
2. Create 9 product repos
3. Begin Express feature extraction

**WEEK 1 END GOAL:**
- Express Edition rendering correctly with Rosette Designer
- Parametric Guitar repo scaffolded
- Clear path to Week 2 features

---

## 📚 Reference Documents

- [Master Segmentation Strategy](./docs/products/MASTER_SEGMENTATION_STRATEGY.md)
- [Product Repo Setup Guide](./PRODUCT_REPO_SETUP.md)
- [Unresolved Tasks Inventory](./UNRESOLVED_TASKS_INVENTORY.md)
- [B22.12 Export Documentation](./docs/B22_12_EXPORTABLE_DIFF_REPORTS.md)
- [Create-ProductRepos.ps1](./scripts/Create-ProductRepos.ps1)

---

**Status:** ✅ Plan Ready for Execution  
**Blocking Task:** B22.12 UI Export Wiring (1 hour)  
**Ready to Start:** After B22.12 complete  
**First Milestone:** Week 1 - Repos created + Express foundation  
**End Goal:** 2 products generating revenue within 4 weeks
