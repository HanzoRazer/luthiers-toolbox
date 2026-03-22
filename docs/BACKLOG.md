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

**Status:** ✅ RESOLVED (ACOUSTIC-001–005 chain completed 2026-03-21)
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

### Resolution

Delivered with ACOUSTIC-002–005 as the acoustic chain (2026-03-21). See sprint board session log.

---

## CALC-001 — side_bending_calc physics version migration

**Status:** ✅ RESOLVED (physics version merged 2026-03-21; follow-up: coverage on large module)
**Priority:** Low
**Effort:** ~2 hours
**Source:** Uploaded file `files - 2026-03-21T123917.995/side_bending_calc.py`

### Problem (historical)

The physics-based `side_bending_calc.py` had breaking changes vs legacy (temperatures, species keys, note text). Migration completed in-repo.

### Remaining (non-blocking)

- Add smoke/unit coverage for the upgraded module (still among the largest uncovered files).

---

## DECOMP-001 — instrument_geometry_router decomposition

**Status:** TODO (separate sprint)
**Priority:** Medium
**Effort:** ~1 day
**Source:** Uploaded file 
### Problem

The uploaded \ (1,915 lines) consolidates geometry endpoints
but should NOT be merged as-is. It imports from 13 calculators, several of which also
need attention:

| Calculator | Lines | Status |
|------------|-------|--------|
| soundhole_calc.py | 2,544 | 🔴 MEGA — split first |
| side_bending_calc.py | 1,058 | ⚠️ Over threshold |
| build_sequence.py | 1,053 | ⚠️ Over threshold |
| electronics_layout_calc.py | 543 | ⚠️ Slightly over |
| fret_wire_calc.py | 417 | ✓ OK |
| voicing_history_calc.py | 385 | ✓ OK |
| fret_leveling_calc.py | 316 | ✓ OK |
| wood_movement_calc.py | 306 | ✓ OK |
| nut_compensation_calc.py | 294 | ✓ OK |
| bridge_calc.py | 284 | ✓ OK |
| nut_comp_calc.py | 272 | ✓ OK |
| setup_cascade.py | 268 | ✓ OK |
| nut_slot_calc.py | 260 | ✓ OK |
| neck_block_calc.py | 228 | ✓ OK |

### Implementation Plan

1. **Phase 1:** Split \ (2,544 → ~3 modules)
2. **Phase 2:** Split \ (1,058 → physics + handlers)
3. **Phase 3:** Split \ (1,053 → stages as separate modules)
4. **Phase 4:** Decompose router into ~5 domain routers:
   - \ (side bending, wood movement)
   - \ (soundhole calc)
   - \ (fret leveling, fret wire, nut slots, nut comp)
   - \ (build sequence, voicing, setup cascade)
   - \ (electronics layout)

**Do NOT merge the 1,915-line file directly.** Split first.

---

## DECOMP-002 — Split soundhole_calc.py (2,544 lines)

**Status:** TODO
**Priority:** Medium
**Effort:** ~3 hours
**File:** 
### Problem

At 2,544 lines with 11 classes and 24 functions, this module handles too many
concerns: Helmholtz physics, two-cavity resonators, side ports, stiffness,
climate factors, presets, and spec builders.

### 7 Natural Modules Identified

| Module | ~Lines | Contains |
|--------|--------|----------|
| \ | ~600 | Helmholtz math, \, \, constants |
| \ | ~400 | Coupled resonator: \, \, \ |
| \ | ~290 | \, \, \, \ |
| \ | ~200 | \, \, \ |
| \ | ~200 | Data layer: \, \, \, species data |
| \ | ~120 | \, \ |
| \ | ~400 | Facade: \, \, re-exports |

### Split Order

1. \ — Pure math, zero dependencies
2. \ — Depends on physics
3. \ — Depends on physics
4. \ — Depends on physics
5. \ — Standalone data
6. \ — Standalone data
7. \ — Facade with re-exports


---

## Notes on how this backlog works

Each item here was identified by reading code, not by speculation.
Every "file to create" path is deliberate — it fits the existing module structure.
Every "what exists" section cites real function names from the actual codebase.

When an item is implemented: delete it from here and add it to `CHANGELOG.md`.
When a new gap is found during implementation: add it here before closing the session.
Do not let findings live only in conversation history.





