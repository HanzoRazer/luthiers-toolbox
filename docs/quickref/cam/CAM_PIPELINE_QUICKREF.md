# CAM Pipeline Integration - Quick Reference

**Status:** ✅ Phase 1 Complete | ⏸️ Phase 2 Pending  
**Date:** November 9, 2025

---

## 🎯 What's Ready Now

### Backend Endpoints (✅ Working)
```bash
GET    /cam/pipeline/presets          # List all presets
POST   /cam/pipeline/presets          # Create preset
GET    /cam/pipeline/presets/{id}     # Get preset by ID
DELETE /cam/pipeline/presets/{id}     # Delete preset
POST   /cam/plan_from_dxf             # DXF → loops JSON
```

### Frontend Components (✅ Created)
- `types/cam.ts` - Shared TypeScript types
- `components/cam/CamBackplotViewer.vue` - Toolpath visualization
- `components/CamPipelineGraph.vue` - Op status nodes

---

## 🚀 Quick Start

### 1. Start Backend
```powershell
cd "services/api"
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --port 8000
```

### 2. Test Endpoints
```powershell
cd "..\\.."
.\test_pipeline_integration_phase1.ps1
```

**Expected Output:**
```
=== Testing CAM Pipeline Integration - Phase 1 ===

1. Testing Health Check
  ✓ Server is running

2. Testing GET /cam/pipeline/presets
  ✓ Presets endpoint working
  Found 0 preset(s)

3. Testing POST /cam/pipeline/presets
  ✓ Created preset: Test_GRBL_6mm
    ID: abc-123-uuid
    Units: mm
    Machine: GUITAR_CNC_01
    Post: GRBL

5. Testing POST /cam/plan_from_dxf
  ✓ DXF plan extraction successful
    Loops found: 1
    Layer: GEOMETRY
    Tool diameter: 6.0 mm
```

---

## 📦 File Structure

```
services/api/app/
├── schemas/
│   └── cam_sim.py                     # NEW - SimIssue normalization
├── routers/
│   ├── pipeline_presets_router.py     # NEW - Preset CRUD
│   └── dxf_plan_router.py             # NEW - DXF → loops
└── data/
    └── pipeline_presets.json          # NEW - Storage (auto-created)

packages/client/src/
├── types/
│   └── cam.ts                         # NEW - Shared types
└── components/
    ├── cam/
    │   └── CamBackplotViewer.vue      # NEW - Toolpath viz
    └── CamPipelineGraph.vue           # NEW - Op graph

test_pipeline_integration_phase1.ps1   # NEW - Backend tests
```

---

## 🔌 API Examples

### Create Preset
```bash
curl -X POST http://localhost:8000/cam/pipeline/presets \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "My_Setup",
    "units": "mm",
    "machine_id": "GUITAR_CNC_01",
    "post_id": "GRBL"
  }'
```

### DXF to Loops
```bash
curl -X POST http://localhost:8000/cam/plan_from_dxf \
  -F "file=@body.dxf" \
  -F "tool_d=6.0" \
  -F "units=mm" \
  -F "stepover=0.45"
```

**Response:**
```json
{
  "plan": {
    "loops": [{"pts": [[0,0], [100,0], [100,60], [0,60]]}],
    "units": "mm",
    "tool_d": 6.0,
    "stepover": 0.45,
    "stepdown": 2.0,
    "margin": 0.5,
    "strategy": "Spiral",
    "feed_xy": 1200.0,
    "safe_z": 5.0,
    "z_rough": -1.5
  },
  "debug": {
    "filename": "body.dxf",
    "layer": "GEOMETRY",
    "loop_count": 1,
    "warnings": [],
    "preflight": {...}
  }
}
```

---

## 🧩 Component Usage (Pending Views)

### CamBackplotViewer
```vue
<template>
  <CamBackplotViewer
    :loops="boundaryLoops"
    :moves="toolpathMoves"
    :overlays="slowdownOverlays"
    :sim-issues="collisionIssues"
    v-model:show-toolpath="showToolpath"
    @segment-hover="onSegmentHover"
    @overlay-hover="onOverlayHover"
  />
</template>

<script setup lang="ts">
import CamBackplotViewer from '@/components/cam/CamBackplotViewer.vue'
import type { BackplotLoop, BackplotMove } from '@/types/cam'

const boundaryLoops: BackplotLoop[] = [
  { pts: [[0,0], [100,0], [100,60], [0,60]] }
]
const toolpathMoves: BackplotMove[] = result.value?.moves ?? []
</script>
```

### CamPipelineGraph
```vue
<template>
  <CamPipelineGraph :results="pipelineResults" />
</template>

<script setup lang="ts">
const pipelineResults = [
  { kind: 'dxf_preflight', ok: true },
  { kind: 'adaptive_plan', ok: true },
  { kind: 'adaptive_plan_run', ok: true },
  { kind: 'export_post', ok: true },
  { kind: 'simulate_gcode', ok: false, error: 'Collision detected' }
]
</script>
```

---

## ⏱️ What's Next (Phase 2)

### Immediate (High Priority)
1. **CamPipelineRunner.vue** (~30 min)
   - DXF upload interface
   - Preset selector/saver
   - Pipeline run button
   - Results display

2. **AdaptiveLabView.vue** (~45 min)
   - `/lab/adaptive` view
   - DXF import → loops
   - Adaptive kernel testing
   - Backplot preview

3. **PipelineLabView.vue** (~20 min)
   - `/lab/pipeline` view
   - Full pipeline orchestration
   - Sim issues overlay

4. **Router Config** (~5 min)
   - Add `/lab/*` routes

---

## 🐛 Troubleshooting

### Backend Won't Start
```powershell
# Check Python environment
cd services/api
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Check for port conflicts
netstat -ano | findstr :8000
```

### Preset Endpoint Returns 404
```powershell
# Verify router registration
grep -r "pipeline_presets_router" services/api/app/main.py
# Should see: app.include_router(pipeline_presets_router)
```

### DXF Import Fails
```powershell
# Check DXF has LWPOLYLINE on GEOMETRY layer
# Verify with ezdxf:
python -c "import ezdxf; doc=ezdxf.readfile('body.dxf'); print([e.dxftype() for e in doc.modelspace()])"
```

---

## 📊 Integration Checklist

### Phase 1 (✅ Complete)
- [x] Backend infrastructure
- [x] Pipeline presets router
- [x] DXF plan router
- [x] SimIssue schema
- [x] CamBackplotViewer component
- [x] CamPipelineGraph component
- [x] Type definitions
- [x] Router registration
- [x] Test script

### Phase 2 (⏸️ Pending)
- [ ] CamPipelineRunner component
- [ ] AdaptiveLabView view
- [ ] PipelineLabView view
- [ ] Router configuration
- [ ] E2E workflow test
- [ ] Complete documentation

---

## 📚 Related Documentation

- [CAM_PIPELINE_PARSE_INTEGRATION_SUMMARY.md](./CAM_PIPELINE_PARSE_INTEGRATION_SUMMARY.md) - Full integration details
- [CAM_PIPELINE_INTEGRATION_PHASE1.md](./CAM_PIPELINE_INTEGRATION_PHASE1.md) - Component specifications
- [ADAPTIVE_POCKETING_MODULE_L.md](./ADAPTIVE_POCKETING_MODULE_L.md) - L.3 kernel docs
- [PHASE3_2_DXF_PREFLIGHT_COMPLETE.md](./PHASE3_2_DXF_PREFLIGHT_COMPLETE.md) - DXF validation

---

**Quick Commands:**
```powershell
# Start backend
cd services/api && .\.venv\Scripts\Activate.ps1 && python -m uvicorn app.main:app --reload --port 8000

# Test backend
.\test_pipeline_integration_phase1.ps1

# Start frontend (when views ready)
cd packages/client && npm run dev
```

**Status:** ✅ Backend Ready | ⏸️ Frontend Views Pending  
**Progress:** 40% Complete  
**ETA:** ~2 hours to Phase 2 completion
