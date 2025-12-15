# Wave E1 CAM Section - Detailed Analysis & Integration Assessment

**Date:** December 12, 2025  
**Scope:** RMOS Patterns + Saw-Ops Router Integration  
**Status:** ⚠️ **PARTIALLY IMPLEMENTED - NEEDS EVALUATION**

---

## 📋 Executive Summary

Wave E1 introduces **RMOS Patterns and Saw Operations** endpoints to bridge the gap between rosette design (Art Studio) and manufacturing execution (Saw Lab). The file you provided (`Wave E1.txt`) is a **code bundle specification** that defines the implementation plan for:

1. **Rosette Pattern CRUD API** (`/api/rosette-patterns`)
2. **Saw Slice Preview** (`/rmos/saw-ops/slice/preview`)
3. **Pipeline Handoff** (`/rmos/saw-ops/pipeline/handoff`)

**Current Implementation Status:**
- ✅ **Routers EXIST** (both `rmos_patterns_router.py` and `rmos_saw_ops_router.py`)
- ✅ **Models EXIST** (`services/api/app/rmos/models/pattern.py`)
- ✅ **Registered in main.py** (Wave E1 section exists)
- ⚠️ **DIVERGENCE DETECTED** (implementation differs from Wave E1 spec)
- ❌ **In-memory store** (Wave E1 spec) vs. **SQLite store** (actual implementation)

---

## 🔍 Deep Dive Analysis

### **1. What Wave E1.txt Proposes**

The specification document outlines a **minimal, test-ready implementation** with:

#### **A. Data Model** (`services/api/app/rmos/models/pattern.py`)
```python
class RosettePattern(BaseModel):
    pattern_id: str
    pattern_name: str
    description: Optional[str]
    outer_radius_mm: float
    inner_radius_mm: float
    ring_count: int
    rings: List[RosetteRing] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]
```

**Purpose:** Generic rosette pattern definition for RMOS-level operations (not Art Studio geometry).

#### **B. In-Memory Store** (`services/api/app/stores/rmos_stores.py`)
```python
_GLOBAL_RMOS_STORES: Dict[str, Any] = {
    "patterns": [],  # List[RosettePattern]
}

def get_rmos_stores() -> Dict[str, Any]:
    return _GLOBAL_RMOS_STORES
```

**Why In-Memory?**
- Fast to implement (no SQLite dependency)
- Easy to test (no DB setup in CI)
- Swappable later (interface stays the same)

#### **C. Patterns Router** (`services/api/app/routers/rmos_patterns_router.py`)
```python
router = APIRouter(prefix="/rosette-patterns", tags=["RMOS", "Patterns"])

@router.get("/")  # List patterns
@router.post("/")  # Create pattern
@router.get("/{pattern_id}")  # Get pattern
@router.put("/{pattern_id}")  # Update pattern
@router.delete("/{pattern_id}")  # Delete pattern
```

**Key Design:** Direct access to in-memory list, no ORM.

#### **D. Saw-Ops Router** (`services/api/app/routers/rmos_saw_ops_router.py`)
```python
router = APIRouter(prefix="/saw-ops", tags=["RMOS", "Saw Operations"])

@router.post("/slice/preview")  # Generate slice preview
@router.post("/pipeline/handoff")  # Queue CAM job
```

**Stub Behavior:**
- `/slice/preview` → Returns lightweight preview with:
  - Estimated path length (circle/arc/polyline formulas)
  - Rough time estimate (`length / feed_rate`)
  - Stub SVG visualization
  - Warnings if feed rate missing
- `/pipeline/handoff` → Returns synthetic job ID (`saw_job_{uuid}`) with "queued" status

#### **E. Main.py Wiring**
```python
app.include_router(rmos_patterns_router.router, prefix="/api")   # → /api/rosette-patterns
app.include_router(rmos_saw_ops_router.router, prefix="/rmos")   # → /rmos/saw-ops
```

**Critical:** Prefix layering ensures paths match test expectations.

---

### **2. What Actually Exists in the Repo**

#### **A. Actual Patterns Router** (`services/api/app/routers/rmos_patterns_router.py`)

**Key Differences:**
```python
# ACTUAL IMPLEMENTATION (lines 20-50)
stores = get_rmos_stores()
pattern_dicts = stores.patterns.list_all()  # ❌ Uses .patterns.list_all() method
patterns = [RosettePattern(**p) for p in pattern_dicts]  # ❌ Expects dict return

# Create endpoint:
pattern_dict = pattern.dict()
pattern_dict['id'] = pattern_dict.pop('pattern_id')  # ❌ Remaps pattern_id → id
pattern_dict['pattern_type'] = 'rosette'  # ❌ Adds pattern_type field
stores.patterns.create(pattern_dict)  # ❌ Uses .create() method
```

**Findings:**
1. **Store interface is different** (has `.list_all()`, `.create()`, `.get_by_id()` methods)
2. **Schema mapping occurs** (`pattern_id` → `id`, adds `pattern_type`)
3. **Returns SQLite dicts**, not Pydantic models directly

**This suggests:** A **SQLite-backed store** was implemented instead of the in-memory store from Wave E1.

#### **B. Actual Saw-Ops Router** (`services/api/app/routers/rmos_saw_ops_router.py`)

**Matches Wave E1 spec closely:**
```python
# Lines 1-132 match the specification almost exactly
def _estimate_path_length_mm(geometry: Dict[str, Any]) -> float:
    # Same circle/arc/polyline logic as spec
    
@router.post("/slice/preview", response_model=SlicePreviewResponse)
async def preview_slice(request: SlicePreviewRequest):
    # Same stub implementation as spec
```

**Status:** ✅ **IMPLEMENTED AS DESIGNED**

#### **C. Main.py Registration**

**Actual code** (lines 844-850):
```python
# Wave E1: RMOS Patterns + Saw-Ops
if rmos_patterns_router:
    app.include_router(rmos_patterns_router, prefix="/api", tags=["RMOS", "Patterns"])

if rmos_saw_ops_router:
    app.include_router(rmos_saw_ops_router, prefix="/rmos", tags=["RMOS", "Saw Operations"])
```

**Status:** ✅ **WIRED CORRECTLY**

---

### **3. CAM Section Inventory**

The `services/api/app/cam/` directory contains **23 modules** implementing various CAM operations:

#### **Core CAM Engines:**
1. **adaptive_core.py** - L.0 adaptive pocketing (legacy)
2. **adaptive_core_l1.py** - L.1 robust pyclipper offsetting
3. **adaptive_core_l2.py** - L.2 spiralizer + adaptive stepover
4. **adaptive_spiralizer_utils.py** - L.2 curvature tools
5. **trochoid_l3.py** - L.3 trochoidal insertion
6. **feedtime_l3.py** - L.3 jerk-aware time estimation
7. **feedtime.py** - Classic time estimation
8. **stock_ops.py** - Material removal calculations

#### **Helical & Retract Patterns:**
9. **helical_core.py** - Helical ramping operations
10. **retract_patterns.py** - Safe Z-axis retraction
11. **probe_patterns.py** - Probe toolpaths
12. **probe_svg.py** - Probe visualization

#### **Geometry & Validation:**
13. **dxf_advanced_validation.py** - DXF file validation
14. **dxf_limits.py** - DXF constraint checking
15. **dxf_preflight.py** - Pre-import validation
16. **dxf_upload_guard.py** - Upload safety checks
17. **polygon_offset_n17.py** - Polygon offsetting (N17 version)
18. **contour_reconstructor.py** - Contour path reconstruction
19. **spatial_hash.py** - Spatial indexing
20. **graph_algorithms.py** - Graph-based path planning

#### **Optimization & Analysis:**
21. **energy_model.py** - Energy consumption modeling
22. **heat_timeseries.py** - Heat accumulation tracking
23. **time_estimator_v2.py** - V2 time estimation
24. **modal_cycles.py** - Modal G-code cycle detection
25. **whatif_opt.py** - What-if optimization scenarios

#### **Rosette-Specific CAM:**
26. **cam/rosette/** - Rosette manufacturing subsystem (14 modules):
    - `pattern_generator.py` - Pattern generation engine
    - `ring_engine.py` - Ring geometry engine
    - `slice_engine.py` - Slice computation (N12 skeleton)
    - `segmentation_engine.py` - Tile segmentation
    - `kerf_engine.py` - Kerf compensation
    - `kerf_compensation.py` - Kerf adjustment logic
    - `twist_engine.py` - Twist angle calculations
    - `herringbone.py` - Herringbone pattern support
    - `preview_engine.py` - Preview generation
    - `photo_converter.py` - Photo-to-rosette conversion
    - `saw_batch_generator.py` - Batch saw operation generation
    - `tile_segmentation.py` - Advanced tile segmentation
    - `rosette_cnc_wiring.py` - CNC integration wiring
    - `cnc/` - CNC-specific rosette operations

27. **cam_preview_router.py** - CAM preview API endpoint

---

### **4. Key Architectural Concerns**

#### **A. Store Implementation Mismatch**

**Wave E1 Spec:**
```python
_GLOBAL_RMOS_STORES: Dict[str, Any] = {
    "patterns": [],  # type: List[RosettePattern]
}
```

**Actual Implementation:**
```python
# Implies a store with methods like:
stores.patterns.list_all()  # Returns List[Dict]
stores.patterns.create(dict)  # Insert pattern
stores.patterns.get_by_id(str)  # Query pattern
```

**Question 1:** Where is the actual `rmos_stores.py` implementation?  
**Question 2:** Was a SQLite store created instead? If so, where's the schema?  
**Question 3:** Does the in-memory fallback still exist for testing?

#### **B. Rosette Pattern Schema Fragmentation**

**Multiple definitions found:**
1. `services/api/app/rmos/models/pattern.py` - **RosettePattern** (Wave E1 RMOS-level)
2. `services/api/app/schemas/rosette_pattern.py` - **RosettePatternBase/Create/Update/InDB** (App-level)
3. `services/api/app/cam/rosette/models.py` - **RosetteRingConfig, Slice, etc.** (CAM-level)

**Question 4:** Which schema is authoritative for which use case?  
**Question 5:** How do these schemas map to each other?  
**Question 6:** Is there a migration path between them?

#### **C. Multiple Rosette APIs**

**Found 3 separate rosette pattern endpoints:**
1. `/api/rosette-patterns` - **rmos_patterns_router.py** (Wave E1)
2. `/rmos/rosette/patterns` - **rmos_pattern_api.py** (N11.1)
3. `/api/patterns` - **rosette_patterns.py** (legacy?)

**Question 7:** Are these intentionally separate or duplicates?  
**Question 8:** What's the migration/consolidation plan?  
**Question 9:** Which one should UI clients use?

#### **D. Saw-Ops Integration Depth**

**Current implementation is a "stub":**
```python
# From rmos_saw_ops_router.py (lines 60-70)
toolpath: List[Dict[str, Any]] = [
    {
        "x": 0.0, "y": 0.0, "z": -float(request.cut_depth_mm),
        "feed_mm_min": feed,
        "comment": "Stub preview move – replace with real Saw Lab path planning.",
    }
]
```

**Real Saw Lab exists:**
- `services/api/app/cam/rosette/slice_engine.py` - **Slice geometry computation**
- `services/api/app/cam/rosette/saw_batch_generator.py` - **Batch saw operations**
- `toolpath_saw_engine.py` (root level) - **plan_saw_toolpaths_for_design()**

**Question 10:** Why isn't the stub connected to the real slice engine?  
**Question 11:** What's the integration timeline for real saw planning?  
**Question 12:** Are there safety concerns with stub-only implementations?

---

### **5. Testing Infrastructure**

**Test scripts mentioned in Wave E1.txt:**
- `scripts/Test-RMOS-Sandbox.ps1` - Pattern creation test
- `scripts/Test-RMOS-SlicePreview.ps1` - Slice preview test  
- `scripts/Test-RMOS-PipelineHandoff.ps1` - Pipeline handoff test

**Question 13:** Do these tests pass with the current implementation?  
**Question 14:** Are there pytest equivalents in `services/api/app/tests/`?  
**Question 15:** Is there CI coverage for Wave E1 endpoints?

---

### **6. Pipeline Handoff Architecture**

**Wave E1 Stub:**
```python
job_id = f"saw_job_{uuid.uuid4().hex[:12]}"
return PipelineHandoffResponse(
    job_id=job_id,
    pattern_id=request.pattern_id,
    status="queued",
    message=f"Pattern {request.pattern_id} queued..."
)
```

**Real Pipeline Found:**
- **Rosette Manufacturing Plan.txt** describes full pipeline handoff system
- **toolpath_saw_engine.py** has `plan_saw_toolpaths_for_design()` returning `RmosToolpathPlan`
- **FULL_ROSETTE_MANUFACTURING_OS_SANDBOX.txt** shows batch preview endpoint

**Question 16:** Is there a queue/job system that reads these job IDs?  
**Question 17:** How does the handoff connect to JobLog?  
**Question 18:** Where are queued jobs stored (`exports/rmos_handoff/`)?

---

## 🎯 Critical Questions for User

### **Immediate Clarification Needed:**

1. **Which store implementation is canonical?**
   - In-memory list (Wave E1 spec)
   - SQLite store (actual implementation)
   - Both (conditional based on environment)?

2. **What's the relationship between the 3 rosette pattern APIs?**
   - `/api/rosette-patterns` (Wave E1)
   - `/rmos/rosette/patterns` (N11.1)
   - `/api/patterns` (legacy)
   - Should they be consolidated?

3. **Why is saw-ops still a stub?**
   - Real slice engines exist in `cam/rosette/`
   - Is there a blocker preventing integration?
   - What's the timeline for wiring them together?

4. **Where is the actual `rmos_stores.py` file?**
   - The routers reference it, but implementation seems different from spec
   - Is it in a different location than `services/api/app/stores/`?

5. **Are Wave E1 tests passing?**
   - Do `Test-RMOS-*.ps1` scripts work?
   - Are there pytest equivalents?
   - What's the CI coverage?

### **Architectural Decisions Needed:**

6. **Schema consolidation strategy:**
   - Which RosettePattern definition should be primary?
   - How to map between RMOS-level and CAM-level schemas?
   - Migration path for existing data?

7. **Pipeline handoff implementation:**
   - Should stub be replaced immediately or incrementally?
   - How to integrate with existing JobLog system?
   - Queue storage mechanism (DB, filesystem, Redis)?

8. **API versioning:**
   - Are multiple rosette endpoints intentional (v1/v2 strategy)?
   - Deprecation plan for older endpoints?
   - Client migration guide?

### **Safety & Testing:**

9. **What happens if stub endpoints are used in production?**
   - Are there guards preventing real manufacturing?
   - Warning system for stub vs. real implementations?

10. **Integration testing strategy:**
    - End-to-end test from pattern creation → saw handoff?
    - Mock vs. real saw lab in tests?
    - Performance testing for batch operations?

---

## 📊 Integration Readiness Assessment

### **✅ GREEN (Ready to Use):**
- ✅ Saw-ops router endpoints functional (stub implementation)
- ✅ Pattern CRUD API wired correctly
- ✅ Main.py registration complete
- ✅ Models defined and importable

### **⚠️ YELLOW (Needs Clarification):**
- ⚠️ Store implementation diverges from spec (in-memory vs. SQLite)
- ⚠️ Multiple rosette pattern APIs with unclear relationships
- ⚠️ Schema fragmentation across 3+ definitions
- ⚠️ Stub implementations not connected to real engines

### **❌ RED (Blocking Issues):**
- ❌ Missing `rmos_stores.py` matching Wave E1 spec
- ❌ No integration tests for E2E pattern → saw handoff flow
- ❌ Pipeline handoff queue system not evident
- ❌ Saw preview not using real slice engine

---

## 🚀 Recommended Next Steps

### **Immediate (This Week):**

1. **Locate/verify store implementation:**
   ```bash
   # Find the actual rmos_stores.py
   grep -r "get_rmos_stores" services/api/app/
   ```

2. **Run existing tests:**
   ```powershell
   .\scripts\Test-RMOS-Sandbox.ps1 -Verbose
   .\scripts\Test-RMOS-SlicePreview.ps1 -Verbose
   .\scripts\Test-RMOS-PipelineHandoff.ps1 -Verbose
   ```

3. **Document schema relationships:**
   - Create mapping diagram between the 3 RosettePattern definitions
   - Identify primary/secondary/deprecated schemas

### **Short-Term (This Month):**

4. **Connect saw-ops stub to real engines:**
   ```python
   # In rmos_saw_ops_router.py, replace stub with:
   from ..cam.rosette.slice_engine import generate_slices_for_ring
   from ..cam.rosette.saw_batch_generator import create_saw_batch
   ```

5. **Consolidate rosette pattern APIs:**
   - Choose canonical endpoint (`/api/rosette-patterns` recommended)
   - Deprecate or proxy others
   - Update client code

6. **Implement queue storage:**
   - If using filesystem: Create `exports/rmos_handoff/` directory
   - If using DB: Add job queue table
   - If using Redis: Add queue service

### **Medium-Term (Next Quarter):**

7. **E2E integration tests:**
   ```python
   # pytest test covering:
   # 1. Create pattern → 2. Preview slice → 3. Handoff → 4. Check queue
   ```

8. **Schema migration tools:**
   - Create utilities to convert between schema versions
   - Add validation layers at API boundaries

9. **Production readiness audit:**
   - Replace all stub implementations
   - Add safety guards
   - Performance testing

---

## 📝 Wave E1 Implementation Gap Summary

| Component | Spec | Actual | Status | Action |
|-----------|------|--------|--------|--------|
| `rmos_patterns_router.py` | In-memory list | SQLite store methods | ⚠️ | Verify store |
| `rmos_saw_ops_router.py` | Stub implementation | Stub implementation | ✅ | Connect real engine |
| `rmos_stores.py` | Simple dict store | Not found at spec location | ❌ | Locate or create |
| Pattern models | Single definition | 3+ definitions | ⚠️ | Consolidate |
| Saw preview | Stub math | Stub math | ⚠️ | Wire to slice_engine |
| Pipeline handoff | UUID + "queued" | UUID + "queued" | ✅ | Add queue storage |
| Main.py wiring | `/api` + `/rmos` | `/api` + `/rmos` | ✅ | No action |
| Tests | 3 PowerShell scripts | Unknown status | ❓ | Run and report |

---

## 🔗 Related Documentation

- **GCODE_GENERATION_SYSTEMS_ANALYSIS.md** - G-code subsystem overview
- **CALCULATORS_DIRECTORY_ANALYSIS.md** - Calculator modules analysis
- **LTB_CALCULATOR_DEPLOYMENT_SUMMARY.md** - Recent calculator integration
- **ADAPTIVE_POCKETING_MODULE_L.md** - Adaptive CAM documentation
- **REPOSITORY_ERROR_ANALYSIS.md** - Error diagnostics (mentions Wave E1)
- **TEST_STATUS_REPORT.md** - Test coverage (includes Wave E1 tests)
- **Rosette Manufacturing Plan.txt** - Full manufacturing system spec
- **FULL_ROSETTE_MANUFACTURING_OS_SANDBOX.txt** - Sandbox implementation

---

## 💡 Design Philosophy Insights

Wave E1 follows a **"stub-first, wire-later" pattern**:

1. **Define interfaces early** (models, request/response contracts)
2. **Implement minimal stubs** (return synthetic data)
3. **Pass integration tests** (routes exist, return valid shapes)
4. **Wire real engines incrementally** (replace stubs with production code)

**Pros:**
- ✅ Unblocks frontend development immediately
- ✅ Allows API contract testing before heavy CAM work
- ✅ Reduces merge conflicts (small, focused PRs)

**Cons:**
- ⚠️ Risk of stub code reaching production
- ⚠️ Integration points may drift from spec
- ⚠️ Testing complexity (mock vs. real implementations)

---

## 🎯 Final Recommendations

**For immediate work:**
1. Run the 3 PowerShell tests and report results
2. Locate the actual `rmos_stores.py` implementation
3. Document which rosette pattern API is primary

**For code quality:**
4. Add integration tests covering full E2E flow
5. Wire saw-ops stub to real slice engine
6. Consolidate schema definitions

**For production readiness:**
7. Implement job queue storage
8. Add safety guards around stub endpoints
9. Create migration guide for schema evolution

---

**Status:** ⚠️ **Wave E1 is ~60% implemented** - routers exist and are wired, but store implementation diverges from spec and saw-ops endpoints are still stubs despite real engines existing in the codebase.

**Next Action:** User needs to clarify store implementation strategy and decide whether to continue with SQLite or revert to in-memory as originally spec'd.
