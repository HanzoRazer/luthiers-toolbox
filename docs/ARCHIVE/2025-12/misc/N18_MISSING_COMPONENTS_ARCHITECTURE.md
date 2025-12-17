# N.18 Missing Components Architecture

**Date:** November 14, 2025  
**Status:** Ready for Implementation  
**Estimated Time:** 2-4 hours

---

## 🎯 Executive Summary

**What's Missing:** One critical file (`poly_offset_spiral.py`) that provides polygon offsetting and spiral toolpath generation.

**Why It's Needed:** The router `adaptive_poly_gcode_router.py` imports this file but it doesn't exist, causing the entire N.18 endpoint to fail with 404 errors.

**Solution:** Create `poly_offset_spiral.py` using existing components from N.17 and Module L as templates.

---

## 🔍 Current State

### **What Exists ✅**

| File | Location | Status |
|------|----------|--------|
| `adaptive_poly_gcode_router.py` | `services/api/app/routers/` | ✅ Complete (30 lines) |
| `g2_emitter.py` | `services/api/app/util/` | ✅ Complete (~80 lines) |
| Router registration | `services/api/app/main.py` | ✅ Registered (lines 62-65, 269-270) |
| Smoke test | `smoke_n18_arcs.ps1` | ✅ Complete (189 lines, 3 tests) |
| Documentation | `PATCH_N18_INTEGRATION_SUMMARY.md` | ✅ Complete |

### **What's Missing ❌**

| File | Location | Impact |
|------|----------|--------|
| `poly_offset_spiral.py` | `services/api/app/util/` | **CRITICAL BLOCKER** |

---

## 📐 Architecture of Missing File

### **File:** `services/api/app/util/poly_offset_spiral.py`

**Estimated Size:** ~250-300 lines

**Purpose:** Generate spiral toolpaths from polygon boundaries using offset-based adaptive pocketing.

### **Required Function Signature**

```python
def build_spiral_poly(
    poly: List[Tuple[float, float]],
    tool_dia: float,
    stepover: float,
    target_engage: float,
    arc_r: float
) -> List[Tuple[float, float]]:
    """
    Generate a continuous spiral toolpath from a closed polygon boundary.
    
    Args:
        poly: Closed polygon as list of (x, y) points in mm
        tool_dia: Tool diameter in mm (e.g., 6.0)
        stepover: Radial stepover as fraction of tool_dia (e.g., 0.4 = 40%)
        target_engage: Target radial engagement fraction (e.g., 0.35 = 35%)
        arc_r: Minimum arc radius for smoothing (mm)
        
    Returns:
        List of (x, y) points forming continuous spiral toolpath
        
    Algorithm:
        1. Generate inward offset rings using polygon offsetting
        2. Link rings into continuous spiral (nearest-point stitching)
        3. Apply arc smoothing at corners
        4. Return flattened point list for G-code emission
    """
```

### **Required Components**

Based on existing code patterns in the project:

#### **1. Polygon Offsetting (Core Algorithm)**
- Use **pyclipper** for robust integer-space offsetting
- Pattern from: `services/api/app/cam/polygon_offset_n17.py` (lines 16-75)
- Functions needed:
  - `offset_polygon_mm()` - Main offsetting function
  - `_scale_to_int()` / `_scale_from_int()` - Integer space conversion (scale=1000)
  - `_clean_polygon()` - Remove duplicate/degenerate points

```python
# Example from polygon_offset_n17.py
def offset_polygon_mm(
    poly: List[Pt],
    offset: float,
    join_type: str = "round",
    arc_tolerance: float = 0.25,
    miter_limit: float = 2.0
) -> Optional[List[List[Pt]]]:
    """Offset polygon using pyclipper"""
    if HAS_PYCLIPPER:
        pc = pyclipper.PyclipperOffset(miter_limit=miter_limit, 
                                       arc_tolerance=arc_tolerance*SCALE)
        jt = pyclipper.JT_ROUND
        poly_scaled = [(int(x * SCALE), int(y * SCALE)) for x, y in poly]
        pc.AddPath(poly_scaled, jt, pyclipper.ET_CLOSEDPOLYGON)
        result = pc.Execute(offset * SCALE)
        return [[(x / SCALE, y / SCALE) for x, y in path] for path in result]
```

#### **2. Offset Stack Generation**
- Pattern from: `services/api/app/cam/adaptive_core_l1.py` (lines 328-448)
- Function: `build_offset_stacks_robust()`
- Algorithm:
  1. Start from `tool_dia/2 + margin` inside boundary
  2. Generate successive inward offsets by `stepover * tool_dia`
  3. Stop when area collapses or reaches center
  4. Return list of offset rings

```python
def generate_offset_rings(
    poly: List[Pt],
    tool_dia: float,
    stepover: float,
    margin: float = 0.5
) -> List[List[Pt]]:
    """Generate inward offset rings"""
    rings = []
    offset_dist = tool_dia / 2.0 + margin  # Initial inset
    step = stepover * tool_dia
    
    while True:
        result = offset_polygon_mm(poly, -offset_dist)
        if not result or len(result[0]) < 3:
            break
        rings.append(result[0])
        offset_dist += step
        if offset_dist > 1000:  # Safety cap
            break
    
    return rings
```

#### **3. Spiral Stitching (Ring Linking)**
- Pattern from: `services/api/app/cam/adaptive_core_l1.py` (lines 449-484)
- Function: `spiralize_linked()`
- Algorithm: Nearest-point stitching between rings

```python
def link_rings_to_spiral(rings: List[List[Pt]]) -> List[Pt]:
    """Link offset rings into continuous spiral"""
    if not rings:
        return []
    
    path = list(rings[0])  # Start from outermost ring
    
    for next_ring in rings[1:]:
        # Find nearest point on next ring
        min_dist = float('inf')
        best_idx = 0
        last_pt = path[-1]
        
        for i, pt in enumerate(next_ring):
            dist = math.hypot(pt[0] - last_pt[0], pt[1] - last_pt[1])
            if dist < min_dist:
                min_dist = dist
                best_idx = i
        
        # Append ring starting from nearest point
        path.extend(next_ring[best_idx:] + next_ring[:best_idx])
    
    return path
```

#### **4. Arc Smoothing (Optional)**
- Pattern from: `services/api/app/cam/adaptive_core_l2.py` (lines 150-250)
- Function: `inject_min_fillet()`
- Adds small arcs at sharp corners based on `arc_r` parameter

```python
def smooth_with_arcs(pts: List[Pt], min_radius: float) -> List[Pt]:
    """Insert arc fillets at sharp corners"""
    # If arc_r is small or disabled, return as-is
    if min_radius < 0.5:
        return pts
    
    # Detect corners with angle < 120° and insert arcs
    # (Implementation from adaptive_core_l2.py inject_min_fillet)
    return pts  # Simplified for now
```

---

## 🏗️ Implementation Template

### **File Structure**

```python
# services/api/app/util/poly_offset_spiral.py

from __future__ import annotations
from typing import List, Tuple, Optional
import math

try:
    import pyclipper
    HAS_PYCLIPPER = True
except ImportError:
    HAS_PYCLIPPER = False

Pt = Tuple[float, float]
SCALE = 1000.0  # Integer scaling for pyclipper


# ============================================================================
# Section 1: Polygon Offsetting (Core)
# ============================================================================

def offset_polygon_mm(
    poly: List[Pt],
    offset: float,
    join_type: str = "round",
    arc_tolerance: float = 0.25,
    miter_limit: float = 2.0
) -> Optional[List[List[Pt]]]:
    """Offset polygon using pyclipper (copy from polygon_offset_n17.py)"""
    # TODO: Copy implementation from polygon_offset_n17.py lines 16-75
    pass


# ============================================================================
# Section 2: Offset Stack Generation
# ============================================================================

def generate_offset_rings(
    poly: List[Pt],
    tool_dia: float,
    stepover: float,
    margin: float = 0.5,
    max_passes: int = 50
) -> List[List[Pt]]:
    """Generate inward offset rings for adaptive pocketing"""
    # TODO: Adapt from adaptive_core_l1.py build_offset_stacks_robust
    pass


# ============================================================================
# Section 3: Spiral Stitching
# ============================================================================

def link_rings_to_spiral(rings: List[List[Pt]]) -> List[Pt]:
    """Link offset rings into continuous spiral via nearest-point stitching"""
    # TODO: Copy from adaptive_core_l1.py spiralize_linked (lines 449-484)
    pass


# ============================================================================
# Section 4: Arc Smoothing (Optional)
# ============================================================================

def smooth_with_arcs(pts: List[Pt], min_radius: float) -> List[Pt]:
    """Insert arc fillets at sharp corners"""
    # TODO: Optionally adapt from adaptive_core_l2.py inject_min_fillet
    # For MVP, can return pts as-is (no smoothing)
    return pts


# ============================================================================
# Section 5: Main Entry Point (Required by Router)
# ============================================================================

def build_spiral_poly(
    poly: List[Tuple[float, float]],
    tool_dia: float,
    stepover: float,
    target_engage: float,
    arc_r: float
) -> List[Tuple[float, float]]:
    """
    Generate spiral toolpath from polygon boundary.
    
    This is the main function called by adaptive_poly_gcode_router.py
    """
    # Validate inputs
    if not poly or len(poly) < 3:
        return []
    if tool_dia <= 0:
        return []
    
    # Ensure closed polygon
    if poly[0] != poly[-1]:
        poly = list(poly) + [poly[0]]
    
    # Step 1: Generate offset rings
    margin = 0.5  # mm clearance from boundary
    rings = generate_offset_rings(poly, tool_dia, stepover, margin)
    
    if not rings:
        return []  # Polygon too small or invalid
    
    # Step 2: Link rings into continuous spiral
    spiral = link_rings_to_spiral(rings)
    
    if not spiral:
        return []
    
    # Step 3: Apply arc smoothing (optional)
    if arc_r > 0.5:
        spiral = smooth_with_arcs(spiral, arc_r)
    
    # Step 4: Return flattened point list
    return spiral


# ============================================================================
# Helper Functions
# ============================================================================

def _polygon_area(poly: List[Pt]) -> float:
    """Calculate signed area of polygon"""
    area = 0.0
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        area += poly[i][0] * poly[j][1]
        area -= poly[j][0] * poly[i][1]
    return area / 2.0
```

---

## 🎯 Implementation Strategy

### **Option A: Copy from Existing Code (RECOMMENDED)**
**Time:** 1-2 hours  
**Complexity:** Low

1. Copy `offset_polygon_mm()` from `polygon_offset_n17.py` (lines 16-75)
2. Copy `generate_offset_rings()` logic from `adaptive_core_l1.py` `build_offset_stacks_robust()` (lines 328-448)
3. Copy `link_rings_to_spiral()` from `adaptive_core_l1.py` `spiralize_linked()` (lines 449-484)
4. Wrap in `build_spiral_poly()` main function
5. Test with smoke test

**Files to Reference:**
- `services/api/app/cam/polygon_offset_n17.py` (offsetting logic)
- `services/api/app/cam/adaptive_core_l1.py` (offset stacks + spiralizer)

### **Option B: Minimal MVP Implementation**
**Time:** 30-60 minutes  
**Complexity:** Very Low

Create simplified version that works without arc smoothing:

```python
def build_spiral_poly(poly, tool_dia, stepover, target_engage, arc_r):
    """Minimal MVP: Simple offset + spiral"""
    # 1. Just use polygon_offset_n17.offset_polygon_mm in a loop
    # 2. Link with simple nearest-point logic
    # 3. Skip arc smoothing (arc_r ignored)
    # 4. Return point list
    pass
```

---

## 📊 Dependencies

### **Already Installed:**
- `pyclipper==1.3.0.post5` (from L.1 integration)
- `shapely` (geometry operations)
- `numpy` (array math)

### **Import Structure:**

```python
# In poly_offset_spiral.py
try:
    import pyclipper
    HAS_PYCLIPPER = True
except ImportError:
    HAS_PYCLIPPER = False
    # Fallback to simple offsetting

# Optional imports (for arc smoothing)
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
```

---

## 🔗 Integration Points

### **1. Router Import**
```python
# services/api/app/routers/adaptive_poly_gcode_router.py (line 5)
from .util.poly_offset_spiral import build_spiral_poly  # ← MISSING FILE
```

### **2. Router Usage**
```python
# services/api/app/routers/adaptive_poly_gcode_router.py (line 27)
pts = build_spiral_poly(
    poly,            # List[(x,y)]
    req.tool_dia,    # 6.0 mm
    req.stepover,    # 2.4 mm (or 0.4 as fraction)
    req.target_engage,  # 0.35 (35% engagement)
    req.arc_r        # 2.0 mm (arc smoothing radius)
)
```

### **3. G-code Emission**
```python
# services/api/app/routers/adaptive_poly_gcode_router.py (line 28)
nc = emit_program_xy(pts, ...)  # ← g2_emitter.py (already exists)
```

---

## 🧪 Testing Plan

### **Step 1: Create File**
```powershell
# Create services/api/app/util/poly_offset_spiral.py
# Copy template above and fill in TODOs
```

### **Step 2: Test Import**
```powershell
cd services/api
.\.venv\Scripts\Activate.ps1
python -c "from app.util.poly_offset_spiral import build_spiral_poly; print('✓ Import successful')"
```

### **Step 3: Test Basic Function**
```python
# Quick test in Python REPL
from app.util.poly_offset_spiral import build_spiral_poly

poly = [(0,0), (100,0), (100,60), (0,60), (0,0)]
pts = build_spiral_poly(poly, tool_dia=6.0, stepover=0.4, target_engage=0.35, arc_r=2.0)
print(f"Generated {len(pts)} points")
# Should return ~100-300 points
```

### **Step 4: Run Smoke Test**
```powershell
.\smoke_n18_arcs.ps1 -SkipStart
```

**Expected Results:**
- Test 1: G2/G3 arcs detected ✅
- Test 2: Linear mode (no arcs) ✅
- Test 3: Feed floor commands ✅

---

## 📋 Implementation Checklist

### **Phase 1: Create File (1-2 hours)**
- [ ] Create `services/api/app/util/poly_offset_spiral.py`
- [ ] Copy `offset_polygon_mm()` from `polygon_offset_n17.py`
- [ ] Copy offset ring generation from `adaptive_core_l1.py`
- [ ] Copy spiral stitching from `adaptive_core_l1.py`
- [ ] Implement `build_spiral_poly()` main function
- [ ] Add helper functions (`_polygon_area`, etc.)
- [ ] Test imports

### **Phase 2: Test Locally (30 min)**
- [ ] Test `build_spiral_poly()` with simple rectangle
- [ ] Verify point count reasonable (100-300 for 100×60mm pocket)
- [ ] Check spiral continuity (no jumps between rings)
- [ ] Restart API server
- [ ] Run smoke test (`smoke_n18_arcs.ps1`)

### **Phase 3: Validate Output (30 min)**
- [ ] Check G-code has G2/G3 commands
- [ ] Verify feed floor commands present
- [ ] Compare output vs N.17 polygon offset
- [ ] Test with island geometry
- [ ] Test linear mode (use_arcs=false)

---

## 🎓 Code Examples from Existing Files

### **Example 1: Offset Ring Generation** (from `adaptive_core_l1.py`)

```python
# Lines 328-400 of adaptive_core_l1.py
def build_offset_stacks_robust(
    boundary: List[Tuple[float,float]],
    islands: List[List[Tuple[float,float]]],
    tool_d: float,
    stepover: float,
    margin: float,
    smoothing: float
) -> List[List[Tuple[float,float]]]:
    """
    Generate inward offset rings using pyclipper.
    """
    SCALE = 10000
    
    # Initial inset
    first_inset = tool_d / 2.0 + margin
    step = stepover * tool_d
    
    rings = []
    offset_dist = first_inset
    
    for pass_idx in range(max_passes):
        # Offset boundary inward
        pc = pyclipper.PyclipperOffset(miter_limit=2.0, 
                                       arc_tolerance=smoothing*SCALE)
        poly_scaled = [(int(x*SCALE), int(y*SCALE)) for x,y in boundary]
        pc.AddPath(poly_scaled, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
        result = pc.Execute(-offset_dist * SCALE)
        
        if not result:
            break
        
        # Scale back to mm
        ring = [(x/SCALE, y/SCALE) for x,y in result[0]]
        rings.append(ring)
        
        offset_dist += step
    
    return rings
```

### **Example 2: Spiral Stitching** (from `adaptive_core_l1.py`)

```python
# Lines 449-484 of adaptive_core_l1.py
def spiralize_linked(rings: List[List[Tuple[float, float]]]) -> List[Tuple[float, float]]:
    """
    Link offset rings into continuous spiral via nearest-point stitching.
    """
    if not rings:
        return []
    
    path = list(rings[0])  # Start from outermost
    
    for next_ring in rings[1:]:
        # Find nearest point on next ring to current path end
        last_pt = path[-1]
        min_dist = float('inf')
        best_idx = 0
        
        for i, pt in enumerate(next_ring):
            dx = pt[0] - last_pt[0]
            dy = pt[1] - last_pt[1]
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < min_dist:
                min_dist = dist
                best_idx = i
        
        # Append next ring starting from nearest point
        path.extend(next_ring[best_idx:] + next_ring[:best_idx])
    
    return path
```

---

## 🚀 Quick Start Command Sequence

```powershell
# 1. Create the missing file
New-Item -Path "services/api/app/util/poly_offset_spiral.py" -ItemType File

# 2. Copy template from this document (sections 1-5 above)

# 3. Fill in TODOs by copying from reference files:
#    - polygon_offset_n17.py (offsetting)
#    - adaptive_core_l1.py (stacks + spiral)

# 4. Test import
cd services/api
.\.venv\Scripts\Activate.ps1
python -c "from app.util.poly_offset_spiral import build_spiral_poly; print('✓')"

# 5. Restart API
uvicorn app.main:app --reload --port 8000

# 6. Run smoke test
cd ..\..
.\smoke_n18_arcs.ps1 -SkipStart
```

---

## 📚 Reference Files

| File | Lines | Purpose |
|------|-------|---------|
| `services/api/app/cam/polygon_offset_n17.py` | 16-75 | Pyclipper offsetting logic |
| `services/api/app/cam/adaptive_core_l1.py` | 328-448 | Offset stack generation |
| `services/api/app/cam/adaptive_core_l1.py` | 449-484 | Spiral stitching |
| `services/api/app/cam/adaptive_core_l2.py` | 150-250 | Arc smoothing (optional) |
| `services/api/app/routers/adaptive_poly_gcode_router.py` | 5, 27 | Import and usage |

---

## 💡 Pro Tips

1. **Start with MVP:** Skip arc smoothing initially (return `pts` as-is). Get basic spiral working first.

2. **Copy liberally:** The code already exists in `adaptive_core_l1.py` and `polygon_offset_n17.py`. Don't reinvent the wheel.

3. **Test incrementally:** Test each function individually before combining:
   ```python
   # Test offsetting
   result = offset_polygon_mm(poly, -3.0)
   
   # Test ring generation
   rings = generate_offset_rings(poly, 6.0, 0.4)
   
   # Test stitching
   spiral = link_rings_to_spiral(rings)
   ```

4. **Validate output:** Point count should be ~100-300 for typical pocket (100×60mm, 6mm tool, 45% stepover).

5. **Use smoke test:** The existing test (`smoke_n18_arcs.ps1`) will validate everything once file exists.

---

## ✅ Success Criteria

**File is complete when:**
- [ ] `build_spiral_poly()` returns non-empty point list
- [ ] Spiral is continuous (no large jumps between points)
- [ ] Router import succeeds (no ModuleNotFoundError)
- [ ] API server starts without errors
- [ ] Smoke test passes (3/3 tests)
- [ ] G-code contains G2/G3 arc commands
- [ ] G-code has feed floor commands

---

**Status:** Ready to implement  
**Estimated Time:** 2-4 hours (MVP: 1-2 hours)  
**Next Step:** Create `poly_offset_spiral.py` using template above
