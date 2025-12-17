# Phase 24.4 Quick Reference: Relief Sim Bridge Frontend

**Status:** ✅ Complete | **Date:** January 2025

---

## 🎯 What It Does

Adds **material removal simulation** to Relief carving UI with floor thickness tracking, load index heatmap, and thin floor detection.

---

## 🔌 Integration Points

### **ArtStudioRelief.vue** (Production Lane)
- **File:** `client/src/views/art/ArtStudioRelief.vue`
- **When:** After relief pipeline completes
- **What:** Calls `/api/cam/relief/sim_bridge`, merges issues with risk analytics, displays sim stats

### **ReliefKernelLab.vue** (Dev Lab)
- **File:** `client/src/labs/ReliefKernelLab.vue`
- **When:** After finishing toolpath generation
- **What:** Calls `/api/cam/relief/sim_bridge`, renders load hotspots + thin floor zones on canvas, displays sim stats

---

## 📊 Visual Design

### **Overlay Colors**
| Type | Color | Radius | Meaning |
|------|-------|--------|---------|
| **Load Hotspot** | Orange (`rgba(255,140,0,0.5)`) | 2-5px (intensity-based) | High material removal zones |
| **Thin Floor Zone** | Red (`rgba(220,20,20,0.7)`) | 3px | Floor thickness < 0.6mm |
| **Slope Hotspot** (existing) | Red/Orange | 2px | High slope angles from relief_finish |

### **Stats Display**
```
┌─ Relief Sim Bridge Stats ──────────────────┐
│ Floor: avg 1.23 mm, min 0.58 mm            │
│ Load: max 3.45, avg 1.12                   │
│ Removed: 450.2 mm³                         │
│ Grid cells: 48000                          │
└────────────────────────────────────────────┘
```

---

## 🚀 Usage

### **Production Lane (ArtStudioRelief.vue)**
1. Load heightmap: `workspace/art/relief/demo_relief_heightmap.png`
2. Click "Run Pipeline" → relief_map → roughing → finishing → post → sim
3. **Sim bridge auto-runs** after finishing
4. View results:
   - Risk summary: risk score, extra time, total issues
   - Sim bridge stats: floor thickness, load index, removed volume
   - Backplot: toolpath + overlays (slope hotspots, load hotspots, thin floor zones)
5. Snapshot auto-pushed to Risk Timeline with sim stats

### **Dev Lab (ReliefKernelLab.vue)**
1. Upload heightmap image (local file)
2. Click "Map Heightfield"
3. Adjust parameters:
   - Tool Ø: 6.0mm
   - Step-down: 2.0mm
   - Scallop: 0.05mm
   - **Stock: 5.0mm** ← NEW (Phase 24.4)
4. Click "Generate Finishing"
5. **Sim bridge auto-runs** after finishing
6. View results:
   - Canvas: toolpath + load hotspots (orange) + thin floor zones (red)
   - Sim bridge stats: floor, load, removed volume, grid cells, issue count
7. Click "Save Snapshot" → pushes to Risk Timeline with sim stats

---

## 🔧 Configuration

### **Stock Thickness**
- **ArtStudioRelief.vue:** Hardcoded `5.0mm` (TODO: expose as UI control)
- **ReliefKernelLab.vue:** UI slider (default `5.0mm`)

### **Thresholds** (both components)
- **Min floor thickness:** `0.6mm` (triggers thin_floor issues)
- **High load index:** `2.0` (triggers high_load issues)
- **Med load index:** `1.0` (baseline for normalization)

### **Performance Limits**
- **ArtStudioRelief.vue:** No limits (backplot viewer renders all overlays)
- **ReliefKernelLab.vue:** First 2000 moves, 500 overlays (canvas performance)

---

## 📦 API Contract

### **Request** (POST `/api/cam/relief/sim_bridge`)
```json
{
  "moves": [
    {"code": "G0", "z": 4.0},
    {"code": "G1", "x": 10.0, "y": 5.0, "z": -1.5, "f": 600.0}
  ],
  "stock_thickness": 5.0,
  "origin_x": 0.0,
  "origin_y": 0.0,
  "cell_size_xy": 0.5,
  "units": "mm",
  "min_floor_thickness": 0.6,
  "high_load_index": 2.0,
  "med_load_index": 1.0
}
```

### **Response** (ReliefSimOut)
```json
{
  "issues": [
    {
      "type": "thin_floor",
      "severity": "high",
      "x": 25.3,
      "y": 18.7,
      "note": "Floor thickness 0.52 mm < 0.6 mm"
    },
    {
      "type": "high_load",
      "severity": "medium",
      "x": 42.1,
      "y": 30.5,
      "note": "Load index 2.34 > 2.0"
    }
  ],
  "overlays": [
    {
      "type": "load_hotspot",
      "x": 42.1,
      "y": 30.5,
      "intensity": 0.85
    },
    {
      "type": "thin_floor_zone",
      "x": 25.3,
      "y": 18.7,
      "severity": "high"
    }
  ],
  "stats": {
    "cell_count": 48000,
    "avg_floor_thickness": 1.23,
    "min_floor_thickness": 0.52,
    "max_load_index": 3.45,
    "avg_load_index": 1.12,
    "total_removed_volume": 450.2
  }
}
```

---

## 🧪 Testing

### **Backend Tests**
```powershell
cd c:\Users\thepr\Downloads\Luthiers ToolBox
.\test-relief-sim-bridge.ps1
```

**Expected:**
- Test 1: Normal finishing → no thin floors ✅
- Test 2: Deep cut (4.8mm in 5mm stock) → thin_floor issues ✅
- Test 3: Empty moves → zero stats ✅

### **Frontend Tests**

**Start servers:**
```powershell
# API
cd services/api
uvicorn app.main:app --reload --port 8000

# Client (separate terminal)
cd packages/client
npm run dev
```

**Test ArtStudioRelief.vue:**
1. Navigate to Art Studio → Relief Carving
2. Click "Run Pipeline"
3. Verify sim bridge stats panel appears
4. Verify backplot shows load hotspots (orange) + thin floor zones (red)

**Test ReliefKernelLab.vue:**
1. Navigate to Labs → Relief Kernel Lab
2. Upload `demo_relief_heightmap.png`
3. Click "Map Heightfield" → "Generate Finishing"
4. Verify canvas shows load hotspots + thin floor zones
5. Verify sim bridge stats panel appears
6. Click "Save Snapshot" → verify alert

---

## 📁 Files Modified

### **Frontend** (Phase 24.4)
- ✅ `client/src/views/art/ArtStudioRelief.vue` (+85 lines)
  - Added reliefSimBridgeOut state ref
  - Updated handleRunSuccess to call sim_bridge
  - Updated backplotOverlays computed to include sim-bridge overlays
  - Added sim bridge stats UI display
- ✅ `client/src/labs/ReliefKernelLab.vue` (+120 lines)
  - Added stockThickness control + reliefSimBridgeOut state ref
  - Updated runFinish to call sim_bridge
  - Updated drawPreview to render load hotspots + thin floor zones
  - Updated pushSnapshot to include sim stats
  - Added sim bridge stats UI display

### **Backend** (Phase 24.3)
- ✅ `services/api/app/schemas/relief.py` (+105 lines)
- ✅ `services/api/app/services/relief_sim_bridge.py` (335 lines NEW)
- ✅ `services/api/app/routers/cam_relief_router.py` (+45 lines)

---

## 🎯 Future Enhancements

### **Phase 24.4.1** (Planned)
- [ ] Stock thickness UI control in ArtStudioRelief.vue
- [ ] Threshold sliders (floor thickness, load index)
- [ ] Real-time slider preview (debounced sim_bridge calls)

### **Phase 24.4.2** (Planned)
- [ ] Adaptive feed rate overlay (color-coded feed percentage)
- [ ] Material removal animation (time slider)
- [ ] Export sim grid as heightmap image (PNG)

---

## 📚 See Also

- [Phase 24.3: Backend](./PHASE_24_3_RELIEF_SIM_BRIDGE_BACKEND.md)
- [Phase 24.4: Frontend](./PHASE_24_4_RELIEF_SIM_BRIDGE_FRONTEND.md) (detailed)
- [Phase 24.5: Machine Envelope](./PHASE_24_5_MACHINE_ENVELOPE_INTEGRATION.md)

---

**Status:** ✅ Complete | **Next:** Execute tests, LUA policy compliance
