# Luthiers Toolbox Repository Data Audit

**Generated:** 2026-04-16

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Files Scanned | 1,847 |
| Instruments with Complete E2E Pipeline | 3 |
| Instruments with Partial Pipeline | 8 |
| Instruments Stub Only | 6 |
| Orphaned Data Files | 12 |
| Phantom Assets | 8 |
| DXF Compliant Files | 6 |
| DXF Non-Compliant Files | 24 |
| Standalone Features Integrated | 3 |
| Standalone Features Disconnected | 3 |
| GEN Phases Complete | 2 |
| GEN Phases Incomplete | 4 |

---

## Section 1: Instrument Data Sources

### Primary Data Registries

| File | Type | Records | Status | Notes |
|------|------|---------|--------|-------|
| `instrument_model_registry.json` | json | 31 | active | Master registry with COMPLETE/PARTIAL/STUB/ASSETS_ONLY flags |
| `body/catalog.json` | json | 23 | active | Point counts vary 10-5451. Some phantom DXF refs |
| `body_dimension_reference.json` | json | 18 | active | Vectorizer scale validation. Waist position by family |
| `instrument_specs.py` | py | 18 | active | Central body validation. BODY_DIMENSIONS, FEATURE_ROUTES |
| `curvature_correction.py` | py | 11 | active | MEASURED_RADII for outline reconstruction |
| `guitars/__init__.py` | py | 19 | active | MODEL_SPECS registry with get_spec() functions |

### Detailed Spec Files

| File | Instruments | Lines | Notes |
|------|-------------|-------|-------|
| `specs/gibson_les_paul.json` | les_paul | 591 | Full outline (669 pts), carved top, CNC ops OP20-OP63 |
| `specs/carlos_jumbo.json` | carlos_jumbo | 591 | Vectorizer: 2,011 primitives, 35 bracing features |
| `specs/jumbo_archtop.json` | jumbo_archtop | 485 | Carlos Jumbo scale + Benedetto construction |
| `specs/gibson_explorer.json` | gibson_explorer | 448 | Variants: original_1958, reissue_76. DXF needs refinement |
| `specs/gibson_flying_v_1958.json` | flying_v | 261 | Split-V headstock, V-shaped body |
| `specs/fender_stratocaster.json` | stratocaster | 221 | Variants: vintage, modern, 24fret |
| `specs/gibson_melody_maker.json` | melody_maker | 135 | Student model, single-cutaway |
| `body/specs/smart_guitar_v1.json` | smart_guitar | 1,026 | Full IoT: Arduino, RPi 5, sensors, DAW integration |

### Model Files

| File | Instruments | Notes |
|------|-------------|-------|
| `models/benedetto_17.json` | benedetto_17 | AI vision extracted. 482.6mm x 431.8mm |
| `models/cuatro_venezolano.json` | cuatro_venezolano | 234.6mm x 321.6mm, 4 strings, 17 frets |
| `models/cuatro_puertorriqueno.json` | cuatro_puertorriqueno | 280mm x 380mm, 10 strings (5 courses) |
| `models/flying_v_1958.json` | flying_v | **STUB** - 25 lines, schema mismatch with loader.py |

### Generator Configs

| File | Instruments | Notes |
|------|-------------|-------|
| `generators/stratocaster_config.py` | stratocaster | CNC toolpaths, tool configs, machine profiles |
| `generators/lespaul_config.py` | les_paul | Uses inches (legacy). Set-neck with 4° angle |

---

## Section 2: End-to-End Pipeline Status

### Pipeline Summary

```
INSTRUMENT          | E2E STATUS  | DATA SOURCES | DXF COMPLIANT
--------------------|-------------|--------------|---------------
stratocaster        | complete    | 9/9          | N/A
telecaster          | partial     | 7/9          | N/A
les_paul            | complete    | 9/9          | NO (ezdxf)
gibson_sg           | partial     | 6/9          | N/A
gibson_explorer     | partial     | 8/9          | N/A
flying_v            | partial     | 9/9          | N/A
melody_maker        | stub        | 7/9          | N/A
es335               | stub        | 6/9          | N/A
smart_guitar        | partial     | 5/9          | NO (R2000)
eds1275             | missing     | 0/9          | N/A
dreadnought         | complete    | 8/9          | N/A
om_000              | partial     | 8/9          | N/A
jumbo               | partial     | 7/9          | N/A
classical           | partial     | 8/9          | N/A
j45                 | partial     | 8/9          | N/A
cuatro              | stub        | 7/9          | N/A
benedetto_17        | partial     | 5/9          | YES
```

### Complete Pipelines (3)

| Instrument | Generator | Endpoint | Output |
|------------|-----------|----------|--------|
| stratocaster | `stratocaster_body_generator.py` | `/instruments/guitar/electric-body/generate/strat` | G-code |
| les_paul | `lespaul_body_generator.py` | `/cam/les_paul/body/gcode` | G-code |
| dreadnought | `acoustic_body_generator.py` | `/cam/acoustic/dreadnought/body/gcode` | G-code |

### Missing Pipeline (1)

| Instrument | Missing |
|------------|---------|
| eds1275 | No spec data, no generator, no endpoint. Double-neck requires specialized geometry. |

### Partial Pipelines - Missing Steps

| Instrument | Missing Steps |
|------------|---------------|
| telecaster | No dedicated body generator, No G-code endpoint |
| gibson_sg | No body generator, No G-code endpoint |
| gibson_explorer | DXF needs refinement (24 pts), No body generator |
| flying_v | Schema mismatch with loader.py, No body generator class |
| smart_guitar | No body generator, DXF uses R2000, Pending electronics cavity |
| om_000 | Outline 5,451 pts but no DXF confirmed |
| jumbo | G-code not confirmed working |
| classical | G-code not confirmed working |
| j45 | Body outline only 30 pts (coarse) |
| benedetto_17 | Not integrated with body_generator, Carved top needs specialized CAM |

### Stub Only (6)

| Instrument | Missing Steps |
|------------|---------------|
| melody_maker | No body generator, No API endpoint, No G-code path |
| es335 | Semi-hollow requires specialized generator, No API endpoint |
| cuatro | No body generator, No endpoint, Two variants need consolidation |

---

## Section 3: Generator Consolidation Status (GEN-1 to GEN-6)

| Phase | Description | Status | Evidence |
|-------|-------------|--------|----------|
| **GEN-1** | Connect spec stubs to project creation | **NOT STARTED** | POST /api/projects does not seed with model_id defaults |
| **GEN-2** | BodyConfig + acoustic_body_style_id | **PARTIAL** | acoustic_body_style_id exists but usage limited; BodyConfig not standalone |
| **GEN-3** | from_project() factories on generators | **COMPLETE** | stratocaster (line 92), lespaul (line 44), acoustic (line 206), dispatcher calls at 108/113/118 |
| **GEN-4** | CAM REST endpoints reading project_id | **PARTIAL** | Endpoints exist but project_id integration incomplete |
| **GEN-5** | Consolidate spec stubs + registry | **NOT STARTED** | 19 MODEL_SPECS vs 31 registry entries. No single source of truth. |
| **GEN-6** | Acoustic body orchestration | **COMPLETE** | generate_outline(), generate_perimeter_gcode(), generate_soundhole_gcode(), generate_binding_channel_gcode(). 8 styles supported. |

### GEN-5 Data Fragmentation Detail

- `guitars/__init__.py` MODEL_SPECS: **19 entries**
- `instrument_model_registry.json`: **31 entries**
- Multiple dimension sources with conflicting values
- `flying_v_1958.json` has schema mismatch with loader.py

---

## Section 4: Standalone Feature Connectivity

| Feature | File | API Endpoint | Vue Component | Connected to body_generator | DXF Standard | Status |
|---------|------|--------------|---------------|------------------------------|--------------|--------|
| Rosette Generator | `calculators/rosette_calc.py` | `/api/art/rosette/*` | `ArtStudioRosette.vue` | NO | ezdxf inline (R12) | **standalone** |
| Headstock Inlay | `art_studio/.../inlay_export.py` | `/api/art/inlay/*` | `ArtStudioInlay.vue` | NO | ezdxf (R12) | **standalone** |
| Soundhole Generator | `calculators/soundhole_calc.py` | `/api/instrument/soundhole` | - | NO | dxf_writer.py | **integrated** |
| Inverse Math Solver | `calculators/plate_design/inverse_solver.py` | - | - | NO | - | **orphaned** |
| Body Outline Generator | `instrument_geometry/body/outlines.py` | `/instruments/guitar/electric-body/*` | - | YES | - | **integrated** |
| Gore/Helmholtz Calculator | `calculators/soundhole_calc.py` | `/api/instrument/soundhole` | - | NO | - | **integrated** |

---

## Section 5: DXF Writer Compliance

### Compliance Summary

| Status | Count |
|--------|-------|
| Compliant (R12) | 6 |
| Non-Compliant | 24 |
| **Compliance Rate** | **20%** |

### Compliant Files (6)

| File | Format | Notes |
|------|--------|-------|
| `app/cam/dxf_writer.py` | R12 | **THE STANDARD.** LINE only, 3dp precision |
| `app/services/layered_dxf_writer.py` | R12 | Blueprint pipeline. POLYLINE2D + LINE fallback |
| `app/cam/unified_dxf_cleaner.py` | R12 | Blueprint import cleaner |
| `app/routers/neck/export.py` | R12 | Neck export, LINE entities |
| `app/calculators/inlay_calc.py` | R12 | Inlay calculator, LINE entities |
| `app/routers/dxf_preflight_router.py` | R12 | Validation router |

### Non-Compliant Production Files (12) - Require Compliance Work

| Priority | File | Format | Called By | Notes |
|----------|------|--------|-----------|-------|
| **1** | `soundhole/spiral_geometry.py` | R2000 | soundhole_router.py | **CLAUDE.md blocking.** 161 tests. |
| **2** | `bridge/archtop_floating_bridge.py` | R2000 | woodworking_router.py | **CLAUDE.md blocking.** |
| **3** | `headstock/dxf_export.py` | R2010 | legacy_dxf_exports_router.py | **CRITICAL VIOLATION.** User-facing. |
| **3** | `blueprint_cam/dxf_preprocessor.py` | R2000 | preprocessor_router.py | Active vectorizer pipeline |
| **3** | `blueprint_cam/contour_reconstruction.py` | R2000 | contour_reconstruction_router.py | Active vectorizer pipeline |
| **4** | `body/smart_guitar_dxf.py` | R2000 | instruments/guitar/__init__.py | Smart Guitar DXF export |
| **4** | `neck/headstock_transition_export.py` | R2010 | business_manifest.py | Registered in manifest |
| **4** | `neck/neck_profile_export.py` | R2010 | business_manifest.py | Registered in manifest |
| **4** | `util/dxf_compat.py` | variable | bracing_router, inlay_router | Art studio compatibility |
| **5** | `archtop/archtop_contour_generator.py` | R2010 | archtop_router.py | Archtop CAM |
| **5** | `cam/archtop_bridge_generator.py` | R2010 | archtop_cam_router.py | Archtop CAM |
| **5** | `cam/archtop_saddle_generator.py` | R2010 | archtop_cam_router.py | Archtop CAM |

### Sandbox Files (6) - Can Defer

| File | Format | Reason |
|------|--------|--------|
| `archtop/archtop_surface_tools.py` | R2010 | Internal to modal_analysis, no router |
| `cam/dxf_advanced_validation.py` | R2010 | CI/validation only |
| `export/curve_export_router.py` | R2010 | No active callers found |
| `smart_guitar_dxf_router.py` | R2010 | Delegates to smart_guitar_dxf.py |
| `generators/bezier_body.py` | R2010 | No router uses DXF output |
| `scripts/generate_smart_guitar_v3_dxf.py` | R2010 | Script file |

### Discard Files (6) - Test Files

- `tests/test_dxf_advanced_validation_smoke.py`
- `tests/test_contour_reconstruction.py`
- `tests/test_dxf_geometry_correction.py`
- `tests/test_dxf_preprocessor.py`
- `tests/test_blueprint_cam_integration.py`
- `tests/test_bezier_body_generator.py`

---

## Section 6: Instrument Coverage Matrix

### Full Coverage (9/9)

| Instrument | Dedicated Spec |
|------------|----------------|
| stratocaster | `specs/fender_stratocaster.json` |
| les_paul | `specs/gibson_les_paul.json` |
| flying_v | `specs/gibson_flying_v_1958.json` |

### High Coverage (8/9)

| Instrument | Missing | Conflicts |
|------------|---------|-----------|
| gibson_explorer | body_templates_json | DXF has 24 pts (needs refinement) |
| dreadnought | dedicated_spec_json | Multiple sources with inconsistent values |
| om_000 | body_templates_json | - |
| classical | dedicated_spec_json | - |
| j45 | measured_radii | Body outline only 30 pts (coarse) |

### Medium Coverage (7/9)

| Instrument | Missing | Conflicts |
|------------|---------|-----------|
| telecaster | body_outlines_json, catalog_json | - |
| melody_maker | body_templates_json, model_specs_generators | - |
| jumbo | body_templates_json, dedicated_spec_json | - |
| cuatro | body_templates_json, model_specs_generators | Two variants not consolidated |

### Low Coverage (5-6/9)

| Instrument | Coverage | Phantom Assets |
|------------|----------|----------------|
| gibson_sg | 6/9 | NO |
| es335 | 6/9 | NO |
| smart_guitar | 5/9 | YES |
| benedetto_17 | 5/9 | YES |

### No Coverage (0/9)

| Instrument | Notes |
|------------|-------|
| eds1275 | Zero data sources. Double-neck requires specialized geometry. |

---

## Section 7: Documentation Map (Top 20 by Size)

| Path | Size | Topic | Status |
|------|------|-------|--------|
| `docs/governance/FENCE_ARCHITECTURE.md` | 78.5 KB | architecture | stale |
| `docs/LUTHERIE_MATH.md` | 72.9 KB | other | active |
| `docs/handoffs/VECTORIZER_PIPELINE_HANDOFF.md` | 55.4 KB | vectorizer | active |
| `docs/GAP_ANALYSIS_MASTER.md` | 50.9 KB | other | active |
| `Luthiers_Toolbox_Platform_Architecture.md` | 49.3 KB | architecture | stale |
| `SPRINTS.md` | 45.6 KB | sprints | stale |
| `docs/handoffs/J45_VINE_OF_LIFE_DESIGN_HANDOFF.md` | 43.5 KB | architecture | active |
| `docs/handoffs/24_FRET_STRATOCASTER_DESIGN_HANDOFF.md` | 41.6 KB | architecture | active |
| `docs/ROSETTE_WHEEL_ENGINE_INTEGRATION_PLAN.md` | 37.7 KB | generator | stale |
| `docs/PHASE6_CAD_GEOMETRY_HANDOFF.md` | 36.4 KB | handoff | active |
| `docs/CHIEF_ENGINEER_HANDOFF.md` | 35.8 KB | handoff | stale |
| `docs/UNFINISHED_REMEDIATION_EFFORTS.md` | 35.8 KB | other | stale |
| `docs/ROUTER_MAP.md` | 33.9 KB | api | stale |
| `docs/THIN_STROKE_PDF_HANDOFF.md` | 29.6 KB | handoff | active |
| `docs/ROSETTE_CONSOLIDATION_HANDOFF.md` | 27.3 KB | generator | stale |
| `docs/BLUEPRINT_VECTORIZER_ARCHITECTURE.md` | 26.4 KB | architecture | stale |
| `SPRINT.md` | 19.1 KB | sprints | active |
| `docs/VECTORIZER_PIPELINE_AUDIT.md` | 18.4 KB | vectorizer | active |
| `CLAUDE.md` | 17.9 KB | guardrails | active |

### Documentation by Status

| Status | Count |
|--------|-------|
| Active | 11 |
| Stale | 9 |

---

## Top 5 Gaps by Impact

1. **DXF Writer Standard Bypass (24 files)** — 80% of DXF-producing files bypass `dxf_writer.py` and use R2000/R2010 with LWPOLYLINE. This caused Fusion 360 freezes. All CAM exports should route through the R12 standard.

2. **GEN-5 Data Source Fragmentation** — 19 MODEL_SPECS entries vs 31 instrument_model_registry entries. Multiple overlapping dimension sources with no single source of truth. `flying_v_1958.json` has schema mismatch with `loader.py`.

3. **Missing EDS-1275 Double-Neck** — Zero data sources, no spec, no body generator. Double-neck requires specialized geometry handling not present in current architecture.

4. **GEN-1 Project Seeding Not Implemented** — `POST /api/projects` does not seed with model_id defaults. Projects created without instrument-specific configuration.

5. **Incomplete E2E Pipelines (8 instruments)** — telecaster, gibson_sg, gibson_explorer, flying_v, es335, om_000, jumbo, classical, j45 all have spec data but missing dedicated body generators or untested G-code paths.

---

## Recommended Priority Order for DXF Compliance

1. `spiral_geometry.py` — Listed in CLAUDE.md as blocking
2. `archtop_floating_bridge.py` — Listed in CLAUDE.md as blocking
3. `headstock/dxf_export.py` — Active user-facing export, R2010 violates standard
4. `blueprint_cam/dxf_preprocessor.py` — Part of active vectorizer pipeline
5. `blueprint_cam/contour_reconstruction.py` — Part of active vectorizer pipeline
6. `smart_guitar_dxf.py` — Smart Guitar priority
7. `neck/*.py` — Neck/headstock exports (2 files)
8. `dxf_compat.py` — Art studio compatibility layer
9. `archtop/*.py` — Archtop CAM files (3 files) - lower priority, partial pipeline
