# N.18 G2/G3 Arc Linkers - Status Report

**Feature:** N.18 G2/G3 Arc Linkers + Feed Floors  
**Status:** ⚠️ **INCOMPLETE INTEGRATION** (Cannot validate)  
**Date:** November 14, 2025

---

## Current State

### ✅ What Exists

1. **Router File** (`services/api/app/routers/adaptive_poly_gcode_router.py`):
   - 30 lines
   - Endpoint: `POST /cam/adaptive3/offset_spiral.nc`
   - Request model: `PolyNCReq` (14 parameters)
   - Registered in `main.py` (lines 62-65, 269-270)

2. **G-code Emitter** (`services/api/app/util/g2_emitter.py`):
   - Exists (not inspected yet)
   - Purpose: Generate G2/G3 arc commands

3. **Smoke Test** (`smoke_n18_arcs.ps1`):
   - 189 lines
   - 3 tests defined
   - Currently failing: All tests return 404

4. **Documentation**:
   - `PATCH_N18_INTEGRATION_SUMMARY.md` (184 lines, status: "In Progress")
   - `PATCH_N18_G2G3_LINKERS.md` (exists)
   - `PATCH_N18_QUICKREF.md` (exists)

### ❌ What's Missing

**Critical Blocker:** `services/api/app/util/poly_offset_spiral.py`

```python
# adaptive_poly_gcode_router.py line 5:
from .util.poly_offset_spiral import build_spiral_poly  # ❌ FILE NOT FOUND
```

**Impact:**
- Router import fails (caught by try/except in `main.py`)
- `adaptive_poly_gcode_router` set to `None`
- Endpoint never registered → 404 errors
- **Cannot validate N.18 without this file**

---

## Integration Checklist (From Docs)

| Task | Status | Notes |
|------|--------|-------|
| Copy `g2_emitter.py` | ✅ Done | File exists |
| Copy `adaptive_poly_gcode_router.py` | ✅ Done | File exists |
| Copy `poly_offset_spiral.py` | ❌ **MISSING** | **Blocker** |
| Register router in `main.py` | ✅ Done | Lines 62-65, 269-270 |
| Create smoke test | ✅ Done | `smoke_n18_arcs.ps1` |
| Test endpoint | ❌ Blocked | 404 errors |
| Validate G2/G3 output | ❌ Blocked | Can't reach endpoint |
| Update Module L docs | ⏳ Pending | Depends on validation |
| Add CI workflow | ⏳ Pending | Depends on validation |

---

## Test Results

**Smoke Test Run:**
```powershell
PS> .\smoke_n18_arcs.ps1 -SkipStart

=== Testing Patch N18: G2/G3 Arc Linkers ===

1. Testing POST /cam/adaptive3/offset_spiral.nc (G2/G3 arcs)
  ✗ Request failed: Response status code does not indicate success: 404 (Not Found).

2. Testing linear mode (use_arcs=false)
  ✗ Request failed: Response status code does not indicate success: 404 (Not Found).

3. Testing feed floor commands
  ✗ Request failed: Response status code does not indicate success: 404 (Not Found).

=== Test Summary ===
Passed: 0
Failed: 3
```

**Root Cause:** Endpoint not registered due to missing dependency

---

## Router Code Analysis

```python
# services/api/app/routers/adaptive_poly_gcode_router.py

from fastapi import APIRouter, Response
from pydantic import BaseModel
from typing import List
from .util.poly_offset_spiral import build_spiral_poly  # ❌ MISSING
from .util.g2_emitter import emit_program_xy             # ✅ EXISTS

router = APIRouter(prefix="/cam/adaptive3", tags=["cam","adaptive-poly","gcode"])

class PolyNCReq(BaseModel):
    polygon: List[List[float]]
    tool_dia: float = 6.0
    stepover: float = 2.4
    target_engage: float = 0.35
    arc_r: float = 2.0
    units: str = "mm"
    z: float = -1.0
    safe_z: float = 5.0
    base_feed: float = 600.0
    min_feed: float = 120.0
    floor_R: float = 3.0
    arc_tol: float = 0.05
    min_R: float = 1.0
    spindle: int = 12000

@router.post("/offset_spiral.nc")
def offset_spiral_nc(req: PolyNCReq):
    poly = [(p[0], p[1]) for p in req.polygon]
    if poly[0] != poly[-1]: poly.append(poly[0])
    pts = build_spiral_poly(poly, req.tool_dia, req.stepover, 
                           req.target_engage, req.arc_r)  # ❌ MISSING FUNCTION
    nc = emit_program_xy(pts, units=req.units, z=req.z, 
                        safe_z=req.safe_z, base_feed=req.base_feed, 
                        min_feed=req.min_feed, floor_R=req.floor_R, 
                        arc_tol=req.arc_tol, min_R=req.min_R, 
                        spindle=req.spindle)
    return Response(content=nc, media_type="text/plain")
```

---

## Options Forward

### Option A: Skip N.18 Validation (Recommended)

**Rationale:**
- Missing critical dependency (`poly_offset_spiral.py`)
- No Phase 3 baseline test exists
- Integration marked "In Progress" (incomplete)
- Similar functionality exists in N.17 (polygon offsetting + arc generation)

**Action:**
- Document N.18 as "incomplete integration"
- Move to N.19 or N.20 validation
- Return to N.18 after locating missing file

**Impact:**
- Phase 5 progress: 564/575 (98.1%) unchanged
- N-Series progress: 13/16 (81.25%) unchanged
- Can revisit N.18 later if dependency located

---

### Option B: Search for poly_offset_spiral.py

**Possible Locations:**
1. Art Studio source repository (mentioned in integration docs)
2. Legacy `ToolBox_Patch_N18_g2g3_linkers_feedfloors` directory
3. Alternative module name or location
4. May need to be reimplemented from scratch

**Search Strategy:**
```powershell
# Search entire workspace
Get-ChildItem -Recurse -Filter "*poly_offset*.py" -ErrorAction SilentlyContinue

# Search for function definition
Select-String -Path "**/*.py" -Pattern "def build_spiral_poly"

# Check Art Studio archives
Get-ChildItem "C:\Users\thepr\Downloads\ToolBox_Art_Studio" -Recurse -Filter "*.py"
```

---

### Option C: Implement poly_offset_spiral.py

**Requirements (Based on Usage):**
```python
def build_spiral_poly(
    poly: List[Tuple[float, float]],
    tool_dia: float,
    stepover: float,
    target_engage: float,
    arc_r: float
) -> List[Tuple[float, float]]:
    """
    Generate spiral toolpath from polygon boundary.
    
    Args:
        poly: Closed polygon boundary
        tool_dia: Tool diameter (mm)
        stepover: Distance between passes (mm)
        target_engage: Target engagement angle (0-1)
        arc_r: Arc radius for linking (mm)
        
    Returns:
        List of XY points forming continuous spiral
    """
    # Implementation needed
    pass
```

**Similar Functionality:**
- `polygon_offset_n17.py` has `toolpath_offsets()` (offset generation)
- `adaptive_core_l2.py` has `true_spiral_from_rings()` (spiral stitching)
- Could potentially bridge N.17 + L.2 to create N.18 equivalent

**Effort:** 4-8 hours to implement and validate

---

## Related Features

### Overlap with N.17 (Polygon Offset)
- N.17: Polygon offsetting + arc/linear G-code
- N.18: Polygon offsetting + G2/G3 arcs + feed floors
- **Difference:** N.18 adds "spiral" mode and `target_engage` parameter

### Overlap with Module L (Adaptive Pocketing)
- L.2: True spiral from offset rings
- L.3: Trochoidal insertion (G2/G3 loops)
- **Difference:** N.18 focuses on arc linkers, L focuses on engagement control

### Potential Consolidation
- N.17 + Module L already provide:
  - Robust offsetting (pyclipper)
  - Spiral stitching (nearest-point)
  - Arc generation (G2/G3)
  - Feed management (slowdown metadata)
- N.18 may be **redundant** if N.17 + L cover all use cases

---

## Recommendation

**Skip N.18 validation and proceed to N.19/N.20**

**Reasons:**
1. ✅ Missing critical dependency (blocker)
2. ✅ No Phase 3 baseline established
3. ✅ Functionality overlap with N.17 (validated at 90%)
4. ✅ Functionality overlap with Module L.2/L.3
5. ✅ Integration marked incomplete in docs
6. ✅ Can revisit if dependency located

**Next Steps:**
1. Document N.18 as "incomplete - missing poly_offset_spiral.py"
2. Search for N.19 specifications
3. If N.19 also incomplete, move to N.20
4. Target: Complete 3 remaining N-series validations

---

## Search Log

**Attempted Searches:**
- `poly_offset_spiral.py` in workspace: **Not found**
- `build_spiral_poly` function definition: **2 matches (both in router import)**
- Phase 3 N.18 baseline: **Not found**
- N.18 comprehensive test: **Not found**

**Files Found:**
- `smoke_n18_arcs.ps1` (smoke test only, 3 tests)
- `adaptive_poly_gcode_router.py` (router with missing import)
- `g2_emitter.py` (utility exists, not inspected)
- Integration docs (3 markdown files)

---

## Decision Matrix

| Option | Pros | Cons | Time | Recommendation |
|--------|------|------|------|----------------|
| **A: Skip** | Fast, maintain momentum | N.18 incomplete | 0h | ✅ **Best** |
| **B: Search** | May find file | May not exist | 1-2h | ⚠️ If time permits |
| **C: Implement** | Complete feature | High effort, may be redundant | 4-8h | ❌ Not now |

---

**Status:** N.18 cannot be validated without `poly_offset_spiral.py`  
**Recommendation:** Proceed to N.19 validation  
**Rationale:** Maintain Phase 5 momentum, N.17 already covers similar functionality  
**Cumulative Progress:** 564/575 (98.1%) - N.18 marked as "incomplete integration"
