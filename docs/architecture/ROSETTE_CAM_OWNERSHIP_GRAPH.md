# Rosette CAM Ownership Graph

**Date:** 2026-05-10  
**Auditor:** Claude (CAM Dev Order 5F)  
**Status:** Audit Complete

---

## Generator Ownership Map

### Primary Generators

```
rosette_engine.py (Art Studio)
├── estimate_rosette_feasibility()
├── render_preview_svg()
├── compute_bom()
├── run_mfg_checks()
└── Consumers:
    ├── rosette_designer_routes.py
    └── rosette_snapshot_routes.py

rosette_cam_bridge.py (Services)
├── plan_rosette_toolpath() [single geometry]
├── plan_per_ring_toolpath() [pattern-aware, Phase 4]
├── postprocess_toolpath_grbl()
└── Consumers:
    ├── rosette_toolpath_router.py
    └── rosette_manufacturing_routes.py

pattern_generator.py (CAM/Rosette)
├── RosettePatternEngine
│   ├── generate_traditional()
│   ├── generate_modern()
│   └── list_preset_matrices()
└── Consumers:
    ├── rosette_pattern_routes.py
    └── rosette_manufacturing_routes.py

tile_segmentation.py (CAM/Rosette)
├── compute_tile_segmentation()
├── generate_slices_for_ring()
├── build_preview_snapshot()
└── Consumers:
    └── rosette_cam_router.py

cnc_gcode_exporter.py (CAM/Rosette/CNC)
├── generate_gcode_from_toolpaths()
└── Consumers:
    └── rosette_cam_router.py

traditional_builder.py (CAM/Rosette)
├── TraditionalBuilder
│   ├── list_master_patterns()
│   ├── get_pattern_info()
│   └── create_project()
└── Consumers:
    └── rosette_manufacturing_routes.py

rosette_planner.py (Core)
├── generate_manufacturing_plan()
└── Consumers:
    └── rosette_manufacturing_routes.py
```

---

## Shared Utilities

| Utility | Location | Consumers |
|---------|----------|-----------|
| `generate_circle_points()` | geometry/arc_utils.py | rosette_jobs_routes.py |
| `RosetteRingConfig` | cam/rosette/models.py | rosette_cam_router.py |
| `MaterialType`, `MachineProfile` | cam/rosette/cnc/__init__.py | rosette_cam_router.py |
| `rosette_snapshot_store` | art_studio/services | rosette_snapshot_routes.py |
| `art_studio_rosette_store` | app/ | rosette_jobs_routes.py, rosette_compare_routes.py |

---

## Duplicate/Overlapping Generators

### Preview Geometry Generation

| Generator | Location | Output | Notes |
|-----------|----------|--------|-------|
| `render_preview_svg()` | rosette_engine.py | SVG string | Tile-based |
| `_generate_rosette_paths()` | rosette_jobs_routes.py | Path points | Simple rings |
| `build_preview_snapshot()` | tile_segmentation.py | Snapshot payload | Slice-based |
| `generate_modern()` | pattern_generator.py | Paths + DXF/SVG | Parametric |

**Finding:** 4 different preview generation approaches, each producing different output formats.

### G-code Generation

| Generator | Location | Output | Profile |
|-----------|----------|--------|---------|
| `postprocess_toolpath_grbl()` | rosette_cam_bridge.py | G-code text | GRBL only |
| `generate_gcode_from_toolpaths()` | cnc_gcode_exporter.py | G-code text | GRBL/FANUC |
| `simulate_build_and_cnc()` | herringbone_parametric.py | Simulation + G-code | Inline |

**Finding:** Multiple G-code generators with different postprocessor implementations.

---

## Schema Ownership

| Schema File | Models | Consumers |
|-------------|--------|-----------|
| `rosette_designer.py` | TileCatalogResponse, PreviewRequest, BomRequest, etc. | rosette_designer_routes |
| `rosette_params.py` | Core rosette parameters | Multiple |
| `rosette_feasibility.py` | FeasibilityResult | rosette_snapshot_routes |
| `rosette_snapshot.py` | RosetteDesignSnapshot, SnapshotMetadata | rosette_snapshot_routes |
| `rosette_pattern.py` | RosettePatternInDB, RosetteRingBand | rosette_manufacturing_routes |
| `rosette_project.py` | RosetteProjectRequest/Response | rosette_manufacturing_routes |
| `models.py` | RosetteRingConfig, SegmentationResult, SliceBatch | rosette_cam_router |
| `pattern_schemas.py` | Pattern-specific schemas | rosette_pattern_routes |

---

## Service Layer Dependencies

```
Frontend (Vue)
    │
    ├── artStudioApi.ts ──────────────────┐
    │   └── generateRosetteGeometry()     │
    │   └── exportRosette()               │
    │   └── renderRosettePreview()        │
    │                                     │
    ├── artPreviewClient.ts ──────────────┤
    │   └── previewSvg()                  │
    │                                     │
    ├── artFeasibilityClient.ts ──────────┤
    │   └── batch()                       │
    │                                     │
    └── rmos.ts ──────────────────────────┤
        └── searchConstraintFirst()       │
                                          ▼
                               Art Studio / RMOS Routes
                                          │
    ┌─────────────────────────────────────┼────────────────────────────────────┐
    │                                     │                                    │
    ▼                                     ▼                                    ▼
rosette_engine.py            rosette_cam_bridge.py               pattern_generator.py
rosette_planner.py           tile_segmentation.py                traditional_builder.py
rosette_snapshot_store.py    cnc_gcode_exporter.py
```

---

## Prototype/Experimental Code

| File | Purpose | Status |
|------|---------|--------|
| `prototypes/herringbone_parametric.py` | Herringbone CNC simulation | EXPERIMENTAL |
| `prototypes/rope_twist_rosette.py` | Rope twist pattern | EXPERIMENTAL |
| `prototypes/rope_twist_rosette_v2.py` | Rope twist v2 | EXPERIMENTAL |
| `prototypes/wave_simple_sine.py` | Wave pattern | EXPERIMENTAL |
| `prototypes/celtic_parametric_knots.py` | Celtic knots | EXPERIMENTAL |
| `prototypes/spanish_ladder_parametric.py` | Spanish ladder | EXPERIMENTAL |
| `prototypes/generate_spanish_rosette.py` | Spanish rosette | EXPERIMENTAL |
| `prototypes/generate_wave_rosette.py` | Wave rosette | EXPERIMENTAL |

**Note:** Prototype code is imported by `rosette_pattern_routes.py` for simulation.

---

## Legacy/Deprecated Code

| File | Notes |
|------|-------|
| `pipelines/rosette/rosette_calc.py` | Legacy calculator, may be superseded |
| `calculators/rosette_calc.py` | Facade, unclear if used |
| `art_studio/services/rosette/` | Service layer, partially integrated |

---

## Canonical Ownership Recommendation

For future normalization, the following ownership model is recommended:

| Concern | Canonical Owner |
|---------|-----------------|
| Design/Preview (SVG) | rosette_engine.py |
| Manufacturing Planning | rosette_planner.py |
| Pattern Generation | pattern_generator.py |
| Toolpath Planning | rosette_cam_bridge.py |
| G-code Generation | cnc_gcode_exporter.py |
| CNC Simulation | herringbone_parametric.py (promote) |

---

## Cross-Reference

| Document | Relevance |
|----------|-----------|
| ROSETTE_CAM_ROUTE_MAP.md | Route inventory |
| ROSETTE_CAM_FRAGMENTATION_AUDIT.md | Overlap analysis |

---

*Ownership graph audit completed: 2026-05-10*
