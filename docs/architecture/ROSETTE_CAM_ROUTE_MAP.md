# Rosette CAM Route Map

**Date:** 2026-05-10  
**Auditor:** Claude (CAM Dev Order 5F)  
**Status:** Audit Complete

---

## Executive Summary

The Rosette CAM ecosystem spans **11 route files** with **~45 endpoints** across 3 distinct subsystems (Art Studio, RMOS/CAM, Export). Significant fragmentation exists between design-time preview, manufacturing planning, and CNC export paths.

---

## Route Surface Inventory

### Art Studio Routes (Design/Preview/Comparison)

| File | Prefix | Endpoints | Status |
|------|--------|-----------|--------|
| `rosette_designer_routes.py` | `/rosette/designer` | 10 | ACTIVE |
| `rosette_jobs_routes.py` | `/api/art/rosette` | 4 | ACTIVE |
| `rosette_compare_routes.py` | `/api/art/rosette` | 4 | ACTIVE |
| `rosette_snapshot_routes.py` | `/rosette/snapshots` | 8 | ACTIVE |
| `rosette_pattern_routes.py` | `/api/art/rosette/pattern` | 7 | ACTIVE |
| `rosette_manufacturing_routes.py` | `/api/art/rosette` | 5 | ACTIVE |

**Total Art Studio:** 38 endpoints

### CAM/RMOS Routes (Toolpath/G-code)

| File | Prefix | Endpoints | Status |
|------|--------|-----------|--------|
| `rosette_toolpath_router.py` | `/rosette` | 2 | ACTIVE |
| `rosette_cam_router.py` | `/rmos` | 7 | ACTIVE |

**Total CAM/RMOS:** 9 endpoints

### Export Routes

| File | Prefix | Endpoints | Status |
|------|--------|-----------|--------|
| `rosette_pdf_router.py` | `/export/rosette` | 1 | CANDIDATE |

**Total Export:** 1 endpoint

---

## Detailed Route Inventory

### 1. rosette_designer_routes.py (Art Studio API)

**Purpose:** Interactive tile-based rosette designer
**Generator:** `rosette_engine.py`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/catalog` | GET | Tile catalog, ring defs, segment options |
| `/place-tile` | POST | Place tile with symmetry |
| `/sym-cells` | POST | Get affected cells for symmetry mode |
| `/cell-info` | GET | Hover info for cell |
| `/bom` | POST | Bill of materials calculation |
| `/bom/csv` | POST | BOM CSV export |
| `/mfg-check` | POST | Manufacturing intelligence checks |
| `/mfg-auto-fix` | POST | Auto-fix manufacturing issues |
| `/recipes` | GET | Recipe presets list |
| `/recipes/{recipe_id}` | GET | Single recipe |
| `/preview` | POST | SVG preview render |
| `/export/svg` | POST | SVG file export |

### 2. rosette_jobs_routes.py (Art Studio API)

**Purpose:** Job CRUD for rosette previews
**Generator:** Inline geometry (arc_utils)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/preview` | POST | Generate geometry preview |
| `/save` | POST | Save rosette job |
| `/jobs` | GET | List saved jobs |
| `/presets` | GET | List available presets |

### 3. rosette_compare_routes.py (Art Studio API)

**Purpose:** Design comparison and risk timeline
**Generator:** N/A (comparison logic)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/compare` | POST | Compare two jobs |
| `/compare/snapshot` | POST | Save comparison to risk timeline |
| `/compare/snapshots` | GET | List comparison snapshots |
| `/compare/export_csv` | GET | Export comparison history CSV |

### 4. rosette_snapshot_routes.py (Art Studio API)

**Purpose:** Snapshot export/import with RMOS run artifacts
**Generator:** `rosette_engine.py` (feasibility)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/export` | POST | Export design as snapshot |
| `/import` | POST | Import design snapshot |
| `/{snapshot_id}` | GET | Get snapshot by ID |
| `/{snapshot_id}` | DELETE | Delete snapshot |
| `/{snapshot_id}` | PUT | Update snapshot metadata |
| `/{snapshot_id}/baseline` | POST | Toggle baseline flag |
| `/baseline` | GET | Get current baseline |
| `/` | GET | List all snapshots |

### 5. rosette_pattern_routes.py (Art Studio API)

**Purpose:** Traditional matrix + modern parametric pattern generation
**Generator:** `pattern_generator.py`, `herringbone_parametric.py`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/status` | GET | Pattern generator availability |
| `/patterns` | GET | List preset patterns |
| `/patterns/{pattern_id}` | GET | Pattern details |
| `/generate_traditional` | POST | Traditional matrix method |
| `/generate_modern` | POST | Modern parametric method |
| `/export` | POST | Export pattern formats |
| `/simulate-build` | POST | Build + CNC simulation |

### 6. rosette_manufacturing_routes.py (Art Studio API)

**Purpose:** Manufacturing planning, traditional builder, unified project
**Generator:** `rosette_planner.py`, `TraditionalBuilder`, `rosette_cam_bridge.py`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/manufacturing-plan` | POST | Multi-family manufacturing plan |
| `/traditional/masters` | GET | List patterns by master luthier |
| `/traditional/patterns/{id}` | GET | Traditional pattern info |
| `/traditional/project` | POST | Full traditional project sheet |
| `/project` | POST | Unified project envelope (Phase 3+4) |

### 7. rosette_toolpath_router.py (CAM)

**Purpose:** OPERATION lane toolpath planning with RMOS governance
**Generator:** `rosette_cam_bridge.py`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/plan-toolpath` | POST | Generate toolpath moves (RMOS artifact) |
| `/post-gcode` | POST | Convert moves to G-code (RMOS artifact) |

### 8. rosette_cam_router.py (RMOS)

**Purpose:** CNC/CAM endpoints delegating to cam.rosette engines
**Generator:** `tile_segmentation.py`, `rosette_cnc_wiring.py`, `cnc_gcode_exporter.py`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/rosette/segment-ring` | POST | Generate segment ring geometry |
| `/rosette/design` | POST | Multi-ring design (GAP-NEW-1) |
| `/rosette/generate-slices` | POST | Generate slices for manufacturing |
| `/rosette/preview` | POST | Preview data for pattern |
| `/rosette/export-cnc` | POST | Export to CNC G-code |
| `/rosette/cnc-history` | GET | CNC job history |
| `/rosette/cnc-job/{id}` | GET | CNC job details |

### 9. rosette_pdf_router.py (Export)

**Purpose:** PDF export for rosette designs
**Status:** CANDIDATE (not fully audited)

---

## Shadow/Duplicate Routes Identified

### Preview Endpoints

| Route | File | Generator | Notes |
|-------|------|-----------|-------|
| `/rosette/preview` | rosette_designer_routes.py | rosette_engine | SVG preview |
| `/api/art/rosette/preview` | rosette_jobs_routes.py | inline arc_utils | Geometry preview |
| `/rmos/rosette/preview` | rosette_cam_router.py | tile_segmentation | Pattern preview |
| `/api/art/rosette/preview/svg` | artPreviewClient (frontend) | ? | Frontend expects this |

**Finding:** 3+ distinct preview implementations with different generators.

### G-code/Export Endpoints

| Route | File | Generator | Notes |
|-------|------|-----------|-------|
| `/rosette/post-gcode` | rosette_toolpath_router.py | rosette_cam_bridge | GRBL postprocessor |
| `/rmos/rosette/export-cnc` | rosette_cam_router.py | cnc_gcode_exporter | Multiple profiles |
| `/api/art/rosette/pattern/simulate-build` | rosette_pattern_routes.py | herringbone_parametric | Simulation only |

**Finding:** G-code generation in multiple paths without unified postprocessor.

---

## Governance Observations

| Concern | Status |
|---------|--------|
| RMOS integration | Partial (rosette_toolpath_router.py has run artifacts) |
| Governed preview | NOT IMPLEMENTED (no gate semantics) |
| Coordinate documentation | PARTIAL (some files document, most don't) |
| Preview/export separation | MIXED (some endpoints do both) |

---

## Cross-Reference

| Document | Relevance |
|----------|-----------|
| ROSETTE_CAM_OWNERSHIP_GRAPH.md | Generator ownership |
| ROSETTE_CAM_FRAGMENTATION_AUDIT.md | Overlap analysis |
| ROSETTE_CAM_NORMALIZATION_BLOCKERS.md | Prerequisites |
| rosette_cam_route_manifest.json | Machine-readable |

---

*Route map audit completed: 2026-05-10*
