"""
================================================================================
Adaptive Pocketing Core Engine (Legacy L.0)
================================================================================

PURPOSE:
--------
Legacy adaptive pocketing implementation using vector-based polygon offsetting.
Generates offset-based toolpaths for clearing rectangular and rounded pockets.
**SUPERSEDED by L.1 (pyclipper) and L.2 (true spiralizer)** - kept for reference.

CORE FUNCTIONS:
--------------
1. plan_adaptive(loops, tool_d, stepover, stepdown, margin, strategy, smoothing, climb)
   - Main planner entry point
   - Generates toolpath points from closed loops
   - Returns: List of (x, y) coordinates for cutting path

2. build_offset_stacks(outer, islands, tool_d, stepover, margin)
   - Creates inward offset rings from outer boundary
   - Stops before collapse or island collision
   - Returns: List of offset loops

3. spiralize(stacks, smoothing)
   - Links offset rings into continuous path
   - Nearest-neighbor ring connection
   - Returns: Single continuous path of points

4. to_toolpath(path_pts, feed_xy, z_rough, safe_z, lead_r, climb)
   - Converts path points to G-code move list
   - Adds lead-in/lead-out, rapids, plunges
   - Returns: List of move dictionaries

ALGORITHM OVERVIEW (L.0 Legacy):
-------------------------------
**Vector-Based Offsetting:**

1. **Initial Inset:**
   - Start offset = tool_d/2 + margin (mm inside boundary)
   - Use vector normals at each vertex
   - Bisector-based miter joins

2. **Successive Offsets:**
   - Step distance = tool_d × stepover (typically 30-60%)
   - Repeat offset operation on previous ring
   - Stop when: area < 0.01 mm² or < 3 points

3. **Miter Join Calculation:**
   ```
   bisector = (left_normal_1 + left_normal_2) / |...|
   miter_length = 1 / sin(half_angle)
   clamped_length = min(10, miter_length)  # Prevent spikes
   offset_point = vertex + bisector × offset × clamped_length
   ```

4. **Spiralizer (Naive):**
   - Link rings via nearest-neighbor connection
   - No angle continuity constraints
   - Simple midpoint interpolation for smoothing

5. **G-code Generation:**
   - G0 rapid to safe Z
   - G0 rapid to XY start
   - G1 plunge to cutting depth
   - G1 linear moves along path
   - G0 retract to safe Z

LIMITATIONS (L.0):
-----------------
❌ **Not Robust for Complex Geometry:**
- Self-intersections cause undefined behavior
- No proper polygon clipping
- Miter spikes clamped but not eliminated

❌ **Naive Spiralizer:**
- Sharp direction changes between rings
- No curvature continuity
- Suboptimal chipload consistency

❌ **No Island Handling:**
- Islands ignored in offset calculation
- No keepout zone subtraction
- Manual collision detection needed

❌ **Limited Smoothing:**
- Only simple corner mitigation
- No arc insertion
- No adaptive stepover

UPGRADE PATH:
------------
**Migrate to Modern Engines:**

**L.1 (Robust Offsetting):**
```python
from app.cam.adaptive_core_l1 import plan_adaptive_l1
path = plan_adaptive_l1(loops, tool_d, stepover, stepdown, margin, smoothing)
# Benefits: pyclipper polygon clipping, island subtraction, min-radius control
```

**L.2 (True Spiralizer):**
```python
from app.cam.adaptive_core_l2 import plan_adaptive_l2
path, overlays = plan_adaptive_l2(loops, tool_d, stepover, stepdown, margin, 
                                   smoothing, min_fillet_r, adaptive_step)
# Benefits: continuous spiral, adaptive stepover, min-fillet injection, HUD overlays
```

**L.3 (Trochoidal + Jerk-Aware):**
```python
from app.services.adaptive_kernel import plan_adaptive
result = plan_adaptive(PlanIn(...))
# Benefits: trochoidal insertion, jerk-aware time, full parameter support
```

USAGE EXAMPLE (Legacy):
-----------------------
    from app.cam.adaptive_core import plan_adaptive, to_toolpath
    
    # Define rectangular pocket (no islands)
    outer_loop = [(0, 0), (100, 0), (100, 60), (0, 60)]
    
    # Generate path points (legacy)
    path_pts = plan_adaptive(
        loops=[outer_loop],
        tool_d=6.0,           # 6mm end mill
        stepover=0.45,        # 45% stepover
        stepdown=1.5,         # Not used in L.0 (single-pass)
        margin=0.5,           # 0.5mm clearance
        strategy="Spiral",    # or "Lanes"
        smoothing=0.3,        # Not effectively used in L.0
        climb=True            # Not used in L.0
    )
    
    # Convert to G-code moves
    moves = to_toolpath(
        path_pts=path_pts,
        feed_xy=1200,         # mm/min
        z_rough=-1.5,         # mm
        safe_z=5.0,           # mm
        lead_r=2.0,           # Not used in L.0
        climb=True            # Not used in L.0
    )
    
    # Result: List of move dicts
    # [
    #   {"code": "G0", "z": 5.0},
    #   {"code": "G0", "x": 3.0, "y": 3.0},
    #   {"code": "G1", "z": -1.5, "f": 1200},
    #   {"code": "G1", "x": 97.0, "y": 3.0, "f": 1200},
    #   ...
    # ]

INTEGRATION POINTS:
------------------
- **Superseded by**: app.services.adaptive_kernel (L.3 service layer)
- **Used by**: (Legacy) Early adaptive router implementations
- **Exports**: plan_adaptive(), build_offset_stacks(), spiralize(), to_toolpath()
- **See Also**: 
  - adaptive_core_l1.py (pyclipper-based, production)
  - adaptive_core_l2.py (true spiralizer, production)
  - services/adaptive_kernel.py (unified service layer, current)

CRITICAL SAFETY RULES:
---------------------
1. **Geometry Validation Required**: Input loops must be closed
   - First loop = outer boundary (CCW)
   - Subsequent loops = islands (CW)
   - No validation in L.0 - caller must ensure

2. **Single-Pass Only**: stepdown parameter ignored
   - L.0 generates single depth level
   - Multi-pass requires external iteration
   - Use L.1+ for automatic multi-pass

3. **Miter Spike Clamping**: Prevents catastrophic offsets
   - Miter length clamped to 10× offset distance
   - Still produces artifacts at tight corners
   - Use L.1 rounded joins for production

4. **Area Collapse Detection**: Prevents infinite loops
   - Stops when offset area < 0.01 mm²
   - Crude heuristic, may miss edge cases
   - L.1 uses proper polygon validity checks

5. **No Collision Detection**: Islands not avoided
   - Manual bounding box checks only
   - No actual island subtraction
   - **PRODUCTION: Use L.1 island handling**

PERFORMANCE CHARACTERISTICS:
---------------------------
- **Offset Generation**: O(n²) per ring (naive miter calculation)
- **Spiralizer**: O(n×m) nearest-neighbor search (not optimal)
- **Memory**: O(n×r) where n=points/ring, r=ring count
- **Typical Performance**: 10-50ms for 100×60mm pocket (100-200 points)

DEPRECATION NOTICE:
------------------
🚨 **L.0 is LEGACY CODE** 🚨

**Do not use for new projects.**

**Reasons for deprecation:**
1. Not robust for complex geometry (self-intersections)
2. No island handling
3. Naive spiralizer (poor chipload consistency)
4. Single-pass only (no multi-depth)
5. No min-radius controls

**Recommended alternatives:**
- Simple pockets: Use L.1 (adaptive_core_l1.py)
- Advanced pockets: Use L.2 (adaptive_core_l2.py)
- Production workflows: Use service layer (adaptive_kernel.py)

**Kept for:**
- Historical reference
- Algorithm comparison
- Educational purposes
- Legacy compatibility testing

PATCH HISTORY:
-------------
- Author: Original adaptive pocketing implementation
- Status: DEPRECATED (superseded by L.1/L.2/L.3)
- Enhanced: Phase 7a (Coding Policy Application)

================================================================================
"""

import math
from typing import List, Dict, Tuple

# Geometry input: list of closed loops (outer first, then inner islands), each loop as [(x,y), ...]
# Output toolpath: list of moves [{"code":"G1","x":...,"y":...,"f":...}, {"code":"G2","x":...,"y":...,"i":...,"j":...}, ...]


# =============================================================================
# VECTOR-BASED POLYGON OFFSETTING (LEGACY L.0)
# =============================================================================

def _offset_loop(loop: List[Tuple[float,float]], offset: float, round_joints=True) -> List[Tuple[float,float]]:
    """
    Very small inward offset: vector normals + miter/round joins. Not robust for self-intersections,
    but good enough for rects/rounded pockets. We iterate this to create offset shells.
    """
    pts = loop[:]
    n = len(pts)
    out = []
    for i in range(n):
        x1,y1 = pts[i-1]
        x2,y2 = pts[i]
        x3,y3 = pts[(i+1)%n]
        # edges
        ux,uy = x2-x1, y2-y1
        vx,vy = x3-x2, y3-y2
        # unit left normals
        lu = (-(uy)/((ux**2+uy**2)**0.5+1e-12), (ux)/((ux**2+uy**2)**0.5+1e-12))
        lv = (-(vy)/((vx**2+vy**2)**0.5+1e-12), (vx)/((vx**2+vy**2)**0.5+1e-12))
        # bisector
        bx,by = lu[0]+lv[0], lu[1]+lv[1]
        bl = (bx**2+by**2)**0.5+1e-12
        bx,by = bx/bl, by/bl
        # miter length; clamp to avoid crazy spikes
        sin_half = max(1e-6, math.sin(0.5*angle_between(ux,uy,vx,vy)))
        m = min(10.0, 1.0/sin_half)
        px = x2 + bx * offset * m
        py = y2 + by * offset * m
        out.append((px,py))
    return out

def angle_between(ax,ay,bx,by):
    a = math.atan2(ay,ax); b = math.atan2(by,bx)
    d = b-a
    while d>math.pi: d -= 2*math.pi
    while d<-math.pi: d += 2*math.pi
    return abs(d)

def build_offset_stacks(outer: List[Tuple[float,float]], islands: List[List[Tuple[float,float]]], tool_d: float, stepover: float, margin: float):
    """
    Returns a list of inward offset loops starting from (tool/2 + margin) inside the outer, stopping before collapse or island collision.
    """
    step = tool_d * max(0.05, min(0.95, stepover))  # mm
    inner = []
    cur = _offset_loop(outer, -(tool_d/2.0 + margin))
    while cur and len(cur) >= 3:
        inner.append(cur)
        nxt = _offset_loop(cur, -step)
        if not nxt or len(nxt) < 3: break
        # crude stop if area collapses
        if polygon_area(nxt) <= 1e-2: break
        cur = nxt
    # TODO: subtract islands properly; in first cut we just stop when inner area <= any island bbox.
    return inner

def polygon_area(loop: List[Tuple[float,float]]):
    a=0.0
    for i in range(len(loop)):
        x1,y1 = loop[i]
        x2,y2 = loop[(i+1)%len(loop)]
        a += x1*y2 - x2*y1
    return abs(a)/2.0


# =============================================================================
# NAIVE SPIRALIZER (LEGACY L.0)
# =============================================================================

def spiralize(stacks: List[List[Tuple[float,float]]], smoothing: float) -> List[Tuple[float,float]]:
    """
    Link successive offset rings with short connectors to create one continuous path.
    smoothing: corner fillet radius (mm). First cut just interpolates midpoints.
    """
    if not stacks: return []
    path = []
    for k, ring in enumerate(stacks):
        if k==0:
            path += ring
        else:
            # connect last of previous to nearest of this ring
            prev_pt = path[-1]
            jmin = min(range(len(ring)), key=lambda j: (ring[j][0]-prev_pt[0])**2+(ring[j][1]-prev_pt[1])**2)
            path += [ring[jmin]] + ring[jmin+1:] + ring[:jmin]
    return path


# =============================================================================
# G-CODE GENERATION (LEGACY L.0)
# =============================================================================

def to_toolpath(path_pts: List[Tuple[float,float]], feed_xy: float, z_rough: float, safe_z: float, lead_r: float, climb=True):
    moves = []
    # lead-in arc
    if path_pts:
        sx,sy = path_pts[0]
        moves += [{"code":"G0","z":safe_z},{"code":"G0","x":sx,"y":sy},{"code":"G1","z":z_rough,"f":feed_xy}]
    for i in range(1,len(path_pts)):
        x,y = path_pts[i]
        moves.append({"code":"G1","x":x,"y":y,"f":feed_xy})
    moves += [{"code":"G0","z":safe_z}]
    return moves


# =============================================================================
# MAIN PLANNER (LEGACY L.0)
# =============================================================================

def plan_adaptive(loops: List[List[Tuple[float,float]]], tool_d: float, stepover: float, stepdown: float, margin: float, strategy: str, smoothing: float, climb: bool):
    outer = loops[0]
    islands = loops[1:] if len(loops)>1 else []
    stacks = build_offset_stacks(outer, islands, tool_d, stepover, margin)
    if strategy.lower().startswith("spiral"):
        path_pts = spiralize(stacks, smoothing)
    else:
        # lanes fallback: just concatenate rings
        path_pts = [pt for ring in stacks for pt in ring]
    return path_pts
