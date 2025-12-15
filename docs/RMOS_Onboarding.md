# RMOS Developer Onboarding Guide
**Project:** Luthier’s Tool Box — Rosette Manufacturing OS (RMOS)  
**Checkpoint Date:** 2025-11-22  
**Doc Version:** v0.3 (Sandbox-aligned)

---

## 1. What RMOS Is

RMOS is a self-contained manufacturing subsystem dedicated to rosette work. It provides:
- Rosette pattern design (rings, families, angles, tile overrides)
- Multi-ring saw slicing CAM (circle_param)
- Risk/DOC evaluation per slice or ring
- Manufacturing planning (tiles → strips → sticks)
- JobLog tracking for plans and saw batches
- Preview G-code and risk without side effects

RMOS is modular by design so ToolBox can consume it cleanly while RMOS evolves independently. :contentReference[oaicite:2]{index=2}

---

## 2. RMOS-Relevant Repo Structure

```
server/
app/
api/routes/
rosette_patterns.py # Pattern CRUD
manufacturing.py # Manufacturing plan endpoint
saw_ops.py # /slice/preview + /batch/preview
joblog.py # Unified JobLog store
core/
  rosette_planner.py       # Multi-family plan generator
  saw_gcode.py             # Saw G-code emitters
  saw_risk.py              # Risk model

schemas/
  rosette_pattern.py
  manufacturing_plan.py
  job_log.py
  saw_slice_op.py
  saw_slice_batch_op.py
client/
src/
models/rmos.ts
stores/
useRosettePatternStore.ts
useManufacturingPlanStore.ts
useJobLogStore.ts
components/rmos/
RosetteTemplateLab.vue
RosetteMultiRingOpPanel.vue
RosettePatternLibrary.vue
RosetteManufacturingPlanPanel.vue
JobLogMiniList.vue
views/
RosettePipelineView.vue
scripts/
rmos_ci_test.py
Test-RMOS-Full.ps1
Test-RMOS-Sandbox.ps1
Test-RMOS-SlicePreview.ps1
```

---

## 3. System Data Flow (Mental Model)

Pattern → Template Lab → Derived SawSliceBatchOp
↓
/rmos/saw-ops/batch/preview → Risk + G-code
↓
/rmos/rosette/manufacturing-plan → Multi-family Plan
↓
JobLog entries

Two loops matter:

### Loop A: Design → Preview → Adjust
- Edit rings/widths/families
- Derived batch op updates immediately
- Preview risk & G-code
- Tune parameters until safe + desired geometry

### Loop B: Plan → Validate → Produce
- Run manufacturing plan for N guitars
- Review per-ring tile demand + per-family strip/stick totals
- Record the plan to JobLog
- Use plan to drive real saw slicing jobs later

---

## 4. Backend API Surface (RMOS)

### 4.1 Patterns
GET /rmos/rosette/patterns
POST /rmos/rosette/patterns
PATCH /rmos/rosette/patterns/{id}
DELETE /rmos/rosette/patterns/{id}

### 4.2 Manufacturing Plan
POST /rmos/rosette/manufacturing-plan

**Request**
```json
{
  "pattern_id": "rosette_default",
  "guitars": 4,
  "tile_length_mm": 8.0,
  "scrap_factor": 0.12,
  "record_joblog": true
}
```
Response: ManufacturingPlan (multi-family)

### 4.3 Saw Ops Preview (no JobLog writes)
POST /rmos/saw-ops/slice/preview
POST /rmos/saw-ops/batch/preview

### 4.4 JobLog
GET  /rmos/joblog
POST /rmos/joblog
GET  /rmos/joblog/{id}

---

## 5. Developer Quickstart

### 5.1 Start Server
```
uvicorn app.main:app --reload
```

### 5.2 Start Client
```
npm install
npm run dev
```

### 5.3 Run Full RMOS CI (local)
```
python scripts/rmos_ci_test.py
```

### 5.4 Run Windows Smoke Suite
```
powershell -File scripts/Test-RMOS-Full.ps1 -Verbose
```

---

## 6. Extending RMOS Safely

**Add a new ring attribute**
1. Update backend schema: RosetteRingBand
2. Update TS model: models/rmos.ts
3. Add field to RosetteTemplateLab.vue
4. Confirm CI passes

**Add strip-family registry metadata (future)**
- Create a family registry schema + store
- Add palette UI in Template Lab
- Use registry defaults in planner (tile length, angle, scrap)

**Add exports**
- Add backend endpoint to export:
  - Manufacturing plan → PDF/JSON
  - Batch G-code → .gcode
- Add UI download buttons

**Add persistence**
Current stores are in-memory. Replace with DB-backed PatternStore + JobLog.

---

## 7. Testing Strategy

- **Unit tests**
  - rosette_planner.generate_manufacturing_plan
  - saw_risk.evaluate_saw_slice_risk
- **Integration tests**
  - saw_ops preview endpoints (circle + line)
  - Plan → JobLog write
- **CI**
  - scripts/rmos_ci_test.py always stays green

---

## 8. Common Pitfalls

**Wrong prefix**
If the UI sees 404:
- Check routers mounted under /rmos

**Schema drift**
If TemplateLab crashes:
- Ensure all ring fields exist:
  - index, radius_mm, width_mm,
  - strip_family_id, slice_angle_deg,
  - tile_length_override_mm, color_hint

**Preview endpoints writing logs**
Rule: previews are side-effect free.
Only real pipeline slicing writes JobLog.

---

## 9. What a new dev should read first
1. RosetteTemplateLab.vue — UI & derivation logic
2. rosette_planner.py — multi-family manufacturing math
3. saw_ops.py — preview/risk/gcode contract
4. rmos_ci_test.py — full E2E sequence

After these four files, a dev is productive.

---

## 10. Guiding Principle
RMOS is a factory subsystem, not a UI convenience. It must stand alone, plug in cleanly, and scale forward.
