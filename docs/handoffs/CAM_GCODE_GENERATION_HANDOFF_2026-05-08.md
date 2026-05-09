# CAM G-Code Generation — Developer Handoff

**Date:** 2026-05-08  
**Purpose:** Map all systems that actually produce G-code and guide refactoring to wire frontend views to real generators

---

## EXECUTIVE SUMMARY

The repository has **28 real G-code generators** but only **4 frontend views** are wired to them. The remaining CAM operation views use `setTimeout()` mocks. The gap is not missing generators — it's missing API wiring.

### Key Numbers

| Metric | Count |
|--------|-------|
| Real G-code generator classes/functions | 28 |
| Frontend CAM views | 12 |
| Views wired to real generators | 4 |
| Views with setTimeout() mocks | 5+ |
| Post-processors (GRBL, LinuxCNC, Fanuc) | 3 |

---

## SECTION 1: NAMESPACE HIERARCHY

### Generator Locations (Actual G-code Production)

```
services/api/app/
├── cam/                              # PRIMARY CAM GENERATORS
│   ├── binding/
│   │   ├── channel_toolpath.py       # BindingChannelGenerator.generate_gcode()
│   │   ├── purfling_ledge.py         # PurflingLedgeGenerator.generate_gcode()
│   │   ├── binding_corner_miter.py   # generate_corner_miter_gcode(), generate_binding_corner_gcode()
│   │   └── om_purf_03_additions.py   # generate_second_pass_gcode(), generate_neck_purfling_gcode()
│   │
│   ├── drilling/
│   │   └── peck_cycle.py             # DrillingPeckCycleGenerator.generate_gcode()
│   │
│   ├── profiling/
│   │   └── profile_toolpath.py       # ProfileToolpathGenerator.generate_gcode()
│   │
│   ├── vcarve/
│   │   └── toolpath.py               # VCarveToolpathGenerator.generate_gcode()
│   │
│   ├── carving/
│   │   └── surface_carving.py        # SurfaceCarvingGenerator, CarvingMove.to_gcode()
│   │
│   ├── fhole/
│   │   └── toolpath.py               # FHoleToolpathGenerator.generate()
│   │
│   ├── neck/
│   │   ├── fret_slots.py             # FretSlotGenerator.generate()
│   │   ├── profile_carving.py        # ProfileCarvingGenerator
│   │   └── truss_rod_channel.py      # TrussRodChannelGenerator
│   │
│   ├── rosette/
│   │   └── cnc/cnc_gcode_exporter.py # generate_gcode_from_toolpaths()
│   │
│   ├── modal_cycles.py               # generate_drilling_gcode()
│   ├── adaptive_core.py              # Core adaptive clearing (used by mvp_router)
│   └── adaptive_core_l1.py           # L1 adaptive strategies
│
├── generators/                       # INSTRUMENT-SPECIFIC GENERATORS
│   ├── acoustic_body_generator.py    # AcousticBodyGenerator
│   │   └── generate_perimeter_gcode(), generate_soundhole_gcode(), generate_binding_channel_gcode()
│   │
│   ├── lespaul_gcode/                # COMPLETE LES PAUL GENERATOR
│   │   ├── generator.py              # LesPaulGCodeGenerator.generate_full_program()
│   │   ├── primitives.py             # G-code primitives (G0, G1, G2, G3)
│   │   ├── perimeter.py              # PerimeterOperationMixin
│   │   ├── pockets.py                # PocketOperationsMixin
│   │   └── drilling.py               # DrillingOperationsMixin
│   │
│   ├── stratocaster_body_generator.py # StratocasterBodyGenerator
│   └── neck_headstock_generator.py    # NeckGCodeGenerator
│
├── calculators/                      # CAM-CAPABLE CALCULATORS
│   ├── fret_slots_cam.py             # compute_fret_slot_toolpath(), generate_gcode()
│   ├── fret_slots_export.py          # generate_gcode()
│   └── cantilever_armrest_calc.py    # generate_gcode()
│
└── rmos/                             # RMOS RUN MANAGEMENT
    ├── mvp_router.py                 # CANONICAL: dxf-to-grbl endpoint
    └── posts/                        # POST-PROCESSORS
        ├── base.py                   # BasePostProcessor
        ├── grbl.py                   # GRBLPostProcessor
        ├── linuxcnc.py               # LinuxCNCPostProcessor
        └── fanuc.py                  # FanucPostProcessor
```

### Router Structure (API Exposure)

```
services/api/app/cam/routers/
├── aggregator.py                     # MAIN: Combines all /api/cam/* routers
│
├── drilling/
│   ├── drill_pattern_router.py       # POST /api/cam/drilling/pattern/gcode
│   └── drill_modal_router.py         # POST /api/cam/drilling/modal/gcode
│
├── profiling/
│   └── profile_router.py             # POST /api/cam/profiling/gcode
│
├── binding/
│   └── binding_router.py             # POST /api/cam/binding/channel/gcode
│                                     # POST /api/cam/binding/purfling/gcode
│
├── vcarve/
│   └── production_router.py          # POST /api/cam/vcarve/production/gcode
│
├── toolpath/
│   ├── vcarve_router.py              # POST /api/cam/toolpath/vcarve/gcode
│   ├── roughing_router.py            # POST /api/cam/toolpath/roughing/gcode
│   ├── biarc_router.py               # POST /api/cam/toolpath/biarc/gcode
│   ├── helical_router.py             # Helical entry toolpaths
│   └── relief_export_router.py       # Relief carving export
│
├── rosette/
│   └── rosette_toolpath_router.py    # POST /api/cam/rosette/post-gcode
│
├── fret_slots/
│   └── fret_slots_router.py          # Fret slot CAM operations
│
└── relief/
    └── (aggregated)                  # Relief carving operations
```

---

## SECTION 2: CANONICAL PATTERN

### The Working Example: `mvp_router.py`

This is the **only fully verified** DXF → G-code path. Copy this pattern.

```python
# services/api/app/rmos/mvp_router.py (lines 24-129)

@router.post("/wrap/mvp/dxf-to-grbl")
async def dxf_to_grbl(
    file: UploadFile = File(...),
    tool_d: float = Form(6.0),
    # ... CAM parameters ...
) -> Dict[str, Any]:
    """
    1. Create run_id for RMOS tracking
    2. Parse DXF with ezdxf
    3. Extract loops from LWPOLYLINE/POLYLINE entities
    4. Build PlanIn schema
    5. Call compute_plan() from adaptive/plan_router
    6. Convert plan moves to G-code lines
    7. Persist attachments via put_bytes_attachment(), put_json_attachment()
    8. Return G-code + run_id + metadata
    """
    run_id = f"RUN-DXF-{uuid.uuid4().hex[:12].upper()}"
    
    # Parse DXF → loops
    # ...
    
    # Generate toolpath plan
    plan_result = compute_plan(plan_in)
    
    # Convert to G-code
    gcode_lines = [...]
    for move in moves:
        # Emit G0/G1/G2/G3
    
    # Persist to RMOS
    put_bytes_attachment(gcode_bytes, kind="gcode_output", ...)
    
    return {"ok": True, "run_id": run_id, "gcode": gcode_str, ...}
```

### Key Components of the Pattern

| Component | Purpose | Location |
|-----------|---------|----------|
| `run_id` | RMOS traceability | Generated at entry |
| `UploadFile` | DXF/geometry input | FastAPI form |
| `PlanIn` schema | Typed CAM parameters | `schemas/adaptive_schemas.py` |
| `compute_plan()` | Toolpath calculation | `routers/adaptive/plan_router.py` |
| `put_*_attachment()` | RMOS artifact storage | `rmos/runs_v2/attachments.py` |
| G-code emission | String building | Inline or generator class |

---

## SECTION 3: FRONTEND ↔ BACKEND MAPPING

### Currently Working

| Frontend View | API Endpoint | Generator | Status |
|---------------|--------------|-----------|--------|
| `DxfToGcodeView` | `/api/rmos/wrap/mvp/dxf-to-grbl` | `adaptive_core` + inline | **CANONICAL** |
| `QuickCutView` | `/api/rmos/wrap/mvp/dxf-to-grbl` | Same as above | **WORKING** |
| `VCarveView` | `/api/cam/toolpath/vcarve/gcode` | `VCarveToolpathGenerator` | **WORKING** |
| `ReliefCarvingView` | `/api/cam/relief/*` | `SurfaceCarvingGenerator` | **WORKING** |

### Fake (setTimeout Mocks)

| Frontend View | Fake Pattern | Real Generator Exists | Wiring Task |
|---------------|--------------|----------------------|-------------|
| `PocketClearingView` | `setTimeout(1000)` | `lespaul_gcode/pockets.py` | Wire to `/api/cam/toolpath/roughing/gcode` |
| `ContourCuttingView` | `setTimeout(1000)` | `profile_toolpath.py` | Wire to `/api/cam/profiling/gcode` |
| `SurfacingView` | `setTimeout(1000)` | **NONE** | Needs new generator |
| `DrillingView` | `setTimeout(500)` | `drilling/peck_cycle.py` | Wire to `/api/cam/drilling/pattern/gcode` |
| `FretSlottingView` | `setTimeout(500)` | `fret_slots_cam.py` | Wire to `/api/cam/fret_slots/*` |

### Partial (DXF only, no G-code)

| Frontend View | Current State | Missing |
|---------------|---------------|---------|
| `FretSlottingView` | DXF export works | G-code generation endpoint |
| `CamWorkspaceView` | Neck G-code works | ToolpathPlayer, RMOS |

---

## SECTION 4: GENERATOR CLASS SIGNATURES

### Core Generator Interface Pattern

```python
# Pattern 1: Class with generate_gcode() method
class ProfileToolpathGenerator:
    def __init__(self, contour: List[Tuple[float, float]], 
                 tool_d: float, feed: float, ...):
        ...
    
    def generate_gcode(self) -> str:
        """Returns complete G-code program as string."""
        ...

# Pattern 2: Standalone function
def generate_drilling_gcode(
    holes: List[Hole],
    tool_d: float,
    peck_depth: float,
    feed: float,
    ...
) -> str:
    """Returns complete G-code program as string."""
    ...

# Pattern 3: Mixin for instrument generators
class PocketOperationsMixin:
    def generate_pocket_gcode(self, cavity: CavitySpec) -> List[str]:
        """Returns list of G-code lines."""
        ...
```

### Schema Requirements

Each generator needs a Pydantic request schema:

```python
# Example: drilling/drill_pattern_router.py
class DrillPatternRequest(BaseModel):
    holes: List[HoleSpec]
    tool_diameter: float = 3.0
    peck_depth: float = 2.0
    feed_rate: float = 100.0
    spindle_rpm: int = 18000
    safe_z: float = 10.0
    retract_z: float = 2.0
```

---

## SECTION 5: REFACTORING TASKS

### Priority 1: Wire Existing Generators to Frontend

| Task | Frontend | Backend Router | Generator | Effort |
|------|----------|----------------|-----------|--------|
| **5.1** | `PocketClearingView` | Create `/api/cam/pocket/gcode` | Adapt `lespaul_gcode/pockets.py` | MEDIUM |
| **5.2** | `ContourCuttingView` | `/api/cam/profiling/gcode` (exists) | `ProfileToolpathGenerator` | LOW |
| **5.3** | `DrillingView` | `/api/cam/drilling/pattern/gcode` (exists) | `DrillingPeckCycleGenerator` | LOW |
| **5.4** | `FretSlottingView` | Create `/api/cam/fret_slots/gcode` | `fret_slots_cam.generate_gcode()` | MEDIUM |

### Priority 2: Create Missing Generator

| Task | Frontend | Generator Needed | Reference |
|------|----------|------------------|-----------|
| **5.5** | `SurfacingView` | `SurfacingGenerator` | Copy `profile_toolpath.py` pattern |

### Priority 3: Normalize Generator Interface

All generators should:
1. Accept a Pydantic `*Request` schema
2. Return `str` (complete G-code) or `Response` with `text/plain`
3. Support optional RMOS run_id for artifact tracking
4. Include spindle control parameters

---

## SECTION 6: AGGREGATOR STATE

The `cam/routers/aggregator.py` shows current router registration:

```python
# ENABLED (mounted at /api/cam/*)
drilling_router      → /api/cam/drilling/*
fret_slots_router    → /api/cam/fret_slots/*
relief_router        → /api/cam/relief/*
risk_router          → /api/cam/risk/*
rosette_router       → /api/cam/rosette/*
toolpath_router      → /api/cam/toolpath/*
pipeline_router      → /api/cam/pipeline/*
profiling_router     → /api/cam/profiling/*
binding_router       → /api/cam/binding/*
vcarve_production    → /api/cam/vcarve/*

# DISABLED (legacy path conflicts)
utility_router       # Duplicated at /api/cam/settings, /api/cam/backup
monitoring_router    # Duplicated at /api/cam/metrics
simulation_router    # Zero frontend usage
export_router        # Duplicates /api/cam_gcode, /api/cam/svg
```

---

## SECTION 7: WIRING CHECKLIST

For each fake view → real generator wiring:

### Frontend Changes

- [ ] Remove `setTimeout()` mock
- [ ] Add API call to real endpoint
- [ ] Map form fields to request schema
- [ ] Handle response (G-code string or blob)
- [ ] Add download button for `.nc` file
- [ ] Optional: Add ToolpathPlayer preview

### Backend Changes (if endpoint missing)

- [ ] Create request schema in `schemas/`
- [ ] Create router endpoint in `cam/routers/<category>/`
- [ ] Wire generator class/function
- [ ] Add RMOS attachment persistence (optional)
- [ ] Register in aggregator.py
- [ ] Add to router_registry manifest

### Example: Wiring ContourCuttingView

```typescript
// packages/client/src/views/cam/ContourCuttingView.vue

// BEFORE (fake)
const generateToolpath = async () => {
  isGenerating.value = true;
  await new Promise(r => setTimeout(r, 1000));
  gcodeResult.value = "; mock contour gcode";
  isGenerating.value = false;
};

// AFTER (real)
const generateToolpath = async () => {
  isGenerating.value = true;
  const response = await fetch('/api/cam/profiling/gcode', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      contour: contourPoints.value,
      tool_diameter: toolDiameter.value,
      stepdown: stepdown.value,
      feed_rate: feedRate.value,
      spindle_rpm: spindleRpm.value,
      tabs: enableTabs.value ? tabConfig.value : null,
    }),
  });
  gcodeResult.value = await response.text();
  isGenerating.value = false;
};
```

---

## SECTION 8: POST-PROCESSOR INTEGRATION

All G-code should pass through a post-processor before export:

```python
# services/api/app/rmos/posts/

class BasePostProcessor:
    def process(self, gcode: str) -> str: ...

class GRBLPostProcessor(BasePostProcessor):
    """GRBL 1.1 compatible output."""
    # Removes unsupported codes, validates line length

class LinuxCNCPostProcessor(BasePostProcessor):
    """LinuxCNC compatible output."""
    # Full G-code support, canned cycles

class FanucPostProcessor(BasePostProcessor):
    """Fanuc-style industrial output."""
    # O-numbers, M-codes, block numbering
```

### Usage Pattern

```python
from app.rmos.posts import GRBLPostProcessor

gcode_raw = generator.generate_gcode()
post = GRBLPostProcessor()
gcode_final = post.process(gcode_raw)
```

---

## SECTION 9: VERIFICATION CHECKLIST

After wiring each view:

- [ ] Generate G-code from UI
- [ ] Verify G-code syntax (no errors in parser)
- [ ] Run through ToolpathPlayer simulation (if available)
- [ ] Download .nc file
- [ ] Optional: Dry run on machine with spindle off
- [ ] Optional: RMOS run artifact created

---

## APPENDIX A: FILE QUICK REFERENCE

| What | Where |
|------|-------|
| Canonical endpoint | `rmos/mvp_router.py:24` |
| Adaptive toolpath | `cam/adaptive_core.py` |
| Profile generator | `cam/profiling/profile_toolpath.py:225` |
| Drilling generator | `cam/drilling/peck_cycle.py:147` |
| V-carve generator | `cam/vcarve/toolpath.py:223` |
| Binding generator | `cam/binding/channel_toolpath.py:167` |
| Fret slot generator | `cam/neck/fret_slots.py:72` |
| Les Paul full program | `generators/lespaul_gcode/generator.py` |
| Router aggregator | `cam/routers/aggregator.py` |
| Post-processors | `rmos/posts/` |
| RMOS attachments | `rmos/runs_v2/attachments.py` |

---

*Document created: 2026-05-08*  
*Classification: Developer Handoff*  
*Status: Ready for team review*
