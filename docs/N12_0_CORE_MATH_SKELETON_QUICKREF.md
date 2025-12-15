# N12.0 Core Math Skeleton — Quick Reference

**Bundle:** #3 — N12.0 Core Math Skeleton  
**Date:** December 1, 2025  
**Status:** ✅ Complete (Drop-in form, coexists with N11 stubs)

---

## 🎯 Overview

Bundle #3 introduces the **N12.0 Core Math Skeleton** — a clean, structured foundation for real rosette geometry computations. This bundle:

- ✅ Defines **canonical dataclasses** for all rosette math objects
- ✅ Creates **structured engine interfaces** with stable signatures
- ✅ Implements **skeleton versions** using placeholder math (8-tile segmentation)
- ✅ **Coexists** with N11.2 stubs without breaking changes
- ✅ Provides **clear replacement path** for N12 real geometry implementation

**Key Design:** All engines return proper dataclasses (not dicts), use type hints, and have clean separation of concerns for easy module-by-module replacement.

---

## 📦 What's New in N12.0

### **8 New Files Created**

```
services/api/app/cam/rosette/
├── models.py                    # 7 dataclasses (NEW)
├── segmentation_engine.py       # Tile segmentation skeleton (NEW)
├── slice_engine.py              # Slice generation skeleton (NEW)
├── kerf_engine.py               # Kerf physics skeleton (NEW)
├── twist_engine.py              # Twist & herringbone skeleton (NEW)
├── ring_engine.py               # Ring orchestrator skeleton (NEW)
├── preview_engine.py            # Preview builder skeleton (NEW)
└── __init__.py                  # Updated exports (N11 + N12)
```

### **N11.2 Stubs Still Active**

```python
# These continue to work unchanged for existing API endpoints
from app.cam.rosette import (
    compute_tile_segmentation_stub,
    apply_kerf_compensation_stub,
    apply_herringbone_stub,
    generate_saw_batch_stub,
)
```

### **N12.0 Skeleton Engines Available**

```python
# New structured engines (not yet wired into API)
from app.cam.rosette import (
    RosetteRingConfig,
    SegmentationResult,
    SliceBatch,
    compute_tile_segmentation,
    generate_slices_for_ring,
    apply_kerf_physics,
    apply_twist,
    apply_herringbone_engine,
    compute_ring_geometry,
)
```

---

## 🏗️ Core Data Model (models.py)

### **RosetteRingConfig**
```python
@dataclass
class RosetteRingConfig:
    ring_id: int
    radius_mm: float
    width_mm: float
    tile_length_mm: float
    kerf_mm: float = 0.3
    herringbone_angle_deg: float = 0.0
    twist_angle_deg: float = 0.0
```

**Usage:**
```python
ring = RosetteRingConfig(
    ring_id=1,
    radius_mm=45.0,
    width_mm=8.0,
    tile_length_mm=12.0,
    kerf_mm=0.3,
    herringbone_angle_deg=22.5,
    twist_angle_deg=5.0,
)
```

### **Tile**
```python
@dataclass
class Tile:
    tile_index: int
    theta_start_deg: float
    theta_end_deg: float
```

**Represents:** A single angular segment of a ring (before saw cutting).

### **SegmentationResult**
```python
@dataclass
class SegmentationResult:
    segmentation_id: str
    ring_id: int
    tile_count: int
    tile_length_mm: float
    tiles: List[Tile] = field(default_factory=list)
```

**Represents:** Complete ring segmentation into tiles.

### **Slice**
```python
@dataclass
class Slice:
    slice_index: int
    tile_index: int
    angle_raw_deg: float          # Before kerf/twist/herringbone
    angle_final_deg: float        # After all adjustments
    
    theta_start_deg: float
    theta_end_deg: float
    
    kerf_mm: float = 0.0
    herringbone_flip: bool = False
    herringbone_angle_deg: float = 0.0
    twist_angle_deg: float = 0.0
```

**Represents:** A single saw cut with all physics applied.

**Future Fields (commented out for N12.0):**
```python
# start_x_mm: float = 0.0
# start_y_mm: float = 0.0
# end_x_mm: float = 0.0
# end_y_mm: float = 0.0
```

### **SliceBatch**
```python
@dataclass
class SliceBatch:
    batch_id: str
    ring_id: int
    slices: List[Slice] = field(default_factory=list)
```

**Represents:** Complete set of slices for one ring.

### **MultiRingAssembly**
```python
@dataclass
class MultiRingAssembly:
    pattern_id: Optional[str] = None
    rings: List[RosetteRingConfig] = field(default_factory=list)
    segmentations: Dict[int, SegmentationResult] = field(default_factory=dict)
    slice_batches: Dict[int, SliceBatch] = field(default_factory=dict)
```

**Represents:** Multi-ring rosette assembly (placeholder for N12 cross-ring alignment).

### **PreviewSnapshot**
```python
@dataclass
class PreviewSnapshot:
    pattern_id: Optional[str] = None
    rings: List[RosetteRingConfig] = field(default_factory=list)
    payload: Dict[str, Any] = field(default_factory=dict)
```

**Represents:** Preview data for UI rendering (will carry SVG/Canvas data in N12).

---

## 🔧 Engine Architecture

### **Data Flow Pipeline**

```
RosetteRingConfig
    ↓
compute_tile_segmentation()
    ↓
SegmentationResult (with Tiles)
    ↓
generate_slices_for_ring()
    ↓
SliceBatch (with raw Slices)
    ↓
apply_kerf_physics()
    ↓
apply_twist()
    ↓
apply_herringbone()
    ↓
SliceBatch (with final Slices)
```

### **Orchestration Layer**

```python
# ring_engine.py
def compute_ring_geometry(ring: RosetteRingConfig) -> tuple[SegmentationResult, SliceBatch]:
    seg = compute_tile_segmentation(ring)
    batch = generate_slices_for_ring(ring, seg)
    
    kerfed = apply_kerf_physics(ring, batch.slices)
    twisted = apply_twist(ring, kerfed)
    final = apply_herringbone(ring, twisted)
    
    batch.slices = final
    return seg, batch
```

**Usage:**
```python
from app.cam.rosette import RosetteRingConfig, compute_ring_geometry

ring = RosetteRingConfig(ring_id=1, radius_mm=45, width_mm=8, tile_length_mm=12)
segmentation, slice_batch = compute_ring_geometry(ring)

print(f"Tiles: {segmentation.tile_count}")
print(f"Slices: {len(slice_batch.slices)}")
```

---

## 📐 Engine APIs

### **1. Segmentation Engine (segmentation_engine.py)**

```python
def compute_tile_segmentation(
    ring: RosetteRingConfig,
    tile_count_override: Optional[int] = None,
) -> SegmentationResult
```

**N12.0 Skeleton Behavior:**
- Uses fixed 8-tile segmentation (or `tile_count_override`)
- Equally spaced tiles around 360 degrees
- Returns proper `SegmentationResult` dataclass

**N12 Final Behavior (Future):**
- Derive tile count from `circumference / tile_length_mm`
- Compute effective tile length (eliminates fractional leftover)
- Apply tile count constraints (min 2, max 300)

**Example:**
```python
from app.cam.rosette import RosetteRingConfig, compute_tile_segmentation

ring = RosetteRingConfig(ring_id=1, radius_mm=45, width_mm=8, tile_length_mm=12)
seg = compute_tile_segmentation(ring)

print(f"Segmentation ID: {seg.segmentation_id}")
print(f"Tile count: {seg.tile_count}")  # 8 (skeleton default)

for tile in seg.tiles:
    print(f"Tile {tile.tile_index}: {tile.theta_start_deg:.1f}° → {tile.theta_end_deg:.1f}°")
```

**Output:**
```
Segmentation ID: seg_ring_1_tc_8
Tile count: 8
Tile 0: 0.0° → 45.0°
Tile 1: 45.0° → 90.0°
Tile 2: 90.0° → 135.0°
...
```

---

### **2. Slice Engine (slice_engine.py)**

```python
def generate_slices_for_ring(
    ring: RosetteRingConfig,
    segmentation: SegmentationResult,
) -> SliceBatch
```

**N12.0 Skeleton Behavior:**
- Creates one slice per tile
- Sets `angle_raw_deg` to tile center angle
- `angle_final_deg` initially equals `angle_raw_deg`
- Copies ring parameters (kerf, herringbone, twist) into slice metadata

**N12 Final Behavior (Future):**
- Compute `angle_raw_deg` from tangent + 90° at ring circumference
- Incorporate radius and width into geometry
- Add 2D coordinate fields (start_x_mm, start_y_mm, end_x_mm, end_y_mm)

**Example:**
```python
from app.cam.rosette import (
    RosetteRingConfig,
    compute_tile_segmentation,
    generate_slices_for_ring,
)

ring = RosetteRingConfig(ring_id=1, radius_mm=45, width_mm=8, tile_length_mm=12, kerf_mm=0.3)
seg = compute_tile_segmentation(ring)
batch = generate_slices_for_ring(ring, seg)

print(f"Batch ID: {batch.batch_id}")
print(f"Slices: {len(batch.slices)}")

for s in batch.slices[:3]:
    print(f"Slice {s.slice_index}: raw={s.angle_raw_deg:.1f}°, final={s.angle_final_deg:.1f}°")
```

**Output:**
```
Batch ID: slice_batch_ring_1
Slices: 8
Slice 0: raw=22.5°, final=22.5°
Slice 1: raw=67.5°, final=67.5°
Slice 2: raw=112.5°, final=112.5°
```

---

### **3. Kerf Engine (kerf_engine.py)**

```python
def apply_kerf_physics(
    ring: RosetteRingConfig,
    slices: List[Slice],
) -> List[Slice]
```

**N12.0 Skeleton Behavior:**
- Leaves `angle_final_deg` unchanged
- Ensures `Slice.kerf_mm` reflects ring kerf

**N12 Final Behavior (Future):**
- Compute `kerf_angle_deg = (kerf_mm / radius_mm) * (180 / π)`
- Adjust `angle_final_deg` for each slice
- Track drift accumulation and enforce constraints

**Example:**
```python
from app.cam.rosette import apply_kerf_physics

# Assume we have slices from previous step
kerfed_slices = apply_kerf_physics(ring, batch.slices)

for s in kerfed_slices[:3]:
    print(f"Slice {s.slice_index}: kerf={s.kerf_mm}mm")
```

**Output:**
```
Slice 0: kerf=0.3mm
Slice 1: kerf=0.3mm
Slice 2: kerf=0.3mm
```

---

### **4. Twist Engine (twist_engine.py)**

```python
def apply_twist(
    ring: RosetteRingConfig,
    slices: List[Slice],
) -> List[Slice]

def apply_herringbone(
    ring: RosetteRingConfig,
    slices: List[Slice],
) -> List[Slice]
```

**N12.0 Skeleton Behavior:**

**apply_twist:**
- Leaves `angle_final_deg` unchanged
- Copies `twist_angle_deg` into slice metadata

**apply_herringbone:**
- Sets `herringbone_flip = (index % 2 == 1)` (odd/even alternation)
- Copies `herringbone_angle_deg` into slice metadata
- Leaves `angle_final_deg` unchanged

**N12 Final Behavior (Future):**

**apply_twist:**
- `angle_final_deg += ring.twist_angle_deg`
- Normalize angles into [0, 360) range

**apply_herringbone:**
- Alternate sign of herringbone angle: `angle_final_deg += (±herringbone_angle_deg)`
- Adjust based on `herringbone_flip` flag

**Example:**
```python
from app.cam.rosette import apply_twist, apply_herringbone

# Apply twist
twisted = apply_twist(ring, kerfed_slices)

# Apply herringbone
final_slices = apply_herringbone(ring, twisted)

for s in final_slices[:3]:
    print(f"Slice {s.slice_index}: flip={s.herringbone_flip}, twist={s.twist_angle_deg}°, hb={s.herringbone_angle_deg}°")
```

**Output:**
```
Slice 0: flip=False, twist=0.0°, hb=0.0°
Slice 1: flip=True, twist=0.0°, hb=0.0°
Slice 2: flip=False, twist=0.0°, hb=0.0°
```

---

### **5. Ring Engine (ring_engine.py)**

```python
def compute_ring_geometry(
    ring: RosetteRingConfig,
) -> tuple[SegmentationResult, SliceBatch]
```

**Purpose:** Orchestrates full ring geometry computation in one call.

**N12.0 Skeleton Behavior:**
- Runs all engines in sequence (segmentation → slices → kerf → twist → herringbone)
- Returns final `SegmentationResult` and `SliceBatch` with all physics applied

**Example:**
```python
from app.cam.rosette import RosetteRingConfig, compute_ring_geometry

ring = RosetteRingConfig(
    ring_id=1,
    radius_mm=45.0,
    width_mm=8.0,
    tile_length_mm=12.0,
    kerf_mm=0.3,
    herringbone_angle_deg=22.5,
    twist_angle_deg=5.0,
)

segmentation, slice_batch = compute_ring_geometry(ring)

print(f"✓ Segmented into {segmentation.tile_count} tiles")
print(f"✓ Generated {len(slice_batch.slices)} slices")
print(f"✓ Applied kerf: {slice_batch.slices[0].kerf_mm}mm")
print(f"✓ Applied herringbone: {slice_batch.slices[1].herringbone_flip}")
```

**Output:**
```
✓ Segmented into 8 tiles
✓ Generated 8 slices
✓ Applied kerf: 0.3mm
✓ Applied herringbone: True
```

---

### **6. Preview Engine (preview_engine.py)**

```python
def build_preview_snapshot(
    pattern_id: str | None,
    rings: List[RosetteRingConfig],
    segmentations: Dict[int, SegmentationResult],
    slice_batches: Dict[int, SliceBatch],
) -> PreviewSnapshot
```

**N12.0 Skeleton Behavior:**
- Returns minimal summary dict with tile/slice counts per ring

**N12 Final Behavior (Future):**
- Generate SVG paths / Canvas drawing instructions
- Produce downsampled raster previews

**Example:**
```python
from app.cam.rosette import build_preview_snapshot

rings = [ring1, ring2, ring3]
segmentations = {1: seg1, 2: seg2, 3: seg3}
slice_batches = {1: batch1, 2: batch2, 3: batch3}

snapshot = build_preview_snapshot("pattern_001", rings, segmentations, slice_batches)

print(f"Pattern ID: {snapshot.pattern_id}")
print(f"Rings: {len(snapshot.rings)}")
print(f"Payload keys: {list(snapshot.payload.keys())}")
```

**Output:**
```
Pattern ID: pattern_001
Rings: 3
Payload keys: ['rings']
```

---

## 🔗 Integration Status

### **N11.2 API Endpoints (Still Active)**

```python
# services/api/app/api/routes/rmos_rosette_api.py
POST /api/rmos/rosette/segment-ring
POST /api/rmos/rosette/generate-slices
GET  /api/rmos/rosette/patterns
```

**Current Behavior:** Uses N11.2 stubs (dict-based returns)

### **N12.0 Engines (Available, Not Wired)**

```python
# New engines exist but are not yet used by API endpoints
from app.cam.rosette import (
    compute_tile_segmentation,    # ← Not yet replacing compute_tile_segmentation_stub
    generate_slices_for_ring,     # ← Not yet replacing generate_saw_batch_stub
    compute_ring_geometry,        # ← New orchestrator
)
```

**Next Bundle (N12.1 Planned):** Wire N12.0 engines into API endpoints with backward-compatible responses.

---

## ✅ Verification Checklist

### **Manual Testing (Python REPL)**

```powershell
cd services/api
.\.venv\Scripts\Activate.ps1
python
```

```python
from app.cam.rosette import (
    RosetteRingConfig,
    compute_tile_segmentation,
    generate_slices_for_ring,
    compute_ring_geometry,
)

# Test 1: Segmentation
ring = RosetteRingConfig(ring_id=1, radius_mm=45, width_mm=8, tile_length_mm=12)
seg = compute_tile_segmentation(ring)
print(f"✓ Segmentation: {seg.tile_count} tiles")
assert seg.tile_count == 8
assert len(seg.tiles) == 8

# Test 2: Slice generation
batch = generate_slices_for_ring(ring, seg)
print(f"✓ Slices: {len(batch.slices)} slices")
assert len(batch.slices) == 8

# Test 3: Full ring geometry
seg2, batch2 = compute_ring_geometry(ring)
print(f"✓ Full geometry: {seg2.tile_count} tiles, {len(batch2.slices)} slices")
assert seg2.tile_count == 8
assert len(batch2.slices) == 8

print("\n✅ All N12.0 skeleton tests passed!")
```

### **Import Test**

```python
# Verify all N12.0 exports available
from app.cam.rosette import (
    RosetteRingConfig,
    SegmentationResult,
    SliceBatch,
    MultiRingAssembly,
    PreviewSnapshot,
    compute_tile_segmentation,
    generate_slices_for_ring,
    apply_kerf_physics,
    apply_twist,
    apply_herringbone_engine,
    compute_ring_geometry,
    build_preview_snapshot,
)

print("✓ All N12.0 imports successful")
```

### **Coexistence Test**

```python
# Verify N11.2 stubs still work
from app.cam.rosette import (
    compute_tile_segmentation_stub,
    apply_kerf_compensation_stub,
    apply_herringbone_stub,
    generate_saw_batch_stub,
)

ring_dict = {"ring_id": 1, "radius_mm": 45, "width_mm": 8, "tile_length_mm": 12}
seg_stub = compute_tile_segmentation_stub(ring_dict)

print(f"✓ N11.2 stub still works: {seg_stub['tile_count']} tiles")
assert seg_stub['tile_count'] == 8
```

---

## 🚀 Next Steps

### **Bundle #4 (N12.1 Planned): API Integration**

Wire N12.0 engines into existing API endpoints:

```python
# services/api/app/api/routes/rmos_rosette_api.py (future update)

@router.post("/segment-ring")
def segment_ring(body: SegmentRingRequest):
    # Convert dict to RosetteRingConfig
    ring = RosetteRingConfig(**body.ring.dict())
    
    # Use N12.0 engine
    seg = compute_tile_segmentation(ring)
    
    # Convert dataclass back to dict for JSON response (backward compatible)
    return {
        "segmentation_id": seg.segmentation_id,
        "ring_id": seg.ring_id,
        "tile_count": seg.tile_count,
        "tiles": [{"tile_index": t.tile_index, "theta_start_deg": t.theta_start_deg, ...} for t in seg.tiles]
    }
```

### **Bundle #5+ (N12.x Planned): Real Geometry**

Replace skeleton implementations with real math:

1. **N12.2: Real Segmentation**
   - Circumference-based tile count derivation
   - Effective tile length calculation
   - Tile count constraints (min 2, max 300)

2. **N12.3: Real Slice Geometry**
   - Tangent + 90° angle computation
   - 2D coordinate calculation (start_x_mm, end_x_mm, etc.)
   - Ring width incorporation

3. **N12.4: Real Kerf Physics**
   - Angular kerf computation: `kerf_angle_deg = (kerf_mm / radius_mm) * (180 / π)`
   - Drift accumulation tracking
   - Constraints enforcement

4. **N12.5: Real Twist & Herringbone**
   - Twist offset: `angle_final_deg += twist_angle_deg`
   - Herringbone alternation: `angle_final_deg += (±herringbone_angle_deg)`
   - Angle normalization [0, 360)

5. **N12.6: SVG Preview Generation**
   - Path commands from slice coordinates
   - Color coding by material
   - Canvas-ready output

---

## 📚 Reference

### **Files Created (8 total)**

```
services/api/app/cam/rosette/
├── models.py                    # 101 lines - 7 dataclasses
├── segmentation_engine.py       # 56 lines - Tile segmentation skeleton
├── slice_engine.py              # 52 lines - Slice generation skeleton
├── kerf_engine.py               # 33 lines - Kerf physics skeleton
├── twist_engine.py              # 58 lines - Twist & herringbone skeleton
├── ring_engine.py               # 42 lines - Ring orchestrator skeleton
├── preview_engine.py            # 61 lines - Preview builder skeleton
└── __init__.py                  # 50 lines - Updated exports (N11 + N12)
```

### **Total Code Added:** ~453 lines (excluding comments/docstrings)

### **Dependencies Added:** None (uses stdlib only: `dataclasses`, `typing`, `math`)

### **Breaking Changes:** None (N11.2 stubs remain active)

---

## 🎯 Summary

**Bundle #3 — N12.0 Core Math Skeleton delivers:**

✅ **Clean separation of concerns** — 6 focused engines (segmentation, slice, kerf, twist, ring, preview)  
✅ **Type-safe interfaces** — Dataclasses with type hints throughout  
✅ **Stable signatures** — Public APIs won't change when filling in real math  
✅ **Backward compatible** — N11.2 stubs untouched, existing API works  
✅ **Module-by-module replacement** — Each engine can be upgraded independently  
✅ **Documentation-driven** — Clear N12.0 vs N12 final behavior comments  

**Ready for:** N12.1 API wiring (convert dict ↔ dataclass at boundaries) and N12.x real geometry implementation.

---

**Status:** ✅ Bundle #3 Complete — N12.0 Core Math Skeleton Merged  
**Next Bundle:** N12.1 API Integration (wire N12.0 engines into FastAPI endpoints)  
**Future Bundles:** N12.2–N12.6 (real circumference math, kerf physics, twist/herringbone, SVG preview)
