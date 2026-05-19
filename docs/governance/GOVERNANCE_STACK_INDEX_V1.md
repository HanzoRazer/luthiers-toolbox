# Governance Stack Index V1

**Status:** Active  
**Date:** 2026-05-18  
**Purpose:** Index of governance stack phases and their relationships

---

## Overview

The governance stack defines the phases of semantic governance work. Each phase has distinct scope and authority boundaries.

---

## C0 — Repository Constitution

**Status:** DRAFT FOR GOVERNANCE RATIFICATION  
**Location:** `REPOSITORY_CONSTITUTION.md`

C0 is the constitutional layer. It defines:
- Semantic authority invariants
- Ratification model
- Runtime authority boundaries
- Experimental containment rules
- CI authority boundaries

C0 governs all other governance phases.

```
C0 defines how semantic authority becomes legitimate.
C0 does not itself make disputed semantics legitimate.
```

---

## C1 — Semantic Inventory Federation

**Status:** Active  
**Location:** `inventory/C1_SEMANTIC_INVENTORY_INDEX.md`

C1 operates downstream of C0.

C1 produces observational inventory artifacts:
- Semantic inventories per sprint
- Authority inventories per sprint
- Lifecycle inventories per sprint
- Provenance inventories per sprint
- Geometry semantics inventories per sprint
- Runtime assumption inventories per sprint
- Semantic collision logs per sprint

C1 findings do not create authority.  
C1 findings feed later reconciliation.

### C1 Core Rule

```
C1 inventories semantic reality.
C1 does not normalize, ratify, enforce, or migrate semantics.
```

### C1 Sprint Inventory Locations

| Terminal | Sprint | Directory |
|----------|--------|-----------|
| 1 | Governance Integration | `inventory/governance_integration/` |
| 2 | Runtime/CAM | `inventory/runtime_cam/` |
| 3 | Geometry/Morphology/Topology | `inventory/geometry_morphology_topology/` |
| 4 | Acoustics/Observational | `inventory/acoustics_observational/` |

### C1 Outputs

- `C1_CROSS_SPRINT_SEMANTIC_DIFF.md` — Cross-sprint overlap report
- `C1_DRIFT_CLASSIFICATION_REPORT.md` — Drift type classification

---

## C2 — Semantic Reconciliation

**Status:** Not Started  
**Prerequisite:** C1 Completion

C2 operates downstream of C1.

C2 consumes C1 collision logs and proposes:
- Term consolidation
- Authority assignments
- Lifecycle normalization

C2 proposals require ratification under C0 rules.

```
C2 proposes semantic resolutions.
C2 does not unilaterally implement resolutions.
```

---

## C3 — Semantic Enforcement

**Status:** Not Started  
**Prerequisite:** C2 Ratification

C3 operates downstream of C2.

C3 implements:
- CI enforcement for ratified rules
- Schema validation for ratified vocabulary
- Authority boundary enforcement

C3 enforces ratified decisions. C3 does not define enforcement targets.

```
C3 enforces what C0-C2 ratified.
C3 does not define what to enforce.
```

---

## Phase Dependencies

```
C0 (Constitution)
 │
 ├─→ C1 (Inventory)      [no semantic authority]
 │    │
 │    └─→ C2 (Reconciliation)  [proposes, does not decide]
 │         │
 │         └─→ C3 (Enforcement)  [enforces ratified decisions]
 │
 └─→ All phases operate under C0 constitutional constraints
```

---

## Governance Phase Rules

| Phase | May | May Not |
|-------|-----|---------|
| C0 | Define invariants, ratification model | Ratify specific vocabulary |
| C1 | Inventory semantics, log collisions | Resolve collisions, rename terms |
| C2 | Propose resolutions, draft consolidation | Bypass ratification |
| C3 | Enforce ratified rules | Define new rules |

---

## Related Documents

- `REPOSITORY_CONSTITUTION.md` — C0 constitutional layer
- `inventory/C1_SEMANTIC_INVENTORY_INDEX.md` — C1 index
- `GOVERNANCE_RATIFICATION_MODEL.md` — Ratification workflow
- `CANONICAL_ONTOLOGY_VOCABULARY.md` — Vocabulary registry
- `CANONICAL_AUTHORITY_MAP.md` — Authority assignments

---

*Governance Stack Index — Version 1*
