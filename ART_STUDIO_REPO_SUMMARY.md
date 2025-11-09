# Art Studio Repository - Detailed Summary & Deployment Guide

**Location:** `C:\Users\thepr\Downloads\Luthiers ToolBox\ToolBox_Art_Studio-repo`  
**Date Analyzed:** November 6, 2025  
**Total Versions:** 22 distinct packages (scaffolds v1-v13, production v15-v15.5, tools v1-v2)

---

## 📦 Repository Structure Overview

This repository contains **incremental development snapshots** of the **Art Studio CAM System** for guitar lutherie, organized into three categories:

### **1. Scaffold Versions (v1-v13)** - Proof-of-Concept Phases
Early development iterations focusing on V-carve art generation and SVG-to-G-code conversion.

### **2. Production Versions (v15-v15.5)** - Production-Ready CAM System
Advanced G-code post-processor system with multi-controller support, CRC, and lead-in/out.

### **3. API Environment Tools (v1-v2)** - DevOps Utilities
Deployment scripts, health checks, and environment management tools.

---

## 🎯 Latest Production Version: **v15.5**

### **Phase 15.5 Features (Most Current)**

**Backend: `cam_post_v155_router.py`** (360 lines)
- **Post-Processor Presets:** GRBL, Mach3, Haas, Marlin
- **Advanced Toolpath Features:**
  - ✅ Lead-in/out strategies (tangent, 90° arc, or none)
  - ✅ CRC-ready output (G41/G42 with optional D# and diameter comments)
  - ✅ Automatic corner smoothing (fillet arcs at sharp corners)
  - ✅ Arc mode selection (IJ or R format)
  - ✅ Axis modal optimization (suppress redundant coordinates)
  - ✅ Arc sweep limiting (prevents >180° arcs for GRBL/Marlin)

**Frontend: `ArtStudioPhase15_5.vue`** (150 lines)
- Interactive UI with preset selector
- Real-time parameter controls:
  - Contour input (JSON polyline)
  - Z-cut depth, feed rate, safe height
  - Lead-in/out type and dimensions
  - CRC mode selection (left/right/none)
  - Corner smoothing parameters (radius, minimum angle)
- 3D toolpath preview
- G-code output display

**Post Presets JSON Configuration:**
```json
{
  "GRBL": {
    "units": "metric",
    "arc_mode": "IJ",
    "allow_major_arc": false,
    "axis_modal_opt": true,
    "arc_max_sweep_deg": 179.9,
    "header": ["(GRBL post v15.5)", "G21", "G90", "G94"],
    "footer": ["M5", "G0 Z5.000"]
  },
  "Mach3": { /* similar with allow_major_arc: true */ },
  "Haas": { /* inch units, G28 homing */ },
  "Marlin": { /* R-mode arcs, no modal optimization */ }
}
```

---

## 🔧 API Endpoints (v15.5)

### **GET `/api/cam_gcode/posts_v155`**
Returns all available post-processor presets with their configurations.

**Response:**
```json
{
  "version": "v15.5",
  "presets": {
    "GRBL": { /* config */ },
    "Mach3": { /* config */ },
    "Haas": { /* config */ },
    "Marlin": { /* config */ }
  }
}
```

---

### **POST `/api/cam_gcode/post_v155`**
Generates G-code from a contour path with advanced options.

**Request Body:**
```typescript
{
  contour: [[0,0], [20,0], [20,10], [0,10], [0,0]], // XY points (mm)
  z_cut_mm: -1.0,                  // Cutting depth
  feed_mm_min: 600.0,              // Feed rate
  plane_z_mm: 5.0,                 // Safe height for rapids
  safe_rapid: true,
  
  // Post-processor selection
  preset: "GRBL",                  // or "Mach3", "Haas", "Marlin"
  custom_post?: { /* override preset fields */ },
  
  // Lead-in/out
  lead_type: "tangent",            // "none", "tangent", or "arc"
  lead_len_mm: 3.0,                // Linear lead length
  lead_arc_radius_mm: 2.0,         // Arc lead radius
  
  // Cutter radius compensation
  crc_mode: "none",                // "none", "left" (G41), "right" (G42)
  crc_diameter_mm?: 6.0,           // Tool diameter (optional)
  d_number?: 1,                    // Wear table index (optional)
  
  // Corner smoothing
  fillet_radius_mm: 0.4,           // Fillet arc radius
  fillet_angle_min_deg: 20.0       // Only fillet corners tighter than this
}
```

**Response:**
```json
{
  "gcode": "(GRBL post v15.5)\nG21\nG90\n...",
  "spans": [
    {"type": "rapid", "x1": 0, "y1": 0, "z1": 5, ...},
    {"type": "line", "x1": 0, "y1": 0, "z1": -1, ...}
  ]
}
```

---

## 🧪 Testing & Smoke Tests (v15.5_smoke)

### **Smoke Test Script: `smoke_posts.ps1`**
```powershell
# Automated testing for all post-processor presets
Param(
  [string]$Host = "127.0.0.1",
  [int]$Port = 8135
)

# Tests:
# 1. Starts API server on specified port
# 2. Calls GET /api/cam_gcode/smoke/posts
# 3. Validates all 4 presets return non-empty G-code
# 4. Reports pass/fail per preset
# 5. Cleans up API server process
```

### **Smoke Test Endpoint: `cam_smoke_v155_router.py`**
```python
@router.get("/smoke/posts")
def smoke_posts():
    """
    Tests all post presets with standard contour:
    - GRBL, Mach3, Haas, Marlin
    - 60x25mm rectangle
    - Tangent lead-in (3mm)
    - 0.3mm fillet radius
    - Returns ok: bool + results per preset
    """
```

**Usage:**
```powershell
# PowerShell (Windows)
.\smoke_posts.ps1 -Host 127.0.0.1 -Port 8135

# Makefile (Unix/macOS)
make api-smoke-posts
```

---

## 📋 Version Evolution Timeline

### **Scaffold Phase (v1-v13)** - Proof of Concept

| Version | Key Feature | Files |
|---------|-------------|-------|
| **v1** | Basic V-carve scaffold | SVG generator, naive toolpath converter |
| **v2** | Improved SVG handling | Enhanced polyline processing |
| **v3** | DXF I/O support | `dxf_io.py`, `svg_gen.py`, `vcarve_toolpath.py` |
| **v4-v5** | CAM integration | Auto-detect routing, project management |
| **v6** | Notification system | `cam_notify.py`, WebSocket support |
| **v7** | Projects router | REST API for design library |
| **v8-v9** | V-carve refinement | `cam_vcarve_router.py` with infill preview |
| **v10-v11** | UI enhancements | Component library expansion |
| **v12** | Performance optimization | Batch processing, caching |
| **v13** | **Folded UI + Preview Infill** | Production-ready preview overlay |

### **Production Phase (v15-v15.5)** - Release Candidates

| Version | Key Feature | Lines | Status |
|---------|-------------|-------|--------|
| **v15** | SVG smoothing | `cam_svg_smooth_router.py` | ✅ |
| **v15.1** | Preview scallop + SVG refine | 2 routers | ✅ |
| **v15.2** | G-code arcs (basic) | `cam_gcode_arcs_router.py` | ✅ |
| **v15.3** | G-code arcs v2 (improved) | `cam_gcode_arcs_v153_router.py` | ✅ |
| **v15.4** | G-code arcs v3 (optimized) | `cam_gcode_arcs_v154_router.py` | ✅ |
| **v15.5** | **Post presets + CRC + Lead-in/out** | 360 lines | ✅ **CURRENT** |

---

## 🚀 Deployment Instructions

### **Step 1: Copy v15.5 Files to Main Repository**

```powershell
# Copy backend router
Copy-Item `
  "C:\Users\thepr\Downloads\Luthiers ToolBox\ToolBox_Art_Studio-repo\ToolBox_Art_Studio_v15_5\backend\app\routers\cam_post_v155_router.py" `
  "C:\Users\thepr\Downloads\Luthiers ToolBox\services\api\app\routers\"

# Copy post presets JSON
Copy-Item `
  "C:\Users\thepr\Downloads\Luthiers ToolBox\ToolBox_Art_Studio-repo\ToolBox_Art_Studio_v15_5\backend\app\posts\posts_v155.json" `
  "C:\Users\thepr\Downloads\Luthiers ToolBox\services\api\app\data\posts\"

# Copy frontend view
Copy-Item `
  "C:\Users\thepr\Downloads\Luthiers ToolBox\ToolBox_Art_Studio-repo\ToolBox_Art_Studio_v15_5\frontend\src\views\ArtStudioPhase15_5.vue" `
  "C:\Users\thepr\Downloads\Luthiers ToolBox\packages\client\src\views\"

# Copy frontend API helper
Copy-Item `
  "C:\Users\thepr\Downloads\Luthiers ToolBox\ToolBox_Art_Studio-repo\ToolBox_Art_Studio_v15_5\frontend\src\api\postv155.ts" `
  "C:\Users\thepr\Downloads\Luthiers ToolBox\packages\client\src\api\"
```

---

### **Step 2: Register Router in FastAPI**

**Edit:** `services/api/app/main.py`

```python
# Add import (near other router imports)
from .routers import cam_post_v155_router

# Add to app (after existing routers)
app.include_router(cam_post_v155_router.router)
```

---

### **Step 3: Add Frontend Route**

**Edit:** `packages/client/src/router/index.js`

```javascript
{
  path: '/art-studio',
  name: 'ArtStudioPhase15_5',
  component: () => import('@/views/ArtStudioPhase15_5.vue'),
  meta: { title: 'Art Studio - Phase 15.5' }
}
```

---

### **Step 4: Set Environment Variable (Optional)**

If posts JSON is in custom location:

```powershell
# Windows (PowerShell)
$env:CAM_POST_PRESETS = "C:\path\to\posts_v155.json"

# Linux/macOS (Bash)
export CAM_POST_PRESETS="/path/to/posts_v155.json"
```

Or add to `.env`:
```env
CAM_POST_PRESETS=services/api/app/data/posts/posts_v155.json
```

---

### **Step 5: Start Backend**

```powershell
cd "C:\Users\thepr\Downloads\Luthiers ToolBox\services\api"
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

---

### **Step 6: Start Frontend**

```powershell
cd "C:\Users\thepr\Downloads\Luthiers ToolBox\packages\client"
npm run dev
```

---

### **Step 7: Test Deployment**

**API Health Check:**
```powershell
curl http://localhost:8000/api/cam_gcode/posts_v155
```

**Expected Response:**
```json
{
  "version": "v15.5",
  "presets": {
    "GRBL": { /* ... */ },
    "Mach3": { /* ... */ },
    "Haas": { /* ... */ },
    "Marlin": { /* ... */ }
  }
}
```

**UI Test:**
1. Open `http://localhost:5173/art-studio`
2. Select preset: GRBL
3. Use default contour (60×25mm rectangle)
4. Set Z cut: -1.0, Feed: 600
5. Lead type: Tangent, 3mm
6. CRC: None (or test G41/G42)
7. Click "Generate"
8. Verify G-code appears in right panel
9. Check 3D preview shows toolpath

---

## 🔧 API Environment Tools (v2)

### **DevOps Scripts**

Located in: `ToolBox_API_EnvTools_v2/services/api/`

**Makefile targets (Unix/macOS):**
```makefile
api-reinstall     # Rebuild Python venv from requirements.txt
api-health        # Health check against running API
env-lock          # Generate requirements.lock from current venv
```

**PowerShell scripts (Windows):**

1. **`tools/reinstall_api_env.ps1`** - Environment rebuild
   ```powershell
   pwsh -File "services/api/tools/reinstall_api_env.ps1" -Force
   ```

2. **`tools/health_check.ps1`** - API health verification
   ```powershell
   pwsh -File "services/api/tools/health_check.ps1"
   ```

3. **`tools/curl_json_pp.ps1`** - Pretty-print JSON responses
   ```powershell
   # Direct URL
   pwsh -File "services/api/tools/curl_json_pp.ps1" -Url "http://127.0.0.1:8088/api/cam_gcode/posts_v155"
   
   # Pipe from curl
   curl.exe -s http://127.0.0.1:8088/api/posts | pwsh -File "services/api/tools/curl_json_pp.ps1"
   ```

---

## 📊 Code Statistics

### **v15.5 Production Bundle**

| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| **Backend** | `cam_post_v155_router.py` | 360 | Post-processor engine |
| **Backend** | `cam_smoke_v155_router.py` | 45 | Smoke test endpoint |
| **Frontend** | `ArtStudioPhase15_5.vue` | 150 | UI component |
| **Frontend** | `postv155.ts` | 40 | API helper |
| **Config** | `posts_v155.json` | 75 | Post presets |
| **Scripts** | `smoke_posts.ps1` | 15 | Test automation |
| **Docs** | `README_v15_5.txt` | 25 | Integration guide |
| **Total** | - | **710 lines** | Complete system |

---

## 🎨 Key Algorithms (v15.5)

### **1. Corner Fillet Generation**
```python
def _fillet_between(a:Point, b:Point, c:Point, R:float):
    """
    Calculates fillet arc between two line segments at corner point b
    
    Algorithm:
    1. Calculate unit vectors along BA and BC
    2. Compute interior angle θ at corner
    3. Calculate tangent distance: t = R × tan(θ/2)
    4. Find tangent points p1, p2 on segments
    5. Compute arc center along angle bisector
    6. Determine CW/CCW direction via cross product
    
    Returns: (p1, p2, cx, cy, direction)
    """
```

### **2. Lead-In/Out Strategies**

**Tangent Lead:**
- Moves backwards along entry vector by `lead_len_mm`
- Ensures smooth tangent entry to contour
- Prevents sudden direction changes

**Arc Lead:**
- Creates 90° arc from offset position
- Radius controlled by `lead_arc_radius_mm`
- Uses G2 (CW) for smooth approach

### **3. Axis Modal Optimization**
```python
def _axis_modal_emit(line, last_xy):
    """
    Suppresses redundant X/Y coordinates when unchanged
    
    Before: G1 X10.000 Y5.000
            G1 X10.000 Y6.000  # X redundant
    
    After:  G1 X10.000 Y5.000
            G1 Y6.000          # X suppressed
    """
```

---

## 🔗 Integration with Main Luthier's Tool Box

### **Shared Systems:**

1. **Post-Processor Architecture**
   - v15.5 presets → `services/api/app/data/posts/posts_v155.json`
   - Main system posts → `services/api/app/data/posts/*.json`
   - **Recommendation:** Merge preset formats into unified structure

2. **G-code Export Pipeline**
   - Art Studio generates contour G-code
   - Main system handles DXF/SVG → G-code
   - Both use same post-processor token system

3. **Frontend Routing**
   - Art Studio: `/art-studio` route
   - Main system: `/cam/settings` route
   - **Recommendation:** Add Art Studio tab to CAM Settings view

4. **Unit Conversion**
   - Art Studio: Metric-first (mm)
   - Main system: Bidirectional mm ↔ inch (`services/api/app/util/units.py`)
   - **Integration Point:** Add unit selector to Art Studio UI

---

## 📋 Deployment Checklist

### **Pre-Deployment:**
- [ ] Review v15.5 files for conflicts with existing code
- [ ] Check Python dependencies (FastAPI, Pydantic, math, json, os)
- [ ] Verify frontend dependencies (Vue 3, TypeScript)
- [ ] Backup existing `main.py` and router files

### **Backend Integration:**
- [ ] Copy `cam_post_v155_router.py` to `services/api/app/routers/`
- [ ] Copy `posts_v155.json` to `services/api/app/data/posts/`
- [ ] Register router in `main.py`
- [ ] Set `CAM_POST_PRESETS` environment variable (optional)
- [ ] Install smoke test router (optional)

### **Frontend Integration:**
- [ ] Copy `ArtStudioPhase15_5.vue` to `packages/client/src/views/`
- [ ] Copy `postv155.ts` to `packages/client/src/api/`
- [ ] Add route to `router/index.js`
- [ ] Add navigation menu item
- [ ] Verify API proxy configuration (`vite.config.ts`)

### **Testing:**
- [ ] Backend health check: `curl /api/cam_gcode/posts_v155`
- [ ] UI smoke test: Generate G-code with GRBL preset
- [ ] Test all 4 presets (GRBL, Mach3, Haas, Marlin)
- [ ] Verify lead-in/out strategies (tangent, arc)
- [ ] Test CRC mode (G41, G42, G40)
- [ ] Validate corner smoothing with different fillet radii
- [ ] Run automated smoke tests: `.\smoke_posts.ps1`

### **Documentation:**
- [ ] Update main README with Art Studio integration
- [ ] Document API endpoints in main API docs
- [ ] Add usage examples for v15.5 features
- [ ] Create deployment guide for production

---

## 🐛 Known Issues & Considerations

### **1. Post Preset Format Differences**
**Issue:** v15.5 uses different JSON schema than main system posts  
**Impact:** Cannot directly use existing posts with v15.5 router  
**Solution:** Create migration script or unified schema

### **2. CRC Compatibility**
**Issue:** Hobby controllers (GRBL, Marlin) often ignore G41/G42  
**Workaround:** CRC mode emits comments with diameter for reference  
**Production Use:** Only use CRC with industrial controllers (Haas, Mach3)

### **3. Arc Sweep Limits**
**Issue:** GRBL/Marlin reject arcs >180°  
**Mitigation:** `arc_max_sweep_deg` preset splits arcs automatically  
**Testing:** Verify with circular contours

### **4. Lead-In/Out Safety**
**Issue:** Lead moves can exceed material boundaries  
**Mitigation:** Preview toolpath before cutting  
**Enhancement:** Add boundary collision detection (future)

### **5. Unit Conversion**
**Issue:** v15.5 assumes metric input, Haas preset uses inches  
**Current:** Manual conversion required  
**Future:** Integrate with `services/api/app/util/units.py`

---

## 🚀 Recommended Next Steps

### **Immediate (Integration):**
1. Deploy v15.5 to main repository following checklist
2. Test all 4 post presets with sample contours
3. Run smoke tests to validate deployment
4. Add Art Studio link to main navigation

### **Short-Term (Enhancement):**
1. Unify post preset formats (v15.5 + main system)
2. Add unit conversion to Art Studio UI
3. Integrate with existing tool tables (N.12)
4. Add batch contour processing

### **Long-Term (Advanced Features):**
1. 3D surface machining (z-depth modulation)
2. True V-bit width compensation (angle-aware)
3. Automatic tool selection from library
4. Pattern library with save/load/share
5. Real-time collision detection
6. Chip load optimization per material

---

## 📚 Related Documentation

**Main System:**
- [PATCH_N14_UNIFIED_CAM_SETTINGS.md](../PATCH_N14_UNIFIED_CAM_SETTINGS.md) - Post editor system
- [PATCH_N12_MACHINE_TOOL_TABLES.md](../PATCH_N12_MACHINE_TOOL_TABLES.md) - Tool management
- [POST_CHOOSER_SYSTEM.md](../POST_CHOOSER_SYSTEM.md) - Multi-post exports

**Art Studio Versions:**
- `ToolBox_Art_Studio-repo/ToolBox_Art_Studio_v15_5/README_v15_5.txt` - v15.5 guide
- `ToolBox_Art_Studio-repo/ToolBox_Art_Studio_scaffold_v13/README_v13.md` - Preview infill
- `ToolBox_Art_Studio-repo/ToolBox_Art_Studio_scaffold_v1/README.md` - V1 scaffold

**API Tools:**
- `ToolBox_Art_Studio-repo/ToolBox_API_EnvTools_v2/README.txt` - DevOps scripts

---

## 📞 Support & Troubleshooting

### **Issue: Router not found after deployment**
**Symptoms:** `404 Not Found` on `/api/cam_gcode/posts_v155`  
**Fixes:**
1. Verify router imported in `main.py`
2. Check FastAPI startup logs for import errors
3. Restart API server with `--reload` flag
4. Test with `curl -v` to see full error response

### **Issue: UI shows "Failed to load posts"**
**Symptoms:** Toast error in Art Studio UI  
**Fixes:**
1. Check API is running on correct port (8000)
2. Verify CORS settings in `main.py`
3. Check browser console for network errors
4. Test API directly: `curl http://localhost:8000/api/cam_gcode/posts_v155`

### **Issue: G-code output empty or invalid**
**Symptoms:** Empty G-code or CNC controller rejects file  
**Fixes:**
1. Verify contour is closed (first point = last point)
2. Check preset selected matches your controller
3. Test with simple rectangle contour first
4. Validate arc_max_sweep_deg for your controller
5. Review generated G-code line-by-line for syntax errors

### **Issue: Corner fillets not appearing**
**Symptoms:** Sharp corners remain in output  
**Fixes:**
1. Increase `fillet_radius_mm` (try 0.5-1.0)
2. Decrease `fillet_angle_min_deg` (try 10-15°)
3. Verify corner angle is actually sharp enough
4. Check contour has sufficient segment length for fillet

---

## 📈 Version Comparison Matrix

| Feature | v1 (Scaffold) | v13 (Folded UI) | v15.5 (Production) |
|---------|---------------|------------------|---------------------|
| SVG Generation | ✅ Basic | ✅ Advanced | ✅ Production |
| G-code Export | ✅ Naive | ✅ Improved | ✅ Post-processor |
| Preview | ❌ None | ✅ 2D Overlay | ✅ 3D Toolpath |
| Post Presets | ❌ None | ❌ None | ✅ 4 Controllers |
| Lead-in/out | ❌ None | ❌ None | ✅ 2 Strategies |
| CRC Support | ❌ None | ❌ None | ✅ G41/G42 |
| Corner Smoothing | ❌ None | ❌ None | ✅ Auto Fillets |
| Arc Optimization | ❌ None | ✅ Basic | ✅ Controller-aware |
| Testing | ❌ Manual | ✅ Basic | ✅ Smoke Tests |
| Documentation | ✅ Basic | ✅ Good | ✅ Complete |

---

**Summary Status:**
- ✅ **Production Ready:** v15.5 (current deployment candidate)
- ✅ **Fully Documented:** All versions have integration guides
- ✅ **Tested:** Smoke test automation included
- ✅ **Deployable:** Step-by-step deployment guide provided
- ⏳ **Integration Pending:** Main repository deployment needed

**Recommended Action:** Deploy v15.5 to main repository using provided checklist and scripts.
