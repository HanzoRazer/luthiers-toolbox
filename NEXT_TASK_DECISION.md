# Next Task Decision: P2.2 vs N15-N18 Frontend

**Date:** November 16, 2025  
**Decision Required:** Choose between two major tasks

---

## 📊 Quick Comparison

| Aspect | **P2.2 DXF Preflight** | **N15-N18 Frontend Build** |
|--------|------------------------|----------------------------|
| **Backend Status** | ✅ Core exists (809 lines) | ✅ 100% Complete |
| **Frontend Status** | ❌ None | ❌ Needs implementation |
| **Documentation** | ⚠️ Minimal | ✅ Complete handoff (1,449 lines) |
| **Estimated Time** | 3-4 hours | 12-16 hours |
| **Complexity** | Medium | High |
| **User Impact** | Moderate (validation) | High (3 new tools) |
| **Dependencies** | None | Backend N15-N18 (ready) |
| **Dashboard Impact** | None | Updates N15 card status |

---

## 🎯 Option 1: P2.2 DXF Preflight

### **Current State**
- ✅ Backend core: `services/api/app/cam/dxf_preflight.py` (809 lines)
- ❌ No router registered in main.py
- ❌ No frontend component
- ❌ No route or navigation

### **What Needs Implementation**

**Backend (1-2 hours):**
1. Create router: `services/api/app/routers/dxf_preflight_router.py`
   - `POST /api/cam/preflight/validate` - Run validation
   - `GET /api/cam/preflight/health` - Health check
2. Register in main.py (safe import pattern)
3. Add smoke test: `smoke_dxf_preflight.ps1`

**Frontend (2-3 hours):**
1. Create component: `client/src/components/toolbox/DXFPreflightLab.vue`
   - File upload area
   - Validation results display (errors, warnings, info)
   - HTML report download
   - Entity statistics
2. Add route: `/lab/dxf-preflight`
3. Update CAM Dashboard card (currently missing)

**Testing (30 minutes):**
- Test with valid DXF (guitar body)
- Test with open paths (should error)
- Test with missing layers (should warn)
- Test HTML report generation

**Estimated Total:** 3-4 hours

---

## 🎯 Option 2: N15-N18 Frontend Build

### **Current State**
- ✅ Backend N15: Complete (`/api/cam/backplot/parse`)
- ✅ Backend N16: Complete (adaptive benchmark router)
- ✅ Backend N17: Complete (polygon offset, pyclipper)
- ✅ Backend N18: Complete (arc linkers)
- ✅ Complete handoff doc: `N16_N18_FRONTEND_DEVELOPER_HANDOFF.md` (1,449 lines)
- ✅ All component specs with full code templates
- ⏳ CAM Dashboard N15 card exists (PLANNED badge, path: `#`)

### **What Needs Implementation**

**Component 1: BackplotGcode.vue (N15)** (3-4 hours)
- 157 lines (spec complete)
- Two-column layout: G-code input | SVG preview + stats
- Features:
  - Paste G-code or upload NC file
  - Feed rate and units controls
  - Generate backplot button
  - SVG visualization (G0 red dashed, G1 blue, G2/G3 green arcs)
  - Statistics: Total length, cutting length, rapid moves, arc count
  - Time estimation with rapid/feed awareness
  - Download SVG button
- API wrapper: `n15.ts` (118 lines spec)
- Route: `/cam/backplot` (new)

**Component 2: AdaptiveBench.vue (N16)** (3-4 hours)
- 193 lines (spec complete)
- Mode toggle: Spiral vs Trochoid
- Parameters: width, height, tool_dia, stepover/arc_radius
- SVG preview with canvas rendering
- Performance metrics display
- Download G-code button
- API wrapper: `n16.ts` (54 lines spec)
- **Note:** Backend already exists at `/cam/adaptive2/bench` ✅

**Component 3: AdaptivePoly.vue (N17+N18)** (4-5 hours)
- 242 lines (spec complete)
- N17/N18 mode toggle (Offset vs Arc Linkers)
- Polygon JSON input (textarea)
- Offset parameters: tool_dia, stepover, join_type, arc_tolerance
- Arc linker parameters: feed_xy, feed_floor, min_radius
- G-code output with stats (line count, arc count, G2/G3 breakdown)
- Download NC files button
- API wrapper: `n17_n18.ts` (88 lines spec)
- **Note:** Backend already exists ✅

**Integration Hub: ArtStudioCAM.vue** (1-2 hours)
- 86 lines (spec complete)
- 4-tool tab navigation: Backplot | Bench | Poly | Helical
- Renders selected component
- Dashboard entry point

**Router + Navigation** (30 minutes)
- Add 4 routes: `/cam/backplot`, `/cam/bench`, `/cam/poly`, `/art-studio-cam`
- Add ArtStudioCAM.vue to Art Studio Dashboard (new card)
- Update N15 Backplot card: path `#` → `/cam/backplot`, status Coming Soon → Beta

**Testing** (1 hour)
- Test N15 backplot with sample G-code
- Test N16 bench spiral vs trochoid
- Test N17 offset with square polygon
- Test N18 arc linkers with same polygon
- Verify tab navigation in ArtStudioCAM

**Estimated Total:** 12-16 hours

---

## 🎯 Recommendation: **N15-N18 Frontend Build**

### **Why N15-N18 is the Better Choice Right Now:**

**1. Complete Specifications Ready** ✅
- 1,449-line handoff document with full component code
- All TypeScript interfaces defined
- API wrappers spec'd out (260 lines total)
- Zero ambiguity - just implement as written

**2. High User Impact** 🚀
- Adds **3 major tools** to the platform
- Unlocks N15 Backplot (most requested CAM feature)
- Completes N16-N18 backend integration story
- Updates N15 dashboard card from PLANNED → Beta

**3. Clean Dependency Chain** ✅
- Backend 100% complete (verified in Priority 1 check)
- No blocking issues
- API endpoints tested and documented
- Zero integration risk

**4. Progressive Delivery Possible** 📦
- Can implement components incrementally:
  1. Day 1-2: BackplotGcode.vue (N15) - immediate value
  2. Day 3: AdaptiveBench.vue (N16) - benchmarking tool
  3. Day 4-5: AdaptivePoly.vue (N17+N18) - advanced workflows
  4. Day 6: ArtStudioCAM.vue hub - tie it together

**5. Dashboard Completion** ✅
- N15 card already exists with PLANNED badge
- Just needs path update and status change
- Immediate visual feedback of progress

---

## 🛑 Why Defer P2.2 DXF Preflight:

**1. Incomplete Specification**
- No component design document
- No API wrapper spec
- No error handling strategy
- Would need 1-2 hours planning before coding

**2. Lower User Impact**
- Validation is "nice to have" not "must have"
- Users can work around bad DXF files (export again)
- Not blocking any workflows

**3. Less Exciting**
- Utility feature, not creative tool
- Won't demonstrate platform capabilities
- Won't generate user enthusiasm

**4. Can Be Done Later**
- Good candidate for Priority 3 (Developer Experience)
- Pairs well with testing/documentation push
- Not time-sensitive

---

## 📋 Recommended Action Plan

### **This Session: Start N15 (BackplotGcode.vue)**
**Estimated:** 3-4 hours for complete implementation

```powershell
# 1. Create API wrapper (30 min)
client/src/api/n15.ts

# 2. Create component (2 hours)
client/src/components/toolbox/BackplotGcode.vue

# 3. Add route (10 min)
# Update client/src/router/index.ts

# 4. Update dashboard card (10 min)
# client/src/views/CAMDashboard.vue
# - path: '#' → '/cam/backplot'
# - status: 'Coming Soon' → 'Beta'
# - badge: 'PLANNED' → 'NEW'

# 5. Test (30 min)
# - Paste sample G-code
# - Generate backplot
# - Verify SVG visualization
# - Test download
```

### **Next Sessions:**
- Session 6A (3-4 hours): AdaptiveBench.vue (N16)
- Session 6B (4-5 hours): AdaptivePoly.vue (N17+N18)
- Session 6C (1-2 hours): ArtStudioCAM.vue hub + final integration

**Total Timeline:** 3 sessions (12-16 hours) to complete all N15-N18 frontend

---

## 🎯 Final Decision

**Proceed with N15-N18 Frontend Build** starting with N15 (BackplotGcode.vue)

**Rationale:**
- Complete specs eliminate planning overhead
- High user value (G-code visualization is #1 requested feature)
- Clean dependency chain (backend ready)
- Dashboard completion (N15 card update)
- Progressive delivery model (can ship incrementally)

**Defer P2.2 DXF Preflight to Priority 3 or later session**

---

**Ready to start N15 implementation?** 🚀
