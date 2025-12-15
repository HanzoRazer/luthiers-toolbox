# Option A - Code Block Inventory

**File:** Option A.txt  
**Total Lines:** 27,152  
**Total Code Blocks:** 17 files  
**Date Analyzed:** November 9, 2025

---

## 📋 Executive Summary

Option A contains a **complete CAM Pipeline orchestration system** with:
- ✅ Full **DXF → Preflight → Adaptive → Post → Sim** workflow
- ✅ **Machine/Post profile management** (GRBL, Haas, LinuxCNC, Fanuc, Mach4)
- ✅ **Pipeline preset system** (save/load recipes)
- ✅ **Simulation-to-backplot wiring** (color-coded errors in visualization)
- ✅ **Art Studio integration endpoints** (Rosette, Headstock, Relief)
- ✅ **Test suites** for blueprint → DXF → adaptive workflows

**Status:** Ready for extraction and integration into main codebase.

---

## 🗂️ File Inventory

### **Frontend Components** (Vue 3 + TypeScript)

#### 1. **CamPipelineRunner.vue** (Line 17)
**Purpose:** Unified pipeline runner component  
**Features:**
- DXF file upload
- Machine/Post profile selection
- Preset save/load
- Per-operation result cards
- Event emissions: `adaptive-plan-ready`, `sim-result-ready`

**API Integration:**
- `POST /cam/pipeline/run` with `FormData(file, pipelineJSON)`
- `GET /cam/presets` for preset listing
- `POST /cam/presets` for saving recipes

**Key State:**
```typescript
const machineId = ref<string | null>(null)
const postId = ref<string | null>(null)
const selectedPresetId = ref<string | null>(null)
const presets = ref<any[]>([])
```

---

#### 2. **PipelineLabView.vue** (Line 56)
**Purpose:** Thin wrapper view at `/lab/pipeline`  
**Features:**
- Mounts `CamPipelineRunner` and `CamBackplotViewer`
- Wires `adaptive-plan-ready` and `sim-result-ready` events
- Prioritizes sim moves for backplot (falls back to adaptive moves)

**Template Structure:**
```vue
<template>
  <CamPipelineRunner
    @adaptive-plan-ready="onAdaptivePlanReady"
    @sim-result-ready="onSimResultReady"
  />
  <CamBackplotViewer
    :moves="plotMoves"
    :stats="plotStats"
    :overlays="adaptiveOverlays"
    :sim-issues="simIssues"
  />
</template>
```

---

#### 3. **MachineListView.vue** (Line 434)
**Purpose:** Machine profile management UI  
**Features:**
- Lists available CNC machine profiles
- Displays specs (max_feed_xy, rapid, accel, jerk, safe_z)
- CRUD operations for machine profiles

**Backend Integration:**
- `GET /cam/machines` → List all profiles
- `GET /cam/machines/{id}` → Get specific machine

**Example Machine:**
```json
{
  "id": "grbl_generic",
  "name": "GRBL Generic Router",
  "max_feed_xy": 2000,
  "rapid": 5000,
  "accel": 500,
  "safe_z_default": 5.0
}
```

---

#### 4. **PostListView.vue** (Line 509)
**Purpose:** Post-processor profile management UI  
**Features:**
- Lists available post-processors (GRBL, Haas, LinuxCNC, Fanuc, Mach4)
- Displays dialect, mode, line number settings
- CRUD operations for post profiles

**Backend Integration:**
- `GET /cam/posts` → List all posts
- `GET /cam/posts/{id}` → Get specific post

**Example Post:**
```json
{
  "id": "haas_ngc",
  "name": "Haas NGC (VMC)",
  "post": "haas",
  "post_mode": "header_footer",
  "line_numbers": true
}
```

---

#### 5. **CamBackplotViewer.vue** (Line 5058)
**Purpose:** Shared backplot component with severity coloring  
**Features:**
- Renders moves as SVG polyline segments
- Color-codes by severity (error=red, warning=orange, rapid=gray)
- Displays overlays (tight radius zones, slowdown markers)
- Normalizes to `viewBox="0 0 100 100"` with padding

**Props:**
```typescript
const props = defineProps<{
  moves: any[]
  stats?: any | null
  overlays?: any[]
  simIssues?: any[] | null  // NEW for sim integration
}>()
```

**Severity Mapping:**
```typescript
function strokeForSegment(seg: Segment): string {
  const severity = severityByMoveIdx.value.get(seg.moveIdx)
  if (!severity) return '#0f172a' // default dark
  if (severity === 'error') return '#b91c1c'   // red
  if (severity === 'warning') return '#f97316' // orange
  return '#0f172a'
}
```

---

#### 6. **Art Studio Components** (Lines 5142-5202)

##### 6a. **ArtStudioRosette.vue** (Line 5142)
**Purpose:** Soundhole rosette designer UI  
**Features:**
- Channel count, width, depth inputs
- Real-time preview canvas
- DXF + G-code export
- Preset management (Martin, Taylor, Gibson styles)

##### 6b. **ArtStudioHeadstock.vue** (Line 5164)
**Purpose:** Headstock inlay designer  
**Features:**
- Logo/design upload
- Vectorization pipeline
- CAM export for inlay pocketing

##### 6c. **ArtStudioRelief.vue** (Line 5182)
**Purpose:** 3D relief carving from images  
**Features:**
- Image upload → depth map
- Adaptive clearing toolpaths
- Multi-pass roughing + finishing

---

#### 7. **Router Configuration** (Lines 126, 5202)
**Purpose:** Vue Router setup for lab routes  
**Routes:**
```typescript
{
  path: '/lab/adaptive',
  name: 'AdaptiveLab',
  component: AdaptiveLabView
},
{
  path: '/lab/pipeline',
  name: 'PipelineLab',
  component: PipelineLabView
}
```

---

### **Backend Routers** (FastAPI + Pydantic)

#### 8. **pipeline_router.py** (Line 5008)
**Purpose:** Main pipeline orchestration endpoint  
**Endpoint:** `POST /cam/pipeline/run`

**Operations Supported:**
```python
PipelineOpKind = Literal[
    "dxf_preflight",
    "adaptive_plan",
    "adaptive_plan_run",
    "export_post",      # NEW
    "simulate_gcode"    # NEW
]
```

**Request Schema:**
```python
class PipelineSpec(BaseModel):
    ops: List[PipelineOpSpec]
    tool_d: float
    units: Literal["mm", "inch"]
    geometry_layer: Optional[str]
    auto_scale: bool
    cam_layer_prefix: str
```

**Response Schema:**
```python
class PipelineResponse(BaseModel):
    ops: List[PipelineOpResult]  # Each with ok, payload, error
    machine_id: Optional[str]
    post_id: Optional[str]
    units: str
```

**Key Implementation:**
```python
@router.post("/pipeline/run", response_model=PipelineResponse)
async def run_pipeline(
    file: UploadFile,
    pipeline: str = Form(...)  # JSON string
) -> PipelineResponse:
    # Parse pipeline spec
    # Execute ops in sequence
    # Return aggregated results
```

---

#### 9. **pipeline_presets_router.py** (Line 2519)
**Purpose:** Save/load pipeline recipes  
**Storage:** JSON file in `app/data/pipeline_presets.json`

**Endpoints:**
- `GET /cam/presets` → List all presets
- `POST /cam/presets` → Create new preset
- `GET /cam/presets/{id}` → Get specific preset
- `DELETE /cam/presets/{id}` → Delete preset

**Preset Schema:**
```python
class PipelinePreset(BaseModel):
    id: str
    name: str
    units: Literal["mm", "inch"]
    machine_id: Optional[str]
    post_id: Optional[str]
    tool_d: float
    created_at: str
```

---

#### 10. **dxf_plan_router.py** (Line 2636)
**Purpose:** DXF → Adaptive Plan conversion  
**Endpoint:** `POST /cam/plan_from_dxf`

**Request:**
```python
class PlanFromDxfIn(BaseModel):
    dxf_bytes: str  # base64 encoded
    layer: Optional[str]
    units: Literal["mm", "inch"]
    auto_scale: bool
```

**Response:**
```python
class PlanFromDxfResponse(BaseModel):
    loops: List[Loop]
    units: str
    area_mm2: float
```

**Integration:** Used by `adaptive_plan` operation in pipeline

---

#### 11. **adaptive_router.py** (Lines 2940-2994, 4982)
**Purpose:** Adaptive pocketing endpoints  
**Endpoints:**
- `POST /cam/pocket/adaptive/plan` → Generate toolpath
- `POST /cam/pocket/adaptive/plan_from_dxf` → DXF → Plan

**Plan Schema:**
```python
class PlanIn(BaseModel):
    loops: List[Loop]
    tool_d: float
    stepover: float
    stepdown: float
    margin: float
    strategy: Literal["Spiral", "Lanes"]
    smoothing: float
    climb: bool
    feed_xy: int
    safe_z: float
    z_rough: float
```

---

#### 12. **cam_sim_router.py** (Lines 4776-4806, 5386-5615)
**Purpose:** G-code simulation and validation  
**Endpoint:** `POST /cam/simulate_gcode`

**Request:**
```python
class SimRequest(BaseModel):
    gcode: str
    safe_z: float = 5.0
    feed_xy: int = 1200
    feed_z: int = 300
```

**Response:**
```python
class SimResult(BaseModel):
    issues: List[SimIssue]
    moves: List[Dict[str, Any]]
    summary: SimSummary
```

**Issue Types:**
- `below_safe_z` (severity: error)
- `rapid_near_stock` (severity: warning)
- `spindle_not_on` (severity: error)
- `feed_too_fast` (severity: warning)

**Simulation Logic:**
```python
def _simulate_moves(
    moves: List[Dict[str, Any]],
    safe_z: float,
    feed_xy: int,
    feed_z: int
) -> Tuple[List[SimIssue], SimSummary]:
    # Track Z position
    # Check safe_z violations
    # Detect rapids near workpiece
    # Validate feed rates
```

---

### **Utility Modules**

#### 13. **cam_sim_bridge.py** (Line 2770)
**Purpose:** Normalize simulation output  
**Functions:**
- `_extract_issues_from_raw()` → Parse sim results into `SimIssue` schema
- `simulate_gcode_inline()` → Wrapper for inline simulation calls

**Schema:**
```python
class SimIssue(BaseModel):
    type: str  # below_safe_z, rapid_near_stock, etc.
    severity: Literal["error", "warning", "info"]
    move_idx: int
    line: Optional[str]
    message: str
```

---

#### 14. **dxf_to_adaptive.py** (Line 5857)
**Purpose:** DXF parsing for adaptive pocketing  
**Functions:**
- `_load_doc_from_bytes()` → Parse DXF from bytes
- `_extract_loops_from_layer()` → Extract LWPOLYLINE loops
- `_auto_detect_geometry_layer()` → Find GEOMETRY/POCKET layers
- `_normalize_units()` → Handle mm ↔ inch conversion

**Error Classes:**
```python
class DxfMissingEngineError(RuntimeError): ...
class DxfParseError(RuntimeError): ...
class DxfGeometryError(RuntimeError): ...
```

---

#### 15. **bridge_preflight.py** (Line 7911)
**Purpose:** DXF preflight validation for bridge profiles  
**Functions:**
- `_validate_bridge_layers()` → Check for required layers
- `_check_saddle_geometry()` → Validate saddle compensation curves
- `_preflight_bridge_dxf()` → Full bridge-specific validation

**Validation Rules:**
- SADDLE layer required
- BRIDGE_OUTLINE layer required
- Closed paths for CNC operations
- Dimension sanity checks

---

#### 16. **TypeScript Types** (Line 5030)
**Purpose:** Frontend type definitions  
**File:** `src/types/cam.ts`

```typescript
export type PipelineOpKind =
  | 'dxf_preflight'
  | 'adaptive_plan'
  | 'adaptive_plan_run'
  | 'export_post'
  | 'simulate_gcode'

export interface PipelineOpSpec {
  kind: PipelineOpKind
  params: Record<string, any>
}

export interface PipelineOpResult {
  kind: PipelineOpKind
  ok: boolean
  payload?: any
  error?: string
}

export interface SimIssue {
  type: string
  severity: 'error' | 'warning' | 'info'
  move_idx: number
  line?: string
  message: string
}
```

---

#### 17. **API Client** (Line 5040)
**Purpose:** Frontend API wrapper functions  
**File:** `src/api/adaptive.ts`

```typescript
export async function planAdaptiveFromDxf(
  dxfBytes: string,
  layer?: string,
  units?: string
): Promise<PlanFromDxfResponse> {
  const resp = await fetch('/cam/plan_from_dxf', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dxf_bytes: dxfBytes, layer, units })
  })
  return resp.json()
}
```

---

### **Test Suites**

#### 18. **test_artstudio_blueprint_dxf.py** (Line 5215)
**Purpose:** Integration tests for Art Studio workflows  
**Test Cases:**
- `test_blueprint_to_dxf_to_adaptive()` → End-to-end blueprint → DXF → toolpath
- `test_adaptive_plan_from_real_dxf()` → DXF parsing → adaptive plan
- `test_pipeline_run_body_adaptive_smoke()` → Full pipeline smoke test

**Example Test:**
```python
def test_blueprint_to_dxf_to_adaptive():
    # 1. Upload blueprint image
    # 2. AI analysis + OpenCV vectorization
    # 3. Export to DXF
    # 4. Parse DXF → loops
    # 5. Generate adaptive toolpath
    # 6. Validate moves/stats
    assert len(result['moves']) > 100
    assert result['stats']['time_s'] > 0
```

---

## 🔑 Key Integration Points

### **1. export_post Operation** (NEW)
**Location:** `pipeline_router.py` line ~2441

**Purpose:** Final G-code export with post-processor headers/footers

**Implementation:**
```python
async def _wrap_export_post(params: Dict[str, Any]) -> Dict[str, Any]:
    endpoint = params.get("endpoint")  # e.g., "/cam/roughing_gcode"
    gcode = params.get("gcode") or ctx["plan_result"]["gcode"]
    
    body = {
        "gcode": gcode,
        "post": params.get("post", "grbl"),
        "post_mode": params.get("post_mode", "header_footer"),
        "units": params.get("units", shared_units)
    }
    
    resp = await client.post(endpoint, json=body)
    return resp.json()
```

**Usage in Pipeline Spec:**
```json
{
  "kind": "export_post",
  "params": {
    "endpoint": "/cam/roughing_gcode",
    "post": "haas_ngc",
    "post_mode": "header_footer",
    "units": "mm"
  }
}
```

---

### **2. simulate_gcode Operation** (NEW)
**Location:** `pipeline_router.py` line ~2441

**Purpose:** Validate exported G-code and detect issues

**Implementation:**
```python
async def _wrap_simulate_gcode(params: Dict[str, Any]) -> Dict[str, Any]:
    gcode = params.get("gcode") or ctx["plan_result"]["gcode"]
    safe_z = params.get("safe_z", 5.0)
    feed_xy = params.get("feed_xy", 1200)
    
    async with httpx.AsyncClient(base_url=base_url) as client:
        resp = await client.post("/cam/simulate_gcode", json={
            "gcode": gcode,
            "safe_z": safe_z,
            "feed_xy": feed_xy
        })
    
    return resp.json()
```

**Output Schema:**
```python
{
  "issues": [
    {
      "type": "below_safe_z",
      "severity": "error",
      "move_idx": 42,
      "message": "Z=-10.0 below safe_z=5.0"
    }
  ],
  "moves": [ ... ],  # Parsed G-code as move objects
  "summary": {
    "time_s": 32.1,
    "move_count": 156,
    "length_mm": 547.3
  }
}
```

---

### **3. Simulation → Backplot Wiring**

**Data Flow:**
```
Pipeline → simulate_gcode op → issues array
    ↓
CamPipelineRunner emits 'sim-result-ready'
    ↓
PipelineLabView receives event
    ↓
CamBackplotViewer :sim-issues prop
    ↓
severityByMoveIdx Map<move_idx, severity>
    ↓
strokeForSegment() colors polylines
```

**Event Payload:**
```typescript
interface SimResultPayload {
  issues: SimIssue[]
  moves: any[]
  summary: {
    time_s: number
    move_count: number
    length_mm: number
  }
}
```

---

### **4. Machine/Post Profile System**

**Profile Storage:**
```
services/api/app/data/
├── machines/
│   ├── grbl_generic.json
│   ├── haas_minimill.json
│   └── ...
└── posts/
    ├── grbl.json
    ├── haas_ngc.json
    └── ...
```

**Machine Profile Example:**
```json
{
  "id": "haas_minimill",
  "name": "Haas MiniMill (metric)",
  "max_feed_xy": 12700,
  "rapid": 25400,
  "accel": 3048,
  "jerk": 15240,
  "safe_z_default": 25.0,
  "work_envelope": {
    "x_min": 0,
    "x_max": 406,
    "y_min": 0,
    "y_max": 254,
    "z_min": -254,
    "z_max": 0
  }
}
```

**Post Profile Example:**
```json
{
  "id": "haas_ngc",
  "name": "Haas NGC (VMC)",
  "post": "haas",
  "post_mode": "header_footer",
  "line_numbers": true,
  "header": [
    "G90 G54 G17 G40 G49 G80",
    "G21",
    "M01"
  ],
  "footer": [
    "M30"
  ]
}
```

---

## 🎯 Extraction Priority

### **Phase 1: Core Pipeline** (Highest Impact)
1. **pipeline_router.py** → Add `export_post` and `simulate_gcode` operations
2. **cam_sim_router.py** → Implement G-code simulation endpoint
3. **CamPipelineRunner.vue** → Full component with preset management
4. **PipelineLabView.vue** → Thin wrapper view
5. **CamBackplotViewer.vue** → Severity-aware visualization

**Estimated Time:** 2-3 days  
**Value:** Complete DXF → G-code → Sim workflow

---

### **Phase 2: Machine/Post Management** (Medium Impact)
1. **Machine/Post routers** → CRUD endpoints for profiles
2. **MachineListView.vue** → Profile management UI
3. **PostListView.vue** → Post-processor management UI
4. **Profile JSON templates** → Initial GRBL, Haas, LinuxCNC configs

**Estimated Time:** 1-2 days  
**Value:** Multi-CNC controller support

---

### **Phase 3: Art Studio Integration** (Lower Priority)
1. **ArtStudioRosette.vue** → Soundhole designer
2. **ArtStudioHeadstock.vue** → Headstock inlay designer
3. **ArtStudioRelief.vue** → Relief carving from images
4. **test_artstudio_blueprint_dxf.py** → Integration tests

**Estimated Time:** 2-3 days  
**Value:** Domain-specific lutherie tools

---

## ✅ Validation Checklist

Before extracting each component, verify:
- [ ] Component doesn't already exist in `services/api/app/routers/` or `packages/client/src/components/`
- [ ] Dependencies are available (ezdxf, pyclipper, shapely for backend; Vue 3, TypeScript for frontend)
- [ ] API contracts match between frontend/backend (Pydantic models ↔ TypeScript interfaces)
- [ ] Comprehensive documentation headers added (Phase 7 coding policy)
- [ ] Integration points identified (router registration, route config, component imports)

---

## 🚀 Next Steps

**Ready to proceed with extraction?**

1. **Start with Phase 1** (Core Pipeline) - highest value, self-contained
2. **Apply coding policy** headers to each extracted file
3. **Create integration tasks** for wiring into existing codebase
4. **Run tests** after each phase to validate functionality

**Estimated Total Time:** 5-8 days for all 3 phases

---

**Status:** ✅ Inventory Complete  
**Date:** November 9, 2025  
**Next Action:** Await user decision on extraction priority
