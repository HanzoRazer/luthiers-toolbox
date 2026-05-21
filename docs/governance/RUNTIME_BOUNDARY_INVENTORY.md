# Runtime Boundary Inventory

**Sprint**: Runtime Boundary Follow-Through  
**Date**: 2026-05-21 (Phase 1B)  
**Status**: PHASE 1B INVENTORY TIGHTENING COMPLETE

## Purpose

Inventory runtime, export, serializer, CAM dispatch, and artifact-generation paths.
Identify where runtime bypasses governance discipline.
Produce patch plan before changing code.

---

## Governance Infrastructure Summary

### Working Boundary Guards

| Module | Location | Invariants | Status |
|--------|----------|------------|--------|
| Export Lifecycle Orchestrator | `cam/export_lifecycle_orchestrator.py` | `machine_output_generated=false`, `translator_output_generated=false`, `machine_ready=false` | ENFORCED |
| Translation Artifact | `cam/translation_artifact.py` | `execution_supported=false`, `executable_payload_present=false`, `machine_output_present=false` | ENFORCED |
| Execution Quarantine | `cam/translator_execution_quarantine.py` | 7H invariants: all execution flags false, all escalation flags true | ENFORCED |
| Runtime Provenance | `cam/runtime_provenance/contracts.py` | Append-only lineage, deterministic hashing | DEFINED |
| DXF Compat Layer | `util/dxf_compat.py` | PROTECTED_PRODUCTION_BASELINE, R12-R18 version control | PROTECTED |
| DxfWriter Class | `cam/dxf_writer.py` | Uses dxf_compat internally | PROTECTED |

### Authority Chains (from registry)

1. **geometry_authority_chain**: Blueprint → IBG → BOE → CadSemantics → TopologyBuilder → ShellValidation → Translator
2. **semantic_authority_chain**: Vocabulary Registry → Domain Owner → Operational Implementation → Runtime Consumer
3. **export_lifecycle_chain**: Export Request → Feasibility Check → Validation → Translation → Authorization Gate → Machine Output

### Classification Levels

| Level | Definition | Risk |
|-------|------------|------|
| lifecycle-governed | Uses dxf_compat + export_lifecycle_orchestrator | LOW |
| compat-governed | Uses dxf_compat.create_document() or DxfWriter | LOW-MEDIUM |
| read-modify-write | Uses ezdxf.readfile(), modifies, saves | LOW-MEDIUM |
| direct-saveas | Creates doc without dxf_compat, calls saveas | MEDIUM |
| direct-ezdxf-bypass | Uses ezdxf.new() directly in production | HIGH |
| blocked_provenance | IBG paths awaiting provenance model ratification | BLOCKED |
| test_fixture | Test-only, allowed per TEST_FIXTURE_ALLOWED | N/A |
| blueprint_import | Blueprint/vectorizer import surface | document_only |
| r_and_d_sandbox | Photo-vectorizer, excluded from enforcement | N/A |

---

## Complete DXF Lifecycle Path Inventory

### A. Lifecycle-Governed Paths (LOW risk)

Only one module uses full export lifecycle orchestration:

| File | Line | Pattern | Disposition |
|------|------|---------|-------------|
| `routers/cam/export_lifecycle_router.py` | 18+ | imports export_lifecycle_orchestrator | no_action |

### B. Compat-Governed Paths (LOW-MEDIUM risk)

These use `create_document()` from dxf_compat or DxfWriter class:

| File | Line | create_document | saveas | Disposition |
|------|------|-----------------|--------|-------------|
| `cam/dxf_writer.py` | 56, 160 | ✓ | ✓ | no_action |
| `cam/unified_dxf_cleaner.py` | 216, 358, 265, 409 | ✓ | ✓ | no_action |
| `cam/layer_consolidator.py` | 179, 239 | ✓ | ✓ | no_action |
| `cam/dxf_consolidator.py` | 243, 273 | ✓ | ✓ | no_action |
| `cam/archtop_bridge_generator.py` | 55, 111 | ✓ | ✓ | no_action |
| `cam/archtop_saddle_generator.py` | 61, 137 | ✓ | ✓ | no_action |
| `cam/archtop/archtop_surface_tools.py` | 147, 156 | ✓ | ✓ | no_action |
| `cam/archtop/archtop_contour_generator.py` | 135, 139, 171, 175 | ✓ | ✓ | no_action |
| `cam/dxf_advanced_validation.py` | 576, 604 | ✓ | — | no_action |
| `routers/neck/neck_profile_export.py` | 248 | ✓ | — | no_action |
| `routers/neck/headstock_transition_export.py` | 147 | ✓ | — | no_action |
| `routers/neck/export.py` | 36 | ✓ | — | no_action |
| `routers/headstock/dxf_export.py` | 274 | ✓ | — | no_action |
| `routers/export/curve_export_router.py` | 56 | ✓ | — | no_action |
| `routers/dxf_preflight_router.py` | 284, 301, 303 | ✓ | ✓ | no_action |
| `routers/blueprint_cam/dxf_preprocessor.py` | 133, 195, 321 | ✓ | ✓ | no_action |
| `routers/blueprint_cam/contour_reconstruction.py` | 374, 392, 453, 512 | ✓ | ✓ | no_action |
| `services/layered_dxf_writer.py` | 81, 115 | ✓ | ✓ | no_action |
| `instrument_geometry/body/smart_guitar_dxf.py` | 298, 595 | ✓ | ✓ | no_action (Phase 1A patched) |
| `routers/instruments/guitar/smart_guitar_dxf_router.py` | 80, 285 | ✓ | ✓ | no_action (Phase 1A patched) |
| `art_studio/services/generators/inlay_export.py` | 81 | ✓ | — | no_action |
| `calculators/inlay_calc.py` | 355, 390 | ✓ | — | no_action |

**Via DxfWriter class** (internally uses create_document):

| File | Line | Uses DxfWriter | saveas | Disposition |
|------|------|----------------|--------|-------------|
| `generators/bezier_body.py` | 460, 465, 472 | ✓ | ✓ | no_action |
| `instrument_geometry/soundhole/spiral_geometry.py` | 287, 296, 311 | ✓ | ✓ | no_action |

### C. Read-Modify-Write Paths (LOW-MEDIUM risk)

These read existing DXF, modify, and save — no document creation:

| File | Line | Pattern | Disposition |
|------|------|---------|-------------|
| `services/text_reinsertion.py` | 296, 318 | ezdxf.readfile() → saveas | document_only |
| `cam/line_deduplicator.py` | 197, 290 | ezdxf.readfile() → saveas | document_only |
| `routers/blueprint_cam/dxf_geometry_correction.py` | 87, 293, 306 | ezdxf.readfile() → saveas | document_only |

### D. IBG Paths — BLOCKED (pending provenance ratification)

These use DxfWriter (compat-governed) but require provenance attachment:

| File | Line | Pattern | Disposition |
|------|------|---------|-------------|
| `instrument_geometry/body/ibg/body_contour_solver.py` | 761, 768, 777, 808 | DxfWriter → saveas | blocked_provenance |
| `instrument_geometry/body/ibg/arc_reconstructor.py` | 1094, 1102, 1116, 1213, 1215, 1279, 1289, 1291, 1303 | DxfWriter → saveas | blocked_provenance |

**Note**: IBG provenance model ratification required before these can be patched.

### E. Scripts (document_only)

| File | Line | Pattern | Disposition |
|------|------|---------|-------------|
| `scripts/generate_smart_guitar_v3_dxf.py` | 83, 254 | ezdxf.new() → saveas | document_only (standalone script) |

### F. Test Fixtures (test_fixture — allowed)

| File | ezdxf.new() calls | saveas calls | Disposition |
|------|-------------------|--------------|-------------|
| `tests/test_dxf_to_grbl_endpoint_smoke.py` | 2 | 2 | test_fixture |
| `tests/test_dxf_preprocessor.py` | 7 | 7 | test_fixture |
| `tests/test_dxf_geometry_correction.py` | 2 | 2 | test_fixture |
| `tests/test_dxf_advanced_validation_smoke.py` | 7 | 0 | test_fixture |
| `tests/test_contour_reconstruction.py` | 10 | 10 | test_fixture |
| `tests/test_blueprint_cam_integration.py` | 3 | 3 | test_fixture |
| `tests/e2e_cam_system.py` | 1 | 1 | test_fixture |
| `tests/test_dxf_compat_r12_compliance.py` | 0 (uses create_document) | 1 | test_fixture |
| `tests/test_dxf_writer.py` | 0 | 1 | test_fixture |

### G. Blueprint-Import Surface (blueprint_import)

| File | Line | Pattern | Disposition |
|------|------|---------|-------------|
| `blueprint-import/vectorizer_phase3.py` | 2517, 2655, 2875, 110, 119 | create_document → saveas | document_only |
| `blueprint-import/dxf_compat.py` | 72, 89 | create_document definition | document_only |
| `blueprint-import/dxf_postprocessor.py` | 307, 386, 435, 526 | create_document → saveas | document_only |
| `blueprint-import/phase4/annotations/exporter.py` | 265, 332, 390 | create_document → saveas | document_only |

### H. R&D Sandbox — Excluded (r_and_d_sandbox)

| File | ezdxf.new() | saveas | Disposition |
|------|-------------|--------|-------------|
| `photo-vectorizer/ai_render_extractor.py` | 1 | 1 | r_and_d_sandbox |
| `photo-vectorizer/edge_to_dxf.py` | 5 | 5 | r_and_d_sandbox |
| `photo-vectorizer/march_pipeline_restore.py` | 2 | 2 | r_and_d_sandbox |
| `photo-vectorizer/light_line_body_extractor.py` | 1 | 1 | r_and_d_sandbox |
| `photo-vectorizer/generate_carlos_jumbo_dxf.py` | 1 | 1 | r_and_d_sandbox |
| `photo-vectorizer/generate_carlos_jumbo_dxf_enhanced.py` | 2 | 2 | r_and_d_sandbox |
| `photo-vectorizer/photo_vectorizer_v2.py` | 1 | 1 | r_and_d_sandbox |
| `photo-vectorizer/photo_silhouette_extractor.py` | 1 | 1 | r_and_d_sandbox |
| `photo-vectorizer/multi_view_reconstructor.py` | 0 (uses dxf_create_document) | 0 | r_and_d_sandbox |

---

## Summary by Classification

| Classification | Count | Risk | Action |
|----------------|-------|------|--------|
| lifecycle-governed | 1 module | LOW | no_action |
| compat-governed | 25+ files | LOW-MEDIUM | no_action |
| read-modify-write | 3 files | LOW-MEDIUM | document_only |
| direct-ezdxf-bypass (production) | 0 files | — | RESOLVED (Phase 1A) |
| blocked_provenance (IBG) | 2 files, 5 saveas | BLOCKED | blocked_provenance |
| scripts | 1 file | — | document_only |
| test_fixture | 9 files | — | test_fixture |
| blueprint_import | 4 files | — | document_only |
| r_and_d_sandbox | 9 files | — | r_and_d_sandbox (excluded) |

---

## Risk Summary

### Resolved Risks

| Risk | Status | Resolution |
|------|--------|------------|
| Direct ezdxf.new() in production | RESOLVED | Phase 1A patched 2 files |

### Active Risks

| Risk | Files | Status | Disposition |
|------|-------|--------|-------------|
| IBG saveas without provenance | 2 files, 5 calls | BLOCKED | Awaiting provenance model ratification |
| CAM toolpath router partial integration | Multiple | DEFERRED | Phase 3 scope |

### Documented (No Action)

| Category | Files | Disposition |
|----------|-------|-------------|
| Read-modify-write pattern | 3 files | document_only |
| Standalone scripts | 1 file | document_only |
| Blueprint-import surface | 4 files | document_only |
| Test fixtures | 9 files | test_fixture |
| R&D sandbox | 9 files | r_and_d_sandbox |

---

## Patch Plan

### Phase 1A: Direct Bypass Remediation — COMPLETE

**Status**: PATCHED 2026-05-21

- `instrument_geometry/body/smart_guitar_dxf.py:297` → `create_document("R2000")` ✓
- `routers/instruments/guitar/smart_guitar_dxf_router.py:77` → `create_document("R2010")` ✓

### Phase 1B: Inventory Tightening — COMPLETE

**Status**: COMPLETE 2026-05-21

- All DXF lifecycle paths inventoried with exact file:line
- Classifications assigned: lifecycle-governed, compat-governed, read-modify-write, blocked_provenance, test_fixture, blueprint_import, r_and_d_sandbox
- Risk levels assigned
- Dispositions documented

### Phase 2: IBG Provenance Attachment — BLOCKED

**Blocked by**: IBG provenance model ratification

Files requiring attention:
- `instrument_geometry/body/ibg/body_contour_solver.py:777,808`
- `instrument_geometry/body/ibg/arc_reconstructor.py:1116,1279,1303`

### Phase 3: CAM Router Audit — DEFERRED

Scope: Audit CAM toolpath routers for lifecycle gate compliance

### Phase 4: Blueprint CAM Classification — DEFERRED

Scope: Documentation only, no code changes

---

## Acceptance Criteria

### Phase 1A
- [x] No direct ezdxf.new() in production code (2 files patched)
- [x] DXF compatibility check passes

### Phase 1B
- [x] All .saveas() calls inventoried with file:line
- [x] All ezdxf.new() calls inventoried with file:line  
- [x] All create_document() calls inventoried with file:line
- [x] Classifications assigned (lifecycle-governed, compat-governed, etc.)
- [x] Risk levels assigned (LOW, LOW-MEDIUM, MEDIUM, HIGH, BLOCKED)
- [x] Dispositions documented (no_action, document_only, blocked_provenance, test_fixture, r_and_d_sandbox)
- [x] IBG paths clearly marked as blocked pending ratification
- [x] No behavior changes
