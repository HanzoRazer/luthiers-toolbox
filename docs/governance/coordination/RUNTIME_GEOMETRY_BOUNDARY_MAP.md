# Runtime Geometry Boundary Map

**Phase:** C2-A — Geometry Authority Decomposition  
**Date:** 2026-05-18  
**Owner:** Terminal 2 (Runtime/CAM Reviewer)  
**Status:** Draft — Requires code verification

---

## Purpose

This document maps runtime geometry consumption patterns, identifying where runtime systems interact with geometry authority and whether any boundary violations occur.

---

## 1. Runtime Geometry Flow

### 1.1 Primary Flow Path

```
CamIntent
  │
  ▼
Dispatcher
  │
  ├─► resolve_geometry() ──► [UNKNOWN SOURCE] ◄── ASM-001
  │
  ▼
PluginRegistry
  │
  ├─► get_plugin_for_operation()
  │
  ▼
Plugin Adapter
  │
  ├─► adapt_geometry() ──► [POTENTIAL COLLAPSE]
  │
  ▼
TopologyBuilder
  │
  ▼
Translator
  │
  ▼
Export
```

### 1.2 Geometry Entry Points

| Entry Point | Location | Authority Question |
|-------------|----------|-------------------|
| `resolve_geometry()` | `dispatcher.py` | Where does geometry come from? |
| `RuntimeGeometryResolution` | `runtime_results.py` | DTO defines geometry fields |
| Plugin `get_geometry()` | Plugin adapters | Plugins may source geometry |
| `BODY_CATEGORY_SUPPORT` | `runtime_support.py` | Implicit authority mapping |

---

## 2. Boundary Analysis

### 2.1 Dispatcher Boundaries

| File | Line | Pattern | Risk |
|------|------|---------|------|
| `dispatcher.py` | — | `resolve_geometry()` | HIGH — source undeclared |
| `dispatcher.py` | 13 | Geometry non-mutation claim | Behavioral, not enforced |
| `dispatcher.py` | 168 | Provenance format | String format, not schema |

**Boundary Status:** UNCLEAR — geometry source not declared

### 2.2 Plugin Registry Boundaries

| File | Line | Pattern | Risk |
|------|------|---------|------|
| `plugin_registry.py` | 80 | Global singleton | MEDIUM — lifecycle unclear |
| `plugin_registry.py` | — | Plugin routing | MEDIUM — may affect geometry path |

**Boundary Status:** OK — registry routes, does not source geometry

### 2.3 Runtime DTO Boundaries

| DTO | File | Geometry Fields | Risk |
|-----|------|-----------------|------|
| `RuntimeGeometryResolution` | `runtime_results.py` | `geometry_hash`, `source_ref` | LOW — metadata only |
| `CamOperationResult` | `runtime_results.py` | None | OK |
| `RuntimeValidationResult` | `runtime_results.py` | None | OK |

**Boundary Status:** OK — DTOs do not define geometry vocabulary

### 2.4 Authority Mapping Boundaries

| File | Mapping | Pattern | Risk |
|------|---------|---------|------|
| `runtime_support.py` | `BODY_CATEGORY_SUPPORT` | Dict maps CadSemantics → TopologyRuntimeSupport | MEDIUM — implicit consumption |
| `runtime_support.py` | `FEATURE_SUPPORT` | Dict maps features → support level | MEDIUM — implicit authority |

**Boundary Status:** ATTENTION — mappings should be explicit, not implicit dicts

---

## 3. Authority Violation Scan

### 3.1 Does Runtime Define Geometry Vocabulary?

| Check | Result | Evidence |
|-------|--------|----------|
| Geometry enums in runtime | NO | No geometry enums in `cam/runtime/` |
| Geometry terms in DTOs | NO | DTOs reference geometry, don't define |
| Geometry vocabulary in dispatcher | NO | Dispatcher consumes, doesn't define |

**Finding:** Runtime does NOT define geometry vocabulary. ✓

### 3.2 Does Runtime Mutate Geometry?

| Check | Result | Evidence |
|-------|--------|----------|
| Dispatcher mutation | CLAIM NO | Behavioral claim at line 13 |
| Plugin mutation | UNKNOWN | Plugins may mutate |
| Adapter normalization | POSSIBLE | Adapters may collapse semantics |

**Finding:** Mutation claim exists but is not type-enforced. ⚠

### 3.3 Does Runtime Source Geometry?

| Check | Result | Evidence |
|-------|--------|----------|
| `resolve_geometry()` source | UNDECLARED | ASM-001 |
| Plugin geometry provision | POSSIBLE | Plugins may provide geometry |
| Adapter geometry injection | POSSIBLE | Adapters may inject |

**Finding:** Geometry source is undeclared. ⚠ (Critical gap)

---

## 4. Identified Boundary Violations

### 4.1 ASM-001: Geometry Source Undeclared

| Aspect | Value |
|--------|-------|
| Location | `dispatcher.py` |
| Pattern | `resolve_geometry()` has no declared source |
| Impact | Geometry may come from undeclared authority |
| Resolution | Declare geometry source in authority chain |

### 4.2 Implicit Authority Mapping

| Aspect | Value |
|--------|-------|
| Location | `runtime_support.py:BODY_CATEGORY_SUPPORT` |
| Pattern | Dict implicitly maps CadSemantics to TopologyBuilder |
| Impact | Authority transition is implicit, not documented |
| Resolution | Make mapping explicit with documented rationale |

### 4.3 Potential Adapter Collapse

| Aspect | Value |
|--------|-------|
| Location | Plugin adapters (various) |
| Pattern | Adapters may normalize geometry for plugin consumption |
| Impact | Semantic distinctions may be collapsed |
| Resolution | Audit adapter conversion logic |

---

## 5. Runtime Propagation Paths

### 5.1 Where Operational Propagation May Harden

| Path | Start | End | Risk |
|------|-------|-----|------|
| Intent → Result | CamIntent | CamOperationResult | LOW — result metadata only |
| Geometry → Plugin | resolve_geometry() | Plugin | MEDIUM — source unclear |
| Plugin → Topology | Plugin output | TopologyBuilder | MEDIUM — plugin may define |
| Topology → Export | TopologyBuilder | Translator | LOW — serialization only |

### 5.2 Hardening Points

| Point | Description | Evidence |
|-------|-------------|----------|
| `BODY_CATEGORY_SUPPORT` | Operational mapping becoming semantic authority | Dict is de-facto authority |
| `FEATURE_SUPPORT` | Feature classification hardening | Dict is de-facto authority |
| Plugin defaults | Plugin may provide default geometry | Needs plugin audit |

---

## 6. Enforcement Gaps

### 6.1 Claims Without Enforcement

| Claim | Location | Enforcement |
|-------|----------|-------------|
| "Runtime does not mutate geometry" | `dispatcher.py:13` | Behavioral only |
| "Runtime does not persist RMOS runs" | `dispatcher.py:14` | Behavioral only |
| "Plugins consume geometry" | Architecture doc | Not verified |

### 6.2 Proposed Enforcement

| Gap | Proposed Fix | Phase |
|----|--------------|-------|
| Geometry mutation | `Literal[False]` type or validator | Implementation |
| RMOS persistence | `Literal[False]` type or validator | Implementation |
| Plugin authority | Plugin capability manifest | Implementation |

---

## 7. Validator Enforcement Review

### 7.1 Do Validators Repair Geometry?

| Validator | Location | Behavior | Risk |
|-----------|----------|----------|------|
| ShellValidator | `topology_builder/` | Reports, does not repair | OK |
| TopologyValidator | `topology_builder/` | Reports, does not repair | OK |
| ExportValidator | `export/` | Gates, does not repair | OK |

**Finding:** Validators do not repair geometry. ✓

### 7.2 Validator Authority Status

| Validator | Has Authority | Evidence |
|-----------|---------------|----------|
| ShellValidator | NO — consumer | Reports quality |
| TopologyValidator | NO — consumer | Reports conformance |
| ExportValidator | NO — consumer | Gates export |

**Finding:** Validators are consumers, not authorities. ✓

---

## 8. T2 Findings Summary

### 8.1 Boundary Status

| Boundary | Status | Action |
|----------|--------|--------|
| Runtime vocabulary definition | OK | None |
| Runtime geometry mutation | UNCLEAR | Add type enforcement |
| Runtime geometry sourcing | VIOLATION | Declare source |
| Implicit authority mapping | ATTENTION | Make explicit |
| Adapter normalization | UNKNOWN | Audit required |
| Validator repair | OK | None |

### 8.2 Critical Gaps

| Gap | Severity | Resolution |
|-----|----------|------------|
| Geometry source undeclared | HIGH | Authority chain declaration |
| `BODY_CATEGORY_SUPPORT` implicit | MEDIUM | Explicit mapping documentation |
| Mutation claim unenforced | MEDIUM | Type-level enforcement |

### 8.3 Positive Findings

| Finding | Evidence |
|---------|----------|
| Runtime does not define geometry vocabulary | No enums in runtime |
| Validators are consumers | No repair behavior |
| DTOs reference, don't define | Metadata fields only |

---

## 9. Required Actions

### 9.1 For C2-A Packet Completion

| Action | Owner | Status |
|--------|-------|--------|
| Document geometry source | T3 | Pending |
| Make implicit mappings explicit | T3 | Pending |
| Audit plugin adapters | T2 | Pending |

### 9.2 For Implementation Phase

| Action | Owner | Status |
|--------|-------|--------|
| Add mutation enforcement | Implementation | Deferred |
| Add plugin capability manifest | Implementation | Deferred |
| Document adapter behavior | Implementation | Deferred |

---

## 10. Cross-Reference

| Document | Relationship |
|----------|--------------|
| `C2A_GEOMETRY_AUTHORITY_PACKET.md` | Parent packet |
| `GEOMETRY_OWNERSHIP_TOPOLOGY.md` | T1 companion |
| `EXPORT_GEOMETRY_AUTHORITY_REVIEW.md` | T5 companion |
| `C1_RUNTIME_CAM_INVENTORY.md` | Evidence source |
| `RUNTIME_ASSUMPTION_INVENTORY.md` | Evidence source |

---

## T2 Status

**Draft complete.** Adapter audit deferred to implementation phase. Critical finding: geometry source undeclared (ASM-001) remains the primary gap.
