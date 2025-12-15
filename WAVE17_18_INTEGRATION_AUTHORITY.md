# Wave 17→18 Integration Reconciliation & Authority Document

**Date:** December 8, 2025  
**Status:** ✅ AUTHORITATIVE — Final Decisions  
**Scope:** Integration of 5 Bundles into Wave 17 Architecture

---

## 🎯 Executive Summary

This document provides **authoritative answers** to all Critical Integration Questions raised during the analysis of five integration bundles (Fretboard Geometry, Feasibility Fusion, RMOS Context Adapter, Instrument Model Loader, CAM Fret Slots Router).

**Key Decisions:**
1. **Wave 17 `GuitarModelSpec` is authoritative** (Bundle 4's version deprecated)
2. **JSON stores inches, Python uses mm** (permanent standard)
3. **RmosContext class must be created** (currently missing)
4. **Calculator stubs acceptable for Wave 17** (full unification in Wave 18)
5. **5-phase integration order** (Foundation → RMOS → Fretboard → Feasibility → CAM)

---

## ✅ Critical Questions — Authoritative Answers

### **1. Architecture & Dependencies — What Exists / What Doesn't**

#### ✔ **Does `instrument_geometry/scale_intonation.py` exist?**

**Answer:** **YES** — Generated in Wave 14–17, must remain.

**Status:** ✅ Production Ready  
**Action:** No changes needed

---

#### ✔ **Does `calculators/service.py` exist?**

**Answer:** **YES, but incomplete** — Facade skeleton exists, needs 5 real calculators.

**Missing Functions:**
- `compute_chipload_risk()`
- `compute_heat_risk()`
- `compute_deflection_risk()`
- `compute_rimspeed_risk()`
- `compute_bom_efficiency()`

**Existing Implementation:** Some functions exist in Saw Lab, some in Router calculators, none unified.

**Decision:** ✅ **Use stubs now; unify in Wave 18 (Saw Lab Wave 2)**

**Rationale:** Allows forward progress without blocking on calculator unification.

**Action Required:**
```python
# services/api/app/calculators/service.py
def compute_chipload_risk(**kwargs) -> Dict[str, Any]:
    """Stub: Returns safe default score until Saw Lab integration."""
    return {"score": 75.0, "risk": "UNKNOWN", "details": kwargs}

# Repeat for all 5 functions
```

---

#### ✔ **Does `rmos/context.py` or `RmosContext` exist?**

**Answer:** **NO** — Partial context adapter code exists, but no authoritative `RmosContext` class.

**Decision:** 🚨 **MUST CREATE `RmosContext` — Everything depends on it**

**Action Required:**
```python
# services/api/app/rmos/context.py
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class RmosContext:
    """
    Unified RMOS context for instrument-aware manufacturing operations.
    
    Integrates:
    - Instrument geometry (model_spec)
    - Toolpaths (DXF/G-code)
    - Materials (wood species, thickness)
    - Cut operations (saw/route/drill)
    - Safety constraints (feeds, speeds, tool limits)
    - Physics inputs (chipload, deflection, heat)
    """
    model_spec: InstrumentSpec
    toolpaths: Optional[ToolpathData] = None
    materials: Optional[MaterialProfile] = None
    cuts: Optional[List[CutOperation]] = None
    safety_constraints: Optional[SafetyConstraints] = None
    physics_inputs: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "RmosContext":
        """Create RmosContext from context_adapter payload."""
        # Implementation in Phase B
        pass
```

**Priority:** 🔴 CRITICAL — Block other integrations until complete

---

### **2. Unit System Consistency — JSON inches, internal mm**

**Question:** Is the inch→mm convention consistent across all bundles?

**Answer:** ✅ **YES — This is the permanent standard**

**Rules:**
1. **JSON presets store ALL values in inches**
2. **Python loader converts to millimeters on load**
3. **All internal code (geometry, CAM, RMOS) works in mm**
4. **API responses default to mm (client can request inch conversion)**

**Rationale:**
- Luthiers and guitar builders measure in inches (industry standard)
- CNC, geometry engines (Shapely), RMOS calculators use metric
- Clean separation: input layer (inches) → processing layer (mm) → output layer (configurable)

**Example:**
```json
// benedetto_17.json (inches)
{
  "scale": {
    "scale_length_in": 25.5,
    "num_frets": 21
  }
}
```

```python
# Python (mm after loader conversion)
model = load_model_spec("benedetto_17")
print(model.scale.scale_length_mm)  # 647.7 mm
```

**Action:** ✅ No changes needed — Wave 17 already follows this pattern

---

### **3. Overlapping Functionality — Two `GuitarModelSpec` versions**

**Question:** Which `GuitarModelSpec` schema is authoritative?

**Conflict:**
- **Bundle 4 Schema:** `scale`, `neck_joint`, `bridge`, `string_set`, `reference_compensation_mm`
- **Wave 17 Schema:** `scale_profile_id`, `strings`, `nut_spacing`, `bridge_spacing`, `neck_taper`, `body_outline_id`

**Answer:** 🏆 **Wave 17 `GuitarModelSpec` IS AUTHORITATIVE**

**Rationale:**
1. ✅ Aligned with RMOS 2.0 architecture
2. ✅ Modular (decoupled scale profiles, string specs, taper specs)
3. ✅ Compatible with DXF asset registry
4. ✅ Compatible with feasibility fusion bundle
5. ✅ Extensible to multiscale (Wave 16–17 plan)
6. ✅ Already integrated with Neck Taper Suite

**Decision:** ❌ **Bundle 4 schema DEPRECATED**

**Migration Path:**
- Bundle 4 JSON presets can be **auto-translated** to Wave 17 format
- No manual conversion required
- Translation script provided in Phase A

**Action Required:**
```python
# services/api/app/instrument_geometry/migration.py
def migrate_bundle4_to_wave17(old_spec: Dict) -> GuitarModelSpec:
    """Translate Bundle 4 schema → Wave 17 schema."""
    # Map old fields to new structure
    pass
```

---

### **4. Calculators Service Facade — Should we create stubs?**

**Question:** Do the 5 calculator functions exist?

**Answer:** **PARTIAL** — Some in Saw Lab, some in Router calculators, none unified.

**Required Functions:**
- `compute_chipload_risk()` — ⚠️ Exists in Router, not in service.py
- `compute_heat_risk()` — ⚠️ Exists in Saw Lab, not unified
- `compute_deflection_risk()` — ⚠️ Exists conceptually, not implemented
- `compute_rimspeed_risk()` — ✅ Exists in Saw Lab
- `compute_bom_efficiency()` — ❌ Conceptual only

**Decision:** ✅ **Create stubs for Wave 17–18; unify in Saw Lab Wave 2**

**Implementation Strategy:**
```python
# services/api/app/calculators/service.py

def compute_chipload_risk(
    tool_id: str,
    material_id: str,
    feed_rate_mm_min: float,
    rpm: float,
    **kwargs
) -> Dict[str, Any]:
    """
    Compute chipload safety score (0-100, higher is safer).
    
    STUB (Wave 17): Returns conservative estimate.
    TODO (Wave 18): Wire to unified Router + Saw Lab calculator.
    """
    # Placeholder logic
    chipload_mm = feed_rate_mm_min / rpm if rpm > 0 else 0
    score = 75.0  # Conservative default
    risk = "MEDIUM"
    
    return {
        "score": score,
        "risk": risk,
        "chipload_mm": chipload_mm,
        "details": kwargs
    }

# Repeat pattern for all 5 functions
```

**Priority:** 🟡 MEDIUM — Stubs sufficient for Phase D (Feasibility)

---

### **5. Naming Conflicts: `fretboard_geometry`**

**Question:** Does `fretboard_geometry.py` conflict with Wave 17 neck geometry?

**Answer:** ❌ **NO CONFLICT** — Different responsibilities

**Scope Separation:**

| Module | Responsibility |
|--------|---------------|
| `neck_taper/` (Wave 17) | Nut width, heel width, neck profile, width taper along length |
| `fretboard_geometry.py` (New) | Fret slot positions, spacing, fan-fret angles, radius compensation |

**Decision:** ✅ **Keep both — They complement each other**

**Future Optimization (Wave 19+):**
- May unify into `fretboard/` package for organization
- Keep separate APIs for now

**Action:** ✅ No changes needed — Proceed with Bundle 1 integration

---

### **6. RMOS Context Structure — Does it exist?**

**Question:** Is there an authoritative `RmosContext` class?

**Answer:** **NO** — Only partial context adapter exists

**Current State:**
- ✅ `context_adapter.py` exists (generates dict payloads)
- ❌ No `RmosContext` dataclass with validation
- ❌ No schema versioning
- ❌ API doesn't enforce context structure

**Decision:** 🚨 **MUST CREATE `rmos/context.py` with full `RmosContext` class**

**Required Structure:**
```python
@dataclass
class RmosContext:
    """Unified RMOS manufacturing context."""
    
    # Core instrument geometry
    model_spec: InstrumentSpec
    
    # Toolpath data (optional, from DXF/G-code import)
    toolpaths: Optional[ToolpathData] = None
    
    # Material specifications
    materials: Optional[MaterialProfile] = None
    
    # Cut operations (saw, route, drill)
    cuts: Optional[List[CutOperation]] = None
    
    # Safety constraints (feeds, speeds, tool limits)
    safety_constraints: Optional[SafetyConstraints] = None
    
    # Physics calculation inputs/outputs
    physics_inputs: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "RmosContext":
        """Factory: Create from context_adapter payload."""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        pass
```

**Enables:**
- Cross-module reasoning (Saw Lab + CNC Router + Instrument Geometry)
- Type-safe context passing
- Validation at RMOS boundaries
- Future versioning (RmosContextV2, etc.)

**Priority:** 🔴 CRITICAL — Phase B dependency

---

### **7. Integration Strategy — Correct Phase Ordering**

**Question:** What is the dependency-correct integration order?

**Answer:** ✅ **5-Phase Sequential Integration**

---

## 🗺️ Authoritative Integration Plan

### **🟦 PHASE A — Foundation (Bundle 4 + Wave 17 Harmonization)**

**Goal:** Establish unified instrument model system

**Tasks:**
1. ✅ **Keep Wave 17 `GuitarModelSpec` as authoritative schema**
2. ✅ **Deprecate Bundle 4 schema** (provide migration script)
3. ✅ **Create/verify `instrument_geometry/models/` structure:**
   - `models.py` (dataclasses with inch→mm properties)
   - `loader.py` (JSON→Python conversion)
   - `benedetto_17.json` (updated preset using Wave 17 schema)
   - Additional presets: `strat_25_5.json`, `lp_24_75.json`, etc.
4. ✅ **Write unit tests for model loading**

**Files Created/Modified:**
- ✅ Already exists: `services/api/app/instrument_geometry/model_spec.py` (Wave 17)
- ✅ Already exists: `services/api/app/instrument_geometry/models.py` (StringSpec, ScaleProfile)
- 🆕 Create: Migration script for Bundle 4→Wave 17 translation

**Success Criteria:**
- [ ] All model presets load without errors
- [ ] Inch→mm conversion validated
- [ ] Tests pass: `pytest tests/test_model_loader.py -v`

**Priority:** 🔴 CRITICAL — Must complete before any other phase

---

### **🟩 PHASE B — RMOS Connectivity (Bundle 3)**

**Goal:** Create unified RMOS context system

**Dependencies:** Phase A (requires `GuitarModelSpec`)

**Tasks:**
1. 🆕 **Create `rmos/context.py`** with `RmosContext` dataclass
2. 🆕 **Create `rmos/context_adapter.py`** (model_id → RmosContext)
3. 🆕 **Optional: Add `rmos/context_router.py`** for API access
   - `GET /api/rmos/models` → list available model IDs
   - `GET /api/rmos/context/{model_id}` → retrieve context payload

**Files Created:**
```
services/api/app/rmos/
├── context.py              # NEW: RmosContext dataclass
├── context_adapter.py      # NEW: Conversion layer
└── context_router.py       # NEW: FastAPI endpoints (optional)
```

**Success Criteria:**
- [ ] `RmosContext.from_dict()` factory works
- [ ] Context adapter converts model_id → full context
- [ ] API endpoint returns valid context JSON
- [ ] Tests pass: `pytest tests/test_rmos_context.py -v`

**Priority:** 🔴 HIGH — Enables Phases C, D, E

---

### **🟨 PHASE C — Fretboard Geometry (Bundle 1)**

**Goal:** Add fret slot geometry calculations and CAM preview

**Dependencies:** Phase A (requires model loader), Phase B (optional RMOS integration)

**Tasks:**
1. 🆕 **Create `instrument_geometry/fretboard_geometry.py`**
   - `FretPoint` dataclass
   - `compute_standard_frets()` (single-scale)
   - `compute_fan_frets()` (multiscale)
   - `interpolate_radius_mm()` (compound radius)
   - `slot_width_at_position_mm()` (taper)
   - `radius_depth_compensation_mm()` (geometry)

2. 🆕 **Create `calculators/fret_slots_cam.py`**
   - `FretSlotParams` dataclass
   - `generate_fret_slots_dxf()` (R12 DXF export)
   - `generate_fret_slots_gcode()` (basic G-code)

3. 🆕 **Optional: Extend `rmos/context_adapter.py`**
   - Add `fretboard_geometry` key to context payload

**Files Created:**
```
services/api/app/
├── instrument_geometry/
│   └── fretboard_geometry.py    # NEW
└── calculators/
    └── fret_slots_cam.py         # NEW
```

**Success Criteria:**
- [ ] Standard fret calculation works (648mm scale → 22 frets)
- [ ] Fan-fret calculation works (multiscale support)
- [ ] DXF export produces valid R12 file
- [ ] G-code export generates slot program
- [ ] Tests pass: `pytest tests/test_fretboard_geometry.py -v`

**Priority:** 🟡 MEDIUM — Can develop in parallel with Phase D

---

### **🟧 PHASE D — Feasibility (Bundle 2)**

**Goal:** Connect RMOS feasibility scoring to instrument geometry

**Dependencies:** Phase B (requires `RmosContext`)

**Tasks:**
1. 🆕 **Create stubs in `calculators/service.py`**
   - `compute_chipload_risk()` → stub returning score 75.0
   - `compute_heat_risk()` → stub returning score 75.0
   - `compute_deflection_risk()` → stub returning score 75.0
   - `compute_rimspeed_risk()` → stub returning score 75.0
   - `compute_bom_efficiency()` → stub returning score 75.0

2. 🆕 **Create `rmos/feasibility_fusion.py`**
   - `ToolSetup` dataclass
   - `PathSummary` dataclass
   - `FeasibilityResult` dataclass
   - `compute_feasibility_for_model_design()` → main scorer

3. 🆕 **Create `rmos/feasibility_router.py`** (optional)
   - `POST /api/rmos/feasibility/model/{model_id}`

**Files Created:**
```
services/api/app/
├── calculators/
│   └── service.py              # MODIFIED: Add stubs
└── rmos/
    ├── feasibility_fusion.py   # NEW
    └── feasibility_router.py   # NEW (optional)
```

**Success Criteria:**
- [ ] Feasibility endpoint returns aggregated score
- [ ] Stub calculators provide safe defaults
- [ ] Context adapter feeds instrument data to scorers
- [ ] Tests pass: `pytest tests/test_feasibility_fusion.py -v`

**Priority:** 🟡 MEDIUM — Stubs allow progress without full calculator unification

---

### **🟥 PHASE E — CAM Preview (Bundle 5)**

**Goal:** Provide fret slot CAM preview API endpoint

**Dependencies:** Phase C (requires `fretboard_geometry.py`)

**Tasks:**
1. 🆕 **Create `cam/fret_slots_router.py`**
   - `FretSlotsPreviewRequest` (Pydantic model, 21 fields)
   - `FretGeometryOut` (Pydantic response model)
   - `FretSlotsPreviewResponse` (full response with DXF/G-code)
   - `post_fret_slots_preview()` → main route handler

2. ✅ **Register in `main.py`:**
   ```python
   from app.cam.fret_slots_router import router as fret_slots_router
   app.include_router(fret_slots_router)
   ```

**Files Created:**
```
services/api/app/cam/
└── fret_slots_router.py    # NEW
```

**API Endpoint:**
```
POST /api/cam/fret_slots/preview
```

**Success Criteria:**
- [ ] Endpoint accepts standard and fan-fret modes
- [ ] Returns fret geometry + DXF + G-code in single response
- [ ] Works with all registered model presets
- [ ] Tests pass: `pytest tests/test_fret_slots_router.py -v`

**Priority:** 🟢 LOW — Nice-to-have for Art Studio integration

---

## 📋 Router Registration Strategy

**Question:** Should all routers register immediately?

**Answer:** ✅ **YES — Register all routers immediately with graceful degradation**

**Pattern:**
```python
# services/api/app/main.py

# Phase B: RMOS Context (optional)
try:
    from .rmos.context_router import router as rmos_context_router
    app.include_router(rmos_context_router)
except Exception as e:
    print(f"Warning: RMOS context router not available: {e}")
    rmos_context_router = None

# Phase D: Feasibility (optional)
try:
    from .rmos.feasibility_router import router as rmos_feasibility_router
    app.include_router(rmos_feasibility_router)
except Exception as e:
    print(f"Warning: RMOS feasibility router not available: {e}")
    rmos_feasibility_router = None

# Phase E: CAM Fret Slots (optional)
try:
    from .cam.fret_slots_router import router as fret_slots_router
    app.include_router(fret_slots_router)
except Exception as e:
    print(f"Warning: CAM fret slots router not available: {e}")
    fret_slots_router = None
```

**Benefits:**
- ✅ Routers return clean 404/500 errors until dependencies are ready
- ✅ API surface is documented even before full implementation
- ✅ Allows parallel development (frontend can mock responses)
- ✅ Standard FastAPI pattern for evolving projects

---

## 🎯 Integration Checklist

### **Phase A: Foundation** ✅
- [x] Wave 17 `GuitarModelSpec` confirmed authoritative
- [x] `model_spec.py` already exists with correct schema
- [x] `STANDARD_SCALE_PROFILES` defined
- [x] Example presets created (`STRAT_25_5_MODEL`, `LP_24_75_MODEL`)
- [ ] Create migration script for Bundle 4→Wave 17
- [ ] Add unit tests for model loader
- [ ] Document inch→mm conversion rules

### **Phase B: RMOS Connectivity**
- [ ] Create `rmos/context.py` with `RmosContext` class
- [ ] Create `rmos/context_adapter.py` (model_id → context)
- [ ] Optional: Create `rmos/context_router.py` (API endpoints)
- [ ] Register routers in `main.py`
- [ ] Add unit tests for context creation
- [ ] Document context payload structure

### **Phase C: Fretboard Geometry**
- [ ] Create `instrument_geometry/fretboard_geometry.py`
- [ ] Create `calculators/fret_slots_cam.py`
- [ ] Optional: Extend context adapter with fretboard data
- [ ] Add unit tests for fret calculations
- [ ] Add unit tests for DXF/G-code generation
- [ ] Document fretboard geometry API

### **Phase D: Feasibility**
- [ ] Create stubs in `calculators/service.py` (5 functions)
- [ ] Create `rmos/feasibility_fusion.py`
- [ ] Optional: Create `rmos/feasibility_router.py`
- [ ] Register router in `main.py`
- [ ] Add unit tests for feasibility scoring
- [ ] Document calculator stub behavior

### **Phase E: CAM Preview**
- [ ] Create `cam/fret_slots_router.py`
- [ ] Register router in `main.py`
- [ ] Add unit tests for preview endpoint
- [ ] Document API request/response format
- [ ] Create example client integration (Vue component)

---

## 🚀 Next Actions

### **Immediate (Today):**
1. ✅ Confirm Phase A completion (Wave 17 already done)
2. 🆕 Create `rmos/context.py` skeleton
3. 🆕 Create Phase B checklist in `WAVE17_TODO.md`

### **This Week:**
4. Complete Phase B (RMOS Context)
5. Start Phase C (Fretboard Geometry)
6. Document migration path for Bundle 4 users

### **Next Sprint:**
7. Complete Phase C & D in parallel
8. Add Phase E (CAM Preview)
9. Update API documentation (Swagger/OpenAPI)

---

## 📚 References

- [Wave 17 TODO](../WAVE17_TODO.md) - Neck Taper Suite integration
- [Wave 17 Model Spec](../services/api/app/instrument_geometry/model_spec.py) - Authoritative schema
- [AGENTS.md](../AGENTS.md) - Project structure and coding standards
- [CODING_POLICY.md](../CODING_POLICY.md) - Style guide and patterns

---

**Last Updated:** December 8, 2025  
**Authority Level:** 🏆 FINAL — No further reconciliation needed  
**Next Review:** After Phase B completion
