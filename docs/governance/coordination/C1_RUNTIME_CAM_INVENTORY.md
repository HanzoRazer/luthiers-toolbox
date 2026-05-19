# C1 Inventory: Runtime/CAM Workstream

**Phase:** C1 — Collection  
**Date:** 2026-05-18  
**Status:** Inventory (no decisions made)  
**Scope:** `services/api/app/cam/`, `services/api/app/cam/runtime/`

---

## Purpose

This document inventories runtime lifecycle terms, provenance semantics, and authority assumptions in the CAM workstream. It does NOT normalize, consolidate, or fix anything.

---

## 1. Runtime Lifecycle Terms

### 1.1 Result Status Vocabulary

| Term | Source File | Domain | Axis | Notes |
|------|-------------|--------|------|-------|
| `available` | `runtime_results.py:44` | CAM Runtime | operational | Result successfully produced |
| `placeholder` | `runtime_results.py:44` | CAM Runtime | operational | Stub result |
| `unsupported` | `runtime_results.py:44` | CAM Runtime | operational | **Collision candidate: Topology uses `UNSUPPORTED_RUNTIME`** |
| `error` | `runtime_results.py:44` | CAM Runtime | operational | Runtime error occurred |

### 1.2 Dispatch Status Vocabulary

| Term | Source File | Domain | Axis | Notes |
|------|-------------|--------|------|-------|
| `unsupported_operation` | `operation_manifest.py:54` | CAM Runtime | operational | No plugin registered |
| `validated_only` | `operation_manifest.py:54` | CAM Runtime | operational | **Collision candidate: matches lifecycle term** |
| `planned_placeholder` | `operation_manifest.py:54` | CAM Runtime | operational | Planning stub completed |
| `runtime_error` | `operation_manifest.py:54` | CAM Runtime | operational | Exception during dispatch |

### 1.3 Validation Gate Vocabulary

| Term | Source File | Domain | Axis | Notes |
|------|-------------|--------|------|-------|
| `green` | `operation_manifest.py:61` | CAM Runtime | enforcement | Validation passed |
| `yellow` | `operation_manifest.py:61` | CAM Runtime | enforcement | Passed with warnings |
| `red` | `operation_manifest.py:61` | CAM Runtime | enforcement | Validation failed |

**Collision:** `CamGate` enum with identical values exists in 3 files:
- `nut_slot_cam.py:36`
- `fret_slots_router.py:36`
- `drilling_preview_router.py:35`

### 1.4 Translator Maturity Vocabulary

| Term | Source File | Domain | Axis | Notes |
|------|-------------|--------|------|-------|
| `placeholder` | `capabilities.py:28` | CAM Translator | maturity | Registered not implemented |
| `experimental` | `capabilities.py:29` | CAM Translator | maturity | **Collision: governance uses same term** |
| `candidate` | `capabilities.py:30` | CAM Translator | maturity | **Collision: governance uses same term** |
| `governed` | `capabilities.py:31` | CAM Translator | maturity | **Collision: governance uses same term** |
| `deprecated` | `capabilities.py:32` | CAM Translator | maturity | **Collision: governance uses same term** |

### 1.5 Execution State Vocabulary

| Term | Source File | Domain | Axis | Notes |
|------|-------------|--------|------|-------|
| `validation_only` | `capabilities.py:37` | CAM Translator | runtime | **Collision: lifecycle registry term** |
| `governed_execution` | `capabilities.py:38` | CAM Translator | runtime | CAM-specific |
| `experimental` | `capabilities.py:39` | CAM Translator | runtime | **Duplicate: also in TranslatorMaturity** |
| `execution_disabled` | `capabilities.py:40` | CAM Translator | runtime | CAM-specific |
| `deprecated` | `capabilities.py:41` | CAM Translator | runtime | **Duplicate: also in TranslatorMaturity** |

### 1.6 Topology Runtime Support (consumed by CAM)

| Term | Source File | Domain | Axis | Notes |
|------|-------------|--------|------|-------|
| `SUPPORTED_PROTOTYPE` | `runtime_support.py:27` | Topology | runtime | Consumed by CAM |
| `PARTIAL_PROTOTYPE` | `runtime_support.py:28` | Topology | runtime | Consumed by CAM |
| `UNSUPPORTED_RUNTIME` | `runtime_support.py:29` | Topology | runtime | **Collision candidate: CAM `unsupported`** |
| `RESEARCH_REQUIRED` | `runtime_support.py:30` | Topology | runtime | Consumed by CAM |

### 1.7 Geometry Resolution Status

| Term | Source File | Domain | Axis | Notes |
|------|-------------|--------|------|-------|
| `resolved` | `runtime_results.py:117` | CAM Runtime | operational | Geometry fully resolved |
| `partial` | `runtime_results.py:118` | CAM Runtime | operational | Some geometry resolved |
| `placeholder` | `runtime_results.py:119` | CAM Runtime | operational | Stub resolution |
| `unsupported` | `runtime_results.py:120` | CAM Runtime | operational | Cannot resolve |

### 1.8 Planning Stage Vocabulary

| Term | Source File | Domain | Axis | Notes |
|------|-------------|--------|------|-------|
| `placeholder` | `runtime_results.py:136` | CAM Runtime | operational | Not implemented |
| `deterministic_stub` | `runtime_results.py:137` | CAM Runtime | operational | Stub with fixed output |
| `unsupported` | `runtime_results.py:138` | CAM Runtime | operational | Cannot plan |

### 1.9 Preview Stage Vocabulary

| Term | Source File | Domain | Axis | Notes |
|------|-------------|--------|------|-------|
| `placeholder` | `runtime_results.py:154` | CAM Runtime | operational | Not implemented |
| `preview_stub` | `runtime_results.py:155` | CAM Runtime | operational | Stub preview |
| `unsupported` | `runtime_results.py:156` | CAM Runtime | operational | Cannot preview |

### 1.10 Export Stage Vocabulary

| Term | Source File | Domain | Axis | Notes |
|------|-------------|--------|------|-------|
| `placeholder` | `runtime_results.py:175` | CAM Runtime | operational | Not implemented |
| `export_stub` | `runtime_results.py:176` | CAM Runtime | operational | Stub export |
| `unsupported` | `runtime_results.py:177` | CAM Runtime | operational | Cannot export |

---

## 2. Runtime Provenance Semantics

### 2.1 Provenance Chain Format

| Pattern | Source | Semantic Type | Notes |
|---------|--------|---------------|-------|
| `dispatcher:routed:{runtime_id}` | `dispatcher.py:168` | action_log | What happened |
| `dispatcher:unsupported_operation` | `operation_manifest.py:117` | action_log | What happened |
| `dispatcher:runtime_error:{runtime_id}` | `operation_manifest.py:138` | action_log | What happened |
| `runtime:validated:{runtime_id}` | `dispatcher.py:183` | action_log | What happened |
| `runtime:geometry:{runtime_id}` | `dispatcher.py:210` | action_log | What happened |
| `runtime:planned:{runtime_id}` | `dispatcher.py:224` | action_log | What happened |
| `runtime:preview:{runtime_id}` | `dispatcher.py:238` | action_log | What happened |
| `runtime:export:{runtime_id}` | `dispatcher.py:252` | action_log | What happened |
| `runtime:unsupported` | `runtime_results.py:207` | action_log | What happened |

**Observation:** All CAM provenance is action_log type. No epistemic_warning or authority_chain usage observed.

### 2.2 ID Prefix Conventions

| Prefix | Source | Purpose |
|--------|--------|---------|
| `rr_` | `runtime_results.py:24` | Runtime result ID |
| `manifest-` | `operation_manifest.py:47` | Operation manifest ID |
| `artifact-` | `operation_manifest.py:23` | Runtime artifact ID |

---

## 3. Dispatcher Authority Assumptions

### 3.1 Explicit Claims (Documented)

| Claim | Source | Verified |
|-------|--------|----------|
| Does not generate machine output | `dispatcher.py:11` | Yes (Literal[False] enforcement) |
| Does not authorize execution | `dispatcher.py:12` | Yes (Literal[False] enforcement) |
| Does not mutate geometry | `dispatcher.py:13` | Not enforced at type level |
| Does not persist RMOS runs | `dispatcher.py:14` | Not enforced at type level |

### 3.2 Implicit Assumptions (Undocumented)

| Assumption | Evidence | Authority Dependency |
|------------|----------|---------------------|
| Intent is canonical input | `CamIntentV1` parameter | Intent schema (frozen) |
| Geometry comes from plugin | `runtime.resolve_geometry()` | **UNDECLARED** |
| Operation type derivable from intent | `resolve_operation_type()` | Intent + mode |
| Plugin registry is singleton | `DEFAULT_RUNTIME_PLUGIN_REGISTRY` | Runtime module |

### 3.3 Authority Boundary Summary

| Owns | Consumes | Does NOT Own |
|------|----------|--------------|
| Routing logic | CamIntentV1 | Geometry |
| Provenance chain | Plugin results | Execution authorization |
| Error manifests | | Machine output |
| Stage sequencing | | RMOS persistence |

---

## 4. Plugin Authority Assumptions

### 4.1 Protocol Invariants (Documented)

| Invariant | Source | Enforcement |
|-----------|--------|-------------|
| Consumes intent, does not redefine | `operation_runtime.py:47` | Behavioral only |
| Does not generate machine output | `operation_runtime.py:48` | Literal[False] on results |
| Does not authorize execution | `operation_runtime.py:49` | Literal[False] on results |
| Does not mutate geometry | `operation_runtime.py:50` | Behavioral only |
| Does not persist RMOS runs | `operation_runtime.py:51` | Behavioral only |
| Results are observational only | `operation_runtime.py:52` | Literal[True] enforcement |

### 4.2 Stage Responsibilities

| Stage | Input | Output | Geometry Authority? |
|-------|-------|--------|---------------------|
| `validate` | CamIntentV1 | RuntimeValidationResult | No |
| `resolve_geometry` | CamIntentV1 | RuntimeGeometryResolution | **QUERIES (source undeclared)** |
| `plan` | CamIntentV1 | RuntimePlanResult | No |
| `preview` | CamIntentV1 | RuntimePreviewResult | No |
| `export` | CamIntentV1 | RuntimeExportResult | No |

---

## 5. Execution-State Semantics

### 5.1 Hard Invariants (Type-Enforced)

| Field | Type | Default | Enforcement |
|-------|------|---------|-------------|
| `execution_ready` | `Literal[False]` | `False` | `field_validator` raises on `True` |
| `machine_operation_authorized` | `Literal[False]` | `False` | `field_validator` raises on `True` |
| `machine_output_generated` | `Literal[False]` | `False` | `field_validator` raises on `True` |
| `observational_only` | `Literal[True]` | `True` | `field_validator` raises on `False` |

### 5.2 Schema Version Pins

| Schema | Version Literal | Hash Pin |
|--------|-----------------|----------|
| RuntimeResultBase | `runtime-result.v1` | None |
| OperationManifestV1 | `operation-manifest.v1` | None |
| CamIntentV1 | `cam_intent_v1` | `9e2f47d2...` (frozen) |

---

## 6. Term Collision Summary

### 6.1 Same Term, Different Meaning

| Term | CAM Meaning | Other Domain | Other Meaning |
|------|-------------|--------------|---------------|
| `unsupported` | Result status | Topology | `UNSUPPORTED_RUNTIME` enum |
| `validation_only` | Execution state | Lifecycle registry | Execution mode |
| `experimental` | Translator maturity | Governance | Lifecycle state |
| `deprecated` | Translator maturity | Governance | Lifecycle state |

### 6.2 Same Concept, Different Term

| Concept | CAM Term | Other Domain | Other Term |
|---------|----------|--------------|------------|
| Cannot execute | `unsupported` | Topology | `UNSUPPORTED_RUNTIME` |
| Under development | `experimental` | Governance | `experimental` (same) |
| Validation passed/failed | `green/yellow/red` | Topology | `blocking/major/warning` |

### 6.3 Duplicate Definitions

| Term | Locations | Values Identical? |
|------|-----------|-------------------|
| `CamGate` | 3 files | Yes |
| `MaterialType` | 3 files | No (different values) |
| `experimental` | TranslatorMaturity + ExecutionState | Yes |
| `deprecated` | TranslatorMaturity + ExecutionState | Yes |

---

## 7. Registry Cross-Reference

### 7.1 Terms vs lifecycle_registry.json

| CAM Term | In Registry? | Status |
|----------|--------------|--------|
| `available` | No | CAM-local |
| `placeholder` | No | CAM-local |
| `unsupported` | No | **Candidate for mapping to `unsupported_runtime`** |
| `error` | No | CAM-local |
| `validation_only` | Yes | Collision (different meaning) |
| `experimental` | Yes | Collision (same meaning, different context) |
| `governed` | Yes | Collision (same meaning, different context) |
| `deprecated` | No | **Candidate for registration** |

### 7.2 Terms vs semantic_registry.json

| CAM Concept | In Registry? | Status |
|-------------|--------------|--------|
| Translator | No | **Candidate for registration** |
| Runtime | Yes | Matches |
| Validation | Yes | Matches |
| Provenance | Yes | Matches (action_log subset) |

---

## 8. Undocumented Authority Dependencies

| Dependency | Location | What's Missing |
|------------|----------|----------------|
| Geometry source | `resolve_geometry()` | Where does geometry come from? |
| Operation vocabulary | `resolve_operation_type()` | Formal operation taxonomy |
| Plugin discovery | `RuntimePluginRegistry` | How are plugins registered? |

---

## Related Documents

- `docs/handoffs/CAM_RUNTIME_DISPATCHER_DEVELOPER_HANDOFF.md`
- `docs/governance/ontology/lifecycle_registry.json`
- `docs/governance/ontology/semantic_registry.json`
- `docs/architecture/CAM_RUNTIME_DISPATCHER_ARCHITECTURE.md`

---

## C1 Status

**Collected:** Yes  
**Decisions made:** None  
**Next phase:** C2 reconciliation (not this document)
