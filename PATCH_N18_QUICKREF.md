# Patch N18: G2/G3 Arc Linkers + Feed Floors - Quick Reference

**Status:** ✅ Integrated  
**Date:** November 7, 2025

---

## 🚀 Quick Start

### **Start API Server**
```powershell
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

### **Run Smoke Test**
```powershell
.\smoke_n18_arcs.ps1
```

---

## 📡 API Endpoint

### **POST `/cam/adaptive3/offset_spiral.nc`**

Generate adaptive pocket toolpath with G2/G3 arc linkers.

**Example Request:**
```json
{
  "boundary": [[0,0], [100,0], [100,60], [0,60]],
  "islands": [[[30,15], [70,15], [70,45], [30,45]]],
  "tool_d": 6.0,
  "stepover": 0.45,
  "stepdown": 1.5,
  "margin": 0.5,
  "feed_xy": 1200,
  "feed_z": 400,
  "safe_z": 5.0,
  "final_depth": -3.0,
  "use_arcs": true,
  "feed_floor_pct": 0.75
}
```

**Example Response (G-code):**
```gcode
G21
G90
G0 Z5.0
G0 X3.5 Y3.0
G1 Z-1.5 F400.0
G1 X96.5 Y3.0 F1200.0
G2 X96.5 Y57.0 I0.0 J27.0 F1200.0
G1 X3.5 Y57.0 F1200.0
G2 X3.5 Y3.0 I0.0 J-27.0 F1200.0
G0 Z5.0
G0 X6.2 Y3.0
G1 Z-3.0 F400.0
G1 X93.8 Y3.0 F900.0
...
M30
```

---

## 🔑 Key Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `boundary` | `[[x,y], ...]` | Required | Outer pocket boundary (CCW) |
| `islands` | `[[[x,y], ...], ...]` | `[]` | Islands/holes (CW) |
| `tool_d` | `float` | Required | Tool diameter (mm) |
| `stepover` | `float` | `0.45` | % of tool diameter (0.3-0.7) |
| `stepdown` | `float` | Required | Depth per pass (mm) |
| `margin` | `float` | `0.5` | Clearance from boundary (mm) |
| `feed_xy` | `float` | `1200` | Cutting feed (mm/min) |
| `feed_z` | `float` | `400` | Plunge feed (mm/min) |
| `safe_z` | `float` | `5.0` | Retract height (mm) |
| `final_depth` | `float` | Required | Total depth (negative, mm) |
| **`use_arcs`** | `bool` | `true` | **Enable G2/G3 arc linkers** 🆕 |
| **`feed_floor_pct`** | `float` | `0.75` | **Feed % at stepdown (0.5-1.0)** 🆕 |

---

## 🎯 Key Features

### **1. G2/G3 Arc Linkers**
- Smooth transitions between offset rings
- Replaces sharp corners with arcs
- Better surface finish vs linear moves
- Works with all CAM software (fallback to G1 if unsupported)

**Enable:** `"use_arcs": true`

### **2. Feed Floors**
- Automatic feed reduction at stepdown transitions
- Prevents tool overload on plunge
- Configurable via `feed_floor_pct` (e.g., 0.75 = 75% speed)

**Example:**
- Normal feed: 1200 mm/min
- Feed floor (0.75): 900 mm/min (first move after plunge)

### **3. Island Handling**
- Automatic keepout zones around holes
- Inherited from Module L.1 (pyclipper)
- Supports multiple islands

---

## 📊 G-code Output Examples

### **With Arcs (`use_arcs: true`)**
```gcode
G1 X50.0 Y10.0 F1200.0
G2 X50.0 Y50.0 I0.0 J20.0 F1200.0  ; Arc linker
G1 X10.0 Y50.0 F1200.0
```

### **Without Arcs (`use_arcs: false`)**
```gcode
G1 X50.0 Y10.0 F1200.0
G1 X50.0 Y30.0 F1200.0  ; Linear transition
G1 X50.0 Y50.0 F1200.0
G1 X10.0 Y50.0 F1200.0
```

### **Feed Floor Example**
```gcode
G1 Z-1.5 F400.0        ; Plunge
G1 X50.0 Y10.0 F900.0  ; Feed floor (75% of 1200)
G1 X50.0 Y50.0 F1200.0 ; Normal feed
```

---

## 🧪 Testing

### **Test 1: Basic Arc Generation**
```powershell
curl -X POST http://localhost:8000/cam/adaptive3/offset_spiral.nc `
  -H "Content-Type: application/json" `
  -d '{
    "boundary": [[0,0], [100,0], [100,60], [0,60]],
    "islands": [],
    "tool_d": 6.0,
    "stepover": 0.45,
    "stepdown": 1.5,
    "final_depth": -3.0,
    "use_arcs": true
  }' `
  -o test_arcs.nc
```

**Validate:**
- Open `test_arcs.nc`
- Search for `G2` or `G3` commands
- Check arc parameters (`I`, `J` center offsets)

### **Test 2: Feed Floor**
```powershell
curl -X POST http://localhost:8000/cam/adaptive3/offset_spiral.nc `
  -H "Content-Type: application/json" `
  -d '{
    "boundary": [[0,0], [60,0], [60,40], [0,40]],
    "tool_d": 6.0,
    "stepdown": 2.0,
    "final_depth": -6.0,
    "feed_xy": 1000,
    "feed_floor_pct": 0.60
  }' `
  -o test_feedfloor.nc
```

**Validate:**
- Check for multiple `F` values (e.g., `F600.0`, `F1000.0`)
- Feed should reduce after each `Z` plunge

---

## 🔗 Integration with Existing Systems

### **Module L (Adaptive Pocketing)**
- N18 extends Module L with arc emission
- Shares same offset-stacking algorithm
- Compatible with L.1 (pyclipper), L.2 (spiralizer), L.3 (trochoidal)

### **Patch N15 (G-code Backplot)**
- Can visualize N18 output with arc support
- Use `/cam/gcode/plot.svg` to preview arcs
- Time estimation includes arc lengths

### **Art Studio v15.5 (Post-Processors)**
- N18 output works with all 4 presets (GRBL, Mach3, Haas, Marlin)
- G2/G3 commands compatible with modern controllers
- Legacy machines: Set `use_arcs: false`

---

## 📁 Integrated Files

```
services/api/app/
├── util/
│   └── g2_emitter.py              # G2/G3 arc generator (🆕 N18)
└── routers/
    └── adaptive_poly_gcode_router.py  # Router with arc support (🆕 N18)

smoke_n18_arcs.ps1                 # Smoke test script (🆕 N18)
PATCH_N18_G2G3_LINKERS.md          # Full documentation (🆕 N18)
PATCH_N18_INTEGRATION_SUMMARY.md   # Integration guide (🆕 N18)
```

---

## 🐛 Troubleshooting

### **Issue:** No G2/G3 commands in output
**Solution:** Check `use_arcs: true` in request body

### **Issue:** Feed floor not working
**Solution:** Verify `feed_floor_pct` is between 0.5-1.0

### **Issue:** Arc radius errors in CAM software
**Solution:** Check arc tolerance in `g2_emitter.py` (default 0.001mm)

### **Issue:** Router not registered
**Solution:** Verify `main.py` has N18 import and registration

---

## 🎯 Next Steps

- **Test with real geometry:** Use actual guitar body outlines
- **Integrate with Module L.3:** Combine arcs with trochoidal insertion
- **CI integration:** Add N18 tests to GitHub Actions
- **Frontend component:** Create `ArcPocketLab.vue` for UI

---

## 📚 See Also

- [PATCH_N18_G2G3_LINKERS.md](./PATCH_N18_G2G3_LINKERS.md) - Full documentation
- [ADAPTIVE_POCKETING_MODULE_L.md](./ADAPTIVE_POCKETING_MODULE_L.md) - Core system
- [PATCH_N15_INTEGRATION_SUMMARY.md](./PATCH_N15_INTEGRATION_SUMMARY.md) - G-code backplot
- [ART_STUDIO_V15_5_QUICKREF.md](./ART_STUDIO_V15_5_QUICKREF.md) - Post-processors

---

**Status:** ✅ Patch N18 fully integrated and ready for testing!
