# Phase D-E Implementation Decisions
**Date:** December 10, 2025  
**Status:** Architectural Guidance  
**Context:** Post-deep-scan implementation strategy for uploaded Phases B-E

---

## 🎯 Executive Summary

After deep scan of 10 uploaded files (Phases B-E, Waves 15-16, tests, audit), discovered that **Phases B, C, and Wave 15 are already implemented** at Wave 17-19 maturity level. The uploads represent earlier iterations.

**What's Actually Needed:**
- ✅ **Phase D (Diagnostics)** — NEW feature, needs implementation
- ⚠️ **Phase E (Export)** — Enhancement to existing, needs merge strategy
- ✅ **Wave 16 (Fan-Fret UI)** — NEW feature, but can wait
- ✅ **Integration Tests** — NEW tests, create now
- ✅ **Tool Library Audit** — Process to run (light audit now, heavy later)

---

## 📋 Critical Questions & Recommendations

### 1️⃣ Phase D Calculators: Wrapper Strategy

**Question:** Do existing calculator functions match Phase D expectations? Create wrappers?

**Recommendation:** ✅ **Yes, create thin wrapper functions**

**Existing State:**
- Low-level calculators: `compute_chipload_risk()`, `estimate_deflection_mm()` in `calculators/service.py`
- These work but have inconsistent signatures

**Phase D Needs:**
- Stable, human-readable contract: `evaluate_cut_risks(params: CutContext) -> RiskReport`
- Consolidated risk scoring: "low", "medium", "high"

**Implementation Plan:**
```python
# services/api/app/calculators/service.py

@dataclass
class CutContext:
    """Unified context for risk evaluation."""
    tool: ToolProfile
    material: MaterialProfile
    cut_depth_mm: float
    cut_width_mm: float
    feed_rate_mmpm: float
    spindle_rpm: float

@dataclass
class RiskReport:
    """Consolidated risk assessment."""
    chipload_risk: Literal["low", "medium", "high"]
    heat_risk: Literal["low", "medium", "high"]
    deflection_risk: Literal["low", "medium", "high"]
    overall_risk: Literal["low", "medium", "high"]
    messages: List[str]

def evaluate_cut_risks(ctx: CutContext) -> RiskReport:
    """
    Phase D-friendly wrapper around existing calculators.
    
    Calls:
      - compute_chipload_risk() for chipload assessment
      - estimate_heat_risk() for thermal analysis (implement if missing)
      - estimate_deflection() for tool deflection
    
    Returns consolidated RiskReport with human-readable levels.
    """
    # Implementation calls existing low-level functions
    # but provides consistent interface
    pass
```

**Why Wrappers:**
- ✅ Preserves existing low-level math (don't break what works)
- ✅ Provides stable API for RMOS/UI consumption
- ✅ Easy to test independently
- ✅ Can evolve low-level functions without breaking Phase D

**Action Items:**
- [ ] Add `CutContext` and `RiskReport` dataclasses
- [ ] Implement `evaluate_cut_risks()` wrapper
- [ ] Check if `estimate_heat_risk()` exists (may need implementation)
- [ ] Add tests for wrapper function

---

### 2️⃣ Phase E Architecture: DXF/G-code Export Strategy

**Question:** Keep coupled in `fret_slots_cam.py` OR extract to `fret_slots_export.py` OR enhance existing?

**Recommendation:** 🎯 **Option C: Enhance existing with internal structure**

**Current State:**
- `calculators/fret_slots_cam.py` (912 lines) has DXF + G-code generation embedded
- Works, generates DXF R12 and GRBL G-code
- Tightly coupled: geometry calculation → export in same function flow

**Upload Proposes:**
- Separate `cam/fret_slots_export.py` module
- Support for DXF R12, R14, R18 (multiple versions)
- `FretSlotsGcodeParams` for configurable feeds

**Decision: Enhance Existing, Structure Internally**

**Implementation Plan:**
```python
# services/api/app/calculators/fret_slots_cam.py

# === Layer 1: Geometry Calculation (Pure) ===
def compute_fret_slots_for_model(
    model_id: str,
    fret_count: int,
    slot_depth_mm: float,
    slot_width_mm: float,
) -> List[FretSlotToolpath]:
    """Pure geometry computation, no export logic."""
    pass

# === Layer 2: Export Helpers (Internal) ===
def _generate_dxf_r12(slots: List[FretSlotToolpath]) -> str:
    """DXF R12 export (existing)."""
    pass

def _generate_dxf_r14(slots: List[FretSlotToolpath]) -> str:
    """DXF R14 export (NEW - add if needed)."""
    pass

def _generate_svg(slots: List[FretSlotToolpath]) -> str:
    """SVG export (existing or add)."""
    pass

def _generate_gcode_for_post(
    slots: List[FretSlotToolpath],
    post_id: str,
    params: FretSlotsGcodeParams,
) -> str:
    """G-code export with post-processor awareness."""
    pass

# === Layer 3: Public API (FastAPI Endpoints) ===
@router.post("/preview")
async def preview_fret_slots(...):
    """Returns JSON preview + geometry."""
    slots = compute_fret_slots_for_model(...)
    return {"toolpaths": slots, ...}

@router.post("/export_multi_post")
async def export_multi_post(...):
    """Returns ZIP with DXF + SVG + N × NC files."""
    slots = compute_fret_slots_for_model(...)
    dxf = _generate_dxf_r12(slots)
    svg = _generate_svg(slots)
    gcode_files = {
        post_id: _generate_gcode_for_post(slots, post_id, params)
        for post_id in request.post_ids
    }
    return create_zip(dxf, svg, gcode_files)
```

**Why This Approach:**
- ✅ Keeps everything in one file for now (easier to navigate)
- ✅ Clear internal separation (geometry vs export)
- ✅ Easy to extract later if it grows (just move `_generate_*` functions)
- ✅ Doesn't break existing endpoints
- ✅ Supports multi-format export without major refactor

**When to Extract:**
- If `fret_slots_cam.py` exceeds 1500 lines
- If export logic becomes complex (e.g., custom post-processor scripts)
- If other CAM modules need same export helpers (DRY violation)

**Action Items:**
- [ ] Refactor `fret_slots_cam.py` into 3 internal layers
- [ ] Add `_generate_dxf_r14()` and `_generate_dxf_r18()` if needed
- [ ] Add `FretSlotsGcodeParams` dataclass
- [ ] Ensure `/export_multi_post` endpoint exists and works

---

### 3️⃣ Wave 16 Priority: Fan-Fret Timing

**Question:** Is fan-fret support critical now?

**Recommendation:** 🚦 **Fan-fret can wait until straight pipeline is stable**

**Current Pipeline Status:**
- ✅ Instrument model registry exists
- ✅ Neck taper + DXF export working
- 🔄 Straight-fret CAM working but needs Phase D (diagnostics)
- ❌ RMOS feasibility UI integration incomplete
- ❌ Fan-fret angles per fret not implemented

**Fan-Fret Complexity:**
- Requires: Multi-scale bridge math, angled fret geometry, per-fret angle calculation
- Affects: CAM toolpath generation, DXF export, feasibility UI (color-coded frets)
- Risk: High complexity before core pipeline is proven

**Strategy:**
1. **Phase 1 (Now):** Stabilize straight-fret pipeline
   - Benedetto 17" straight → full CAM path → DXF/G-code → RMOS diagnostics → UI
   - Get Phase D working with straight frets first
   - Prove feasibility scoring works for simple case

2. **Phase 2 (Later):** Add fan-fret support
   - After straight pipeline is production-ready
   - Implement `compute_fan_fret_positions()` in `instrument_geometry`
   - Add UI controls in Wave 16
   - Test with multi-scale models

**Design Hooks (Keep in Place):**
```python
# Already in router signature:
mode: Literal['standard', 'fan'] = Field('standard')
treble_scale_mm: Optional[float] = None
bass_scale_mm: Optional[float] = None
perpendicular_fret: Optional[int] = None
```

**Action Items:**
- [ ] Document fan-fret as "future feature" in quickref
- [ ] Keep `mode` parameter but validate `mode == 'standard'` for now
- [ ] Add TODO comments where fan-fret logic would go
- [ ] Prioritize Phase D (straight-fret diagnostics) first

---

### 4️⃣ Tool Library Audit: Timing Strategy

**Question:** Audit NOW or after Phase D/E?

**Recommendation:** ⚖️ **Light audit NOW, heavy audit LATER**

**Why Audit Matters:**
- Tool Library exists: `services/api/app/data/tool_library.json`
- Loader exists: `load_tool_library()` in `data/tool_library.py`
- Risk: New CAM code might hard-code `diameter_mm`, `rpm`, `feed_mm_min`

**Light Audit (NOW):**
```powershell
# Find obvious hard-coded tool usage in new code
grep -r "diameter_mm.*=.*[0-9]" services/api/app/calculators/
grep -r "rpm.*=.*[0-9]{4,}" services/api/app/calculators/
grep -r "feed_mm_min.*=.*[0-9]" services/api/app/calculators/

# Check fret_slots_cam.py specifically
grep "18000\|12000\|0.58\|3.0" services/api/app/calculators/fret_slots_cam.py
```

**Fix Obvious Cases:**
```python
# BEFORE (hard-coded):
spindle_rpm = 18000  # ❌ magic number
slot_width_mm = 0.58  # ❌ magic number

# AFTER (tool library):
tool = get_tool_by_id("fret_saw_std")  # ✅ from tool library
spindle_rpm = tool.default_rpm
slot_width_mm = tool.kerf_mm
```

**Heavy Audit (LATER - After Phase D/E):**
- Run full audit checklist (8 sections)
- Search entire `calculators/`, `rmos/`, `saw_lab/` directories
- Refactor all hard-coded tools to use `tool_id`
- Update frontend to fetch tools from `/api/tooling/tools`

**Action Items:**
- [ ] Run light audit PowerShell script
- [ ] Fix any egregious hard-coded tools in `fret_slots_cam.py`
- [ ] Document findings in `TOOL_LIBRARY_AUDIT_FINDINGS.md`
- [ ] Schedule heavy audit for after Phase D/E integration

---

### 5️⃣ Testing Strategy: Stubs vs Post-Implementation

**Question:** Create test stubs NOW or after implementation?

**Recommendation:** 🧪 **Create stubs NOW, expand as we implement**

**Why Stubs First:**
- Prevents accidental renames (e.g., `compute_fret_slots` → `generate_fret_slots`)
- Guards against broken imports during refactoring
- Provides scaffold for TDD approach
- Catches missing dependencies early

**Stub Test Pattern:**
```python
# services/api/app/tests/test_fret_slots_cam_stubs.py

def test_fret_slots_cam_imports():
    """Guard against import breakage."""
    from app.calculators.fret_slots_cam import (
        generate_fret_slot_cam,
        FretSlotToolpath,
        FretSlotCAMOutput,
    )
    assert generate_fret_slot_cam is not None
    assert FretSlotToolpath is not None
    assert FretSlotCAMOutput is not None

def test_fret_slots_preview_endpoint_exists():
    """Verify router wiring."""
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    # Don't care about success, just that endpoint exists
    resp = client.post("/api/cam/fret_slots/preview", json={
        "model_id": "benedetto_17",
        "fret_count": 22,
    })
    assert resp.status_code in (200, 422)  # 422 = validation error (OK for stub)
```

**Expand as We Implement:**
```python
# After Phase D is implemented:
def test_per_fret_diagnostics_integration():
    """Verify Phase D diagnostics work end-to-end."""
    client = TestClient(app)
    resp = client.post("/api/rmos/fret_slots/diagnostics", json={
        "model_id": "benedetto_17",
        "fret_count": 22,
        "slot_depth_mm": 3.0,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "diagnostics" in data
    assert len(data["diagnostics"]) == 22  # one per fret
    assert data["diagnostics"][0]["risk_level"] in ["low", "medium", "high"]
```

**Action Items:**
- [ ] Create `test_fret_slots_cam_stubs.py` NOW
- [ ] Create `test_phase_d_diagnostics_stubs.py` NOW
- [ ] Add real assertions as Phase D is implemented
- [ ] Run tests after each implementation step

---

## 🗓️ Implementation Sequence

### **Wave 1: Foundation & Tests** (This Week)
1. ✅ Apply PATCH_N11_SCHEMA_FIX
2. ✅ Create rosette router tests (`test_rosette_patterns_router.py`)
3. ✅ Update AGENTS.md with fret slots CAM section
4. [ ] Create test stubs for fret slots CAM
5. [ ] Run light tool library audit
6. [ ] Commit as `patch/n11_rosette_schema_fix_and_tests`

### **Wave 2: Phase D Diagnostics** (Next Week)
1. [ ] Create `RiskReport` and `CutContext` dataclasses
2. [ ] Implement `evaluate_cut_risks()` wrapper
3. [ ] Check/implement `estimate_heat_risk()` if missing
4. [ ] Create `rmos/fret_diagnostics.py` module
5. [ ] Create `rmos/fret_diagnostics_router.py`
6. [ ] Register router in `main.py`
7. [ ] Expand test stubs with real assertions
8. [ ] Test with Benedetto 17" straight frets

### **Wave 3: Phase E Export Enhancement** (After Phase D)
1. [ ] Refactor `fret_slots_cam.py` into 3 layers
2. [ ] Add `FretSlotsGcodeParams` dataclass
3. [ ] Add `_generate_dxf_r14()` if needed
4. [ ] Ensure `/export_multi_post` endpoint works
5. [ ] Test multi-post export (GRBL, Mach4, LinuxCNC)

### **Wave 4: Heavy Tool Audit** (After Phase E)
1. [ ] Run full 8-section audit checklist
2. [ ] Document all hard-coded tool references
3. [ ] Refactor to use `get_tool_by_id()`
4. [ ] Update frontend tool fetching

### **Wave 5: Fan-Fret Support** (Future)
1. [ ] Implement `compute_fan_fret_positions()`
2. [ ] Add Wave 16 UI controls
3. [ ] Test with multi-scale models

---

## 📊 Success Metrics

### Phase D Complete When:
- ✅ `/api/rmos/fret_slots/diagnostics` endpoint returns per-fret risks
- ✅ Risk levels ("low", "medium", "high") match calculator outputs
- ✅ Tests cover chipload/heat/deflection integration
- ✅ UI can consume and display risk colors

### Phase E Complete When:
- ✅ `/api/cam/fret_slots/export_multi_post` returns ZIP with DXF + SVG + NC files
- ✅ Supports at least 3 post-processors (GRBL, Mach4, LinuxCNC)
- ✅ DXF R12 format validated
- ✅ G-code includes correct post headers/footers

### Tool Audit Complete When:
- ✅ No hard-coded tool diameters in `calculators/`
- ✅ No hard-coded RPMs in `rmos/`
- ✅ All CAM modules use `get_tool_by_id()`
- ✅ Frontend fetches tools from `/api/tooling/tools`

---

## 🔗 References

- **Uploaded Files:** Phases B-E, Waves 15-16, Integration Tests, Tool Audit Checklist
- **Existing Implementations:** `rmos/context.py`, `calculators/fret_slots_cam.py`, `routers/cam_fret_slots_router.py`
- **Tool Library:** `data/tool_library.json`, `data/tool_library.py`
- **N11 Schema Fix:** `PATCH_N11_SCHEMA_FIX.md`

---

**Status:** ✅ Ready for Wave 1 implementation  
**Next Action:** Create test stubs and run light tool audit
