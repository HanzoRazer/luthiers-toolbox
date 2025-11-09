# Art Studio v15.5 - Quick Reference

**Status:** ✅ Backend Complete | ⏳ Frontend Needs Router + three.js

---

## 🚀 Quick Start

### **1. Install Frontend Dependencies**
```powershell
cd packages/client
npm install three
npm install --save-dev @types/three
```

### **2. Test Backend**
```powershell
# Start API
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload

# Test in another terminal
curl http://localhost:8000/api/cam_gcode/posts_v155
```

### **3. Configure Frontend Route**
Add to router config:
```typescript
{
  path: '/art-studio-v15',
  name: 'ArtStudioPhase15_5',
  component: () => import('@/views/ArtStudioPhase15_5.vue')
}
```

### **4. Test UI**
```powershell
cd packages/client
npm run dev
# Navigate to http://localhost:5173/art-studio-v15
```

---

## 📁 Files Created

| File | Lines | Status |
|------|-------|--------|
| `services/api/app/routers/cam_post_v155_router.py` | 360 | ✅ |
| `services/api/app/data/posts/posts_v155.json` | 75 | ✅ |
| `services/api/app/main.py` | +10 | ✅ |
| `packages/client/src/api/postv155.ts` | 20 | ✅ |
| `packages/client/src/components/ToolpathPreview3D.vue` | 50 | ✅ |
| `packages/client/src/views/ArtStudioPhase15_5.vue` | 138 | ✅ |

---

## 🔌 API Endpoints

### **GET `/api/cam_gcode/posts_v155`**
Returns 4 presets: GRBL, Mach3, Haas, Marlin

### **POST `/api/cam_gcode/post_v155`**
Generate G-code with:
- Lead-in/out (tangent/arc/none)
- CRC (G41/G42 left/right)
- Corner smoothing (fillet arcs)
- Axis modal optimization
- 3D preview spans

**Request Example:**
```json
{
  "contour": [[0,0],[60,0],[60,25],[0,25],[0,0]],
  "z_cut_mm": -1.0,
  "feed_mm_min": 600,
  "plane_z_mm": 5.0,
  "preset": "GRBL",
  "lead_type": "tangent",
  "lead_len_mm": 3.0,
  "crc_mode": "none",
  "fillet_radius_mm": 0.4,
  "fillet_angle_min_deg": 20.0
}
```

---

## ⚙️ Controller Presets

| Preset | Units | Arc Mode | Major Arcs | Modal | Max Sweep |
|--------|-------|----------|------------|-------|-----------|
| **GRBL** | Metric | IJ | No | Yes | 179.9° |
| **Mach3** | Metric | IJ | Yes | Yes | 359° |
| **Haas** | Inch | IJ | Yes | Yes | 359° |
| **Marlin** | Metric | R | No | No | 179.9° |

---

## 🎨 UI Features

**ArtStudioPhase15_5.vue:**
- ✅ Preset selector (GRBL/Mach3/Haas/Marlin)
- ✅ Contour JSON input
- ✅ Z cut, feed, safe Z controls
- ✅ Lead-in/out controls (type, length, radius)
- ✅ CRC controls (mode, D#, diameter)
- ✅ Corner smoothing (fillet radius, min angle)
- ✅ 3D preview (Three.js WebGL)
- ✅ G-code output display

---

## 🧪 Quick Test

### **Backend Test:**
```powershell
# Start API
cd services/api
uvicorn app.main:app --reload

# Test GET
curl http://localhost:8000/api/cam_gcode/posts_v155

# Test POST (GRBL with tangent lead)
curl -X POST http://localhost:8000/api/cam_gcode/post_v155 `
  -H "Content-Type: application/json" `
  -d '{"contour":[[0,0],[60,0],[60,25],[0,25],[0,0]],"z_cut_mm":-1.0,"feed_mm_min":600,"plane_z_mm":5.0,"preset":"GRBL","lead_type":"tangent","lead_len_mm":3.0,"crc_mode":"none","fillet_radius_mm":0.4,"fillet_angle_min_deg":20.0}'
```

**Expected Output:**
```gcode
G21
G90
G17
(GRBL 1.1 post)
G0 Z5.0000
G0 X-3.0000 Y0.0000
G1 Z-1.0000 F600.0
G1 X0.0000 F600.0
G1 X60.0000 F600.0
...
M30
(End of program)
```

### **Frontend Test:**
1. Navigate to `/art-studio-v15` (after router config)
2. Select **GRBL** preset
3. Enter contour: `[[0,0],[60,0],[60,25],[0,25],[0,0]]`
4. Set Z cut: `-1.0`, Feed: `600`
5. Select lead type: **tangent**, length: `3.0`
6. Click **Generate**
7. Verify G-code output and 3D preview

---

## 🔧 Key Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `z_cut_mm` | -1.0 | < 0 | Cutting depth (negative) |
| `feed_mm_min` | 600 | 100-3000 | Cutting feed rate |
| `plane_z_mm` | 5.0 | > 0 | Safe Z height |
| `lead_type` | tangent | none/tangent/arc | Lead-in/out strategy |
| `lead_len_mm` | 3.0 | 0.5-10 | Lead approach length |
| `crc_mode` | none | none/left/right | CRC compensation |
| `fillet_radius_mm` | 0.4 | 0.1-5.0 | Corner smoothing radius |
| `fillet_angle_min_deg` | 20.0 | 0-90 | Min angle for fillet |

---

## ⚠️ Known Limitations

### **CRC Support:**
- ❌ **GRBL/Marlin:** Ignore G41/G42 (hobby controllers)
- ✅ **Mach3/Haas:** Full CRC with tool table

### **Arc Limits:**
- **GRBL/Marlin:** Max 179.9° (split larger arcs)
- **Mach3/Haas:** Max 359° (full-circle OK)

### **Units:**
- **Haas:** Inch by default (G20)
- **Others:** Metric by default (G21)

---

## 📋 TODO Checklist

- [ ] Install `three` dependency
- [ ] Configure frontend router
- [ ] Add navigation menu link
- [ ] Test all 4 presets
- [ ] Test lead-in/out strategies
- [ ] Test CRC modes
- [ ] Validate 3D preview
- [ ] Document user workflow

---

## 📚 Related Docs

- [ART_STUDIO_V15_5_INTEGRATION.md](./ART_STUDIO_V15_5_INTEGRATION.md) - Complete guide
- [ART_STUDIO_REPO_SUMMARY.md](./ART_STUDIO_REPO_SUMMARY.md) - Version catalog
- [PATCH_N14_UNIFIED_CAM_SETTINGS.md](./PATCH_N14_UNIFIED_CAM_SETTINGS.md) - Post editor

---

**Last Updated:** November 2025  
**Integration Status:** Backend ✅ | Frontend ⏳ (Needs router + three.js)
