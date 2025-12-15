# RMOS Integration Quick Start

**Status:** Ready to integrate Phase 1 implementation  
**Date:** November 21, 2025

---

## 🚀 Quick Integration (5 Minutes)

### **Step 1: Register Backend Routers**

Edit `services/api/app/main.py`:

```python
# Add imports at top
from app.api.routes import joblog, rosette_patterns, manufacturing

# Register routers (add after existing routers)
app.include_router(joblog.router, prefix="/api", tags=["RMOS"])
app.include_router(rosette_patterns.router, prefix="/api", tags=["RMOS"])
app.include_router(manufacturing.router, prefix="/api", tags=["RMOS"])
```

### **Step 2: Start Server**

```powershell
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

### **Step 3: Run Smoke Test**

In another terminal:

```powershell
cd C:\Users\thepr\Downloads\Luthiers ToolBox
.\scripts\Test-RMOS-Sandbox.ps1 -Verbose
```

**Expected Output:**
```
=== RMOS Sandbox Smoke Test ===
[ OK ] Pattern created: id=smoke_rosette_20251121..., rings=2
[ OK ] Manufacturing plan received
  Pattern: Smoke Test Rosette ...
  Guitars: 4
  Strip families: 1
  
  Strip Plans:
    - Family: bw_checker_main
      Tiles needed: 2246
      Strip length: 17.97 m
      Sticks needed: 67

[ OK ] Pattern found in library: Smoke Test Rosette ...
[ OK ] JobLog entries: total=1, rosette_plan=1, saw_slice_batch=0
[ OK ] Test pattern deleted
=== RMOS smoke test completed ===
```

---

## 🧪 Manual Testing (Alternative)

### **Test 1: Create Pattern**

```powershell
curl -X POST http://localhost:8000/api/rosette-patterns `
  -H 'Content-Type: application/json' `
  -d '{
    "id": "test_pattern",
    "name": "Test Pattern",
    "center_x_mm": 0,
    "center_y_mm": 0,
    "ring_bands": [
      {
        "id": "ring0",
        "index": 0,
        "radius_mm": 40,
        "width_mm": 2,
        "strip_family_id": "ebony",
        "slice_angle_deg": 0,
        "color_hint": "#1a1a1a"
      }
    ],
    "default_slice_thickness_mm": 1.0,
    "default_passes": 1,
    "default_workholding": "vacuum",
    "default_tool_id": "saw_default"
  }'
```

### **Test 2: List Patterns**

```powershell
curl http://localhost:8000/api/rosette-patterns
```

### **Test 3: Generate Manufacturing Plan**

```powershell
curl -X POST http://localhost:8000/api/rosette/manufacturing-plan `
  -H 'Content-Type: application/json' `
  -d '{
    "pattern_id": "test_pattern",
    "guitars": 4,
    "tile_length_mm": 8.0,
    "scrap_factor": 0.12,
    "record_joblog": true
  }'
```

### **Test 4: Check JobLog**

```powershell
curl http://localhost:8000/api/joblog
```

---

## 📁 File Locations Checklist

Verify these files exist:

**Backend Schemas:**
- ✅ `services/api/app/schemas/job_log.py`
- ✅ `services/api/app/schemas/rosette_pattern.py`
- ✅ `services/api/app/schemas/manufacturing_plan.py`

**Backend Core:**
- ✅ `services/api/app/core/rosette_planner.py`

**Backend Routes:**
- ✅ `services/api/app/api/routes/joblog.py`
- ✅ `services/api/app/api/routes/rosette_patterns.py`
- ✅ `services/api/app/api/routes/manufacturing.py`

**Frontend Models:**
- ✅ `packages/client/src/models/rmos.ts`

**Frontend Stores:**
- ✅ `packages/client/src/stores/useRosettePatternStore.ts`
- ✅ `packages/client/src/stores/useManufacturingPlanStore.ts`
- ✅ `packages/client/src/stores/useJobLogStore.ts`

**Tests:**
- ✅ `scripts/Test-RMOS-Sandbox.ps1`

---

## 🐛 Troubleshooting

### **Issue: Import Error**

```
ModuleNotFoundError: No module named 'app.api.routes.joblog'
```

**Solution:** Verify file exists at correct path. Restart uvicorn:
```powershell
uvicorn app.main:app --reload --port 8000
```

### **Issue: 404 Not Found**

**Check:** Router prefixes in `main.py`. Should be `/api` not `/rmos`:
```python
app.include_router(joblog.router, prefix="/api")
```

### **Issue: Validation Error 422**

**Check:** Request body matches Pydantic schema exactly. Use `--verbose` in curl or check FastAPI docs at `http://localhost:8000/docs`

---

## 📊 API Reference

### **Rosette Patterns**

- `GET /api/rosette-patterns` - List all patterns
- `GET /api/rosette-patterns/{id}` - Get single pattern
- `POST /api/rosette-patterns` - Create pattern
- `PUT /api/rosette-patterns/{id}` - Update pattern
- `DELETE /api/rosette-patterns/{id}` - Delete pattern

### **Manufacturing Plans**

- `POST /api/rosette/manufacturing-plan` - Generate plan

### **JobLog**

- `GET /api/joblog` - List all jobs (newest first)
- `GET /api/joblog/{id}` - Get single job
- `POST /api/joblog` - Create job (explicit)

---

## ✅ Success Criteria

After integration, you should be able to:

- [x] Create rosette patterns via API
- [x] List patterns with multi-strip families
- [x] Generate manufacturing plans (tiles, strips, sticks per family)
- [x] View rosette_plan jobs in JobLog
- [x] Delete patterns
- [x] Run smoke test successfully

---

## 🎯 Next Steps

### **Option A: Add Vue Components**
Create frontend UI:
- RosetteTemplateLab.vue (pattern editor)
- RosetteMultiRingOpPanel.vue (batch preview)
- RosetteManufacturingPlanPanel.vue (plan viewer)
- JobLogMiniList.vue (job history)

### **Option B: Add Saw Batch Runner**
Implement Phase 2C:
- `services/api/app/pipelines/saw_nodes.py`
- `run_saw_slice_batch()` function
- Writes SawBatchJobLog entries
- `/saw-ops/batch/preview` endpoint

### **Option C: Database Migration**
Replace in-memory stores with SQLite:
- Create tables for patterns, plans, joblog
- Add SQLAlchemy models
- Update CRUD operations

---

**Status:** ✅ Ready for Integration Testing  
**Test Script:** `.\scripts\Test-RMOS-Sandbox.ps1`  
**Documentation:** See `projects/rmos/PHASE1_IMPLEMENTATION_COMPLETE.md`
