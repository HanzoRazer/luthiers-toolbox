# Export Lifecycle Classification Matrix

**Sprint**: Runtime Boundary Follow-Through  
**Phase**: 2B  
**Date**: 2026-05-21  
**Status**: GUARD ROLLOUT READINESS

**Cross-reference**: [RUNTIME_BOUNDARY_INVENTORY.md](./RUNTIME_BOUNDARY_INVENTORY.md)

---

## Purpose

Canonical classification matrix for DXF/export lifecycle behavior.
Provides stable baseline for Phase 2 provenance work.
Machine-parseable via HTML markers; human-readable via section headings.

---

## Legend

### Lifecycle Status Labels

| Label | Meaning |
|-------|---------|
| `LIFECYCLE_GOVERNED` | Uses export_lifecycle_orchestrator with full gate validation |
| `COMPAT_ONLY` | Uses dxf_compat but no lifecycle orchestration |
| `DIRECT_SAVE_GAP` | Direct saveas without lifecycle gate (read-modify-write) |
| `BLOCKED_PROVENANCE` | IBG paths awaiting provenance model ratification |
| `TEST_ONLY` | Test fixtures, excluded from production enforcement |
| `R_AND_D_EXCLUDED` | R&D sandbox, excluded from enforcement |

### Export Type

| Code | Meaning |
|------|---------|
| `dxf-create-save` | Uses create_document() or DxfWriter, calls saveas() |
| `dxf-read-modify-save` | Uses ezdxf.readfile(), modifies, calls saveas() |
| `dxf-create-only` | Uses create_document(), caller handles save |
| `dxf-preview` | Creates doc for validation, no save |
| `dxf-write-only` | Receives existing doc/object, writes/saves it |

### Document Creation Path

| Code | Meaning |
|------|---------|
| `create_document` | Uses dxf_compat.create_document() |
| `DxfWriter` | Uses cam/dxf_writer.py (internally uses create_document) |
| `ezdxf.readfile` | Reads existing DXF file |
| `ezdxf.new` | Direct ezdxf.new() — bypass (should not exist in production) |
| `caller` | Document passed in by caller |

### Runtime Callable

| Code | Meaning |
|------|---------|
| `router_endpoint` | Directly reachable through FastAPI router |
| `runtime_service` | Callable by runtime service path |
| `script_only` | CLI/dev utility |
| `test_only` | Test fixtures |
| `excluded` | R&D/archive/user asset |

### Risk Level

| Level | Meaning |
|-------|---------|
| LOW | Lifecycle-governed or compat-governed with no gaps |
| LOW-MEDIUM | Compat-governed but direct saveas |
| MEDIUM | Direct saveas without lifecycle gate |
| HIGH | Direct ezdxf bypass in production |
| BLOCKED | Awaiting provenance model ratification |
| N/A | Test/R&D/excluded |

### Lifecycle Column Values

| Code | Meaning |
|------|---------|
| `Y` | Uses export_lifecycle_orchestrator |
| `N` | No lifecycle orchestration |
| `GUARD` | Uses dxf_lifecycle_guard (Phase 2A+) |

### Guard Status (Phase 2B)

| Code | Meaning |
|------|---------|
| `GUARD_ADDED` | Lifecycle guard integrated |
| `GUARD_CANDIDATE` | Ready for guard integration |
| `ORCHESTRATOR_CANDIDATE` | Candidate for full orchestrator adoption |
| `BLOCKED_PROVENANCE` | IBG, awaiting provenance ratification |
| `NOT_APPLICABLE` | Test/R&D/excluded, no guard needed |

### Disposition

| Code | Meaning |
|------|---------|
| `no_action` | Already governed, no changes needed |
| `document_only` | Known boundary, document but no patch this phase |
| `blocked_provenance` | IBG, awaiting ratification |
| `test_fixture` | Test-only, allowed |
| `r_and_d_sandbox` | Excluded from enforcement |
| `guarded_2a` | Lifecycle guard added in Phase 2A |

---

<!-- SECTION:PRODUCTION_RUNTIME_EXPORTS -->
## Section 1: Production Runtime Exports

### 1A. Lifecycle-Governed (Full Orchestration)

| File | Export Type | Creation | Save | Compat | Lifecycle | Provenance | Callable | Risk | Lifecycle Status | Disposition | Guard Status |
|------|-------------|----------|------|--------|-----------|------------|----------|------|------------------|-------------|--------------|
| `routers/cam/export_lifecycle_router.py` | dxf-preview | — | — | Y | Y | NO | router_endpoint | LOW | LIFECYCLE_GOVERNED | no_action | NOT_APPLICABLE |

### 1B. Compat-Governed Router Endpoints

| File | Export Type | Creation | Save | Compat | Lifecycle | Provenance | Callable | Risk | Lifecycle Status | Disposition | Guard Status |
|------|-------------|----------|------|--------|-----------|------------|----------|------|------------------|-------------|--------------|
| `routers/neck/neck_profile_export.py` | dxf-create-save | create_document | Y | Y | N | NO | router_endpoint | LOW-MEDIUM | COMPAT_ONLY | no_action | GUARD_CANDIDATE |
| `routers/neck/headstock_transition_export.py` | dxf-create-save | create_document | Y | Y | N | NO | router_endpoint | LOW-MEDIUM | COMPAT_ONLY | no_action | GUARD_CANDIDATE |
| `routers/neck/export.py` | dxf-create-save | create_document | Y | Y | N | NO | router_endpoint | LOW-MEDIUM | COMPAT_ONLY | no_action | GUARD_CANDIDATE |
| `routers/headstock/dxf_export.py` | dxf-create-save | create_document | Y | Y | N | NO | router_endpoint | LOW-MEDIUM | COMPAT_ONLY | no_action | GUARD_CANDIDATE |
| `routers/export/curve_export_router.py` | dxf-create-save | create_document | Y | Y | N | NO | router_endpoint | LOW-MEDIUM | COMPAT_ONLY | no_action | GUARD_CANDIDATE |
| `routers/dxf_preflight_router.py` | dxf-create-save | create_document | Y | Y | N | NO | router_endpoint | LOW-MEDIUM | COMPAT_ONLY | no_action | GUARD_CANDIDATE |
| `routers/instruments/guitar/smart_guitar_dxf_router.py` | dxf-create-save | create_document | Y | Y | GUARD | NO | router_endpoint | LOW | COMPAT_ONLY | guarded_2a | GUARD_ADDED |

### 1C. Compat-Governed Blueprint/CAM Routers

| File | Export Type | Creation | Save | Compat | Lifecycle | Provenance | Callable | Risk | Lifecycle Status | Disposition | Guard Status |
|------|-------------|----------|------|--------|-----------|------------|----------|------|------------------|-------------|--------------|
| `routers/blueprint_cam/dxf_preprocessor.py` | dxf-create-save | create_document | Y | Y | N | NO | router_endpoint | LOW-MEDIUM | COMPAT_ONLY | no_action | ORCHESTRATOR_CANDIDATE |
| `routers/blueprint_cam/contour_reconstruction.py` | dxf-create-save | create_document | Y | Y | N | NO | router_endpoint | LOW-MEDIUM | COMPAT_ONLY | no_action | ORCHESTRATOR_CANDIDATE |
| `routers/blueprint_cam/dxf_geometry_correction.py` | dxf-read-modify-save | ezdxf.readfile | Y | Y | N | NO | router_endpoint | LOW-MEDIUM | DIRECT_SAVE_GAP | document_only | ORCHESTRATOR_CANDIDATE |

---

<!-- SECTION:COMPAT_ONLY_EXPORTS -->
## Section 2: Compat-Only / Lifecycle-Gap Exports

### 2A. CAM Services (Compat-Governed)

| File | Export Type | Creation | Save | Compat | Lifecycle | Provenance | Callable | Risk | Lifecycle Status | Disposition | Guard Status |
|------|-------------|----------|------|--------|-----------|------------|----------|------|------------------|-------------|--------------|
| `cam/dxf_writer.py` | dxf-create-save | create_document | Y | Y | N | NO | runtime_service | LOW-MEDIUM | COMPAT_ONLY | no_action | GUARD_CANDIDATE |
| `cam/unified_dxf_cleaner.py` | dxf-create-save | create_document | Y | Y | N | NO | runtime_service | LOW-MEDIUM | COMPAT_ONLY | no_action | GUARD_CANDIDATE |
| `cam/layer_consolidator.py` | dxf-create-save | create_document | Y | Y | N | NO | runtime_service | LOW-MEDIUM | COMPAT_ONLY | no_action | GUARD_CANDIDATE |
| `cam/dxf_consolidator.py` | dxf-create-save | create_document | Y | Y | N | NO | runtime_service | LOW-MEDIUM | COMPAT_ONLY | no_action | GUARD_CANDIDATE |
| `cam/line_deduplicator.py` | dxf-read-modify-save | ezdxf.readfile | Y | Y | N | NO | runtime_service | LOW-MEDIUM | DIRECT_SAVE_GAP | document_only | GUARD_CANDIDATE |
| `cam/dxf_advanced_validation.py` | dxf-preview | create_document | N | Y | N | NO | runtime_service | LOW | COMPAT_ONLY | no_action | NOT_APPLICABLE |

### 2B. CAM Archtop Generators

| File | Export Type | Creation | Save | Compat | Lifecycle | Provenance | Callable | Risk | Lifecycle Status | Disposition | Guard Status |
|------|-------------|----------|------|--------|-----------|------------|----------|------|------------------|-------------|--------------|
| `cam/archtop_bridge_generator.py` | dxf-create-save | create_document | Y | Y | N | NO | runtime_service | LOW-MEDIUM | COMPAT_ONLY | no_action | GUARD_CANDIDATE |
| `cam/archtop_saddle_generator.py` | dxf-create-save | create_document | Y | Y | N | NO | runtime_service | LOW-MEDIUM | COMPAT_ONLY | no_action | GUARD_CANDIDATE |
| `cam/archtop/archtop_surface_tools.py` | dxf-create-save | create_document | Y | Y | N | NO | runtime_service | LOW-MEDIUM | COMPAT_ONLY | no_action | GUARD_CANDIDATE |
| `cam/archtop/archtop_contour_generator.py` | dxf-create-save | create_document | Y | Y | N | NO | runtime_service | LOW-MEDIUM | COMPAT_ONLY | no_action | GUARD_CANDIDATE |

### 2C. Instrument Geometry Services

| File | Export Type | Creation | Save | Compat | Lifecycle | Provenance | Callable | Risk | Lifecycle Status | Disposition | Guard Status |
|------|-------------|----------|------|--------|-----------|------------|----------|------|------------------|-------------|--------------|
| `instrument_geometry/body/smart_guitar_dxf.py` | dxf-create-save | create_document | Y | Y | N | NO | runtime_service | LOW-MEDIUM | COMPAT_ONLY | no_action | GUARD_CANDIDATE |
| `instrument_geometry/soundhole/spiral_geometry.py` | dxf-create-save | DxfWriter | Y | Y | N | NO | runtime_service | LOW-MEDIUM | COMPAT_ONLY | no_action | GUARD_CANDIDATE |
| `generators/bezier_body.py` | dxf-create-save | DxfWriter | Y | Y | N | NO | runtime_service | LOW-MEDIUM | COMPAT_ONLY | no_action | GUARD_CANDIDATE |

### 2D. Art Studio / Inlay Services

| File | Export Type | Creation | Save | Compat | Lifecycle | Provenance | Callable | Risk | Lifecycle Status | Disposition | Guard Status |
|------|-------------|----------|------|--------|-----------|------------|----------|------|------------------|-------------|--------------|
| `art_studio/services/generators/inlay_export.py` | dxf-create-only | create_document | N | Y | N | NO | runtime_service | LOW | COMPAT_ONLY | no_action | NOT_APPLICABLE |
| `calculators/inlay_calc.py` | dxf-create-only | create_document | N | Y | N | NO | runtime_service | LOW | COMPAT_ONLY | no_action | NOT_APPLICABLE |

### 2E. Other Services

| File | Export Type | Creation | Save | Compat | Lifecycle | Provenance | Callable | Risk | Lifecycle Status | Disposition | Guard Status |
|------|-------------|----------|------|--------|-----------|------------|----------|------|------------------|-------------|--------------|
| `services/layered_dxf_writer.py` | dxf-create-save | create_document | Y | Y | N | NO | runtime_service | LOW-MEDIUM | COMPAT_ONLY | no_action | GUARD_CANDIDATE |
| `services/text_reinsertion.py` | dxf-read-modify-save | ezdxf.readfile | Y | Y | N | NO | runtime_service | LOW-MEDIUM | DIRECT_SAVE_GAP | document_only | GUARD_CANDIDATE |

---

<!-- SECTION:BLOCKED_PROVENANCE -->
## Section 3: IBG Blocked Provenance Candidates

These paths use DxfWriter (compat-governed) but are blocked pending provenance model ratification.

| File | Export Type | Creation | Save | Compat | Lifecycle | Provenance | Callable | Risk | Lifecycle Status | Disposition | Guard Status |
|------|-------------|----------|------|--------|-----------|------------|----------|------|------------------|-------------|--------------|
| `instrument_geometry/body/ibg/body_contour_solver.py:777` | dxf-create-save | DxfWriter | Y | Y | N | BLOCKED | runtime_service | BLOCKED | BLOCKED_PROVENANCE | blocked_provenance | BLOCKED_PROVENANCE |
| `instrument_geometry/body/ibg/body_contour_solver.py:808` | dxf-create-save | DxfWriter | Y | Y | N | BLOCKED | runtime_service | BLOCKED | BLOCKED_PROVENANCE | blocked_provenance | BLOCKED_PROVENANCE |
| `instrument_geometry/body/ibg/arc_reconstructor.py:1116` | dxf-create-save | DxfWriter | Y | Y | N | BLOCKED | runtime_service | BLOCKED | BLOCKED_PROVENANCE | blocked_provenance | BLOCKED_PROVENANCE |
| `instrument_geometry/body/ibg/arc_reconstructor.py:1279` | dxf-create-save | DxfWriter | Y | Y | N | BLOCKED | runtime_service | BLOCKED | BLOCKED_PROVENANCE | blocked_provenance | BLOCKED_PROVENANCE |
| `instrument_geometry/body/ibg/arc_reconstructor.py:1303` | dxf-create-save | DxfWriter | Y | Y | N | BLOCKED | runtime_service | BLOCKED | BLOCKED_PROVENANCE | blocked_provenance | BLOCKED_PROVENANCE |

**Blocking condition**: IBG provenance model ratification required before Phase 2 work can proceed.

---

<!-- SECTION:TEST_FIXTURES -->
## Section 4: Test Fixtures

| File | Export Type | Creation | Compat | Provenance | Callable | Risk | Lifecycle Status | Disposition | Guard Status |
|------|-------------|----------|--------|------------|----------|------|------------------|-------------|--------------|
| `tests/test_dxf_to_grbl_endpoint_smoke.py` | dxf-create-save | ezdxf.new | N | N/A | test_only | N/A | TEST_ONLY | test_fixture | NOT_APPLICABLE |
| `tests/test_dxf_preprocessor.py` | dxf-create-save | ezdxf.new | N | N/A | test_only | N/A | TEST_ONLY | test_fixture | NOT_APPLICABLE |
| `tests/test_dxf_geometry_correction.py` | dxf-create-save | ezdxf.new | N | N/A | test_only | N/A | TEST_ONLY | test_fixture | NOT_APPLICABLE |
| `tests/test_dxf_advanced_validation_smoke.py` | dxf-create-only | ezdxf.new | N | N/A | test_only | N/A | TEST_ONLY | test_fixture | NOT_APPLICABLE |
| `tests/test_contour_reconstruction.py` | dxf-create-save | ezdxf.new | N | N/A | test_only | N/A | TEST_ONLY | test_fixture | NOT_APPLICABLE |
| `tests/test_blueprint_cam_integration.py` | dxf-create-save | ezdxf.new | N | N/A | test_only | N/A | TEST_ONLY | test_fixture | NOT_APPLICABLE |
| `tests/e2e_cam_system.py` | dxf-create-save | ezdxf.new | N | N/A | test_only | N/A | TEST_ONLY | test_fixture | NOT_APPLICABLE |
| `tests/test_dxf_compat_r12_compliance.py` | dxf-create-save | create_document | Y | N/A | test_only | N/A | TEST_ONLY | test_fixture | NOT_APPLICABLE |
| `tests/test_dxf_writer.py` | dxf-write-only | caller | Y | N/A | test_only | N/A | TEST_ONLY | test_fixture | NOT_APPLICABLE |

---

<!-- SECTION:SCRIPTS -->
## Section 5: Scripts

| File | Export Type | Creation | Compat | Provenance | Callable | Risk | Lifecycle Status | Disposition | Guard Status |
|------|-------------|----------|--------|------------|----------|------|------------------|-------------|--------------|
| `scripts/generate_smart_guitar_v3_dxf.py` | dxf-create-save | ezdxf.new | N | N/A | script_only | N/A | R_AND_D_EXCLUDED | document_only | NOT_APPLICABLE |

---

<!-- SECTION:BLUEPRINT_IMPORT -->
## Section 6: Blueprint-Import Surface

| File | Export Type | Creation | Compat | Provenance | Callable | Risk | Lifecycle Status | Disposition | Guard Status |
|------|-------------|----------|--------|------------|----------|------|------------------|-------------|--------------|
| `blueprint-import/vectorizer_phase3.py` | dxf-create-save | create_document | Y | N/A | excluded | N/A | R_AND_D_EXCLUDED | document_only | NOT_APPLICABLE |
| `blueprint-import/dxf_compat.py` | — | — | Y | N/A | excluded | N/A | R_AND_D_EXCLUDED | document_only | NOT_APPLICABLE |
| `blueprint-import/dxf_postprocessor.py` | dxf-create-save | create_document | Y | N/A | excluded | N/A | R_AND_D_EXCLUDED | document_only | NOT_APPLICABLE |
| `blueprint-import/phase4/annotations/exporter.py` | dxf-create-save | create_document | Y | N/A | excluded | N/A | R_AND_D_EXCLUDED | document_only | NOT_APPLICABLE |

---

<!-- SECTION:R_AND_D_SANDBOX -->
## Section 7: R&D Sandbox (Photo-Vectorizer)

| File | Export Type | Creation | Compat | Provenance | Callable | Risk | Lifecycle Status | Disposition | Guard Status |
|------|-------------|----------|--------|------------|----------|------|------------------|-------------|--------------|
| `photo-vectorizer/ai_render_extractor.py` | dxf-create-save | ezdxf.new | N | N/A | excluded | N/A | R_AND_D_EXCLUDED | r_and_d_sandbox | NOT_APPLICABLE |
| `photo-vectorizer/edge_to_dxf.py` | dxf-create-save | ezdxf.new | N | N/A | excluded | N/A | R_AND_D_EXCLUDED | r_and_d_sandbox | NOT_APPLICABLE |
| `photo-vectorizer/march_pipeline_restore.py` | dxf-create-save | ezdxf.new | N | N/A | excluded | N/A | R_AND_D_EXCLUDED | r_and_d_sandbox | NOT_APPLICABLE |
| `photo-vectorizer/light_line_body_extractor.py` | dxf-create-save | ezdxf.new | N | N/A | excluded | N/A | R_AND_D_EXCLUDED | r_and_d_sandbox | NOT_APPLICABLE |
| `photo-vectorizer/generate_carlos_jumbo_dxf.py` | dxf-create-save | ezdxf.new | N | N/A | excluded | N/A | R_AND_D_EXCLUDED | r_and_d_sandbox | NOT_APPLICABLE |
| `photo-vectorizer/generate_carlos_jumbo_dxf_enhanced.py` | dxf-create-save | ezdxf.new | N | N/A | excluded | N/A | R_AND_D_EXCLUDED | r_and_d_sandbox | NOT_APPLICABLE |
| `photo-vectorizer/photo_vectorizer_v2.py` | dxf-create-save | ezdxf.new | N | N/A | excluded | N/A | R_AND_D_EXCLUDED | r_and_d_sandbox | NOT_APPLICABLE |
| `photo-vectorizer/photo_silhouette_extractor.py` | dxf-create-save | ezdxf.new | N | N/A | excluded | N/A | R_AND_D_EXCLUDED | r_and_d_sandbox | NOT_APPLICABLE |
| `photo-vectorizer/multi_view_reconstructor.py` | dxf-create-save | create_document | Y | N/A | excluded | N/A | R_AND_D_EXCLUDED | r_and_d_sandbox | NOT_APPLICABLE |

---

## Current Runtime Boundary State

### What Is Governed Today

| Governance Level | Description | Count |
|------------------|-------------|-------|
| **LIFECYCLE_GOVERNED** | Uses export_lifecycle_orchestrator with full gate validation | 1 module |
| **COMPAT_ONLY** | Uses dxf_compat.create_document() or DxfWriter | 25+ files |

All production DXF document creation now goes through dxf_compat (Phase 1A resolved direct bypasses).

### What Remains Compat-Only (No Lifecycle Gate)

| Category | Files | Lifecycle Status |
|----------|-------|------------------|
| Router endpoints | 10+ | COMPAT_ONLY |
| CAM services | 10+ | COMPAT_ONLY |
| Instrument geometry | 3+ | COMPAT_ONLY |
| Read-modify-write paths | 3 | DIRECT_SAVE_GAP |

These paths use dxf_compat for document creation but do not go through export_lifecycle_orchestrator.
No provenance metadata is attached at save time.

### What Is Blocked Pending Provenance Ratification

| Category | Files | Saveas Calls | Lifecycle Status |
|----------|-------|--------------|------------------|
| IBG outputs | 2 | 5 | BLOCKED_PROVENANCE |

IBG paths (`body_contour_solver.py`, `arc_reconstructor.py`) use DxfWriter (compat-governed) but require provenance attachment before Phase 2 work can proceed.

**Blocking condition**: IBG provenance model ratification.

### What Remains Intentionally Excluded

| Category | Files | Lifecycle Status | Reason |
|----------|-------|------------------|--------|
| Test fixtures | 9 | TEST_ONLY | Test-only, ezdxf.new allowed per TEST_FIXTURE_ALLOWED |
| Scripts | 1 | R_AND_D_EXCLUDED | CLI/dev utility, standalone |
| Blueprint-import | 4 | R_AND_D_EXCLUDED | Import surface, not production runtime |
| Photo-vectorizer | 9 | R_AND_D_EXCLUDED | R&D sandbox, excluded from enforcement |

---

## Phase 2 Provenance Work Baseline

This matrix provides the stable inventory for Phase 2 provenance attachment work:

| Phase 2 Target | Current Lifecycle Status | Required |
|----------------|--------------------------|----------|
| IBG outputs | BLOCKED_PROVENANCE | provenance model ratification |
| Router endpoints | COMPAT_ONLY | lifecycle gate integration |
| CAM services | COMPAT_ONLY | lifecycle gate integration |

Phase 2 scope depends on IBG provenance model ratification and governance escalation decisions.

---

## Summary Counts by Lifecycle Status

| Lifecycle Status | Production | Test | Blueprint | R&D | Total |
|------------------|------------|------|-----------|-----|-------|
| LIFECYCLE_GOVERNED | 1 | — | — | — | 1 |
| COMPAT_ONLY | 22+ | 2 | — | — | 24+ |
| DIRECT_SAVE_GAP | 3 | — | — | — | 3 |
| BLOCKED_PROVENANCE | 5 calls | — | — | — | 5 |
| TEST_ONLY | — | 9 | — | — | 9 |
| R_AND_D_EXCLUDED | — | — | 4 | 9 | 13 |
| **Total** | 31+ | 11 | 4 | 9 | 55+ |
