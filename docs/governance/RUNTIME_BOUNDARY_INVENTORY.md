# Runtime Boundary Inventory

**Sprint**: Runtime Boundary Follow-Through  
**Date**: 2026-05-20  
**Status**: INVENTORY COMPLETE — Patch Plan Proposed

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

### Authority Chains (from registry)

1. **geometry_authority_chain**: Blueprint → IBG → BOE → CadSemantics → TopologyBuilder → ShellValidation → Translator
2. **semantic_authority_chain**: Vocabulary Registry → Domain Owner → Operational Implementation → Runtime Consumer
3. **export_lifecycle_chain**: Export Request → Feasibility Check → Validation → Translation → Authorization Gate → Machine Output

---

## Path Classifications

### Category 1: Governed Export Paths (COMPLIANT)

These paths use the governed export lifecycle or dxf_compat layer:

| Path | Uses dxf_compat | Uses Lifecycle Orchestrator | Risk |
|------|-----------------|----------------------------|------|
| `art_studio/services/generators/inlay_export.py` | ✓ | — | LOW |
| `calculators/inlay_calc.py` | ✓ | — | LOW |
| `cam/dxf_writer.py` | ✓ | — | LOW |
| `cam/unified_dxf_cleaner.py` | ✓ | — | LOW |
| `cam/layer_consolidator.py` | ✓ | — | LOW |
| `cam/dxf_consolidator.py` | ✓ | — | LOW |
| `cam/archtop_bridge_generator.py` | ✓ | — | LOW |
| `cam/archtop_saddle_generator.py` | ✓ | — | LOW |
| `cam/archtop/archtop_contour_generator.py` | ✓ | — | LOW |
| `cam/archtop/archtop_surface_tools.py` | ✓ | — | LOW |
| `routers/neck/*.py` (3 files) | ✓ | — | LOW |
| `routers/headstock/dxf_export.py` | ✓ | — | LOW |
| `routers/export/curve_export_router.py` | ✓ | — | LOW |
| `routers/blueprint_cam/contour_reconstruction.py` | ✓ | — | LOW |
| `routers/blueprint_cam/dxf_preprocessor.py` | ✓ | — | LOW |
| `services/layered_dxf_writer.py` | ✓ | — | LOW |

### Category 2: Direct ezdxf Bypass (BYPASS RISK)

These paths call `ezdxf.new()` directly, bypassing dxf_compat:

| Path | Line | Version Used | Risk | Issue |
|------|------|--------------|------|-------|
| `instrument_geometry/body/smart_guitar_dxf.py` | 297 | R2000 | MEDIUM | Direct ezdxf.new(), no dxf_compat |
| `routers/instruments/guitar/smart_guitar_dxf_router.py` | 77 | R2010 | MEDIUM | Direct ezdxf.new(), no dxf_compat |

### Category 3: Saveas Without Lifecycle (PROVENANCE GAP)

These paths emit DXF via `.saveas()` without going through governed export lifecycle:

| Path | Classification | Provenance Tracked | Risk |
|------|----------------|-------------------|------|
| `generators/bezier_body.py:472` | artifact generation | NO | MEDIUM |
| `instrument_geometry/soundhole/spiral_geometry.py:311` | artifact generation | NO | LOW (debug output) |
| `instrument_geometry/body/ibg/body_contour_solver.py:777,808` | IBG output | NO | HIGH |
| `instrument_geometry/body/ibg/arc_reconstructor.py:1116,1279,1303` | IBG output | NO | HIGH |
| `routers/dxf_preflight_router.py:301,303` | preflight | NO | LOW (validation only) |
| `routers/blueprint_cam/dxf_geometry_correction.py:306` | blueprint CAM | NO | MEDIUM |
| `services/text_reinsertion.py:318` | service | NO | LOW |
| `cam/line_deduplicator.py:290` | CAM utility | NO | LOW |

### Category 4: CAM Dispatch Paths

| Module | Dispatch Pattern | Governance Integration | Risk |
|--------|-----------------|----------------------|------|
| `cam/export_lifecycle_orchestrator.py` | `dispatch_preview()`, `dispatch_export_object()` | FULL | LOW |
| `cam/cam_operation_registry.py` | registry-driven | FULL | LOW |
| `cam/routers/toolpath/*.py` | toolpath dispatch | PARTIAL | MEDIUM |
| `cam/archtop/archtop_pipeline.py` | pipeline dispatch | PARTIAL | MEDIUM |

### Category 5: Runtime Provenance Paths

| Module | Provenance Recording | Risk |
|--------|---------------------|------|
| `cam/runtime_provenance/recorder.py` | DEFINED | LOW |
| `cam/runtime_provenance/contracts.py` | DEFINED | LOW |
| `instrument_geometry/body/ibg/body_evidence_candidate.py` | DEFINED (authority + provenance) | LOW |

---

## Bypass Risks Summary

### Risk 1: Direct ezdxf Bypass (2 files)

**Files**:
- `instrument_geometry/body/smart_guitar_dxf.py:297`
- `routers/instruments/guitar/smart_guitar_dxf_router.py:77`

**Issue**: Direct `ezdxf.new()` calls bypass the PROTECTED_PRODUCTION_BASELINE dxf_compat layer.

**Authority chain violation**: No version validation through dxf_compat.validate_version().

**Recommendation**: Replace direct calls with `dxf_compat.create_document()`.

### Risk 2: IBG Output Without Provenance (5 saveas calls)

**Files**:
- `instrument_geometry/body/ibg/body_contour_solver.py` (2 calls)
- `instrument_geometry/body/ibg/arc_reconstructor.py` (3 calls)

**Issue**: IBG geometry outputs bypass the export lifecycle and emit DXF without provenance metadata attachment.

**Authority chain violation**: geometry_authority_chain terminates at TopologyBuilder without going through Translation → Authorization Gate.

**Recommendation**: Wire IBG outputs through export lifecycle OR attach provenance metadata at saveas boundary.

### Risk 3: CAM Toolpath Routers Partial Integration

**Files**: `cam/routers/toolpath/*.py` (multiple)

**Issue**: Some toolpath routers dispatch directly without full lifecycle orchestration.

**Authority chain violation**: export_lifecycle_chain steps may be skipped.

**Recommendation**: Audit each router for lifecycle gate compliance.

### Risk 4: Blueprint CAM Saveas Without Lifecycle

**Files**:
- `routers/blueprint_cam/dxf_geometry_correction.py:306`
- `routers/blueprint_cam/contour_reconstruction.py:392,512`

**Issue**: Blueprint processing emits DXF without governed export lifecycle.

**Authority chain violation**: Export without Feasibility Check or Authorization Gate.

**Recommendation**: These are processing utilities, not user-facing exports. Add metadata comments clarifying intent vs. marking as intermediate artifacts.

---

## Classification Summary

| Category | Count | Risk Level |
|----------|-------|------------|
| Governed (dxf_compat or lifecycle) | 16+ files | LOW |
| Direct ezdxf bypass | 2 files | MEDIUM |
| Saveas without lifecycle | 8+ locations | MEDIUM-HIGH |
| CAM dispatch partial | 2+ modules | MEDIUM |
| Provenance defined | 3+ modules | LOW |

---

## Patch Plan (Proposed)

### Phase 1: Direct Bypass Remediation (LOW RISK)

1. **smart_guitar_dxf.py:297**
   - Change: `ezdxf.new("R2000")` → `dxf_compat.create_document("R2000")`
   - Add import: `from app.util.dxf_compat import create_document`
   - Test: Run existing smart_guitar tests

2. **smart_guitar_dxf_router.py:77**
   - Change: `ezdxf.new("R2010")` → `dxf_compat.create_document("R2010")`
   - Add import: `from app.util.dxf_compat import create_document`
   - Test: Run router integration tests

### Phase 2: IBG Provenance Attachment (REQUIRES REVIEW)

**Blocked by**: IBG provenance model ratification (per memory: "IBG blocked until provenance model ratified")

1. Define IBG-specific provenance attachment point
2. Wire IBG outputs through minimal provenance wrapper
3. Attach authority_state and lineage hash to saveas outputs

### Phase 3: CAM Router Audit (DEFERRED)

1. Inventory all CAM toolpath routers
2. Classify each as: preview-only, export-ready, or machine-output
3. Wire export-ready routers through lifecycle orchestrator

### Phase 4: Blueprint CAM Classification (DOCUMENTATION ONLY)

1. Add docstring annotations clarifying artifact type (intermediate vs. final)
2. No code changes — processing utilities remain as-is

---

## Phase 1 Implementation Status

### Phase 1A: Direct Bypass Remediation — COMPLETE

**Commit**: d5033799

| File | Change | Status |
|------|--------|--------|
| `instrument_geometry/body/smart_guitar_dxf.py:297` | `ezdxf.new("R2000")` → `create_document("R2000")` | DONE |
| `routers/instruments/guitar/smart_guitar_dxf_router.py:77` | `ezdxf.new("R2010")` → `create_document("R2010")` | DONE |

### Phase 1B: Comprehensive DXF Export Inventory — COMPLETE

See: [EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md](./EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md)

**Findings**:
- 55+ DXF export paths identified
- 25+ compat-governed paths (production)
- 1 lifecycle-governed path (export_lifecycle_router)
- 5 IBG blocked provenance calls
- 9 test fixtures (excluded)
- 13 R&D/script paths (excluded)

### Phase 1C: Classification Matrix Document — COMPLETE

Created canonical classification matrix with:
- HTML markers for machine parsing
- Lifecycle Status column for each row
- Risk level and disposition tracking
- Cross-reference to this inventory

### Phase 1D: Lifecycle Guard Baseline — COMPLETE

**Created**:
- `scripts/governance/validate_export_lifecycle_matrix.py` — Matrix validator
- `tests/governance/test_validate_export_lifecycle_matrix.py` — 24 tests

**Integrated**:
- Added to `check_all.py` as warning-only check at CI tier

**Validator behavior**:
- Parses HTML markers first, falls back to headings with warning
- Validates required sections exist
- Validates production rows have required columns
- Validates BLOCKED_PROVENANCE rows not marked LIFECYCLE_GOVERNED
- Warnings exit 0, structural failures exit 1
- `--strict` promotes warnings to exit 1

---

## Acceptance Criteria Met

- [x] Boundary inventory complete
- [x] Bypass risks listed with file:line
- [x] Patch plan proposed (Phase 1-4)
- [x] No code changes until reviewed
- [x] Phase 1A: Direct bypasses fixed
- [x] Phase 1B: Comprehensive inventory complete
- [x] Phase 1C: Classification matrix created
- [x] Phase 1D: Validator script and tests created, integrated to CI

---

## Next Action

Phase 1 complete. Phase 2 (IBG provenance attachment) blocked pending provenance model ratification.
