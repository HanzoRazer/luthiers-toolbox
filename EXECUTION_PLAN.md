# Luthier's Tool Box – Execution Plan
**Date:** November 27, 2025  
**Status:** Active Development  
**Target:** Complete integration of 62+ code bundles from specification extraction

---

## 🎯 Executive Summary

**Objective:** Integrate extracted specifications (12,747 lines) into production-ready CAM/CNC system with Art Studio enhancements, SpeTool vendor integration, comprehensive saw blade safety system, and Live Learn telemetry.

**Timeline:** 4-6 weeks (phased rollout)  
**Risk Level:** Medium (most core modules already tested)  
**Dependencies:** shapely>=2.0.0, pyclipper==1.3.0.post5, pdfplumber>=0.11.0

---

## 📊 Current State Assessment

### ✅ **Production-Ready (70% Complete)**
- Art Studio Phase 30.5 & 30.6 (5 components)
- SpeTool integration CP-S44→S49 (vendor data + learner)
- Saw blade registry CP-S50→S55 (catalog + UI)
- Basic geometry engine CP-S56 (5 modules)
- Live Learn telemetry foundation CP-S59

### 🔄 **In Progress (20% - Needs Integration)**
- Advanced offset engine CP-S56.5 (70% complete)
- G-code generator CP-S57 (80% complete)
- G-code preview panel CP-S58 (75% complete)
- Live Learn ingestor CP-S60 (85% complete)
- Dashboard + Risk Actions CP-S61/S62 (90% complete)

### ⚠️ **Pending (10% - Wire-Up Only)**
- Router registrations in main.py
- Navigation menu updates
- Cross-module integration testing
- Production deployment configs

---

## 🗓️ Phase-by-Phase Execution Plan

---

## **PHASE 1: Foundation & Dependencies (Week 1)**
**Goal:** Ensure all backend dependencies and core infrastructure are in place

### Task 1.1: Dependency Installation ⚡ **Priority: CRITICAL**
**Time:** 30 minutes  
**Risk:** Low

```powershell
# Backend dependencies
cd services/api
.\.venv\Scripts\Activate.ps1
pip install shapely>=2.0.0 pyclipper==1.3.0.post5 pdfplumber>=0.11.0 numpy>=1.24.0
pip freeze > requirements.txt

# Verify installations
python -c "import shapely; print(f'shapely {shapely.__version__}')"
python -c "import pyclipper; print(f'pyclipper {pyclipper.__version__}')"
python -c "import pdfplumber; print(f'pdfplumber {pdfplumber.__version__}')"
```

**Acceptance Criteria:**
- [ ] All imports succeed without errors
- [ ] requirements.txt updated
- [ ] No version conflicts in pip check

---

### Task 1.2: Database Schema Validation ⚡ **Priority: HIGH**
**Time:** 1 hour  
**Risk:** Medium

**Files to Create/Verify:**
- [ ] `services/api/app/data/cam_core/saw_runs.json` (JobLog storage)
- [ ] `services/api/app/data/cam_core/saw_telemetry.json` (Telemetry storage)
- [ ] `services/api/app/data/cam_core/saw_blades/*.json` (Blade catalogs)

**SQL Migrations (if using database):**
```sql
-- Already defined in specs:
CREATE TABLE job_run_telemetry (...)
CREATE TABLE spetool_preview_transitions (...)
CREATE TABLE spetool_lane_scale_audit (...)
```

**Acceptance Criteria:**
- [ ] All JSON storage paths exist
- [ ] Database tables created (if applicable)
- [ ] Sample data loads successfully

---

### Task 1.3: Core Module Structure Verification 🔍 **Priority: HIGH**
**Time:** 2 hours  
**Risk:** Low

**Directory Structure to Verify:**
```
services/api/app/
├── cam_core/
│   ├── geometry/
│   │   ├── geometry_models.py          ✅ (CP-S56)
│   │   ├── polyline_ops.py             ✅ (CP-S56)
│   │   ├── offset_curve.py             ✅ (CP-S56)
│   │   ├── radius_analysis.py          ✅ (CP-S56)
│   │   ├── contour_engine.py           ✅ (CP-S56)
│   │   └── advanced_offset.py          🔄 (CP-S56.5 - NEEDS COMPLETION)
│   ├── gcode/
│   │   ├── gcode_models.py             🔄 (CP-S57 - CREATE)
│   │   └── saw_gcode_generator.py      🔄 (CP-S57 - CREATE)
│   ├── tools/
│   │   ├── vendor_registry/
│   │   │   ├── spe_tool_spiral.json    ✅ (CP-S44)
│   │   │   ├── spetool_machine_scaling.json ✅ (CP-S45)
│   │   │   └── saw_blades/*.json       ✅ (CP-S50)
│   │   └── vendor_import/
│   │       ├── spe_tool_importer.py    ✅ (CP-S44)
│   │       └── tenryu_catalog_importer.py ✅ (CP-S51)
├── cnc_production/
│   ├── joblog/
│   │   ├── saw_joblog_models.py        🔄 (CP-S59 - CREATE)
│   │   └── saw_joblog_store.py         🔄 (CP-S59 - CREATE)
│   ├── feeds_speeds/core/
│   │   └── live_learn_telemetry.py     🔄 (CP-S60 - CREATE)
│   └── learn/
│       ├── risk_buckets.py             🔄 (CP-S61 - CREATE)
│       └── saw_live_learn_dashboard.py 🔄 (CP-S61 - CREATE)
└── routers/
    ├── saw_geometry_router.py          ✅ (CP-S56)
    ├── saw_gcode_router.py             🔄 (CP-S57 - CREATE)
    ├── saw_joblog_router.py            🔄 (CP-S59 - CREATE)
    ├── live_learn_telemetry_router.py  🔄 (CP-S60 - CREATE)
    └── saw_live_learn_dashboard_router.py 🔄 (CP-S61 - CREATE)
```

**Action Items:**
- [ ] Create missing directories
- [ ] Verify existing modules load correctly
- [ ] Run `pytest services/api/tests/` (if tests exist)

---

## **PHASE 2: Complete Backend Modules (Week 1-2)**
**Goal:** Finish all partially-complete backend implementations

### Task 2.1: Complete CP-S56.5 (Advanced Offset Engine) ⚡ **Priority: CRITICAL**
**Time:** 4 hours  
**Risk:** Medium (shapely integration)

**Implementation Steps:**
1. ✅ Add shapely to requirements (done in 1.1)
2. ✅ Extend geometry_models.py with join_style params (already extracted)
3. 🔄 **Complete advanced_offset.py implementation:**
   ```python
   # File: services/api/app/cam_core/geometry/advanced_offset.py
   # Status: 70% complete - need to finish:
   # - offset_polyline_advanced() function body
   # - _extract_exterior_coords() refinement
   # - Error handling for degenerate geometries
   ```
4. 🔄 **Update contour_engine.py to use advanced offsets:**
   ```python
   # Add conditional logic:
   if req.use_advanced_offset and HAVE_SHAPELY:
       offset_in_pts = offset_polyline_advanced(...)
   else:
       offset_in_pts = offset_polyline(...)  # fallback
   ```
5. ⚠️ **Frontend: Add UI controls in SawContourPanel.vue:**
   ```vue
   <select v-model="joinStyle">
     <option value="miter">Miter</option>
     <option value="round">Round</option>
     <option value="bevel">Bevel</option>
   </select>
   ```

**Testing:**
```powershell
cd services/api
pytest tests/cam_core/geometry/test_advanced_offset.py -v
```

**Acceptance Criteria:**
- [ ] shapely.buffer() integration works
- [ ] Join styles (miter/round/bevel) produce different geometries
- [ ] Fallback to simple offset when shapely unavailable
- [ ] No self-intersections in output
- [ ] Frontend controls wire to API correctly

---

### Task 2.2: Create CP-S57 (Saw G-Code Generator) ⚡ **Priority: HIGH**
**Time:** 3 hours  
**Risk:** Low (well-defined spec)

**Files to Create:**
1. `services/api/app/cam_core/gcode/gcode_models.py`
   - SawToolpath, DepthPass, SawGCodeRequest, SawGCodeResult
2. `services/api/app/cam_core/gcode/saw_gcode_generator.py`
   - plan_depth_passes(), emit_header(), emit_footer()
   - emit_toolpath_at_depth(), generate_saw_gcode()
3. `services/api/app/routers/saw_gcode_router.py`
   - POST /saw_gcode/generate endpoint

**Testing:**
```powershell
# Test slice operation
curl -X POST http://localhost:8000/saw_gcode/generate `
  -H "Content-Type: application/json" `
  -d '{"op_type":"slice","toolpaths":[{"points":[[0,0],[100,0]],"is_closed":false}],"total_depth_mm":3.0,"doc_per_pass_mm":1.0,"feed_ipm":60,"plunge_ipm":20}'
```

**Acceptance Criteria:**
- [ ] Multi-pass DOC planning works correctly
- [ ] G-code has proper header/footer
- [ ] Feed conversion (IPM → mm/min) accurate
- [ ] Safe Z retracts between passes
- [ ] Works for slice/batch/contour ops

---

### Task 2.3: Create CP-S63 (Universal Saw Blade PDF OCR) ⚡ **Priority: HIGH**
**Time:** 3 hours  
**Risk:** Medium (PDF parsing variability)

**Why This Matters:**
The 9 vendor PDFs (SpeTool router bits, Kanefusa saw blades) contain ~500+ blade specifications. CP-S63 automates extraction so you don't manually enter data for hours.

**Files to Create:**
1. `services/api/app/cam_core/saw_lab/importers/pdf_saw_blade_importer.py`
   - `PdfBladeRow` model (raw extracted row)
   - `SawBladeSpec` model (normalized blade spec)
   - `extract_blade_rows_from_pdf()` - pdfplumber table extraction
   - `normalize_pdf_row()` - header mapping (D → diameter, B → kerf, etc.)
   - `upsert_into_registry()` - integration with CP-S50 registry
   - CLI entrypoint with `--vendor` and `--no-registry` flags

2. `services/api/scripts/import_saw_blades_from_pdf.py` (optional helper)

3. `docs/CAM_Core/CP-S63_SawBlade_PDF_OCR.md` (usage guide)

**Header Mapping Logic:**
```python
# Common synonyms across vendors:
"D", "dia", "diameter" → diameter_mm
"B", "kerf", "width" → kerf_mm
"B1", "plate", "body" → plate_thickness_mm
"d2", "bore", "hole" → bore_mm
"Z", "teeth" → teeth
"hook" → hook_angle_deg
"top bevel" → top_bevel_angle_deg
"clearance" → clearance_angle_deg
"application", "for" → application
"material" → material_family
```

**Usage Examples:**
```powershell
# Import Tenryu catalog (full)
cd services/api
python -m app.cam_core.saw_lab.importers.pdf_saw_blade_importer `
  data/vendor_pdfs/TENRYU_Catalogue_Full_021224.pdf `
  --vendor Tenryu

# Import Kanefusa specifications
python -m app.cam_core.saw_lab.importers.pdf_saw_blade_importer `
  data/vendor_pdfs/Kanefusa_Saw_Blade_Specifications.pdf `
  --vendor Kanefusa

# Import SpeTool spiral bits
python -m app.cam_core.saw_lab.importers.pdf_saw_blade_importer `
  data/vendor_pdfs/SpeTool_Carbide_Spiral_Router_Bit.pdf `
  --vendor SpeTool

# Dry-run (JSON output only, no registry upsert)
python -m app.cam_core.saw_lab.importers.pdf_saw_blade_importer `
  data/vendor_pdfs/Kanefusa.pdf `
  --vendor Kanefusa `
  --no-registry > kanefusa_blades.json
```

**Testing:**
```powershell
# Test with each of the 9 PDFs
$pdfs = @(
  "SpeTool_Tray_Core_Box_Router_Bit.pdf",
  "SpeTool_Spoilboard_Surfacing_Bit.pdf",
  "SpeTool_2D_3D_Tapered_Router_Bit.pdf",
  "SpeTool_V_Groove_Signmaking_Bit.pdf",
  "SpeTool_Carbide_Spiral_Router_Bit.pdf",
  "SpeTool_Spiral_Bit_General.pdf",
  "Kanefusa_Saw_Blade_Specifications.pdf",
  "Circular_Saw_Blade_Specifications.pdf",
  "TENRYU_Catalogue_Full_021224.pdf"
)

foreach ($pdf in $pdfs) {
  Write-Host "Testing $pdf..." -ForegroundColor Cyan
  $vendor = if ($pdf -like "SpeTool*") { "SpeTool" } 
            elseif ($pdf -like "Kanefusa*") { "Kanefusa" }
            elseif ($pdf -like "TENRYU*") { "Tenryu" }
            else { "Generic" }
  
  python -m app.cam_core.saw_lab.importers.pdf_saw_blade_importer `
    "data/vendor_pdfs/$pdf" `
    --vendor $vendor `
    --no-registry | Out-File "test_output_$vendor.json"
  
  $count = (Get-Content "test_output_$vendor.json" | ConvertFrom-Json).Count
  Write-Host "✓ Extracted $count blades from $pdf" -ForegroundColor Green
}
```

**Acceptance Criteria:**
- [ ] pdfplumber extracts tables from all 9 PDFs without crashing
- [ ] Header mapping correctly identifies diameter, kerf, bore, teeth fields
- [ ] Numeric parsing handles units (mm, in, deg) and converts to floats
- [ ] At least 80% of blade rows successfully normalized
- [ ] Registry integration creates valid SawBladeSpec records
- [ ] CLI prints JSON output with --no-registry flag
- [ ] Duplicate blades (same vendor + model_code) are updated, not duplicated

**Integration with Existing Bundles:**
- Calls `upsert_blades_from_pdf()` from CP-S50 Saw Blade Registry
- Feeds `BladeBrowserPanel.vue` (CP-S52) with imported blades
- Enables validation in `SawSlicePanel`, `SawBatchPanel`, `SawContourPanel` (CP-S53/54/55)

---

### Task 2.4: Create CP-S59 (Saw JobLog & Telemetry) 🔍 **Priority: HIGH**
**Time:** 2 hours  
**Risk:** Low

**Files to Create:**
1. `services/api/app/cnc_production/joblog/saw_joblog_models.py`
2. `services/api/app/cnc_production/joblog/saw_joblog_store.py`
3. `services/api/app/routers/saw_joblog_router.py`

**Testing:**
```powershell
# Create run
$runData = @{
  op_type = "slice"
  machine_profile = "bcam_router_2030"
  material_family = "hardwood"
  gcode = "G21`nG90`nM30"
} | ConvertTo-Json

$run = Invoke-RestMethod -Method POST -Uri "http://localhost:8000/joblog/saw_runs" `
  -ContentType "application/json" -Body $runData

# Add telemetry
$telemData = @{
  saw_rpm = 18000
  spindle_load_pct = 65.3
} | ConvertTo-Json

Invoke-RestMethod -Method POST -Uri "http://localhost:8000/joblog/saw_runs/$($run.run_id)/telemetry" `
  -ContentType "application/json" -Body $telemData
```

**Acceptance Criteria:**
- [ ] Runs saved to saw_runs.json
- [ ] Telemetry samples saved to saw_telemetry.json
- [ ] GET endpoints retrieve data correctly
- [ ] run_id links runs to telemetry

---

### Task 2.5: Create CP-S60 (Live Learn Ingestor) 🔍 **Priority: MEDIUM**
**Time:** 3 hours  
**Risk:** Medium (depends on learned_overrides module)

**Files to Create:**
1. `services/api/app/cnc_production/feeds_speeds/core/live_learn_telemetry.py`
2. `services/api/app/routers/live_learn_telemetry_router.py`

**Integration Point:**
```python
# Hook into existing learned_overrides system (from CP-S11)
from cnc_production.feeds_speeds.core.learned_overrides import apply_lane_scale

# If doesn't exist yet, create stub:
def apply_lane_scale(tool_id, material, mode, machine_profile, lane_scale, source, meta):
    # TODO: Wire to actual lane storage system
    pass
```

**Testing:**
```powershell
# Test telemetry ingestion with suggestion
$ingestData = @{
  run_id = "<run_id_from_task_2.3>"
  tool_id = "spe_upcut_0.25"
  material = "hardwood"
  mode = "roughing"
  machine_profile = "bcam_router_2030"
  current_lane_scale = 1.0
  apply = $false
} | ConvertTo-Json

Invoke-RestMethod -Method POST -Uri "http://localhost:8000/live_learn/saw/ingest" `
  -ContentType "application/json" -Body $ingestData
```

**Acceptance Criteria:**
- [ ] Metrics computed from telemetry
- [ ] Risk score calculated (0-1)
- [ ] Scale delta suggested based on load thresholds
- [ ] apply=true writes to lane store
- [ ] apply=false returns suggestion only

---

### Task 2.6: Create CP-S61 & CP-S62 (Dashboard + Risk Actions) 🔍 **Priority: MEDIUM**
**Time:** 4 hours  
**Risk:** Low

**Files to Create:**
1. `services/api/app/cnc_production/learn/risk_buckets.py`
2. `services/api/app/cnc_production/learn/saw_live_learn_dashboard.py`
3. `services/api/app/routers/saw_live_learn_dashboard_router.py`

**Testing:**
```powershell
# Fetch dashboard summary
Invoke-RestMethod -Uri "http://localhost:8000/live_learn/saw/runs_summary?limit=20"
```

**Acceptance Criteria:**
- [ ] Risk buckets (Green/Yellow/Orange/Red/Unknown) classify runs
- [ ] Dashboard aggregates runs with telemetry
- [ ] Lane scale history retrieved per run
- [ ] Risk actions compute suggestions for Orange/Red runs

---

## **PHASE 3: Frontend Integration (Week 2-3)**
**Goal:** Wire all Vue components and create user-facing panels

### Task 3.1: Complete CP-S58 (G-Code Preview Panel) 🎨 **Priority: HIGH**
**Time:** 4 hours  
**Risk:** Low

**File to Create:**
- `packages/client/src/cnc_production/SawGcodePreviewPanel.vue`

**Integration Points:**
```typescript
// Embed in SawSlicePanel.vue, SawBatchPanel.vue, SawContourPanel.vue
<SawGcodePreviewPanel
  v-if="gcodeResult"
  :op-type="'contour'"
  :preview-layers="previewLayers"
  :gcode="gcodeResult.gcode"
  :depth-passes="gcodeResult.depth_passes"
  @joblog-sent="onJoblogSent"
/>
```

**Acceptance Criteria:**
- [ ] SVG overlay renders toolpaths
- [ ] G-code text viewer displays formatted output
- [ ] Download .nc button works
- [ ] Send to JobLog creates run record

---

### Task 3.2: Create Dashboard UI (CP-S61/S62) 🎨 **Priority: MEDIUM**
**Time:** 5 hours  
**Risk:** Medium

**File to Create:**
- `packages/client/src/cnc_production/SawLiveLearnDashboard.vue`

**API Helpers to Create:**
- `packages/client/src/cam_core/api/liveLearnSawDashboardApi.ts`
- `packages/client/src/cam_core/api/liveLearnTelemetryApi.ts`

**Acceptance Criteria:**
- [ ] Recent runs table displays with risk chips
- [ ] Run detail panel shows telemetry summary
- [ ] Lane scale history table populated
- [ ] Risk Actions panel computes suggestions
- [ ] Apply button triggers lane tweak with confirmation

---

### Task 3.3: Add PDF Import UI to Blade Browser (CP-S63 Frontend) 🎨 **Priority: MEDIUM**
**Time:** 2 hours  
**Risk:** Low

**File to Modify:**
- `packages/client/src/cam_core/BladeBrowserPanel.vue`

**New Features to Add:**
1. **"Import PDF" button** in blade list toolbar
2. **File upload dialog** (accepts .pdf files)
3. **Vendor selection dropdown** (Tenryu, Kanefusa, SpeTool, Other)
4. **Import progress indicator** (processing PDF...)
5. **Results summary modal**: "✓ 23 blades imported, 2 skipped (invalid data)"

**API Endpoint to Create:**
```python
# services/api/app/routers/saw_blade_import_router.py
@router.post("/saw_blades/import_pdf")
async def import_pdf_blades(
    file: UploadFile = File(...),
    vendor: str = Form(...),
):
    # Save uploaded PDF temporarily
    # Call pdf_saw_blade_importer.import_saw_blades_from_pdf()
    # Return { imported: int, skipped: int, blades: [...] }
```

**Frontend Implementation:**
```vue
<template>
  <div class="blade-browser">
    <!-- Existing blade list -->
    <div class="toolbar">
      <button @click="showImportDialog = true">
        📄 Import PDF
      </button>
    </div>
    
    <!-- Import dialog -->
    <dialog v-if="showImportDialog">
      <h3>Import Saw Blades from PDF</h3>
      <input type="file" accept=".pdf" @change="onFileSelect" />
      <select v-model="selectedVendor">
        <option value="Tenryu">Tenryu</option>
        <option value="Kanefusa">Kanefusa</option>
        <option value="SpeTool">SpeTool</option>
        <option value="Other">Other</option>
      </select>
      <button @click="uploadAndImport" :disabled="!pdfFile || importing">
        {{ importing ? 'Importing...' : 'Import' }}
      </button>
    </dialog>
    
    <!-- Results modal -->
    <dialog v-if="importResults">
      <h3>Import Complete</h3>
      <p>✓ {{ importResults.imported }} blades imported</p>
      <p v-if="importResults.skipped > 0">
        ⚠️ {{ importResults.skipped }} rows skipped (invalid data)
      </p>
      <button @click="closeResults">Close</button>
    </dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import axios from 'axios'

const showImportDialog = ref(false)
const pdfFile = ref<File | null>(null)
const selectedVendor = ref('Tenryu')
const importing = ref(false)
const importResults = ref<{ imported: number; skipped: number } | null>(null)

async function uploadAndImport() {
  if (!pdfFile.value) return
  importing.value = true
  
  const formData = new FormData()
  formData.append('file', pdfFile.value)
  formData.append('vendor', selectedVendor.value)
  
  try {
    const { data } = await axios.post('/saw_blades/import_pdf', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    importResults.value = data
    showImportDialog.value = false
    // Refresh blade list
    await loadBlades()
  } catch (err) {
    console.error('Import failed:', err)
  } finally {
    importing.value = false
  }
}
</script>
```

**Acceptance Criteria:**
- [ ] "Import PDF" button appears in blade browser toolbar
- [ ] File upload dialog accepts only .pdf files
- [ ] Vendor dropdown pre-populated with known vendors
- [ ] Progress indicator shows during processing
- [ ] Results modal displays imported/skipped counts
- [ ] Blade list refreshes automatically after import
- [ ] Error handling for malformed PDFs (shows user-friendly message)

---

### Task 3.4: Update Navigation & Routing 🧭 **Priority: HIGH**
**Time:** 2 hours  
**Risk:** Low

**Files to Modify:**
1. `packages/client/src/router/index.ts`
   ```typescript
   // Add routes for:
   { path: '/saw/live-learn', component: SawLiveLearnDashboard },
   { path: '/saw/slice', component: SawSlicePanel },
   { path: '/saw/batch', component: SawBatchPanel },
   { path: '/saw/contour', component: SawContourPanel },
   ```

2. Navigation component (main menu)
   ```vue
   <!-- Add Saw Lab section -->
   <nav-item to="/saw/slice" label="Saw Lab" icon="🪚" />
   ```

**Acceptance Criteria:**
- [ ] All Saw Lab routes accessible
- [ ] Breadcrumbs show correct path
- [ ] Navigation tooltips updated

---

## **PHASE 4: Backend Router Registration (Week 3)**
**Goal:** Wire all API endpoints into main FastAPI app

### Task 4.1: Register All Routers ⚡ **Priority: CRITICAL**
**Time:** 1 hour  
**Risk:** Low

**File to Modify:**
- `services/api/app/main.py`

**Routers to Register:**
```python
# Existing (verify):
from .routers.saw_geometry_router import router as saw_geometry_router
app.include_router(saw_geometry_router, prefix="/saw_geometry", tags=["saw_geometry"])

# New routers to add:
from .routers.saw_gcode_router import router as saw_gcode_router
app.include_router(saw_gcode_router, prefix="/saw_gcode", tags=["saw_gcode"])

from .routers.saw_joblog_router import router as saw_joblog_router
app.include_router(saw_joblog_router)  # prefix="/joblog" in router

from .routers.live_learn_telemetry_router import router as live_learn_telemetry_router
app.include_router(live_learn_telemetry_router)  # prefix="/live_learn/saw"

from .routers.saw_live_learn_dashboard_router import router as saw_live_learn_dashboard_router
app.include_router(saw_live_learn_dashboard_router)  # prefix="/live_learn/saw"

# Art Studio routers (if not already registered):
from .routers.art_import_validator_router import router as art_import_validator_router
app.include_router(art_import_validator_router, prefix="/api/art", tags=["art_import"])
```

**Testing:**
```powershell
# Start API
cd services/api
uvicorn app.main:app --reload --port 8000

# Check OpenAPI docs
Start-Process "http://localhost:8000/docs"

# Verify all endpoints show up:
# - /saw_geometry/contour
# - /saw_gcode/generate
# - /joblog/saw_runs
# - /live_learn/saw/ingest
# - /live_learn/saw/runs_summary
```

**Acceptance Criteria:**
- [ ] All routers import without errors
- [ ] OpenAPI docs show all endpoints
- [ ] No route conflicts (400/404 errors)
- [ ] CORS configured if needed

---

## **PHASE 5: Integration Testing (Week 3-4)**
**Goal:** End-to-end validation of full workflow

### Task 5.1: Saw Lab Full Workflow Test 🧪 **Priority: CRITICAL**
**Time:** 3 hours  
**Risk:** High

**Test Scenario: Contour Operation with Telemetry**
```powershell
# 1. Select blade (CP-S52)
GET /cam_core/blades
# Pick blade_id

# 2. Generate contour geometry (CP-S56 + CP-S56.5)
POST /saw_geometry/contour
# Body: { polyline, kerf_mm, blade_diameter_mm, use_advanced_offset: true }

# 3. Generate G-code (CP-S57)
POST /saw_gcode/generate
# Body: { op_type: "contour", toolpaths, depth, feeds }

# 4. Log run (CP-S59)
POST /joblog/saw_runs
# Body: { op_type, machine, material, blade_id, gcode }
# Save run_id

# 5. Add telemetry sample (CP-S59)
POST /joblog/saw_runs/{run_id}/telemetry
# Body: { saw_rpm, spindle_load_pct, vibration_rms }

# 6. Ingest telemetry (CP-S60)
POST /live_learn/saw/ingest
# Body: { run_id, tool_id, material, mode, machine_profile, apply: false }

# 7. View dashboard (CP-S61)
GET /live_learn/saw/runs_summary
# Verify run shows up with risk bucket

# 8. Apply lane tweak if needed (CP-S62)
POST /live_learn/saw/ingest
# Body: { ..., apply: true }
```

**Acceptance Criteria:**
- [ ] All 8 steps complete without errors
- [ ] G-code is valid (can load in CAM software)
- [ ] Telemetry links to run correctly
- [ ] Risk bucket calculated accurately
- [ ] Lane scale applied to correct lane context

---

### Task 5.2: Art Studio Workflow Test 🧪 **Priority: HIGH**
**Time:** 2 hours  
**Risk:** Medium

**Test Scenario: Preset Comparison & Promotion**
```powershell
# 1. View preset aggregate (Phase 30.5)
GET /api/art/presets_aggregate

# 2. Compare two presets
Navigate to /art/preset-compare?presetA=<id>&presetB=<id>

# 3. View Rosette compare with filtering
Navigate to /art/rosette-compare?presetA=<id>&presetB=<id>

# 4. Promote winning preset
POST /api/art/presets/promote
# Body: { parent_id, child_id, lane, rationale, recommended: true }

# 5. View tuning tree with recommended-first sorting
GET /api/art/presets/tuning_tree?lane=<lane>

# 6. Export recommended presets
GET /api/art/presets/recommended_export?format=csv
```

**Acceptance Criteria:**
- [ ] All components load without errors
- [ ] Preset filtering works in history
- [ ] Promotion marks preset as recommended
- [ ] Tuning tree sorts correctly
- [ ] Export generates valid CSV/JSON

---

### Task 5.3: Graphics Validation Test 🧪 **Priority: MEDIUM**
**Time:** 1 hour  
**Risk:** Low

**Test Scenario: Import Validator (CP-S51)**
```powershell
# Test with various file types
$testFiles = @(
  "test_300dpi.png",      # Should pass
  "test_150dpi.jpg",      # Should fail (low DPI)
  "test_vector.svg",      # Should pass (vector)
  "test_blueprint.pdf"    # Should pass (PDF)
)

foreach ($file in $testFiles) {
  curl -X POST http://localhost:8000/api/art/import/validate `
    -F "file=@$file" `
    -o "result_$file.json"
}
```

**Acceptance Criteria:**
- [ ] DPI check works for rasters
- [ ] Vector files classified correctly
- [ ] Issues list populated with severity
- [ ] meets_standard flag accurate

---

## **PHASE 6: Production Deployment (Week 4)**
**Goal:** Deploy to production environment with monitoring

### Task 6.1: Create Deployment Configs 🚀 **Priority: HIGH**
**Time:** 3 hours  
**Risk:** Medium

**Files to Create/Update:**
1. `docker-compose.prod.yml`
   ```yaml
   services:
     api:
       environment:
         - ENV=production
         - LOG_LEVEL=info
     client:
       build:
         args:
           - VITE_API_URL=https://api.luthiers-toolbox.com
   ```

2. `.env.production`
   ```bash
   DATABASE_URL=postgresql://...
   REDIS_URL=redis://...
   SENTRY_DSN=https://...
   ```

3. `nginx.conf` (if using Nginx proxy)
   ```nginx
   location /api/ {
     proxy_pass http://api:8000/;
   }
   location /joblog/ {
     proxy_pass http://api:8000/joblog/;
   }
   ```

**Acceptance Criteria:**
- [ ] Environment variables configured
- [ ] API accessible via production URL
- [ ] HTTPS certificates valid
- [ ] CORS allows production origins

---

### Task 6.2: Set Up Monitoring & Logging 📊 **Priority: HIGH**
**Time:** 2 hours  
**Risk:** Low

**Tools to Configure:**
1. **API Logging**
   ```python
   # In main.py
   import logging
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
       handlers=[
           logging.FileHandler('api.log'),
           logging.StreamHandler()
       ]
   )
   ```

2. **Error Tracking (Sentry - optional)**
   ```python
   import sentry_sdk
   sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))
   ```

3. **Performance Monitoring**
   ```python
   # Add middleware for request timing
   from time import time
   @app.middleware("http")
   async def add_process_time_header(request, call_next):
       start_time = time()
       response = await call_next(request)
       process_time = time() - start_time
       response.headers["X-Process-Time"] = str(process_time)
       return response
   ```

**Acceptance Criteria:**
- [ ] API logs to file and console
- [ ] Error tracking captures exceptions
- [ ] Request timing headers present

---

### Task 6.3: Create Backup & Recovery Plan 💾 **Priority: MEDIUM**
**Time:** 2 hours  
**Risk:** Low

**Backup Strategy:**
```powershell
# Daily backup script
$backupDir = "C:\Backups\LuthiersToolbox\$(Get-Date -Format 'yyyy-MM-dd')"
New-Item -ItemType Directory -Path $backupDir -Force

# Backup JSON data stores
Copy-Item "services\api\app\data\cam_core\*.json" $backupDir -Recurse

# Backup database (if using PostgreSQL)
pg_dump -U postgres luthiers_toolbox > "$backupDir\database.sql"

# Backup uploaded files
Copy-Item "services\api\uploads\*" "$backupDir\uploads" -Recurse

# Create archive
Compress-Archive -Path $backupDir\* -DestinationPath "$backupDir.zip"
```

**Acceptance Criteria:**
- [ ] Automated daily backups configured
- [ ] Backup retention policy defined (30 days)
- [ ] Recovery procedure documented

---

## **PHASE 7: Documentation & Training (Week 4-5)**
**Goal:** User-facing documentation and internal guides

### Task 7.1: Create User Guides 📚 **Priority: MEDIUM**
**Time:** 4 hours  
**Risk:** Low

**Documents to Create:**
1. **Saw Lab User Guide**
   - How to select blades
   - How to generate contours
   - How to export G-code
   - Interpreting risk buckets

2. **Live Learn Dashboard Guide**
   - Understanding telemetry metrics
   - When to apply lane tweaks
   - Risk action workflow

3. **Art Studio Quickstart**
   - Preset comparison workflow
   - Promotion best practices
   - Graphics import standards

**Acceptance Criteria:**
- [ ] Each guide has screenshots
- [ ] Step-by-step instructions clear
- [ ] Common errors documented

---

### Task 7.2: Create API Documentation 📖 **Priority: MEDIUM**
**Time:** 3 hours  
**Risk:** Low

**Files to Create:**
1. `docs/api/SAW_LAB_API.md`
   - All Saw Lab endpoints
   - Request/response examples
   - Error codes

2. `docs/api/LIVE_LEARN_API.md`
   - Telemetry endpoints
   - Ingest workflow
   - Risk bucket mapping

3. Update OpenAPI schema descriptions
   ```python
   @router.post("/ingest", response_model=TelemetryIngestResponse,
                description="Ingest telemetry from a saw run and compute lane adjustments")
   ```

**Acceptance Criteria:**
- [ ] All endpoints documented
- [ ] Examples tested and valid
- [ ] OpenAPI schema complete

---

## **PHASE 8: Performance Optimization (Week 5-6)**
**Goal:** Optimize for production workloads

### Task 8.1: Backend Performance Tuning ⚡ **Priority: LOW**
**Time:** 3 hours  
**Risk:** Low

**Optimizations:**
1. **Add caching to expensive operations**
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=128)
   def get_blade_catalog():
       # Expensive blade loading
       pass
   ```

2. **Database query optimization**
   ```python
   # Add indexes on frequently queried fields
   CREATE INDEX idx_run_id ON job_run_telemetry(run_id);
   CREATE INDEX idx_machine_profile ON saw_runs(machine_profile);
   ```

3. **Async file I/O**
   ```python
   import aiofiles
   async def save_gcode(filename, content):
       async with aiofiles.open(filename, 'w') as f:
           await f.write(content)
   ```

**Acceptance Criteria:**
- [ ] Response times < 200ms for API calls
- [ ] No N+1 query issues
- [ ] File operations non-blocking

---

### Task 8.2: Frontend Performance Tuning 🎨 **Priority: LOW**
**Time:** 2 hours  
**Risk:** Low

**Optimizations:**
1. **Lazy load heavy components**
   ```typescript
   const SawLiveLearnDashboard = defineAsyncComponent(
     () => import('./components/SawLiveLearnDashboard.vue')
   )
   ```

2. **Virtualize long lists**
   ```vue
   <!-- Use vue-virtual-scroller for run history -->
   <RecycleScroller :items="runs" :item-size="50" />
   ```

3. **Debounce API calls**
   ```typescript
   import { debounce } from 'lodash-es'
   const searchBlades = debounce(async (query) => {
     // API call
   }, 300)
   ```

**Acceptance Criteria:**
- [ ] Initial load < 2 seconds
- [ ] Smooth scrolling on large datasets
- [ ] No memory leaks in long sessions

---

## 📋 **Acceptance Testing Checklist**

### **System-Wide Tests**
- [ ] All API endpoints return 200 or appropriate error codes
- [ ] CORS configured correctly (no CORS errors in browser)
- [ ] Authentication/authorization works (if implemented)
- [ ] Error messages user-friendly (no stack traces exposed)
- [ ] All forms validate input correctly
- [ ] File uploads handle large files (>10MB)
- [ ] Database connections pool correctly
- [ ] No memory leaks after 1 hour of operation

### **Saw Lab Integration Tests**
- [ ] Blade selection persists across sessions
- [ ] **PDF import extracts blades from all 9 vendor PDFs** 🆕
- [ ] **Imported blades appear in blade browser immediately** 🆕
- [ ] **Duplicate blades update existing records (no duplicates)** 🆕
- [ ] Contour geometry generates without self-intersections
- [ ] G-code validates in CAM software (Fusion 360 / VCarve)
- [ ] Telemetry links to correct run
- [ ] Risk buckets classify runs accurately
- [ ] Lane tweaks apply to correct lane context
- [ ] Multi-pass DOC generates correct Z-levels

### **Art Studio Integration Tests**
- [ ] Preset comparison shows correct deltas
- [ ] Rosette filtering works with preset IDs
- [ ] Promotion workflow creates recommended presets
- [ ] Tuning tree sorts recommended-first
- [ ] Export generates valid CSV/JSON files
- [ ] Graphics validator catches low-DPI files

### **Performance Tests**
- [ ] API handles 100 concurrent requests
- [ ] Frontend handles 1000+ list items
- [ ] G-code generation < 5 seconds for complex contours
- [ ] Dashboard loads in < 3 seconds

---

## 🚨 **Risk Mitigation**

### **High-Risk Areas**
1. **Shapely Integration (CP-S56.5)**
   - **Risk:** Shapely not installed or version incompatible
   - **Mitigation:** Fallback to simple offsets, clear error messages
   - **Rollback:** Disable use_advanced_offset flag

2. **Lane Scale Integration (CP-S60)**
   - **Risk:** Learned overrides module doesn't exist yet
   - **Mitigation:** Create stub functions, defer full integration
   - **Rollback:** Return suggestions without applying

3. **Production Deployment**
   - **Risk:** Environment differences cause runtime errors
   - **Mitigation:** Docker ensures consistency, staging environment
   - **Rollback:** Keep previous version running, blue-green deployment

### **Dependency Issues**
- **pyclipper:** Required for L.1 adaptive pocketing
  - Fallback: Use original adaptive_core.py (L.0)
- **pdfplumber:** Required for Tenryu PDF import
  - Fallback: Manual JSON entry for blade catalogs
- **shapely:** Required for advanced offsets
  - Fallback: Simple normal-based offsets

---

## 📊 **Progress Tracking**

### **Weekly Milestones**
- **Week 1 (Dec 2-6):** Foundation complete, backend 50% done
- **Week 2 (Dec 9-13):** Backend 100%, frontend 40% done
- **Week 3 (Dec 16-20):** Frontend 100%, integration testing 50%
- **Week 4 (Dec 23-27):** Testing complete, production deployment 80%
- **Week 5 (Dec 30-Jan 3):** Documentation complete, optimization 50%
- **Week 6 (Jan 6-10):** Final polish, production-ready ✅

### **Go/No-Go Criteria**
Before production deployment:
- [ ] All critical path tests passing (saw workflow, art studio workflow)
- [ ] Zero known high-severity bugs
- [ ] Documentation complete (user guides + API docs)
- [ ] Backups configured and tested
- [ ] Performance meets targets (< 200ms API, < 2s frontend)

---

## 🎯 **Success Metrics**

**Technical Metrics:**
- API uptime > 99.5%
- Response time p95 < 300ms
- Error rate < 0.1%
- Test coverage > 70%

**User Metrics:**
- Saw Lab workflow completion rate > 80%
- Art Studio preset promotions > 50/month
- Average session duration > 15 minutes
- User-reported bugs < 5/month

---

## 📞 **Escalation Plan**

**Blockers:**
- **Dependency issues:** Post in #dev-support, contact library maintainers
- **Integration failures:** Review API contracts, check version compatibility
- **Performance issues:** Profile with py-spy (backend) / Chrome DevTools (frontend)
- **Production outages:** Rollback to previous version, investigate offline

**Communication:**
- Daily standups (async): Post progress in #dev-updates
- Weekly demos: Show completed features to stakeholders
- Incident reports: Document any production issues within 24h

---

## ✅ **Definition of Done**

A phase is complete when:
1. All tasks marked as complete
2. Tests passing (unit + integration)
3. Code reviewed by 1+ developer
4. Documentation updated
5. Deployed to staging environment
6. Stakeholder sign-off received

---

**Next Steps:**
1. Review this execution plan with team
2. Assign tasks to developers
3. Set up project board (GitHub Projects / Jira)
4. Start Phase 1 (Dependencies) immediately

**Estimated Total Time:** 85-125 hours (2-3 developers, 4-6 weeks)  
**Target Completion:** January 10, 2026  
**Priority:** Complete CP-S56.5, CP-S57, **CP-S63**, CP-S58 first (critical path for Saw Lab)

---

## 🎯 **CP-S63 Impact Summary**

### **What CP-S63 Enables:**
✅ **Automates 500+ blade entries** from 9 vendor PDFs  
✅ **Eliminates hours of manual data entry**  
✅ **Vendor-agnostic** (works with any table-based PDF)  
✅ **Seamless registry integration** (auto-upserts to CP-S50)  
✅ **CLI + UI workflow** (power users + casual users)

### **Data Coverage from 9 PDFs:**
1. **SpeTool Router Bits** (~120 entries)
   - Core box, surfacing, tapered, V-groove, spiral bits
   - Chipload tables by material/diameter/direction
   
2. **Kanefusa Saw Blades** (~200 entries)
   - Full geometry specs (D, Kerf, Bore, Teeth, Hook angle)
   - Tooth shapes, clearance angles, plate features
   
3. **Tenryu Catalog** (~180 entries)
   - Comprehensive crosscut/rip blade lineup
   - Application-specific recommendations

**Total Extracted:** ~500 blade/bit specifications  
**Manual Entry Time Saved:** 20-30 hours  
**Ongoing Benefit:** New vendor PDFs ingest in minutes, not days
