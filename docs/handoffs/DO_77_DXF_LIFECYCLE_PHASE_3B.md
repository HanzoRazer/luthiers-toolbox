# Dev Order 77: DXF Lifecycle — Phase 3B (Blueprint CAM Orchestrator)

**Sprint:** DXF Lifecycle — Runtime Boundary Follow-Through  
**Order:** DO 77 / Phase 3B  
**Status:** IMPLEMENTED  
**Date:** 2026-05-19  
**Prerequisite:** Phase 3A-4 merged (PR #43)  
**Branch:** `feat/dxf-lifecycle-phase-3b` from `main`

---

## Executive Summary

Adopt **governed DXF export lifecycle** on the three `routers/blueprint_cam/*` orchestrator candidates. All production `saveas` boundaries route through `governed_doc_saveas()` with `lifecycle_status="LIFECYCLE_GOVERNED"`. Validation-only — no DXF byte changes, no provenance attachment.

This is the **last DXF lifecycle batch** before IBG `BLOCKED_PROVENANCE` paths (R namespace).

---

## Scope

### In scope (3 modules, 5 save sites)

| File | Save sites | `export_type` | Prior status |
|------|------------|---------------|--------------|
| `routers/blueprint_cam/dxf_preprocessor.py` | `normalize_dxf_format`, `densify_dxf` | create-save, read-modify-save | COMPAT_ONLY / DIRECT_SAVE_GAP |
| `routers/blueprint_cam/contour_reconstruction.py` | `reconstruct_contours`, `reconstruct_bracing_dxf` | dxf-create-save | COMPAT_ONLY |
| `routers/blueprint_cam/dxf_geometry_correction.py` | `_apply_transformations` | dxf-read-modify-save | DIRECT_SAVE_GAP |

**New module:** `app/util/blueprint_dxf_export_lifecycle.py`

- `assert_governed_blueprint_dxf_export()` — guard with `router_endpoint` / `user_request` / `LIFECYCLE_GOVERNED`
- `governed_doc_saveas()` — assert then `doc.saveas(path)`

**Not in scope:** CAM G-code `export_lifecycle_orchestrator` (does not emit DXF). IBG provenance (5 paths). Further blueprint_cam refactors.

---

## Verification

```bash
cd services/api
pytest tests/test_dxf_lifecycle*.py tests/test_dxf_lifecycle_blueprint_cam_orchestrator.py -q
pytest tests/test_dxf_preprocessor.py tests/test_contour_reconstruction.py tests/test_dxf_geometry_correction.py -q
```

---

## Matrix updates

| File | Lifecycle | Lifecycle Status | Guard Status |
|------|-----------|------------------|--------------|
| `dxf_preprocessor.py` | N → Y | LIFECYCLE_GOVERNED | LIFECYCLE_GOVERNED |
| `contour_reconstruction.py` | N → Y | LIFECYCLE_GOVERNED | LIFECYCLE_GOVERNED |
| `dxf_geometry_correction.py` | N → Y | LIFECYCLE_GOVERNED | LIFECYCLE_GOVERNED |

**Metrics:** `ORCHESTRATOR_CANDIDATE: 0`, `LIFECYCLE_GOVERNED: 3` (blueprint_cam save paths; plus existing CAM export lifecycle router).

---

## Next

**R1 / R2:** IBG provenance ratification — 5 `BLOCKED_PROVENANCE` save points in `body_contour_solver.py` and `arc_reconstructor.py`.

---

*DO 77 — Phase 3B complete. DXF lifecycle guard rollout finished for non-IBG production paths.*
