# CAM Essentials N0-N10: Quick Reference

**Component:** CAMEssentialsLab.vue  
**Route:** `/lab/cam-essentials`  
**Backend:** 9 routers (roughing, drilling, drill_pattern, probe, retract, biarc)  
**Tests:** `test_cam_essentials_n0_n10.ps1` (12 tests)

---

## 🎯 Operations at a Glance

| Operation | Badge | Backend Endpoint | UI Lines | Status |
|-----------|-------|-----------------|----------|--------|
| Roughing | N01 | `/cam/roughing/gcode` | 38 | ✅ |
| Drilling | N06 | `/cam/drilling/gcode` | 38 | ✅ |
| Patterns | N07 | `/cam/drill/pattern/gcode` | 58 | ✅ |
| Contour | N10 | `/cam/biarc/gcode` | 32 | ✅ |
| Probe | N09 | `/cam/probe/*` | 47 | ✅ NEW |
| Retract | N08 | `/cam/retract/gcode` | 35 | ✅ NEW |

**Total:** 6 operations, 248 UI lines, 12 smoke tests

---

## 📌 Quick Start

### **1. Access CAM Essentials Lab**
```
http://localhost:5173/lab/cam-essentials
```

### **2. Run Smoke Tests**
```powershell
# Terminal 1: Start backend
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# Terminal 2: Run tests
cd ../..
.\test_cam_essentials_n0_n10.ps1
```

### **3. Expected Output**
```
✓ All CAM Essentials (N0-N10) tests passed!
  - N01: Roughing (GRBL, Mach4)
  - N06: Drilling (G81, G83)
  - N07: Drill Patterns (Grid, Circle, Line)
  - N08: Retract Patterns (Direct, Helical)
  - N09: Probe Patterns (Corner, Boss, Surface)

CAM Essentials integration is production-ready!
```

---

## 🔧 API Examples

### **N01: Roughing**
```bash
curl -X POST http://localhost:8000/api/cam/roughing/gcode \
  -H 'Content-Type: application/json' \
  -d '{
    "width": 100.0,
    "height": 60.0,
    "stepdown": 3.0,
    "stepover": 2.5,
    "feed": 1200.0,
    "safe_z": 5.0,
    "post": "GRBL",
    "units": "mm"
  }'
```

### **N06: Drilling G83 (Peck)**
```bash
curl -X POST http://localhost:8000/api/cam/drilling/gcode \
  -H 'Content-Type: application/json' \
  -d '{
    "cycle": "G83",
    "holes": [{"x":10,"y":10}, {"x":20,"y":10}],
    "depth": -20.0,
    "retract": 2.0,
    "feed": 250.0,
    "peck_depth": 3.0,
    "post_id": "GRBL",
    "units": "mm"
  }'
```

### **N07: Drill Pattern (Grid)**
```bash
curl -X POST 'http://localhost:8000/api/cam/drill/pattern/gcode?z=-10&feed=300&cycle=G81&post=GRBL' \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "grid",
    "origin_x": 0.0,
    "origin_y": 0.0,
    "grid": {"rows": 3, "cols": 4, "dx": 10.0, "dy": 10.0}
  }'
```

### **N09: Probe Pattern (Corner)**
```bash
curl -X POST http://localhost:8000/api/cam/probe/corner \
  -H 'Content-Type: application/json' \
  -d '{
    "pattern": "corner_outside",
    "approach_distance": 20.0,
    "retract_distance": 2.0,
    "feed_probe": 100.0,
    "safe_z": 10.0,
    "work_offset": 1
  }'
```

### **N08: Retract Pattern (Helical)**
```bash
curl -X POST http://localhost:8000/api/cam/retract/gcode \
  -H 'Content-Type: application/json' \
  -d '{
    "strategy": "helical",
    "current_z": -15.0,
    "safe_z": 5.0,
    "helix_radius": 5.0,
    "helix_pitch": 1.0
  }'
```

---

## 🎨 UI Component Structure

```vue
<!-- CAMEssentialsLab.vue -->
<template>
  <div class="cam-essentials-lab">
    <h1>CAM Essentials Lab</h1>
    
    <div class="operations-grid">
      <!-- 6 operation cards -->
      <div class="operation-card"> ... </div>
    </div>
    
    <div class="info-section"> ... </div>
  </div>
</template>

<script setup lang="ts">
// 6 reactive parameter groups
const roughing = ref({ ... })
const drilling = ref({ ... })
const pattern = ref({ ... })
const biarc = ref({ ... })
const probe = ref({ ... })     // NEW
const retract = ref({ ... })   // NEW

// 6 export functions
async function exportRoughing() { ... }
async function exportDrilling() { ... }
async function exportPattern() { ... }
async function exportBiarc() { ... }
async function exportProbeGcode() { ... }     // NEW
async function exportProbeSVG() { ... }       // NEW
async function exportRetractGcode() { ... }   // NEW
</script>
```

---

## 📊 Post-Processor Support

| Post | Modal Cycles | Arc Mode | Dwell | Probing |
|------|-------------|----------|-------|---------|
| GRBL | ⚠️ Expand | I/J | G4 P | G38.2 |
| Mach4 | ✅ Native | I/J | G4 P | G31 |
| LinuxCNC | ✅ Native | I/J | G4 P | G38.2 |
| PathPilot | ✅ Native | I/J | G4 P | G38.2 |
| MASSO | ✅ Native | I/J | G4 P | G31 |
| Haas | ✅ Native | R-mode | G4 S | G31 |

**Note:** GRBL requires `expand_cycles: true` for drilling (converts G81-G89 to G0/G1)

---

## 🧪 Testing Checklist

### **Pre-Flight**
- [ ] Backend running on port 8000
- [ ] All routers registered (check `main.py` lines 324-382)
- [ ] Post configs present (`services/api/app/data/posts/*.json`)

### **Smoke Test Validation**
- [ ] N01: Roughing exports with G21 (mm mode)
- [ ] N06: Drilling G81 contains modal cycle code
- [ ] N06: Drilling G83 contains peck depth (Q parameter)
- [ ] N07: Grid pattern generates 12 holes (3×4)
- [ ] N07: Circle pattern generates 6 holes
- [ ] N09: Corner probe contains G31 commands
- [ ] N09: Boss probe generates 4-point pattern
- [ ] N08: Direct retract uses G0 rapid
- [ ] N08: Helical retract contains G2/G3 arcs

### **UI Validation**
- [ ] All 6 operation cards render
- [ ] Post selector dropdowns populated
- [ ] Export buttons trigger downloads
- [ ] Parameters update reactively
- [ ] Conditional fields show/hide correctly (peck depth, helix params)

---

## 🐛 Troubleshooting

### **Issue:** Export button doesn't download file
**Fix:** Check browser console for CORS or network errors. Ensure backend is running.

### **Issue:** Test fails with "Expected content not found"
**Fix:** Check router registration in `main.py`. Verify endpoint prefix (e.g., `/api/cam/...`).

### **Issue:** Probe pattern returns 404
**Fix:** Ensure `probe_router.py` is registered (line 378-382 in `main.py`). Check `probe_patterns.py` exists.

### **Issue:** Drilling cycles not expanded for GRBL
**Fix:** Set `expand_cycles: true` in request body. GRBL doesn't support modal cycles natively.

---

## 📝 Common Workflows

### **Workflow 1: Bridge Pocket with Probe Setup**
1. **Probe:** Corner outside → Set G54 work offset
2. **Roughing:** 100×60mm pocket, 3mm stepdown, GRBL post
3. **Drilling:** G83 peck drill 6 bridge pin holes (12mm deep)
4. **Export:** Download `.nc` files, load into GRBL sender

### **Workflow 2: Control Cavity with Multiple Posts**
1. **Pattern:** Grid 4×3 for mounting screws
2. **Roughing:** 80×50mm cavity, 2mm stepdown
3. **Probe:** Surface Z to find cavity depth
4. **Export:** GRBL for prototyping, Mach4 for production

### **Workflow 3: Helical Retract from Deep Pocket**
1. **Roughing:** 120×80mm pocket, 10mm depth
2. **Retract:** Helical spiral (5mm radius, 1mm pitch)
3. **Export:** Prevents side load on tool during rapid

---

## 🔗 Related Routes

| Route | Component | Purpose |
|-------|-----------|---------|
| `/lab/cam-essentials` | CAMEssentialsLab | Main unified lab (6 ops) |
| `/lab/drilling` | DrillingLab | Advanced drilling UI (688 lines) |
| `/cam/dashboard` | CAMDashboard | Operation catalog |
| `/lab/helical` | HelicalRampLab | Helical Z-ramping (v16.1) |
| `/lab/adaptive-kernel` | AdaptiveKernelLab | Adaptive pocketing (Module L) |

---

## 📚 Documentation

- [CAM Essentials Status](./CAM_ESSENTIALS_N0_N10_STATUS.md) - Full analysis
- [Integration Complete](./CAM_ESSENTIALS_N0_N10_INTEGRATION_COMPLETE.md) - Session summary
- [A_N Build Roadmap](./A_N_BUILD_ROADMAP.md) - Release planning
- [Patch N01](./PATCH_N01_ROUGHING_POST_MIN.md) - Roughing integration
- [Patch N06](./PATCH_N06_MODAL_CYCLES.md) - Drilling cycles
- [Patch N09](./PATCH_N09_PROBE_PATTERNS.md) - Probe patterns

---

**Quick Status:** ✅ 85% Complete, Production-Ready  
**Last Updated:** November 17, 2025  
**Test Command:** `.\test_cam_essentials_n0_n10.ps1`
