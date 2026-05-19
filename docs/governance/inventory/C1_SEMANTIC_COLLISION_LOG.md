# C1 Semantic Collision Log

**Phase**: C1 — Collection (no decisions, no changes)  
**Date**: 2026-05-18  
**Purpose**: Document semantic collisions across sprint workstreams

---

## Collision Format

Each collision is logged with:
- **ID**: Unique collision identifier
- **Term(s)**: The colliding vocabulary
- **Locations**: Where the collision occurs
- **Collision Type**: Category of collision
- **Severity**: Impact assessment
- **C2 Candidate**: Recommended reconciliation approach (not implemented in C1)

---

## COLL-001: Invariant Naming Divergence

**Term(s)**: `execution_ready` vs `execution_authorized`

**Locations**:
- `app/cam/runtime/operation_manifest.py:70` — `execution_ready: Literal[False]`
- `app/cam/runtime_semantic_consumption.py` — `execution_authorized: bool = False`
- `app/cam/runtime_semantic_consumption_ledger.py` — `execution_authorized: bool = False`

**Collision Type**: Synonym proliferation

**Severity**: Medium — Same semantic intent, different names

**C2 Candidate**: Normalize to single term (`execution_authorized` preferred — matches governance vocabulary)

---

## COLL-002: Machine Output Invariant Naming

**Term(s)**: `machine_operation_authorized` vs `machine_output_allowed` vs `machine_output_generated`

**Locations**:
- `app/cam/runtime/operation_manifest.py:74` — `machine_operation_authorized`
- `app/cam/runtime/runtime_results.py:185` — `machine_output_generated`
- `app/cam/runtime_semantic_consumption.py` — `machine_output_allowed`
- All 7L-7O models — `machine_output_allowed`

**Collision Type**: Synonym proliferation

**Severity**: Medium — Same semantic intent, three different names

**C2 Candidate**: Normalize to single term (`machine_output_allowed` preferred — matches 7L-7O governance chain)

---

## COLL-003: Validation Gate Duplication

**Term(s)**: `green`, `yellow`, `red` (validation gate semantics)

**Locations**:
- `app/cam/runtime/operation_manifest.py:61` — `validation_gate: Literal["green", "yellow", "red"]`
- `app/cam/runtime/runtime_results.py:74` — same
- `app/cam/dxf_validation_gate.py` — (not scanned, referenced)
- `app/cam/translator_readiness_matrix.py` — (readiness uses similar concepts)
- `docs/governance/` — check_all.py tier system uses pass/warn/fail

**Collision Type**: Unregistered repeated vocabulary

**Severity**: High — Same vocabulary defined in 3+ locations without 7M registration

**C2 Candidate**: Register `validation_gate` in 7M with `lifecycle_semantics: ["green", "yellow", "red"]`

---

## COLL-004: Provenance Semantic Split

**Term(s)**: `provenance`

**Locations**:
- `app/cam/runtime/runtime_results.py:46` — `provenance: list[str]` (action log)
- `app/cam/runtime/operation_manifest.py:79` — same (action log)
- `app/cam/canonical_ontology_registry.py:384` — 7M definition (governance chain)
- `app/cam/runtime_semantic_consumption_ledger.py` — lineage hashes (epistemic)

**Collision Type**: Semantic overloading

**Severity**: High — Same term, three different meanings:
1. Action log: "what happened" (runtime)
2. Governance chain: "who approved" (7M definition)
3. Lineage hash: "epistemic continuity" (7O ledger)

**C2 Candidate**: Distinguish `action_provenance`, `governance_provenance`, `lineage_provenance`

---

## COLL-005: Status Vocabulary Collision

**Term(s)**: `status`

**Locations**:
- `app/cam/runtime/runtime_results.py:44` — `status: Literal["available", "placeholder", "unsupported", "error"]`
- `app/cam/runtime/operation_manifest.py:31` — artifact status (same vocabulary)
- `app/cam/runtime/operation_manifest.py:54` — `dispatch_status` (different vocabulary)
- RMOS workflow states — `pending`, `active`, `completed` (different vocabulary)
- MRP promotion — `draft`, `candidate`, `canonical` (different vocabulary)

**Collision Type**: Domain-scoped same-name different-meaning

**Severity**: High — "status" means different things in different contexts

**C2 Candidate**: Prefix all status fields: `result_status`, `dispatch_status`, `workflow_status`, `promotion_status`

---

## COLL-006: Unsupported Term Overloading

**Term(s)**: `unsupported`

**Locations**:
- `app/cam/runtime/runtime_results.py:44` — result status
- `app/cam/runtime/runtime_results.py:120` — geometry_resolution_status
- `app/cam/runtime/runtime_results.py:139` — planning_stage
- `app/cam/runtime/runtime_results.py:157` — preview_stage
- `app/cam/runtime/runtime_results.py:178` — export_stage

**Collision Type**: Same term in multiple type enums

**Severity**: Medium — Same string value in 5 different Literal types

**C2 Candidate**: This may be intentional (consistent "unsupported" across stages) — confirm design intent before changing

---

## COLL-007: Observational vs Immutable

**Term(s)**: `observational_only` vs `immutable`

**Locations**:
- `app/cam/runtime/runtime_results.py:49` — `observational_only: Literal[True]`
- `app/cam/runtime_semantic_consumption_ledger.py` — `immutable: bool = True`
- `app/cam/canonical_ontology_registry.py` — `immutable: bool = True`

**Collision Type**: Overlapping semantic concepts

**Severity**: Low — Different focus but related:
- `observational_only` = "doesn't authorize execution"
- `immutable` = "cannot be modified"

**C2 Candidate**: Keep both — they express different constraints. Document relationship.

---

## COLL-008: Translator Lifecycle vs Runtime Lifecycle

**Term(s)**: Lifecycle state vocabularies

**Locations**:
- `app/cam/canonical_ontology_registry.py:341` — translator: `["registered", "validated", "authorized", "quarantined"]`
- `app/cam/canonical_ontology_registry.py:357` — runtime: `["absent", "quarantined", "authorized"]`
- `app/cam/runtime/` — No lifecycle states, only result statuses

**Collision Type**: Lifecycle vocabulary divergence

**Severity**: Medium — Translator has 4 states, runtime has 3 states, dispatcher has 0 states

**C2 Candidate**: Determine if dispatcher should consume translator/runtime lifecycle states

---

## COLL-009: Geometry Authority Boundary

**Term(s)**: `geometry`, `geometry_authority`, `geometry_resolution`

**Locations**:
- `app/cam/canonical_ontology_registry.py` — `geometry_authority` registered (Tier 2, Geometry domain)
- `app/cam/runtime/runtime_results.py:117` — `geometry_resolution_status`
- `app/cam/runtime/dispatcher.py:208` — `runtime.resolve_geometry(intent)`

**Collision Type**: Undeclared authority dependency

**Severity**: Medium — Dispatcher calls geometry resolution without checking `geometry_authority`

**C2 Candidate**: Either:
1. Dispatcher should validate geometry authority before calling resolve_geometry
2. Or geometry_resolution is operational, not authoritative (document this)

---

## COLL-010: Plugin Registry vs 7N Consumer Registry

**Term(s)**: Runtime registration patterns

**Locations**:
- `app/cam/runtime/plugin_registry.py` — `RuntimePluginRegistry`
- `app/cam/runtime_semantic_consumption.py` — `register_runtime_semantic_consumer()`

**Collision Type**: Parallel registration systems

**Severity**: Medium — Two registration systems for runtime components:
1. Plugin registry: "what operations can this runtime handle"
2. Consumer registry: "what ontology does this runtime consume"

**C2 Candidate**: Connect the two — when a plugin registers, it should also register as a 7N consumer

---

## Summary Statistics

| Severity | Count |
|----------|-------|
| High | 3 |
| Medium | 6 |
| Low | 1 |
| **Total** | **10** |

| Collision Type | Count |
|----------------|-------|
| Synonym proliferation | 2 |
| Semantic overloading | 1 |
| Unregistered vocabulary | 1 |
| Domain-scoped collision | 1 |
| Enum overloading | 1 |
| Overlapping concepts | 1 |
| Lifecycle divergence | 1 |
| Undeclared dependency | 1 |
| Parallel systems | 1 |

---

## C1 Rule Observed

> C1 makes semantic collisions visible. C1 does not make semantic decisions.

No changes were made. This log is evidence for C2 reconciliation.
