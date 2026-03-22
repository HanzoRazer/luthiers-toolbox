# Production Shop — Implementation Backlog

Items here are fully analyzed and scoped. Each one has a source, a
specific file path, and enough context to implement without re-researching.
Nothing here was invented in a planning meeting — every item came from
reading actual code.

---


## TEST-001 — Fix pre-existing test failures

**Status:** ✅ RESOLVED (20→0 failures, 3,887 tests collected)
**Priority:** Medium
**Effort:** ~1 hour

### Root Causes Found and Fixed

**1. Missing `__init__.py`** (`app/dxf/__init__.py`)
- Module `app.dxf.preflight_service` was not importable
- 11 tests in `test_golden_dxf_preflight.py` failed with ImportError
- **Fix:** Created `app/dxf/__init__.py` with exports

**2. Logging `filename` key collision** (`app/cam/dxf_validation_gate.py`)
- Python's LogRecord reserves `filename` attribute
- Logging `extra={"filename": ...}` caused `KeyError: "Attempt to overwrite 'filename'"`
- **Fix:** Changed to `"dxf_filename": filename` in logger extra dicts (lines 171, 178, 198, 217)

**3. Wrong method call** (`app/routers/dxf_adaptive_consolidated_router.py`)
- Called `preflight.validate()` but method is `run_all_checks()`
- Accessed `report.ok` but attribute is `report.passed`
- **Fix:** Changed method name and attribute access

**4. Unhandled `DXFStructureError`** (`app/routers/dxf_adaptive_consolidated_router.py`)
- Invalid DXF content (`b"not a dxf file"`) raised unhandled exception
- **Fix:** Added `from ezdxf.lldxf.const import DXFStructureError` import
- Wrapped DXF validation in try/except, returns HTTP 422 with clear error

### Files Changed
- `services/api/app/dxf/__init__.py` (created)
- `services/api/app/cam/dxf_validation_gate.py`
- `services/api/app/routers/dxf_adaptive_consolidated_router.py`

---

## STUB-001 — Stub Endpoint Debt Audit

**Status:** ✅ RESOLVED (0 endpoint stubs remaining)
**Priority:** Low
**Effort:** Audit only

### Findings

The `PHASE_2_3_IMPLEMENTATION_PLAN.md` claimed 23 stubs across 3 files, but audit found:

1. **`cam/routers/stub_routes.py`** — FILE DELETED (was 4 stubs)
2. **`rmos/stub_routes.py`** — FILE DELETED (was 13 stubs)
3. **`routers/misc_stub_routes.py`** — CLEANED UP (was 6 stubs)
   - Now contains 1 real proxy endpoint (`/ai/advisories/request` → `rmos.ai_advisory.service`)
   - All stubs either wired to real implementations or removed

### Intentional Test Utilities (Keep)

- `rmos/engines/feasibility_stub.py` — Test/dev engine for deterministic results
  - Disabled in production (requires `ALLOW_STUB_ENGINE=true`)
  - Returns GREEN by default, supports `force_status` for test injection

**No action required** — stub debt is already resolved.

---

## WIRE-001 — Wire choose_batch_plan endpoint

**Status:** ✅ RESOLVED (6 tests pass)
**Priority:** Medium
**Effort:** ~1 hour

### What Was Implemented

Added `POST /api/saw/batch/plan/choose` endpoint to `batch_router.py`:
1. Accepts `BatchPlanChooseRequest` with `batch_plan_artifact_id`, `selected_setup_key`, `selected_op_ids`
2. Creates a `saw_batch_decision` artifact with selected operations
3. Optionally applies tuning multipliers when `apply_recommended_patch=True`
4. Returns `BatchPlanChooseResponse` with `batch_decision_artifact_id` and metadata

### Files Changed

- `services/api/app/saw_lab/batch_router.py` — added `choose_batch_plan` endpoint (~80 lines)
- `services/api/tests/test_plan_choose_persists_decision_payload_unit.py` — removed skip decorator

---

## WIRE-002 — Wire Relief/VCarve preview router

**Status:** ✅ RESOLVED (commit 4600b02f)
**Priority:** Low
**Effort:** ~1 hour
**Test:** `tests/test_relief_vcarve_endpoint_smoke.py`

### What Was Implemented

- `POST /api/preview` endpoint added to art_studio preview routes
- Accepts `{"svg": "<svg>...</svg>", "normalize": bool}`
- Parses SVG elements and returns stats with polyline count, bbox

---

## WIRE-003 — Fix workflow session router path mismatch

**Status:** ✅ RESOLVED (3 tests pass, 1 skipped for missing approve endpoint)
**Priority:** Medium
**Effort:** ~30 minutes
**Test:** `tests/test_rmos_workflow_e2e.py`

### What Was Fixed

- Changed router prefix from `/api/workflow/sessions` to `/api/rmos/workflow/sessions`
- Added test fixture to create `workflow_sessions` SQLite table
- Fixed test schema: `mode` → `workflow_type`, `state` → `current_step`
- Skipped `test_workflow_approve_requires_feasibility` (endpoint not yet exposed)

### Remaining Work

- `POST /api/rmos/workflow/approve` endpoint needs to be wired (state_machine.approve exists)

---

## BACKEND-001 — Curve-to-DXF endpoint

**Status:** Frontend TODO at `useCurveHistory.ts:46`
**Priority:** Medium
**Effort:** ~2 hours

### What's Needed

- Endpoint: `POST /api/export/curve-dxf` or similar
- Input: curve path data (points, control handles)
- Output: DXF file download

### Frontend Blocker

`packages/client/src/components/curvelab/composables/useCurveHistory.ts:46` has:
```typescript
function exportDXF() {
  // TODO: Implement DXF export via API
  alert("DXF export coming soon! Use Export JSON for now.");
}
```

---

## BACKEND-002 — Rosette PDF export service

**Status:** Frontend TODO at `useRosetteDesignerExport.ts:101`
**Priority:** Medium
**Effort:** ~half day

### What's Needed

- PDF generation service with rosette annotations
- Input: rosette design state (rings, materials, dimensions)
- Output: PDF with design rendering + BOM + measurements

### Frontend Blocker

`packages/client/src/components/toolbox/composables/useRosetteDesignerExport.ts:101` has:
```typescript
function exportDimensionSheet() {
  status.value = "📄 Dimension sheet export (coming soon)";
  // TODO: Generate PDF with annotations
}
```

---

## ACOUSTIC-001 — Saddle height inverse solver

**Status:** TODO
**Priority:** High
**Effort:** ~2 hours
**File:** `services/api/app/instrument_geometry/neck/neck_angle.py`

### Problem

`saddle_height_required_mm` uses an approximation. The correct formula is:
```
H_saddle = L_body × tan(θ_target) + H_fretboard − H_bridge
```
where θ_target comes from action at the 12th fret via:
```
θ_target = arcsin(action_at_12th / L_nut_to_12th)
```

### Implementation

1. Fix `saddle_height_required_mm` to use the exact geometry
2. Add inverse function `solve_for_target_action(target_action_12th_mm, bridge_height_mm, ...)` that returns `{neck_angle_deg, saddle_height_mm, relief_contribution_mm}`
3. Add 4 unit tests covering edge cases

---

## ACOUSTIC-005 — Wire acoustic chain into build_sequence

**Status:** TODO (depends on ACOUSTIC-001 through 004)
**Priority:** Low
**Effort:** ~2 hours
**File:** `services/api/app/workflow/build_sequence.py`

### What's Needed

Add acoustic analysis step to the build sequence workflow:
1. After body dimensions finalized: run top_deflection_calc
2. After bracing designed: validate combined stiffness
3. After neck angle set: verify saddle height is manufacturable (> 3mm, < 12mm)

Return warnings if any acoustic constraint is violated.

---

## Notes on how this backlog works

Each item here was identified by reading code, not by speculation.
Every "file to create" path is deliberate — it fits the existing module structure.
Every "what exists" section cites real function names from the actual codebase.

When an item is implemented: delete it from here and add it to `CHANGELOG.md`.
When a new gap is found during implementation: add it here before closing the session.
Do not let findings live only in conversation history.





