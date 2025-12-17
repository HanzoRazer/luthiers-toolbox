# Phase 3.2 Quick Reference — DXF Preflight Validation

**Status:** ✅ Backend Complete, UI Ready for Testing  
**Last Updated:** November 6, 2025

---

## 🚀 Quick Start

### **Test Backend (10 minutes)**

```powershell
# Terminal 1: Start API
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# Terminal 2: Run tests
cd "C:\Users\thepr\Downloads\Luthiers ToolBox"
.\test_dxf_preflight.ps1
```

**Expected:** Health check passes, JSON + HTML reports generated, validation rules verified

### **Test Frontend (Development)**

```powershell
# Terminal 1: API (if not running)
cd services/api && uvicorn app.main:app --reload --port 8000

# Terminal 2: Client dev server
cd packages/client
npm run dev  # http://localhost:5173
```

**Navigate to:** `http://localhost:5173/pipeline-lab`

---

## 📦 Files Created

| File | Size | Purpose |
|------|------|---------|
| `services/api/app/cam/dxf_preflight.py` | 600 lines | Validation engine |
| `services/api/app/routers/blueprint_cam_bridge.py` | Updated | Added `/preflight` endpoint |
| `test_dxf_preflight.ps1` | 200 lines | Test script |
| `packages/client/src/views/PipelineLab.vue` | 700+ lines | UI workflow |
| `PHASE3_2_DXF_PREFLIGHT_COMPLETE.md` | 1000+ lines | Full documentation |

---

## 🔌 API Endpoints

### **POST `/api/cam/blueprint/preflight`**

**Parameters:**
- `file` (form-data): DXF file to validate
- `format` (query): "json" or "html"

**JSON Response:**
```json
{
  "filename": "gibson_l00_body.dxf",
  "passed": false,
  "issues": [
    {
      "severity": "ERROR",
      "message": "Open LWPOLYLINE found",
      "category": "geometry",
      "layer": "Contours",
      "suggestion": "Close path in CAD"
    }
  ],
  "summary": {
    "errors": 1,
    "warnings": 3,
    "info": 2
  }
}
```

**HTML Response:** Visual report with color-coded badges

---

## 🎯 Validation Categories (5)

| Category | Checks | Example Issue |
|----------|--------|---------------|
| **Layer** | GEOMETRY/CONTOURS, excessive layers | "No CONTOURS layer found" |
| **Entity** | CAM-compatible types (LWPOLYLINE/LINE) | "No machinable entities" |
| **Geometry** | Closed paths, zero-length segments | "Open LWPOLYLINE found" |
| **Dimension** | Bounding box (50-2000mm) | "Very small dimensions (5mm)" |
| **Units** | Scale reasonableness | "Dimension outlier detected" |

---

## ⚠️ Severity Levels (3)

| Level | Color | Meaning | Action |
|-------|-------|---------|--------|
| **ERROR** | 🔴 Red | Blocks CAM processing | Fix required |
| **WARNING** | 🟡 Yellow | May cause issues | Review suggested |
| **INFO** | 🔵 Blue | Optimization tip | Optional improvement |

---

## 🖥️ PipelineLab UI Workflow

```
┌─────────────────────┐
│ 1. Upload DXF       │  Drag-drop or browse
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ 2. Preflight Check  │  Validate geometry
│  ├─ Status badge    │  ✅ PASSED / ❌ FAILED
│  ├─ Issue list      │  Categorized by severity
│  └─ HTML report     │  Download visual report
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ 3. Reconstruct      │  Chain primitives (if needed)
│  ├─ Layer select    │  Choose contour layer
│  ├─ Tolerance       │  0.1mm default
│  └─ Loop preview    │  Visualize extracted loops
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ 4. Adaptive Pocket  │  Generate toolpath
│  ├─ Tool params     │  Diameter, stepover, feeds
│  ├─ Strategy        │  Spiral or Lanes
│  └─ G-code export   │  Download NC file
└─────────────────────┘
```

---

## 🧪 Test Script Usage

```powershell
.\test_dxf_preflight.ps1
```

**Tests:**
1. Health check (Phase 3.2 endpoints)
2. Preflight JSON (parse response, display issues)
3. Preflight HTML (generate report, validate structure)
4. Validation rules (5 checks: parsing, layers, entities, categories, severity)

**Opens:** HTML report in browser on success

---

## 💡 Common Issues & Fixes

### **"Open LWPOLYLINE found"** (ERROR)
- **Cause:** Path not closed (required for pocketing)
- **Fix:** Close path in CAD software or use contour reconstruction

### **"Very small dimensions (5.2mm)"** (WARNING)
- **Cause:** Unit conversion issue (inches imported as mm)
- **Fix:** Scale by 25.4× (inch → mm)

### **"SPLINE entity will need reconstruction"** (INFO)
- **Cause:** SPLINEs not directly machinable
- **Fix:** Use `/reconstruct-contours` endpoint

### **"No CAM-compatible entities"** (ERROR)
- **Cause:** DXF contains only TEXT/MTEXT
- **Fix:** Add LWPOLYLINE/LINE geometry in CAD

---

## 🔗 Quick Links

| Resource | Path |
|----------|------|
| **Full Docs** | `PHASE3_2_DXF_PREFLIGHT_COMPLETE.md` |
| **Phase 3.1** | `PHASE3_1_CONTOUR_RECONSTRUCTION_COMPLETE.md` |
| **Test Script** | `test_dxf_preflight.ps1` |
| **Validation Engine** | `services/api/app/cam/dxf_preflight.py` |
| **API Router** | `services/api/app/routers/blueprint_cam_bridge.py` |
| **UI Component** | `packages/client/src/views/PipelineLab.vue` |
| **OM Project** | `OM Project/Gibson/L-00/gibson_l00_body.dxf` |

---

## ✅ Phase 3.2 Status

| Component | Status | Lines | Purpose |
|-----------|--------|-------|---------|
| **Validation Engine** | ✅ Complete | 600 | 5 check categories, 3 severity levels |
| **HTML Report** | ✅ Complete | Embedded | Visual validation report |
| **/preflight Endpoint** | ✅ Complete | 100 | JSON + HTML formats |
| **Test Script** | ✅ Complete | 200 | Comprehensive testing |
| **PipelineLab UI** | ✅ Complete | 700+ | 4-stage workflow |

---

## 🎯 Next Steps

1. **Test Backend:** Run `test_dxf_preflight.ps1`
2. **Test UI:** Start client dev server, navigate to /pipeline-lab
3. **End-to-End:** Test Gibson L-00 full workflow
4. **Integration:** Add to main navigation, CI/CD
5. **Phase 3.3:** Advanced features (self-intersection, volume calc)

---

**Pattern:** Port of `nc_lint.py` validation system to DXF input files  
**Integration:** Phase 3.2 of Blueprint → CAM pipeline  
**Dependencies:** ezdxf, FastAPI, Vue 3, Phase 3.1 (contour reconstruction)
