# Patch N18: G2/G3 Arc Linkers + Feed Floors Integration

**Status:** 🔄 In Progress  
**Date:** November 7, 2025

---

## 🎯 Overview

Patch N18 adds **G2/G3 arc emission** for adaptive pocketing toolpaths with:
- Arc linkers between offset rings (smoother motion)
- Feed floor support (stepdown-aware feed reduction)
- New endpoint `/cam/adaptive3/offset_spiral.nc`

---

## 📦 Files to Integrate

### **1. Backend Files**

| Source | Destination | Purpose |
|--------|-------------|---------|
| `server/util/g2_emitter.py` | `services/api/app/util/g2_emitter.py` | G2/G3 arc generator |
| `server/adaptive_poly_gcode_router.py` | `services/api/app/routers/adaptive_poly_gcode_router.py` | New router with arc support |
| `server_patch/main_register_n18.diff` | Apply to `services/api/app/main.py` | Router registration |

### **2. Documentation**

| Source | Destination |
|--------|-------------|
| `docs/README_Patch_N18_g2g3_linkers_feedfloors.md` | `PATCH_N18_G2G3_LINKERS.md` |

---

## 🔧 Integration Steps

### **Step 1: Copy g2_emitter.py**
```powershell
Copy-Item "C:\Users\thepr\Downloads\ToolBox_Art_Studio\ToolBox_Patch_N18_g2g3_linkers_feedfloors\ToolBox_Patch_N18_g2g3_linkers_feedfloors\server\util\g2_emitter.py" `
  -Destination "services/api/app/util/g2_emitter.py"
```

### **Step 2: Copy adaptive_poly_gcode_router.py**
```powershell
Copy-Item "C:\Users\thepr\Downloads\ToolBox_Art_Studio\ToolBox_Patch_N18_g2g3_linkers_feedfloors\ToolBox_Patch_N18_g2g3_linkers_feedfloors\server\adaptive_poly_gcode_router.py" `
  -Destination "services/api/app/routers/adaptive_poly_gcode_router.py"
```

### **Step 3: Register Router in main.py**
Add to `services/api/app/main.py`:

```python
# Patch N.18 — G2/G3 Arc Linkers + Feed Floors
try:
    from .routers.adaptive_poly_gcode_router import router as adaptive_poly_gcode_router
except Exception:
    adaptive_poly_gcode_router = None

# ... later in router registration section ...

# Patch N.18: Adaptive offset-spiral with G2/G3 arcs
if adaptive_poly_gcode_router:
    app.include_router(adaptive_poly_gcode_router)
```

### **Step 4: Create Smoke Test**
Create `smoke_n18_arcs.ps1` to test `/cam/adaptive3/offset_spiral.nc`

---

## 📊 New API Endpoint

### **POST `/cam/adaptive3/offset_spiral.nc`**

Generate adaptive pocket toolpath with G2/G3 arcs.

**Request:**
```json
{
  "boundary": [[0,0], [100,0], [100,60], [0,60]],
  "islands": [
    [[30,15], [70,15], [70,45], [30,45]]
  ],
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

**Response:**
```gcode
G21
G90
G0 Z5.0
G0 X3.0 Y3.0
G1 Z-1.5 F400.0
G1 X97.0 Y3.0 F1200.0
G2 X97.0 Y57.0 I0.0 J27.0 F1200.0  ; Arc linker
G1 X3.0 Y57.0 F1200.0
...
M30
```

---

## 🔑 Key Features

### **1. G2/G3 Arc Linkers**
- Smooth transitions between offset rings
- Reduces toolpath length vs straight line + feedrate changes
- Better surface finish

### **2. Feed Floors**
- Automatic feed reduction at stepdown transitions
- `feed_floor_pct` parameter (e.g., 0.75 = 75% of normal feed)
- Prevents tool overload on plunge

### **3. Arc Detection**
- `use_arcs=true` enables G2/G3 emission
- Falls back to G1 linear moves if disabled
- Compatible with all post-processors

---

## 📋 Integration Checklist

- [ ] Copy `g2_emitter.py` to `services/api/app/util/`
- [ ] Copy `adaptive_poly_gcode_router.py` to `services/api/app/routers/`
- [ ] Update `main.py` with N18 router registration
- [ ] Create `smoke_n18_arcs.ps1` test script
- [ ] Test endpoint with sample geometry
- [ ] Validate G2/G3 output in G-code viewer
- [ ] Update ADAPTIVE_POCKETING_MODULE_L.md with N18 features
- [ ] Add CI workflow test for arc emission

---

## 🧪 Testing

### **Local API Test**
```powershell
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

### **Smoke Test**
```powershell
.\smoke_n18_arcs.ps1
```

**Expected:**
- G2/G3 commands in output
- Feed floor commands at stepdown
- Smoother toolpath vs N15 backplot

---

## 🔗 Related Patches

- **N15**: G-code backplot + time estimator (already integrated)
- **N16**: Adaptive spiral kernels (not yet integrated)
- **N17**: Polygon offset with pyclipper (not yet integrated)
- **L.3**: Trochoidal insertion (Module L enhancement)

---

## 📚 Documentation

Full docs will be in:
- `PATCH_N18_G2G3_LINKERS.md` (detailed)
- `PATCH_N18_QUICKREF.md` (quick reference)

---

**Next Action:** Copy files and register router ⏭️
