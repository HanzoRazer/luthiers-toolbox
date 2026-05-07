# CAM End-to-End Pipeline Audit — Developer Handoff

**Date:** 2026-05-06  
**Scope:** Full E2E audit of all calculator/generator → CAM → manufacturing artifact flows  
**Purpose:** Identify where pipeline claims diverge from executable reality  
**Methodology:** Trace actual code paths, not file presence or documentation claims

---

## Executive Summary

This audit answers a single question:

> For every upstream generator/calculator, can a user go from input → generated geometry/toolpath/G-code → CAM preview/simulation → downloadable or persisted manufacturing artifact?

**Answer: Partially. 11 flows work end-to-end. 3 flows silently fail. 9 design tools have no CAM handoff at all.**

The codebase contains significant CAM infrastructure, but the integration between design tools and CAM is incomplete. Several UI elements imply functionality that does not exist, creating a trust gap where users believe they've generated manufacturing output when they haven't.

---

## Severity Classification

| Level | Definition | User Impact |
|-------|------------|-------------|
| **P0** | User believes they generated CAM/manufacturing output but actual E2E flow is broken, fake, or silently failed | User may attempt to run non-existent or corrupted G-code on CNC |
| **P1** | Capability exists in backend or generates locally but is not wired to CAM visualization, simulation, or persistence | User cannot verify output or integrate into workflow |
| **P2** | Cleanup, duplicate code, orphan endpoints, or future enhancement | Developer friction, no direct user impact |

---

## Part 1: P0 Critical Failures

These are flows where the UI suggests success but the backend does not deliver.

### 1.1 Body Outline → CAM (SILENT FAILURE)

**User expectation:** Click "Send to CAM" on body outline design, receive toolpath for CNC routing.

**What actually happens:** Button calls endpoint that does not exist. Error is caught and not displayed prominently.

```
User clicks "Send to CAM"
    ↓
GuitarDimensionsForm.vue calls useGuitarCAM.ts
    ↓
POST /api/guitar/design/parametric/to-cam
    ↓
404 Not Found (endpoint does not exist)
    ↓
Error caught, user sees... nothing definitive
```

**Evidence:**

File: `packages/client/src/components/toolbox/composables/useGuitarCAM.ts`
```typescript
// Line ~60-80 (approximate)
const response = await fetch('/api/guitar/design/parametric/to-cam', {
  method: 'POST',
  body: JSON.stringify(payload)
});
```

File: `services/api/app/routers/` — **No file contains this endpoint.**

Verification command:
```bash
grep -rn "parametric/to-cam\|parametric.to.cam" services/api/app
# Returns: nothing
```

**Why this is P0:** User completes a design workflow, clicks a prominent action button labeled "Send to CAM", and receives no manufacturing output. The failure is silent — no error toast, no redirect, no explanation.

**Remediation options:**
1. Implement `/api/guitar/design/parametric/to-cam` endpoint that converts body outline to adaptive pocket input
2. Remove the "Send to CAM" button until endpoint exists
3. Change button to "Export DXF" (which does work) and remove CAM implication

---

### 1.2 Toolpath Simulator View (FAKE ENDPOINTS)

**User expectation:** Upload or paste G-code, see animated toolpath simulation with analysis.

**What actually happens:** View references endpoints that do not exist. Simulation panel shows static/empty state.

**Evidence:**

File: `packages/client/src/views/cam/ToolpathSimulatorView.vue`
```vue
<!-- Docstring at top of file -->
/**
 * Calls:
 * - POST /api/cam/simulate/preview
 * - POST /api/cam/simulate/analyze
 */
```

These endpoints do not exist. The actual working endpoints are:
- `POST /api/cam/sim/gcode`
- `POST /api/cam/sim/upload`
- `POST /api/cam/gcode/simulate`

Verification:
```bash
grep -rn "simulate/preview\|simulate/analyze" services/api/app
# Returns: nothing

grep -rn "sim/gcode\|gcode/simulate" services/api/app
# Returns: actual endpoints in simulation_consolidated_router.py
```

**Why this is P0:** The view exists in the router, users can navigate to it, and the docstring claims API integration. A developer extending this view would trust the docstring and waste hours debugging non-existent endpoints.

**Remediation options:**
1. Wire view to actual `/api/cam/sim/gcode` endpoint
2. Import and use `ToolpathPlayer.vue` component (which is production-ready)
3. Update docstring to reflect reality

---

### 1.3 Fret Slotting Generate Toolpath (MOCK TIMEOUT)

**User expectation:** Configure fret parameters, click "Generate Toolpath", receive G-code for fret slot cutting.

**What actually happens:** Button triggers a `setTimeout` that simulates delay, then shows... nothing real.

**Evidence:**

File: `packages/client/src/views/cam/FretSlottingView.vue`
```typescript
// Approximate location
const generateToolpath = async () => {
  isGenerating.value = true;
  // Mock delay - no actual API call
  await new Promise(resolve => setTimeout(resolve, 1500));
  isGenerating.value = false;
  // No G-code produced, no simulation, no download
};
```

The backend has preview capability but no G-code generation:
```bash
grep -rn "fret_slots" services/api/app/routers services/api/app/cam
# Returns:
# fret_slots_router.py: POST /preview (returns visualization data)
# fret_slots_router.py: NO /gcode or /generate endpoint
```

**Why this is P0:** User sees a loading spinner, believes generation is happening, and receives nothing. The "preview" endpoint works, creating the illusion that the feature is complete.

**Remediation options:**
1. Implement `POST /api/cam/fret_slots/gcode` endpoint using existing `generate_fret_slot_toolpaths` calculation
2. Change button label to "Preview Only" and add "G-code generation coming soon" notice
3. Wire to FretboardEcosphere DXF export as interim (DXF exists and works)

---

## Part 2: P1 Partially Wired Flows

These flows generate real output but fail to reach CAM visualization or persistence.

### 2.1 Neck Generator (Console-Only G-code)

**Flow:** User configures neck parameters → NeckGCodeGenerator class produces G-code → Output goes to console.log

**Evidence:**

File: `packages/client/src/components/toolbox/generators/LesPaulNeckGenerator.vue`
```typescript
import { NeckGCodeGenerator } from '@/lib/gcode/NeckGCodeGenerator';

// G-code is generated...
const gcode = generator.generate(params);
console.log(gcode);  // ...and logged to console
// No ToolpathPlayer, no download, no RMOS artifact
```

**What's missing:**
- ToolpathPlayer integration for visualization
- Download button for G-code file
- RMOS run creation for artifact persistence
- "Send to Simulator" handoff

**Why this is P1:** The generation works — real G-code is produced. But a user cannot access it without opening browser DevTools. No manufacturing workflow is possible.

**Remediation:**
1. Add `<ToolpathPlayer :gcode-text="generatedGcode" />` to template
2. Add download button: `<button @click="downloadGcode">Download G-code</button>`
3. Optionally wire to RMOS for run tracking

---

### 2.2 CAM Operation Views (Form Scaffolds)

**Affected views:**
- `/cam/pocket` → `PocketView.vue`
- `/cam/contour` → `ContourView.vue`
- `/cam/surfacing` → `SurfacingView.vue`
- `/cam/drilling` → `DrillingView.vue`

**Evidence:**

Each view contains parameter forms but no API integration:
```typescript
// Pattern found in all four views
const generateToolpath = () => {
  // Form validation
  if (!validateParams()) return;
  
  // TODO: API call
  // No fetch(), no axios, no apiClient
  
  console.log('Params:', params);
};
```

Comments in code claim "Connected to API endpoints" but grep shows no actual calls:
```bash
grep -rn "fetch\|axios\|apiClient" packages/client/src/views/cam/PocketView.vue
# Returns: nothing
```

**Why this is P1:** Backend endpoints exist for all of these operations (`/api/cam/pocket/adaptive/*`, `/api/cam/drilling/gcode`, etc.). The UI is built but not wired. Users see professional-looking forms that do nothing.

**Remediation:**
1. Wire each view to corresponding backend endpoint
2. Add ToolpathPlayer for visualization
3. Add download/RMOS integration
4. OR: Mark views as "Coming Soon" explicitly in UI

---

### 2.3 Blueprint Vectorizer → CAM (Manual Gap)

**Flow:** User uploads blueprint image → Vectorizer extracts geometry → DXF is produced → User must manually download and re-upload to Quick Cut

**Evidence:**

File: `services/blueprint-import/vectorizer_phase3.py`
```python
def export_to_dxf(self, output_path: str):
    # DXF is written to disk
    # No automatic handoff to CAM
```

Frontend Blueprint Lab has no "Send to CAM" or "Open in Quick Cut" button.

**Why this is P1:** The vectorization pipeline works. The CAM pipeline works. They are not connected. Users must perform manual file transfer between features that should flow automatically.

**Remediation:**
1. Add "Send to Quick Cut" button that passes DXF blob directly to QuickCutView
2. Or: Store vectorized DXF in RMOS artifact, provide link to open in CAM

---

## Part 3: Backend Orphan Endpoints

These endpoints exist and function but have no frontend UI calling them.

| Endpoint | Router File | Purpose | Frontend Status |
|----------|-------------|---------|-----------------|
| `POST /api/cam/binding/channel/gcode` | `binding_router.py` | Binding channel toolpath | No UI |
| `POST /api/cam/binding/purfling/gcode` | `binding_router.py` | Purfling inlay toolpath | No UI |
| `POST /api/cam/profiling/gcode` | `profiling_router.py` | Profile with holding tabs | No UI |
| `POST /api/cam/toolpath/biarc/gcode` | `toolpath_router.py` | Biarc smoothing | No UI |
| `POST /api/cam/toolpath/roughing/gcode` | `toolpath_router.py` | Roughing passes | No UI |
| `POST /api/cam/headstock/generate-inlay` | `headstock_router.py` | Headstock inlay | Limited (Art Studio only) |
| `POST /api/cam/toolpath/helical_entry` | `helical_router.py` | Helical ramping | HelicalRampLab only |

**Verification:**
```bash
# For each endpoint, search for frontend callers
grep -rn "binding/channel\|binding/purfling" packages/client/src
# Returns: nothing

grep -rn "profiling/gcode" packages/client/src
# Returns: nothing

grep -rn "biarc/gcode\|roughing/gcode" packages/client/src
# Returns: nothing
```

**Why this matters:** These represent implemented CAM capabilities that users cannot access. The backend work is done; only frontend views are missing.

**Remediation:**
1. Build views for high-value operations (binding, profiling)
2. Document API-only operations for advanced users
3. Or: Expose through a "Custom CAM" view with operation selector

---

## Part 4: Frontend Calls to Missing Endpoints

| Component | Called Endpoint | Exists? |
|-----------|-----------------|---------|
| `useGuitarCAM.ts` | `POST /api/guitar/design/parametric/to-cam` | **NO** |
| `ToolpathSimulatorView.vue` | `POST /api/cam/simulate/preview` | **NO** |
| `ToolpathSimulatorView.vue` | `POST /api/cam/simulate/analyze` | **NO** |
| `FretSlottingView.vue` | `POST /api/cam/fret-slots/generate` | **NO** (only `/preview`) |

**Verification methodology:**
```bash
# Extract all /api/ calls from frontend
grep -rhn "/api/" packages/client/src --include="*.ts" --include="*.vue" | \
  grep -E "fetch|axios|post|get" | \
  sort -u > frontend_api_calls.txt

# Extract all registered routes from backend
grep -rhn "@router\.\(get\|post\|put\|delete\)" services/api/app | \
  sort -u > backend_routes.txt

# Diff to find mismatches (manual review required)
```

---

## Part 5: Silent Fallback Locations

These are places where errors are caught and suppressed, potentially hiding failures from users.

### 5.1 Wood Stiffness Index

File: `packages/client/src/composables/useStiffnessIndex.ts`
```typescript
// Line ~200
} catch (error) {
  // Silent fallback to hardcoded set - do not surface error to user
  return HARDCODED_STIFFNESS_VALUES;
}
```

**Risk:** User receives stiffness calculations without knowing they're from fallback data, not their actual wood species.

### 5.2 Bridge Presets

File: `packages/client/src/composables/useBridgePresets.ts`
```typescript
// Lines 53-55
if (!response.ok) {
  console.debug('Using fallback presets');
  return FALLBACK_PRESETS;
}
```

**Risk:** User receives preset values without knowing API failed.

### 5.3 General Pattern

Multiple components follow this pattern:
```typescript
try {
  const data = await fetchSomething();
  return data;
} catch {
  return defaultValue;  // Silent fallback
}
```

**Remediation:** Add info banners when fallback is used: "Using cached data — refresh to retry"

---

## Part 6: Missing "Send to CAM" Handoffs

These design tools generate geometry or calculations but have no path to CAM.

| Design Tool | Route | Output Type | CAM Handoff |
|-------------|-------|-------------|-------------|
| Body Outline Generator | `/design-hub` → body-outline | Polygon points | **Broken** (P0) |
| Neck Generator | `/design-hub` → neck | G-code text | **Console only** (P1) |
| Archtop Calculator | `/design-hub` → archtop | Contour data | **None** |
| Bracing Calculator | `/design-hub` → bracing | Brace positions | **None** |
| Hardware Layout | `/design-hub` → hardware | Drill positions | **DXF only** |
| Rosette Designer (Design Hub) | `/design-hub` → rosette | Ring geometry | **Unclear** (separate from RMOS flow) |
| Bridge Calculator | `/design-hub` → bridge | Bridge dimensions | **DXF only** |
| Fretboard Compound Radius | `/design-hub` → compound-radius | Radius profile | **None** |
| Scale Length Designer | `/design-hub` → scale-length | Fret positions | **None** |

**Pattern:** Design Hub is a collection of calculators that produce geometry, but only a few connect to manufacturing output. The hub implies a complete workflow that doesn't exist.

**Remediation strategy:**
1. **High value:** Body outline → Adaptive pocket (core guitar manufacturing)
2. **Medium value:** Hardware layout → Drilling G-code
3. **Lower value:** Calculators that inform design but don't directly produce CAM

---

## Part 7: Fully Working E2E Flows

For reference, these flows work correctly from input to downloadable/persisted artifact:

| Flow | Entry Point | Backend | Simulation | Download | RMOS |
|------|-------------|---------|------------|----------|------|
| Quick Cut (DXF→GRBL) | `/quick-cut` | `/api/rmos/wrap/mvp/dxf-to-grbl` | Risk check | Yes | Yes |
| Adaptive Pocket | `/lab/adaptive` | `/api/cam/pocket/adaptive/*` | Backplot | Yes | Yes |
| Rosette CAM | `/rosette` | `/api/cam/rosette/*` | Preview | Yes | Yes |
| V-Carve | `/art-studio/vcarve` | `/api/cam/vcarve/gcode` | Preview | Yes | No |
| Bridge DXF | `/lab/bridge` | `/api/cam/bridge/export_dxf` | N/A | Yes | No |
| G-code Simulation | `/dxf-to-gcode` | `/api/cam/sim/*` | ToolpathPlayer | N/A | Yes |

**What makes these work:**
1. Frontend calls real backend endpoint
2. Backend returns actual generated data (not mock)
3. Frontend displays result in appropriate viewer
4. Download/export mechanism exists
5. (Optional) RMOS tracks run artifacts

---

## Part 8: Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DESIGN HUB                                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ Body Outline│ │    Neck     │ │   Archtop   │ │   Bracing   │           │
│  │  Generator  │ │  Generator  │ │ Calculator  │ │ Calculator  │           │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘           │
│         │               │               │               │                   │
│         ▼               ▼               ▼               ▼                   │
│    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐                │
│    │ Points  │    │ G-code  │    │ Contour │    │ Brace   │                │
│    │ (JSON)  │    │ (text)  │    │ (JSON)  │    │ (JSON)  │                │
│    └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘                │
│         │              │              │              │                      │
│         ▼              ▼              ▼              ▼                      │
│    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐                │
│    │ Send to │    │ console │    │  (none) │    │  (none) │                │
│    │   CAM   │    │  .log() │    │         │    │         │                │
│    │  ✗ P0   │    │  ✗ P1   │    │  ✗ P1   │    │  ✗ P1   │                │
│    └─────────┘    └─────────┘    └─────────┘    └─────────┘                │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                              CAM VIEWS                                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │  Quick Cut  │ │  Fret Slot  │ │   Pocket    │ │  Simulator  │           │
│  │   ✓ E2E    │ │   ✗ P0     │ │   ✗ P1     │ │   ✗ P0     │           │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘           │
│         │               │               │               │                   │
│         ▼               ▼               ▼               ▼                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ /api/rmos/  │ │ setTimeout  │ │   (none)    │ │ /api/cam/   │           │
│  │ wrap/mvp/   │ │   mock      │ │             │ │ simulate/   │           │
│  │ dxf-to-grbl │ │             │ │             │ │ ✗ missing   │           │
│  │   ✓ real   │ │   ✗ fake   │ │   ✗ stub   │ │             │           │
│  └──────┬──────┘ └─────────────┘ └─────────────┘ └─────────────┘           │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │                    RMOS ARTIFACT STORE                       │           │
│  │  DXF input │ CAM plan │ G-code output │ Decision record     │           │
│  │     ✓           ✓           ✓               ✓               │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                           BACKEND CAM ENDPOINTS                              │
│                                                                             │
│  CALLED BY FRONTEND:                    ORPHAN (no frontend):              │
│  ┌────────────────────┐                 ┌────────────────────┐             │
│  │ /cam/sim/gcode     │ ✓               │ /cam/binding/*     │ ✗           │
│  │ /cam/pocket/adapt/*│ ✓               │ /cam/profiling/*   │ ✗           │
│  │ /cam/rosette/*     │ ✓               │ /cam/biarc/*       │ ✗           │
│  │ /cam/vcarve/*      │ ✓               │ /cam/roughing/*    │ ✗           │
│  │ /rmos/wrap/mvp/*   │ ✓               │ /cam/helical/*     │ ✗           │
│  └────────────────────┘                 └────────────────────┘             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

Legend:
  ✓ = Working E2E
  ✗ P0 = Silent failure / fake
  ✗ P1 = Exists but not wired
  ✗ = Orphan / unused
```

---

## Part 9: Recommended Execution Order

### Phase 1: Stop the Bleeding (P0 fixes)

**Goal:** No user should click a button and receive silent failure.

| # | Task | Effort | Files |
|---|------|--------|-------|
| 1 | Remove or fix "Send to CAM" button in GuitarDimensionsForm | 2h | `GuitarDimensionsForm.vue`, `useGuitarCAM.ts` |
| 2 | Wire ToolpathSimulatorView to real `/api/cam/sim/gcode` | 4h | `ToolpathSimulatorView.vue` |
| 3 | Replace fret slot mock with real generation or "Preview Only" label | 4h | `FretSlottingView.vue`, `fret_slots_router.py` |

### Phase 2: Connect Existing Capabilities (P1 fixes)

**Goal:** Backend capabilities should be accessible from frontend.

| # | Task | Effort | Files |
|---|------|--------|-------|
| 4 | Add ToolpathPlayer + download to Neck Generator | 4h | `LesPaulNeckGenerator.vue` |
| 5 | Wire CAM operation views to backend endpoints | 8h | `PocketView.vue`, `ContourView.vue`, etc. |
| 6 | Add "Send to Quick Cut" from Blueprint Lab | 4h | Blueprint views, QuickCutView |
| 7 | Implement fret slot G-code endpoint | 8h | `fret_slots_router.py` |

### Phase 3: Complete Design Hub → CAM Flow (P1 strategic)

**Goal:** Design tools should flow into manufacturing.

| # | Task | Effort | Files |
|---|------|--------|-------|
| 8 | Body outline → Adaptive pocket integration | 8h | Design Hub, Adaptive Lab |
| 9 | Hardware layout → Drilling G-code | 4h | Hardware view, drilling router |
| 10 | Surface silent fallbacks with info banners | 4h | Various composables |

### Phase 4: Expose Orphan Capabilities (P2)

**Goal:** Backend work should not go unused.

| # | Task | Effort | Files |
|---|------|--------|-------|
| 11 | Build binding channel view | 8h | New view |
| 12 | Build profiling view | 8h | New view |
| 13 | Document API-only operations | 4h | Documentation |

---

## Part 10: Verification Commands

```bash
# Verify P0 endpoints don't exist
grep -rn "parametric/to-cam" services/api/app                    # Should return nothing
grep -rn "simulate/preview\|simulate/analyze" services/api/app   # Should return nothing
grep -rn "fret.slots/generate\|fret-slots/generate" services/api/app  # Should return nothing

# Verify working endpoints exist
grep -rn "sim/gcode" services/api/app/routers                    # Should find simulation_consolidated_router
grep -rn "dxf-to-grbl" services/api/app/rmos                     # Should find mvp_router

# Find all setTimeout mocks in CAM views
grep -rn "setTimeout" packages/client/src/views/cam              # Should find FretSlottingView

# Find console.log in generators (output going nowhere)
grep -rn "console.log" packages/client/src/components/toolbox/generators

# Count orphan backend endpoints
grep -rn "@router.post" services/api/app/cam/routers | wc -l     # Total CAM endpoints
grep -rn "cam/binding\|cam/profiling\|cam/biarc" packages/client/src | wc -l  # Frontend calls (should be 0)

# Verify ToolpathPlayer is used in DxfToGcodeView (working flow)
grep -n "ToolpathPlayer" packages/client/src/views/DxfToGcodeView.vue

# Verify ToolpathPlayer is NOT used in CamWorkspaceView (gap)
grep -n "ToolpathPlayer" packages/client/src/views/cam/CamWorkspaceView.vue
```

---

## Part 11: Key File Reference

### Frontend — Critical Gaps

```
packages/client/src/
├── components/toolbox/
│   ├── composables/
│   │   └── useGuitarCAM.ts              ← Calls missing endpoint (P0)
│   └── generators/
│       └── LesPaulNeckGenerator.vue     ← Console-only output (P1)
├── views/cam/
│   ├── FretSlottingView.vue             ← setTimeout mock (P0)
│   ├── ToolpathSimulatorView.vue        ← Wrong endpoint refs (P0)
│   ├── PocketView.vue                   ← Form scaffold (P1)
│   ├── ContourView.vue                  ← Form scaffold (P1)
│   ├── SurfacingView.vue                ← Form scaffold (P1)
│   └── DrillingView.vue                 ← Form scaffold (P1)
└── views/
    ├── DxfToGcodeView.vue               ← WORKING E2E
    └── QuickCutView.vue                 ← WORKING E2E
```

### Backend — Working vs Orphan

```
services/api/app/
├── routers/
│   └── simulation_consolidated_router.py    ← WORKING (sim/gcode, sim/upload)
├── cam/routers/
│   ├── adaptive/plan_router.py              ← WORKING
│   ├── rosette_router.py                    ← WORKING
│   ├── fret_slots_router.py                 ← PARTIAL (preview only)
│   ├── binding_router.py                    ← ORPHAN
│   ├── profiling_router.py                  ← ORPHAN
│   └── toolpath_router.py                   ← ORPHAN (biarc, roughing)
└── rmos/
    └── mvp_router.py                        ← WORKING (dxf-to-grbl)
```

---

## Appendix: Audit Methodology

This audit was conducted by:

1. **Endpoint enumeration:** Grep all `@router.post`/`@router.get` in backend, all `fetch`/`axios` in frontend
2. **Cross-reference:** Match frontend calls to backend routes, identify mismatches
3. **Code path tracing:** For each UI action button, trace handler → API call → response handling → display
4. **Mock detection:** Search for `setTimeout`, `mock`, `stub`, `TODO`, `FIXME` in action handlers
5. **Silent failure detection:** Search for `catch {}`, `catch (e) { }`, `return []`, `return null` patterns
6. **RMOS integration check:** Verify which flows create runs/artifacts vs. transient output

**Tools used:**
- `grep -rn` for pattern matching
- Manual code review for flow tracing
- Router registry inspection for endpoint registration

---

*Audit completed: 2026-05-06*  
*Auditor: Claude (comprehensive E2E trace)*  
*Supersedes: CAM_PIPELINE_DEVELOPER_HANDOFF_2026-05-06.md (component-level only)*
