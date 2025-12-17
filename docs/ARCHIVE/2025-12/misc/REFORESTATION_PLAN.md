# 🌲 Re-Forestation Plan: CAM & Art Studio Scaffolding

**Status:** 🚧 Planning Phase  
**Date:** November 13, 2025  
**Mission:** Build foundational scaffolds for CAM section and Art Studio, then integrate unintegrated code snippets  
**Philosophy:** "Clear the forest" → "Re-plant the forest" with organized architecture

---

## 🎯 Overview

After the successful "forest clearing" integration (FOREST_CLEARING_COMPLETE.md), we have **high-quality unintegrated patches** waiting for deployment. This plan organizes them into two major scaffolding efforts:

1. **CAM Section Scaffold** - Unified CNC toolpath generation hub
2. **Art Studio Scaffold** - Decorative lutherie design tools hub

Then systematically integrate available patches into these scaffolds.

---

## 📦 Unintegrated Code Inventory

### **🎨 Art Studio Patches** (Ready to Integrate)

#### **Art Studio v16.1 - Helical Z-Ramping** ⭐⭐⭐⭐⭐
**Status:** ✅ Complete, Documented, Tested  
**Location:** `ART_STUDIO_V16_1_HELICAL_INTEGRATION.md` (504 lines)  
**Priority:** P1 (Critical for hardwood lutherie)

**Files Ready:**
- ✅ Backend: `services/api/app/routers/cam_helical_v161_router.py` (165 lines)
- ✅ Frontend API: `packages/client/src/api/v161.ts` (20 lines)
- ✅ Frontend UI: `packages/client/src/views/HelicalRampLab.vue` (60 lines)
- ✅ Test Script: `smoke_v161_helical.ps1` (PowerShell smoke test)
- ✅ CI Badge: `.github/workflows/helical_badges.yml`

**API Endpoints:**
```
GET  /api/cam/toolpath/helical_health
POST /api/cam/toolpath/helical_entry
```

**Integration Effort:** Low (2-3 hours)
- Router already written and tested
- Vue component standalone (no dependencies)
- Just needs route registration and navigation entry

**Use Cases:**
- Bridge pocket entry (acoustic guitar)
- Neck cavity plunging (hardwood)
- Control cavity drilling (electric guitar)
- Pickup routing (reduces tool breakage by 50%)

---

#### **Art Studio v16.0 - SVG Editor + Relief Mapper** ✅
**Status:** Already Integrated  
**Files Active:**
- `services/api/app/routers/cam_relief_v160_router.py`
- `services/api/app/routers/cam_svg_v160_router.py`
- `packages/client/src/views/ReliefMapperLab.vue`

**Notes:** Gold standard for Art Studio design philosophy. Used as reference for v16.1 integration.

---

#### **Art Studio v15.5 - Post-Processor (CRC, Lead-In/Out)** ✅
**Status:** Already Integrated  
**Files Active:**
- `services/api/app/routers/cam_post_v155_router.py`
- `services/api/app/routers/cam_smoke_v155_router.py`

**Notes:** Production-ready post-processor with cutter radius compensation and entry/exit strategies.

---

#### **Art Studio v13 - V-Carve Add-On** ⚠️
**Status:** Documented but Not in Active Codebase  
**Location:** `VCARVE_ADDON_DEVELOPER_HANDOFF.md` (790+ lines)

**Files Available (Legacy):**
- `server/vcarve_router.py` (legacy location)
- `frontend/views/ArtStudio.vue` (legacy location)
- `manage_v13.ps1` - Management script
- `ltb_v13_dependency_pin.patch` - Dependency pinning
- `ltb_v13_revert.patch` - Uninstall patch

**Decision Needed:** Upgrade to v16.x architecture or archive?
- ⚠️ Legacy code uses old FastAPI patterns
- ⚠️ Frontend uses Options API (pre-Composition API)
- ✅ Algorithm (centerline infill) is solid
- ✅ Raster mode works well

**Recommendation:** Archive v13, extract algorithm, rewrite as v16.2 if needed.

---

### **🔧 CAM Patches** (Ready to Integrate)

#### **Patch N17 - Polygon Offset with Pyclipper + Arc Linkers** ⭐⭐⭐⭐⭐
**Status:** Ready, High Priority  
**Priority:** P1 (Replaces L.1 basic offsetting)

**Location:** Documented in `A_N_BUILD_ROADMAP.md`  
**Files:** `polyclip_v17/` (not yet in codebase)

**Features:**
- Robust polygon offsetting (no self-intersection)
- Arc-link injection for smooth transitions
- Min engagement angle control (prevent tool overload)
- Island handling with clearance zones

**Integration Tasks:**
- [ ] Copy `polyclip_v17/` → `services/api/app/cam/`
- [ ] Create router: `cam_polyclip_v17_router.py`
- [ ] Extend Module L to use pyclipper engine
- [ ] Add min-engagement controls to adaptive UI
- [ ] Create smoke test: `smoke_n17_polyclip.ps1`

**Integration Effort:** Medium (1 week)
- Algorithm complete
- Needs FastAPI router wrapper
- UI integration with Module L controls

---

#### **Patch N16 - Adaptive Spiral + Trochoidal Bench** ⭐⭐⭐⭐⭐
**Status:** Ready, Testing Framework  
**Priority:** P1 (Validates Module L.3 performance)

**Location:** Documented in `A_N_BUILD_ROADMAP.md`

**Features:**
- Benchmark suite for adaptive toolpaths
- Cycle time comparisons (spiral vs lanes)
- Trochoidal vs linear performance data
- CSV export for performance reports

**Integration Tasks:**
- [ ] Copy benchmark scripts → `services/api/tests/benchmarks/`
- [ ] Create comparison dashboard UI
- [ ] Generate performance reports (CSV export)
- [ ] Document: `PATCH_N16_BENCHMARK_GUIDE.md`

**Integration Effort:** Low (3-4 days)
- Benchmarks are standalone Python scripts
- Dashboard is simple data visualization
- No new algorithms to implement

---

#### **Patch N0-N10 - CAM Essentials Rollup** ⭐⭐⭐⭐
**Status:** Ready, Large Integration  
**Priority:** P1 (Completes post-processor ecosystem)

**Location:** `PATCH_N_SERIES_ROLLUP.md` (644 lines)

**Patches Included:**
1. **N.0** - Smart Post Configurator (1100 lines spec)
2. **N.01** - Roughing Integration (800 lines, 90-min example)
3. **N.03** - Standardization Framework (900 lines)
4. **N.03** - Drop-In Middleware (200 lines production code) ✅
5. **N.04** - Router Snippets (700 lines copy-paste patterns)
6. **N.04c** - Helper Utilities (500 lines convenience functions) ✅
7. **N.05** - Fanuc/Haas Support (TBD, planned)
8. **N.06** - Modal Cycles (G81-G89) (TBD)
9. **N.07** - Drilling UI (TBD)
10. **N.08** - Retract Patterns + Tools (TBD)
11. **N.09** - Probe Patterns + SVG Export (TBD)
12. **N.10** - CAM Essentials Unified API (TBD)

**Already Integrated:**
- ✅ N.03 Drop-In Middleware (`post_injection_dropin.py`)
- ✅ N.04c Helper Utilities (`post_injection_helpers.py`)

**Integration Tasks:**
- [ ] Complete N.01 roughing router
- [ ] Standardize all CAM routers with N.03 framework
- [ ] Add N.06 modal cycles support
- [ ] Build N.07 drilling UI component
- [ ] Implement N.08 retract patterns
- [ ] Add N.09 probing patterns
- [ ] Create N.10 unified API endpoint

**Integration Effort:** High (2-3 weeks)
- 10+ patches to consolidate
- Requires coordination across routers
- UI components for drilling, probing

---

#### **Patch N15 - G-code Backplot + Time Estimator** ✅
**Status:** Already Integrated  
**Files Active:**
- `services/api/app/routers/gcode_backplot_router.py`
- Time estimation in Module L (`feedtime.py`, `feedtime_l3.py`)

---

#### **Patch N18 - G2/G3 Arc Linkers + Feed Floors** ✅
**Status:** Already Integrated  
**Features:** Arc linking in Module L.2, feed floor constraints

---

#### **Patch N12 - Machine + Tool Tables** ✅
**Status:** Complete  
**Location:** `PATCH_N12_IMPLEMENTATION_SUMMARY.md`  
**Files Active:**
- `services/api/app/routers/machines_tools_router.py`
- Machine + tool CRUD endpoints

---

### **🧪 Simulation & Visualization Patches**

#### **Patch I.1.2 - Simulation with Arcs** ⭐⭐⭐⭐
**Status:** Ready  
**Priority:** P2 (Improves toolpath validation)

**Features:**
- Arc interpolation (G2/G3 → line segments)
- Time scrubber (slider for progress)
- Speed heatmap (color-coded by feed rate)
- Material removal visualization

**Integration Tasks:**
- [ ] WebGL arc rendering
- [ ] Slider UI component
- [ ] Heatmap color gradient
- [ ] 3D material removal (Three.js)

**Integration Effort:** Medium (1 week)
- Requires WebGL experience
- Three.js scene setup
- Performance optimization for large toolpaths

---

#### **Patch I.1.3 - Web Workers for Simulation** ⭐⭐⭐
**Status:** Ready  
**Priority:** P2 (Performance for complex parts)

**Features:**
- Offload simulation to background threads
- Non-blocking UI during computation
- Progress reporting

**Integration Effort:** Low (2-3 days)
- Wrap existing simulation in Web Worker
- Add progress callback hooks

---

### **🔧 Utility & QoL Patches**

#### **CurveLab - DXF Preflight Validation** ⭐⭐⭐⭐
**Status:** Ready  
**Priority:** P2 (Prevents CAM import failures)

**Features:**
- Closed path validation (no open polylines for pockets)
- Duplicate vertex cleanup
- Scale verification (mm vs inch)
- Layer structure validation
- Tolerance sanity checks (0.001-1.0mm)

**Integration Tasks:**
- [ ] Pre-export modal: "DXF Preflight Report"
- [ ] Auto-fix suggestions (one-click cleanup)
- [ ] Markdown export for documentation

**Integration Effort:** Low (3-4 days)
- Validation logic straightforward
- UI is simple modal dialog

---

#### **CurveLab - Markdown Reports** ⭐⭐⭐
**Status:** Ready  
**Priority:** P2 (Documentation generation)

**Features:**
- Export toolpath reports as Markdown
- Embed statistics, parameters, geometry previews
- Link to generated files (DXF, SVG, NC)

**Integration Effort:** Low (2 days)
- Template-based generation
- Simple download button

---

#### **Bridge Calculator** ⭐⭐⭐
**Status:** Ready  
**Priority:** P2 (Essential lutherie tool)

**Calculations:**
- Saddle height (action + neck angle)
- String spacing (nut to bridge)
- Compensation (intonation offsets)
- Pin hole layout (6-string, 12-string)

**Integration Tasks:**
- [ ] Vue component with input fields
- [ ] Calculation engine (simple trig)
- [ ] Visual diagram of bridge geometry
- [ ] Export to DXF for machining

**Integration Effort:** Low (3 days)
- Standalone calculator
- No CAM dependencies

---

#### **Wiring Workbench** ⭐⭐
**Status:** Documented  
**Priority:** P3 (Nice-to-have for electric guitars)

**Features:**
- Electronics layout planner
- Wiring diagrams (pickups, pots, switches)
- Finish planner (stain, clear coat schedules)

**Integration Effort:** Medium (1 week)
- Requires SVG diagramming
- Database for wiring templates

---

### **📊 Post-Processor Patches**

#### **Patch J.1 - Post Injection System** ✅
**Status:** Already Integrated (as N.03 Drop-In)  
**Files Active:** `post_injection_dropin.py`

---

#### **Patch J.2 - All-in-One Post System** ✅
**Status:** Already Integrated (as N.04c Helpers)  
**Files Active:** `post_injection_helpers.py`

---

## 🏗️ Scaffold Architecture Plan

### **1. CAM Section Scaffold**

**Purpose:** Unified hub for all CNC toolpath generation and export operations.

**Structure:**
```
packages/client/src/views/CAMSection/
├── CAMDashboard.vue              # Main entry point with operation cards
├── AdaptivePocketLab.vue         # Module L (already exists)
├── HelicalRampLab.vue            # v16.1 (ready to integrate)
├── PolygonOffsetLab.vue          # N17 (future)
├── DrillingLab.vue               # N.07 (future)
├── ProbingLab.vue                # N.09 (future)
├── SimulationViewer.vue          # I.1.2 (future)
└── ExportWizard.vue              # Multi-post bundle export
```

**Router Configuration:**
```typescript
// packages/client/src/router/index.ts
{
  path: '/cam',
  component: () => import('../views/CAMSection/CAMDashboard.vue'),
  meta: { title: 'CAM Operations' },
  children: [
    { path: 'adaptive', component: AdaptivePocketLab, meta: { title: 'Adaptive Pocketing' } },
    { path: 'helical', component: HelicalRampLab, meta: { title: 'Helical Ramping' } },
    { path: 'polygon', component: PolygonOffsetLab, meta: { title: 'Polygon Offset' } },
    { path: 'drilling', component: DrillingLab, meta: { title: 'Drilling Patterns' } },
    { path: 'probing', component: ProbingLab, meta: { title: 'Probe Patterns' } },
    { path: 'sim', component: SimulationViewer, meta: { title: 'Toolpath Simulation' } }
  ]
}
```

**Navigation Menu:**
```vue
<!-- packages/client/src/components/MainNav.vue -->
<template>
  <nav>
    <RouterLink to="/">Home</RouterLink>
    <RouterLink to="/cam">CAM Operations</RouterLink>
    <RouterLink to="/art-studio">Art Studio</RouterLink>
    <RouterLink to="/calculators">Calculators</RouterLink>
  </nav>
</template>
```

**Dashboard Cards:**
```vue
<!-- CAMDashboard.vue -->
<template>
  <div class="cam-dashboard">
    <h1>CAM Operations</h1>
    <div class="operation-grid">
      <OperationCard
        title="Adaptive Pocketing"
        description="Spiral and lane-based pocket milling with trochoidal insertion"
        icon="🌀"
        path="/cam/adaptive"
        status="Production"
      />
      <OperationCard
        title="Helical Ramping"
        description="Smooth spiral entry for plunge operations"
        icon="🌊"
        path="/cam/helical"
        status="Production"
      />
      <OperationCard
        title="Polygon Offset"
        description="Robust offsetting with min-engagement control"
        icon="🔺"
        path="/cam/polygon"
        status="Beta"
      />
      <OperationCard
        title="Drilling Patterns"
        description="Modal cycles (G81-G89) for hole arrays"
        icon="🔩"
        path="/cam/drilling"
        status="Coming Soon"
      />
      <!-- More cards... -->
    </div>
  </div>
</template>
```

**Backend Router Group:**
```python
# services/api/app/main.py
from .routers import (
    adaptive_router,
    cam_helical_v161_router,
    # ... other CAM routers
)

# Register all under /api/cam prefix
app.include_router(adaptive_router, prefix="/cam/pocket/adaptive", tags=["CAM"])
app.include_router(cam_helical_v161_router, prefix="/cam/toolpath", tags=["CAM"])
# ...
```

---

### **2. Art Studio Scaffold**

**Purpose:** Decorative lutherie design tools hub (v-carving, relief mapping, rosettes).

**Structure:**
```
packages/client/src/views/ArtStudio/
├── ArtStudioDashboard.vue        # Main entry point with design cards
├── ReliefMapperLab.vue           # v16.0 (already exists)
├── RosetteLab.vue                # v16.0 (already exists)
├── HelicalRampLab.vue            # v16.1 (ready to integrate) ⭐
├── VCarveEditor.vue              # v16.2 (future, upgraded from v13)
└── InlayDesigner.vue             # v16.3 (future)
```

**Router Configuration:**
```typescript
// packages/client/src/router/index.ts
{
  path: '/art-studio',
  component: () => import('../views/ArtStudio/ArtStudioDashboard.vue'),
  meta: { title: 'Art Studio' },
  children: [
    { path: 'relief', component: ReliefMapperLab, meta: { title: 'Relief Mapper' } },
    { path: 'rosette', component: RosetteLab, meta: { title: 'Rosette Designer' } },
    { path: 'helical', component: HelicalRampLab, meta: { title: 'Helical Ramping' } },
    { path: 'vcarve', component: VCarveEditor, meta: { title: 'V-Carve Editor' } },
    { path: 'inlay', component: InlayDesigner, meta: { title: 'Inlay Designer' } }
  ]
}
```

**Dashboard Cards:**
```vue
<!-- ArtStudioDashboard.vue -->
<template>
  <div class="art-studio-dashboard">
    <h1>Art Studio</h1>
    <p>Decorative lutherie design tools for CNC machining</p>
    <div class="design-grid">
      <DesignCard
        title="Relief Mapper"
        description="SVG to 3D relief carving with depth control"
        icon="🗿"
        path="/art-studio/relief"
        status="Production"
        version="v16.0"
      />
      <DesignCard
        title="Rosette Designer"
        description="Parametric acoustic guitar rosettes"
        icon="🌺"
        path="/art-studio/rosette"
        status="Production"
        version="v16.0"
      />
      <DesignCard
        title="Helical Ramping"
        description="Smooth spiral entry for hardwood plunging"
        icon="🌊"
        path="/art-studio/helical"
        status="Beta"
        version="v16.1"
        badge="NEW"
      />
      <DesignCard
        title="V-Carve Editor"
        description="Centerline art to decorative V-grooves"
        icon="✏️"
        path="/art-studio/vcarve"
        status="Coming Soon"
        version="v16.2"
      />
      <!-- More cards... -->
    </div>
  </div>
</template>
```

---

## 🚀 Integration Roadmap

### **Phase 1: Foundation Scaffolds** (Week 1)
**Goal:** Build navigation and dashboard structure

**Tasks:**
1. [ ] Create `CAMDashboard.vue` with operation cards
2. [ ] Create `ArtStudioDashboard.vue` with design cards
3. [ ] Update `MainNav.vue` with CAM and Art Studio links
4. [ ] Register routes in `router/index.ts`
5. [ ] Add placeholder cards for future features
6. [ ] Style dashboards with grid layout
7. [ ] Add status badges (Production, Beta, Coming Soon)

**Deliverable:** Working navigation between Home → CAM → Art Studio sections

---

### **Phase 2: Art Studio v16.1 Integration** (Week 1-2)
**Goal:** Integrate helical ramping into Art Studio

**Tasks:**
1. [ ] Copy `cam_helical_v161_router.py` → `services/api/app/routers/`
2. [ ] Register router in `main.py` with try/except pattern
3. [ ] Copy `v161.ts` API wrapper → `packages/client/src/api/`
4. [ ] Copy `HelicalRampLab.vue` → `packages/client/src/views/ArtStudio/`
5. [ ] Add route: `/art-studio/helical`
6. [ ] Update `ArtStudioDashboard.vue` with helical card
7. [ ] Run smoke test: `smoke_v161_helical.ps1`
8. [ ] Update CI badge workflow
9. [ ] Mark as "Production" in dashboard

**Deliverable:** Working helical ramping tool in Art Studio section

---

### **Phase 3: CAM Essentials (N17) Integration** (Week 2-3)
**Goal:** Add polygon offset with min-engagement control

**Tasks:**
1. [ ] Copy `polyclip_v17/` → `services/api/app/cam/`
2. [ ] Create `cam_polyclip_v17_router.py`
3. [ ] Extend Module L to use pyclipper engine
4. [ ] Create `PolygonOffsetLab.vue` component
5. [ ] Add route: `/cam/polygon`
6. [ ] Update `CAMDashboard.vue` with polygon card
7. [ ] Add min-engagement controls to UI
8. [ ] Create smoke test: `smoke_n17_polyclip.ps1`
9. [ ] Document: `PATCH_N17_INTEGRATION_SUMMARY.md`

**Deliverable:** Production-grade polygon offsetting in CAM section

---

### **Phase 4: Benchmark Suite (N16) Integration** (Week 3)
**Goal:** Validate Module L.3 performance with benchmarks

**Tasks:**
1. [ ] Copy benchmark scripts → `services/api/tests/benchmarks/`
2. [ ] Create `BenchmarkDashboard.vue` component
3. [ ] Add route: `/cam/benchmarks`
4. [ ] Generate CSV performance reports
5. [ ] Add comparison charts (Chart.js or similar)
6. [ ] Document: `PATCH_N16_BENCHMARK_GUIDE.md`

**Deliverable:** Benchmark dashboard showing adaptive vs trochoidal performance

---

### **Phase 5: CAM Essentials Rollup (N0-N10)** (Week 4-6)
**Goal:** Complete post-processor ecosystem

**Tasks:**
1. [ ] Integrate N.01 roughing router
2. [ ] Standardize all CAM routers with N.03 framework
3. [ ] Add N.06 modal cycles support (G81-G89)
4. [ ] Build N.07 `DrillingLab.vue` component
5. [ ] Implement N.08 retract patterns
6. [ ] Add N.09 `ProbingLab.vue` component
7. [ ] Create N.10 unified API endpoint: `/api/cam/essentials/complete`
8. [ ] Update all CAM cards with unified post-processor

**Deliverable:** Complete CAM essentials system with drilling, probing, retract patterns

---

### **Phase 6: Simulation & Visualization (I.1.2-3)** (Week 7-8)
**Goal:** Real-time toolpath visualization with arcs

**Tasks:**
1. [ ] Implement WebGL arc rendering
2. [ ] Create `SimulationViewer.vue` component
3. [ ] Add time scrubber slider
4. [ ] Implement speed heatmap
5. [ ] Add Web Workers for background computation (I.1.3)
6. [ ] Integrate with Module L and v16.1 outputs
7. [ ] Add route: `/cam/sim`

**Deliverable:** Real-time toolpath simulation with arc support

---

### **Phase 7: Quality of Life Features** (Week 9-10)
**Goal:** DXF preflight, bridge calculator, markdown reports

**Tasks:**
1. [ ] Implement CurveLab DXF preflight validator
2. [ ] Create `BridgeCalculator.vue` component
3. [ ] Add markdown report generation
4. [ ] Add route: `/calculators/bridge`
5. [ ] Pre-export modal for DXF validation

**Deliverable:** Validation tools and lutherie calculators

---

### **Phase 8: Testing & Documentation** (Week 11-12)
**Goal:** 80% test coverage and comprehensive docs

**Tasks:**
1. [ ] Unit tests for all new routers
2. [ ] Integration tests for end-to-end workflows
3. [ ] Smoke tests for all new endpoints
4. [ ] Update `DEVELOPER_ONBOARDING.md`
5. [ ] API documentation (Swagger/Redoc)
6. [ ] User guide for CAM section
7. [ ] User guide for Art Studio

**Deliverable:** Production-ready system with full test coverage

---

## 📋 Integration Checklist Template

For each patch integration, use this checklist:

```markdown
### Patch [NAME] Integration

**Status:** 🚧 In Progress  
**Assignee:** [Name]  
**Target Date:** [Date]

#### Backend
- [ ] Copy source files to `services/api/app/`
- [ ] Create FastAPI router (if needed)
- [ ] Register router in `main.py`
- [ ] Add error handling (HTTPException patterns)
- [ ] Validate with Pydantic models
- [ ] Test locally with `uvicorn --reload`

#### Frontend
- [ ] Copy Vue components to `packages/client/src/views/`
- [ ] Create API wrapper in `packages/client/src/api/`
- [ ] Add route to `router/index.ts`
- [ ] Update navigation (dashboard cards)
- [ ] Test locally with `npm run dev`

#### Testing
- [ ] Create smoke test script (PowerShell)
- [ ] Run smoke test locally
- [ ] Add CI workflow step
- [ ] Verify badges update

#### Documentation
- [ ] Create/update integration summary doc
- [ ] Update `A_N_BUILD_ROADMAP.md`
- [ ] Update `.github/copilot-instructions.md`
- [ ] Add to relevant quickref docs

#### Deployment
- [ ] Merge to main branch
- [ ] Verify CI passes
- [ ] Test on staging
- [ ] Deploy to production
- [ ] Monitor for errors (Sentry)
```

---

## 🎯 Priority Matrix

| Feature | Priority | Effort | Dependencies | Target Phase |
|---------|----------|--------|--------------|--------------|
| **CAM Dashboard** | P1 | Low | None | Phase 1 |
| **Art Studio Dashboard** | P1 | Low | None | Phase 1 |
| **Helical v16.1** | P1 | Low | None | Phase 2 |
| **Polygon N17** | P1 | Medium | Module L | Phase 3 |
| **Benchmark N16** | P1 | Low | Module L.3 | Phase 4 |
| **CAM Essentials N0-N10** | P1 | High | N.03, N.04c | Phase 5 |
| **Simulation I.1.2** | P2 | Medium | N15 | Phase 6 |
| **Web Workers I.1.3** | P2 | Low | I.1.2 | Phase 6 |
| **DXF Preflight** | P2 | Low | None | Phase 7 |
| **Bridge Calculator** | P2 | Low | None | Phase 7 |
| **Markdown Reports** | P2 | Low | None | Phase 7 |
| **Test Coverage 80%** | P1 | High | All | Phase 8 |
| **API Docs** | P1 | Medium | All | Phase 8 |

---

## 🚦 Success Criteria

### **Phase 1-2 Complete (Week 2)**
- ✅ Navigation structure built (CAM, Art Studio dashboards)
- ✅ Helical v16.1 integrated and tested
- ✅ Users can navigate to /cam and /art-studio
- ✅ All existing features still work (no regressions)

### **Phase 3-4 Complete (Week 4)**
- ✅ Polygon offset N17 integrated
- ✅ Benchmark suite N16 running
- ✅ Performance data validated (30-40% time savings with trochoids)

### **Phase 5 Complete (Week 6)**
- ✅ CAM essentials rollup (N0-N10) complete
- ✅ Drilling and probing UIs functional
- ✅ Unified post-processor system active

### **Phase 6-7 Complete (Week 10)**
- ✅ Simulation with arcs working
- ✅ DXF preflight preventing bad exports
- ✅ Bridge calculator available

### **Phase 8 Complete (Week 12)**
- ✅ 80% test coverage achieved
- ✅ All endpoints documented (Swagger)
- ✅ User guides written
- ✅ Production deployment verified

---

## 🌲 Re-Forestation Philosophy

**Original "Clearing":** Consolidated 18 files, 3,800+ lines into unified system (FOREST_CLEARING_COMPLETE.md)

**New "Re-Forestation":** Plant organized trees (scaffolds) then fill with high-quality branches (patches)

**Key Differences:**
1. **Structured Growth** - Scaffolds first, then features
2. **No Regressions** - Every integration passes smoke tests
3. **Documentation-Driven** - Each patch has integration summary
4. **Modular Design** - Features can be disabled independently
5. **User-Centric** - Dashboard navigation vs scattered routes

**Success Metric:** Users can discover all features from two dashboards (CAM, Art Studio) without hunting through docs.

---

## 📚 Related Documentation

- [A_N_BUILD_ROADMAP.md](./A_N_BUILD_ROADMAP.md) - Original build plan
- [FOREST_CLEARING_COMPLETE.md](./FOREST_CLEARING_COMPLETE.md) - Previous integration philosophy
- [ART_STUDIO_V16_1_HELICAL_INTEGRATION.md](./ART_STUDIO_V16_1_HELICAL_INTEGRATION.md) - v16.1 ready to integrate
- [PATCH_N_SERIES_ROLLUP.md](./PATCH_N_SERIES_ROLLUP.md) - CAM essentials documentation
- [ADAPTIVE_POCKETING_MODULE_L.md](./ADAPTIVE_POCKETING_MODULE_L.md) - Module L overview
- [CODING_POLICY.md](./CODING_POLICY.md) - Integration standards

---

## 🎬 Next Steps

1. **Review this plan** - User confirms approach and priorities
2. **Start Phase 1** - Build CAM and Art Studio dashboard scaffolds
3. **Integrate v16.1** - Add helical ramping to Art Studio (quick win)
4. **Continue rollout** - Follow phases 3-8 systematically

**Ready to begin Phase 1 scaffold construction?**

---

**Status:** 📋 Plan Complete, Awaiting User Approval  
**Last Updated:** November 13, 2025  
**Next Action:** Start Phase 1 - Build dashboard scaffolds
