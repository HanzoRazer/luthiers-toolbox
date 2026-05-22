# DXF Save/Write Lifecycle Guard Plan

**Sprint**: Runtime Boundary Follow-Through  
**Phase**: 1E → 2A  
**Date**: 2026-05-21  
**Status**: PHASE 2A COMPLETE — First Guard Integrated

**Cross-reference**: [EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md](./EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md)

---

## Purpose

Prepare the first safe implementation plan for DXF save/write lifecycle guards.

Phase 1E produced the patch plan. Phase 2A implemented the first guard integration.

---

## Phase 2A Implementation Status

**Completed**: 2026-05-21

| Deliverable | Status |
|-------------|--------|
| `app/util/dxf_lifecycle_guard.py` | CREATED |
| `DxfLifecycleContext` dataclass | IMPLEMENTED |
| `validate_dxf_lifecycle_context()` | IMPLEMENTED |
| `assert_dxf_lifecycle_context()` | IMPLEMENTED |
| `DxfLifecycleGuardError` | IMPLEMENTED |
| Unit tests (33 tests) | PASSING |
| First production integration | `smart_guitar_dxf_router.py` |

**Behavior**: Validation-only, no mutation, no logging, no side effects.

---

## Guard Definition

A lifecycle guard is a pre-save/export boundary check + audit hook.

**In scope**:
- Validate export context exists
- Validate declared export type
- Validate DXF version known
- Validate caller/source module known
- Optionally emit audit/log record

**Out of scope**:
- Full provenance stamping
- Document mutation
- Machine execution authorization

---

## Metadata Schema

Lightweight lifecycle context:

```python
@dataclass
class ExportLifecycleContext:
    source_module: str           # e.g., "routers.neck.neck_profile_export"
    export_type: str             # e.g., "dxf-create-save"
    dxf_version: str             # e.g., "R2000"
    lifecycle_status: str        # e.g., "COMPAT_ONLY"
    runtime_callable: str        # e.g., "router_endpoint"
    authority_context: str       # e.g., "user_request" | "pipeline_stage"
    provenance_status: str       # e.g., "NOT_ATTACHED" | "BLOCKED"
```

---

## Candidate Summary

### By Priority Group

| Priority | Group | COMPAT_ONLY | DIRECT_SAVE_GAP | Total |
|----------|-------|-------------|-----------------|-------|
| 1 | Router Endpoints | 9 | 1 | 10 |
| 2 | Runtime Services | 15 | 2 | 17 |
| 3 | Script-Only | — | — | 0 |
| — | Blocked (IBG) | — | — | 5 calls |
| — | Excluded (Test/R&D) | — | — | 23 |
| | **Total Candidates** | **24** | **3** | **27** |

### Save Pattern Analysis

| Pattern | Count | Guard Strategy |
|---------|-------|----------------|
| `doc.write(buf)` → StreamingResponse | 10 | Pre-write guard in each router |
| `DxfWriter.saveas(path)` | 12 | Guard in DxfWriter.saveas() |
| `DxfWriter.to_bytes()` | 3 | Guard in DxfWriter.to_bytes() |
| `doc.saveas(path)` direct | 3 | Pre-saveas guard in each module |

---

## Guard Insertion Points

### Priority 1: Router Endpoints (10 paths)

#### 1.1 COMPAT_ONLY Router Endpoints (9 paths)

All use the same pattern: `create_document()` → build geometry → `doc.write(buf)` → StreamingResponse

| # | File | Creation | Save Pattern | Guard Point | Disposition |
|---|------|----------|--------------|-------------|-------------|
| 1 | `routers/neck/neck_profile_export.py` | create_document | doc.write(buf) | before write | guard_only |
| 2 | `routers/neck/headstock_transition_export.py` | create_document | doc.write(buf) | before write | guard_only |
| 3 | `routers/neck/export.py` | create_document | doc.write(buf) | before write | guard_only |
| 4 | `routers/headstock/dxf_export.py` | create_document | doc.write(buf) | before write | guard_only |
| 5 | `routers/export/curve_export_router.py` | create_document | doc.write(buf) | before write | guard_only |
| 6 | `routers/dxf_preflight_router.py` | create_document | doc.write(buf) | before write | guard_only |
| 7 | `routers/instruments/guitar/smart_guitar_dxf_router.py` | create_document | doc.saveas(tmp) | before saveas | guard_only |
| 8 | `routers/blueprint_cam/dxf_preprocessor.py` | create_document | doc.write(buf) | before write | later_orchestrator_candidate |
| 9 | `routers/blueprint_cam/contour_reconstruction.py` | create_document | doc.write(buf) | before write | later_orchestrator_candidate |

**Guard insertion template for routers**:

```python
from app.cam.export_lifecycle_guard import validate_export_context

# Before doc.write(buf):
validate_export_context(
    source_module=__name__,
    export_type="dxf-create-save",
    dxf_version=doc.dxfversion,
    lifecycle_status="COMPAT_ONLY",
    runtime_callable="router_endpoint",
)
buf = io.BytesIO()
doc.write(buf)
buf.seek(0)
```

#### 1.2 DIRECT_SAVE_GAP Router Endpoints (1 path)

| # | File | Creation | Save Pattern | Guard Point | Disposition |
|---|------|----------|--------------|-------------|-------------|
| 10 | `routers/blueprint_cam/dxf_geometry_correction.py` | ezdxf.readfile | doc.saveas(tmp) | before saveas | later_orchestrator_candidate |

**Guard insertion for read-modify-write**:

```python
from app.cam.export_lifecycle_guard import validate_export_context

# Before doc.saveas():
validate_export_context(
    source_module=__name__,
    export_type="dxf-read-modify-save",
    dxf_version=doc.dxfversion,
    lifecycle_status="DIRECT_SAVE_GAP",
    runtime_callable="router_endpoint",
)
doc.saveas(tmp.name)
```

---

### Priority 2: Runtime Services (17 paths)

#### 2.1 DxfWriter (Central Control Point)

DxfWriter is used by 12+ paths. Guarding here provides leverage.

| # | File | Methods | Guard Point | Disposition |
|---|------|---------|-------------|-------------|
| 1 | `cam/dxf_writer.py` | saveas(), to_bytes() | in method body | guard_only |

**Guard insertion in DxfWriter**:

```python
class DxfWriter:
    def __init__(self, ..., lifecycle_context: Optional[ExportLifecycleContext] = None):
        self._lifecycle_context = lifecycle_context or ExportLifecycleContext(
            source_module="unknown",
            export_type="dxf-create-save",
            dxf_version=version,
            lifecycle_status="COMPAT_ONLY",
            runtime_callable="runtime_service",
            authority_context="unknown",
            provenance_status="NOT_ATTACHED",
        )

    def saveas(self, path: str) -> None:
        validate_export_context(self._lifecycle_context)
        self._doc.saveas(path)

    def to_bytes(self) -> bytes:
        validate_export_context(self._lifecycle_context)
        stream = io.StringIO()
        self._doc.write(stream)
        return stream.getvalue().encode("utf-8")
```

**Callers should pass context**:

```python
writer = create_dxf_writer(
    layer_names=[...],
    lifecycle_context=ExportLifecycleContext(
        source_module=__name__,
        export_type="dxf-create-save",
        ...
    )
)
```

#### 2.2 CAM Services Using DxfWriter (covered by 2.1)

These paths use DxfWriter and will inherit guards from 2.1:

| # | File | Creation | Covered By | Disposition |
|---|------|----------|------------|-------------|
| 2 | `cam/unified_dxf_cleaner.py` | create_document | DxfWriter guard | no_action |
| 3 | `cam/layer_consolidator.py` | create_document | DxfWriter guard | no_action |
| 4 | `cam/dxf_consolidator.py` | create_document | DxfWriter guard | no_action |
| 5 | `cam/dxf_advanced_validation.py` | create_document | N/A (preview only) | no_action |
| 6 | `cam/archtop_bridge_generator.py` | create_document | DxfWriter guard | no_action |
| 7 | `cam/archtop_saddle_generator.py` | create_document | DxfWriter guard | no_action |
| 8 | `cam/archtop/archtop_surface_tools.py` | create_document | DxfWriter guard | no_action |
| 9 | `cam/archtop/archtop_contour_generator.py` | create_document | DxfWriter guard | no_action |

#### 2.3 Instrument Geometry Services

| # | File | Creation | Save Pattern | Guard Point | Disposition |
|---|------|----------|--------------|-------------|-------------|
| 10 | `instrument_geometry/body/smart_guitar_dxf.py` | create_document | doc.saveas(path) | before saveas | guard_only |
| 11 | `instrument_geometry/soundhole/spiral_geometry.py` | DxfWriter | writer.saveas() | covered by 2.1 | no_action |
| 12 | `generators/bezier_body.py` | DxfWriter | writer.saveas() | covered by 2.1 | no_action |

#### 2.4 Art Studio / Inlay Services (dxf-create-only)

| # | File | Creation | Save Pattern | Guard Point | Disposition |
|---|------|----------|--------------|-------------|-------------|
| 13 | `art_studio/services/generators/inlay_export.py` | create_document | caller saves | N/A | no_action |
| 14 | `calculators/inlay_calc.py` | create_document | caller saves | N/A | no_action |

These return documents without saving — guard responsibility shifts to caller.

#### 2.5 Other Services

| # | File | Creation | Save Pattern | Guard Point | Disposition |
|---|------|----------|--------------|-------------|-------------|
| 15 | `services/layered_dxf_writer.py` | create_document | doc.write/saveas | before write | guard_only |

#### 2.6 DIRECT_SAVE_GAP Services (2 paths)

| # | File | Creation | Save Pattern | Guard Point | Disposition |
|---|------|----------|--------------|-------------|-------------|
| 16 | `cam/line_deduplicator.py` | ezdxf.readfile | doc.saveas(path) | before saveas | guard_only |
| 17 | `services/text_reinsertion.py` | ezdxf.readfile | doc.saveas(path) | before saveas | guard_only |

---

## Explicitly Blocked / Deferred Paths

### Blocked: IBG Provenance (5 calls in 2 files)

| File | Lines | Status | Blocking Condition |
|------|-------|--------|-------------------|
| `instrument_geometry/body/ibg/body_contour_solver.py` | 777, 808 | BLOCKED_PROVENANCE | IBG provenance model ratification |
| `instrument_geometry/body/ibg/arc_reconstructor.py` | 1116, 1279, 1303 | BLOCKED_PROVENANCE | IBG provenance model ratification |

**Disposition**: blocked_provenance — do not add guards until provenance model is ratified.

### Deferred: Test Fixtures (9 files)

Test fixtures use direct `ezdxf.new()` per TEST_FIXTURE_ALLOWED policy.

**Disposition**: no_action — tests are excluded from production enforcement.

### Deferred: Scripts (1 file)

| File | Status | Disposition |
|------|--------|-------------|
| `scripts/generate_smart_guitar_v3_dxf.py` | R_AND_D_EXCLUDED | no_action |

### Deferred: Blueprint-Import (4 files)

Import surface, not production runtime.

**Disposition**: no_action — excluded from enforcement.

### Deferred: Photo-Vectorizer (9 files)

R&D sandbox.

**Disposition**: no_action — excluded from enforcement.

---

## Metadata Required

### Per-Path Metadata

| Field | Source | Required |
|-------|--------|----------|
| `source_module` | `__name__` | YES |
| `export_type` | From matrix classification | YES |
| `dxf_version` | `doc.dxfversion` | YES |
| `lifecycle_status` | From matrix classification | YES |
| `runtime_callable` | From matrix classification | YES |
| `authority_context` | Caller context | OPTIONAL |
| `provenance_status` | Current state | YES |

### Authority Context Values

| Value | Meaning |
|-------|---------|
| `user_request` | Direct user-initiated export |
| `pipeline_stage` | Part of CAM pipeline execution |
| `batch_operation` | Batch/bulk processing |
| `preview_only` | Validation/preview, no final export |

---

## Test Plan

### Unit Tests

| Test | Description | Coverage |
|------|-------------|----------|
| `test_validate_export_context_valid` | Valid context passes | Core guard |
| `test_validate_export_context_missing_source` | Missing source_module fails | Core guard |
| `test_validate_export_context_missing_version` | Missing dxf_version fails | Core guard |
| `test_validate_export_context_invalid_status` | Invalid lifecycle_status fails | Core guard |

### Integration Tests

| Test | Description | Coverage |
|------|-------------|----------|
| `test_dxf_writer_guard_fires` | DxfWriter.saveas() triggers guard | DxfWriter |
| `test_router_export_guard_fires` | Router export triggers guard | Router endpoints |
| `test_read_modify_save_guard_fires` | Read-modify-save triggers guard | DIRECT_SAVE_GAP |

### Regression Tests

| Test | Description | Coverage |
|------|-------------|----------|
| `test_existing_exports_unchanged` | Guard does not alter output | All paths |
| `test_guard_does_not_block_valid_export` | Valid exports complete | All paths |

---

## Rollout Recommendation

### Phase 2A: Core Infrastructure (No Behavior Change)

1. Create `app/cam/export_lifecycle_guard.py`:
   - `ExportLifecycleContext` dataclass
   - `validate_export_context()` function
   - Logging/audit hook (disabled by default)

2. Add unit tests for guard logic

3. **No integration yet** — guard module exists but is not called

### Phase 2B: DxfWriter Integration (Lowest Churn)

1. Modify `DxfWriter.__init__()` to accept optional `lifecycle_context`
2. Add guard calls in `saveas()` and `to_bytes()`
3. Default context for backwards compatibility
4. Integration tests for DxfWriter

**Impact**: All DxfWriter consumers get guards automatically

### Phase 2C: Router Endpoint Integration (Priority 1)

1. Add guard calls to 10 router endpoints
2. Order by simplest first:
   - `smart_guitar_dxf_router.py` (already has saveas pattern)
   - `neck_profile_export.py`
   - `dxf_export.py`
   - remaining routers

3. Integration tests for each router

### Phase 2D: DIRECT_SAVE_GAP Paths (Priority 2)

1. Add guard calls to 3 read-modify-write paths:
   - `line_deduplicator.py`
   - `text_reinsertion.py`
   - `dxf_geometry_correction.py`

2. These require explicit guard calls (no DxfWriter leverage)

### Phase 2E: Audit/Logging Enablement

1. Enable audit logging in guard
2. Add metrics collection
3. Validate guard coverage in CI

---

## Implementation Order Summary

| Order | Target | Files | Churn | Risk |
|-------|--------|-------|-------|------|
| 2A | Core guard module | 1 new | LOW | LOW |
| 2B | DxfWriter | 1 modify | LOW | LOW |
| 2C | Router endpoints | 10 modify | MEDIUM | LOW |
| 2D | DIRECT_SAVE_GAP | 3 modify | LOW | LOW |
| 2E | Audit enablement | 1 modify | LOW | LOW |

**Total**: 1 new file, 14 modified files

---

## Guard Disposition Summary

| Disposition | Count | Description |
|-------------|-------|-------------|
| `guard_only` | 14 | Add lightweight guard, no orchestrator |
| `later_orchestrator_candidate` | 3 | Guard now, orchestrator integration later |
| `blocked_provenance` | 5 | IBG paths, await ratification |
| `no_action` | 32 | Already covered, preview-only, or excluded |
| **Total** | **54** | |

---

## Acceptance Criteria

- [x] All COMPAT_ONLY production candidates listed
- [x] All DIRECT_SAVE_GAP production candidates listed
- [x] Blocked IBG paths remain separated
- [x] Guard insertion points are concrete
- [x] Implementation order is clear
- [x] No code changes in this phase
- [x] Test plan covers guard behavior
- [x] Rollout recommendation follows priority order
