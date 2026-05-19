# Runtime Assumption Inventory

**Status:** C1 COLLECTION — NOT NORMALIZATION  
**Date:** 2026-05-18  
**Purpose:** Record undeclared runtime authority assumptions  
**Authority:** EVIDENCE ONLY — does not modify CANONICAL_AUTHORITY_MAP

---

## Collection Methodology

```
C1 makes semantic collisions visible.
C1 does not make semantic decisions.
```

This inventory records cases where runtime systems:
- Assume authority not explicitly granted
- Depend on authority not explicitly declared
- Behave as authority without governance grant

---

## Assumption Entry Format

| Field | Description |
|-------|-------------|
| Assumption ID | Unique identifier (ASM-YYYY-NNNN) |
| System | Runtime system making assumption |
| Location | File path |
| Assumed Authority | What authority is assumed |
| Evidence | Code or documentation showing assumption |
| Constitutional Risk | Which invariant might be violated |
| Collision With | What canonical authority this overlaps |
| Status | LOGGED / UNDER_REVIEW / RESOLVED |
| Notes | Interpretation notes |

---

## Logged Assumptions

### ASM-2026-0001: resolve_geometry() Authority

| Field | Value |
|-------|-------|
| Assumption ID | ASM-2026-0001 |
| System | CAM Runtime Dispatcher |
| Location | `services/api/app/cam/runtime/dispatcher.py` |
| Assumed Authority | Geometry transformation/resolution |
| Evidence | `resolve_geometry()` method transforms CAM intent to geometric representation without explicit authority grant |
| Constitutional Risk | Invariant 2: Runtime consumes ontology; runtime does not define ontology |
| Collision With | Geometry layer (canonical owner of geometry truth per CANONICAL_AUTHORITY_MAP.md) |
| Status | LOGGED |
| Notes | PRIORITY — If `resolve_geometry()` evolves to define geometry semantics rather than consume them, this becomes an Invariant 2 violation. Current implementation appears to consume, but authority boundary is implicit. |

---

### ASM-2026-0002: Plugin Authority Scope

| Field | Value |
|-------|-------|
| Assumption ID | ASM-2026-0002 |
| System | CAM Runtime Plugin Registry |
| Location | `services/api/app/cam/runtime/plugin_registry.py` |
| Assumed Authority | Operation type classification |
| Evidence | Plugins register for operation types; registry routes based on operation classification |
| Constitutional Risk | Invariant 1: No subsystem may silently become ontology authority |
| Collision With | CAM ontology layer (canonical owner of CAM intent semantics) |
| Status | LOGGED |
| Notes | Registration creates de facto operation type authority. If plugin registration evolves to define operation types (rather than implement them), this becomes authority assumption. |

---

### ASM-2026-0003: Dispatch Flow Authority

| Field | Value |
|-------|-------|
| Assumption ID | ASM-2026-0003 |
| System | CAM Runtime Dispatcher |
| Location | `services/api/app/cam/runtime/dispatcher.py` |
| Assumed Authority | Stage execution sequence |
| Evidence | Dispatcher defines 5-stage flow: validate → resolve_geometry → plan → preview → export |
| Constitutional Risk | Low (implementation authority is legitimate) |
| Collision With | None — execution sequence is implementation, not ontology |
| Status | LOGGED |
| Notes | This assumption is LIKELY LEGITIMATE — dispatcher authority over execution sequence is implementation, not semantic authority. Logging for completeness. |

---

### ASM-2026-0004: Result ID Generation

| Field | Value |
|-------|-------|
| Assumption ID | ASM-2026-0004 |
| System | CAM Runtime Results |
| Location | `services/api/app/cam/runtime/runtime_results.py` |
| Assumed Authority | Result ID namespace |
| Evidence | Auto-generates `rr_` prefixed IDs |
| Constitutional Risk | None — ID generation is implementation |
| Collision With | None |
| Status | LOGGED |
| Notes | This assumption is LEGITIMATE — runtime may generate IDs within its namespace. Logging for completeness. |

---

### ASM-2026-0005: Validation Gate Interpretation

| Field | Value |
|-------|-------|
| Assumption ID | ASM-2026-0005 |
| System | CAM Runtime Validation |
| Location | `services/api/app/cam/runtime/runtime_results.py` |
| Assumed Authority | Validation gate semantics (green/yellow/red) |
| Evidence | Runtime defines and interprets gate values |
| Constitutional Risk | Invariant 1 if gate semantics become ontology |
| Collision With | CamGate (capabilities.py) — potential duplication |
| Status | LOGGED |
| Notes | See COL-2026-0003 — validation gate semantics are duplicated. If these evolve independently, semantic drift occurs. |

---

### ASM-2026-0006: Hard Invariant Enforcement

| Field | Value |
|-------|-------|
| Assumption ID | ASM-2026-0006 |
| System | CAM Runtime Results |
| Location | `services/api/app/cam/runtime/runtime_results.py` |
| Assumed Authority | Safety invariant enforcement |
| Evidence | Pydantic validators enforce `execution_ready=False`, `machine_operation_authorized=False`, `observational_only=True` |
| Constitutional Risk | None — enforcement is legitimate |
| Collision With | None — aligns with constitutional safety requirements |
| Status | LOGGED |
| Notes | This assumption is LEGITIMATE and DESIRABLE — runtime enforces safety invariants structurally. This is correct behavior. |

---

## Pending Investigation

Assumptions to investigate:

- [ ] RMOS workflow state authority
- [ ] MRP promotion decision authority
- [ ] IBG morphology classification authority (sandbox)
- [ ] Blueprint vectorizer extraction authority
- [ ] Export format selection authority

---

## Assumption Statistics by Constitutional Risk

| Risk Level | Count |
|------------|-------|
| Invariant 2 risk | 1 |
| Invariant 1 risk | 2 |
| Low/None | 3 |
| **Total** | **6** |

---

## Priority Assumptions

| Assumption ID | Risk | Action Candidate |
|---------------|------|------------------|
| ASM-2026-0001 | Invariant 2 | Declare explicit geometry consumption boundary |
| ASM-2026-0002 | Invariant 1 | Clarify plugin registration vs operation definition |
| ASM-2026-0005 | Duplication | Consolidate CamGate semantics |

**Note:** Action candidates are for later phases — C1 does not implement.

---

## Related Documents

- `CANONICAL_AUTHORITY_MAP.md` — canonical authority registry
- `SEMANTIC_COLLISION_LOG.md` — collision candidates
- `AUTHORITY_INVENTORY_C1.md` — authority claims
- `GEOMETRY_AUTHORITY_DECOMPOSITION.md` — geometry layer ownership

---

*Runtime Assumption Inventory — C1 Collection Phase*
