# Art Studio Bundle 5: Backend Implementation Complete ✅

**Date:** 2025-01-XX  
**Status:** Backend Complete (8/8 files)  
**Progress:** 53% of total bundle (8/15 files)

---

## 🎯 Overview

Backend infrastructure for **Art Studio Rosette → CAM → Pipeline → Risk Timeline** workflow is complete. All services, routers, and tests are implemented and integrated.

---

## ✅ Backend Services (8/8 Complete)

### **1. rosette_cam_bridge.py** ✅
**Path:** `services/api/app/services/rosette_cam_bridge.py`  
**Size:** 180 lines  
**Purpose:** Core CAM toolpath planning and G-code generation

**Key Classes:**
- `RosetteGeometry` - Rosette dimensions (center, inner/outer radius, units)
- `CamParams` - CAM parameters (tool, stepover, stepdown, feeds, safe Z, cut depth)

**Key Functions:**
- `plan_rosette_toolpath(geom, params, segments=64)` → (moves[], stats{})
  - Calculates radial passes based on tool diameter + stepover
  - Calculates Z passes based on cut depth + stepdown
  - Generates concentric ring toolpaths as line segments
  - Returns moves + stats (rings, z_passes, length_mm, move_count)

- `postprocess_toolpath_grbl(moves, units, spindle_rpm)` → (gcode_text, stats{})
  - Converts neutral moves to GRBL G-code
  - Header: G21/G20, G90, G17, M3 S{rpm}, G4 P2
  - Body: G0/G1 commands with X/Y/Z/F
  - Footer: M5, G0 Z10, M30
  - Returns G-code + stats (lines, bytes)

---

### **2. art_jobs_store.py** ✅
**Path:** `services/api/app/services/art_jobs_store.py`  
**Size:** 85 lines  
**Purpose:** File-based job storage for Art Studio

**Storage:** `data/art_jobs.json` (JSON file, easy inspection)

**Key Classes:**
- `ArtJob` dataclass: id, job_type, created_at, post_preset, rings, z_passes, length_mm, gcode_lines, meta

**Key Functions:**
- `_load_jobs()` - Load from JSON file
- `_save_jobs(jobs)` - Save to JSON file
- `create_art_job(job_id, job_type, ...)` - Create and store new job
- `get_art_job(job_id)` - Retrieve job by ID

---

### **3. pipeline_ops_rosette.py** ✅
**Path:** `services/api/app/services/pipeline_ops_rosette.py`  
**Size:** 55 lines  
**Purpose:** Rosette CAM pipeline operation wrapper

**Key Classes:**
- `RosetteCamOpInput` - Input model (job_id, post_preset)
- `RosetteCamOpResult` - Result model (success, job_id, stats, message)

**Key Functions:**
- `run_rosette_cam_op(input)` - Execute Rosette CAM pipeline op
  - Fetches job from art_jobs_store
  - Returns success + job stats
  - Future: Re-run plan/post, attach analytics

---

### **4. risk_reports_store.py** ✅
**Path:** `services/api/app/services/risk_reports_store.py`  
**Size:** 95 lines  
**Purpose:** Risk report storage for timeline tracking

**Storage:** `data/cam_risk_reports.json`

**Key Classes:**
- `RiskReport` dataclass: id, created_at, lane, job_id, preset, source, steps[], summary{}, meta{}

**Key Functions:**
- `_load_reports()` - Load from JSON
- `_save_reports(reports)` - Save to JSON
- `create_risk_report(report_id, lane, ...)` - Create and store report
- `list_risk_reports(lane, preset, source, job_id, limit=200)` - Filter + list reports
  - Filters by multiple criteria
  - Sorts by newest first
  - Returns up to limit entries

---

### **5. cam_pipeline_router.py** ✅
**Path:** `services/api/app/routers/cam_pipeline_router.py`  
**Size:** 85 lines  
**Purpose:** Unified CAM pipeline API

**Prefix:** `/api/cam/pipeline`

**Key Models:**
- `RosetteCamPipelineOp` - Model for Rosette ops
- `PipelineOp` - Union type (expandable for AdaptivePocket, ReliefRoughing, etc.)
- `PipelineRunRequest` - Request (ops[], meta{})
- `PipelineStepResult` - Step result (step_index, op_type, result{})
- `PipelineRunResponse` - Response (steps[])

**Endpoints:**
- `POST /run` - Execute unified CAM pipeline
  - Accepts ops[] array
  - Executes each op sequentially
  - Returns steps[] with results
  - Currently supports: RosetteCam
  - Future: AdaptivePocket, ReliefRoughing

---

### **6. cam_risk_router.py** ✅
**Path:** `services/api/app/routers/cam_risk_router.py`  
**Size:** 110 lines  
**Purpose:** Risk report CRUD API

**Prefix:** `/api/cam/risk`

**Key Models:**
- `RiskReportCreateRequest` - Create request
- `RiskReportCreateResponse` - Create response
- `RiskReportSummary` - List item summary

**Endpoints:**
- `POST /reports` - Create risk report
  - Input: report_id, lane, job_id, preset, source, steps[], summary{}, meta{}
  - Stores to risk_reports_store
  - Returns: report_id, created_at, message

- `GET /reports` - List risk reports with filters
  - Query params: lane, preset, source, job_id, limit
  - Returns: List[RiskReportSummary]
  - Sorted newest first

---

### **7. art_studio_rosette_router.py (Extended)** ✅
**Path:** `services/api/app/routers/art_studio_rosette_router.py`  
**Size:** 584 lines (existing) + ~300 lines (added) = ~884 lines  
**Purpose:** Art Studio Rosette API with CAM integration

**Existing Endpoints:** (Preview, save, list, presets, compare, snapshots, CSV export)

**New CAM Endpoints Added:**

#### **POST /api/art/rosette/cam/plan_toolpath**
Generate toolpath moves for a rosette design.

**Request:**
```json
{
  "center_x": 0.0,
  "center_y": 0.0,
  "inner_radius": 25.0,
  "outer_radius": 50.0,
  "units": "mm",
  "tool_d": 6.0,
  "stepover": 0.45,
  "stepdown": 1.5,
  "feed_xy": 1200,
  "feed_z": 400,
  "safe_z": 5.0,
  "cut_depth": 3.0,
  "circle_segments": 64
}
```

**Response:**
```json
{
  "moves": [
    {"code": "G0", "z": 5.0},
    {"code": "G0", "x": 28.5, "y": 0.0},
    {"code": "G1", "z": -1.5, "f": 400},
    ...
  ],
  "stats": {
    "rings": 5,
    "z_passes": 2,
    "length_mm": 450.5,
    "move_count": 127
  }
}
```

#### **POST /api/art/rosette/cam/post_gcode**
Generate G-code from toolpath moves.

**Request:**
```json
{
  "moves": [...],
  "units": "mm",
  "spindle_rpm": 18000
}
```

**Response:**
```json
{
  "gcode": "G21\nG90\nG17\n...\nM30\n",
  "stats": {
    "lines": 127,
    "bytes": 3456
  }
}
```

#### **POST /api/art/rosette/jobs/cam_job**
Create a CAM job for pipeline handoff.

**Request:**
```json
{
  "job_id": "rosette_cam_001",
  "post_preset": "grbl",
  "rings": 5,
  "z_passes": 2,
  "length_mm": 450.5,
  "gcode_lines": 127,
  "meta": {
    "inner_radius": 25.0,
    "outer_radius": 50.0,
    "tool_d": 6.0
  }
}
```

**Response:**
```json
{
  "job_id": "rosette_cam_001",
  "message": "CAM job 'rosette_cam_001' created successfully"
}
```

#### **GET /api/art/rosette/jobs/{job_id}**
Retrieve a CAM job by ID.

**Response:**
```json
{
  "id": "rosette_cam_001",
  "job_type": "rosette_cam",
  "created_at": "2025-01-15T14:23:45Z",
  "post_preset": "grbl",
  "rings": 5,
  "z_passes": 2,
  "length_mm": 450.5,
  "gcode_lines": 127,
  "meta": {
    "inner_radius": 25.0,
    "outer_radius": 50.0,
    "tool_d": 6.0
  }
}
```

---

### **8. Test Files** ✅

#### **test_rosette_cam_bridge.py**
**Path:** `services/api/tests/test_rosette_cam_bridge.py`  
**Size:** 250 lines  
**Tests:**
- `test_rosette_plan_toolpath_smoke()` - Basic toolpath generation
- `test_rosette_post_gcode_smoke()` - G-code post-processing
- `test_rosette_toolpath_units_inch()` - Inch unit support
- `test_rosette_multiple_z_passes()` - Multi-pass Z strategy
- `test_rosette_toolpath_edge_cases()` - Small rosettes, large stepover

**Run with:** `pytest tests/test_rosette_cam_bridge.py -v`

#### **test_cam_pipeline_rosette_op.py**
**Path:** `services/api/tests/test_cam_pipeline_rosette_op.py`  
**Size:** 180 lines  
**Tests:**
- `test_rosette_cam_op_smoke()` - Basic pipeline op execution
- `test_rosette_cam_op_missing_job()` - Missing job error handling
- `test_rosette_cam_op_with_metadata()` - Metadata preservation
- `test_rosette_cam_op_multiple_jobs()` - Batch job execution

**Run with:** `pytest tests/test_cam_pipeline_rosette_op.py -v`

---

## 🔌 Integration Status

### **Router Registration** ✅
**File:** `services/api/app/main.py`

**Added:**
```python
# Art Studio Bundle 5 — Rosette CAM Integration (Pipeline + Risk Timeline)
try:
    from .routers.cam_pipeline_router import router as cam_pipeline_router
except Exception as e:
    print(f"Warning: Could not load cam_pipeline_router: {e}")
    cam_pipeline_router = None

try:
    from .routers.cam_risk_router import router as cam_risk_router
except Exception as e:
    print(f"Warning: Could not load cam_risk_router: {e}")
    cam_risk_router = None

# ... (later in file)

# Art Studio Bundle 5: CAM Pipeline and Risk Timeline
if cam_pipeline_router:
    app.include_router(cam_pipeline_router, prefix="/api/cam/pipeline", tags=["CAM", "Pipeline"])

if cam_risk_router:
    app.include_router(cam_risk_router, prefix="/api/cam/risk", tags=["CAM", "Risk"])
```

**Note:** `art_studio_rosette_router` was already registered at `/api/art/rosette`

---

## 🔄 Integration Flow

```
ArtStudioRosette.vue
  ↓ Design rosette (inner/outer radius, segments)
  ↓ POST /api/art/rosette/cam/plan_toolpath → Generate toolpath moves
  ↓ POST /api/art/rosette/cam/post_gcode → Generate G-code
  ↓ POST /api/art/rosette/jobs/cam_job → Create job + redirect
  ↓ Navigate → /lab/pipeline?lane=rosette&job_id=X&preset=grbl

PipelineLab.vue
  ↓ GET /api/art/rosette/jobs/{job_id} → Load job details
  ↓ Show banner (job stats: rings, z_passes, length, gcode lines)
  ↓ POST /api/cam/pipeline/run → Execute pipeline with [RosetteCam op]
  ↓ Show results (steps with stats)
  ↓ POST /api/cam/risk/reports → Save risk report
  ↓ Link to → /lab/risk

CamRiskTimeline.vue
  ↓ GET /api/cam/risk/reports?lane=rosette → List all risk reports
  ↓ Filter by preset/source/job_id
  ↓ Navigate back → PipelineLab or ArtStudio with context params
```

---

## 📊 Backend Statistics

**Files Created/Modified:**
- 6 new service/router files
- 1 extended router (art_studio_rosette_router.py)
- 2 test files
- 1 main.py integration
- **Total: 10 files touched**

**Lines of Code:**
- rosette_cam_bridge.py: 180 lines
- art_jobs_store.py: 85 lines
- pipeline_ops_rosette.py: 55 lines
- risk_reports_store.py: 95 lines
- cam_pipeline_router.py: 85 lines
- cam_risk_router.py: 110 lines
- art_studio_rosette_router.py extensions: ~300 lines
- test_rosette_cam_bridge.py: 250 lines
- test_cam_pipeline_rosette_op.py: 180 lines
- main.py changes: ~20 lines
- **Total: ~1,360 lines**

---

## ⏸️ Remaining Frontend Work (7 Files)

### **9. ArtStudioRosette.vue Extensions** (~600 lines)
**Path:** `packages/client/src/components/ArtStudioRosette.vue`

**Needs:**
- CAM state (camParams, toolpathMoves, toolpathStats, gcode, gcodeStats)
- CAM actions (handleGenerateToolpath, handleGenerateGcode, handleSendToPipeline)
- CAM UI panel:
  - Configuration form (inner/outer radius, tool params, feeds)
  - Generate toolpath button → calls POST /cam/plan_toolpath
  - Generate G-code button → calls POST /cam/post_gcode
  - Send to Pipeline button → calls POST /jobs/cam_job, redirects to PipelineLab
  - Toolpath stats display
  - G-code viewer

---

### **10. PipelineLab.vue Extensions** (~700 lines)
**Path:** `packages/client/src/components/PipelineLab.vue`

**Needs:**
- Rosette job state (pipelineRosetteJob, isLoadingRosetteJob, rosetteJobError)
- Pipeline run state (pipelineRunLoading, pipelineRunSteps)
- Risk report state (isSavingRosetteRiskReport, lastRosetteRiskReportId)
- Read query params: lane, job_id, preset
- Actions:
  - loadRosetteJobIfNeeded() → GET /api/art/rosette/jobs/{job_id}
  - handleRunRosettePipeline() → POST /api/cam/pipeline/run
  - handleSaveRosettePipelineRiskReport() → POST /api/cam/risk/reports
- UI:
  - Rosette job banner (job_id, preset, stats)
  - Run pipeline button
  - Pipeline results panel
  - Save risk report button

---

### **11. ArtStudioRosetteCompare.vue Extensions** (~800 lines)
**Path:** `packages/client/src/components/ArtStudioRosetteCompare.vue`

**Needs:**
- Preset filtering (filterPreset, applyPresetFilterFromQuery)
- Auto-scroll (tryScrollToFirstFilteredSnapshot)
- Highlighting (highlightedSnapshotId, snapshotRowRefs)
- Breadcrumb (returnSourceLabel, returnPresetLabel, isPresetPairsView)
- Back navigation (backTargetRoute)
- Read query params: preset, from, view
- Auto-behaviors:
  - Filter by preset on mount
  - Scroll to matching snapshot
  - Highlight for 4 seconds
  - Enable compare-by-preset if view=presetPairs
- UI:
  - Breadcrumb banner: "Returned from {source} (preset: {preset})"
  - Back button: "← Back to Pipeline/Adaptive"

---

### **12. CamRiskTimeline.vue (NEW)** (~500 lines)
**Path:** `packages/client/src/components/CamRiskTimeline.vue`

**Needs:**
- State (filters, reports[], loading, error)
- Filters (lane, preset, source, job_id, limit)
- Actions:
  - loadReports() → GET /api/cam/risk/reports with filters
  - goToPipeline(report) → Navigate to PipelineLab with context
  - goToArtStudioRosette(report) → Navigate to ArtStudio with context
- UI:
  - Filter controls (dropdowns for lane, preset, source)
  - Reports table (id, created_at, lane, job_id, preset, summary stats)
  - Refresh button
  - Navigation links per report

---

### **13. Router Integration**
**Path:** `packages/client/src/router/index.ts`

**Needs:**
- Add route: `/lab/risk` → CamRiskTimeline.vue
- Register with proper navigation links

---

## 🚀 Testing Backend

### **Start API Server**
```powershell
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

### **Run Tests**
```powershell
# Test CAM bridge
pytest tests/test_rosette_cam_bridge.py -v

# Test pipeline operation
pytest tests/test_cam_pipeline_rosette_op.py -v

# Test all
pytest tests/ -v -k rosette
```

### **Manual Smoke Test**
```powershell
# Plan toolpath
curl -X POST http://localhost:8000/api/art/rosette/cam/plan_toolpath `
  -H "Content-Type: application/json" `
  -d '{
    "inner_radius": 25.0,
    "outer_radius": 50.0,
    "units": "mm",
    "tool_d": 6.0,
    "stepover": 0.45,
    "stepdown": 1.5,
    "feed_xy": 1200,
    "feed_z": 400,
    "safe_z": 5.0,
    "cut_depth": 3.0
  }'

# Create job
curl -X POST http://localhost:8000/api/art/rosette/jobs/cam_job `
  -H "Content-Type: application/json" `
  -d '{
    "job_id": "test_001",
    "post_preset": "grbl",
    "rings": 5,
    "z_passes": 2,
    "length_mm": 450.5,
    "gcode_lines": 127,
    "meta": {}
  }'

# Get job
curl http://localhost:8000/api/art/rosette/jobs/test_001

# Run pipeline
curl -X POST http://localhost:8000/api/cam/pipeline/run `
  -H "Content-Type: application/json" `
  -d '{
    "ops": [
      {
        "op": "RosetteCam",
        "input": {
          "job_id": "test_001",
          "post_preset": "grbl"
        }
      }
    ],
    "meta": {}
  }'

# List risk reports
curl "http://localhost:8000/api/cam/risk/reports?lane=rosette&limit=10"
```

---

## 📚 Design Decisions

### **1. File-Based Storage**
**Reasoning:**
- Easy to inspect/debug (human-readable JSON)
- No database setup required (faster MVP)
- Sufficient for MVP/prototyping scale
- Clear migration path to SQLite/PostgreSQL later

**Files:**
- `data/art_jobs.json` - CAM job storage
- `data/cam_risk_reports.json` - Risk report storage

### **2. Unified Pipeline Pattern**
**Reasoning:**
- Easy to extend with new op types (AdaptivePocket, ReliefRoughing)
- Consistent API for all CAM operations
- Type-safe with Pydantic union types

**Future Ops:**
```python
class PipelineOp(BaseModel):
    __root__: Union[
        RosetteCamPipelineOp,
        AdaptivePocketPipelineOp,    # Future
        ReliefRoughingPipelineOp,    # Future
        HelicalRampingPipelineOp,    # Future
    ]
```

### **3. GRBL Post-Processor First**
**Reasoning:**
- Most common hobby CNC controller
- Simple, well-documented format
- Easy to swap with other post-processors later

**Future Posts:**
- Add Mach4, LinuxCNC, PathPilot by adding more postprocess functions
- Or integrate with existing multi-post system in geometry_router.py

---

## ✅ Next Steps

### **Immediate: Frontend Implementation**
1. Extend ArtStudioRosette.vue with CAM panel (~600 lines)
2. Extend PipelineLab.vue with Rosette job loading (~700 lines)
3. Extend ArtStudioRosetteCompare.vue with preset filtering (~800 lines)
4. Create CamRiskTimeline.vue dashboard (~500 lines)
5. Add router integration for /lab/risk route

**Estimated Time:** 3-4 hours

### **Testing: End-to-End Workflow**
1. Design rosette in Art Studio
2. Generate toolpath + G-code
3. Send to PipelineLab
4. Run pipeline operation
5. Save risk report
6. View in timeline dashboard
7. Navigate back with context preservation

---

## 📖 Documentation

**Related Docs:**
- [Art Studio Bundle 5 User's Document](./Rosette_Compare_preset_aware.txt) - Original specification
- [ADAPTIVE_POCKETING_MODULE_L.md](./ADAPTIVE_POCKETING_MODULE_L.md) - Similar CAM pipeline pattern
- [Multi-Post Export System](./PATCH_K_EXPORT_COMPLETE.md) - Post-processor integration examples

---

**Status:** ✅ Backend Complete (8/8 files) | ⏸️ Frontend Pending (7 files)  
**Overall Progress:** 53% (8/15 files)  
**Next:** Implement frontend Vue component extensions
