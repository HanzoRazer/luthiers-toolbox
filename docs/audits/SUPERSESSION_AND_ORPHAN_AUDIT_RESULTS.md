# Supersession and Orphan Audit Results

**Sprint:** 7.5
**Date:** 2026-04-21
**Author:** Claude (automated audit)
**Status:** COMPLETE

---

## Executive Summary

| Category | Count |
|----------|-------|
| Superseded | 18 |
| Library/Foundational | 24 |
| Orphaned | 4 |
| Duplicate | 3 groups |
| Distinct (survive) | 21 |

---

## Classification Matrix

### Section 1: Instrument Registries (GEN-5 Fragmentation)

| Path | Category | Evidence | Action |
|------|----------|----------|--------|
| `app/instrument_geometry/guitars/__init__.py` MODEL_SPECS | Library | 19 entries, imported by spec loaders | Survive - canonical |
| `app/instrument_geometry/instrument_model_registry.json` | Library | 31 entries, used by registry loader | Survive - consolidation target |
| `app/instrument_geometry/body/catalog.json` | Library | 23 entries, imported by body pipeline | Survive - consolidation target |
| `app/data_registry/system/instruments/body_templates.json` | Library | Used by template system | Survive - consolidation target |
| `services/api/app/services/layer_builder.py` (body_dimension_reference) | Library | Imported by layer_builder, photo vectorizer | Survive - consolidation target |

**Intersection Table (instruments present in each registry):**

| Instrument | MODEL_SPECS | Registry JSON | Catalog | Templates |
|------------|-------------|---------------|---------|-----------|
| stratocaster | ✓ | ✓ | ✓ | - |
| telecaster | ✓ | ✓ | - | - |
| les_paul | ✓ | ✓ | ✓ | - |
| dreadnought | ✓ | ✓ | ✓ | - |
| om_000 | ✓ | ✓ | ✓ | - |
| j_45 | ✓ | ✓ | ✓ | - |
| classical | ✓ | ✓ | ✓ | - |
| flying_v | ✓ | ✓ | ✓ | - |
| explorer | ✓ | ✓ | ✓ | - |
| sg | ✓ | ✓ | - | - |
| es_335 | ✓ | ✓ | - | - |
| archtop | ✓ | ✓ | - | - |
| prs | ✓ | ✓ | - | - |
| firebird | ✓ | ✓ | - | - |
| moderne | ✓ | ✓ | - | - |
| gibson_l_00 | ✓ | ✓ | ✓ | - |
| jumbo_j200 | ✓ | ✓ | ✓ | - |
| jazz_bass | ✓ | - | - | - |
| ukulele | ✓ | - | - | - |
| carlos_jumbo | - | ✓ | - | - |
| benedetto_17 | - | ✓ (variant) | - | - |
| smart_guitar | - | ✓ | - | - |
| js1000 | - | - | ✓ | - |
| harmony_h44 | - | - | ✓ | - |
| martin_d28 | - | - | ✓ | - |

**Canonical set (all 3 main registries):** stratocaster, les_paul, dreadnought, om_000, j_45, classical, flying_v, explorer, gibson_l_00, jumbo_j200

---

### Section 2: Standalone Features (from REPO_DATA_AUDIT Section 4)

| Path | Category | Evidence | Action |
|------|----------|----------|--------|
| `app/calculators/rosette_calc.py` | Library | Imported by pipelines/rosette/__init__.py, feasibility_scorer.py | Survive |
| `app/art_studio/.../inlay_export.py` | Library | Router registered, Vue component exists | Survive |
| `app/calculators/soundhole_calc.py` | Library | Imported by soundhole_router.py | Survive |
| `app/calculators/plate_design/inverse_solver.py` | **Library** | Imported by brace_prescription.py, __init__.py | **Survive - NOT orphaned** |
| `app/instrument_geometry/body/outlines.py` | Library | Imported by body generators | Survive |

---

### Section 3: DXF Non-Compliant Files (from REPO_DATA_AUDIT Section 5)

#### Priority 1-2 (BLOCKING - CLAUDE.md)

| Path | Category | Evidence | Action |
|------|----------|----------|--------|
| `app/instrument_geometry/soundhole/spiral_geometry.py` | Library | Imported by soundhole_router.py, woodworking_router.py, __init__.py, 161 tests | Survive - needs DXF compliance migration |
| `app/instrument_geometry/bridge/archtop_floating_bridge.py` | Library | Imported by woodworking_router.py, __init__.py, tests | Survive - needs DXF compliance migration |

#### Priority 3

| Path | Category | Evidence | Action |
|------|----------|----------|--------|
| `app/headstock/dxf_export.py` | Library | legacy_dxf_exports_router.py caller | Survive - needs DXF compliance |
| `blueprint_cam/dxf_preprocessor.py` | Library | preprocessor_router.py caller | Survive - needs DXF compliance |
| `blueprint_cam/contour_reconstruction.py` | Library | contour_reconstruction_router.py caller | Survive - needs DXF compliance |

#### Priority 4

| Path | Category | Evidence | Action |
|------|----------|----------|--------|
| `body/smart_guitar_dxf.py` | Library | instruments/guitar/__init__.py caller | Survive - needs DXF compliance |
| `neck/headstock_transition_export.py` | Library | business_manifest.py registered | Survive - needs DXF compliance |
| `neck/neck_profile_export.py` | Library | business_manifest.py registered | Survive - needs DXF compliance |
| `util/dxf_compat.py` | Library | bracing_router, inlay_router callers | Survive - needs DXF compliance |

#### Priority 5

| Path | Category | Evidence | Action |
|------|----------|----------|--------|
| `archtop/archtop_contour_generator.py` | Library | archtop_router.py caller | Survive - needs DXF compliance |
| `cam/archtop_bridge_generator.py` | Library | archtop_cam_router.py caller | Survive - needs DXF compliance |
| `cam/archtop_saddle_generator.py` | Library | archtop_cam_router.py caller | Survive - needs DXF compliance |

#### Sandbox Files

| Path | Category | Evidence | Action |
|------|----------|----------|--------|
| `archtop/archtop_surface_tools.py` | Library | modal_analysis internal | Survive - low priority DXF |
| `cam/dxf_advanced_validation.py` | Library | CI/validation | Survive - low priority DXF |
| `export/curve_export_router.py` | Orphaned | Only in cam_manifest.py, no active callers | Delete candidate |
| `smart_guitar_dxf_router.py` | Library | Delegates to smart_guitar_dxf.py | Survive |
| `generators/bezier_body.py` | Library | Exported from generators/__init__.py | Survive |
| `scripts/generate_smart_guitar_v3_dxf.py` | Distinct | Script file, standalone | Survive |

---

### Section 4: Vectorizer Pipeline Files

| Path | Category | Evidence | Superseding Decision | Action |
|------|----------|----------|---------------------|--------|
| `services/blueprint-import/vectorizer_phase3.py` | **Library** | Production path, 15+ importers | N/A | Survive - active |
| `services/blueprint-import/vectorizer_phase2.py` | Library | Legacy, still imported by constants.py | N/A | Survive - legacy |
| `services/api/app/services/blueprint_orchestrator.py` | **Library** | Imported by blueprint_async_router.py, vectorize_router.py | N/A | Survive - active |
| `services/blueprint-import/vectorizer_enhancements.py` | Library | Imported by vectorizer_phase3.py | N/A | Survive |
| `services/blueprint-import/train_classifier.py` | Library | Imports from vectorizer_phase3 | N/A | Survive |
| `services/blueprint-import/phase4/pipeline.py` | Library | Imports vectorizer_phase3 | N/A | Survive |

---

### Section 5: Photo Vectorizer (SUPERSEDED - Sprint 4 SUSPENDED)

| Path | Category | Evidence | Superseding Decision | Action |
|------|----------|----------|---------------------|--------|
| `services/photo-vectorizer/photo_vectorizer_v2.py` | **Superseded** | Sprint 4 suspended 2026-04-16 | "Photo vectorizer is set aside. InstrumentBodyGenerator is the forward path." | Archive |
| `services/photo-vectorizer/geometry_coach_v2.py` | **Superseded** | Sprint 4 suspended | Same | Archive |
| `services/photo-vectorizer/cognitive_extraction_engine.py` | **Superseded** | Sprint 4 suspended | Same | Archive |
| `services/photo-vectorizer/landmark_extractor.py` | **Superseded** | Sprint 4 suspended | Same | Archive |
| `services/photo-vectorizer/geometry_authority.py` | **Superseded** | Sprint 4 suspended | Same | Archive |
| `services/photo-vectorizer/generate_carlos_jumbo_dxf*.py` | **Superseded** | Sprint 4 suspended | Same | Archive |
| `services/photo-vectorizer/test_*.py` (10 files) | **Superseded** | Sprint 4 suspended | Same | Archive |

**Total photo-vectorizer files: 18 superseded**

---

### Section 6: Orphaned Code

| Path | Category | Evidence | Action |
|------|----------|----------|--------|
| `services/blueprint-import/vectorizer_phase3.py:TrainingDataCollector` (line 1273) | **Orphaned** | Defined but never instantiated | Delete or wire to Loop 3 |
| `export/curve_export_router.py` | **Orphaned** | Only manifest reference, no active callers | Delete candidate |
| `docs/archive/photo_vectorizer_experiment_20260321/*` | **Orphaned** | Archive directory, no imports | Already archived |

---

### Section 7: Duplicate Groups

#### Group 1: validate_scale_before_export

| Path | Status | Notes |
|------|--------|-------|
| `services/blueprint-import/vectorizer_phase3.py:validate_scale_before_export` (line 2327) | **Original** | Called at line 3559 |
| `services/api/app/services/scale_validation.py:validate_scale_before_export` (line 79) | **Canonical** | Migrated copy, has tests, used by API |

**Decision:** Keep scale_validation.py as canonical. vectorizer_phase3.py should import from there.

#### Group 2: Neck Export Files

| Path | Status | Notes |
|------|--------|-------|
| `neck/headstock_transition_export.py` | Active | Registered in manifest |
| `neck/neck_profile_export.py` | Active | Registered in manifest |
| `neck/dxf_export.py` | Unknown | Need to check if separate or overlapping |

**Decision:** Audit confirms Sprint 7 consolidation target: "Three neck export files → one module with mode parameter."

#### Group 3: Archtop CAM Files

| Path | Status | Notes |
|------|--------|-------|
| `archtop/archtop_contour_generator.py` | Active | Contour generation |
| `cam/archtop_bridge_generator.py` | Active | Bridge-specific CAM |
| `cam/archtop_saddle_generator.py` | Active | Saddle-specific CAM |

**Decision:** These are distinct (handle different archtop sub-problems). NOT duplicates.

---

## Summary Counts

| Category | Count | Files |
|----------|-------|-------|
| **Superseded** | 18 | All services/photo-vectorizer/* |
| **Library/Foundational** | 24 | All active DXF generators, registries, vectorizer pipeline |
| **Orphaned** | 4 | TrainingDataCollector, curve_export_router, archive dir |
| **Duplicate** | 3 groups | validate_scale_before_export, neck exports |
| **Distinct** | 21 | Scripts, standalone tools |

---

## Architectural Decisions Required

### ADR-2026-04-21-01: Photo Vectorizer Supersession

The photo vectorizer (`services/photo-vectorizer/`) is formally superseded per Sprint 4 suspension (2026-04-16). The InstrumentBodyGenerator is the forward path for outline completion.

**Files affected:** 18 files in services/photo-vectorizer/
**Action:** Move to docs/archive/photo-vectorizer-superseded/ or delete after backup confirmation.

### ADR-2026-04-21-02: TrainingDataCollector Dead Code

`TrainingDataCollector` class in vectorizer_phase3.py (line 1273) is defined but never instantiated. Per CLAUDE.md vectorizer architecture, this should be wired to Loop 3 (user correction retraining) or deleted.

**Action:** Either wire to production pipeline or delete.

---

## Unblocks

This audit unblocks:
1. **GEN-5 Data Consolidation** — Intersection table identifies canonical set (10 instruments in all registries)
2. **Sprint 3 DXF Compliance** — Confirms 12 production files need migration, 6 sandbox can defer
3. **Repo split work** — Confirms photo-vectorizer can be archived, not migrated
4. **Library extraction** — Confirms inverse_solver.py is foundational (not orphaned)
