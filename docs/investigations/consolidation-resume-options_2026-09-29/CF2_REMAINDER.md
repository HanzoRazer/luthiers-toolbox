# CF2 Remainder — the 13 `LIVE_UNGOVERNED` manufacturing-output rows

Evidence-only. Source: committed `services/api/governance/manufacturing_output_inventory.json` at `5258d4c6`. All 13 rows appear here exactly once. Rows sharing one handler/service are noted and consolidated into a single ledger candidate (see `CANDIDATE_LEDGER.json`), but each route is listed individually below.

## The 13 rows

| # | Route | Handler / symbol | Ledger candidate | Subsystem | Introduced | Governed sibling? |
|---|---|---|---|---|---|---|
| 1 | POST /api/acoustics/radius-dish/generate-gcode | `radius_dish_router.generate_radius_dish_gcode` | CF2-07 | Acoustics | 2026-03-21 | no |
| 2 | POST /api/art-studio/inlay/export-gcode | `art_studio._inlay_gcode_addon.generate_inlay_gcode` | CF2-08 | Art Studio | 2026-03-10 | no |
| 3 | POST /api/cam/fret_slots/preview | `calculators.fret_slots_cam.generate_fret_slot_toolpaths` | CF2-09 | CAM / calculators | 2025-12-09 | n/a (preview) |
| 4 | POST /api/cam/polygon_offset.nc | `polygon_offset_router.generate_polygon_offset_nc_program` | CF2-02 | CAM | 2025-12-13 | **yes** (`/api/cam/polygon_offset_governed.nc` FAIL_CLOSED) |
| 5 | POST /api/geometry/export_bundle | `geometry.bundle_router.export_bundle` | CF2-01 | Geometry export | 2026-02-10 | no |
| 6 | POST /api/geometry/export_bundle_multi | `geometry.bundle_router.export_bundle_multi` | CF2-01 | Geometry export | 2026-02-10 | no |
| 7 | POST /api/geometry/export_gcode | `geometry.export_router.export_gcode` | CF2-01 | Geometry export | 2026-02-10 | **yes** (`/api/geometry/export_gcode_governed` FAIL_CLOSED) |
| 8 | POST /api/headstock/transition/gcode | `neck.headstock_transition_export.build_transition_gcode` | CF2-10 | Neck / headstock | 2026-03-18 | no |
| 9 | POST /api/rmos/toolpaths | `rmos.api_contracts.generate_toolpaths_for_design` | CF2-04 | RMOS core | 2025-12-04 | no (shared multi-mode generator) |
| 10 | POST /api/rmos/wrap/mvp/dxf-to-grbl | inline (`rmos/mvp_router.py`) | CF2-05 | RMOS wrap MVP | unverified | no |
| 11 | POST /api/saw/batch/toolpaths/from-decision | `saw_lab_toolpaths_from_decision_service.generate_toolpaths_from_decision` | CF2-03 | Saw Lab | 2025-12-26 | no |
| 12 | POST /api/saw/compare/toolpaths | `saw_lab_toolpaths_from_decision_service.generate_toolpaths_from_decision` | CF2-03 | Saw Lab | 2025-12-26 | no |
| 13 | POST /api/vision/photo-to-gcode | inline (`vision/router.py`) | CF2-06 | Vision (Beta) | unverified | no |

## Subsystem grouping & shared handlers
- **Geometry export (rows 5,6,7)** — `bundle_router` + `export_router`; `export_gcode` already has a governed sibling `export_gcode_governed` (a proven in-repo containment template). One ledger candidate CF2-01.
- **Saw Lab toolpaths (rows 11,12)** — both call `generate_toolpaths_from_decision` in one service. One ledger candidate CF2-03. No governed sibling.
- **Single-handler standalone (rows 1,2,8)** — radius-dish, inlay, headstock: dedicated handlers, no governed sibling. Small standalone candidates CF2-07/08/10.
- **RMOS core/wrap (rows 9,10)** — generic `generate_toolpaths_for_design` (shared multi-mode) and an MVP wrap inline emitter.
- **Vision (row 13)** — Beta subsystem inline emitter.
- **Preview vs emitter (row 3)** — `/api/cam/fret_slots/preview` is named a preview; requires classification (emitter vs non-emitting preview) before containment.

## Draft-lane note (important)
Rows 4 (`polygon_offset.nc`) and 7 (`export_gcode`) are **intentional draft/preview lanes with governed siblings already FAIL_CLOSED**. The `polygon_offset_router` docstring explicitly directs governed execution to `/polygon_offset_governed.nc`. These are not "missing containment" in the same sense as the others; they may be `DEFERRED_AUTHORIZED` (documented draft lanes) rather than CF2 targets. CF2-02 is dispositioned `DEFERRED_AUTHORIZED`.

## Manufacturing risk ranking (evidence-based, coarse)
1. **Highest — genuinely ungoverned program emitters with no governed path**: saw toolpaths (11,12), geometry bundle (5,6), radius-dish (1), inlay (2), headstock (8), rmos/wrap (10), vision (13).
2. **Medium — shared/generic**: rmos/toolpaths (9) — a multi-mode generator; governance may belong at the mode-specific routes.
3. **Lower — draft lanes with governed siblings**: polygon_offset.nc (4), export_gcode (7).
4. **Needs classification**: fret_slots/preview (3).

## Should these stay in CF2 or move to another program?
- The genuinely-ungoverned emitters (group 1) are the natural continuation of CF2 and mirror the Rosette containment pattern exactly (authority-before-generation, FAIL_CLOSED).
- The draft lanes (group 3) should be **documented as intentional** rather than contained, unless policy requires draft-lane governance — a separate policy decision, not a CF2 gap.
- `rmos/toolpaths` (9) and Vision (13) warrant a scope decision (generic vs mode-specific; Beta maturity) before containment.
- Route order in the inventory is **not** used to choose the next target (frozen decision).

CRO-012 (all 13 rows present exactly once) and CRO-013 (no governed/unknown row misreported as live-ungoverned) are satisfied by this table being generated from the committed inventory JSON.
