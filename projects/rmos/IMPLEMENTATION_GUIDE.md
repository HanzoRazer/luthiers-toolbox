# 📋 RTL Implementation Guide

**Version:** 0.1.0-alpha  
**Last Updated:** November 20, 2025  
**Purpose:** Step-by-step deployment of all 15 patches

---

## 🎯 Overview

This guide walks you through implementing RTL from scratch using **15 cumulative patch bundles** (A through O).

### **Key Principles**

1. **Sequential Application:** Patches must be applied in order (A → B → C → ...)
2. **Test After Each:** Run smoke tests after every patch
3. **Incremental Value:** Each patch adds working functionality
4. **No Skipping:** Don't skip patches (dependencies break)

### **Timeline Estimates**

| Phase | Patches | Duration | Deliverable |
|-------|---------|----------|-------------|
| v0.1 MVP | A-D | 4-6 weeks | Basic patterns + single-ring saw + JobLog |
| v0.2 Multi-Family | E-J | 2-3 weeks | Pattern library + multi-family planner |
| v0.3 Production | K-O | 3-4 weeks | Complete manufacturing + persistence |
| Total | A-O | ~10-13 weeks | Full RMOS system |

---

## 📦 Prerequisites

### **Environment Setup**

```powershell
# Backend
cd services/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Frontend
cd packages/client
npm install

# Verify main ToolBox works
cd ../..
docker compose up --build  # Or use local dev servers
```

### **Dependencies**

**Backend (requirements.txt):**
```txt
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.4.0
sqlalchemy>=2.0.0        # For v0.3 persistence
sqlite3                   # For v0.3 persistence
pytest>=7.4.0
```

**Frontend (package.json):**
```json
{
  "dependencies": {
    "vue": "^3.3.4",
    "pinia": "^2.1.7",
    "vue-router": "^4.2.5"
  }
}
```

---

## 🔧 Patch Deployment Guide

### **General Pattern for Each Patch**

1. **Read Patch Doc:** `patches/PATCH_X_NAME.md`
2. **Apply Backend Files:** Copy from `code_bundles/backend/`
3. **Apply Frontend Files:** Copy from `code_bundles/frontend/`
4. **Run Tests:** `.\tests\test_X.ps1`
5. **Verify Manually:** Open UI and test feature
6. **Commit:** `git commit -m "Apply Patch X: Description"`

---

## Patch A: Core Infrastructure

**File:** [patches/PATCH_A_CORE.md](./patches/PATCH_A_CORE.md)

### **What It Does**
- Adds `RosettePattern` and `RosetteRingBand` schemas
- Creates `/rosette-patterns` CRUD router
- Registers router in `main.py`

### **Files Changed**

**Backend:**
```
services/api/app/schemas/rosette_pattern.py          (new)
services/api/app/routers/rosette_patterns.py         (new)
services/api/app/main.py                             (modified)
```

**Frontend:** None (backend only)

### **Implementation Steps**

1. **Create Schema:**
```powershell
cd services/api/app/schemas
# Copy rosette_pattern.py from code_bundles/backend/schemas/
```

2. **Create Router:**
```powershell
cd ../routers
# Copy rosette_patterns.py from code_bundles/backend/routers/
```

3. **Register Router:**
```python
# app/main.py
from .routers.rosette_patterns import router as rosette_patterns_router
app.include_router(rosette_patterns_router, prefix="/rosette-patterns", tags=["RMOS"])
```

4. **Test:**
```powershell
cd ../../../..
uvicorn app.main:app --reload --port 8000

# In another terminal:
cd projects/rmos/tests
.\test_core.ps1  # Should show CRUD operations working
```

### **Expected Output**
```
✓ POST /rosette-patterns: Created pattern (201)
✓ GET /rosette-patterns: Retrieved 1 pattern
✓ GET /rosette-patterns/{id}: Retrieved specific pattern
✓ PUT /rosette-patterns/{id}: Updated pattern name
✓ DELETE /rosette-patterns/{id}: Deleted pattern
```

### **Duration:** 1-2 hours

---

## Patch B: JobLog Integration

**File:** [patches/PATCH_B_JOBLOG.md](./patches/PATCH_B_JOBLOG.md)

### **What It Does**
- Extends `JobLogEntry` schema with RMOS fields
- Adds `job_type` field (`saw_slice_batch` vs `rosette_plan`)
- Creates rosette-specific JobLog writer

### **Files Changed**

**Backend:**
```
services/api/app/schemas/job_log.py                  (modified)
services/api/app/routers/joblog.py                   (modified)
```

**Frontend:** None (backend only)

### **Implementation Steps**

1. **Extend JobLogEntry Schema:**
```python
# app/schemas/job_log.py
class JobLogEntry(BaseModel):
    job_id: str
    job_type: str  # "saw_slice_batch" or "rosette_plan"
    
    # ... existing fields
    
    # RMOS fields (new)
    plan_pattern_id: Optional[str] = None
    plan_guitars: Optional[int] = None
    plan_total_tiles: Optional[int] = None
    strip_plans: Optional[List[dict]] = None
```

2. **Add JobLog Writer:**
```python
# app/routers/joblog.py
@router.post("/joblog")
async def create_job(body: JobLogEntry):
    # Validation
    if body.job_type not in ["saw_slice_batch", "rosette_plan"]:
        raise HTTPException(400, "Invalid job_type")
    
    # Store
    jobs_db.append(body)
    return {"job_id": body.job_id}
```

3. **Test:**
```powershell
.\test_joblog.ps1
```

### **Expected Output**
```
✓ POST /joblog: Created saw_slice_batch job (201)
✓ POST /joblog: Created rosette_plan job (201)
✓ GET /joblog?job_type=rosette_plan: Filtered correctly
✓ Schema validation: Rejected invalid job_type
```

### **Duration:** 1 hour

---

## Patch C: Multi-Ring Saw Support

**File:** [patches/PATCH_C_MULTIRING.md](./patches/PATCH_C_MULTIRING.md)

### **What It Does**
- Adds `SawSliceBatchOpCircle` schema
- Implements circle geometry G-code generator
- Adds risk analysis for multi-ring operations

### **Files Changed**

**Backend:**
```
services/api/app/schemas/saw_slice_batch_op.py       (new)
services/api/app/core/saw_gcode.py                   (new)
services/api/app/core/saw_risk.py                    (new)
services/api/app/routers/saw_ops.py                  (new)
services/api/app/main.py                             (modified)
```

**Frontend:** None (backend only)

### **Implementation Steps**

1. **Create Schemas:**
```powershell
cd services/api/app/schemas
# Copy saw_slice_batch_op.py from code_bundles
```

2. **Implement G-Code Generator:**
```python
# app/core/saw_gcode.py
def generate_circle_gcode(op: SawSliceBatchOpCircle) -> str:
    gcode = ["G21", "G90", "G17"]  # mm, absolute, XY plane
    
    for ring_idx in range(op.num_rings):
        radius = op.base_radius_mm + (ring_idx * op.radial_step_mm)
        
        # Position at start
        gcode.append(f"G0 X{radius:.4f} Y0.0000")
        
        # Plunge
        gcode.append(f"G1 Z{-op.slice_thickness_mm:.4f} F300")
        
        # Full circle (CW arc)
        gcode.append(f"G2 X{radius:.4f} Y0.0000 I{-radius:.4f} J0.0000 F1200")
        
        # Retract
        gcode.append("G0 Z5.0000")
    
    gcode.append("M30")
    return "\n".join(gcode)
```

3. **Implement Risk Analysis:**
```python
# app/core/saw_risk.py
def analyze_circle_risk(op: SawSliceBatchOpCircle) -> dict:
    outer_radius = op.base_radius_mm + ((op.num_rings - 1) * op.radial_step_mm)
    
    # Check rim speed
    rim_speed_grade = check_rim_speed(outer_radius, 10000, 50)
    
    # Check gantry span
    span_grade = check_gantry_span(outer_radius, 300)
    
    # Overall risk
    if "RED" in [rim_speed_grade, span_grade]:
        overall = "RED"
    elif "YELLOW" in [rim_speed_grade, span_grade]:
        overall = "YELLOW"
    else:
        overall = "GREEN"
    
    return {
        "grade": overall,
        "rim_speed_grade": rim_speed_grade,
        "gantry_span_grade": span_grade
    }
```

4. **Create Router:**
```python
# app/routers/saw_ops.py
@router.post("/saw-ops/slice/execute")
async def execute_saw_slice(body: SawSliceBatchOpCircle):
    # Generate G-code
    gcode = generate_circle_gcode(body)
    
    # Analyze risk
    risk = analyze_circle_risk(body)
    
    # Write to JobLog
    job_entry = JobLogEntry(
        job_id=f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        job_type="saw_slice_batch",
        op_data=body.dict(),
        tool_id=body.tool_id,
        material=body.material,
        num_slices=body.num_rings,
        risk_summary=risk,
        created_at=datetime.now().isoformat()
    )
    
    # Execute (mock for now)
    return {"job_id": job_entry.job_id, "gcode": gcode, "risk": risk}
```

5. **Test:**
```powershell
.\test_multiring_saw.ps1
```

### **Expected Output**
```
✓ POST /saw-ops/slice/execute: Generated G-code for 5 rings
✓ G-code contains: G21, G90, G17, G2 (arcs)
✓ Risk analysis: grade=YELLOW (rim speed caution)
✓ JobLog entry created
```

### **Duration:** 2-3 hours

---

## Patch D: Preview Endpoints

**File:** [patches/PATCH_D_PREVIEW.md](./patches/PATCH_D_PREVIEW.md)

### **What It Does**
- Adds `/saw-ops/slice/preview` endpoint (G-code + risk, no execution)
- Adds `/rosette-patterns/{id}/preview` endpoint (pattern visualization data)

### **Files Changed**

**Backend:**
```
services/api/app/routers/saw_ops.py                  (modified)
services/api/app/routers/rosette_patterns.py         (modified)
```

**Frontend:** None (backend only)

### **Implementation Steps**

1. **Add Saw Preview:**
```python
# app/routers/saw_ops.py
@router.post("/saw-ops/slice/preview")
async def preview_saw_slice(body: SawSliceBatchOpCircle):
    gcode = generate_circle_gcode(body)
    risk = analyze_circle_risk(body)
    
    return {
        "gcode": gcode,
        "risk": risk,
        "stats": {
            "num_rings": body.num_rings,
            "total_length_m": sum(2 * math.pi * (body.base_radius_mm + i * body.radial_step_mm) for i in range(body.num_rings)) / 1000
        }
    }
```

2. **Add Pattern Preview:**
```python
# app/routers/rosette_patterns.py
@router.get("/rosette-patterns/{pattern_id}/preview")
async def preview_pattern(pattern_id: str):
    pattern = patterns_db.get(pattern_id)
    if not pattern:
        raise HTTPException(404)
    
    # Generate ring radii for visualization
    radii = []
    for ring in pattern.ring_bands:
        radius = 20 + (ring.index * 2.5)  # Default spacing
        radii.append({
            "index": ring.index,
            "radius": radius,
            "color": ring.color_hint,
            "family": ring.strip_family_id
        })
    
    return {"pattern": pattern, "radii": radii}
```

3. **Test:**
```powershell
.\test_preview.ps1
```

### **Expected Output**
```
✓ POST /saw-ops/slice/preview: Preview returned G-code (200)
✓ Preview includes risk analysis
✓ GET /rosette-patterns/{id}/preview: Visualization data (200)
```

### **Duration:** 1 hour

---

## 🎨 Frontend Patches (E-J)

### **Patch E: Multi-Ring OpPanel**

**File:** [patches/PATCH_E_OPPANEL.md](./patches/PATCH_E_OPPANEL.md)

**What It Does:** Vue component for multi-ring saw operations in PipelineLab

**Files Changed:**
```
packages/client/src/components/RosetteMultiRingOpPanel.vue (new)
packages/client/src/stores/pipelineStore.ts                (modified)
```

**Duration:** 2-3 hours

---

### **Patch F: JobLog Mini-Viewer**

**File:** [patches/PATCH_F_JOBLOG_UI.md](./patches/PATCH_F_JOBLOG_UI.md)

**What It Does:** Enhanced JobLog viewer with RMOS job type filtering

**Files Changed:**
```
packages/client/src/components/JobLogMiniList.vue          (modified)
```

**Duration:** 1-2 hours

---

### **Patch G: Rosette Manufacturing OS**

**File:** [patches/PATCH_G_TEMPLATE.md](./patches/PATCH_G_TEMPLATE.md)

**What It Does:** Visual pattern editor with ring band management

**Files Changed:**
```
packages/client/src/views/RosetteTemplateLab.vue          (new)
packages/client/src/components/RingBandEditor.vue         (new)
packages/client/src/components/PatternPreview.vue         (new)
```

**Duration:** 4-5 hours

---

### **Patch H: Pattern → CAM Mapper**

**File:** [patches/PATCH_H_MAPPER.md](./patches/PATCH_H_MAPPER.md)

**What It Does:** Utility to convert RosettePattern → SawSliceBatchOpCircle

**Files Changed:**
```
packages/client/src/utils/pattern_to_batch.ts             (new)
```

**Duration:** 1 hour

---

### **Patch I: Pattern Library Backend**

**File:** [patches/PATCH_I_LIBRARY_BE.md](./patches/PATCH_I_LIBRARY_BE.md)

**What It Does:** Persistence for pattern library (save/load/search)

**Files Changed:**
```
services/api/app/routers/rosette_patterns.py              (modified)
services/api/app/core/pattern_library.py                  (new)
```

**Duration:** 2 hours

---

### **Patch J: Pattern Library Frontend**

**File:** [patches/PATCH_J_LIBRARY_FE.md](./patches/PATCH_J_LIBRARY_FE.md)

**What It Does:** UI for browsing/searching saved patterns

**Files Changed:**
```
packages/client/src/views/PatternLibrary.vue              (new)
packages/client/src/stores/rosettePatternStore.ts         (new)
```

**Duration:** 3-4 hours

---

## 📊 Manufacturing Patches (K-O)

### **Patch K: Single-Family Planner**

**File:** [patches/PATCH_K_PLANNER_1.md](./patches/PATCH_K_PLANNER_1.md)

**What It Does:** Calculate material requirements for single strip family

**Files Changed:**
```
services/api/app/core/planner.py                          (new)
services/api/app/routers/manufacturing_plans.py           (new)
```

**Duration:** 2-3 hours

---

### **Patch L: Multi-Family Planner**

**File:** [patches/PATCH_L_PLANNER_MULTI.md](./patches/PATCH_L_PLANNER_MULTI.md)

**What It Does:** Extend planner to handle multiple strip families

**Files Changed:**
```
services/api/app/core/planner.py                          (modified)
```

**Duration:** 2 hours

---

### **Patch M: Planner → JobLog**

**File:** [patches/PATCH_M_PLAN_JOBLOG.md](./patches/PATCH_M_PLAN_JOBLOG.md)

**What It Does:** Write manufacturing plans to JobLog as `rosette_plan` jobs

**Files Changed:**
```
services/api/app/routers/manufacturing_plans.py           (modified)
```

**Duration:** 1 hour

---

### **Patch N: Manufacturing Plan Panel UI**

**File:** [patches/PATCH_N_PLAN_UI.md](./patches/PATCH_N_PLAN_UI.md)

**What It Does:** Vue component for reviewing manufacturing plans

**Files Changed:**
```
packages/client/src/views/ManufacturingPlanPanel.vue      (new)
packages/client/src/components/StripPlanTable.vue         (new)
```

**Duration:** 3-4 hours

---

### **Patch O: End-to-End Sync**

**File:** [patches/PATCH_O_SYNC.md](./patches/PATCH_O_SYNC.md)

**What It Does:** Bidirectional sync between PipelineLab and RMOS

**Files Changed:**
```
packages/client/src/stores/pipelineStore.ts               (modified)
packages/client/src/stores/rosettePatternStore.ts         (modified)
```

**Duration:** 2-3 hours

---

## 🧪 Testing Strategy

### **Test Script Pattern**

Each patch has a corresponding PowerShell test:
```
projects/rmos/tests/
├── test_core.ps1              # Patch A
├── test_joblog.ps1            # Patch B
├── test_multiring_saw.ps1     # Patch C
├── test_preview.ps1           # Patch D
├── test_pattern_mapper.ps1    # Patch H
├── test_planner.ps1           # Patches K-L
└── test_integration.ps1       # Full system (Patch O)
```

### **Running Tests**

**After Each Patch:**
```powershell
cd projects/rmos/tests
.\test_<patch_name>.ps1
```

**All Tests:**
```powershell
Get-ChildItem .\test_*.ps1 | ForEach-Object { & $_ }
```

### **Expected Test Coverage**

- ✅ All CRUD operations
- ✅ Schema validation (reject invalid data)
- ✅ G-code generation (check for G21, G90, G2)
- ✅ Risk analysis (verify grade calculation)
- ✅ JobLog writes (confirm job_type filtering)
- ✅ Pattern → CAM mapping (roundtrip conversion)

---

## 🐛 Troubleshooting

### **Issue: Import Error `rosette_pattern` Module Not Found**

**Solution:**
```powershell
# Restart uvicorn after adding new modules
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

---

### **Issue: JobLog Schema Validation Fails**

**Symptom:** `422 Unprocessable Entity` on POST /joblog

**Solution:** Check `job_type` field matches enum:
```python
if body.job_type not in ["saw_slice_batch", "rosette_plan"]:
    raise HTTPException(400, "Invalid job_type")
```

---

### **Issue: Frontend Components Not Rendering**

**Solution:** Verify router registration:
```typescript
// router/index.ts
{
  path: '/rosette-template',
  name: 'RosetteTemplateLab',
  component: () => import('@/views/RosetteTemplateLab.vue')
}
```

---

### **Issue: G-Code Missing G21 Command**

**Solution:** Always prepend units command:
```python
gcode = ["G21", "G90", "G17"]  # mm, absolute, XY plane
```

---

## 📋 Checklist: v0.1 MVP Complete

After Patches A-D, verify:

- [ ] POST /rosette-patterns creates pattern
- [ ] GET /rosette-patterns lists patterns
- [ ] POST /joblog accepts `saw_slice_batch` jobs
- [ ] POST /joblog accepts `rosette_plan` jobs
- [ ] POST /saw-ops/slice/execute generates G-code
- [ ] POST /saw-ops/slice/preview returns risk analysis
- [ ] GET /rosette-patterns/{id}/preview returns visualization data
- [ ] All tests pass: `.\test_core.ps1`, `.\test_joblog.ps1`, `.\test_multiring_saw.ps1`, `.\test_preview.ps1`

---

## 📋 Checklist: v0.2 Multi-Family Complete

After Patches E-J, verify:

- [ ] RosetteMultiRingOpPanel renders in PipelineLab
- [ ] JobLogMiniList filters by job_type
- [ ] RosetteTemplateLab creates/edits patterns
- [ ] Pattern → CAM mapper converts patterns to saw ops
- [ ] Pattern Library backend stores patterns
- [ ] Pattern Library frontend displays saved patterns

---

## 📋 Checklist: v0.3 Production Complete

After Patches K-O, verify:

- [ ] Manufacturing planner calculates strip requirements
- [ ] Planner handles multiple strip families
- [ ] Manufacturing plans saved to JobLog
- [ ] ManufacturingPlanPanel displays plans
- [ ] PipelineLab ↔ RMOS bidirectional sync works
- [ ] Full integration test passes: `.\test_integration.ps1`

---

## 🚀 Deployment to Production

### **Staging Environment**

1. **Apply All Patches** (A-O)
2. **Run Full Test Suite**
3. **Manual QA:** Create pattern → Generate plan → Execute saw op → View JobLog
4. **Performance Test:** 100+ patterns, 1000+ jobs

### **Production Rollout**

1. **Database Migration:** Add RMOS tables to SQLite
2. **Backup Existing Jobs:** Export current JobLog
3. **Deploy Backend:** Update FastAPI service
4. **Deploy Frontend:** Build Vue app (`npm run build`)
5. **Smoke Test:** Run `.\test_integration.ps1` against production
6. **Monitor:** Watch error logs for 24 hours

---

## 📚 Additional Resources

- **ARCHITECTURE.md** - Deep technical dive
- **API_REFERENCE.md** - Complete endpoint docs
- **TECHNICAL_AUDIT.md** - Known issues
- **ROADMAP.md** - Future phases (v0.4-v1.0)
- **Main Handoff** - `../../CAM_CAD_DEVELOPER_HANDOFF.md` Appendix E

---

## 💡 Tips for Success

1. **Don't Skip Patches:** Dependencies break if you skip
2. **Test Incrementally:** Catch issues early
3. **Read Patch Docs First:** Understand before applying
4. **Commit Often:** Small commits per patch
5. **Ask Questions:** Use TECHNICAL_AUDIT.md for known issues

---

**Status:** ✅ Guide Complete  
**Next:** Apply Patch A (Core Infrastructure)  
**Timeline:** 10-13 weeks for full RMOS (Patches A-O)
