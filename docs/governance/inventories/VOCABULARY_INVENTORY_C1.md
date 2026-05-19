# Vocabulary Inventory C1

**Status:** C1 COLLECTION — NOT NORMALIZATION  
**Date:** 2026-05-18  
**Purpose:** Per-term semantic inventory with domain/source tracking  
**Authority:** EVIDENCE ONLY — does not create canonical status

---

## Collection Methodology

```
C1 makes semantic collisions visible.
C1 does not make semantic decisions.
```

**Collection method:** Hybrid
1. Automated discovery (grep for term definitions, enums, constants)
2. Manual curation (fill domain, source, collision candidates)

---

## Inventory Format

Each term entry uses this structure:

| Field | Description |
|-------|-------------|
| Term | The vocabulary term |
| Domain | Primary domain (CAM, MRP, IBG, Acoustics, Governance, etc.) |
| Source Location | File path or document reference |
| Definition Found | Actual definition text or inferred meaning |
| Canonical Reference | Link to CANONICAL_ONTOLOGY_VOCABULARY.md entry if exists |
| Collision Candidates | Other terms with overlapping/conflicting meaning |
| Classification | canonical / domain-local / sandbox / unregistered |
| Notes | Interpretation notes |

---

## Vocabulary Entries

### status

| Field | Value |
|-------|-------|
| Term | status |
| Domain | CROSS-DOMAIN COLLISION |
| Source Location | Multiple — see below |
| Definition Found | Multiple competing definitions |
| Canonical Reference | Not in CANONICAL_ONTOLOGY_VOCABULARY.md |
| Collision Candidates | dispatch_status, result_status, workflow_status, promotion_status |
| Classification | unregistered |
| Notes | PRIORITY 1 collision — 4+ different meanings across domains |

**Usage locations:**

| Location | Meaning | Domain |
|----------|---------|--------|
| `cam/runtime/operation_manifest.py` | Dispatch outcome | CAM |
| `cam/runtime/runtime_results.py` | Result availability | CAM |
| RMOS workflow | Workflow state | RMOS |
| MRP promotion | Promotion readiness | MRP |

---

### available

| Field | Value |
|-------|-------|
| Term | available |
| Domain | CAM |
| Source Location | `services/api/app/cam/runtime/runtime_results.py` |
| Definition Found | Result successfully produced |
| Canonical Reference | None |
| Collision Candidates | None identified |
| Classification | domain-local |
| Notes | CAM result status vocabulary |

---

### placeholder

| Field | Value |
|-------|-------|
| Term | placeholder |
| Domain | CAM |
| Source Location | `services/api/app/cam/runtime/runtime_results.py` |
| Definition Found | Stub result, not yet implemented |
| Canonical Reference | None |
| Collision Candidates | None identified |
| Classification | domain-local |
| Notes | CAM result status vocabulary |

---

### unsupported

| Field | Value |
|-------|-------|
| Term | unsupported |
| Domain | CAM / Topology |
| Source Location | `cam/runtime/runtime_results.py`, `cam/topology_builder/` |
| Definition Found | Operation not supported / Runtime not supported |
| Canonical Reference | None |
| Collision Candidates | UNSUPPORTED_RUNTIME (Topology) |
| Classification | domain-local (collision candidate) |
| Notes | Overlaps with Topology vocabulary — see SEMANTIC_COLLISION_LOG |

---

### error

| Field | Value |
|-------|-------|
| Term | error |
| Domain | CAM |
| Source Location | `services/api/app/cam/runtime/runtime_results.py` |
| Definition Found | Runtime error occurred |
| Canonical Reference | None |
| Collision Candidates | runtime_error (dispatch status) |
| Classification | domain-local |
| Notes | Generic term — may need disambiguation |

---

### unsupported_operation

| Field | Value |
|-------|-------|
| Term | unsupported_operation |
| Domain | CAM |
| Source Location | `services/api/app/cam/runtime/operation_manifest.py` |
| Definition Found | No plugin registered for operation type |
| Canonical Reference | None |
| Collision Candidates | unsupported (result status) |
| Classification | domain-local |
| Notes | CAM dispatch status vocabulary |

---

### validated_only

| Field | Value |
|-------|-------|
| Term | validated_only |
| Domain | CAM |
| Source Location | `services/api/app/cam/runtime/operation_manifest.py` |
| Definition Found | Validation passed, no further execution |
| Canonical Reference | None |
| Collision Candidates | None identified |
| Classification | domain-local |
| Notes | CAM dispatch status vocabulary |

---

### planned_placeholder

| Field | Value |
|-------|-------|
| Term | planned_placeholder |
| Domain | CAM |
| Source Location | `services/api/app/cam/runtime/operation_manifest.py` |
| Definition Found | Planning stub completed |
| Canonical Reference | None |
| Collision Candidates | placeholder (result status) |
| Classification | domain-local |
| Notes | CAM dispatch status vocabulary |

---

### runtime_error

| Field | Value |
|-------|-------|
| Term | runtime_error |
| Domain | CAM |
| Source Location | `services/api/app/cam/runtime/operation_manifest.py` |
| Definition Found | Exception during dispatch |
| Canonical Reference | None |
| Collision Candidates | error (result status) |
| Classification | domain-local |
| Notes | CAM dispatch status vocabulary |

---

### green / yellow / red

| Field | Value |
|-------|-------|
| Term | green, yellow, red |
| Domain | CAM |
| Source Location | `cam/runtime/operation_manifest.py`, `cam/runtime/runtime_results.py` |
| Definition Found | Validation gate states (pass / warning / fail) |
| Canonical Reference | None |
| Collision Candidates | CamGate (capabilities.py) |
| Classification | domain-local (duplication candidate) |
| Notes | Duplicated in multiple CAM subsystems — see SEMANTIC_COLLISION_LOG |

---

### observational_only

| Field | Value |
|-------|-------|
| Term | observational_only |
| Domain | CAM |
| Source Location | `services/api/app/cam/runtime/runtime_results.py` |
| Definition Found | Hard invariant: result is observational, not authoritative |
| Canonical Reference | Added to CANONICAL_ONTOLOGY_VOCABULARY.md (Dev 58) |
| Collision Candidates | None |
| Classification | canonical |
| Notes | Structural safety invariant via Literal[True] |

---

### execution_ready

| Field | Value |
|-------|-------|
| Term | execution_ready |
| Domain | CAM |
| Source Location | `services/api/app/cam/runtime/runtime_results.py` |
| Definition Found | Hard invariant: always false — no machine execution authorized |
| Canonical Reference | Added to CANONICAL_ONTOLOGY_VOCABULARY.md (Dev 58) |
| Collision Candidates | None |
| Classification | canonical |
| Notes | Structural safety invariant via Literal[False] |

---

### machine_operation_authorized

| Field | Value |
|-------|-------|
| Term | machine_operation_authorized |
| Domain | CAM |
| Source Location | `cam/runtime/operation_manifest.py`, `cam/runtime/runtime_results.py` |
| Definition Found | Hard invariant: always false — no machine output permitted |
| Canonical Reference | Added to CANONICAL_ONTOLOGY_VOCABULARY.md (Dev 58) |
| Collision Candidates | None |
| Classification | canonical |
| Notes | Structural safety invariant via Literal[False] |

---

### machine_output_generated

| Field | Value |
|-------|-------|
| Term | machine_output_generated |
| Domain | CAM |
| Source Location | `services/api/app/cam/runtime/runtime_results.py` |
| Definition Found | Hard invariant: always false — no machine output produced |
| Canonical Reference | Added to CANONICAL_ONTOLOGY_VOCABULARY.md (Dev 58) |
| Collision Candidates | None |
| Classification | canonical |
| Notes | Structural safety invariant via Literal[False] |

---

## Pending Discovery

Terms to inventory (automated scan needed):

- [ ] MRP lifecycle terms
- [ ] RMOS workflow terms
- [ ] IBG morphology terms (sandbox classification)
- [ ] Acoustics measurement terms
- [ ] Blueprint vectorizer terms
- [ ] Export governance terms

---

## Related Documents

- `CANONICAL_ONTOLOGY_VOCABULARY.md` — canonical vocabulary registry
- `SEMANTIC_COLLISION_LOG.md` — collision candidates
- `LIFECYCLE_INVENTORY_C1.md` — lifecycle term inventory
- `AUTHORITY_INVENTORY_C1.md` — authority assumption inventory

---

*Vocabulary Inventory C1 — Collection Phase*
