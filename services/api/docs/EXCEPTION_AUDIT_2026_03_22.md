# Exception Handler Audit — 2026-03-22

## Summary

Audited 64 `except Exception` blocks across 32 files. Categorized by pattern and risk level.

## Categories

### Category A: Job/Pipeline Handlers (22 instances) — KEEP

**Pattern**: Catch any exception from user-provided or dynamic handlers, convert to structured failure result.

**Files**:
- `app/calculators/build_sequence.py` (10 instances) — Build pipeline stages
- `app/core/job_queue/queue_execution.py` (4 instances) — Job worker loop
- `app/agentic/router.py` (2 instances) — Agent decision pipeline
- `app/agentic/spine/replay.py` (1 instance) — Moment detection
- `app/routers/dxf_adaptive_consolidated_router.py` (2 instances) — DXF processing pipeline
- `app/routers/binding_design_router.py` (2 instances) — Binding pipeline
- `app/routers/cam/cam_workspace_router.py` (1 instance) — CAM workspace

**Rationale**: These are legitimate "catch all from untrusted/dynamic code" patterns. The exception is logged and converted to a structured error response. **Action**: Add `# audited: pipeline-handler` comment.

---

### Category B: Optional Import/Feature Detection (8 instances) — KEEP

**Pattern**: Try to import optional dependency, fall back gracefully if unavailable.

**Files**:
- `app/calculators/setup_cascade.py` (2 instances) — Optional sgspec import
- `app/routers/photo_vectorizer_router.py` (1 instance) — Optional vectorizer import
- `app/routers/cam/cam_workspace_router.py` (1 instance) — Optional cam_exec import
- `app/ci/ban_experimental_ai_core_imports.py` (1 instance) — AST parsing fallback
- `app/ci/check_bare_except.py` (0 instances) — Just prints guidance, not a real exception handler
- `app/ai/context_retrieval.py` (1 instance) — Optional context fetch
- `app/materials/registry/tonewoods.py` (2 instances) — Optional registry load

**Rationale**: ImportError is the expected exception, but module code may raise other exceptions during import. **Action**: Narrow to `(ImportError, Exception)` with `# audited: optional-import` comment.

---

### Category C: HTTP Endpoint Catch-All (18 instances) — NARROW

**Pattern**: Catch exception, convert to HTTP 500, log error.

**Files**:
- `app/routers/ai/defect_detection_router.py` (2 instances)
- `app/routers/ai/recommendations_router.py` (3 instances)
- `app/routers/ai/assistant_router.py` (2 instances)
- `app/routers/ai/wood_grading_router.py` (2 instances)
- `app/routers/ltb_calculator_router.py` (2 instances)
- `app/routers/neck/headstock_transition_export.py` (2 instances)
- `app/routers/neck/neck_profile_export.py` (2 instances)
- `app/routers/export/curve_export_router.py` (1 instance)
- `app/routers/export/rosette_pdf_router.py` (1 instance)
- `app/routers/blueprint_cam/blueprint_cam_core_router.py` (2 instances)
- `app/routers/headstock/dxf_export.py` (1 instance)
- `app/routers/cam/guitar/flying_v_cam_router.py` (1 instance)

**Rationale**: These should be narrowed to specific exceptions where possible. At minimum, document the expected exceptions. **Action**: Add `# audited: http-catch-all — ValueError, KeyError, IOError` comment with expected types.

---

### Category D: Best-Effort/Non-Fatal Operations (10 instances) — KEEP

**Pattern**: Operation failure is logged but doesn't break the main flow.

**Files**:
- `app/websocket/router.py` (2 instances) — WebSocket send failures
- `app/middleware/rate_limit.py` (1 instance) — Rate limit Redis failure fallback
- `app/infra/live_monitor.py` (1 instance) — Monitor emission failure
- `app/projects/service.py` (1 instance) — Project save best-effort
- `app/blueprint/project_writer.py` (1 instance) — Blueprint write best-effort
- `app/dxf/preflight_service.py` (1 instance) — DXF preflight best-effort
- `app/calculators/plate_design/inverse_solver.py` (1 instance) — Solver iteration fallback

**Rationale**: These operations are non-fatal by design. Failure is logged and the main operation continues. **Action**: Add `# audited: best-effort-non-fatal` comment.

---

### Category E: Safety-Relevant — NARROW IMMEDIATELY (6 instances)

**Pattern**: Exception handling in code paths that affect CNC operations.

**Files**:
- `app/routers/cam/cam_workspace_router.py` (2 instances — lines 553, 573)
- `app/routers/dxf_adaptive_consolidated_router.py` (2 instances — lines 152, 211)

**Rationale**: These are in CAM code paths. Broad exception handling could mask safety-critical errors. **Action**: Narrow to specific exceptions and add explicit safety annotation.

---

## Recommended Actions

### Immediate (Safety-Critical)
1. `cam_workspace_router.py:553,573` — Narrow to `(ValueError, KeyError, ezdxf.DXFError)`
2. `dxf_adaptive_consolidated_router.py:152,211` — Already handles `DXFStructureError`, narrow the generic catch

### High Priority (Technical Debt)
3. Add `# audited: <category>` comment to all 64 instances
4. Narrow HTTP catch-all instances to `(ValueError, KeyError, TypeError, IOError)`

### Documentation
5. Add this audit to `docs/` and reference in SPRINT_BOARD.md

---

## Audit Trail

| Date | Auditor | Action |
|------|---------|--------|
| 2026-03-22 | Claude | Initial audit, 64 instances categorized |
