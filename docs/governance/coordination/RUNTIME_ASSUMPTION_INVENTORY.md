# Runtime Assumption Inventory

**Phase:** C1 — Collection  
**Date:** 2026-05-18  
**Status:** Evidence collection (no decisions made)

---

## Purpose

This document inventories undocumented runtime assumptions, implicit authority dependencies, and unverified contracts across workstreams. Each entry records the assumption without validating or fixing it.

---

## Assumption Categories

| Category | Meaning |
|----------|---------|
| `AUTHORITY_DEPENDENCY` | System depends on another's authority without declaration |
| `CONTRACT_ASSUMPTION` | System assumes contract exists without verification |
| `OWNERSHIP_AMBIGUITY` | Unclear which system owns a semantic |
| `IMPLICIT_FLOW` | Data flows without explicit contract |
| `ENFORCEMENT_GAP` | Invariant claimed but not enforced |

---

## Logged Assumptions

### ASM-001: Geometry Source Undeclared

| Field | Value |
|-------|-------|
| Category | `AUTHORITY_DEPENDENCY` |
| System | CAM Runtime Dispatcher |
| Location | `dispatcher.py` → `runtime.resolve_geometry()` |
| Assumption | Geometry comes from somewhere when `resolve_geometry()` is called |
| What's missing | Declaration of geometry authority source |
| Impact | If geometry source changes, CAM silently inherits drift |
| Evidence | `RuntimeGeometryResolution` has no `geometry_source` field |

---

### ASM-002: Operation Type Vocabulary

| Field | Value |
|-------|-------|
| Category | `CONTRACT_ASSUMPTION` |
| System | CAM Runtime Dispatcher |
| Location | `dispatcher.py:43` — `resolve_operation_type()` |
| Assumption | Operation type can be derived from `design.operation` or `mode.value` |
| What's missing | Formal operation type taxonomy |
| Impact | Operation vocabulary evolves without governance |
| Evidence | Comment: "temporary dispatcher-resolution behavior" |

---

### ASM-003: Plugin Registry Singleton

| Field | Value |
|-------|-------|
| Category | `IMPLICIT_FLOW` |
| System | CAM Runtime |
| Location | `plugin_registry.py:80` |
| Assumption | `DEFAULT_RUNTIME_PLUGIN_REGISTRY` is the canonical registry |
| What's missing | Documentation of registry lifecycle |
| Impact | Multiple registries could cause routing inconsistency |
| Evidence | Global mutable singleton pattern |

---

### ASM-004: Intent Schema Stability

| Field | Value |
|-------|-------|
| Category | `CONTRACT_ASSUMPTION` |
| System | CAM Runtime Dispatcher |
| Location | `dispatcher.py` |
| Assumption | `CamIntentV1` schema is frozen and stable |
| What's missing | Nothing — this IS documented and hash-pinned |
| Impact | N/A — properly governed |
| Evidence | `CAM_INTENT_SCHEMA_HASH_V1` in `schemas_intent.py` |
| Status | **Verified — good pattern** |

---

### ASM-005: Geometry Mutation Invariant

| Field | Value |
|-------|-------|
| Category | `ENFORCEMENT_GAP` |
| System | CAM Runtime |
| Location | `dispatcher.py:13`, `operation_runtime.py:50` |
| Assumption | Runtime does not mutate geometry |
| What's missing | Type-level enforcement |
| Impact | Plugin could mutate geometry without detection |
| Evidence | Only behavioral claim, no Literal type or validator |

---

### ASM-006: RMOS Persistence Invariant

| Field | Value |
|-------|-------|
| Category | `ENFORCEMENT_GAP` |
| System | CAM Runtime |
| Location | `dispatcher.py:14`, `operation_runtime.py:51` |
| Assumption | Runtime does not persist RMOS runs |
| What's missing | Type-level enforcement |
| Impact | Plugin could persist without detection |
| Evidence | Only behavioral claim, no structural enforcement |

---

### ASM-007: Topology Consumes CadSemantics

| Field | Value |
|-------|-------|
| Category | `AUTHORITY_DEPENDENCY` |
| System | TopologyBuilder |
| Location | `topology_builder/builder.py` |
| Assumption | CadSemantics provides body category |
| What's missing | Explicit authority chain declaration |
| Impact | If CadSemantics changes, TopologyBuilder silently inherits |
| Evidence | TopologyBuilder imports CadSemantics types |

---

### ASM-008: Translator Consumes Topology

| Field | Value |
|-------|-------|
| Category | `AUTHORITY_DEPENDENCY` |
| System | CAM Translators |
| Location | `translators/base/` |
| Assumption | TopologyBuilder output is geometry truth |
| What's missing | Explicit authority chain declaration |
| Impact | If TopologyBuilder semantics drift, translators inherit |
| Evidence | Translators serialize topology objects |

---

### ASM-009: Validation Gate Semantics

| Field | Value |
|-------|-------|
| Category | `OWNERSHIP_AMBIGUITY` |
| System | CAM Runtime |
| Location | `operation_manifest.py:61` |
| Assumption | `green/yellow/red` gate semantics are CAM-local |
| What's missing | Mapping to governance severity vocabulary |
| Impact | Different interpretation than topology `blocking/warning` |
| Evidence | No cross-reference to lifecycle registry |

---

### ASM-010: Result ID Uniqueness

| Field | Value |
|-------|-------|
| Category | `CONTRACT_ASSUMPTION` |
| System | CAM Runtime |
| Location | `runtime_results.py:24` |
| Assumption | `uuid4().hex[:12]` produces unique IDs |
| What's missing | Collision probability analysis |
| Impact | 12 hex chars = 48 bits, low collision risk |
| Evidence | UUID4 is cryptographically random |
| Status | **Acceptable assumption** |

---

### ASM-011: Provenance Format Stability

| Field | Value |
|-------|-------|
| Category | `CONTRACT_ASSUMPTION` |
| System | CAM Runtime |
| Location | `dispatcher.py:168` |
| Assumption | Provenance format `{system}:{action}:{id}` is stable |
| What's missing | Formal provenance schema |
| Impact | Parsing depends on string format |
| Evidence | Hardcoded format strings throughout |

---

### ASM-012: Artifact Type Vocabulary

| Field | Value |
|-------|-------|
| Category | `CONTRACT_ASSUMPTION` |
| System | CAM Runtime |
| Location | `operation_manifest.py:24` |
| Assumption | Artifact types are limited to declared Literal values |
| What's missing | Extensibility model |
| Impact | Adding new artifact types requires schema change |
| Evidence | `Literal["validation_report", "geometry_resolution", ...]` |

---

---

### ASM-013: IBG Zone Boundaries as Implicit Authority

| Field | Value |
|-------|-------|
| Category | `AUTHORITY_DEPENDENCY` |
| System | IBG Body Grid |
| Location | `zones.py:69-338` |
| Assumption | Zone Y-range constants are authoritative body region definitions |
| What's missing | Governance declaration of zone boundary authority |
| Impact | Hardcoded values become de-facto authority without review |
| Evidence | `ZONE_DEFINITIONS` dict with arbitrary Y-ranges |

---

### ASM-014: CadSemantics → TopologyBuilder Authority Chain

| Field | Value |
|-------|-------|
| Category | `AUTHORITY_DEPENDENCY` |
| System | TopologyBuilder |
| Location | `runtime_support.py`, `contracts.py` |
| Assumption | CadSemantics body_category determines TopologyRuntimeSupport |
| What's missing | Explicit authority chain declaration |
| Impact | TopologyBuilder silently consumes CadSemantics decisions |
| Evidence | `BODY_CATEGORY_SUPPORT` dict maps cad_semantics values |

---

### ASM-015: Harvest Term Normalization Authority

| Field | Value |
|-------|-------|
| Category | `CONTRACT_ASSUMPTION` |
| System | Morphology Harvest |
| Location | `morphology_harvest/schema.py:83-97` |
| Assumption | TERM_NORMALIZATIONS dict is authoritative mapping |
| What's missing | Governance review of normalization decisions |
| Impact | Hardcoded term mappings bypass semantic review |
| Evidence | `TERM_NORMALIZATIONS` with drift mappings |

---

## Assumption Statistics

| Category | Count |
|----------|-------|
| AUTHORITY_DEPENDENCY | 5 |
| CONTRACT_ASSUMPTION | 5 |
| OWNERSHIP_AMBIGUITY | 1 |
| IMPLICIT_FLOW | 1 |
| ENFORCEMENT_GAP | 2 |
| **Verified/Acceptable** | 2 |
| Total | 15 |

---

## Critical Assumptions (Require C2 Attention)

| ID | Summary | Risk |
|----|---------|------|
| ASM-001 | Geometry source undeclared | HIGH — authority gap |
| ASM-005 | Geometry mutation not enforced | MEDIUM — behavioral only |
| ASM-006 | RMOS persistence not enforced | MEDIUM — behavioral only |
| ASM-007 | Topology←CadSemantics undeclared | HIGH — authority gap |
| ASM-008 | Translator←Topology undeclared | HIGH — authority gap |
| ASM-013 | IBG zones as implicit authority | HIGH — sandbox pressure |
| ASM-014 | CadSemantics→TopologyBuilder chain | HIGH — authority gap |
| ASM-015 | Harvest term normalization | MEDIUM — hardcoded decisions |

---

## Positive Patterns Observed

| ID | Pattern | Notes |
|----|---------|-------|
| ASM-004 | Schema hash pinning | CamIntentV1 has frozen contract with hash |
| ASM-010 | UUID-based IDs | Acceptable collision risk |

---

## C1 Status

**Logged:** 15 assumptions  
**Critical:** 8  
**Acceptable:** 2  
**Decisions made:** None  
**Next phase:** C2 authority chain formalization
