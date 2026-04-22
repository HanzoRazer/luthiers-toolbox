# Supersession and Orphan Audit Results — v3

**Sprint:** 7.5 (v3 methodology)
**Date:** 2026-04-21
**Author:** Claude (automated audit with per-file classification)
**Status:** COMPLETE

---

## Executive Summary

| Category | Count |
|----------|-------|
| Live (Blueprint path) | 9 |
| Suspended (Photo path) | 15 |
| Suspended (AI path) | 8 |
| Scaffolded (ML training layer) | 5 |
| Library/Foundational | 24 |
| Orphaned | 2 |
| Duplicate | 2 groups |
| Test/Replay infrastructure | 5 |
| Test files | 38 |

**Key revision from v1 → v3.1:** Photo vectorizer has THREE extraction paths with different statuses:

| Path | Entry Point | Status | Grade |
|------|-------------|--------|-------|
| **Blueprint path** | `source_type="blueprint"` | **LIVE** | 85-90% |
| **Photo path** | `source_type="photo"` (12-stage) | **Suspended** | L-1 poor |
| **AI path** | `source_type="ai"` (4-stage) | **Suspended** | AI renders poor |

**No code sharing with blueprint vectorizer.** `photo_vectorizer_v2.py` does not import from
`vectorizer_phase3.py`. They are separate pipelines.

**IBG wiring target:** `PhotoVectorizerV2.extract(source_type="blueprint")` — the established
interface for blueprint path output → IBG second-pass correction.

---

## Section 1: Photo Vectorizer Files (Per-File Classification)

**Note:** `photo_vectorizer_v2.py` is internally "Photo Vectorizer v3.0" with three extraction paths.
See `docs/audits/photo_vectorizer_path_distinction.md` for full documentation.

### Blueprint Path Files — LIVE (scanned PNG/JPEG → 85-90% grade)

| Path | Category | Role | Entry Point |
|------|----------|------|-------------|
| `photo_vectorizer_v2.py` | **Live** | Orchestrator | `extract(source_type="blueprint")` |
| `light_line_body_extractor.py` | **Live** | Core blueprint extraction | `_extract_blueprint_path()` |
| `edge_to_dxf.py` | **Live** | DXF output | Blueprint path output |
| `blueprint_view_segmenter.py` | **Live** | View segmentation | Blueprint path |
| `extract_body_grid_v5.py` | **Live** | Grid extraction (latest) | Blueprint path |
| `grid_classify.py` | **Live** | Grid classification | Blueprint path |
| `body_model.py` | **Live** | Shared data structures | All paths |
| `material_bom.py` | **Live** | BOM generation | All paths |
| `__init__.py` | **Live** | Package init | Module structure |

### Photo Path Files — SUSPENDED (L-1 historical images)

| Path | Category | Role | Suspension Reason |
|------|----------|------|-------------------|
| `body_isolation_stage.py` | **Suspended** | 12-stage body isolation | L-1 poor results |
| `body_isolation_result.py` | **Suspended** | Result data structure | Photo path dependency |
| `contour_stage.py` | **Suspended** | Contour extraction | Photo path dependency |
| `contour_election.py` | **Suspended** | Contour selection | Photo path dependency |
| `contour_plausibility.py` | **Suspended** | Plausibility scoring | Photo path dependency |
| `contour_debug_overlay.py` | **Suspended** | Debugging | Photo path dependency |
| `landmark_extractor.py` | **Suspended** | Landmark detection | Photo path dependency |
| `geometry_authority.py` | **Suspended** | Geometry validation | Photo path dependency |
| `multi_view_reconstructor.py` | **Suspended** | Multi-view handling | Photo path dependency |
| `photo_silhouette_extractor.py` | **Suspended** | Silhouette extraction | Photo path variant |
| `march_pipeline_restore.py` | **Suspended** | Pipeline restoration | Photo path |
| `extract_body_grid.py` | **Suspended** | Grid extraction v1 | Photo path |
| `extract_body_grid_v2.py` | **Suspended** | Grid extraction v2 | Photo path |
| `extract_body_grid_v3.py` | **Suspended** | Grid extraction v3 | Photo path |
| `extract_body_grid_v4.py` | **Suspended** | Grid extraction v4 | Photo path |

### AI Path Files — SUSPENDED (AI renders)

| Path | Category | Role | Suspension Reason |
|------|----------|------|-------------------|
| `ai_render_extractor.py` | **Suspended** | AI render extraction | AI renders poor results |
| `cognitive_extraction_engine.py` | **Suspended** | Cognitive AI path | AI path dependency |
| `cognitive_extractor.py` | **Suspended** | AI cognitive extraction | AI path dependency |
| `generate_carlos_jumbo_dxf.py` | **Suspended** | Carlos Jumbo AI script | AI path |
| `generate_carlos_jumbo_dxf_enhanced.py` | **Suspended** | Carlos Jumbo enhanced | AI path |
| `calibrate_carlos_jumbo.py` | **Suspended** | Carlos Jumbo calibration | AI path |
| `_experimental/ai_photo_path/ai_extractor.py` | **Suspended** | Experimental AI | Never production |
| `_experimental/ai_photo_path/__init__.py` | **Suspended** | Experimental AI | Never production |

### Test/Replay Infrastructure — LIVE

| Path | Category | Role |
|------|----------|------|
| `live_test_run.py` | **Live** | Test harness |
| `live_test_summary.py` | **Live** | Test summary |
| `replay_summary.py` | **Live** | Replay summary |
| `replay_objects.py` | **Live** | Replay data structures |
| `replay_fixture_loader.py` | **Live** | Fixture loading |

### Scaffolded — ML Training Layer (IBG Dependency)

| Path | Category | Evidence | Future Home |
|------|----------|----------|-------------|
| `geometry_coach_v2.py` | **Scaffolded** | ML coaching layer | TBD (not sg.coach) |
| `geometry_coach.py` | **Scaffolded** | Older coaching version | TBD |
| `vectorizer_phase3.py:TrainingDataCollector` (line 1273) | **Scaffolded** | Defined, not instantiated | Wire to Loop 3 |
| `vectorizer_phase3.py:FeedbackSystem` (line 1181) | **Scaffolded** | Instantiated in pipeline | Active but underutilized |
| `replay_execution.py` | **Scaffolded** | Replay for training | ML training |

### Replay Infrastructure

| Path | Category | Evidence | Notes |
|------|----------|----------|-------|
| `replay_summary.py` | **Live** | Replay summary | Testing infrastructure |
| `replay_objects.py` | **Live** | Replay data structures | imports photo_vectorizer_v2 |
| `replay_fixture_loader.py` | **Live** | Fixture loading | Testing infrastructure |

### Test Files (38 total — follow parent module classification)

| Pattern | Count | Classification follows |
|---------|-------|------------------------|
| `test_photo_vectorizer_v2*.py` | 1 | Live |
| `test_geometry_coach_v2*.py` | 7 | Scaffolded |
| `test_ai_render_extractor.py` | 1 | Suspended |
| `test_contour_*.py` | 6 | Live |
| `test_body_*.py` | 5 | Live |
| `test_carlos_jumbo*.py` | 1 | Suspended |
| `test_landmark_extractor.py` | 1 | Live |
| `test_blueprint_view_segmenter.py` | 1 | Live |
| `test_material_bom.py` | 1 | Live |
| `test_multi_view_reconstructor.py` | 1 | Live |
| `test_patch*.py` | 3 | Live |
| `test_plausibility_scorer.py` | 1 | Live |
| `test_real_image_comparison.py` | 1 | Live |
| `test_replay_*.py` | 4 | Live |
| `test_regression_replay_*.py` | 2 | Live |
| `test_coaching_convergence.py` | 1 | Scaffolded |
| `test_extract_coach_integration.py` | 1 | Scaffolded |

---

## Section 2: Vectorizer Pipeline Files

| Path | Category | Evidence | Action |
|------|----------|----------|--------|
| `services/blueprint-import/vectorizer_phase3.py` | **Live** | Production path, 15+ importers, v3.6 active | Survive |
| `services/blueprint-import/vectorizer_phase2.py` | **Live** | Legacy but constants.py imports | Survive |
| `services/api/app/services/blueprint_orchestrator.py` | **Live** | Imported by async router, vectorize_router | Survive |
| `services/blueprint-import/vectorizer_enhancements.py` | **Live** | Imported by vectorizer_phase3.py | Survive |
| `services/blueprint-import/train_classifier.py` | **Live** | Imports from vectorizer_phase3 | Survive |
| `services/blueprint-import/phase4/pipeline.py` | **Live** | Imports vectorizer_phase3 | Survive |

---

## Section 3: InstrumentBodyGenerator (IBG) Files

| Path | Category | Evidence | Future Home |
|------|----------|----------|-------------|
| `sandbox/arc_reconstructor/body_contour_solver.py` | **Library** | IBG completion library | New standalone repo (TBD) |
| `sandbox/arc_reconstructor/arc_reconstructor.py` | **Library** | Arc reconstruction | New standalone repo (TBD) |
| `sandbox/arc_reconstructor/reference_outline_bridge.py` | **Library** | Reference geometry | New standalone repo (TBD) |

**Architectural note:** IBG is analogous to `inverse_solver.py` — foundational code called by consumers (Body Outline Editor, vectorizer, photo-vectorizer), not exposed via direct API endpoint.

---

## Section 4: Confirmed Library/Foundational (unchanged from v1)

| Path | Category | Evidence | Action |
|------|----------|----------|--------|
| `app/calculators/plate_design/inverse_solver.py` | **Library** | Imported by brace_prescription.py, __init__.py | Survive |
| `app/calculators/rosette_calc.py` | **Library** | Imported by pipelines, feasibility_scorer | Survive |
| `app/calculators/soundhole_calc.py` | **Library** | Imported by soundhole_router.py | Survive |
| `app/instrument_geometry/soundhole/spiral_geometry.py` | **Library** | Active, 161 tests | Survive (DXF migration needed) |
| `app/instrument_geometry/bridge/archtop_floating_bridge.py` | **Library** | Active, router imports | Survive (DXF migration needed) |

---

## Section 5: Confirmed Orphaned

| Path | Category | Evidence | Action |
|------|----------|----------|--------|
| `export/curve_export_router.py` | **Orphaned** | Only manifest reference, no active callers | Delete candidate |
| `docs/archive/photo_vectorizer_experiment_20260321/*` | **Archived** | Archive directory | Already archived |

**Note:** `TrainingDataCollector` reclassified from Orphaned to **Scaffolded** — it's part of the planned ML training layer, not dead code.

---

## Section 6: Duplicate Groups (unchanged)

### Group 1: validate_scale_before_export

| Path | Status |
|------|--------|
| `services/api/app/services/scale_validation.py` | **Canonical** |
| `services/blueprint-import/vectorizer_phase3.py` (line 2327) | Duplicate — should import from canonical |

### Group 2: Neck Export Files

| Path | Status |
|------|--------|
| `neck/headstock_transition_export.py` | Active |
| `neck/neck_profile_export.py` | Active |
| `neck/dxf_export.py` | Needs audit |

**Consolidation target:** Three neck export files → one module with mode parameter.

---

## Section 7: Registry Intersection (unchanged from v1)

**Canonical set (in all 3 main registries):** stratocaster, les_paul, dreadnought, om_000, j_45, classical, flying_v, explorer, gibson_l_00, jumbo_j200

---

## Architectural Decisions Recorded

### ADR-2026-04-21-01: Vectorizer Ceiling Reversal (revised)

The 2026-04-16 ceiling declaration is **reversed**. Blueprint vectorizer v3.6 is the primary production path. Photo vectorizer is **Live** for scanned blueprint PNG/JPEG inputs at 85-90% grade; suspension applies only to AI renders and L-1 historical images.

### ADR-2026-04-21-02: IBG as Completion Library

InstrumentBodyGenerator is a **completion library** (no direct API endpoint), connected via imports. Analogous to `inverse_solver.py`. Scheduled for extraction to a new standalone repo (name TBD).

### ADR-2026-04-21-03: ML Training Layer Scaffolded

`TrainingDataCollector`, `FeedbackSystem`, `GeometryCoachV2` are **Scaffolded** (planned capability expansion), not Orphaned. These teach IBG instrument recognition from the 275-plan library.

### ADR-2026-04-21-04: sg.coach Deprecated

sg.coach repo is deprecated (2026-02-02, superseded by sg-agentd). Not a candidate for hosting ML training layer, IBG, or any forward-path component.

---

## Summary Counts (v3)

| Category | v1 Count | v3 Count | Delta |
|----------|----------|----------|-------|
| Superseded | 18 | 0 | -18 (reclassified) |
| Live | — | 42 | +42 |
| Live (Suspended scope) | — | 8 | +8 |
| Scaffolded | — | 5 | +5 |
| Library/Foundational | 24 | 24 | 0 |
| Orphaned | 4 | 2 | -2 (TrainingDataCollector → Scaffolded) |
| Duplicate | 3 groups | 2 groups | -1 |

---

## Unblocks

This audit unblocks:
1. **GEN-5 Data Consolidation** — 10 canonical instruments ready
2. **Sprint 3 DXF Compliance** — 12 production files confirmed for migration
3. **IBG extraction sprint** — files classified as Library, ready for new repo
4. **Photo vectorizer scanned-blueprint work** — NOT blocked, can proceed
5. **ML training layer planning** — Scaffolded files identified, home TBD
