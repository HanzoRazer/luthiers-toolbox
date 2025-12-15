# Wave 17→18 Integration Implementation Plan

**Date:** December 9, 2025  
**Status:** 🚀 READY TO EXECUTE  
**Based On:** Your authoritative reconciliation answers

---

## 🎯 Current State Assessment

### **✅ What Already Exists (Verified)**

#### **Phase B: RmosContext System — COMPLETE** 🎉
- ✅ `rmos/context.py` (532 lines) — RmosContext, MaterialProfile, SafetyConstraints
- ✅ `rmos/context_adapter.py` (329 lines) — build_rmos_context_for_model()
- ✅ `rmos/context_router.py` (262 lines) — 5 FastAPI endpoints
- ✅ Material database: 11 wood species with density/hardness
- ✅ Test script: `test_phase_b_context.ps1` (150 lines)
- ✅ Registered in main.py with graceful degradation

#### **Wave 17: Model Specification — COMPLETE** ✅
- ✅ `instrument_geometry/model_spec.py` (316 lines) — GuitarModelSpec IS AUTHORITATIVE
- ✅ `instrument_geometry/models.py` (288 lines) — InstrumentModelId enum (19 models)
- ✅ `instrument_geometry/neck/fret_math.py` (261 lines) — Fret position calculations
- ✅ `instrument_geometry/neck_taper/` — Complete taper math + DXF export

#### **Calculators: Service Facade — MOSTLY COMPLETE** 🟡
- ✅ `calculators/service.py` (401 lines) — CalculatorService class
- ✅ Router/Saw mode switching
- ✅ Methods: check_chipload_feasibility(), check_heat_dissipation(), etc.
- ⚠️ Missing: Top-level wrapper functions for API compatibility

#### **Unit System — CONFIRMED STANDARD** ✅
- ✅ JSON stores inches (luthier-friendly)
- ✅ Python uses millimeters (physics/CNC standard)
- ✅ Conversion happens at loader boundary
- ✅ Already implemented in model_spec.py

---

## 🚧 What Needs To Be Created

### **CRITICAL PATH TO WAVE 15-16 UI:**

```
Action 1: scale_intonation.py shim (5 min)
    ↓
Action 2: Calculator API wrappers (30 min)
    ↓
Phase C: Fretboard CAM (2-3 hrs) ← YOU ARE HERE
    ↓
Phase D: Feasibility Fusion (3-4 hrs)
    ↓
Phase E: CAM Preview Router (2-3 hrs)
    ↓
Wave 15: UI Foundation (3-4 hrs)
    ↓
Wave 16: UI Enhancements (1-2 hrs)
```

---

## 📝 ACTION 1: Create scale_intonation.py Compatibility Shim

**Priority:** 🟢 TRIVIAL (5 minutes)  
**File:** `services/api/app/instrument_geometry/scale_intonation.py`  
**Reason:** Expected import path for bundles, but logic already exists in `neck/fret_math.py`

### Implementation:
```python
"""
Scale & Intonation Calculations

Compatibility shim for expected import paths.
All logic implemented in instrument_geometry.neck.fret_math

Wave 17→18 Integration: This module provides backward-compatible
imports for code expecting scale_intonation.py

Usage:
    from instrument_geometry.scale_intonation import compute_fret_positions_mm
    positions = compute_fret_positions_mm(648.0, 22)  # Fender 25.5" scale
"""

from .neck.fret_math import (  # noqa: F401
    compute_fret_positions_mm,
    compute_fret_spacing_mm,
    SEMITONE_RATIO,
)

__all__ = [
    "compute_fret_positions_mm",
    "compute_fret_spacing_mm",
    "SEMITONE_RATIO",
]
```

### Test:
```powershell
python -c "from services.api.app.instrument_geometry.scale_intonation import compute_fret_positions_mm; print(len(compute_fret_positions_mm(648.0, 22)))"
# Expected: 22
```

---

## 📝 ACTION 2: Add Calculator API Wrappers

**Priority:** 🟡 REQUIRED FOR PHASE D (30 minutes)  
**File:** `services/api/app/calculators/service.py` (append to end)  
**Reason:** Bundle 2 (Feasibility Fusion) expects top-level functions

### Implementation:
Add these 5 functions to the END of `calculators/service.py`:

```python
# ---------------------------------------------------------------------------
# Public API Wrappers (Wave 17→18 Integration)
# ---------------------------------------------------------------------------
# These thin wrappers provide top-level functions for RMOS feasibility API
# while delegating to the CalculatorService class for actual logic.
# ---------------------------------------------------------------------------

from typing import Dict, Any

def compute_chipload_risk(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate chipload risk for given design and context.
    
    Args:
        request: {
            "design": RosetteParamSpec or dict,
            "context": RmosContext or dict,
        }
    
    Returns:
        {
            "score": float (0-100),
            "risk": str ("GREEN"|"YELLOW"|"RED"),
            "warnings": List[str],
            "details": dict
        }
    """
    from ..rmos.context import RmosContext
    service = CalculatorService()
    design = request.get("design")
    ctx_data = request.get("context")
    ctx = RmosContext.from_dict(ctx_data) if isinstance(ctx_data, dict) else ctx_data
    return service.check_chipload_feasibility(design, ctx)


def compute_heat_risk(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate heat dissipation risk for given design and context.
    
    Args:
        request: Same as compute_chipload_risk
    
    Returns:
        {
            "score": float (0-100),
            "risk": str ("GREEN"|"YELLOW"|"RED"),
            "warnings": List[str],
            "details": dict
        }
    """
    from ..rmos.context import RmosContext
    service = CalculatorService()
    design = request.get("design")
    ctx_data = request.get("context")
    ctx = RmosContext.from_dict(ctx_data) if isinstance(ctx_data, dict) else ctx_data
    return service.check_heat_dissipation(design, ctx)


def compute_deflection_risk(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate tool deflection risk for given design and context.
    
    Args:
        request: Same as compute_chipload_risk
    
    Returns:
        {
            "score": float (0-100),
            "risk": str ("GREEN"|"YELLOW"|"RED"),
            "warnings": List[str],
            "details": dict
        }
    """
    from ..rmos.context import RmosContext
    service = CalculatorService()
    design = request.get("design")
    ctx_data = request.get("context")
    ctx = RmosContext.from_dict(ctx_data) if isinstance(ctx_data, dict) else ctx_data
    return service.check_tool_deflection(design, ctx)


def compute_rimspeed_risk(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate rim speed safety for given design and context.
    
    Args:
        request: Same as compute_chipload_risk
    
    Returns:
        {
            "score": float (0-100),
            "risk": str ("GREEN"|"YELLOW"|"RED"),
            "warnings": List[str],
            "details": dict
        }
    """
    from ..rmos.context import RmosContext
    service = CalculatorService()
    design = request.get("design")
    ctx_data = request.get("context")
    ctx = RmosContext.from_dict(ctx_data) if isinstance(ctx_data, dict) else ctx_data
    return service.check_rim_speed(design, ctx)


def compute_bom_efficiency(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate bill-of-materials efficiency for given design and context.
    
    Note: BOM calculator is still under development.
    Returns conservative score until fully implemented.
    
    Args:
        request: Same as compute_chipload_risk
    
    Returns:
        {
            "score": float (0-100, currently 75.0 default),
            "risk": str ("YELLOW"),
            "warnings": List[str],
            "details": dict
        }
    """
    from ..rmos.context import RmosContext
    service = CalculatorService()
    design = request.get("design")
    ctx_data = request.get("context")
    ctx = RmosContext.from_dict(ctx_data) if isinstance(ctx_data, dict) else ctx_data
    
    # TODO: Implement full BOM calculator
    # For now, return conservative score
    return {
        "score": 75.0,
        "risk": "YELLOW",
        "warnings": ["BOM calculator not fully implemented - using conservative score"],
        "details": {
            "design_type": getattr(design, "design_type", "unknown"),
            "model_id": ctx.model_id if ctx else "unknown"
        }
    }


__all__ = [
    "CalculatorService",
    "compute_chipload_risk",
    "compute_heat_risk",
    "compute_deflection_risk",
    "compute_rimspeed_risk",
    "compute_bom_efficiency",
]
```

### Test:
```powershell
python -c @"
from services.api.app.calculators.service import compute_chipload_risk
from services.api.app.rmos.context import RmosContext

ctx = RmosContext.from_model_id('strat_25_5')
result = compute_chipload_risk({'design': {}, 'context': ctx})
print(f'Score: {result[\"score\"]}, Risk: {result[\"risk\"]}')
"@
# Expected: Score and risk level printed
```

---

## 📝 PHASE C: Fretboard CAM Operations

**Priority:** 🔴 CRITICAL (2-3 hours)  
**Files to Create/Extend:**
1. `calculators/fret_slots_cam.py` (NEW)
2. Extend `body/fretboard_geometry.py` (MODIFY)

### C.1: Create fret_slots_cam.py

**File:** `services/api/app/calculators/fret_slots_cam.py`  
**Purpose:** Generate CNC toolpaths for fret slot operations

```python
"""
Fret Slots CAM Generator

Phase C — Wave 17→18 Integration

Generates CNC toolpaths (DXF + G-code) for fret slot cutting operations.

Integrates:
- instrument_geometry.neck.fret_math (fret positions)
- instrument_geometry.body.fretboard_geometry (board outline)
- rmos.context (material, tool, safety constraints)

Usage:
    from calculators.fret_slots_cam import generate_fret_slots_toolpath
    
    result = generate_fret_slots_toolpath(
        model_id="strat_25_5",
        board_width_mm=60.0,
        slot_depth_mm=2.0,
        tool_diameter_mm=0.6,
    )
    
    print(result["dxf"])    # DXF R12 format
    print(result["gcode"])  # G-code with safety
```

[IMPLEMENTATION CONTINUES IN NEXT FILE DUE TO LENGTH...]
```

**Status:** Implementation specification ready, requires full code generation

---

## 📝 PHASE D: Feasibility Fusion

**Priority:** 🟡 MEDIUM (3-4 hours after Phase C)  
**Files to Create:**
1. `rmos/feasibility_fusion.py` (NEW)
2. `rmos/feasibility_router.py` (NEW)

[SPECIFICATION CONTINUES...]

---

## 📝 PHASE E: CAM Preview Router

**Priority:** 🟡 MEDIUM (2-3 hours after Phase D)  
**Files to Create:**
1. `cam/fret_slots_router.py` (NEW)

[SPECIFICATION CONTINUES...]

---

## 📝 WAVE 15: Frontend Foundation

**Priority:** 🟢 FRONTEND (3-4 hours after Phase E)  
**Files to Create:**
1. `packages/client/src/stores/instrumentGeometryStore.ts`
2. `packages/client/src/modules/instrument-geometry/components/FretboardPreviewSvg.vue`
3. `packages/client/src/modules/instrument-geometry/InstrumentGeometryPanel.vue`

[SPECIFICATION CONTINUES...]

---

## 📝 WAVE 16: Frontend Enhancements

**Priority:** 🟢 FRONTEND (1-2 hours after Wave 15)  
**Modifications:**
1. Enhance instrumentGeometryStore (fan-fret, diagnostics)
2. Add risk coloring to SVG
3. Add fan-fret UI controls
4. Add risk legend

[SPECIFICATION CONTINUES...]

---

## 🎯 IMMEDIATE NEXT STEPS

### **Step 1: Verify Phase B is Working**
```powershell
.\test_phase_b_context.ps1
```
**Expected:** All 5 test suites pass ✅

### **Step 2: Create ACTION 1 + ACTION 2**
Execute the two trivial actions above (35 minutes total)

### **Step 3: Decide Phase Order**
**Question for you:** Should we implement:
- **Option A:** Backend-first (C→D→E→15→16) — Full API then UI
- **Option B:** Parallel (C+15 together) — UI can mock Phase D/E initially
- **Option C:** UI-first (15→16→C→D→E) — Visual mockups then wire

**Recommendation:** Option A (backend-first) for type safety

---

## ❓ QUESTIONS FOR YOU

1. **Have you run `test_phase_b_context.ps1`?** Should we verify Phase B works first?

2. **Which phase should we implement FIRST?**
   - Phase C (Fretboard CAM)
   - Phase D (Feasibility)
   - Phase E (Preview Router)
   - Wave 15 (UI Foundation)

3. **Do you want complete implementations NOW** or **step-by-step with pauses for review?**

4. **Testing preference:**
   - Create PowerShell smoke tests as we go?
   - pytest unit tests?
   - Manual API testing only?

---

## 📊 Time Estimates

| Phase | Time | Status |
|-------|------|--------|
| Action 1 (shim) | 5 min | ⏸️ Ready |
| Action 2 (wrappers) | 30 min | ⏸️ Ready |
| Phase C | 2-3 hrs | ⏸️ Specified above |
| Phase D | 3-4 hrs | ⏸️ Needs specification |
| Phase E | 2-3 hrs | ⏸️ Needs specification |
| Wave 15 | 3-4 hrs | ⏸️ Needs specification |
| Wave 16 | 1-2 hrs | ⏸️ Needs specification |
| **TOTAL** | **12-16 hrs** | - |

---

**Ready to proceed with Actions 1 & 2?** Say "yes" and I'll implement them immediately.

**Want full Phase C specification?** Say "show me Phase C" and I'll generate the complete implementation.

**Have questions?** Ask away — I have complete context on your entire codebase structure.
