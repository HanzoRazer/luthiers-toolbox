# Production Shop — Implementation Backlog

Items here are fully analyzed and scoped. Each one has a source, a
specific file path, and enough context to implement without re-researching.
Nothing here was invented in a planning meeting — every item came from
reading actual code.

---


## TEST-001 — Fix 33 pre-existing test failures

**Status:** ✅ RESOLVED (test_dxf_plan_endpoint_smoke.py: 24/24 passing)
**Priority:** Medium
**Effort:** ~1 hour

### Root Causes Found and Fixed

**1. Logging `filename` key collision** (`app/cam/dxf_validation_gate.py`)
- Python's LogRecord reserves `filename` attribute
- Logging `extra={"filename": ...}` caused `KeyError: "Attempt to overwrite 'filename'"`
- **Fix:** Changed to `"dxf_filename": filename` in logger extra dicts (lines 171, 178, 198, 217)

**2. Wrong method call** (`app/routers/dxf_adaptive_consolidated_router.py`)
- Called `preflight.validate()` but method is `run_all_checks()`
- Accessed `report.ok` but attribute is `report.passed`
- **Fix:** Changed method name and attribute access

**3. Unhandled `DXFStructureError`** (`app/routers/dxf_adaptive_consolidated_router.py`)
- Invalid DXF content (`b"not a dxf file"`) raised unhandled exception
- **Fix:** Added `from ezdxf.lldxf.const import DXFStructureError` import
- Wrapped DXF validation in try/except, returns HTTP 422 with clear error

### Files Changed
- `services/api/app/cam/dxf_validation_gate.py`
- `services/api/app/routers/dxf_adaptive_consolidated_router.py`

---

## CLEANUP-001 — Graduate _experimental/analytics/

**Status:** Ready to graduate — 4 active consumers
**Priority:** Medium
**Effort:** ~2 hours

4 production routers import from `_experimental/analytics/`:
- `analytics_advanced_router.py`
- `analytics_jobs_router.py`
- `analytics_materials_router.py`
- `analytics_patterns_router.py`

### Steps
1. Move: `app/_experimental/analytics/` → `app/analytics/`
2. Update all 4 import paths
3. Register in a new `analytics_manifest.py`
4. Run tests after

---

## Notes on how this backlog works

Each item here was identified by reading code, not by speculation.
Every "file to create" path is deliberate — it fits the existing module structure.
Every "what exists" section cites real function names from the actual codebase.

When an item is implemented: delete it from here and add it to `CHANGELOG.md`.
When a new gap is found during implementation: add it here before closing the session.
Do not let findings live only in conversation history.





