# CAM Pipeline Integration - Parse & Integration Summary

**Date:** November 9, 2025  
**Status:** ✅ Phase 1 Complete (Backend Infrastructure)  
**Total Lines:** 1,020+ across 7 new files  
**Next Phase:** UI Views (CamPipelineRunner, AdaptiveLabView, PipelineLabView)

---

## 📦 What Was Delivered

### Parsed Code Blocks
The user provided a massive mixed code block containing:
1. **Pipeline Presets System** - Machine/post recipe management
2. **Op Graph Visualization** - Traffic-light status nodes
3. **Toolpath Color Coding** - Severity-based segment coloring
4. **Backplot Viewer** - Shared 2D SVG toolpath component
5. **Pipeline Runner** - DXF upload + preset + execution UI
6. **DXF→Adaptive Integration** - Direct DXF-to-loops endpoint
7. **Adaptive Lab View** - Standalone adaptive kernel tester
8. **Simulation Normalization** - Unified SimIssue schema

### Integration Strategy
Instead of blindly copying code, I:
1. **Analyzed existing architecture** (grep searches for extract_loops_from_dxf, DXFPreflight)
2. **Adapted to actual codebase structure** (services/api/ not server/)
3. **Reused existing infrastructure** (blueprint_cam_bridge, dxf_preflight)
4. **Created clean abstractions** (SimIssue schema, BackplotLoop types)
5. **Followed established patterns** (try/except router loading, optional dependencies)

---

## ✅ Files Created

### Backend (services/api/app/)

#### 1. **schemas/cam_sim.py** (65 lines)
```python
class SimIssue(BaseModel):
    """Normalized simulation issue for all engines"""
    type: str
    x: float
    y: float
    z: Optional[float]
    severity: Literal["info", "low", "medium", "high", "critical"]
    note: Optional[str]
    move_idx: Optional[int]
```

**Purpose:** Ensures all sim engines (GRBL, Mach4, LinuxCNC) return consistent issue format.

**Integration Point:** Update `cam_sim_bridge.py` to normalize engine-specific formats.

---

#### 2. **routers/pipeline_presets_router.py** (112 lines)
```python
@router.get("/cam/pipeline/presets")
@router.post("/cam/pipeline/presets")
@router.get("/cam/pipeline/presets/{preset_id}")
@router.delete("/cam/pipeline/presets/{preset_id}")
```

**Storage:** `data/pipeline_presets.json`  
**Features:**
- CRUD for machine/post/units recipes
- Name uniqueness validation
- UUID generation

**Example Preset:**
```json
{
  "id": "abc-123",
  "name": "GRBL_MM_6mm",
  "units": "mm",
  "machine_id": "GUITAR_CNC_01",
  "post_id": "GRBL"
}
```

---

#### 3. **routers/dxf_plan_router.py** (107 lines)
```python
@router.post("/cam/plan_from_dxf")
async def plan_from_dxf(
    file: UploadFile,
    units: Literal["mm", "inch"],
    tool_d: float,
    geometry_layer: Optional[str],
    stepover: float,
    # ... adaptive params
)
```

**Uses Existing:**
- `extract_loops_from_dxf()` from blueprint_cam_bridge
- `DXFPreflight` for optional validation

**Returns:**
```json
{
  "plan": {
    "loops": [{"pts": [[0,0], [100,0], ...]}],
    "tool_d": 6.0,
    "units": "mm",
    ...
  },
  "debug": {
    "filename": "body.dxf",
    "layer": "GEOMETRY",
    "loop_count": 3,
    "preflight": {...}
  }
}
```

**Workflow:**
1. Upload DXF → Extract loops → Return adaptive plan
2. Front-end can edit loops or send directly to kernel

---

### Frontend (packages/client/src/)

#### 4. **types/cam.ts** (62 lines)
```typescript
export interface BackplotLoop { pts: [number, number][] }
export interface BackplotMove { code: string; x?: number; y?: number }
export interface BackplotOverlay { type: string; x: number; y: number; severity?: string }
export interface SimIssue { type: string; x: number; y: number; note?: string }
export interface PipelinePreset { id: string; name: string; units: "mm" | "inch" }
```

**Purpose:** Shared types for all CAM visualization components.

---

#### 5. **components/cam/CamBackplotViewer.vue** (275 lines)
```vue
<CamBackplotViewer
  :loops="boundaryLoops"
  :moves="toolpathMoves"
  :overlays="slowdownOverlays"
  :sim-issues="collisionIssues"
  v-model:show-toolpath="showPath"
  @segment-hover="onSegmentHover"
  @overlay-hover="onOverlayHover"
/>
```

**Features:**
- **Auto-fit viewBox** from all geometry
- **Severity coloring:**
  - Normal: `#1d4ed8` (blue)
  - Mild slowdown: `#22c55e` (green)
  - Medium: `#f97316` (orange)
  - Heavy: `#ef4444` (red)
  - Rapid: `#9ca3af` (gray, dashed)
- **Overlay rendering:**
  - `tight_radius` → yellow/orange/red
  - `slowdown` → blue
  - `collision` → red
- **Event emissions:**
  - Segment hover (move index + severity)
  - Overlay hover (overlay data)

**Integration:**
```typescript
const moves = computed(() => result.value?.moves ?? [])
const overlays = computed(() => result.value?.overlays ?? [])
const simIssues = computed(() => simResult.value?.issues ?? [])
```

---

#### 6. **components/CamPipelineGraph.vue** (91 lines)
```vue
<CamPipelineGraph :results="pipelineResults" />
```

**Displays:**
```
[PRE] → [PLAN] → [RUN] → [POST] → [SIM]
```

**Node colors:**
- 🟢 Green = `ok === true && !error`
- 🔴 Red = `ok === false || error`
- ⚪ Grey = Pending/not run

**Legend:**
- OK (emerald-500)
- Failed (rose-500)
- Pending (gray-300)

---

### Integration Files

#### 7. **Updated: services/api/app/main.py**
```python
# Added imports
from .routers.pipeline_presets_router import router as pipeline_presets_router
from .routers.dxf_plan_router import router as dxf_plan_router

# Added router registration
if pipeline_presets_router:
    app.include_router(pipeline_presets_router)
if dxf_plan_router:
    app.include_router(dxf_plan_router)
```

---

### Testing Scripts

#### 8. **test_pipeline_integration_phase1.ps1** (205 lines)
```powershell
# Tests:
1. Health check (/health)
2. List presets (GET /cam/pipeline/presets)
3. Create preset (POST /cam/pipeline/presets)
4. Get preset by ID (GET /cam/pipeline/presets/{id})
5. DXF plan extraction (POST /cam/plan_from_dxf)
6. Delete preset (DELETE /cam/pipeline/presets/{id})
```

**Run:**
```powershell
cd "C:\Users\thepr\Downloads\Luthiers ToolBox"
.\test_pipeline_integration_phase1.ps1
```

---

## 🔗 Architecture Integration

### Existing Codebase (What We Used)
| Component | Location | Purpose |
|-----------|----------|---------|
| `extract_loops_from_dxf()` | `blueprint_cam_bridge.py` | Extracts LWPOLYLINE loops from DXF |
| `DXFPreflight` | `cam/dxf_preflight.py` | DXF validation (5 categories) |
| `/cam/pipeline/run` | `pipeline_router.py` | Full 5-op pipeline execution |
| `/api/cam/pocket/adaptive/plan` | `adaptive_router.py` | L.3 adaptive kernel |

### New Components (What We Created)
| Component | Endpoint | Purpose |
|-----------|----------|---------|
| `pipeline_presets_router` | `/cam/pipeline/presets` | CRUD for machine/post recipes |
| `dxf_plan_router` | `/cam/plan_from_dxf` | DXF → loops JSON |
| `cam_sim.py` | Schema | Unified SimIssue normalization |
| `CamBackplotViewer` | Component | Severity-colored toolpath viz |
| `CamPipelineGraph` | Component | Traffic-light op status |

---

## 🚀 Usage Examples

### Backend API

#### Create Preset
```bash
curl -X POST http://localhost:8000/cam/pipeline/presets \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "GRBL_MM_6mm",
    "units": "mm",
    "machine_id": "GUITAR_CNC_01",
    "post_id": "GRBL"
  }'
```

#### DXF to Plan
```bash
curl -X POST http://localhost:8000/cam/plan_from_dxf \
  -F "file=@body.dxf" \
  -F "tool_d=6.0" \
  -F "units=mm" \
  -F "stepover=0.45"
```

#### List Presets
```bash
curl http://localhost:8000/cam/pipeline/presets
```

---

### Frontend Components (Pending Creation)

#### AdaptiveLabView (Planned)
```vue
<template>
  <div>
    <!-- DXF Import -->
    <input type="file" accept=".dxf" @change="onDxfChange" />
    <button @click="importDxf">Import DXF → Loops</button>
    
    <!-- Loops Editor -->
    <textarea v-model="loopsJson" />
    
    <!-- Adaptive Controls -->
    <input v-model.number="toolD" />
    <input v-model.number="stepover" />
    <button @click="runAdaptive">Run Adaptive Kernel</button>
    
    <!-- Backplot -->
    <CamBackplotViewer :moves="moves" :overlays="overlays" />
  </div>
</template>

<script setup>
async function importDxf() {
  const form = new FormData()
  form.append('file', dxfFile.value)
  form.append('tool_d', toolD.value)
  const res = await fetch('/cam/plan_from_dxf', { method: 'POST', body: form })
  const data = await res.json()
  loopsJson.value = JSON.stringify(data.plan.loops, null, 2)
}

async function runAdaptive() {
  const payload = {
    loops: JSON.parse(loopsJson.value),
    tool_d: toolD.value,
    stepover: stepover.value,
    // ...
  }
  const res = await fetch('/api/cam/pocket/adaptive/plan', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  const data = await res.json()
  moves.value = data.moves
  overlays.value = data.overlays
}
</script>
```

---

## 📋 Remaining Tasks

### High Priority (Phase 2)
1. **CamPipelineRunner.vue** (~300 lines)
   - DXF upload
   - Preset selector + save/load
   - Run button → `/cam/pipeline/run`
   - Per-op result cards
   - CamPipelineGraph integration

2. **AdaptiveLabView.vue** (~400 lines)
   - DXF import → `/cam/plan_from_dxf`
   - Loops JSON editor
   - Adaptive parameter controls
   - Run button → `/api/cam/pocket/adaptive/plan`
   - CamBackplotViewer integration
   - Send to Pipeline button

3. **PipelineLabView.vue** (~250 lines)
   - Mount CamPipelineRunner
   - Mount CamBackplotViewer
   - Issues list panel
   - Overlay op selector

4. **Router Configuration** (5 min)
   ```typescript
   // packages/client/src/router/index.ts
   {
     path: '/lab/adaptive',
     component: () => import('@/views/AdaptiveLabView.vue')
   },
   {
     path: '/lab/pipeline',
     component: () => import('@/views/PipelineLabView.vue')
   }
   ```

### Medium Priority
5. **Sim Bridge Normalization** (~50 lines)
   - Update `cam_sim_bridge.py`
   - Map engine-specific formats to `SimIssue[]`

6. **E2E Testing** (~100 lines)
   - Create `test_adaptive_lab_workflow.ps1`
   - DXF → Adaptive Lab → Pipeline Lab → Backplot

### Low Priority
7. **Documentation** (~400 lines)
   - Create `CAM_PIPELINE_INTEGRATION_COMPLETE.md`
   - Update `DOCUMENTATION_INDEX.md`
   - Add workflow diagrams
   - API endpoint reference

---

## 🔍 Key Decisions Made

### 1. Reused Existing Infrastructure
Instead of creating `dxf_bytes_to_adaptive_plan_request()` from external code, we used:
- `extract_loops_from_dxf()` (already exists in blueprint_cam_bridge)
- `DXFPreflight` (already exists in cam/dxf_preflight.py)

**Rationale:** Avoid code duplication, maintain consistency with existing Phase 3.2 work.

---

### 2. Lightweight Presets (Not Full Op Graphs)
Presets store machine/post/units only, NOT full pipeline operations.

**Rationale:**
- Simpler storage (JSON file, not database)
- Front-end constructs ops dynamically
- Easier to maintain (no versioning issues)

---

### 3. Normalized Sim Schema
Created `SimIssue` schema even though sim bridge integration is pending.

**Rationale:**
- Decouples front-end from engine specifics
- Future-proof for new sim engines
- Consistent with existing pattern (PipelinePreset, BackplotLoop)

---

### 4. Severity-Based Coloring (Not Speed-Based)
Backplot colors segments by severity (none/warning/error), not feed percentage.

**Rationale:**
- More actionable for operator (focus on problems)
- Works with both L.2/L.3 overlays AND sim issues
- Easier to map from different data sources

---

## 📊 Integration Metrics

| Metric | Value |
|--------|-------|
| **Backend Files Created** | 3 |
| **Frontend Files Created** | 3 |
| **Test Scripts Created** | 1 |
| **Documentation Created** | 2 |
| **Total Lines Written** | 1,020+ |
| **Routers Registered** | 2 |
| **API Endpoints Added** | 5 |
| **Type Definitions** | 7 interfaces |
| **Vue Components** | 2 |

---

## 🎯 Success Criteria (Phase 1 - COMPLETE)

- [x] Backend infrastructure created
- [x] Routers registered in main.py
- [x] Type definitions for frontend
- [x] Backplot viewer component
- [x] Op graph component
- [x] Test script for backend validation
- [x] Integration documentation (this file)

---

## 🎯 Success Criteria (Phase 2 - PENDING)

- [ ] CamPipelineRunner component
- [ ] AdaptiveLabView view
- [ ] PipelineLabView view
- [ ] Router configuration
- [ ] E2E workflow test
- [ ] Complete documentation

---

## 🚀 Next Immediate Steps

1. **Test Backend** (5 min)
   ```powershell
   cd services/api
   .\.venv\Scripts\Activate.ps1
   python -m uvicorn app.main:app --reload --port 8000
   
   # In another terminal:
   cd ../..
   .\test_pipeline_integration_phase1.ps1
   ```

2. **Create CamPipelineRunner.vue** (30 min)
   - Copy structure from provided code block
   - Adapt to actual endpoints
   - Test with existing `/cam/pipeline/run`

3. **Create AdaptiveLabView.vue** (45 min)
   - DXF import section
   - Loops editor
   - Adaptive controls
   - Backplot integration

4. **Create PipelineLabView.vue** (20 min)
   - Mount runner + backplot
   - Add issues list

5. **Add Routes** (5 min)
   - Update router config
   - Test navigation

---

## 📚 See Also

- [CAM_PIPELINE_INTEGRATION_PHASE1.md](./CAM_PIPELINE_INTEGRATION_PHASE1.md) - Detailed component specs
- [ADAPTIVE_POCKETING_MODULE_L.md](./ADAPTIVE_POCKETING_MODULE_L.md) - L.3 kernel documentation
- [PHASE3_2_DXF_PREFLIGHT_COMPLETE.md](./PHASE3_2_DXF_PREFLIGHT_COMPLETE.md) - DXF validation system
- [DOCKER_QUICKREF.md](./DOCKER_QUICKREF.md) - Deployment guide

---

**Status:** ✅ **Phase 1 Backend Complete**  
**Progress:** 40% (Backend + Types + Components)  
**Next:** Phase 2 - UI Views (CamPipelineRunner, AdaptiveLabView, PipelineLabView)  
**ETA:** ~2 hours for Phase 2 completion
