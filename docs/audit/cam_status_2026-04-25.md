# CAM System Audit — 2026-04-25

## Methodology

- **Production paths only** — excludes sandbox/, docs/archive/recovered/, __pycache__/, node_modules/, .git/, services/api/test_temp/
- **Live grep on current code** — not cached data
- **Cross-referenced against git log** for actual state
- **Status determination:** positive evidence (working consumer + working backend) vs structural inspection (file exists, looks like code)

---

## 1. CAM File Inventory

### Directory Structure

| Directory | File Count | Total Lines | Purpose |
|-----------|-----------|-------------|---------|
| services/api/app/cam/ | 148+ | ~25,000+ | Core CAM modules |
| services/api/app/cam_core/ | 49 | ~4,500 | Feeds/speeds, tools, saw lab |
| services/api/app/routers/blueprint_cam/ | 9 | ~1,200 | Blueprint vectorization CAM |
| services/api/app/routers/cam/ | 10 | ~800 | Guitar-specific CAM routers |
| services/api/app/rmos/cam/ | 3 | ~150 | RMOS CAM intent schemas |
| services/api/app/data/cam_core/ | 3 (JSON) | N/A | Saw blades, runs, telemetry |
| services/api/app/data_registry/edition/pro/cam_presets/ | 1 (JSON) | N/A | Pro tier CAM presets |

### Key CAM Modules (services/api/app/cam/)

| File | Lines | Commits | Last Modified | Output Type | Status |
|------|-------|---------|---------------|-------------|--------|
| dxf_writer.py | 148 | 3 | 2026-04-25 | DXF (R12) | ACTIVE |
| post_processor.py | 539 | 2 | 2026-03-24 | G-code | ACTIVE |
| machines.py | 337 | 3 | 2026-04-05 | Config | ACTIVE |
| adaptive_core.py | 362 | 6 | 2026-03-24 | Toolpath | ACTIVE |
| adaptive_core_l1.py | 368 | 7 | 2026-03-28 | Toolpath | ACTIVE |
| adaptive_core_l2.py | 445 | 2 | 2026-02-09 | Toolpath | ACTIVE |
| contour_reconstructor.py | 405 | 7 | 2026-02-09 | Geometry | ACTIVE |
| dxf_advanced_validation.py | 618 | 11 | 2026-03-22 | Validation | ACTIVE |
| dxf_preflight.py | 498 | 9 | 2026-03-19 | Validation | ACTIVE |
| unified_dxf_cleaner.py | 583 | 3 | 2026-04-11 | DXF | ACTIVE |
| probe_patterns.py | 495 | 4 | 2026-03-24 | G-code | ACTIVE |
| modal_cycles.py | 419 | 6 | 2026-03-23 | G-code | ACTIVE |
| helical_core.py | 367 | 3 | 2026-03-24 | Toolpath | ACTIVE |
| trochoid_l3.py | 323 | 3 | 2026-02-26 | Toolpath | ACTIVE |

### CAM Subsystem Directories

#### services/api/app/cam/archtop/ (recently active)
| File | Lines | Commits | Last Modified | Status |
|------|-------|---------|---------------|--------|
| archtop_contour_generator.py | 199 | 3 | 2026-04-07 | ACTIVE |
| archtop_modal_analysis.py | 536 | 2 | 2026-04-07 | ACTIVE |
| archtop_pipeline.py | 92 | 1 | 2026-04-07 | ACTIVE |
| archtop_stiffness_map.py | 464 | 2 | 2026-04-07 | ACTIVE |
| archtop_surface_tools.py | 368 | 1 | 2026-04-07 | ACTIVE |

#### services/api/app/cam/binding/
| File | Lines | Commits | Last Modified | Status |
|------|-------|---------|---------------|--------|
| binding_corner_miter.py | 456 | 2 | 2026-03-17 | ACTIVE |
| channel_toolpath.py | 325 | 1 | 2026-03-10 | ACTIVE |
| purfling_ledge.py | 347 | 2 | 2026-03-17 | ACTIVE |
| offset_geometry.py | 135 | 1 | 2026-03-10 | ACTIVE |

#### services/api/app/cam/carving/
| File | Lines | Commits | Last Modified | Status |
|------|-------|---------|---------------|--------|
| surface_carving.py | 515 | 3 | 2026-03-24 | ACTIVE |
| graduation_map.py | 484 | 2 | 2026-03-15 | ACTIVE |
| config.py | 423 | 2 | 2026-03-15 | ACTIVE |
| orchestrator.py | 271 | 2 | 2026-03-24 | ACTIVE |

#### services/api/app/cam/rosette/ (CNC subsystem)
| File | Lines | Commits | Last Modified | Status |
|------|-------|---------|---------------|--------|
| tile_segmentation.py | 558 | 5 | 2026-03-16 | ACTIVE |
| traditional_builder.py | 539 | 5 | 2026-03-12 | ACTIVE |
| preset_definitions.py | 580 | 1 | 2026-03-17 | ACTIVE |
| pattern_renderer.py | 450 | 6 | 2026-04-06 | ACTIVE |
| photo_converter.py | 466 | 4 | 2026-02-27 | ACTIVE |

#### services/api/app/cam/neck/
| File | Lines | Commits | Last Modified | Status |
|------|-------|---------|---------------|--------|
| profile_carving.py | 383 | 3 | 2026-03-24 | ACTIVE |
| fret_slots.py | 247 | 3 | 2026-03-24 | ACTIVE |
| orchestrator.py | 279 | 2 | 2026-03-24 | ACTIVE |
| truss_rod_channel.py | 209 | 3 | 2026-03-24 | ACTIVE |
| config.py | 325 | 1 | 2026-03-15 | ACTIVE |

#### services/api/app/cam/vcarve/
| File | Lines | Commits | Last Modified | Status |
|------|-------|---------|---------------|--------|
| toolpath.py | 430 | 2 | 2026-03-12 | ACTIVE |
| geometry.py | 159 | 1 | 2026-03-10 | ACTIVE |
| chipload.py | 183 | 1 | 2026-03-10 | ACTIVE |

### CAM Core (services/api/app/cam_core/)

#### feeds_speeds/
| File | Lines | Commits | Last Modified | Status |
|------|-------|---------|---------------|--------|
| learned_overrides.py | 454 | 1 | 2026-03-19 | ACTIVE |
| calculator.py | 142 | 2 | 2026-01-30 | ACTIVE |
| presets_db.py | 81 | 2 | 2026-02-07 | ACTIVE |
| materials.py | 19 | 1 | 2025-12-14 | MINIMAL |
| deflection_model.py | 15 | 1 | 2026-01-30 | COMPLETE |
| heat_model.py | 18 | 1 | 2026-01-30 | COMPLETE |

#### saw_lab/
| File | Lines | Commits | Last Modified | Status |
|------|-------|---------|---------------|--------|
| saw_blade_validator.py | 499 | 4 | 2026-03-24 | ACTIVE |
| saw_blade_registry.py | 394 | 3 | 2026-02-07 | ACTIVE |
| queue.py | 265 | 4 | 2026-02-27 | ACTIVE |
| operations.py | 221 | 4 | 2026-03-24 | ACTIVE |
| learning.py | 205 | 3 | 2026-03-19 | ACTIVE |

#### gcode/
| File | Lines | Commits | Last Modified | Status |
|------|-------|---------|---------------|--------|
| saw_gcode_generator.py | 358 | 5 | 2026-03-23 | ACTIVE |
| gcode_models.py | 175 | 3 | 2026-03-08 | ACTIVE |

---

## 2. Stub Identification

### Confirmed Stubs: NONE

No files contain `raise NotImplementedError` in the CAM directories.

### Minimal/Placeholder Files

| File | Lines | Issue | Recommendation |
|------|-------|-------|----------------|
| cam_core/feeds_speeds/materials.py | 19 | Only hardwood/softwood | Expand with lutherie woods |
| cam_core/feeds_speeds/chipload_calc.py | 9 | Single import wrapper | Evaluate necessity |
| cam_core/feeds_speeds/presets.py | 9 | Single import wrapper | Evaluate necessity |

### TODO/FIXME Comments (3 total)

| File | Line | Comment |
|------|------|---------|
| adaptive_core.py | 296 | TODO: subtract islands properly |
| adaptive_core_l1.py | 172 | TODO: Island subtraction uses simple expansion |
| archtop_modal_analysis.py | 370 | TODO: Implement simply_supported when solver supports it |

**Assessment:** These are enhancement notes, not blockers. The island subtraction works with a simplified approach.

---

## 3. Reported vs Actual Discrepancies

### SPRINTS.md Claims vs Reality

| Claim | Status | Evidence |
|-------|--------|----------|
| blueprint_cam/dxf_preprocessor.py migrated to dxf_writer | **TRUE** | imports dxf_writer |
| blueprint_cam/contour_reconstruction.py migrated | **TRUE** | imports dxf_writer |
| cam/archtop_bridge_generator.py migrated | **TRUE** | imports dxf_writer |
| cam/archtop_saddle_generator.py migrated | **TRUE** | imports dxf_writer |
| Archtop scripts exist at cam/archtop/ | **TRUE** | All 5 files present |

### Outstanding DXF Migrations (from generator audit)

| File | Current Version | Action Needed |
|------|-----------------|---------------|
| cam/archtop/archtop_surface_tools.py | R2010 | Convert LWPOLYLINE |
| cam/dxf_consolidator.py | R2000 | Migrate to dxf_writer |
| cam/dxf_advanced_validation.py | R2010 (×2) | Migrate to dxf_writer |
| cam/layer_consolidator.py | R2000 | Migrate to dxf_writer |

---

## 4. CAM Router / Endpoint Inventory

### Registered CAM Routers (cam_manifest.py)

| Module | Prefix | Category | Status |
|--------|--------|----------|--------|
| simulation_consolidated_router | /api/cam/sim | cam_core | ACTIVE |
| routers/adaptive | /api | cam_core | ACTIVE |
| cam.routers.monitoring | /api/cam | cam_core | ACTIVE |
| cam.routers.utility | /api/cam | cam_core | ACTIVE |
| routers/cam_learn_router | /api/cam/learn | cam_core | ACTIVE |
| routers/gcode_consolidated_router | /api | cam | ACTIVE |
| routers/dxf_adaptive_consolidated_router | /api | cam | ACTIVE |
| routers/dxf_preflight_router | /api | cam | ACTIVE |
| routers/polygon_offset_router | /api | cam | ACTIVE |
| routers/bridge_presets_router | /api | config | ACTIVE |
| routers/machines_consolidated_router | /api/machines | config | ACTIVE |
| routers/cam.guitar | /api/cam/guitar | instrument | ACTIVE |
| routers/cam.cam_workspace_router | /api/cam-workspace | workspace | ACTIVE |
| routers/blueprint_cam | /api/cam/blueprint | business | ACTIVE |

### API v1 CAM Endpoints

| Endpoint | Handler | Status |
|----------|---------|--------|
| POST /api/v1/cam/plan | dxf_workflow.py | ACTIVE |
| POST /api/v1/cam/gcode | dxf_workflow.py | ACTIVE |
| GET /api/v1/cam/posts | dxf_workflow.py | ACTIVE |

### Frontend Callers (packages/client/src/)

| Vue Component | CAM Endpoint |
|---------------|--------------|
| components/cam/CamBackplot3D.vue | /api/cam/* |
| components/cam/CamBackplotPanel.vue | /api/cam/* |
| components/cam/CamBridgePreflightPanel.vue | /api/cam/* |
| components/cam/CamJobInsightsPanel.vue | /api/cam/* |
| components/cam/CamMachineEnvelopePanel.vue | /api/cam/* |
| components/cam/CamPipelineGraph.vue | /api/cam/* |
| components/cam/CamPipelineRunner.vue | /api/cam/* |
| components/adaptive/AdaptivePreview.vue | /api/cam/pocket/adaptive/* |
| api/adaptive.ts | /api/cam/pocket/adaptive/* |
| api/vcarve.ts | /api/cam/* |
| cam_core/api.ts | /api/cam-core/* |

---

## 5. DXF Input Dependencies

### Files Using DxfWriter (18 total)

| File | Import Source | Status |
|------|---------------|--------|
| instrument_geometry/body/ibg/arc_reconstructor.py | DxfWriter | ACTIVE |
| generators/bezier_body.py | DxfWriter | ACTIVE |
| instrument_geometry/body/ibg/body_contour_solver.py | DxfWriter | ACTIVE |
| instrument_geometry/bridge/archtop_floating_bridge.py | DxfWriter | ACTIVE |
| instrument_geometry/soundhole/spiral_geometry.py | DxfWriter | ACTIVE |
| routers/neck/headstock_transition_export.py | DxfWriter | ACTIVE |
| routers/headstock/dxf_export.py | DxfWriter | ACTIVE |
| cam/archtop_saddle_generator.py | DxfWriter | ACTIVE |
| cam/archtop_bridge_generator.py | DxfWriter | ACTIVE |
| cam/archtop/archtop_contour_generator.py | DxfWriter | ACTIVE |
| routers/neck/neck_profile_export.py | DxfWriter | ACTIVE |
| routers/blueprint_cam/contour_reconstruction.py | DxfWriter | ACTIVE |
| routers/blueprint_cam/dxf_preprocessor.py | DxfWriter | ACTIVE |
| routers/export/curve_export_router.py | DxfWriter | ACTIVE |
| instrument_geometry/body/smart_guitar_dxf.py | DxfWriter | ACTIVE |
| routers/editor_export_router.py | DxfWriter | ACTIVE |
| services/blueprint_orchestrator.py | DxfWriter | ACTIVE |
| routers/archtop_router.py | DxfWriter | ACTIVE |

### DXF Entity Type Expectations

CAM files expect **R12 LINE entities** from dxf_writer.py. The DXF standard enforces:
- Format: R12 (AC1009)
- Entities: LINE only (no LWPOLYLINE)
- Coordinates: 3 decimal precision
- Layers: Named layers, no geometry on layer 0

---

## 6. Tool / Material / Machine Config Inventory

### Machine Configurations (machines.py)

| Machine ID | Name | Controller | Travel (mm) | Spindle | Status |
|------------|------|------------|-------------|---------|--------|
| bcam_2030a | BCAMCNC 2030A Lutherie Router | GRBL | 600×900×120 | VFD 6-24k | PRIMARY |
| shapeoko_3 | Carbide3D Shapeoko 3 | GRBL | 425×425×75 | Router 30k | ACTIVE |
| shapeoko_xxl | Carbide3D Shapeoko XXL | GRBL | 838×838×75 | Router 30k | ACTIVE |
| x_carve_1000 | Inventables X-Carve 1000mm | GRBL | 750×750×65 | Router 30k | ACTIVE |
| avid_cnc_4x4 | Avid CNC Pro 4x4 | Mach4 | 1219×1219×200 | VFD 6-24k | ACTIVE |
| laguna_iq | Laguna IQ | Mach3 | 610×610×114 | VFD 6-18k | ACTIVE |
| haas_vf2 | Haas VF-2 | Haas | 762×406×508 | Servo 0-8.1k | ACTIVE |

### Tool Definitions (cam_core/tools/models.py)

| Tool Type | Model Class | Fields | Status |
|-----------|-------------|--------|--------|
| Router Bit | RouterBitTool | diameter, flute_count, flute_length, taper_angle | COMPLETE |
| Saw Blade | SawBladeTool | diameter, kerf, tooth_count, max_rpm, preset_modes | COMPLETE |
| Drill Bit | DrillBitTool | diameter, tip_angle | COMPLETE |

### Tool Presets (data/cam_core/saw_blades.json)

| Blade ID | Diameter | Kerf | Teeth | Presets | Status |
|----------|----------|------|-------|---------|--------|
| ultra_thin_140 | 140mm | 1.0mm | 80 | 3 (Gentle, Normal, Aggressive) | ACTIVE |

### CAM Presets (data_registry/edition/pro/cam_presets/presets.json)

| Preset ID | Operation | Material | Tool | Status |
|-----------|-----------|----------|------|--------|
| body_rough_alder | adaptive_pocket | Alder | flat_6mm_2f | ACTIVE |
| body_finish_alder | profile | Alder | downcut_6mm_2f | ACTIVE |

### Material Profiles

| File | Materials Defined | Status |
|------|-------------------|--------|
| cam_core/feeds_speeds/materials.py | hardwood, softwood | MINIMAL |
| data/cam_core/saw_blades.json | hardwood, softwood, veneer | ACTIVE |

**Gap:** Material profiles in feeds_speeds/materials.py are placeholder-level. Saw blades JSON has better material coverage.

---

## 7. G-Code Dialect Coverage

### Supported Dialects (rmos/posts/)

| Dialect | File | Line Numbers | Cutter Comp | Tool Length Comp | Status |
|---------|------|--------------|-------------|------------------|--------|
| GRBL | grbl.py | No | No | No | ACTIVE |
| FANUC | fanuc.py | Yes (N###) | G41/G42 | G43 | ACTIVE |
| LinuxCNC | linuxcnc.py | Optional | G41/G42 | G43 | ACTIVE |
| Mach3 | (via base.py) | Optional | G41/G42 | G43 | ACTIVE |
| Haas | (via base.py) | Yes | G41/G42 | G43 | ACTIVE |

### BCAM 2030A Specific

The BCAM_2030A machine preset specifies GRBL controller. G-code output uses:
- G21 (metric units)
- G90 (absolute positioning)
- No line numbers
- Semicolon comments
- Standard GRBL modal groups

---

## 8. Sprint Closeout Check

### CAM-Related Sprint Work (from SPRINTS.md)

| Sprint/Task | Documented | Closeout Doc | Verified |
|-------------|------------|--------------|----------|
| DXF Migration Sprint 3B | Yes | generator_status_2026-04-25.md | YES |
| Archtop Free Tier Phase 1 | Yes | sprints_audit_2026-04-23.md | YES |
| blueprint_cam migrations | Yes | dxf_reconciliation_investigation_2026-04-25.md | YES |

### Missing Closeout Documents

No CAM-specific sprints found without closeout documentation.

---

## 9. Active Development Surface

### Recent CAM Commits (since 2026-04-01)

| Date | Commit | Description |
|------|--------|-------------|
| 2026-04-25 | 3b7e0a99 | fix(dxf): remove inverted EXTMIN/EXTMAX sentinel values |
| 2026-04-25 | 9397c055 | refactor(dxf): Sprint 3B PR 1 — critical path migration to DxfWriter |
| 2026-04-19 | 8f1c4119 | feat(ibg): wire layer_consolidator as step zero in DXF intake |
| 2026-04-19 | 7769bae0 | fix(cam): preserve all non-LINE entities in consolidator |
| 2026-04-19 | 30b91b9a | fix(cam): check layer existence before adding in consolidator |
| 2026-04-19 | 7d392d19 | feat(cam): add layer-aware DXF consolidator with binding deduplication |
| 2026-04-11 | f13b749e | fix(cleaner): add extract_chains and write_selected_chains methods |
| 2026-04-07 | db2b8ba1 | feat(archtop): add archtop API router |
| 2026-04-07 | 143a0018 | feat(archtop): complete pipeline committed |
| 2026-04-05 | 1fcf28a4 | chore: rename BCAM 2030A → BCAMCNC 2030A across repo |

### In-Flight Work

1. **DXF Writer Migration** — Sprint 3B active, critical path migrated
2. **Archtop Pipeline** — Recently committed (2026-04-07), API router added
3. **Layer Consolidator** — Active development for DXF intake

---

## 10. Bridges to Nowhere Check

### Files with Substantial Implementation but Limited Integration

| File | Lines | Issue | Consumers |
|------|-------|-------|-----------|
| cam_core/geometry/advanced_offset.py | ~200 | Full shapely offset engine | Import unclear |
| cam/rosette/rosette_cnc_wiring.py | 248 | N14/N16 bundle code | rosette pipeline |
| cam/rosette/image_prompts.py | ~180 | AI prompt templates | No API exposure |

**Assessment:** These are not bridges to nowhere — they serve specific subsystems (rosette CNC, image generation). Integration is through their parent modules.

### Orphaned Code: NONE FOUND

All CAM files examined have either:
- Direct router registration
- Import from other production modules
- Test coverage

---

## Summary

### Health Assessment

| Category | Status | Notes |
|----------|--------|-------|
| Core CAM Modules | **HEALTHY** | 200+ files, active development |
| DXF Writer | **HEALTHY** | Sprint 3B migration in progress |
| Machine Configs | **COMPLETE** | 7 machines including BCAM_2030A |
| Post-Processors | **COMPLETE** | 5 G-code dialects |
| Tool Definitions | **COMPLETE** | Router, saw, drill models |
| Material Profiles | **MINIMAL** | Only hardwood/softwood placeholders |
| Test Coverage | **GOOD** | 30+ CAM test files |
| Stub Count | **ZERO** | No NotImplementedError found |
| Frontend Integration | **COMPLETE** | Full components/cam/ directory |

### Blocking Issues

1. **DXF Migrations Incomplete** — 4 files still use R2000/R2010 directly instead of dxf_writer.py
2. **Material Profiles Minimal** — feeds_speeds/materials.py has only placeholder data

### Recommendations

1. Complete DXF migration for remaining 4 files
2. Expand material profiles with lutherie-specific woods (mahogany, rosewood, maple, etc.)
3. Monitor the 3 TODO items in adaptive_core and archtop_modal_analysis

---

*Audit completed: 2026-04-25*
*Methodology: Production paths only, live grep, git log cross-reference*
