# CAM Runtime Dispatcher Developer Handoff

**Date:** 2026-05-16  
**Dev Orders Covered:** 54, 56, 57, 58  
**Author:** Claude Code (Opus 4.5)  
**Branch:** fix/wood-shrinkage-data-integrity

---

## Executive Summary

This handoff documents the implementation of the CAM Runtime Dispatcher infrastructure across four sequential dev orders. The work establishes governed scaffolding for future CAM runtime plugins while enforcing hard safety invariants that prevent premature machine output generation.

**Key constraint observed throughout:** All infrastructure is observational/diagnostic scaffolding ONLY. No calibration, no prediction, no persistence, no restore, no backend upload. Human authority ratifies all canonical ontology decisions.

---

## Dev Order 54: Measurement Archive Infrastructure

### What Was Built

Frontend infrastructure for archiving observational acoustic measurements with full provenance tracking.

### Files Created

| File | Purpose |
|------|---------|
| `packages/client/src/types/acoustics/measurementArchive.ts` | TypeScript interfaces for archive records |
| `packages/client/src/utils/acoustics/measurementArchive.ts` | Archive utility helpers |
| `packages/client/src/components/shared/acoustics/MeasurementArchivePreviewCard.vue` | Read-only preview component |
| `docs/architecture/MEASUREMENT_ARCHIVE_ARCHITECTURE.md` | Architecture reference |

### Key Design Decisions

1. **Schema versioning via literal type**: `schema_version: 'measurement-archive.v1'`
   - **Why:** Enables forward-compatible migrations without runtime type coercion

2. **Provenance as first-class citizen**: Every measurement carries `observer_id`, `device_id`, `capture_timestamp`, `environmental_conditions`
   - **Why:** Observational data without provenance is noise. The archive exists to preserve epistemic integrity.

3. **No computed fields**: Archive stores raw measurements only, no derived values
   - **Why:** Derivation belongs to analysis systems. Archive is a record of what was observed, not what was concluded.

### Annotation: Why This Matters

The measurement archive creates a separation between "what happened" (observed data) and "what it means" (interpretation). This separation is critical for the Three-Loop Architecture — Loop 3 (user correction retraining) requires ground truth that isn't contaminated by model assumptions.

---

## Dev Order 56: Canonical Reconciliation Layer

### What Was Built

Governance foundation for managing semantic drift across the ontology. Four interconnected documents establishing vocabulary, authority, workflow, and drift classification.

### Files Created

| File | Purpose |
|------|---------|
| `docs/governance/CANONICAL_ONTOLOGY_VOCABULARY.md` | 28 canonical terms with full field structure |
| `docs/governance/CANONICAL_AUTHORITY_MAP.md` | Hybrid authority mapping |
| `docs/governance/ONTOLOGY_RECONCILIATION_WORKFLOW.md` | 8-stage workflow with 4 roles |
| `docs/governance/ONTOLOGY_DRIFT_CLASSIFICATIONS.md` | 9 drift categories with real examples |

### Key Design Decisions

1. **Hybrid authority model**: Abstract Canonical Owner + named Operational Owner
   - **Why:** Pure abstract ownership ("Domain Owner") loses traceability. Pure named ownership ("@alice") creates bus-factor risk. Hybrid preserves both semantic clarity and accountability.

2. **AI constraints stated twice**: In Authority Map AND Reconciliation Workflow
   - **Why:** Different readers enter at different documents. The constraint that AI assistance is advisory-only must be visible regardless of entry point.

3. **Prohibited Reinterpretations field**: Every vocabulary term explicitly lists forbidden meanings
   - **Why:** Semantic drift happens through creative reinterpretation. Stating what a term does NOT mean is as important as stating what it does mean.

4. **Real examples for drift categories**: Not theoretical — actual code paths cited
   - **Why:** Abstract drift categories become meaningless without concrete grounding. "Subsumption Conflict" means nothing until you see `mode` trying to absorb `workflow_stage`.

### Annotation: Semantic Fragmentation Risks Identified

During implementation, several existing risks were documented:

| Risk | Location | Mitigation Status |
|------|----------|-------------------|
| "status" vocabulary collision | 4 different meanings across CAM, RMOS, MRP | Documented in vocabulary, not yet resolved |
| "provenance" semantic split | Action log vs epistemic warning vs authority chain | Vocabulary entry distinguishes usage |
| "canonical" overloading | "official" vs "immutable" vs "source-of-truth" | Lifecycle Notes field clarifies |
| Geometry layer ambiguity | "geometry" used for both data and visualization | Pending disambiguation |

---

## Dev Order 57: CAM Runtime Dispatcher Skeleton

### What Was Built

Governed host structure for future CAM runtime plugins. The dispatcher consumes CamIntentV1 and routes to registered plugins, returning OperationManifestV1 with hard safety invariants.

### Files Created

| File | Purpose |
|------|---------|
| `services/api/app/cam/runtime/__init__.py` | Package exports |
| `services/api/app/cam/runtime/dispatcher.py` | RuntimeDispatcher class |
| `services/api/app/cam/runtime/operation_runtime.py` | CamOperationRuntime Protocol |
| `services/api/app/cam/runtime/operation_manifest.py` | OperationManifestV1 schema |
| `services/api/app/cam/runtime/plugin_registry.py` | RuntimePluginRegistry |
| `services/api/tests/test_cam_runtime_dispatcher.py` | 21 tests |
| `docs/architecture/CAM_RUNTIME_DISPATCHER_ARCHITECTURE.md` | Architecture reference |

### Key Design Decisions

1. **Protocol-based interface**: `CamOperationRuntime(Protocol)` not ABC
   - **Why:** Structural subtyping. A class satisfies the protocol if it has the right methods — no inheritance ceremony required. This aligns with Python typing best practices.

2. **Operation type resolution fallback**: `design.operation` → `mode.value`
   - **Why:** Intent contracts may specify operation explicitly, or it may be implied by mode. The resolution order is intentional until formal operation vocabulary exists.

3. **Unsupported is not an error**: Returns valid manifest with `dispatch_status="unsupported_operation"`
   - **Why:** Unknown operations are a valid dispatch outcome, not an exception. The dispatcher must remain stable even when the ecosystem is incomplete.

4. **Hard invariants via Pydantic validators**:
   ```python
   execution_ready: Literal[False] = False
   machine_operation_authorized: Literal[False] = False
   ```
   - **Why:** These cannot be bypassed at runtime. The Literal[False] type combined with field validator ensures no codepath can set True.

### Annotation: Why Skeleton-First

The dispatcher skeleton exists before any real plugins do. This is intentional:

1. **Prevents CAM runtime fragmentation** — New operations must conform to the protocol, not invent their own export paths
2. **Establishes governance before capability** — Safety invariants are structural, not behavioral
3. **Enables parallel development** — Plugin authors can develop against a stable interface

---

## Dev Order 58: Runtime Result Contract Normalization

### What Was Built

Normalized result contracts for all five dispatch stages (validate, resolve_geometry, plan, preview, export). Every stage returns a typed result with shared semantics.

### Files Created/Modified

| File | Change |
|------|--------|
| `services/api/app/cam/runtime/runtime_results.py` | **New** — All result contracts |
| `services/api/tests/test_cam_runtime_results.py` | **New** — 30 result contract tests |
| `services/api/app/cam/runtime/operation_manifest.py` | **Modified** — Added result ID references |
| `services/api/app/cam/runtime/dispatcher.py` | **Modified** — Full 5-stage chain |
| `services/api/tests/test_cam_runtime_dispatcher.py` | **Modified** — Updated for full chain |
| `docs/architecture/CAM_RUNTIME_DISPATCHER_ARCHITECTURE.md` | **Modified** — Result normalization docs |
| `docs/governance/CANONICAL_ONTOLOGY_VOCABULARY.md` | **Modified** — 6 new runtime terms |

### Key Design Decisions

1. **Shared base class with common fields**:
   ```python
   class RuntimeResultBase(BaseModel):
       result_id: str  # Auto-generated with rr_ prefix
       schema_version: Literal["runtime-result.v1"]
       status: Literal["available", "placeholder", "unsupported", "error"]
       provenance: list[str]
       diagnostics: list[str]
       observational_only: Literal[True] = True
   ```
   - **Why:** All results share traceability (result_id), status classification, and observational constraint. This prevents parallel ontology drift where different stages invent incompatible status vocabularies.

2. **Auto-generated result IDs**: `rr_` prefix + 12 hex chars
   - **Why:** Every result must be traceable. Auto-generation ensures IDs exist even when callers forget. The prefix makes result IDs distinguishable from intent IDs or artifact IDs.

3. **Stage-specific result types inherit and extend**:
   - `RuntimeValidationResult` adds `validation_gate`, `execution_ready`, `machine_operation_authorized`
   - `RuntimeExportResult` adds `export_stage`, `machine_output_generated`
   - **Why:** Each stage has unique semantics, but shares the base observational contract.

4. **Factory functions for unsupported results**:
   ```python
   create_unsupported_validation_result(reason, provenance)
   create_unsupported_geometry_result(reason)
   # etc.
   ```
   - **Why:** Unsupported operations must still return normalized results. Factory functions ensure consistency even in failure paths.

5. **Manifest includes result ID references**:
   ```python
   validation_result_id: str | None
   geometry_result_id: str | None
   plan_result_id: str | None
   preview_result_id: str | None
   export_result_id: str | None
   ```
   - **Why:** The manifest is the summary; the results contain detail. ID references enable drill-down without embedding full results in the manifest.

### Annotation: Hard Invariants Summary

| Invariant | Enforced By | Applies To |
|-----------|-------------|------------|
| `observational_only = True` | `Literal[True]` + validator | All results |
| `execution_ready = False` | `Literal[False]` + validator | RuntimeValidationResult |
| `machine_operation_authorized = False` | `Literal[False]` + validator | RuntimeValidationResult, OperationManifestV1 |
| `machine_output_generated = False` | `Literal[False]` + validator | RuntimeExportResult |

These invariants are structural. They cannot be bypassed by passing different values — Pydantic rejects the input at validation time.

---

## Testing Status

### Test Counts

| Test File | Tests | Status |
|-----------|-------|--------|
| `test_cam_runtime_dispatcher.py` | 21 | ✅ All passing |
| `test_cam_runtime_results.py` | 30 | ✅ All passing |

### Test Categories

1. **Invariant enforcement**: Cannot set `execution_ready=True`, `machine_operation_authorized=True`, `machine_output_generated=True`, `observational_only=False`
2. **Protocol compliance**: StubRuntime implements CamOperationRuntime correctly
3. **Dispatch flow**: Full 5-stage chain executes with provenance
4. **Error handling**: Runtime exceptions produce `runtime_error` manifests without execution authorization
5. **Result ID traceability**: All result IDs preserved through dispatch chain

---

## Governance Integration

### Existing Infrastructure Discovered

The repository has extensive governance infrastructure already in place:

| Category | Count/Details |
|----------|---------------|
| GitHub Actions workflows | 57 workflow files |
| Governance scripts | `scripts/governance/check_all.py` with tier system |
| Pre-commit hook | Runs `--tier precommit` checks |
| Pydantic schema system | Extensive throughout codebase |
| Single owner | HanzoRazer |

### Governance Docs Committed

All four canonical governance documents from Dev Order 56 are committed:
- `docs/governance/CANONICAL_ONTOLOGY_VOCABULARY.md`
- `docs/governance/CANONICAL_AUTHORITY_MAP.md`
- `docs/governance/ONTOLOGY_RECONCILIATION_WORKFLOW.md`
- `docs/governance/ONTOLOGY_DRIFT_CLASSIFICATIONS.md`

---

## Semantic Risks Requiring Future Attention

### Priority 1: Status Vocabulary Collision

The term "status" means different things:
- CAM: dispatch outcome (`validated_only`, `unsupported_operation`, `runtime_error`)
- RMOS: workflow state (`pending`, `active`, `completed`)
- MRP: promotion readiness (`draft`, `candidate`, `canonical`)
- Runtime Results: availability (`available`, `placeholder`, `unsupported`, `error`)

**Recommendation:** Prefix status fields with domain (e.g., `dispatch_status`, `workflow_status`, `promotion_status`, `result_status`) — partially done in runtime contracts.

### Priority 2: Provenance Semantic Split

"Provenance" is used for:
- Action log: "what happened" (list of stage executions)
- Epistemic warning: "why this might be wrong" (uncertainty markers)
- Authority chain: "who approved this" (governance trail)

**Recommendation:** Distinguish `action_provenance`, `epistemic_flags`, `authority_chain` in future schemas.

### Priority 3: Geometry Layer Ambiguity

"Geometry" refers to both:
- Data: coordinates, curves, meshes
- Visualization: layers, colors, line weights

**Recommendation:** Use `geometry_data` vs `geometry_presentation` in CAM contracts.

---

## Files Modified on This Branch

```
M services/api/app/calculators/nut_compensation_calc.py
M services/api/app/cam/adaptive_spiralizer_utils.py
M services/api/app/cam/profiling/tabs.py
M services/api/app/cam_core/geometry/advanced_offset.py
M services/api/app/core/pipeline_handoff.py
M services/api/app/instrument_geometry/neck/fret_math.py
M services/api/app/models/tool_db.py
M services/api/app/util/cam_notifier.py
M services/api/app/util/names.py
M services/api/app/util/template_engine.py
```

Note: These modifications predate the current session. The runtime dispatcher work created new files rather than modifying existing ones.

---

## Next Steps (Not Yet Implemented)

### Cross-Sprint Coordination Phases

A synthesis document outlined 8 coordination phases (CS-1 through CS-8):

1. **CS-1**: Cross-Sprint Governance Layer — create `CROSS_SPRINT_COORDINATION.md`
2. **CS-2**: Semantic Freeze Prep — schema hash pins, migration tests
3. **CS-3**: Vocabulary Alignment Audit — resolve status collision
4. **CS-4**: Authority Consolidation — merge redundant governance docs
5. **CS-5**: Interface Contracts — formal API contracts between sprints
6. **CS-6**: Provenance Unification — single provenance model
7. **CS-7**: Test Governance — cross-sprint regression suite
8. **CS-8**: Documentation Synthesis — unified architecture view

### Immediate Plugin Candidates

When real runtime plugins are built, candidates include:
- `pocket_runtime` — pocket milling operations
- `profile_runtime` — profile/contour operations
- `drill_runtime` — drilling operations
- `engrave_runtime` — engraving/V-carve operations

Each would implement `CamOperationRuntime` and register with `RuntimePluginRegistry`.

---

## Justification Summary

| Decision | Justification |
|----------|---------------|
| Skeleton before plugins | Prevents fragmentation; establishes protocol first |
| Hard invariants via Pydantic | Cannot be bypassed; structural safety |
| Hybrid authority model | Preserves semantics AND accountability |
| Result ID auto-generation | Ensures traceability even when callers forget |
| Unsupported returns manifest, not exception | Graceful degradation; ecosystem can be incomplete |
| Provenance on every result | Observational data without provenance is noise |
| Schema version literals | Forward-compatible migrations |
| AI constraints stated twice | Different entry points, same constraint visible |

---

## Contact

For questions about this implementation:
- **Repository Owner:** HanzoRazer
- **Branch:** fix/wood-shrinkage-data-integrity
- **Session Date:** 2026-05-16
