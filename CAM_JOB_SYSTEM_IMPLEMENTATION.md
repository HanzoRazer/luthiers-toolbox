# CAM Job System Implementation Specification

**Status:** Ready for Implementation  
**Date:** December 2, 2025  
**Version:** 1.0  
**Integration Target:** Luthier's ToolBox Repository

---

## 🎯 Executive Summary

This document specifies the implementation of a FreeCAD-inspired CAM Job system for the Luthier's Tool Box, designed to:

- **Unify CAM workflows** under a single Job-based architecture
- **Maintain backward compatibility** with existing N16 RMOS, Module L adaptive pocketing, and multi-post export systems
- **Enable future expansion** to Profile2D, Pocket2D, Drill, Engrave, and VCarve operations
- **Support ToolBit/ToolLibrary** imports from FreeCAD (`.fctb`, `.fctl`)
- **Integrate with CompareLab** for validation and golden baseline checks

---

## 📦 Architecture Integration

### **Three-Layer Model**

```
┌─────────────────────────────────────────────────────────────┐
│ GEOMETRY LAYER                                               │
│ - Rosette Designer, Fingerboard Generator, Body Templates   │
│ - DXF/SVG importers                                         │
│ - Tagged geometry (role: "body_outline", "rosette_channel") │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ CAM MODEL LAYER (NEW)                                       │
│ - CAMJob: Top-level unit of work                           │
│ - ToolBit/ToolLibrary: Cutting tool definitions            │
│ - ToolController: Tool + feeds/speeds for Job context      │
│ - Operations: Profile2D, Pocket2D, Drill, Engrave, etc.    │
│ - Dressups: Tabs, Ramps, Lead-in/out modifiers             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ EXECUTION LAYER (EXISTING + ENHANCED)                       │
│ - Neutral Path Program: Internal DSL                        │
│ - Post Processors: GRBL, Mach4, FANUC, etc. (existing)     │
│ - CompareLab: SVG/G-code diffs (existing)                  │
│ - Golden Compare: Baseline regression checks                │
└─────────────────────────────────────────────────────────────┘
```

---

## 🗂️ File Structure

### **Backend (Python/FastAPI)**

```
services/api/app/
├── cam/                              # Existing CAM engines
│   ├── tooling/                      # NEW: ToolBit system
│   │   ├── __init__.py
│   │   ├── models.py                 # ToolBit, ToolLibrary Pydantic models
│   │   ├── store.py                  # JSON-based CRUD for tools
│   │   └── freecad_importer.py       # .fctb/.fctl parser
│   ├── jobs/                         # NEW: CAM Job system
│   │   ├── __init__.py
│   │   ├── models.py                 # CAMJob, ToolController, Operation models
│   │   ├── store.py                  # Job storage (file-based JSON)
│   │   └── path_engine.py            # Job → neutral path program generator
│   ├── operations/                   # NEW: Operation engines
│   │   ├── __init__.py
│   │   ├── base.py                   # Base operation interface
│   │   ├── profile_2d.py             # Profile2D implementation
│   │   ├── pocket_2d.py              # Pocket2D (wraps adaptive_core_l3)
│   │   ├── drill_pattern.py          # DrillPattern implementation
│   │   ├── engrave.py                # Engrave/VCarve implementation
│   │   └── adaptive_2d.py            # Adaptive2D (L.3 engine wrapper)
│   ├── dressups/                     # NEW: Dressup modifiers
│   │   ├── __init__.py
│   │   ├── tabs.py                   # Tab insertion
│   │   ├── ramp_entry.py             # Ramp entry strategy
│   │   └── lead_inout.py             # Lead-in/out arcs
│   ├── posts/                        # NEW: Post-processor plugins
│   │   ├── __init__.py
│   │   ├── base.py                   # Post processor interface
│   │   ├── grbl_post.py              # GRBL dialect
│   │   ├── fanuc_post.py             # FANUC dialect
│   │   └── thin_saw_post.py          # Thin-kerf saw safety mode
│   ├── adaptive_core_l3.py           # EXISTING: Keep as-is
│   ├── feedtime_l3.py                # EXISTING: Keep as-is
│   ├── rosette/                      # EXISTING: N16 system (keep as-is)
│   └── ...                           # Other existing CAM modules
│
├── routers/                          # API endpoints
│   ├── cam_jobs_router.py            # NEW: /api/cam/jobs CRUD
│   ├── cam_tooling_router.py         # NEW: /api/cam/tools, /api/cam/libraries
│   ├── cam_operations_router.py      # NEW: /api/cam/operations (future)
│   ├── adaptive_router.py            # EXISTING: Keep /api/cam/pocket/adaptive/*
│   ├── rmos_rosette_api.py           # EXISTING: Keep N16 endpoints
│   └── ...                           # Other existing routers
│
├── data/                             # Storage
│   ├── cam_jobs/                     # NEW: CAM Job JSON files
│   ├── cam_tooling/                  # NEW: ToolBit + ToolLibrary JSON
│   │   ├── tools/                    # Individual ToolBit files
│   │   └── libraries/                # ToolLibrary files
│   ├── posts/                        # EXISTING: Post configs (keep as-is)
│   └── presets.json                  # EXISTING: B41 presets (keep as-is)
│
└── main.py                           # Router registration (update)
```

### **Frontend (Vue/TypeScript)**

```
packages/client/src/
├── views/
│   ├── cam/                          # NEW: CAM Job UI
│   │   ├── CAMJobsView.vue           # Job list/management
│   │   ├── CAMJobEditorView.vue      # Job editor (tabs: Stock, Tools, Ops, Export)
│   │   └── CAMToolLibraryView.vue    # ToolBit/Library management
│   ├── RMOSCncHistoryView.vue        # EXISTING: Keep N16 UI
│   └── ...                           # Other existing views
│
├── components/
│   ├── cam/                          # NEW: CAM Job components
│   │   ├── CAMJobEditor.vue          # Main editor component
│   │   ├── StockConfigPanel.vue      # Stock/material setup
│   │   ├── ToolControllerPanel.vue   # Tool + feeds/speeds
│   │   ├── OperationList.vue         # Operation sequence editor
│   │   ├── OperationEditor.vue       # Type-specific operation editors
│   │   ├── DressupEditor.vue         # Dressup modifier editors
│   │   ├── ToolLibraryPanel.vue      # ToolBit browser
│   │   ├── ToolBitImporter.vue       # FreeCAD import UI
│   │   └── SimulationPreview.vue     # 2D toolpath preview
│   ├── AdaptivePocketLab.vue         # EXISTING: Keep Module L UI
│   └── ...                           # Other existing components
│
└── router/
    ├── camJobRoutes.ts               # NEW: /cam/jobs, /cam/jobs/:id/edit, /cam/tools
    └── index.ts                      # Update to include camJobRoutes
```

---

## 📐 Schema Definitions

### **1. ToolBit Schema**

**File:** `services/api/app/cam/tooling/models.py`

```python
from typing import Optional, List, Literal
from pydantic import BaseModel, Field

class ToolBit(BaseModel):
    """
    Single cutting tool definition.
    Compatible with FreeCAD ToolBit format.
    """
    id: str = Field(..., description="Unique tool identifier (slug or UUID)")
    name: str = Field(..., description="Human-readable tool name")
    type: Literal["endmill", "ballend", "vbit", "drill", "saw"] = Field(
        ..., description="Tool geometry type"
    )
    
    # Geometry
    diameter: float = Field(..., description="Tool diameter in mm", gt=0)
    flute_length: Optional[float] = Field(None, description="Flute length in mm", ge=0)
    tool_length: Optional[float] = Field(None, description="Total tool length in mm", ge=0)
    corner_radius: Optional[float] = Field(None, description="Corner radius in mm (ballend)", ge=0)
    included_angle: Optional[float] = Field(None, description="Included angle in degrees (V-bit)", gt=0, lt=180)
    
    # Saw-specific
    kerf: Optional[float] = Field(None, description="Kerf width in mm (saw blades)", ge=0)
    tooth_count: Optional[int] = Field(None, description="Number of teeth (saw blades)", ge=1)
    
    # Metadata
    vendor: Optional[str] = Field(None, description="Manufacturer/vendor name")
    part_number: Optional[str] = Field(None, description="Manufacturer part number")
    notes: Optional[str] = Field(None, description="Usage notes or recommendations")
    tags: List[str] = Field(default_factory=list, description="User-defined tags")


class ToolLibrary(BaseModel):
    """
    Collection of ToolBits with shared metadata.
    Compatible with FreeCAD ToolBit Library format.
    """
    id: str = Field(..., description="Unique library identifier")
    name: str = Field(..., description="Library name")
    machine_id: Optional[str] = Field(None, description="Associated machine profile ID")
    material_tag: Optional[str] = Field(None, description="Target material tag")
    tools: List[ToolBit] = Field(default_factory=list, description="ToolBits in this library")
    notes: Optional[str] = Field(None, description="Library description")
```

### **2. ToolController Schema**

**File:** `services/api/app/cam/jobs/models.py`

```python
from typing import Optional, Literal
from pydantic import BaseModel, Field

class ToolController(BaseModel):
    """
    Binds a ToolBit to a Job with operational context.
    Mirrors FreeCAD's ToolController concept.
    """
    id: str = Field(..., description="Unique controller ID within job")
    tool_bit_id: str = Field(..., description="Reference to ToolBit.id")
    
    # Spindle/Feed
    spindle_speed: int = Field(..., description="Spindle RPM", gt=0)
    feed_rate: float = Field(..., description="Cutting feed rate (mm/min)", gt=0)
    plunge_rate: float = Field(..., description="Plunge/ramp feed rate (mm/min)", gt=0)
    
    # Stepdown/Stepover
    stepdown: float = Field(..., description="Max Z step per pass (mm)", gt=0)
    stepover: float = Field(..., description="XY stepover (mm or % of diameter)", gt=0)
    
    # Options
    coolant: Literal["none", "mist", "flood"] = Field(default="none")
    ramp_entry: bool = Field(default=True, description="Use ramped plunge entries")
    notes: Optional[str] = Field(None, description="Controller-specific notes")
```

### **3. CAMJob Schema**

**File:** `services/api/app/cam/jobs/models.py`

```python
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field

class MachineConfig(BaseModel):
    """Machine configuration for job."""
    id: str = Field(..., description="Machine profile ID (e.g., 'router_bcm2030')")
    label: str = Field(..., description="Human-readable machine name")
    controller: Literal["grbl", "mach3", "mach4", "fanuc", "linuxcnc", "pathpilot", "masso"] = Field(
        ..., description="Controller type"
    )
    work_envelope: Dict[str, float] = Field(
        ..., description="Work envelope in mm (x, y, z)", 
        example={"x": 2000, "y": 3000, "z": 200}
    )


class StockConfig(BaseModel):
    """Stock material configuration."""
    material: str = Field(..., description="Material type (e.g., 'maple', 'mahogany')")
    units: Literal["mm", "inch"] = Field(default="mm")
    size: Dict[str, float] = Field(..., description="Stock dimensions", example={"x": 900, "y": 200, "z": 50})
    origin: Literal["lower_left_top", "center_top", "lower_left_bottom"] = Field(
        default="lower_left_top", description="Stock origin reference"
    )
    work_offset: str = Field(default="G54", description="Work coordinate system (G54-G59)")


class GeometrySource(BaseModel):
    """Reference to geometry for operations."""
    type: Literal["toolbox-design", "dxf-upload", "svg-upload", "freecad-import"] = Field(
        ..., description="Geometry source type"
    )
    id: str = Field(..., description="Geometry identifier or file reference")


class PostConfig(BaseModel):
    """Post-processor configuration."""
    id: str = Field(..., description="Post-processor ID (e.g., 'post_grbl_router')")
    output_path: str = Field(..., description="Output G-code file path")
    safe_z: float = Field(default=5.0, description="Safe retract height (mm)")
    clearance_z: float = Field(default=10.0, description="Clearance height for rapids (mm)")
    home_sequence: Optional[str] = Field(None, description="G-code home command (e.g., 'G28')")
    header_template: Optional[str] = Field(None, description="Custom header G-code")
    footer_template: Optional[str] = Field(None, description="Custom footer G-code")


class Operation(BaseModel):
    """Base operation structure."""
    id: str = Field(..., description="Unique operation ID within job")
    type: Literal[
        "Profile2D", "Pocket2D", "DrillPattern", "Engrave", "VCarve", "Adaptive2D"
    ] = Field(..., description="Operation type")
    label: str = Field(..., description="Human-readable operation name")
    enabled: bool = Field(default=True, description="Enable/disable operation")
    priority: int = Field(default=10, description="Execution priority (lower = earlier)")
    
    tool_controller_id: str = Field(..., description="Reference to ToolController.id")
    geometry_ref: Dict[str, Any] = Field(
        ..., 
        description="Geometry reference with source and selection tags",
        example={"source": "geometry_layer", "selection_tags": ["neck_outline"]}
    )
    parameters: Dict[str, Any] = Field(..., description="Type-specific operation parameters")
    dressups: List[Dict[str, Any]] = Field(default_factory=list, description="Dressup modifiers")


class CAMJob(BaseModel):
    """
    Top-level CAM Job definition.
    Loosely based on FreeCAD's CAM Job model.
    """
    id: str = Field(..., description="Unique job identifier")
    name: str = Field(..., description="Job name")
    description: Optional[str] = Field(None, description="Job description")
    
    machine: MachineConfig = Field(..., description="Machine configuration")
    stock: StockConfig = Field(..., description="Stock configuration")
    geometry_source: GeometrySource = Field(..., description="Geometry reference")
    
    tool_controllers: List[ToolController] = Field(default_factory=list, description="Tool controllers")
    operations: List[Operation] = Field(default_factory=list, description="CAM operations")
    
    post: PostConfig = Field(..., description="Post-processor settings")
    
    # Metadata
    created_at: Optional[str] = Field(None, description="ISO 8601 timestamp")
    updated_at: Optional[str] = Field(None, description="ISO 8601 timestamp")
    schema_version: str = Field(default="1.0", description="CAMJob schema version")
```

### **4. Operation Parameter Schemas**

**File:** `services/api/app/cam/operations/models.py`

```python
from typing import Optional, Literal, Dict
from pydantic import BaseModel, Field

class Profile2DParams(BaseModel):
    """Parameters for Profile2D operation."""
    side: Literal["outside", "inside", "on"] = Field(default="outside")
    depth_mode: Literal["absolute", "relative"] = Field(default="absolute")
    final_depth: float = Field(..., description="Target depth (mm, negative = below top)")
    allowance: float = Field(default=0.0, description="Finishing allowance (mm)")
    stepdown_override: Optional[float] = Field(None, description="Override tool controller stepdown")
    compensation: Literal["left", "right", "none"] = Field(default="left", description="Cutter compensation")
    entry_strategy: Literal["plunge", "ramp", "helix"] = Field(default="ramp")
    ramp_angle: float = Field(default=5.0, description="Ramp angle in degrees", gt=0, lt=90)
    tabs: Optional[Dict[str, float]] = Field(None, description="Tab configuration")


class Pocket2DParams(BaseModel):
    """Parameters for Pocket2D operation."""
    strategy: Literal["offset", "zigzag", "spiral"] = Field(default="offset")
    depth_mode: Literal["absolute", "relative"] = Field(default="absolute")
    final_depth: float = Field(..., description="Target depth (mm)")
    stepdown_override: Optional[float] = Field(None)
    allowance: float = Field(default=0.0, description="Finishing allowance (mm)")
    island_tags: List[str] = Field(default_factory=list, description="Tags for keepout islands")
    pocket_clearance: float = Field(default=0.5, description="Clearance from pocket walls (mm)")


class DrillPatternParams(BaseModel):
    """Parameters for DrillPattern operation."""
    pattern_type: Literal["points-from-tags", "grid", "linear"] = Field(default="points-from-tags")
    point_tags: List[str] = Field(default_factory=list, description="Tags for drill point geometry")
    peck_drilling: bool = Field(default=True, description="Enable peck drilling")
    peck_depth: float = Field(default=2.0, description="Peck depth per cycle (mm)", gt=0)
    dwell: float = Field(default=0.25, description="Dwell time at depth (seconds)", ge=0)
    retract_mode: Literal["full", "partial"] = Field(default="full")


class EngraveParams(BaseModel):
    """Parameters for Engrave/VCarve operation."""
    mode: Literal["engrave", "vcarve"] = Field(default="engrave")
    depth: float = Field(..., description="Engraving depth (mm, negative)")
    follow_centerline: bool = Field(default=True, description="Follow path centerline")
    use_inline_width: bool = Field(default=False, description="Use path width for V-carve depth")
```

---

## 🔌 API Endpoints

### **CAM Jobs**

```
POST   /api/cam/jobs              Create new CAM Job
GET    /api/cam/jobs              List all jobs (with filters)
GET    /api/cam/jobs/{id}         Get job by ID
PUT    /api/cam/jobs/{id}         Update job
DELETE /api/cam/jobs/{id}         Delete job
POST   /api/cam/jobs/{id}/generate-path    Generate neutral path program (debug)
POST   /api/cam/jobs/{id}/export-gcode     Export G-code with post-processor
POST   /api/cam/jobs/{id}/compare          Trigger CompareLab diff
POST   /api/cam/jobs/{id}/duplicate        Duplicate job with new ID
```

### **ToolBits & Libraries**

```
POST   /api/cam/tools             Create ToolBit
GET    /api/cam/tools             List all tools (with filters)
GET    /api/cam/tools/{id}        Get tool by ID
PUT    /api/cam/tools/{id}        Update tool
DELETE /api/cam/tools/{id}        Delete tool

POST   /api/cam/libraries         Create ToolLibrary
GET    /api/cam/libraries         List all libraries
GET    /api/cam/libraries/{id}    Get library by ID
PUT    /api/cam/libraries/{id}    Update library
DELETE /api/cam/libraries/{id}    Delete library

POST   /api/cam/tools/import/freecad      Import FreeCAD .fctb/.fctl files
```

### **Existing Endpoints (Keep As-Is)**

```
POST   /api/cam/pocket/adaptive/plan      Module L adaptive pocketing
POST   /api/cam/pocket/adaptive/gcode     Module L G-code export
POST   /api/rmos/rosette/export-gcode     N16 rosette CNC export
GET    /api/presets                       B41 unified presets
POST   /api/geometry/export_bundle_multi  Multi-post export
```

---

## 🔄 Backward Compatibility Strategy

### **1. RMOS N16 System (Rosette CNC)**

**Status:** Keep as-is, no breaking changes

**Strategy:**
- Maintain all `/api/rmos/rosette/*` endpoints
- N16 system continues to use `cnc_machine_profiles.py` and `cnc_materials.py`
- Future: Create "Rosette CAM Job preset" that wraps N16 logic internally
- Migration path: Users can manually recreate rosette jobs as CAM Jobs if desired

**No code changes required** for N16 in Phase 1.

### **2. Module L Adaptive Pocketing**

**Status:** Integrate as Operation type

**Strategy:**
- Keep existing `/api/cam/pocket/adaptive/*` endpoints functional
- Create new `Adaptive2D` operation type that wraps `adaptive_core_l3.py`
- `services/api/app/cam/operations/adaptive_2d.py` acts as adapter:
  ```python
  from ..adaptive_core_l3 import plan_adaptive_l3
  
  class Adaptive2DOperation:
      def execute(self, params, tool_controller, geometry):
          # Convert CAM Job params to adaptive_core_l3 format
          loops = geometry_to_loops(geometry)
          path_pts = plan_adaptive_l3(loops, tool_controller.tool_bit.diameter, ...)
          return path_pts
  ```

**Benefit:** Existing adaptive pocketing tools (AdaptivePocketLab.vue) continue working while CAM Jobs can also use adaptive strategy.

### **3. Multi-Post Export System**

**Status:** Integrate with CAM Job post-processors

**Strategy:**
- CAM Job `post.id` references existing post configs in `services/api/app/data/posts/`
- New post-processor plugins (`cam/posts/grbl_post.py`, etc.) read these JSON configs
- Reuse existing post header/footer templates
- `/export-gcode` endpoint on jobs uses same multi-post infrastructure

**No changes to post JSON files** required in Phase 1.

### **4. B41 Unified Presets**

**Status:** Extend to support CAM Job presets

**Strategy:**
- Add new preset `kind: "cam_job"` to existing presets system
- Preset stores entire CAM Job JSON
- Frontend "Load Preset" button in CAM Job Editor populates job fields
- Backward compatible: Existing `kind: "cam"` presets remain valid

**Code change:** Add `cam_job` to `PresetKind` enum in `presets_store.py`.

---

## 🧪 Testing Strategy

### **Phase 1: Foundation (Weeks 1-2)**

**Backend Tests** (`services/api/app/tests/test_cam_jobs.py`):
```python
class TestToolBits:
    def test_create_toolbit()
    def test_list_toolbits()
    def test_update_toolbit()
    def test_delete_toolbit()
    def test_freecad_import_fctb()
    def test_freecad_import_fctl()

class TestToolLibraries:
    def test_create_library()
    def test_add_tool_to_library()
    def test_remove_tool_from_library()

class TestCAMJobs:
    def test_create_job()
    def test_add_tool_controller()
    def test_add_operation()
    def test_validate_job_schema()
    def test_job_with_invalid_tool_ref()  # negative case
```

**Frontend Tests** (Vitest/Testing Library):
```typescript
describe('CAMJobEditor', () => {
  test('renders stock config panel')
  test('adds tool controller')
  test('adds Profile2D operation')
  test('reorders operations by priority')
  test('validates required fields')
})

describe('ToolLibraryPanel', () => {
  test('imports FreeCAD .fctb file')
  test('filters tools by type')
  test('assigns tool to job')
})
```

**PowerShell Smoke Tests** (`scripts/test_cam_jobs.ps1`):
```powershell
# Test job creation
$job = @{
  name = "Test Neck Profile"
  machine = @{ id = "router_bcm2030"; controller = "grbl" }
  stock = @{ material = "maple"; size = @{x=900; y=200; z=50} }
} | ConvertTo-Json

curl -X POST http://localhost:8000/api/cam/jobs -d $job

# Test G-code export
curl -X POST http://localhost:8000/api/cam/jobs/test-job-001/export-gcode?post=grbl
```

### **Phase 2: Execution (Weeks 3-4)**

**Backend Tests**:
```python
class TestPathEngine:
    def test_generate_neutral_path_program()
    def test_profile_2d_execution()
    def test_pocket_2d_with_islands()
    def test_dressup_tabs_insertion()
    def test_tool_change_sequence()

class TestPostProcessors:
    def test_grbl_post_header()
    def test_fanuc_post_o_number()
    def test_thin_saw_safety_constraints()
```

**Integration Tests**:
```python
class TestCAMJobIntegration:
    def test_job_to_gcode_full_pipeline()
    def test_adaptive_operation_wrapper()
    def test_comparelab_validation()
    def test_multi_post_export_from_job()
```

---

## 📅 Implementation Phases

### **Phase 1: Foundation (2 weeks)**

**Week 1: Backend Core**
- [ ] Create `cam/tooling/` module with ToolBit/ToolLibrary models
- [ ] Implement JSON storage for tools/libraries
- [ ] Create `cam/jobs/` module with CAMJob models
- [ ] Implement JSON storage for jobs
- [ ] Create API routers for `/api/cam/tools` and `/api/cam/jobs`
- [ ] Write backend tests for CRUD operations

**Week 2: FreeCAD Importer + Frontend Shell**
- [ ] Implement FreeCAD `.fctb`/`.fctl` importer
- [ ] Create frontend route structure (`/cam/jobs`, `/cam/tools`)
- [ ] Build basic CAMJobEditor.vue (read-only display)
- [ ] Build ToolLibraryPanel.vue with import button
- [ ] Wire up API calls to backend
- [ ] Write frontend tests for components

**Deliverable:** CAM Jobs and ToolBits can be created, edited, stored, and displayed in UI. FreeCAD tools can be imported.

### **Phase 2: Execution (2 weeks)**

**Week 3: Path Engine + Operations**
- [ ] Create `cam/operations/` base interface
- [ ] Implement Profile2D operation engine
- [ ] Implement Pocket2D operation (wrapper for adaptive_core_l3)
- [ ] Create neutral path program generator in `path_engine.py`
- [ ] Write operation execution tests

**Week 4: Post Processors + G-code Export**
- [ ] Create `cam/posts/` base interface
- [ ] Implement GRBL post-processor plugin
- [ ] Implement FANUC post-processor plugin
- [ ] Wire `/export-gcode` endpoint to post plugins
- [ ] Integration tests for full job → G-code pipeline

**Deliverable:** CAM Jobs with Profile2D and Pocket2D operations can generate G-code for GRBL and FANUC controllers.

### **Phase 3: Integration (2+ weeks)**

**Week 5: CompareLab + Validation**
- [ ] Wire `/compare` endpoint to CompareLab diff router
- [ ] Implement golden baseline storage for jobs
- [ ] Add validation hooks in export pipeline
- [ ] Create CI workflow for CAM Job tests

**Week 6: Additional Operations + Dressups**
- [ ] Implement DrillPattern operation
- [ ] Implement Engrave/VCarve operation
- [ ] Create dressup system (tabs, ramps, lead-in/out)
- [ ] Add operation priority sorting in path engine

**Week 7+: Polish + Migration Tools**
- [ ] Create "Import from N16 Rosette" converter
- [ ] Create "CAM Job Preset" system (extend B41)
- [ ] Build SimulationPreview.vue component
- [ ] Performance optimization and UX polish

---

## 🔗 Integration Points

### **1. Geometry Layer**

**Current State:** Geometry is scattered across:
- Rosette Designer → inline JSON
- DXF uploads → parsed by `dxf_plan_router.py`
- SVG uploads → parsed by various importers

**CAM Job Integration:**
- `geometry_source.id` references geometry by source type + ID
- For `"toolbox-design"`: References saved design IDs
- For `"dxf-upload"`: References uploaded file path
- Operations use `selection_tags` to filter geometry (e.g., `["body_outline"]`)

**Future:** Create unified geometry registry (`services/api/app/geometry/store.py`) that all design tools write to.

### **2. CompareLab**

**Current State:** CompareLab compares SVG files via `/cam/compare/diff`.

**CAM Job Integration:**
- `/api/cam/jobs/{id}/compare` endpoint generates:
  1. SVG from job geometry
  2. SVG from exported G-code simulation
  3. Calls CompareLab diff endpoint
  4. Returns overlay comparison + delta stats

**Files to modify:**
- `cam_compare_diff_router.py` – Add job-aware comparison mode

### **3. Golden Baseline System**

**Current State:** Not yet implemented repository-wide.

**CAM Job Integration:**
- Store "golden" G-code baselines in `services/api/app/data/cam_jobs/{id}/golden.nc`
- `/export-gcode` compares new output against golden
- Drift > threshold → warning in response
- CI workflow runs golden checks on job presets

**New files:**
- `services/api/app/cam/jobs/golden_validator.py`

### **4. RMOS N16 System**

**Current State:** Rosette CNC export at `/api/rmos/rosette/export-gcode`.

**CAM Job Integration:**
- **Phase 1:** No integration (parallel systems)
- **Phase 2:** Create converter that reads N16 ring geometry → CAM Job with Pocket2D operations
- **Phase 3:** Deprecate direct N16 endpoint in favor of CAM Jobs

**Migration path:** Add "Import from RMOS Rosette" button in CAM Job UI.

### **5. Module L Adaptive Pocketing**

**Current State:** Standalone adaptive engine at `/api/cam/pocket/adaptive/plan`.

**CAM Job Integration:**
- Create `Adaptive2D` operation type
- `cam/operations/adaptive_2d.py` wraps `adaptive_core_l3.plan_adaptive_l3()`
- Existing AdaptivePocketLab.vue continues to work (calls old endpoint)
- CAM Jobs can also use adaptive strategy via operation

**Benefit:** Unified tooling (adaptive uses ToolController feeds/speeds) while maintaining standalone tool.

---

## 🚨 Critical Design Decisions

### **1. Storage: File-Based JSON vs Database**

**Decision:** File-based JSON for Phase 1-2, optional DB for Phase 3+.

**Rationale:**
- Matches existing patterns (B41 presets, post configs)
- Simple deployment (no migrations)
- Git-friendly (jobs can be version controlled)
- Easy backup/restore

**Future:** Add SQLite adapter if job count > 100 or multi-user concurrency needed.

### **2. Namespace: `/api/cam/jobs` vs `/api/toolbox-cam/jobs`**

**Decision:** `/api/cam/jobs`

**Rationale:**
- Existing CAM endpoints already use `/api/cam/*` prefix
- Shorter, cleaner URLs
- Avoid confusion with "ToolBox" (the project name)

**Note:** Existing `/api/cam/pocket`, `/api/cam/sim`, etc. remain unchanged.

### **3. Operation Execution: Inline vs External Services**

**Decision:** Inline execution within path engine for Phase 1-2.

**Rationale:**
- Simpler architecture (no microservices)
- Faster development (no IPC overhead)
- Sufficient for single-user local dev

**Future:** If job execution becomes slow (>10 seconds), consider:
- Celery task queue for background processing
- WebSocket progress updates

### **4. Post Processors: Python Plugins vs JSON Configs**

**Decision:** Python plugins with JSON config **hybrid**.

**Rationale:**
- JSON configs (existing): Simple header/footer templates (GRBL, Mach4)
- Python plugins (new): Complex logic (thin-kerf saw safety, advanced arc modes)
- Base class loads JSON, plugins override methods for custom behavior

**Example:**
```python
# cam/posts/grbl_post.py
class GRBLPost(PostProcessor):
    def __init__(self):
        self.config = load_json("posts/grbl.json")  # header/footer
    
    def emit_arc(self, move):
        # GRBL-specific arc format (G2/G3 with IJK)
        return f"G2 X{move.x} Y{move.y} I{move.i} J{move.j}"
```

### **5. Dressup Composition: Array Order vs Priority Field**

**Decision:** Array order determines application sequence.

**Rationale:**
- Simpler mental model (visual sequence in UI)
- Matches FreeCAD's dressup ordering
- No ambiguity with priority conflicts

**Example:**
```json
"dressups": [
  {"type": "RampEntry", "parameters": {"angle": 3.0}},   // Applied first
  {"type": "Tabs", "parameters": {"tab_length": 10.0}}   // Applied to ramped path
]
```

---

## 📝 Implementation Checklist

### **Backend Core**
- [ ] Create `cam/tooling/` module with models, store, importer
- [ ] Create `cam/jobs/` module with models, store, path_engine
- [ ] Create `cam/operations/` module with base + Profile2D + Pocket2D
- [ ] Create `cam/posts/` module with base + GRBL + FANUC
- [ ] Create `cam_jobs_router.py` with CRUD endpoints
- [ ] Create `cam_tooling_router.py` with tool/library endpoints
- [ ] Register routers in `main.py`
- [ ] Write backend tests (CRUD, execution, post-processing)

### **Frontend Core**
- [ ] Create `views/cam/` directory with Job/Editor/Library views
- [ ] Create `components/cam/` directory with editor components
- [ ] Create `router/camJobRoutes.ts` with route definitions
- [ ] Wire routes into `router/index.ts`
- [ ] Build CAMJobEditor.vue with tabs (Stock, Tools, Ops, Export)
- [ ] Build ToolLibraryPanel.vue with FreeCAD import
- [ ] Build OperationEditor.vue with type-specific forms
- [ ] Write frontend tests (component rendering, API calls)

### **Integration**
- [ ] Wire CAM Job `/compare` endpoint to CompareLab
- [ ] Create Adaptive2D operation wrapper for Module L
- [ ] Extend B41 presets to support `kind: "cam_job"`
- [ ] Create "Import from RMOS Rosette" converter (optional Phase 3)
- [ ] Add CI workflow for CAM Job tests

### **Documentation**
- [ ] Update `.github/copilot-instructions.md` with CAM Job patterns
- [ ] Create `CAM_JOB_QUICKREF.md` with usage examples
- [ ] Update `DEVELOPER_HANDOFF_N16_COMPLETE.md` with Phase status
- [ ] Create tutorial: "Your First CAM Job"

---

## 🎯 Success Criteria

### **Phase 1 Complete When:**
- ✅ ToolBits can be created, stored, and imported from FreeCAD
- ✅ ToolLibraries can be created and managed
- ✅ CAM Jobs can be created with stock, tools, and operations
- ✅ Jobs display correctly in frontend editor
- ✅ All CRUD endpoints functional and tested
- ✅ No regressions in N16 or Module L systems

### **Phase 2 Complete When:**
- ✅ CAM Jobs with Profile2D operations export valid GRBL G-code
- ✅ CAM Jobs with Pocket2D operations use adaptive engine correctly
- ✅ Path engine generates neutral program from job
- ✅ Post-processors apply headers/footers from configs
- ✅ Integration tests pass for full job → G-code pipeline

### **Phase 3 Complete When:**
- ✅ CompareLab validates job exports against geometry
- ✅ DrillPattern and Engrave operations functional
- ✅ Dressup system (tabs, ramps) integrated
- ✅ CI workflow runs CAM Job tests on every push
- ✅ Documentation complete with examples

---

## 📚 References

- [TOOLBOX_CAM_ARCHITECTURE_v1.md](./TOOLBOX_CAM_ARCHITECTURE_v1.md) – Original architecture proposal
- [CAM_TOOLBIT_IMPORTER_DESIGN.md](./CAM_TOOLBIT_IMPORTER_DESIGN.md) – FreeCAD importer spec
- [CAM_JOB_SCHEMA_v1.md](./CAM_JOB_SCHEMA_v1.md) – Detailed schema definitions
- [ADAPTIVE_POCKETING_MODULE_L.md](./ADAPTIVE_POCKETING_MODULE_L.md) – Module L integration guide
- [DEVELOPER_HANDOFF_N16_COMPLETE.md](./docs/DEVELOPER_HANDOFF_N16_COMPLETE.md) – N16 system reference

---

**Status:** ✅ Specification Complete – Ready for Phase 1 Implementation  
**Next Step:** Begin backend core development (ToolBit/ToolLibrary models + storage)  
**Estimated Timeline:** 6-8 weeks for Phases 1-3  
**Backward Compatibility:** 100% – No breaking changes to existing systems
