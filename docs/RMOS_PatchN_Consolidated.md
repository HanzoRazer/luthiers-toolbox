# Rosette OS — Patch N Consolidation
**Project:** Luthier’s Tool Box — RMOS  
**Compiled:** 2025-11-22  
**Covers:** Phase 1 → Phase 3 + CI Pack

---

## N0 — Foundations (Schemas + JobLog split)

### Schemas added/updated
- `RosetteRingBand`
- `RosettePatternBase / RosettePatternInDB`
- `ManufacturingPlan` (multi-family)
- `RingRequirement`
- `StripFamilyPlan`
- `SawSliceOp`
- `SawSliceBatchOp`

### JobLog split
- `RosettePlanJobLog`
- `SawBatchJobLog`
- `JobLogEntry` union to support multiple job types

---

## N1 — Core RMOS Backend Logic

### `core/rosette_planner.py`
- multi-strip-family grouping
- per-ring circumference + tile counts
- per-family strip length + sticks needed
- scrap factor support
- per-ring tile length overrides

### `api/routes/manufacturing.py`
- `POST /rosette/manufacturing-plan`
- writes a `rosette_plan` JobLog entry
- returns full `ManufacturingPlan` payload

### Pipeline saw node integration
- batch saw slicing evaluates risk per ring
- emits G-code blocks
- writes `saw_slice_batch` JobLog entries

---

## N2 — Saw Preview Endpoints (API glue)

### `api/routes/saw_ops.py`
- `POST /saw-ops/slice/preview`
  - line_param or circle_param
- `POST /saw-ops/batch/preview`
  - circle_param multi-ring preview
- **No JobLog side effects**
- Contract matches Vue Op Panel exactly

---

## N3 — Frontend TypeScript Models

### `client/src/models/rmos.ts`
- Rosette patterns + rings
- manufacturing plan response types
- saw op and batch op types
- JobLog union types (plans + batches)
- risk summary types

---

## N4 — Pinia Stores

### `useRosettePatternStore.ts`
- fetch/create/update/delete patterns
- selectedPattern tracking
- optimistic local updates

### `useManufacturingPlanStore.ts`
- requests /manufacturing-plan
- stores currentPlan
- exposes loading/error

### `useJobLogStore.ts`
- fetches unified JobLog
- provides entries, refresh, filters

---

## N5 — Phase 3 Vue UI Components (Drop-in)

### Components completed
- `RosetteTemplateLab.vue`
  - editable ring table + pattern metadata
  - derived batch op emitter
- `RosetteMultiRingOpPanel.vue`
  - `/saw-ops/batch/preview` risk + G-code preview
- `RosettePatternLibrary.vue`
  - pattern CRUD + selection
- `RosetteManufacturingPlanPanel.vue`
  - multi-family plan viewer
- `JobLogMiniList.vue`
  - compact logs for plan + batch types
- `RosettePipelineView.vue`
  - full RMOS 3-panel integrated view

These match the Phase 3 spec. :contentReference[oaicite:4]{index=4}

---

## N6 — CI & Tooling Pack

### Python CI runner
- `scripts/rmos_ci_test.py`
- boots uvicorn
- creates pattern
- runs manufacturing plan
- runs slice preview + batch preview
- asserts JobLog presence

### PowerShell smoke tests
- `Test-RMOS-Sandbox.ps1`
- `Test-RMOS-SlicePreview.ps1`
- `Test-RMOS-Full.ps1`

### GitHub Actions
- `.github/workflows/rmos_ci.yml`
- runs python CI on push/PR

---

## N7 — Stability Guarantees (current state)

- Backend ↔ TS schema parity maintained
- Previews are side-effect free
- Planner is multi-family aware
- CI covers full RMOS flow end-to-end
- TemplateLab → BatchOp derivation is reactive and stable

---

## N8 — Reserved Future Slots

- N8.1 Strip Family Registry + Palette UI
- N8.2 DXF-guided slicing ops
- N8.3 Export manufacturing plan (PDF/JSON)
- N8.4 Jig template exports
- N8.5 Full CAM pipeline integration
- N8.6 Persistent DB stores

---

✅ How to Apply
1. Create folder:
2. `docs/`
3. Drop in both files above.
4. Commit:
```
git add docs/RMOS_Onboarding.md docs/RMOS_PatchN_Consolidated.md
git commit -m "Add RMOS onboarding + Patch-N consolidation docs"
git push
```
