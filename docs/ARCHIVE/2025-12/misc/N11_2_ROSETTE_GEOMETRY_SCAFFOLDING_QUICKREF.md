# N11.2 — Rosette Geometry Engine Scaffolding Quick Reference

**Bundle:** N11.2 (Drop-in Style)  
**Status:** ✅ Complete  
**Date:** December 1, 2025  
**Dependencies:** N11.1 (Rosette Pattern Scaffolding)

---

## 🎯 Overview

N11.2 adds the **complete vertical slice** for the RMOS Studio rosette designer - from UI to backend geometry engine. All components use **placeholder/stub implementations** so it's safe to merge before implementing real geometry calculations in N12.

**What's New:**
- ✅ Backend: `cam/rosette/` package with 5 stub geometry modules
- ✅ Backend: 3 REST API endpoints (`/segment-ring`, `/generate-slices`, `/patterns`)
- ✅ Frontend: Pinia store for rosette designer state management
- ✅ Frontend: Main view + 3 stub UI components
- ✅ Frontend: Router registration at `/rmos/rosette-designer`

**Key Feature:** Complete end-to-end flow works with dummy 8-tile segmentation and placeholder geometry.

---

## 📦 Components

### **1. Backend: cam/rosette Package**

**Location:** `services/api/app/cam/rosette/`

**Files Created:**

#### `__init__.py` (Package Exports)
```python
from .tile_segmentation import compute_tile_segmentation_stub
from .kerf_compensation import apply_kerf_compensation_stub
from .herringbone import apply_herringbone_stub
from .saw_batch_generator import generate_saw_batch_stub

__all__ = [
    "compute_tile_segmentation_stub",
    "apply_kerf_compensation_stub",
    "apply_herringbone_stub",
    "generate_saw_batch_stub",
]
```

#### `tile_segmentation.py` (8-Tile Stub)
```python
def compute_tile_segmentation_stub(ring: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns 8-tile dummy segmentation.
    N12 will implement real circumference-based calculations.
    """
    # Returns: segmentation_id, ring_id, tile_count, tiles[]
```

#### `kerf_compensation.py` (Passthrough Stub)
```python
def apply_kerf_compensation_stub(slices, kerf_mm) -> List[Dict]:
    """
    Attaches kerf_mm field to each slice.
    N12 will implement angular compensation.
    """
```

#### `herringbone.py` (Flip Flag Stub)
```python
def apply_herringbone_stub(slices, herringbone_angle_deg) -> List[Dict]:
    """
    Alternates herringbone_flip boolean on each slice.
    N12 will apply real angle transformations.
    """
```

#### `saw_batch_generator.py` (Slice Batch Stub)
```python
def generate_saw_batch_stub(ring_id, segmentation) -> Dict[str, Any]:
    """
    Converts tiles to slices with angle data.
    N12 will add real geometry coordinates.
    """
```

---

### **2. Backend: Rosette API Router**

**File:** `services/api/app/api/routes/rmos_rosette_api.py`

**Endpoints:**

#### `POST /api/rmos/rosette/segment-ring`
Compute tile segmentation for a ring.

**Request:**
```json
{
  "ring": {
    "ring_id": 0,
    "radius_mm": 45.0,
    "width_mm": 3.0,
    "tile_length_mm": 5.0,
    "kerf_mm": 0.3,
    "herringbone_angle_deg": 0.0,
    "twist_angle_deg": 0.0
  }
}
```

**Response:**
```json
{
  "segmentation_id": "seg_stub_0",
  "ring_id": 0,
  "tile_count": 8,
  "tile_length_mm": 5.0,
  "tiles": [
    {
      "tile_index": 0,
      "theta_start_deg": 0.0,
      "theta_end_deg": 45.0
    },
    ...
  ]
}
```

---

#### `POST /api/rmos/rosette/generate-slices`
Generate saw slices from segmentation with kerf and herringbone.

**Request:**
```json
{
  "ring_id": 0,
  "segmentation": {
    "segmentation_id": "seg_stub_0",
    "ring_id": 0,
    "tile_count": 8,
    "tiles": [...]
  },
  "kerf_mm": 0.3,
  "herringbone_angle_deg": 0.0
}
```

**Response:**
```json
{
  "batch_id": "saw_batch_stub_0",
  "ring_id": 0,
  "slices": [
    {
      "slice_index": 0,
      "tile_index": 0,
      "angle_deg": 22.5,
      "theta_start_deg": 0.0,
      "theta_end_deg": 45.0,
      "kerf_mm": 0.3,
      "herringbone_flip": false,
      "herringbone_angle_deg": 0.0
    },
    ...
  ]
}
```

---

#### `GET /api/rmos/rosette/patterns`
List all rosette patterns (from N11.1 PatternStore).

**Response:**
```json
{
  "patterns": [
    {
      "pattern_id": "rosette_001",
      "name": "Spanish Traditional 5-Ring",
      "pattern_type": "rosette",
      "ring_count": 5,
      "rosette_geometry": {...},
      "metadata": {...}
    }
  ]
}
```

---

### **3. Frontend: Pinia Store**

**File:** `packages/client/src/stores/useRosetteDesignerStore.ts`

**State:**
```typescript
interface RosetteRing {
  ring_id: number
  radius_mm: number
  width_mm: number
  tile_length_mm: number
  kerf_mm: number
  herringbone_angle_deg: number
  twist_angle_deg: number
}

// Store state
rings: RosetteRing[]
selectedRingId: number | null
segmentation: SegmentationResult | null
sliceBatch: SliceBatch | null
loading: boolean
error: string | null
```

**Actions:**
- `addDefaultRing()` - Create new ring with default parameters
- `segmentSelectedRing()` - Call `/segment-ring` API
- `generateSlicesForSelectedRing()` - Call `/generate-slices` API

**Usage:**
```typescript
import { useRosetteDesignerStore } from '@/stores/useRosetteDesignerStore'

const store = useRosetteDesignerStore()

// Add ring
store.addDefaultRing()

// Segment ring
await store.segmentSelectedRing()

// Generate slices
await store.generateSlicesForSelectedRing()
```

---

### **4. Frontend: UI Components**

**Location:** `packages/client/src/`

#### Main View: `views/RosetteDesignerView.vue`
- 3-column layout (left: config, center: preview, right: debug)
- Action buttons: Add Ring, Segment Ring, Generate Slices
- Status indicators: loading spinner, error messages
- Debug panel: Raw JSON output from backend

#### Left Panel: `components/rmos/ColumnStripEditor.vue`
- **Stub component** for N11.2
- Placeholder for strip width/color/material editing
- N12 will implement full strip column management

#### Left Panel: `components/rmos/RingConfigPanel.vue`
- **Working component** with 6 ring parameter inputs:
  - Radius (mm)
  - Width (mm)
  - Tile length (mm)
  - Kerf (mm)
  - Herringbone angle (deg)
  - Twist angle (deg)
- Two-way binding to store's selected ring

#### Center Panel: `components/rmos/TilePreviewCanvas.vue`
- **Stub component** for N11.2
- Shows tile count and angle ranges as text list
- N12 will implement canvas rendering with actual geometry

---

## 🧪 Testing

### **Manual Testing Flow**

1. **Start Backend:**
```powershell
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

2. **Start Frontend:**
```powershell
cd packages/client
npm run dev
```

3. **Navigate to Designer:**
```
http://localhost:5173/rmos/rosette-designer
```

4. **Test Workflow:**
```
1. Click "Add Ring" → Creates ring with defaults (radius=45mm)
2. Adjust parameters in Ring Config Panel
3. Click "Segment Ring" → API call returns 8-tile segmentation
4. Check center panel → Should show 8 tiles with angles
5. Click "Generate Slices" → API call returns slice batch with kerf/herringbone
6. Check right panel → JSON output shows full slice data
```

**Expected Results:**
- ✅ No console errors
- ✅ Segmentation shows 8 tiles (0°-45°, 45°-90°, etc.)
- ✅ Slices show `kerf_mm: 0.3` field
- ✅ Every other slice has `herringbone_flip: true`
- ✅ Debug panel updates with API responses

---

## 📊 Data Flow

### **Complete Vertical Slice**

```
User Interaction (RosetteDesignerView.vue)
    ↓
Action: "Add Ring"
    ↓
Store: useRosetteDesignerStore.addDefaultRing()
    ↓
State: rings[] updated, selectedRingId set
    ↓
UI: RingConfigPanel shows parameters
    ↓
───────────────────────────────────────
User Interaction: "Segment Ring"
    ↓
Store: segmentSelectedRing()
    ↓
API: POST /api/rmos/rosette/segment-ring
    ↓
Backend: rmos_rosette_api.segment_ring()
    ↓
cam/rosette: compute_tile_segmentation_stub()
    ↓
Response: 8-tile segmentation JSON
    ↓
Store: segmentation state updated
    ↓
UI: TilePreviewCanvas shows tiles
    ↓
───────────────────────────────────────
User Interaction: "Generate Slices"
    ↓
Store: generateSlicesForSelectedRing()
    ↓
API: POST /api/rmos/rosette/generate-slices
    ↓
Backend: rmos_rosette_api.generate_slices()
    ↓
cam/rosette: 
  - generate_saw_batch_stub()
  - apply_kerf_compensation_stub()
  - apply_herringbone_stub()
    ↓
Response: Slice batch with 8 slices
    ↓
Store: sliceBatch state updated
    ↓
UI: Debug panel shows JSON
```

---

## 🔧 Usage Examples

### **Example 1: Programmatic Ring Creation**

```typescript
import { useRosetteDesignerStore } from '@/stores/useRosetteDesignerStore'

const store = useRosetteDesignerStore()

// Create custom ring
store.rings.push({
  ring_id: 0,
  radius_mm: 50,
  width_mm: 4,
  tile_length_mm: 6,
  kerf_mm: 0.25,
  herringbone_angle_deg: 5,
  twist_angle_deg: 0,
})
store.selectedRingId = 0

// Run segmentation
await store.segmentSelectedRing()

console.log('Tile count:', store.segmentation?.tile_count)
```

### **Example 2: Direct API Call**

```typescript
// Segment ring via direct fetch
const response = await fetch('/api/rmos/rosette/segment-ring', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    ring: {
      ring_id: 0,
      radius_mm: 40,
      width_mm: 3,
      tile_length_mm: 5,
      kerf_mm: 0.3,
      herringbone_angle_deg: 0,
      twist_angle_deg: 0,
    }
  })
})

const segmentation = await response.json()
console.log('Segmentation:', segmentation)
```

### **Example 3: Testing Herringbone**

```typescript
const store = useRosetteDesignerStore()

// Add ring with herringbone
store.addDefaultRing()
const ring = store.rings[0]
ring.herringbone_angle_deg = 10  // Set herringbone angle

// Segment and generate
await store.segmentSelectedRing()
await store.generateSlicesForSelectedRing()

// Check alternating pattern
const slices = store.sliceBatch?.slices || []
console.log('Slice 0 flip:', slices[0].herringbone_flip)  // false
console.log('Slice 1 flip:', slices[1].herringbone_flip)  // true
console.log('Slice 2 flip:', slices[2].herringbone_flip)  // false
```

---

## 🚀 Integration Points

### **N11.1 Integration (Completed)**

N11.2 successfully integrates with N11.1's pattern storage:
- `/api/rmos/rosette/patterns` endpoint uses `SQLitePatternStore.list_by_type('rosette')`
- Frontend can load saved rosette patterns (future feature)
- No changes required to N11.1 scaffolding

### **N12 Integration (Next Bundle)**

N12 will replace stub implementations with real geometry:

**Backend (`cam/rosette/` package):**
```python
# N12 will replace:
compute_tile_segmentation_stub()
# With:
compute_tile_segmentation_real()
  - Use ring circumference: C = 2πr
  - Calculate tile count: N = floor(C / tile_length_mm)
  - Apply constraints: 2 ≤ N ≤ 300
  - Return real theta angles

apply_kerf_compensation_stub()
# With:
apply_kerf_compensation_real()
  - Adjust angles for kerf width
  - Compute angular compensation: Δθ = (kerf_mm / r) × (180/π)

apply_herringbone_stub()
# With:
apply_herringbone_real()
  - Apply alternating angle transformations
  - Compute herringbone geometry coordinates
```

**Frontend (TilePreviewCanvas.vue):**
```vue
<!-- N12 will replace text list with: -->
<canvas ref="canvasRef" width="600" height="400"></canvas>

<script setup lang="ts">
// Draw actual ring geometry
function drawRing(ctx: CanvasRenderingContext2D) {
  // Draw ring boundary
  // Draw tile separators
  // Color-code by strip family
  // Show kerf lines
}
</script>
```

---

## 🐛 Troubleshooting

### **Issue: "segment-ring failed with 500"**
**Cause:** Backend cam/rosette package import error  
**Solution:**
```powershell
# Verify package structure
ls services/api/app/cam/rosette/

# Should show:
# __init__.py
# tile_segmentation.py
# kerf_compensation.py
# herringbone.py
# saw_batch_generator.py

# Check server logs for import errors
```

### **Issue: TilePreviewCanvas shows empty**
**Cause:** Segmentation not computed yet  
**Solution:** Click "Segment Ring" button before checking preview

### **Issue: Ring parameters don't update**
**Cause:** Ring not selected  
**Solution:** Click "Add Ring" to create and select a ring

### **Issue: "Module not found: @/stores/useRosetteDesignerStore"**
**Cause:** Store file not in correct location  
**Solution:** Verify file exists at `packages/client/src/stores/useRosetteDesignerStore.ts`

---

## ✅ Validation Checklist

**Backend Verification:**
- [x] cam/rosette package created with 5 modules
- [x] All stub functions return valid JSON structures
- [x] rmos_rosette_api.py registered in main.py
- [x] Server starts without import errors
- [x] Swagger UI shows 3 rosette endpoints at `/docs`

**Frontend Verification:**
- [x] useRosetteDesignerStore.ts created with 3 actions
- [x] RosetteDesignerView.vue created with 3-panel layout
- [x] 3 stub components created (ColumnStripEditor, RingConfigPanel, TilePreviewCanvas)
- [x] Route registered at `/rmos/rosette-designer`
- [x] UI accessible via navigation

**Integration Verification:**
- [x] "Add Ring" creates ring in store
- [x] "Segment Ring" calls API and updates state
- [x] "Generate Slices" calls API with segmentation
- [x] Debug panel shows API responses
- [x] No console errors during workflow

**Post-Deployment Test:**
```powershell
# 1. Start servers
cd services/api && uvicorn app.main:app --reload
cd packages/client && npm run dev

# 2. Open browser
http://localhost:5173/rmos/rosette-designer

# 3. Execute workflow
Add Ring → Segment Ring → Generate Slices

# 4. Verify outputs
- Center panel shows 8 tiles
- Right panel shows JSON with kerf_mm and herringbone_flip
- No errors in console or terminal
```

---

## 📚 See Also

- [N11.1 Rosette Scaffolding](./N11_1_ROSETTE_SCAFFOLDING_QUICKREF.md) - Pattern storage system
- [RMOS N8-N10 Architecture](./RMOS_N8_N10_ARCHITECTURE.md) - Integration blueprint
- [RMOS Studio Algorithms](./specs/rmos_studio/RMOS_STUDIO_ALGORITHMS.md) - Real geometry math for N12
- [RMOS Studio Saw Pipeline](./specs/rmos_studio/RMOS_STUDIO_SAW_PIPELINE.md) - Slice batch operations

---

## 🎯 Next Steps: N12

**N12 Bundle: Real Geometry Engine**

Replace all stub implementations with production algorithms:

**Backend Tasks:**
1. `compute_tile_segmentation_real()` - Circumference-based tile calculations
2. `apply_kerf_compensation_real()` - Angular kerf adjustments
3. `apply_herringbone_real()` - Alternating angle transformations
4. `generate_saw_batch_real()` - Full 2D slice coordinates

**Frontend Tasks:**
1. Canvas-based tile preview with actual geometry
2. Ring visualization with color-coded strips
3. Kerf line rendering
4. Interactive tile selection/editing

**Data Structure Extensions:**
```typescript
// N12 will add geometry coordinates to slices
interface Slice {
  slice_index: number
  tile_index: number
  angle_deg: number
  kerf_mm: number
  herringbone_flip: boolean
  
  // NEW in N12:
  vertices: Array<{x: number, y: number}>  // 2D coordinates
  arc_path: string  // SVG path data
  strip_layers: Array<StripLayer>  // Nested geometry
}
```

---

## 📊 Bundle Summary

| Component | Files Created | Lines of Code |
|-----------|---------------|---------------|
| Backend cam/rosette | 5 | ~150 |
| Backend API router | 1 | ~150 |
| Frontend store | 1 | ~120 |
| Frontend view | 1 | ~80 |
| Frontend components | 3 | ~150 |
| Router registration | 1 (edit) | ~7 |
| **Total** | **12** | **~657** |

**Status:** ✅ N11.2 Bundle Complete  
**Merge Safety:** 100% (all stub implementations, no real geometry)  
**Next:** N12 (Real Geometry Engine)  
**Final Goal:** Production-ready RMOS Studio rosette designer

---

**Key Achievement:** Complete vertical slice from UI button click through Pinia store, REST API, backend cam package, and back to UI - all with working placeholder implementations that can be replaced module-by-module in N12.
