# Phase 25.0 Pipeline Preset Integration - Quick Reference

## 🎯 What It Does
Save BridgeLab configurations as reusable pipeline presets. Run them immediately or later via standalone runner.

## 📍 Access Points

### **BridgeLab Panel**
- **URL:** `/lab/bridge`
- **Location:** Below "Machine Envelope Selection" panel
- **Actions:** Save preset, Save & Run preset

### **Standalone Runner**
- **URL:** `/lab/pipeline-preset` or `/lab/pipeline-preset?preset_id=YOUR_ID`
- **Actions:** Run preset by ID

## ⚡ Quick Start

### **Save a Preset**
1. Navigate to `/lab/bridge`
2. Upload DXF via preflight panel
3. Select machine (e.g., Shapeoko Pro)
4. Configure adaptive params (tool, stepover, stepdown, feed)
5. Scroll to "Save as Pipeline Preset" panel
6. Enter preset name (e.g., "Bridge Pocket 6mm")
7. Click "Save preset"
8. **Result:** Success message with preset ID

### **Save & Run**
1. Same setup as "Save a Preset"
2. Click "Save & Run" button
3. **Result:** Preset saved AND pipeline executes immediately

### **Run Saved Preset**
1. Navigate to `/lab/pipeline-preset`
2. Enter preset ID (from save step)
3. Click "Run Pipeline"
4. **Result:** JSON result displays with run ID and step outputs

## 🔧 API Endpoints

### **Backend**
```
POST /api/cam/pipeline/presets/{preset_id}/run
```
**Body:** `{}` (empty JSON)  
**Response:** Pipeline run result (run_id, steps, errors)

### **Error Codes**
- `404`: Preset not found
- `500`: Invalid preset spec
- `502`: Pipeline execution failed

## 📦 Components

### **Backend**
- `services/api/app/routers/cam_pipeline_preset_run_router.py` (85 lines)
- Registration: `services/api/app/main.py`
- Dependency: `httpx>=0.24.0`

### **Frontend**
- `packages/client/src/components/CamBridgeToPipelinePanel.vue` (262 lines)
- `client/src/views/PipelinePresetRunner.vue` (182 lines)
- Route: `client/src/router/index.ts` → `/lab/pipeline-preset`

## 🧪 Testing

### **1. Backend Smoke Test**
```powershell
cd services/api
pip install httpx  # If not installed
uvicorn app.main:app --reload --port 8000

# In another terminal:
curl http://localhost:8000/health
# Expected: {"ok": true}
```

### **2. Frontend Smoke Test**
```powershell
cd client
npm run dev

# Browser:
# 1. http://localhost:5173/lab/bridge → Panel visible below machine envelope
# 2. http://localhost:5173/lab/pipeline-preset → Preset runner visible
```

### **3. Workflow Test**
1. Save preset from BridgeLab → Verify success message
2. Copy preset ID from success message
3. Navigate to `/lab/pipeline-preset?preset_id=YOUR_ID`
4. Click "Run Pipeline" → Verify result JSON

## 🐛 Troubleshooting

### **Issue:** "Could not load cam_pipeline_preset_run_router"
**Solution:** Install httpx: `pip install httpx>=0.24.0`

### **Issue:** Panel not visible in BridgeLab
**Solution:** Hard refresh browser (Ctrl+Shift+R) to clear component cache

### **Issue:** "Preset not found" error
**Solution:** Verify preset ID matches saved preset (check database or success message)

### **Issue:** "Pipeline execution failed" error
**Solution:** Check server logs for pipeline runner errors (invalid geometry, missing machine config)

## 📊 Preset Spec Format

```json
{
  "name": "Bridge Pocket 6mm Standard",
  "spec": {
    "ops": [
      { "step": "dxf_preflight", "layer": "GEOMETRY" },
      { "step": "adaptive_plan", "tool_d": 6.0, "stepover": 0.45, "stepdown": 2.0 },
      { "step": "adaptive_plan_run", "feed_xy": 1200 },
      { "step": "export_post", "post_id": "GRBL" },
      { "step": "simulate_gcode" }
    ],
    "tool_d": 6.0,
    "units": "mm",
    "geometry_layer": "GEOMETRY",
    "machine_id": "shapeoko_pro",
    "post_id": "GRBL"
  }
}
```

## 💡 Use Cases

### **Solo Luthier**
- Save proven workflows for recurring tasks (bridge pockets, fretboard slots)
- Test tool/feed combinations, keep best configs

### **Team**
- Share preset IDs in chat (Slack, Discord)
- Bookmarkable URLs: `/lab/pipeline-preset?preset_id=team_standard_6mm`

### **Production Shop**
- Encode best practices in presets (safety margins, proven feeds)
- Reduce manual parameter entry errors

## 🚀 Next Steps

1. **Install httpx:** `pip install httpx`
2. **Restart server:** Check logs for import errors
3. **Test save workflow:** Save preset from BridgeLab
4. **Test run workflow:** Run preset from standalone runner
5. **Share presets:** Send preset IDs to team members

## 📝 Files Modified

| File | Changes |
|------|---------|
| `services/api/app/main.py` | Router import + registration |
| `services/api/requirements.txt` | Added httpx>=0.24.0 |
| `packages/client/src/views/BridgeLabView.vue` | Imported + mounted panel |
| `client/src/router/index.ts` | Added `/lab/pipeline-preset` route |

## 📝 Files Created

| File | Purpose | Lines |
|------|---------|-------|
| `services/api/app/routers/cam_pipeline_preset_run_router.py` | Run endpoint | 85 |
| `packages/client/src/components/CamBridgeToPipelinePanel.vue` | Save UI | 262 |
| `client/src/views/PipelinePresetRunner.vue` | Standalone runner | 182 |

---

**Status:** ✅ Complete (All 7 tasks)  
**Ready:** Backend + frontend complete, awaiting `pip install httpx` and testing  
**Documentation:** See `PHASE_25_0_PIPELINE_PRESET_COMPLETE.md` for full details
