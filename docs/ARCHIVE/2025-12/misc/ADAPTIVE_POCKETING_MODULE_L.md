# Module L: Adaptive Pocketing Engine 2.0

A complete adaptive pocketing system for CNC milling operations with offset-based toolpath generation, post-processor awareness, and real-time simulation.

**Current Version:** L.3 (Trochoidal Insertion + Jerk-Aware Time)  
**Status:** ✅ Production Ready

## 🎯 Overview

This module provides:
- **Trochoidal insertion** (G2/G3 loops in overload zones) 🆕 L.3
- **Jerk-aware time estimation** (realistic runtime predictions) 🆕 L.3
- **True continuous spiral** (nearest-point ring stitching) L.2
- **Adaptive local stepover** (automatic densification near curves) L.2
- **Curvature-based respacing** (uniform engagement in tight zones) L.2 Merged
- **Per-move slowdown metadata** (feed scaling with meta.slowdown field) L.2 Merged
- **Heatmap visualization** (color-coded toolpath by speed) L.2 Merged
- **Min-fillet injection** (automatic arc insertion at sharp corners) L.2
- **HUD overlay system** (visual annotations for tight radii and slowdown zones) L.2
- **Robust polygon offsetting** with pyclipper (L.1)
- **Island/hole handling** with automatic keepout zones (L.1)
- **Min-radius smoothing controls** (rounded joins, arc tolerance) (L.1)
- **Multi-strategy support**: Spiral (continuous), Lanes (discrete passes)
- **Post-processor integration**: G-code export with headers/footers for 5 CNC platforms
- **Real-time statistics**: Classic + jerk-aware time, length, volume, tight segments, trochoid arcs
- **Interactive UI**: Vue component with canvas preview, heatmap, HUD overlays, and parameter controls

> **🔥 L.3 New:** See [PATCH_L3_SUMMARY.md](./PATCH_L3_SUMMARY.md) for trochoidal insertion and jerk-aware time estimation documentation.  
> **🔥 L.2 Merged:** See [PATCH_L2_MERGED_SUMMARY.md](./PATCH_L2_MERGED_SUMMARY.md) for details on the enhanced implementation with curvature-based respacing and heatmap visualization.  
> **🔥 L.2 Original:** See [PATCH_L2_TRUE_SPIRALIZER.md](./PATCH_L2_TRUE_SPIRALIZER.md) for original continuous spiral system documentation.  
> **🔥 L.1 Upgrade:** See [PATCH_L1_ROBUST_OFFSETTING.md](./PATCH_L1_ROBUST_OFFSETTING.md) for details on the production-grade polygon offsetting system.

---

## 📁 Architecture

### **Server Components** (`services/api/app/`)

```
cam/
├── adaptive_core.py              # L.0 Core offset engine (legacy)
├── adaptive_core_l1.py           # L.1 Robust pyclipper offsetting
├── adaptive_core_l2.py           # L.2 True spiralizer + fillets + HUD + respacing
├── adaptive_spiralizer_utils.py  # L.2 Merged: Curvature tools & respacing
├── trochoid_l3.py                # L.3 Trochoidal insertion for overload segments 🆕
├── feedtime_l3.py                # L.3 Jerk-aware time estimator 🆕
├── feedtime.py                   # Classic time estimation (rapid/feed awareness)
├── stock_ops.py                  # Material removal calculations
└── __init__.py

routers/
└── adaptive_router.py    # FastAPI endpoints (plan, gcode, sim) - uses L.3 ⭐
```

### **Client Components** (`packages/client/src/`)

```
components/
└── AdaptivePocketLab.vue  # Interactive pocket planning UI
```

### **CI/CD** (`.github/workflows/`)

```
workflows/
├── adaptive_pocket.yml    # API smoke tests
└── proxy_adaptive.yml     # Full stack tests via proxy
```

---

## 🔌 API Endpoints

### **POST `/api/cam/pocket/adaptive/plan`**
Generate adaptive pocket toolpath from boundary loops with island handling.

**Request:**
```json
{
  "loops": [
    {"pts": [[0,0], [100,0], [100,60], [0,60]]},  // Outer boundary (first loop)
    {"pts": [[30,15], [70,15], [70,45], [30,45]]} // Island/hole (optional) 🆕
  ],
  "units": "mm",
  "tool_d": 6.0,
  "stepover": 0.45,    // 45% of tool diameter
  "stepdown": 1.5,     // mm per pass
  "margin": 0.5,       // mm clearance from boundary
  "strategy": "Spiral", // or "Lanes"
  "smoothing": 0.3,    // arc tolerance (mm) for rounded joins 🆕
  "climb": true,       // climb vs conventional milling
  "feed_xy": 1200,     // mm/min
  "safe_z": 5,         // mm above work
  "z_rough": -1.5      // cutting depth
}
```

**Response:**
```json
{
  "moves": [
    {"code": "G0", "z": 5},
    {"code": "G0", "x": 3, "y": 3},
    {"code": "G1", "z": -1.5, "f": 1200},
    {"code": "G1", "x": 97, "y": 3, "f": 1200},
    ...
  ],
  "stats": {
    "length_mm": 547.3,
    "area_mm2": 6000.0,
    "time_s": 32.1,
    "volume_mm3": 9000.0,
    "move_count": 156
  }
}
```

### **POST `/api/cam/pocket/adaptive/gcode`**
Generate post-processor aware G-code.

**Request:** Same as `/plan` plus:
```json
{
  ...
  "post_id": "GRBL"  // GRBL, Mach4, LinuxCNC, PathPilot, MASSO
}
```

**Response:** G-code file with headers/footers
```gcode
G21
G90
G17
(POST=GRBL;UNITS=mm;DATE=2025-11-05T...)
G0 Z5.0000
G0 X3.0000 Y3.0000
G1 Z-1.5000 F1200.0
G1 X97.0000 Y3.0000 F1200.0
...
M30
(End of program)
```

### **POST `/api/cam/pocket/adaptive/sim`**
Simulate without generating full G-code.

**Request:** Same as `/plan`

**Response:**
```json
{
  "success": true,
  "stats": { ... },
  "moves": [ ... ]  // First 10 moves for preview
}
```

---

## 🎨 UI Component Usage

### **AdaptivePocketLab.vue**

```vue
<template>
  <AdaptivePocketLab/>
</template>

<script setup lang="ts">
import AdaptivePocketLab from '@/components/AdaptivePocketLab.vue'
</script>
```

**Features:**
- **Left Panel**: Parameter controls (tool, stepover, strategy, feeds, units, post)
- **Right Panel**: Canvas preview with geometry outline (gray) and toolpath (blue)
- **Stats HUD**: Length, area, time, volume, move count
- **Export**: One-click G-code download with post-processor headers

**Demo Geometry:** 100×60mm rectangle (replaceable with real geometry from upload)

---

## 🧮 Algorithms

### **1. Offset Stacking**
```python
# Start from tool/2 + margin inside boundary
offset_0 = boundary - (tool_d/2 + margin)

# Generate successive inward offsets
offset_1 = offset_0 - (tool_d * stepover)
offset_2 = offset_1 - (tool_d * stepover)
...
# Stop when area collapses or island collision
```

**Offset Method:**
- Vector normals at each vertex
- Bisector-based miter joins
- Clamp miter length to avoid spikes (max 10× offset)

### **2. Spiralizer**
```python
# Link offset rings into continuous path
path = ring_0
for ring in rings[1:]:
    # Find nearest point on next ring
    connect = nearest(path[-1], ring)
    # Append ring starting from connection
    path += ring[connect:] + ring[:connect]
```

**Benefits:**
- Single continuous toolpath (no retracts between rings)
- Reduced air time
- Better surface finish

### **3. Lane Fallback**
```python
# Just concatenate rings (discrete passes)
path = []
for ring in rings:
    path += ring
    # Implicit retract between rings
```

**Use Cases:**
- Shallow pockets where spiraling causes uneven depth
- When discrete passes preferred (stepdown control)

### **4. Time Estimation**
```python
time = 0
for move in moves:
    distance = sqrt((x2-x1)² + (y2-y1)² + (z2-z1)²)
    if move.code == 'G0':  # Rapid
        time += distance / rapid_feed
    elif 'z' in move:      # Plunge
        time += distance / plunge_feed
    else:                  # Cutting
        time += distance / cutting_feed
time *= 1.10  # 10% controller overhead
```

---

## 🧪 Testing

### **Local API Tests**

**L.1 Island Tests** (New):
```powershell
cd services/api
.\.venv\Scripts\Activate.ps1
pip install pyclipper==1.3.0.post5  # Install L.1 dependency
uvicorn app.main:app --reload --port 8000

# In another terminal:
cd ../..
.\test_adaptive_l1.ps1  # Runs island subtraction tests
```

**Basic Tests** (Original):
```powershell
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# In another terminal:
cd ../..
.\test_adaptive_pocket.ps1
```

**Expected Output:**
```
=== Testing Adaptive Pocketing Engine ===

1. Testing POST /api/cam/pocket/adaptive/plan
✓ Plan successful:
  Length: 547.3 mm
  Area: 6000.0 mm²
  Time: 32.1 s (0.54 min)
  Moves: 156
  Volume: 9000.0 mm³

2. Testing POST /api/cam/pocket/adaptive/gcode
✓ G-code generated (first 10 lines):
  G21
  G90
  G17
  (POST=GRBL;UNITS=mm;DATE=2025-11-05...)
  ...
  ✓ G21 (mm units) found
  ✓ G90 (absolute mode) found
  ✓ GRBL metadata found

3. Testing POST /api/cam/pocket/adaptive/sim
✓ Simulation successful

4. Testing pocket with island (basic)
✓ Pocket with island planned
```

### **CI Tests**
```bash
# GitHub Actions will automatically run:
# - adaptive_pocket.yml: API-only tests
# - proxy_adaptive.yml: Full stack through proxy
```

---

## 📊 Performance Characteristics

### **Typical Parameters**
| Parameter | Typical Range | Notes |
|-----------|---------------|-------|
| Tool Ø | 3-12 mm | End mill diameter |
| Stepover | 30-60% | % of tool diameter |
| Stepdown | 0.5-3 mm | Depth per pass |
| Feed XY | 800-2000 mm/min | Cutting feed |
| Safe Z | 5-10 mm | Retract height |

### **Example: 100×60mm Pocket**
- **Tool:** 6mm end mill
- **Stepover:** 45% (2.7mm)
- **Stepdown:** 1.5mm
- **Strategy:** Spiral

**Results:**
- **Path Length:** ~547mm
- **Time:** ~32 seconds
- **Moves:** ~156
- **Volume Removed:** ~9000 mm³

---

## 🚀 Usage Examples

### **Example 1: Simple Rectangular Pocket**
```typescript
const response = await fetch('/api/cam/pocket/adaptive/plan', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    loops: [
      {pts: [[0,0], [50,0], [50,30], [0,30]]}
    ],
    units: 'mm',
    tool_d: 6.0,
    stepover: 0.45,
    stepdown: 1.5,
    margin: 0.5,
    strategy: 'Spiral',
    climb: true,
    feed_xy: 1200,
    safe_z: 5,
    z_rough: -1.5
  })
})

const {moves, stats} = await response.json()
console.log(`Toolpath: ${stats.length_mm}mm in ${stats.time_s}s`)
```

### **Example 2: Export GRBL G-code**
```typescript
const response = await fetch('/api/cam/pocket/adaptive/gcode', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    loops: [{pts: [[0,0], [100,0], [100,60], [0,60]]}],
    units: 'mm',
    tool_d: 6.0,
    stepover: 0.45,
    stepdown: 1.5,
    strategy: 'Spiral',
    post_id: 'GRBL'
  })
})

const blob = await response.blob()
// Download as pocket_spiral_grbl.nc
```

### **Example 3: Lanes Strategy for Shallow Pocket**
```typescript
const response = await fetch('/api/cam/pocket/adaptive/plan', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    loops: [{pts: [[0,0], [80,0], [80,50], [0,50]]}],
    strategy: 'Lanes',  // Discrete passes instead of spiral
    stepover: 0.50,
    climb: false        // Conventional milling
  })
})
```

---

## 🔧 Configuration

### **Strategy Selection**

**Spiral** (Recommended for most cases)
- ✅ Continuous toolpath (no retracts)
- ✅ Faster cycle time
- ✅ Better surface finish
- ❌ Requires full-depth capability

**Lanes**
- ✅ Discrete depth control
- ✅ Better for shallow pockets
- ✅ Easier chipload management
- ❌ More retracts (longer time)

### **Stepover Guidelines**

| Material | Stepover |
|----------|----------|
| Softwood | 50-70% |
| Hardwood | 40-50% |
| Plywood | 30-45% |
| MDF | 45-60% |
| Acrylic | 40-50% |
| Aluminum | 30-40% |

### **Feed Rate Guidelines**

| Material | Feed (mm/min) |
|----------|---------------|
| Softwood | 1500-2500 |
| Hardwood | 1000-1800 |
| Plywood | 1200-2000 |
| MDF | 1500-2500 |
| Acrylic | 800-1500 |
| Aluminum | 500-1200 |

---

## 🐛 Troubleshooting

### **Issue**: Path self-intersects
**Solution**: Reduce stepover (try 30-40%) or increase margin

### **Issue**: Tool crashes into boundary
**Solution**: Increase margin (try 1.0-2.0mm)

### **Issue**: Time estimate too long
**Solution**: Increase feed rate or reduce stepover

### **Issue**: Spiral path skips rings
**Solution**: Check tool diameter vs pocket size ratio

---

## 🎯 Enhancement Roadmap

### **✅ L.1: Robust Offsetting + Island Subtraction** (IMPLEMENTED)
- ✅ Polygon clipping library integration (pyclipper)
- ✅ Proper island/hole handling with keepout zones
- ✅ Min radius guard with rounded joins and arc tolerance
- 📖 **See:** [PATCH_L1_ROBUST_OFFSETTING.md](./PATCH_L1_ROBUST_OFFSETTING.md)

### **✅ L.2: True Spiralizer + Adaptive Stepover + Min-Fillet + HUD** (IMPLEMENTED)
- ✅ Continuous spiral (nearest-point ring stitching)
- ✅ Adaptive local stepover (perimeter ratio heuristic)
- ✅ Min-fillet injection (automatic arc insertion at sharp corners)
- ✅ HUD overlay system (tight radius, slowdown, fillet markers)
- 📖 **See:** [PATCH_L2_TRUE_SPIRALIZER.md](./PATCH_L2_TRUE_SPIRALIZER.md)

### **🔜 L.3: Trochoidal Passes + Jerk-Aware Estimator** (Planned)
- Circular milling in tight corners (trochoidal arcs)
- Accel/jerk caps per machine profile
- Min-radius feed reduction

---

## 📚 See Also

- [Patch L.1: Robust Offsetting](./PATCH_L1_ROBUST_OFFSETTING.md) 🆕
- [Multi-Post Export System](./PATCH_K_EXPORT_COMPLETE.md)
- [Post-Processor Chooser](./POST_CHOOSER_SYSTEM.md)
- [Unit Conversion](./services/api/app/util/units.py)

---

## ✅ Integration Checklist

**Module L Core (L.0):**
- [x] Create `cam/` package with adaptive_core, feedtime, stock_ops
- [x] Create `routers/adaptive_router.py` with 3 endpoints
- [x] Register router in `main.py`
- [x] Create `AdaptivePocketLab.vue` component
- [x] Add CI workflow `adaptive_pocket.yml` (API tests)
- [x] Add CI workflow `proxy_adaptive.yml` (full stack)
- [x] Create test script `test_adaptive_pocket.ps1`

**L.1 Upgrade:**
- [x] Add `pyclipper==1.3.0.post5` to requirements.txt
- [x] Create `adaptive_core_l1.py` with robust offsetting
- [x] Update router to use `plan_adaptive_l1()`
- [x] Extend CI with island geometry tests
- [x] Create `test_adaptive_l1.ps1` for island validation
- [x] Document L.1 features and migration guide

**L.2 Upgrade:**
- [x] Add `numpy>=1.24.0` to requirements.txt
- [x] Create `adaptive_core_l2.py` with true spiralizer
- [x] Implement `inject_min_fillet()` for automatic arc insertion
- [x] Implement `adaptive_local_stepover()` for densification
- [x] Implement `true_spiral_from_rings()` for continuous paths
- [x] Implement `analyze_overloads()` for HUD overlay generation
- [x] Update router to use `plan_adaptive_l2()`
- [x] Extend PlanIn/PlanOut models with L.2 parameters and overlays
- [x] Add arc sampling for canvas preview
- [x] Update `AdaptivePocketLab.vue` with HUD controls and rendering
- [x] Extend CI with L.2 overlay assertions
- [x] Create `test_adaptive_l2.ps1` for comprehensive validation
- [x] Document L.2 features and algorithms

**Integration Tasks:**
- [x] Document API endpoints and algorithms
- [ ] Add to main navigation/router
- [ ] Replace demo geometry with real upload integration
- [ ] Implement trochoids (L.3)

---

**Status:** ✅ Module L Core + L.1 + L.2 Complete  
**Current Version:** L.2 (True Spiralizer + Adaptive Stepover + Min-Fillet + HUD)  
**Next Steps:** Wire AdaptivePocketLab into main UI navigation and test with real geometry uploads  
**Future:** L.3 (Trochoidal passes + jerk-aware motion planning)
