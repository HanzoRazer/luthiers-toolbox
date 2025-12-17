# Option A Validation Report - Code Overlap Analysis

**Generated:** November 9, 2025  
**Analyst:** AI System  
**Purpose:** Compare Option A.txt (27,152 lines) against existing codebase to identify overlaps, unique implementations, and merge strategies

---

## Executive Summary

### Key Findings

**✅ GOOD NEWS:** Several core Option A components **already exist** in the codebase with similar functionality:
- `pipeline_router.py` (1,365 lines existing vs ~700 lines in Option A)
- `cam_sim_router.py` (30 lines existing vs ~100 lines in Option A)
- `CamBackplotViewer.vue` (295 lines existing vs ~200 lines in Option A)
- `cam_sim_bridge.py` (341 lines existing, not in Option A inventory but discovered)

**⚠️ EXTRACTION NEEDED:** Unique Option A components not in existing codebase:
- `CamPipelineRunner.vue` (full component with preset management)
- `PipelineLabView.vue` (wrapper view at /lab/pipeline)
- `AdaptiveLabView.vue` (standalone adaptive tester)
- `MachineListView.vue` and `PostListView.vue` (management UIs)
- `ArtStudioRosette.vue`, `ArtStudioHeadstock.vue`, `ArtStudioRelief.vue` (Art Studio flows)
- `CamPipelineGraph.vue` (pipeline visualization)
- `pipeline_presets_router.py` (preset save/load)
- `dxf_plan_router.py` (DXF → Adaptive Plan helper)

**Overlap Assessment:**
- **High overlap:** ~40% (pipeline core, sim integration, backplot viewer)
- **Unique Option A code:** ~60% (UI wrappers, preset system, Art Studio views)
- **Merge complexity:** **MEDIUM** (existing code is more comprehensive but Option A has better UI integration)

---

## Detailed Component Analysis

### 🔵 Backend Components

#### 1. **pipeline_router.py** - MAJOR OVERLAP ⚠️

**Existing File:** `services/api/app/routers/pipeline_router.py` (1,365 lines)

**Status:** ✅ Already implemented with MORE features than Option A

**Existing Implementation:**
- Unified CAM pipeline orchestration (5 operation types)
- Machine awareness (auto-apply feed/accel/jerk limits)
- Post-processor awareness (template-based G-code formatting)
- Error isolation (per-operation error capture)
- Context propagation (shared parameters across operations)
- Comprehensive documentation headers (Phase 7 policy compliant)

**Option A Version:** (~700 lines in "Option A.txt")
- Similar orchestration but less comprehensive
- Simpler machine/post profile integration
- Basic error handling

**Recommendation:** ✅ **KEEP EXISTING**, do NOT extract Option A version  
**Rationale:** Existing implementation is more mature, better documented, and production-ready

**Missing from Existing (extract these):**
- Inspector panel UI integration (preset preview with machine/post specs)
- Client-side preset loading/saving workflow

---

#### 2. **cam_sim_router.py** - OVERLAP + ENHANCEMENT 🔶

**Existing File:** `services/api/app/routers/cam_sim_router.py` (30 lines)

**Status:** ⚠️ Existing is STUB, Option A has full implementation

**Existing Implementation:**
```python
# Minimal stub:
@router.post("/simulate_gcode")
def simulate_gcode(body: SimInput):
    sim = simulate(body.gcode, accel=body.accel or DEFAULT_ACCEL, ...)
    return Response(...)
```

**Option A Version:** (~100 lines)
- Full simulation with issue detection
- Severity levels (error, warning, info)
- Move-by-move analysis
- Timing estimation
- Issue metadata (move_idx, severity, message)

**Recommendation:** ✅ **EXTRACT Option A version**, replace existing stub  
**Merge Strategy:**
1. Keep existing endpoint path `/cam/simulate_gcode`
2. Replace stub logic with Option A's full implementation
3. Maintain backward compatibility with existing callers
4. Add Phase 7 documentation headers

---

#### 3. **cam_sim_bridge.py** - UNIQUE EXISTING 🆕

**Existing File:** `services/api/app/services/cam_sim_bridge.py` (341 lines)

**Status:** ✅ Already implemented, NOT in Option A inventory

**Discovery:** This file exists in the codebase but was NOT listed in Option A.txt

**Key Functions:**
- `simulate_gcode_inline(gcode, stock_thickness, **extra)` - inline sim call
- `_extract_issues_from_raw(raw)` - normalize engine-specific formats
- Multi-engine support (issues[], collisions[], gouges[] formats)

**Recommendation:** ✅ **KEEP EXISTING**, do NOT extract  
**Rationale:** This is a more comprehensive implementation than Option A (which doesn't have an equivalent)

**Integration Note:** Use this with extracted cam_sim_router.py for engine-agnostic simulation

---

#### 4. **adaptive_router.py** - PARTIAL OVERLAP 🔶

**Existing File:** `services/api/app/routers/adaptive_router.py` (1,061 lines)

**Status:** ⚠️ Option A has NEW endpoint: `/plan_from_dxf`

**Existing Implementation:**
- `/plan` endpoint (full adaptive pocketing engine)
- L.1 robust offsetting with islands
- L.2 true spiralizer + min-fillet injection
- L.3 trochoidal insertion + jerk-aware time
- Comprehensive models (PlanIn, PlanOut, Loop schemas)

**Option A Addition:**
```python
@router.post("/plan_from_dxf", response_model=PlanFromDxfOut)
def plan_adaptive_from_dxf(req: PlanFromDxfIn) -> PlanFromDxfOut:
    # DXF → loops + adaptive plan in one call
    # Convenience wrapper for dev/testing
```

**Recommendation:** ✅ **EXTRACT `/plan_from_dxf` endpoint ONLY**  
**Merge Strategy:**
1. Add new endpoint to existing adaptive_router.py
2. Keep existing `/plan` endpoint unchanged
3. Use existing adaptive kernel for actual planning
4. Add Phase 7 documentation for new endpoint

---

#### 5. **pipeline_presets_router.py** - UNIQUE OPTION A ✅

**Location in Option A:** Line 2519

**Status:** ❌ NOT in existing codebase

**Functionality:**
- Save/load pipeline recipes (JSON storage)
- CRUD endpoints: GET/POST/DELETE /cam/pipeline/presets
- Preset model: `{ id, name, description, units, machine_id, post_id }`
- localStorage integration on frontend

**Recommendation:** ✅ **EXTRACT FULLY**  
**Estimated Effort:** 2-3 hours (simple CRUD with JSON file storage)

**Integration Points:**
- Uses existing machine/post profile IDs
- Wired to `CamPipelineRunner.vue` preset dropdown
- Storage: `services/api/app/data/pipeline_presets.json`

---

#### 6. **dxf_plan_router.py** - UNIQUE OPTION A ✅

**Location in Option A:** Line 2636

**Status:** ❌ NOT in existing codebase

**Functionality:**
- `/cam/plan_from_dxf` endpoint (distinct from adaptive router version)
- DXF file upload + parsing
- Returns adaptive PlanIn-compatible request
- Includes preflight validation integration

**Recommendation:** ⚠️ **REVIEW BEFORE EXTRACT**  
**Reason:** DUPLICATE functionality with `/cam/pocket/adaptive/plan_from_dxf`

**Decision Required:**
- **Option 1:** Extract and merge both endpoints into one canonical version
- **Option 2:** Skip extraction (existing adaptive router endpoint is sufficient)
- **Option 3:** Keep both but document distinction (one takes file path, one takes upload)

**Recommended:** Option 1 (merge into single canonical endpoint)

---

#### 7. **Machine/Post Router Stubs** - UNIQUE OPTION A ✅

**Location in Option A:** Lines 5008-5094 (machine_router.py, posts_router.py)

**Status:** ⚠️ PARTIALLY exists in codebase

**Existing Files:**
- `services/api/app/routers/machine_router.py` (105 lines)
- `services/api/app/routers/machines_router.py` (85 lines)
- `services/api/app/routers/posts_router.py` (97 lines)

**Option A Version:**
- Demo machine profiles (GRBL generic, Haas MiniMill)
- Demo post profiles (GRBL, LinuxCNC, Haas NGC, Fanuc 0i)
- JSON-based storage structure

**Recommendation:** ✅ **COMPARE & MERGE**  
**Merge Strategy:**
1. Read existing machine/posts router implementations
2. If existing are stubs, extract Option A demo profiles
3. If existing are full CRUD, keep existing and add demo profiles to data files
4. Estimated effort: 1-2 hours

---

### 🟢 Frontend Components

#### 8. **CamBackplotViewer.vue** - MAJOR OVERLAP ⚠️

**Existing File:** `packages/client/src/components/cam/CamBackplotViewer.vue` (295 lines)

**Status:** ✅ Already implemented with COMPARABLE features

**Existing Implementation:**
- SVG-based backplot rendering
- Boundary loops display (gray stroke)
- Toolpath segments (colored by severity)
- Overlays rendering (circles with fill-opacity)
- Legend with stroke samples
- Props: `moves`, `stats`, `overlays`, `simIssues`

**Option A Version:** (~200 lines)
- Similar SVG rendering
- Severity-aware coloring (red=error, orange=warning)
- Event emissions (segment-hover, overlay-hover)

**Comparison:**
| Feature | Existing (295 lines) | Option A (200 lines) |
|---------|---------------------|---------------------|
| SVG rendering | ✅ | ✅ |
| Severity coloring | ✅ | ✅ |
| Overlays | ✅ | ✅ |
| Sim issues | ✅ | ✅ |
| Legend | ✅ | ✅ |
| Event emissions | ⚠️ Limited | ✅ Full |
| ViewBox auto-fit | ✅ | ✅ |

**Recommendation:** 🔶 **MERGE ENHANCEMENTS**  
**Merge Strategy:**
1. Keep existing file as base
2. Extract event emission patterns from Option A (`segment-hover`, `overlay-hover`)
3. Add any missing severity levels
4. Test with existing consumers (AdaptivePocketLab, etc.)
5. Estimated effort: 1-2 hours

---

#### 9. **CamPipelineRunner.vue** - UNIQUE OPTION A ✅

**Location in Option A:** Lines 17, 5094

**Status:** ❌ NOT in existing codebase

**Functionality:**
- DXF file upload + pipeline configuration
- Machine/Post ID inputs
- Preset dropdown (load/save)
- Inspector panel (show machine/post specs)
- Event emissions:
  - `@adaptive-plan-ready` (moves, stats, overlays)
  - `@sim-result-ready` (issues, moves, summary)
- Run pipeline button with loading state

**Recommendation:** ✅ **EXTRACT FULLY**  
**Estimated Effort:** 4-6 hours (complex component with state management)

**Integration Points:**
- Wires to `/cam/pipeline/run` endpoint
- Uses preset endpoints from `pipeline_presets_router.py`
- Emits events for `PipelineLabView.vue` to consume

---

#### 10. **PipelineLabView.vue** - UNIQUE OPTION A ✅

**Location in Option A:** Line 56

**Status:** ❌ NOT in existing codebase

**Functionality:**
- Wrapper view at `/lab/pipeline`
- Mounts `CamPipelineRunner` + `CamBackplotViewer`
- Event routing:
  - `@adaptive-plan-ready` → update backplot moves
  - `@sim-result-ready` → update sim issues overlay
- Prioritizes sim moves over adaptive moves for display

**Recommendation:** ✅ **EXTRACT FULLY**  
**Estimated Effort:** 2-3 hours (mostly wiring, simple logic)

**Integration Points:**
- Route: `/lab/pipeline`
- Uses `CamPipelineRunner.vue` and `CamBackplotViewer.vue`

---

#### 11. **AdaptiveLabView.vue** - UNIQUE OPTION A ✅

**Location in Option A:** Lines 5202+ (inferred from router config)

**Status:** ❌ NOT in existing codebase

**Functionality:**
- Standalone adaptive tester
- DXF import → loops extraction
- Loops JSON editor (textarea with demo button)
- Adaptive parameter controls (tool_d, stepover, etc.)
- "Send to PipelineLab" button (router.push('/lab/pipeline'))
- Backplot preview

**Recommendation:** ✅ **EXTRACT FULLY**  
**Estimated Effort:** 3-4 hours (medium complexity)

**Integration Points:**
- Route: `/lab/adaptive`
- Uses existing `/cam/pocket/adaptive/plan` endpoint
- Wires to `CamBackplotViewer.vue`

---

#### 12. **MachineListView.vue & PostListView.vue** - UNIQUE OPTION A ✅

**Location in Option A:** Lines 434, 509

**Status:** ❌ NOT in existing codebase

**Functionality:**
- Read-only machine/post profile viewers
- Grid layout (2 columns on desktop)
- Profile cards showing:
  - **Machines:** max_feed_xy, rapid, accel, jerk, safe_z_default
  - **Posts:** dialect, mode, line_numbers
- Alpha implementation (no CRUD UI)

**Recommendation:** ✅ **EXTRACT FULLY**  
**Estimated Effort:** 2-3 hours (simple list views)

**Integration Points:**
- Routes: `/machines`, `/posts`
- Fetches from `/cam/machines` and `/cam/posts` endpoints

---

#### 13. **Art Studio Views** - UNIQUE OPTION A ✅

**Location in Option A:** Lines 5142, 5164, 5182

**Status:** ❌ NOT in existing codebase

**Files:**
- `ArtStudioRosette.vue` - Rosette pocketing workflow
- `ArtStudioHeadstock.vue` - Headstock inlay V-carve workflow
- `ArtStudioRelief.vue` - Relief rough + finish workflow

**Functionality:**
- Each view uses `CamPipelineRunner` with preset ops
- Displays backplot with severity-aware coloring
- DXF input per Art Studio domain (rosettes, headstock, relief)

**Recommendation:** 🔶 **DEFER TO PHASE 3** (Art Studio is SECONDARY)  
**Rationale:** User explicitly stated "Art Studio is the secondary concern"

**Extraction Priority:** LOW (after Phase 1 & 2 complete)

---

#### 14. **CamPipelineGraph.vue** - UNIQUE OPTION A ✅

**Location in Option A:** Line 5094 (embedded in CamPipelineRunner)

**Status:** ❌ NOT in existing codebase

**Functionality:**
- Visual pipeline operation graph
- Nodes with short labels (PRE, PLAN, RUN, POST, SIM)
- Color-coded by status (green=OK, red=FAIL, gray=pending)
- Arrows connecting sequential operations

**Recommendation:** ✅ **EXTRACT FULLY**  
**Estimated Effort:** 1-2 hours (simple visualization component)

**Integration Points:**
- Used by `CamPipelineRunner.vue` to display pipeline state
- Props: `results: PipelineOpResult[]`

---

## Merge Strategy & Phasing

### Phase 1: Core Pipeline Infrastructure (HIGH PRIORITY) ⭐

**Estimated Time:** 2-3 days

**Components to Extract:**
1. ✅ `cam_sim_router.py` enhancement (replace existing stub)
2. ✅ `/plan_from_dxf` endpoint addition to `adaptive_router.py`
3. ✅ `pipeline_presets_router.py` (NEW)
4. ✅ `CamPipelineRunner.vue` (NEW)
5. ✅ `CamPipelineGraph.vue` (NEW)
6. ✅ `PipelineLabView.vue` (NEW)
7. 🔶 `CamBackplotViewer.vue` enhancements (event emissions)

**Validation Steps:**
- [ ] Pipeline runs DXF → Preflight → Adaptive → Post → Sim
- [ ] Presets save/load works
- [ ] Inspector panel shows machine/post specs
- [ ] Backplot displays with severity coloring
- [ ] Simulation issues overlay on backplot

**Files to Create:**
```
services/api/app/routers/pipeline_presets_router.py  (NEW)
services/api/app/data/pipeline_presets.json          (NEW, initially empty [])
packages/client/src/components/cam/CamPipelineRunner.vue  (NEW)
packages/client/src/components/cam/CamPipelineGraph.vue   (NEW)
packages/client/src/views/PipelineLabView.vue        (NEW)
```

**Files to Modify:**
```
services/api/app/routers/cam_sim_router.py           (REPLACE stub)
services/api/app/routers/adaptive_router.py          (ADD /plan_from_dxf)
packages/client/src/components/cam/CamBackplotViewer.vue  (ENHANCE events)
packages/client/src/router/index.ts                  (ADD /lab/pipeline route)
services/api/app/main.py                             (REGISTER preset router)
```

---

### Phase 2: Machine/Post Management (MEDIUM PRIORITY) ⭐

**Estimated Time:** 1-2 days

**Components to Extract:**
1. ✅ `MachineListView.vue` (NEW)
2. ✅ `PostListView.vue` (NEW)
3. ✅ `AdaptiveLabView.vue` (NEW)
4. 🔶 Machine/Post router enhancements (demo profiles)

**Validation Steps:**
- [ ] `/machines` route displays profile list
- [ ] `/posts` route displays post configs
- [ ] `/lab/adaptive` allows standalone adaptive testing
- [ ] Demo profiles load correctly (GRBL, Haas, LinuxCNC, Fanuc, MASSO)

**Files to Create:**
```
packages/client/src/views/MachineListView.vue   (NEW)
packages/client/src/views/PostListView.vue      (NEW)
packages/client/src/views/AdaptiveLabView.vue   (NEW)
```

**Files to Review (may need merging):**
```
services/api/app/routers/machine_router.py      (COMPARE with Option A)
services/api/app/routers/machines_router.py     (COMPARE with Option A)
services/api/app/routers/posts_router.py        (COMPARE with Option A)
```

**Files to Modify:**
```
packages/client/src/router/index.ts  (ADD /machines, /posts, /lab/adaptive routes)
```

---

### Phase 3: Art Studio Components (LOW PRIORITY) ⏸️

**Estimated Time:** 2-3 days

**Components to Extract:**
1. ✅ `ArtStudioRosette.vue` (NEW)
2. ✅ `ArtStudioHeadstock.vue` (NEW)
3. ✅ `ArtStudioRelief.vue` (NEW)
4. 🔶 Art Studio router integration

**Validation Steps:**
- [ ] `/art/rosette` workflow runs DXF → Adaptive → Helix → Post → Sim
- [ ] `/art/headstock` workflow runs DXF → VCarve → Post → Sim
- [ ] `/art/relief` workflow runs DXF → Rough → Finish → Post → Sim
- [ ] Backplot shows Art Studio-specific overlays

**Files to Create:**
```
packages/client/src/views/art/ArtStudioRosette.vue      (NEW)
packages/client/src/views/art/ArtStudioHeadstock.vue    (NEW)
packages/client/src/views/art/ArtStudioRelief.vue       (NEW)
```

**Files to Modify:**
```
packages/client/src/router/index.ts  (ADD /art/* routes)
```

**Deferred Rationale:** User stated "Art Studio is the secondary concern. The overall CAM pipeline is the heart of the ToolBox."

---

## Conflict Resolution Strategy

### 1. **pipeline_router.py** - KEEP EXISTING ✅

**Conflict:** Existing has 1,365 lines vs Option A has ~700 lines

**Resolution:**
- ✅ Keep existing implementation (more comprehensive)
- ❌ Do NOT extract Option A version
- 🔶 Extract UI integration patterns (inspector panel concept)

**Rationale:** Existing file has:
- Better documentation (Phase 7 policy)
- More comprehensive error handling
- Machine/post awareness already integrated
- Production-tested (6 commits in history)

---

### 2. **cam_sim_router.py** - REPLACE STUB WITH OPTION A ✅

**Conflict:** Existing is 30-line stub vs Option A is ~100-line full implementation

**Resolution:**
- ✅ Extract Option A version
- ✅ Replace existing stub logic
- ✅ Keep existing endpoint path `/cam/simulate_gcode`
- ✅ Add Phase 7 documentation headers

**Rationale:** Option A has full simulation engine with:
- Issue detection
- Severity levels
- Move-by-move analysis
- Timing estimation

---

### 3. **CamBackplotViewer.vue** - MERGE ENHANCEMENTS 🔶

**Conflict:** Both have similar features, slightly different implementations

**Resolution:**
- ✅ Keep existing file as base (295 lines)
- ✅ Extract event emission patterns from Option A
- ✅ Add any missing severity levels
- ✅ Test with existing consumers

**Merge Checklist:**
- [ ] Add `@segment-hover` event emission
- [ ] Add `@overlay-hover` event emission
- [ ] Verify severity color mapping matches Option A
- [ ] Test with AdaptivePocketLab.vue integration
- [ ] Test with new PipelineLabView.vue integration

---

### 4. **adaptive_router.py** - ADD NEW ENDPOINT 🔶

**Conflict:** Existing has full kernel, Option A adds `/plan_from_dxf` endpoint

**Resolution:**
- ✅ Keep existing `/plan` endpoint unchanged
- ✅ Extract `/plan_from_dxf` endpoint from Option A
- ✅ Add to existing adaptive_router.py file
- ✅ Document as convenience wrapper

**New Endpoint Signature:**
```python
@router.post("/plan_from_dxf", response_model=PlanFromDxfOut)
def plan_adaptive_from_dxf(req: PlanFromDxfIn) -> PlanFromDxfOut:
    """Convenience: DXF → loops + adaptive plan in one call"""
    # Extract loops from DXF using existing utilities
    # Call existing /plan endpoint
    # Return loops + plan together
```

---

### 5. **dxf_plan_router.py** - SKIP OR MERGE ⚠️

**Conflict:** DUPLICATE functionality with adaptive_router.py `/plan_from_dxf`

**Resolution Options:**

**Option 1 (Recommended):** ❌ SKIP EXTRACTION
- Rationale: adaptive_router.py version is sufficient
- Avoids duplicate endpoints

**Option 2:** 🔶 MERGE INTO SINGLE CANONICAL ENDPOINT
- Review both implementations
- Take best features from each
- Create unified `/cam/dxf/plan` endpoint

**Option 3:** ⚠️ EXTRACT BOTH (NOT RECOMMENDED)
- Maintain two separate endpoints
- Document distinction clearly
- Risk: confusion for API consumers

**Decision Required:** User input needed

**Recommendation:** Option 1 (skip extraction, use adaptive_router version)

---

## Testing & Validation Checklist

### Backend API Tests

**Phase 1 Tests:**
- [ ] `POST /cam/simulate_gcode` returns issues array
- [ ] `POST /cam/pipeline/presets` creates preset
- [ ] `GET /cam/pipeline/presets` lists presets
- [ ] `DELETE /cam/pipeline/presets/{id}` removes preset
- [ ] `POST /cam/pocket/adaptive/plan_from_dxf` returns loops + plan

**Phase 2 Tests:**
- [ ] `GET /cam/machines` returns demo profiles
- [ ] `GET /cam/machines/{id}` returns specific profile
- [ ] `GET /cam/posts` returns demo presets
- [ ] `GET /cam/posts/{id}` returns specific preset

**Phase 3 Tests:**
- [ ] Art Studio endpoints wire correctly (if applicable)

---

### Frontend Integration Tests

**Phase 1 Tests:**
- [ ] `/lab/pipeline` route loads PipelineLabView
- [ ] CamPipelineRunner uploads DXF and runs pipeline
- [ ] Preset dropdown loads/saves correctly
- [ ] Inspector panel shows machine/post specs
- [ ] CamBackplotViewer displays severity-colored toolpath
- [ ] Simulation issues overlay on backplot

**Phase 2 Tests:**
- [ ] `/machines` route displays profile cards
- [ ] `/posts` route displays preset cards
- [ ] `/lab/adaptive` route allows standalone testing
- [ ] AdaptiveLabView DXF import works
- [ ] "Send to PipelineLab" button navigates correctly

**Phase 3 Tests:**
- [ ] `/art/rosette` workflow completes
- [ ] `/art/headstock` workflow completes
- [ ] `/art/relief` workflow completes

---

### End-to-End Workflow Tests

**Critical Path 1: DXF → Pipeline → Backplot**
```
1. User uploads guitar_body.dxf in PipelineLabView
2. Pipeline runs: Preflight → Adaptive → Post → Sim
3. CamBackplotViewer shows:
   - Boundary loops (gray)
   - Toolpath (blue/green/orange/red by severity)
   - Simulation issues (red circles)
4. User saves preset "Les Paul Standard"
5. User reloads page, preset appears in dropdown
6. User selects preset, inspector shows machine/post specs
```

**Critical Path 2: Adaptive Lab → Pipeline Lab**
```
1. User enters /lab/adaptive
2. User clicks "Load demo loops"
3. User adjusts tool_d, stepover
4. User clicks "Run Adaptive Kernel"
5. Backplot shows toolpath preview
6. User clicks "Send to PipelineLab"
7. Route navigates to /lab/pipeline
8. (Future enhancement: carry over loops/params)
```

---

## Risk Assessment

### High Risk Items ⚠️

**1. pipeline_router.py Overlap**
- **Risk:** Accidentally overwriting existing production implementation
- **Mitigation:** Git diff review before any changes, create backup branch
- **Impact if failed:** Complete pipeline orchestration broken

**2. CamBackplotViewer.vue Merge**
- **Risk:** Breaking existing consumers (AdaptivePocketLab, etc.)
- **Mitigation:** Incremental merge with regression testing
- **Impact if failed:** Multiple views display blank/broken backplots

**3. DXF Plan Router Duplication**
- **Risk:** Two endpoints doing same thing (API confusion)
- **Mitigation:** Choose single canonical endpoint, document clearly
- **Impact if failed:** Maintenance burden, user confusion

---

### Medium Risk Items 🔶

**4. cam_sim_router.py Replacement**
- **Risk:** Stub replacement may break existing callers
- **Mitigation:** Check for existing usages with grep_search before replacement
- **Impact if failed:** Simulation results not returned to pipeline

**5. Preset System Integration**
- **Risk:** localStorage sync issues between client/server
- **Mitigation:** Add explicit save confirmation UI, handle network errors
- **Impact if failed:** Presets don't persist across sessions

---

### Low Risk Items ✅

**6. New Vue Components**
- **Risk:** Minimal (net-new components, no existing dependencies)
- **Mitigation:** Standard component testing
- **Impact if failed:** New features don't work, but existing features unaffected

**7. Art Studio Views**
- **Risk:** Minimal (secondary priority, isolated functionality)
- **Mitigation:** Phase 3 deferred until Phase 1 & 2 complete
- **Impact if failed:** Art Studio features unavailable, core CAM unaffected

---

## Dependencies & Prerequisites

### Before Phase 1 Extraction

**Required:**
- [ ] Verify `services/api/app/services/cam_sim_bridge.py` exists (✅ confirmed)
- [ ] Verify `/cam/simulate_gcode` endpoint exists (✅ confirmed)
- [ ] Verify `/cam/pocket/adaptive/plan` endpoint exists (✅ confirmed in adaptive_router.py)
- [ ] Verify `CamBackplotViewer.vue` exists (✅ confirmed)

**Optional:**
- [ ] Review existing machine_router.py (105 lines)
- [ ] Review existing machines_router.py (85 lines)
- [ ] Review existing posts_router.py (97 lines)

---

### Phase 1 Dependencies

**Backend:**
- `pyclipper` (for adaptive offsetting) - ✅ already installed
- `ezdxf` (for DXF parsing) - ✅ already installed
- `shapely` (for geometry operations) - ✅ already installed

**Frontend:**
- Vue 3 + Vite - ✅ already setup
- Vue Router - ✅ already setup
- TypeScript - ✅ already setup

**File System:**
- `services/api/app/data/` directory exists - ⚠️ verify
- Write permissions for preset storage - ⚠️ verify

---

### Phase 2 Dependencies

**Backend:**
- Machine profile JSON templates - ⚠️ create in `app/data/machines/`
- Post config JSON templates - ⚠️ create in `app/data/posts/`

**Frontend:**
- No new dependencies

---

### Phase 3 Dependencies

**Backend:**
- Art Studio operation handlers (VCarveInfill, ReliefRoughing, etc.) - ⚠️ may not exist yet

**Frontend:**
- No new dependencies

---

## Recommended Extraction Order

### Step-by-Step Plan

**Day 1: Backend Foundation**
1. ✅ Extract `pipeline_presets_router.py` (2 hours)
2. ✅ Replace `cam_sim_router.py` stub (1 hour)
3. ✅ Add `/plan_from_dxf` to `adaptive_router.py` (1 hour)
4. ✅ Create demo machine/post JSON files (1 hour)
5. ✅ Test all new endpoints with curl (1 hour)

**Day 2: Core UI Components**
1. ✅ Extract `CamPipelineGraph.vue` (1 hour)
2. ✅ Extract `CamPipelineRunner.vue` (3 hours)
3. ✅ Enhance `CamBackplotViewer.vue` events (1 hour)
4. ✅ Extract `PipelineLabView.vue` (2 hours)

**Day 3: Integration & Testing**
1. ✅ Wire `/lab/pipeline` route (30 min)
2. ✅ Test DXF upload → pipeline → backplot workflow (2 hours)
3. ✅ Test preset save/load (1 hour)
4. ✅ Test inspector panel machine/post display (1 hour)
5. ✅ Write documentation updates (2 hours)

**Day 4: Machine/Post Management**
1. ✅ Extract `MachineListView.vue` (1 hour)
2. ✅ Extract `PostListView.vue` (1 hour)
3. ✅ Extract `AdaptiveLabView.vue` (2 hours)
4. ✅ Wire `/machines`, `/posts`, `/lab/adaptive` routes (1 hour)
5. ✅ Test all list views (1 hour)

**Day 5: Validation & Cleanup**
1. ✅ End-to-end workflow testing (2 hours)
2. ✅ Apply Phase 7 coding policy to all extracted code (3 hours)
3. ✅ Update OPTION_A_VALIDATION_REPORT.md with final status (1 hour)
4. ✅ Create pull request with comprehensive description (1 hour)

---

## Final Recommendations

### Immediate Actions (User Decision Required)

**1. Confirm Extraction Priority ⚠️**
- [ ] User confirms: Phase 1 (Core Pipeline) is highest priority ✅
- [ ] User confirms: Phase 2 (Machine/Post) is medium priority ✅
- [ ] User confirms: Phase 3 (Art Studio) is deferred (SECONDARY) ✅

**2. Resolve dxf_plan_router.py Conflict ⚠️**
- [ ] User decides: Skip extraction (use adaptive_router version)
- [ ] OR: Merge both into canonical endpoint
- [ ] OR: Extract both and document distinction

**3. Choose Starting Approach 🎯**
- [ ] **Option A:** Begin Phase 1 extraction immediately (recommended)
- [ ] **Option B:** Show one component first as proof-of-concept
- [ ] **Option C:** User wants more validation before proceeding

---

### Success Metrics

**Phase 1 Complete When:**
- ✅ `/lab/pipeline` route loads and displays UI
- ✅ DXF upload → pipeline run → backplot display works end-to-end
- ✅ Preset save/load persists across sessions
- ✅ Inspector panel shows machine/post specs correctly
- ✅ Simulation issues display as red overlays on backplot
- ✅ All Phase 1 components have Phase 7 documentation headers

**Phase 2 Complete When:**
- ✅ `/machines` and `/posts` routes display profile lists
- ✅ `/lab/adaptive` allows standalone adaptive testing
- ✅ Demo profiles load correctly (5 machines, 5 posts)
- ✅ AdaptiveLabView → PipelineLabView navigation works

**Phase 3 Complete When:**
- ✅ `/art/rosette`, `/art/headstock`, `/art/relief` routes work
- ✅ Each Art Studio workflow completes full pipeline
- ✅ Art Studio backplots display correctly

---

## Document Status

**Version:** 1.0  
**Last Updated:** November 9, 2025  
**Next Review:** After user decision on extraction approach  
**Maintainer:** AI System

**Change Log:**
- 2025-11-09: Initial validation report created
- Pending: User decision on extraction approach
- Pending: Resolution of dxf_plan_router.py conflict

---

## Appendix: File Counts by Category

### Backend (Python)
- ✅ Already Implemented: 4 files (pipeline_router, cam_sim_bridge, adaptive_router, machine/post routers)
- ⚠️ Needs Enhancement: 2 files (cam_sim_router stub, adaptive_router missing /plan_from_dxf)
- ✅ Extract New: 2 files (pipeline_presets_router, dxf_plan_router if needed)

### Frontend (Vue)
- ✅ Already Implemented: 1 file (CamBackplotViewer.vue)
- ⚠️ Needs Enhancement: 1 file (CamBackplotViewer.vue events)
- ✅ Extract New: 7 files (CamPipelineRunner, PipelineLabView, AdaptiveLabView, MachineListView, PostListView, CamPipelineGraph, Art Studio views)

### Configuration/Data
- ✅ Extract New: 3+ JSON files (pipeline_presets.json, demo machine profiles, demo post configs)

**Total Extraction Estimate:**
- **Phase 1:** 6 files + 2 enhancements = ~20-25 hours work
- **Phase 2:** 3 files + 1 enhancement = ~8-10 hours work  
- **Phase 3:** 3 files = ~8-10 hours work

**Grand Total:** ~36-45 hours across 3 phases

---

**END OF VALIDATION REPORT**
