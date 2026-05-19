# Authority Inventory C1

**Status:** C1 COLLECTION — NOT NORMALIZATION  
**Date:** 2026-05-18  
**Purpose:** Inventory authority claims and assumptions across domains  
**Authority:** EVIDENCE ONLY — does not modify CANONICAL_AUTHORITY_MAP

---

## Collection Methodology

```
C1 makes semantic collisions visible.
C1 does not make semantic decisions.
```

**Classification:**
- registered — in CANONICAL_AUTHORITY_MAP.md
- claimed — system claims authority in documentation/code
- assumed — system behaves as if it has authority
- sandbox — experimental system, pre-governance
- unregistered — no authority claim found

---

## Authority Entry Format

| Field | Description |
|-------|-------------|
| Concern | The semantic concern |
| Claimant | System or component claiming/assuming authority |
| Domain | Primary domain |
| Source Location | File path or document reference |
| Claim Type | registered / claimed / assumed / sandbox / unregistered |
| Canonical Owner | From CANONICAL_AUTHORITY_MAP.md if registered |
| Evidence | Documentation/code showing authority behavior |
| Collision Candidates | Other systems claiming same concern |
| Notes | Interpretation notes |

---

## Inventoried Authority Claims

### Geometry Truth

| Field | Value |
|-------|-------|
| Concern | Geometry truth |
| Claimant | Geometry layer |
| Domain | Instrument Geometry |
| Source Location | `services/api/app/instrument_geometry/` |
| Claim Type | registered |
| Canonical Owner | Geometry layer (per CANONICAL_AUTHORITY_MAP.md) |
| Evidence | Authority map entry |
| Collision Candidates | CAM resolve_geometry(), IBG body grid |
| Notes | Operational owners: IBG, Body Grid |

---

### CAM Intent Definition

| Field | Value |
|-------|-------|
| Concern | CAM intent semantics |
| Claimant | CAM ontology layer |
| Domain | CAM |
| Source Location | `services/api/app/cam/` |
| Claim Type | registered |
| Canonical Owner | CAM ontology layer (per CANONICAL_AUTHORITY_MAP.md) |
| Evidence | Authority map entry |
| Collision Candidates | None identified |
| Notes | Operational owners: Intent schemas, Workflow specs |

---

### CAM Runtime Dispatch

| Field | Value |
|-------|-------|
| Concern | CAM runtime dispatch authority |
| Claimant | CAM Runtime Dispatcher |
| Domain | CAM |
| Source Location | `services/api/app/cam/runtime/dispatcher.py` |
| Claim Type | registered |
| Canonical Owner | Runtime layer (per CANONICAL_AUTHORITY_MAP.md) |
| Evidence | Authority map entry, dispatcher implementation |
| Collision Candidates | None identified |
| Notes | Dispatcher routes but does not authorize machine execution |

---

### Geometry Resolution (Undeclared)

| Field | Value |
|-------|-------|
| Concern | Geometry resolution/transformation |
| Claimant | CAM Runtime Dispatcher (`resolve_geometry()`) |
| Domain | CAM |
| Source Location | `services/api/app/cam/runtime/dispatcher.py` |
| Claim Type | assumed |
| Canonical Owner | NOT REGISTERED |
| Evidence | `resolve_geometry()` method transforms intent to geometry without explicit authority grant |
| Collision Candidates | Geometry layer (canonical owner of geometry truth) |
| Notes | PRIORITY — see RUNTIME_ASSUMPTION_INVENTORY; potential Invariant 2 violation if this becomes geometry definition |

---

### Validation Semantics

| Field | Value |
|-------|-------|
| Concern | Validation rule definition |
| Claimant | Validation layer |
| Domain | Cross-domain |
| Source Location | `services/api/app/cam/runtime/runtime_results.py` (validation gate) |
| Claim Type | registered |
| Canonical Owner | Validation layer (per CANONICAL_AUTHORITY_MAP.md) |
| Evidence | Authority map entry |
| Collision Candidates | None identified |
| Notes | Validation systems may not claim authority over what they validate |

---

### Export Lifecycle

| Field | Value |
|-------|-------|
| Concern | Export lifecycle governance |
| Claimant | Export governance layer |
| Domain | CAM / Export |
| Source Location | `services/api/app/routers/export/` |
| Claim Type | registered |
| Canonical Owner | Export governance layer (per CANONICAL_AUTHORITY_MAP.md) |
| Evidence | Authority map entry |
| Collision Candidates | Runtime dispatchers |
| Notes | Operational owners: CAM Export, DXF Writer |

---

### Provenance Lineage

| Field | Value |
|-------|-------|
| Concern | Provenance definition |
| Claimant | Governance layer |
| Domain | Governance |
| Source Location | `docs/governance/CANONICAL_PROVENANCE_MODEL.md` |
| Claim Type | registered |
| Canonical Owner | Governance layer (per CANONICAL_AUTHORITY_MAP.md) |
| Evidence | Authority map entry, C0 provenance model |
| Collision Candidates | Runtime provenance field (list[str]) |
| Notes | Runtime systems produce provenance records; governance owns provenance semantics |

---

### Morphology Classification (Sandbox)

| Field | Value |
|-------|-------|
| Concern | Morphology classification vocabulary |
| Claimant | IBG Body Grid |
| Domain | IBG (Sandbox) |
| Source Location | `services/api/app/instrument_geometry/body/ibg/` |
| Claim Type | sandbox |
| Canonical Owner | NOT REGISTERED — sandbox/pre-governance |
| Evidence | IBG morphology harvest creates classification vocabulary |
| Collision Candidates | Geometry layer (body geometry authority) |
| Notes | IBG is experimental; produces evidence, not ontology; see EXPERIMENTAL_ONTOLOGY_POLICY |

---

### Vocabulary Definition

| Field | Value |
|-------|-------|
| Concern | Canonical vocabulary definition |
| Claimant | Governance layer |
| Domain | Governance |
| Source Location | `docs/governance/CANONICAL_ONTOLOGY_VOCABULARY.md` |
| Claim Type | registered |
| Canonical Owner | Governance layer (per CANONICAL_AUTHORITY_MAP.md) |
| Evidence | Authority map entry |
| Collision Candidates | Domain-local vocabulary (CAM, RMOS, etc.) |
| Notes | No subsystem may independently create canonical vocabulary |

---

### Authority Assignment

| Field | Value |
|-------|-------|
| Concern | Authority assignment |
| Claimant | Governance layer |
| Domain | Governance |
| Source Location | `docs/governance/CANONICAL_AUTHORITY_MAP.md` |
| Claim Type | registered |
| Canonical Owner | Governance layer (per CANONICAL_AUTHORITY_MAP.md) |
| Evidence | Authority map entry |
| Collision Candidates | None (self-referential) |
| Notes | No system may self-grant authority |

---

## Pending Discovery

Authority claims to investigate:

- [ ] RMOS workflow authority
- [ ] MRP promotion authority
- [ ] Acoustic measurement authority
- [ ] Blueprint vectorizer extraction authority
- [ ] Wood species data authority

---

## Authority Statistics by Claim Type

| Claim Type | Count |
|------------|-------|
| registered | 8 |
| claimed | 0 |
| assumed | 1 |
| sandbox | 1 |
| unregistered | 0 |
| **Total** | **10** |

---

## Related Documents

- `CANONICAL_AUTHORITY_MAP.md` — canonical authority registry
- `SEMANTIC_COLLISION_LOG.md` — collision candidates
- `RUNTIME_ASSUMPTION_INVENTORY.md` — undeclared runtime assumptions
- `GEOMETRY_AUTHORITY_DECOMPOSITION.md` — geometry layer ownership

---

*Authority Inventory C1 — Collection Phase*
