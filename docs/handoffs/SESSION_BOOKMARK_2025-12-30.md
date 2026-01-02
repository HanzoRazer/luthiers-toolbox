# Session Bookmark: CAM OPERATION Lane Promotion

**Date:** 2025-12-30
**Branch:** `feature/cnc-saw-labs`
**Latest Commit:** `d2d6e61`

## What Was Accomplished

### ADR-003 Phase 1 Complete

Promoted all CAM G-code generating endpoints to OPERATION lane with artifact persistence:

| Wave | Endpoints | Commit |
|------|-----------|--------|
| 9 | RMOS Toolpaths, Rosette CNC, V-Carve | `cc5dd03`, `98af7e0`, `0ea2c81` |
| 10 | Roughing, Drilling, Drill Pattern, Bi-Arc | `3afbe6d` |
| 11 | Relief, Adaptive, Helical | `9b7cb47` |

### Files Modified

**Routers (Phase 1 artifact wrapper added):**
- `services/api/app/rmos/api/rmos_toolpaths_router.py`
- `services/api/app/cam/routers/rosette/cam_router.py`
- `services/api/app/art_studio/vcarve_router.py`
- `services/api/app/cam/routers/toolpath/roughing_router.py`
- `services/api/app/routers/drilling_router.py`
- `services/api/app/cam/routers/drilling/pattern_router.py`
- `services/api/app/cam/routers/toolpath/biarc_router.py`
- `services/api/app/art_studio/relief_router.py`
- `services/api/app/routers/adaptive_router.py`
- `services/api/app/cam/routers/toolpath/helical_router.py`

**Documentation:**
- `docs/adr/ADR-003-cam-operation-lane-promotion.md` — Created and tracking updated
- `docs/ENDPOINT_TRUTH_MAP.md` — Updated with all promoted endpoints
- `docs/OPERATION_EXECUTION_GOVERNANCE_v1.md` — Added Appendix D (Execution Classes)
- `docs/WHY_SAW_LAB_IS_DIFFERENT.md` — Created contributor explainer
- `services/api/app/ci/check_execution_class_compliance.py` — Created CI rule

### Artifact Kinds Created

| Endpoint | Artifact Kind |
|----------|---------------|
| `/api/rmos/toolpaths` | `rmos_toolpaths_execution`, `rmos_toolpaths_blocked` |
| `/api/cam/rosette/plan-toolpath` | `rosette_toolpath_plan` |
| `/api/cam/rosette/post-gcode` | `rosette_gcode_post` |
| `/api/art-studio/vcarve/gcode` | `vcarve_gcode_execution` |
| `/api/cam/toolpath/roughing/gcode` | `roughing_gcode_execution` |
| `/api/cam/drilling/gcode` | `drilling_gcode_execution` |
| `/api/cam/drilling/pattern/gcode` | `drill_pattern_gcode_execution` |
| `/api/cam/toolpath/biarc/gcode` | `biarc_gcode_execution` |
| `/api/art-studio/relief/export-dxf` | `relief_dxf_export` |
| `/api/cam/pocket/adaptive/plan` | `adaptive_plan_execution` |
| `/api/cam/pocket/adaptive/gcode` | `adaptive_gcode_execution` |
| `/api/cam/toolpath/helical_entry` | `helical_gcode_execution` |

## What Remains

### CAM Unification Phases 2-5

Per ADR-003 migration path:

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Artifact Wrapper | ✅ Complete |
| Phase 2 | Feasibility Gate (RED blocking) | ❌ Planned |
| Phase 3 | Move Standardization (GCodeMove) | ❌ Planned |
| Phase 4 | Full Pipeline (SPEC→PLAN→DECISION→EXECUTE) | ❌ Planned |
| Phase 5 | Feedback Loop (job logs, learning) | ❌ Planned |

### CI Enforcement

- `check_lane_annotations.py` — Needs to be wired into CI workflow
- `check_execution_class_compliance.py` — Needs to be wired into CI workflow

### Permanent UTILITY Lane (By Design)

These remain in UTILITY and don't need promotion:
- Preview/simulation endpoints (`/preview`, `/sim`)
- Metadata endpoints (`/info`, `/health`)
- Root-mounted legacy (`/feasibility`, `/toolpaths`)
- Non-machine exports (DXF/SVG preview)

## How to Resume

```bash
cd C:/Users/thepr/Downloads/luthiers-toolbox
git checkout feature/cnc-saw-labs
git pull

# Check current state
git log --oneline -5

# Continue with Phase 2 (feasibility gates) or CI enforcement
```

## Key Documents

- `docs/OPERATION_EXECUTION_GOVERNANCE_v1.md` — Master governance contract
- `docs/adr/ADR-003-cam-operation-lane-promotion.md` — Promotion plan and tracking
- `docs/ENDPOINT_TRUTH_MAP.md` — Complete endpoint inventory with lane classifications
- `docs/CNC_SAW_LAB_DEVELOPER_GUIDE.md` — Reference implementation guide

## Session Context

This session consolidated CAM endpoints under the OPERATION lane governance model established by the CNC Saw Lab reference implementation. The goal was to ensure all G-code generating endpoints have audit trails (artifacts + hashes) for production shop-floor safety.

Phase 1 (artifact persistence) is complete. Full unification to match the Saw Lab's 5-stage pipeline (SPEC→PLAN→DECISION→EXECUTE→EXPORT with feasibility gates and feedback loops) requires additional work in Phases 2-5.
