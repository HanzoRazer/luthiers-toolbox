# Architectural Consolidation Audit — Developer Handoff

**Date:** 2026-05-06  
**Scope:** Repository-wide structural simplification and footprint reduction  
**Purpose:** Transform disconnected feature islands into canonical manufacturing workflows  
**Methodology:** Trace actual code paths, overlapping responsibilities, duplicated abstractions

---

## Executive Summary

The luthiers-toolbox repository has grown organically from a focused CAD/CAM platform into a sprawling multi-domain system with significant architectural drift:

| Metric | Current State | Problem |
|--------|---------------|---------|
| Frontend routes | 73 | Excessive route proliferation |
| Backend routers | 250+ | Micro-fragmentation |
| Lab views | 15+ | Labs evolved to production without consolidation |
| Toolpath viewers | 6 | Same capability, different wrappers |
| DXF-to-G-code workflows | 5 | Parallel implementations |
| Art studio routes | 16 | Should be tabs, not routes |

**Core finding:** The repository exhibits the "feature island" anti-pattern — vertical slices were built to demonstrate capability without consolidating into shared platform infrastructure.

**Target state:** Reduce to ~20 routes, ~80 routers, unified ToolpathPlayer, two canonical CAM entry points (QuickCut + CamWorkspace).

---

## Part 1: Domain Map

| Domain | Canonical Flow | Duplicate/Overlapping Systems | Consolidation? |
|--------|----------------|-------------------------------|----------------|
| **DXF to G-code** | QuickCutView | DxfToGcodeView, PipelineLabView, BridgeLabView, AdaptiveLabView, CamWorkspaceView | **P0** |
| **Toolpath Visualization** | ToolpathPlayer | CamBackplotViewer, ToolpathCanvas, ToolpathCanvas3D, ToolpathSimulatorView, GcodeViewer, BackplotGcode | **P0** |
| **Rosette/Art** | RosettePipelineView | ArtStudio, ArtStudioV16, RosetteDesignerView, 16 art-studio sub-routes | **P1** |
| **Instrument Design** | InstrumentGeometryView | GuitarDesignHubView, GuitarDimensionsView, InstrumentDesignView, DesignHub | **P1** |
| **CAM Operations** | CamWorkspaceView | PocketClearingView, ContourCuttingView, SurfacingView, DrillingView, FretSlottingView | **P1** |
| **RMOS** | RmosRunsView | RMOSLiveMonitorView, RmosAnalyticsView, RMOSCncHistoryView | Moderate |
| **Saw Lab** | SawLabView | SawLabDashboard, saw/slice, saw/batch, saw/contour | Partial |
| **Calculator Hub** | CalculatorHubView | 85+ calculator components in toolbox/ | Cleanup only |

---

## Part 2: CAM/CAD Workflow Consolidation

### Current State: 5 Parallel DXF-to-G-code Workflows

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CURRENT: 5 PARALLEL PATHS                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │ QuickCutView│  │DxfToGcode   │  │PipelineLab  │                 │
│  │ (3-step)    │  │View (GRBL)  │  │View (full)  │                 │
│  │ PRODUCTION  │  │ PRODUCTION  │  │ PRODUCTION  │                 │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                 │
│         │                │                │                         │
│         ▼                ▼                ▼                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │ BridgeLab   │  │ AdaptiveLab │  │CamWorkspace │                 │
│  │ View        │  │ View        │  │ View (neck) │                 │
│  │ PRODUCTION  │  │ LAB         │  │ PRODUCTION  │                 │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
│                                                                      │
│  User confusion: "Which one do I use?"                              │
│  Developer burden: 5 implementations to maintain                    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Target State: 2 Canonical Entry Points

```
┌─────────────────────────────────────────────────────────────────────┐
│                    TARGET: 2 CANONICAL PATHS                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                      QuickCut (Free Tier)                    │   │
│  │  3-step: Upload DXF → Configure → Download G-code           │   │
│  │  Simple, fast, onboarding-focused                           │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    CamWorkspace (Pro Tier)                   │   │
│  │  ┌─────────┬─────────┬─────────┬─────────┬─────────┐       │   │
│  │  │  Neck   │ Adaptive│  Bridge │  Pocket │ Fret    │       │   │
│  │  │  Tab    │  Tab    │   Tab   │   Tab   │ Tab     │       │   │
│  │  └─────────┴─────────┴─────────┴─────────┴─────────┘       │   │
│  │  Full multi-operation workspace with ToolpathPlayer         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  Labs become embedded panels, not separate routes                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Workflow Status Table

| View | Purpose | Status | Action |
|------|---------|--------|--------|
| **QuickCutView** | 3-step simplified onboarding | Production | **CANONICAL FREE** |
| **CamWorkspaceView** | Multi-operation workspace | Production | **CANONICAL PRO** |
| DxfToGcodeView | Shop-floor GRBL path | Production | Merge → QuickCut |
| PipelineLabView | Full pipeline orchestration | Production | Merge → CamWorkspace |
| BridgeLabView | Bridge-specific CAM | Production | Embed as CamWorkspace tab |
| AdaptiveLabView | Adaptive pocketing | Lab | Embed as CamWorkspace tab |
| HelicalRampLab | Helical ramping | Lab | Embed as CamWorkspace panel |
| PolygonOffsetLab | Offset operations | Lab | Embed as CamWorkspace panel |

---

## Part 3: Toolpath Visualization Consolidation

### Current State: 6 Redundant Viewers

| Component | Location | Purpose | Status |
|-----------|----------|---------|--------|
| ToolpathPlayer | `components/cam/ToolpathPlayer.vue` | Full-featured player | **CANONICAL** |
| ToolpathCanvas | `components/cam/ToolpathCanvas.vue` | 2D canvas renderer | Keep as ToolpathPlayer internal |
| ToolpathCanvas3D | `components/cam/ToolpathCanvas3D.vue` | Three.js renderer | Keep as ToolpathPlayer internal |
| CamBackplotViewer | `components/cam/CamBackplotViewer.vue` | Simple backplot | **DELETE** → use ToolpathPlayer |
| ToolpathSimulatorView | `views/cam/ToolpathSimulatorView.vue` | Standalone simulator | **DELETE** → use ToolpathPlayer |
| GcodeViewer | `components/toolbox/GcodeViewer.vue` | Text + preview | **DELETE** → use ToolpathPlayer |
| BackplotGcode | `components/toolbox/BackplotGcode.vue` | Basic backplot | **DELETE** → use ToolpathPlayer |

### Target: Single ToolpathPlayer with Mode Switching

```vue
<ToolpathPlayer
  :gcode-text="gcode"
  :mode="'3d'"           <!-- '2d' | '3d' | 'simulation' -->
  :show-controls="true"
  :show-hud="true"
  @ready="onPlayerReady"
/>
```

**ToolpathPlayer absorbs all visualization needs:**
- 2D backplot mode
- 3D Three.js mode
- Simulation playback mode
- HUD overlay
- Export controls

---

## Part 4: Router/Backend Consolidation

### Current Router Sprawl

| Category | Current Count | Target Count | Reduction |
|----------|---------------|--------------|-----------|
| CAM core | 31 routers | 3 | 90% |
| Art Studio | 16 routers | 1 | 94% |
| RMOS | 25+ routers | 5 | 80% |
| Instrument Geometry | 12 routers | 2 | 83% |
| Saw Lab | 14 routers | 2 | 86% |
| **Total** | **250+** | **~80** | **68%** |

### P0 Router Consolidation Targets

| Current Routers | Merge Into | Rationale |
|-----------------|------------|-----------|
| `dxf_adaptive_consolidated_router.py` | `cam_consolidated_router.py` | DXF+CAM belong together |
| `adaptive_preview_router.py` | `cam_consolidated_router.py` | Preview is CAM operation |
| `gcode_consolidated_router.py` | `cam_operations_router.py` | G-code ops are CAM |
| `cam_pipeline_preset_run_router.py` | `cam_consolidated_router.py` | Pipeline is CAM |
| `probe/*.py` (5 files) | `cam_operations_router.py` | Probe is CAM operation |
| `retract/*.py` (3 files) | `cam_operations_router.py` | Retract is CAM operation |
| `art_studio/api/*.py` (16 files) | `art_studio_consolidated_router.py` | Single art domain router |

### Dead Routers to Delete

| Router | Reason |
|--------|--------|
| `routers/_archived/pipeline_schemas.py` | Already archived |
| `routers/_archived/pipeline_context.py` | Already archived |
| `routers/_archived/pipeline_helpers.py` | Already archived |
| `routers/_archived/pipeline_validators.py` | Already archived |
| `routers/_archived/pipeline_operations.py` | Already archived |
| `cam/routers/simulation/simulation_consolidated_router.py` | Dead duplicate |

### Target Backend Structure

```
services/api/app/routers/
├── cam/
│   ├── cam_consolidated_router.py      # Core CAM ops
│   ├── cam_operations_router.py        # Pocket, drill, profile, etc.
│   └── cam_simulation_router.py        # Simulation endpoints
├── art_studio/
│   └── art_studio_consolidated_router.py  # All art ops
├── instrument/
│   ├── instrument_geometry_router.py   # Geometry calculations
│   └── instrument_design_router.py     # Design workflows
├── rmos/
│   ├── rmos_runs_router.py             # Run management
│   ├── rmos_safety_router.py           # Safety gates
│   └── rmos_artifacts_router.py        # Artifact storage
└── system/
    ├── machines_router.py              # Machine configs
    ├── materials_router.py             # Material database
    └── health_router.py                # Health checks
```

---

## Part 5: Frontend Route Consolidation

### Current: 73 Routes

**Route categories:**
- 16 art-studio sub-routes → should be tabs
- 5 CAM operation routes → should be tabs
- 5 lab routes → should be panels
- 12 RMOS sub-routes → should be tabs
- Remaining are legitimate top-level

### Target: ~20 Top-Level Routes

```typescript
const routes = [
  // Core workflows
  { path: '/', component: Dashboard },
  { path: '/quick-cut', component: QuickCutView },
  { path: '/cam', component: CamWorkspaceView },        // tabs: neck, adaptive, bridge, pocket, etc.
  { path: '/art-studio', component: ArtStudioView },    // tabs: rosette, inlay, binding, relief, etc.
  { path: '/design', component: InstrumentDesignView }, // tabs: body, neck, hardware, etc.
  
  // Manufacturing
  { path: '/rmos', component: RmosView },               // tabs: runs, analytics, monitor
  { path: '/rmos/runs/:id', component: RmosRunDetail },
  
  // Tools
  { path: '/calculators', component: CalculatorHubView },
  { path: '/smart-guitar', component: SmartGuitarView },
  { path: '/blueprint', component: BlueprintLabView },
  
  // Settings
  { path: '/settings', component: SettingsView },
  { path: '/machines', component: MachinesView },
  
  // Dev/Admin
  { path: '/admin', component: AdminView },
];
```

### Routes That Become Tabs

| Current Route | Becomes | Parent View |
|---------------|---------|-------------|
| `/cam/pocket` | Tab | CamWorkspace |
| `/cam/contour` | Tab | CamWorkspace |
| `/cam/surfacing` | Tab | CamWorkspace |
| `/cam/drilling` | Tab | CamWorkspace |
| `/cam/fret-slots` | Tab | CamWorkspace |
| `/lab/bridge` | Tab | CamWorkspace |
| `/lab/adaptive` | Tab | CamWorkspace |
| `/lab/helical` | Panel | CamWorkspace |
| `/art-studio/relief` | Tab | ArtStudio |
| `/art-studio/vcarve` | Tab | ArtStudio |
| `/art-studio/inlay` | Tab | ArtStudio |
| `/art-studio/binding` | Tab | ArtStudio |
| `/art-studio/purfling` | Tab | ArtStudio |
| `/art-studio/headstock` | Tab | ArtStudio |
| `/art-studio/rosette` | Tab | ArtStudio |
| `/rmos/analytics` | Tab | RMOS |
| `/rmos/live-monitor` | Tab | RMOS |

---

## Part 6: Shared Infrastructure Extraction

### Current Platform Gaps

| Capability | Current State | Instances | Problem |
|------------|---------------|-----------|---------|
| Toolpath visualization | Fragmented | 6 viewers | 5 redundant implementations |
| DXF import | Fragmented | 12+ importers | No shared composable |
| G-code export | Scattered | 77 files | Each feature reimplements |
| Manufacturing pipeline | None | N/A | No unified abstraction |
| Machine profiles | Partial | 3 stores | Not centralized |

### Recommended Platform Services

#### 1. useManufacturingPipeline

```typescript
// composables/useManufacturingPipeline.ts
export function useManufacturingPipeline() {
  return {
    // Unified flow: DXF → Preflight → CAM → Simulation → Export
    uploadDxf,
    runPreflight,
    selectOperation,
    generateToolpath,
    checkSafetyGate,
    runSimulation,
    exportGcode,
    createRmosRun,
  };
}
```

**Consumers:** QuickCut, CamWorkspace, BridgeLab, all CAM flows

#### 2. useToolpathVisualization

```typescript
// composables/useToolpathVisualization.ts
export function useToolpathVisualization() {
  return {
    // Unified visualization with mode switching
    setGcode,
    setMode,        // '2d' | '3d' | 'simulation'
    play,
    pause,
    seek,
    exportFrame,
  };
}
```

**Consumers:** All views that show toolpaths

#### 3. useGeometryIO

```typescript
// composables/useGeometryIO.ts
export function useGeometryIO() {
  return {
    // Unified geometry import/export
    importDxf,
    importSvg,
    exportDxf,
    exportGcode,
    transformCoordinates,
    extractLayers,
  };
}
```

**Consumers:** All views that handle geometry files

---

## Part 7: Delete/Archive Candidates

### Immediate Delete

| Path | Reason | Action |
|------|--------|--------|
| `routers/_archived/*.py` (5 files) | Already archived | Delete |
| `cam/routers/simulation/simulation_consolidated_router.py` | Dead duplicate | Delete |
| `archive/experimental/2026-03/**/*.py` | Historical snapshots | Delete |
| `archive/code/2026/*.py` | Superseded code | Delete |

### Archive (move to docs/archive/2026/)

| Component | Reason |
|-----------|--------|
| `ArtStudioV16.vue` | Version artifact, superseded |
| `ArtStudioPhase15_5.vue` | Phase artifact, superseded |
| `PipelineLab.vue` | Duplicate of PipelineLabView |
| `RiskDashboardCrossLab.vue` | Superseded by V2 |

### Merge Into Canonical

| Component | Merge Into | Rationale |
|-----------|------------|-----------|
| `DxfToGcodeView.vue` | `QuickCutView.vue` | Duplicate production path |
| `ToolpathSimulatorView.vue` | `ToolpathPlayer.vue` | Redundant viewer |
| `CamBackplotViewer.vue` | `ToolpathPlayer.vue` | Redundant viewer |
| `BackplotGcode.vue` | `ToolpathPlayer.vue` | Redundant viewer |
| `GcodeViewer.vue` | `ToolpathPlayer.vue` | Redundant viewer |
| `PocketClearingView.vue` | `CamWorkspaceView.vue` (tab) | Route → tab |
| `ContourCuttingView.vue` | `CamWorkspaceView.vue` (tab) | Route → tab |
| `SurfacingView.vue` | `CamWorkspaceView.vue` (tab) | Route → tab |
| `DrillingView.vue` | `CamWorkspaceView.vue` (tab) | Route → tab |
| `FretSlottingView.vue` | `CamWorkspaceView.vue` (tab) | Route → tab |

---

## Part 8: Anti-Patterns Identified

### 1. Vertical Slice Proliferation

**Pattern:** Each new feature gets its own route, router, store, and component tree.

**Evidence:** 73 routes, 250+ routers, 31 stores for a single-product application.

**Fix:** Features should extend existing surfaces (tabs, panels) not create new routes.

### 2. Lab Pattern Abuse

**Pattern:** "Labs" created for experimentation evolved to production without consolidation.

**Evidence:** 15+ lab views, many with production-quality code, existing as separate routes.

**Fix:** Labs should either:
- Remain dev-only (not in production router)
- Graduate to tabs in parent workspaces

### 3. Phase Artifact Accumulation

**Pattern:** Version-named files (V16, Phase15_5) remain in codebase after supersession.

**Evidence:** `ArtStudioV16.vue`, `ArtStudioPhase15_5.vue`, multiple "phase" directories.

**Fix:** Archive or delete superseded versions immediately after promotion.

### 4. Router Micro-Fragmentation

**Pattern:** One router per endpoint group instead of domain-level consolidation.

**Evidence:** Average 6 endpoints per router. 16 art_studio routers for one domain.

**Fix:** Domain-level routers (cam, art, instrument, rmos) with sub-prefixes.

### 5. Component Over-Specialization

**Pattern:** Same capability wrapped differently for each context.

**Evidence:** 6 toolpath viewers (ToolpathPlayer, CamBackplot, ToolpathCanvas, GcodeViewer, BackplotGcode, ToolpathSimulator).

**Fix:** Single component with mode/config props.

### 6. Store Proliferation

**Pattern:** One store per feature instead of domain stores.

**Evidence:** 31 stores when ~12 domain stores would suffice.

**Fix:** Domain stores (camStore, artStore, instrumentStore, rmosStore, uiStore).

### 7. Composable Duplication

**Pattern:** Same patterns reimplemented per-feature.

**Evidence:** G-code export logic in 77 files. DXF import in 12+ locations.

**Fix:** Platform composables (useManufacturingPipeline, useGeometryIO).

---

## Part 9: Estimated Footprint Reduction

| Metric | Current | After Consolidation | Reduction |
|--------|---------|---------------------|-----------|
| Frontend routes | 73 | ~20 | **73%** |
| Vue components | ~300 | ~180 | **40%** |
| Backend routers | 250+ | ~80 | **68%** |
| Pinia stores | 31 | 12 | **61%** |
| Composables | 45 | 25 | **44%** |
| Estimated LOC | 150K | 90K | **40%** |

### Cognitive Load Reduction

| Before | After |
|--------|-------|
| "Which CAM view do I use?" (5 options) | QuickCut or CamWorkspace |
| "Which toolpath viewer?" (6 options) | ToolpathPlayer |
| "Where does bridge CAM live?" (own route) | CamWorkspace → Bridge tab |
| "How do I export G-code?" (77 implementations) | useManufacturingPipeline.exportGcode() |

---

## Part 10: Migration Sequence

### Phase 1: Cleanup (Week 1-2)

| Task | Effort | Risk |
|------|--------|------|
| Delete `routers/_archived/*.py` | 1h | None |
| Delete dead simulation router duplicate | 1h | None |
| Archive version artifacts (V16, Phase15_5) | 2h | None |
| Delete `archive/experimental/` contents | 1h | None |

### Phase 2: Viewer Consolidation (Week 3-4)

| Task | Effort | Risk |
|------|--------|------|
| Audit all ToolpathPlayer usages | 4h | None |
| Remove CamBackplotViewer usages → ToolpathPlayer | 8h | Medium |
| Remove GcodeViewer usages → ToolpathPlayer | 4h | Low |
| Remove BackplotGcode usages → ToolpathPlayer | 4h | Low |
| Delete redundant viewer components | 2h | None |

### Phase 3: CAM Route Consolidation (Week 5-8)

| Task | Effort | Risk |
|------|--------|------|
| Add tab infrastructure to CamWorkspaceView | 8h | Low |
| Migrate PocketClearingView → tab | 4h | Medium |
| Migrate ContourCuttingView → tab | 4h | Medium |
| Migrate SurfacingView → tab | 4h | Medium |
| Migrate DrillingView → tab | 4h | Medium |
| Migrate FretSlottingView → tab | 4h | Medium |
| Migrate BridgeLabView → tab | 8h | Medium |
| Migrate AdaptiveLabView → tab | 8h | Medium |
| Remove old routes, add redirects | 4h | Low |

### Phase 4: Art Studio Consolidation (Week 9-10)

| Task | Effort | Risk |
|------|--------|------|
| Add tab infrastructure to ArtStudioView | 8h | Low |
| Migrate 10 art-studio sub-views → tabs | 20h | Medium |
| Remove old routes, add redirects | 4h | Low |

### Phase 5: Backend Router Consolidation (Week 11-14)

| Task | Effort | Risk |
|------|--------|------|
| Create `cam_consolidated_router.py` | 8h | Medium |
| Migrate 31 CAM routers → consolidated | 24h | High |
| Create `art_studio_consolidated_router.py` | 4h | Medium |
| Migrate 16 art routers → consolidated | 16h | High |
| Update frontend API calls | 8h | Medium |
| Add deprecation warnings to old endpoints | 4h | Low |

### Phase 6: Platform Services (Week 15-18)

| Task | Effort | Risk |
|------|--------|------|
| Create `useManufacturingPipeline` composable | 16h | Medium |
| Create `useGeometryIO` composable | 8h | Low |
| Migrate QuickCut to use pipeline | 8h | Medium |
| Migrate CamWorkspace to use pipeline | 16h | Medium |
| Standardize G-code export across 77 files | 24h | Medium |

---

## Part 11: Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking existing bookmarks/links | High | Medium | Redirect old routes for 6 months |
| User confusion during transition | Medium | Medium | In-app migration notice |
| API consumers break on router consolidation | High | High | Versioned API, deprecation headers |
| Store consolidation breaks state | Medium | High | Gradual migration, compatibility layer |
| Lost functionality during merge | Low | High | Feature flag each migration |
| Test coverage gaps exposed | Medium | Medium | Audit test coverage before merge |

### Mitigation Strategy

1. **Route redirects:** Keep old routes as redirects for 6 months
2. **API versioning:** New consolidated endpoints under `/api/v2/`, deprecate `/api/v1/`
3. **Feature flags:** Each major migration behind flag, rollback capability
4. **Parallel running:** Old and new coexist during transition
5. **User communication:** Banner explaining consolidation, linking to new locations

---

## Part 12: Canonical Workflows That Survive

After consolidation, these are the production workflows:

| Workflow | Entry Point | Description |
|----------|-------------|-------------|
| **QuickCut** | `/quick-cut` | Free tier: 3-step DXF → G-code |
| **CamWorkspace** | `/cam` | Pro tier: Multi-tab CAM workspace |
| **ArtStudio** | `/art-studio` | Decorative manufacturing |
| **InstrumentDesign** | `/design` | Parametric instrument design |
| **RMOS** | `/rmos` | Manufacturing run tracking |
| **CalculatorHub** | `/calculators` | Standalone calculations |
| **SmartGuitar** | `/smart-guitar` | IoT instrument module |
| **BlueprintLab** | `/blueprint` | PDF/image vectorization (dev) |

Everything else becomes a tab, panel, or deleted.

---

## Appendix A: File Inventory for Deletion

```bash
# Dead routers
rm services/api/app/routers/_archived/pipeline_schemas.py
rm services/api/app/routers/_archived/pipeline_context.py
rm services/api/app/routers/_archived/pipeline_helpers.py
rm services/api/app/routers/_archived/pipeline_validators.py
rm services/api/app/routers/_archived/pipeline_operations.py
rm services/api/app/cam/routers/simulation/simulation_consolidated_router.py

# Version artifacts (archive first)
mv packages/client/src/views/art-studio/ArtStudioV16.vue docs/archive/2026/
mv packages/client/src/views/art-studio/ArtStudioPhase15_5.vue docs/archive/2026/

# Redundant viewers (after migration)
rm packages/client/src/components/cam/CamBackplotViewer.vue
rm packages/client/src/components/toolbox/GcodeViewer.vue
rm packages/client/src/components/toolbox/BackplotGcode.vue
rm packages/client/src/views/cam/ToolpathSimulatorView.vue
```

## Appendix B: Verification Commands

```bash
# Count current routes
grep -c "path:" packages/client/src/router/index.ts

# Count current routers
find services/api/app -name "*router*.py" | wc -l

# Find all lab views
find packages/client/src/views -iname "*lab*"

# Find all toolpath-related components
grep -rl "ToolpathPlayer\|Backplot\|GcodeViewer" packages/client/src

# Find G-code export implementations
grep -rl "downloadGcode\|exportGcode\|download.*gcode" packages/client/src | wc -l

# Count stores
find packages/client/src/stores -name "*.ts" | wc -l
```

---

## Appendix C: Target Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              TARGET ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  FRONTEND ROUTES (~20)                                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ /              Dashboard                                              │   │
│  │ /quick-cut     QuickCut (Free tier - 3 steps)                        │   │
│  │ /cam           CamWorkspace (Pro tier - tabs: neck, adaptive, etc.)  │   │
│  │ /art-studio    ArtStudio (tabs: rosette, inlay, binding, etc.)       │   │
│  │ /design        InstrumentDesign (tabs: body, neck, hardware)         │   │
│  │ /rmos          RMOS (tabs: runs, analytics, monitor)                 │   │
│  │ /calculators   CalculatorHub                                         │   │
│  │ /smart-guitar  SmartGuitar                                           │   │
│  │ /settings      Settings                                              │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  SHARED COMPONENTS                                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ ToolpathPlayer (unified viewer - 2D/3D/simulation modes)             │   │
│  │ DxfUploadZone (unified uploader)                                     │   │
│  │ RiskBadge (unified risk display)                                     │   │
│  │ GcodeDownloader (unified export)                                     │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  PLATFORM COMPOSABLES                                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ useManufacturingPipeline (DXF→Preflight→CAM→Sim→Export→RMOS)        │   │
│  │ useToolpathVisualization (unified player control)                    │   │
│  │ useGeometryIO (DXF/SVG/G-code import/export)                        │   │
│  │ useMachineConfig (machine profiles)                                  │   │
│  │ useRmosSafety (safety gates)                                        │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  BACKEND ROUTERS (~80)                                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ /api/v2/cam/*           CAM consolidated (3 routers)                 │   │
│  │ /api/v2/art/*           Art Studio consolidated (1 router)           │   │
│  │ /api/v2/instrument/*    Instrument geometry (2 routers)              │   │
│  │ /api/v2/rmos/*          RMOS consolidated (5 routers)                │   │
│  │ /api/v2/system/*        System services (3 routers)                  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

*Audit completed: 2026-05-06*  
*Estimated consolidation timeline: 18 weeks*  
*Estimated footprint reduction: 40-70% depending on metric*
