# N18 Spiral PolyCut - Quick Reference

**Status:** ✅ Production Ready  
**Version:** Phase 4 Complete (Offsetting + Spiral + Arc Smoothing + Validation Suite)  
**Location:** `services/api/app/util/poly_offset_spiral.py`

**Release Notes:** See [N18_SPIRAL_POLYCUT_RELEASE_NOTES.md](docs/releases/N18_SPIRAL_POLYCUT_RELEASE_NOTES.md)

---

## 🎯 What is N18?

Production-grade **polygon spiral pocketing** for CNC guitar lutherie with:
- **Robust offsetting** using pyclipper (no floating-point drift)
- **Spiral stitching** (concentric rings → continuous path)
- **Arc smoothing** (G2/G3-ready geometry)

Designed for **bridge slots, thin strips, and small rectangular pockets** in hardwoods.

---

## 🚀 Quick Start

### Import and Use

```python
from app.util.poly_offset_spiral import build_spiral_poly

# Define pocket boundary (closed polygon)
outer = [(0, 0), (100, 0), (100, 60), (0, 60), (0, 0)]

# Generate spiral toolpath
spiral = build_spiral_poly(
    outer=outer,
    tool_d=6.0,              # Tool diameter (mm)
    stepover=0.45,           # 45% of tool diameter
    margin=0.5,              # Wall clearance (mm)
    climb=True,              # Climb milling (CCW)
    corner_radius_min=1.0,   # Arc smoothing radius (mm)
    corner_tol_mm=0.3,       # Arc tolerance (mm)
)

# Result: List of (x, y) points ready for G-code
print(f"Spiral has {len(spiral)} points")
```

---

## 📋 API Reference

### `build_spiral_poly()`

**Main entry point** for N18 spiral generation.

```python
def build_spiral_poly(
    outer: Sequence[Point],
    tool_d: float,
    stepover: float,
    margin: float,
    *,
    climb: bool = True,
    corner_radius_min: Optional[float] = None,
    corner_tol_mm: Optional[float] = None,
) -> Path
```

**Parameters:**
- `outer`: Boundary polygon as list of (x, y) tuples (mm)
- `tool_d`: Tool diameter in mm (e.g., 6.0 for 6mm end mill)
- `stepover`: Fraction of tool diameter (0.3-0.7, typically 0.45)
- `margin`: Wall clearance in mm (typically 0.5-1.0mm)
- `climb`: True for climb milling (CCW), False for conventional (CW)
- `corner_radius_min`: Minimum fillet radius for arc smoothing (mm)
- `corner_tol_mm`: Arc tolerance for smoothing (mm)

**Returns:** List of (x, y) points forming continuous spiral path

**Raises:** `ValueError` if inputs invalid (e.g., tool too large, bad stepover)

---

### Phase 1: `offset_polygon_mm()`

**Low-level** concentric offset generator (onion-skin rings).

```python
def offset_polygon_mm(
    outer: Sequence[Point],
    offset_step: float,
    *,
    max_rings: int = 256,
    min_area_mm2: float = 0.5,
    miter_limit: float = 4.0,
    arc_tolerance: float = 0.05,
) -> Paths
```

Returns list of inward offset rings (outermost first).

---

### Phase 2: `generate_offset_rings()` + `link_rings_to_spiral()`

**Mid-level** helpers for ring-to-spiral conversion.

```python
def generate_offset_rings(
    outer: Sequence[Point],
    tool_d: float,
    stepover: float,
    margin: float,
    *,
    max_rings: int = 256,
) -> Paths

def link_rings_to_spiral(
    rings: Paths,
    *,
    climb: bool = True,
) -> Path
```

---

### Phase 3: `smooth_with_arcs()`

**Arc smoothing** for sharp corners.

```python
def smooth_with_arcs(
    path: Sequence[Point],
    corner_radius_min: float,
    corner_tol_mm: float,
) -> Path
```

Inserts circular fillets at corners exceeding angle threshold.

---

## 🧪 Testing

### Run Baseline Tests

```powershell
# From repo root
cd services/api
python scripts/validate_n18_baseline.py
```

**Expected output:**
```
============================================================
N18 Spiral PolyCut - Baseline Validation
============================================================

============================================================
Testing: Small Rect (100×60mm)
============================================================
✓ Loaded geometry: geom_small_rect.json
✓ Generated spiral: 156 points
✓ Spiral structure valid
✓ Total path length: 547.32mm
✓ Spiral bounds valid

✅ Small Rect (100×60mm): PASS

[... similar for Bridge Slot and Thin Strip ...]

============================================================
Summary
============================================================

Passed: 3/3

✅ All N18 baselines PASS
```

### Run pytest Suite

```powershell
pytest tests/test_n18_spiral_gcode.py -v
```

---

## 🎮 REST API

### Endpoint: `POST /cam/adaptive3/offset_spiral.nc`

**Request:**
```json
{
  "polygon": [[0,0], [100,0], [100,60], [0,60], [0,0]],
  "tool_dia": 6.0,
  "stepover": 2.7,
  "z": -1.5,
  "safe_z": 5.0,
  "base_feed": 1200.0,
  "min_R": 1.0,
  "arc_tol": 0.3
}
```

**Response:** G-code file (text/plain)
```gcode
( N18 Spiral PolyCut - Simple G-code )
G90 G21
G0 Z5.0000
G0 X3.5000 Y3.5000
G1 Z-1.5000 F600.0
G1 X96.5000 Y3.5000 F1200.0
G1 X96.5000 Y56.5000 F1200.0
...
G0 Z5.0000
M30
(END)
```

---

## ⚙️ Configuration

### Typical Parameters

| Material | Stepover | Margin | Corner Radius |
|----------|----------|--------|---------------|
| **Softwood** | 0.50-0.60 | 0.5mm | 1.0mm |
| **Hardwood** | 0.40-0.50 | 0.8mm | 1.2mm |
| **Plywood** | 0.35-0.45 | 0.5mm | 0.8mm |
| **MDF** | 0.50-0.65 | 0.3mm | 0.6mm |
| **Acrylic** | 0.40-0.50 | 1.0mm | 1.5mm |

### Tool Recommendations

| Tool Ø | Use Case | Feed Rate |
|--------|----------|-----------|
| **3.175mm (1/8")** | Thin slots, detail work | 600-1000 mm/min |
| **6.0mm (1/4")** | General pockets, bridges | 1000-1800 mm/min |
| **12.7mm (1/2")** | Large pockets, roughing | 1500-2500 mm/min |

---

## 🐛 Troubleshooting

### Issue: `RuntimeError: pyclipper is required`

**Solution:** Install dependency
```powershell
pip install pyclipper==1.3.0.post5
```

### Issue: Spiral extends outside boundary

**Symptoms:** Tool crashes into walls

**Solution:**
- Increase `margin` (try 1.0-2.0mm)
- Reduce `stepover` (try 0.35-0.40)
- Check outer polygon orientation (should be CCW for outer boundary)

### Issue: Too many points / slow simulation

**Symptoms:** 1000+ points, sluggish UI

**Solution:**
- Increase `stepover` (try 0.55-0.65)
- Increase `corner_tol_mm` (try 0.5-0.8mm)
- Simplify input geometry (fewer vertices)

### Issue: Gaps in spiral (discontinuous)

**Symptoms:** Missing connections between rings

**Solution:** This shouldn't happen with N18. If it does:
- Check `link_rings_to_spiral()` output
- Verify rings list is not empty
- File bug report with geometry

---

## 📊 Performance

### Typical Results

| Pocket Size | Tool Ø | Spiral Points | Generation Time | Path Length |
|-------------|---------|---------------|-----------------|-------------|
| 100×60mm    | 6mm     | ~150-180      | <5ms            | ~550mm      |
| 140×18mm    | 3.175mm | ~180-220      | <8ms            | ~480mm      |
| 200×12mm    | 6mm     | ~200-250      | <10ms           | ~620mm      |

**Hardware:** Typical development machine (Intel i5/i7, 16GB RAM)

---

## 🔗 Integration Points

### With Adaptive Pocketing L.1

N18 can **replace** the vector-normal offsetting in `adaptive_core_l1.py`:

```python
# Old approach (basic vector offsetting)
from ..cam.adaptive_core_l1 import build_offset_stacks_robust

# N18 approach (production pyclipper)
from ..util.poly_offset_spiral import generate_offset_rings, link_rings_to_spiral

rings = generate_offset_rings(outer, tool_d, stepover, margin)
spiral = link_rings_to_spiral(rings, climb=True)
```

### With DXF Import (Phase 27.0)

```python
# adaptive_router.py /plan_from_dxf endpoint
loops = _dxf_to_loops_from_bytes(dxf_data)
outer = loops[0]

# Use N18 for spiral generation
spiral = build_spiral_poly(outer, tool_d, stepover, margin)

# Convert to moves for G-code emission
moves = to_toolpath(spiral, feed_xy, safe_z, z_rough)
```

---

## 📚 See Also

- **PATCH_L1_ROBUST_OFFSETTING.md**: L.1 pyclipper integration details
- **ADAPTIVE_POCKETING_MODULE_L.md**: Complete adaptive system overview
- **COMPLETE_BUNDLE_EXTRACTION_PLAN.md**: N18 extraction roadmap (Bundle 3, lines 1-2236)
- **N18_SPIRAL_POLYCUT_RELEASE_NOTES.md**: Full feature documentation

---

## ✅ Status Checklist

- [x] Phase 1: Robust offsetting (`offset_polygon_mm`)
- [x] Phase 2: Spiral stitching (`link_rings_to_spiral`)
- [x] Phase 3: Arc smoothing (`smooth_with_arcs`)
- [x] Baseline test geometries (3 cases)
- [x] Validation script (`validate_n18_baseline.py`)
- [x] REST API endpoint (`/cam/adaptive3/offset_spiral.nc`)
- [x] pytest test suite (`test_n18_spiral_gcode.py`)
- [ ] Integration with adaptive_core_l1.py (optional upgrade)
- [ ] G2/G3 arc emission (currently outputs linear moves)
- [ ] CI/CD pipeline integration (GitHub Actions)

---

**Version:** N.18 Phase 3  
**Status:** ✅ Production Ready  
**Dependencies:** `pyclipper==1.3.0.post5`  
**Author:** Luthier's Tool Box Team  
**Date:** November 2025
