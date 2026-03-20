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

**Status:** ⏳ PENDING
**Priority:** Medium
**Effort:** ~2 hours
**Test:** `tests/test_plan_choose_persists_decision_payload_unit.py`

### What's Missing

The test expects a `choose_batch_plan` function in `app/saw_lab/batch_router.py` that:
1. Accepts `BatchPlanChooseRequest` with `batch_plan_artifact_id`, `selected_setup_key`, `selected_op_ids`
2. Creates a `saw_batch_decision` artifact
3. Optionally applies tuning multipliers when `apply_recommended_patch=True`
4. Returns `batch_decision_artifact_id` and metadata

### Files to Modify

- `services/api/app/saw_lab/batch_router.py` — add `choose_batch_plan` endpoint
- `services/api/app/saw_lab/schemas_batch.py` — add `BatchPlanChooseRequest`, `BatchPlanChooseResponse`

---

## WIRE-002 — Wire Relief/VCarve preview router

**Status:** ⏳ PENDING
**Priority:** Low
**Effort:** ~1 hour
**Test:** `tests/test_relief_vcarve_endpoint_smoke.py`

### What's Missing

The test expects `POST /api/preview` endpoint that:
1. Accepts `{"svg": "<svg>...</svg>", "normalize": bool}`
2. Parses SVG elements (rect, circle, path, polygon, etc.)
3. Returns `{"stats": {...}, "normalized": bool}` with polyline count, bbox

### Files to Modify

- `services/api/app/art_studio/relief_router.py` or `vcarve_router.py` — implement preview endpoint
- Wire router in `app/main.py` or router registry

---

## WIRE-003 — Fix workflow session router path mismatch

**Status:** ⏳ PENDING
**Priority:** Medium
**Effort:** ~30 minutes
**Test:** `tests/test_rmos_workflow_e2e.py`

### What's Wrong

The test expects endpoints at `/api/rmos/workflow/sessions` but the router is mounted at `/api/workflow/sessions`.

**Actual router prefix:** `routes.py:30` → `prefix="/api/workflow/sessions"`
**Test expects:** `/api/rmos/workflow/sessions`

### Options

1. **Change router prefix** to `/api/rmos/workflow/sessions` (breaking change)
2. **Change test paths** to `/api/workflow/sessions` (if that's the intended API)
3. **Add alias route** that forwards to the existing router

### Files to Modify

- `services/api/app/workflow/sessions/routes.py` — change prefix, OR
- `services/api/tests/test_rmos_workflow_e2e.py` — update test paths

---

## Notes on how this backlog works

Each item here was identified by reading code, not by speculation.
Every "file to create" path is deliberate — it fits the existing module structure.
Every "what exists" section cites real function names from the actual codebase.

When an item is implemented: delete it from here and add it to `CHANGELOG.md`.
When a new gap is found during implementation: add it here before closing the session.
Do not let findings live only in conversation history.





