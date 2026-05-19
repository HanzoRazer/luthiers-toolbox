# Semantic Collision Log

**Status:** C1 COLLECTION — NOT NORMALIZATION  
**Date:** 2026-05-18  
**Purpose:** Record semantic collisions for later reconciliation  
**Authority:** EVIDENCE ONLY — does not make semantic decisions

---

## Collection Methodology

```
C1 makes semantic collisions visible.
C1 does not make semantic decisions.
```

This log records:
- Term collisions (same term, different meanings)
- Authority overlaps (multiple systems claiming same concern)
- Lifecycle conflicts (incompatible state machines)
- Provenance ambiguity (unclear provenance type usage)

---

## Collision Entry Format

| Field | Description |
|-------|-------------|
| Collision ID | Unique identifier (COL-YYYY-NNNN) |
| Type | TERM_COLLISION / AUTHORITY_OVERLAP / LIFECYCLE_CONFLICT / PROVENANCE_AMBIGUITY |
| Terms Involved | The conflicting terms or concepts |
| Domains | Which domains are in collision |
| Description | What the collision is |
| Impact | Why this matters |
| Resolution Candidate | Possible resolution (NOT a decision) |
| Status | LOGGED / UNDER_REVIEW / DEFERRED |

---

## Logged Collisions

### COL-2026-0001: Status Vocabulary Collision

| Field | Value |
|-------|-------|
| Collision ID | COL-2026-0001 |
| Type | TERM_COLLISION |
| Terms Involved | status, dispatch_status, result_status, workflow_status, promotion_status |
| Domains | CAM, RMOS, MRP, Runtime Results |
| Description | "status" means different things: dispatch outcome (CAM), result availability (Runtime), workflow state (RMOS), promotion readiness (MRP) |
| Impact | Cross-domain queries using "status" produce inconsistent results; API consumers must know which "status" is meant |
| Resolution Candidate | Domain-prefixed status fields already partially implemented in CAM (dispatch_status); extend pattern to other domains |
| Status | LOGGED |

---

### COL-2026-0002: Unsupported Terminology Overlap

| Field | Value |
|-------|-------|
| Collision ID | COL-2026-0002 |
| Type | TERM_COLLISION |
| Terms Involved | unsupported (CAM result), UNSUPPORTED_RUNTIME (Topology) |
| Domains | CAM, Topology |
| Description | Both domains use "unsupported" but with different scopes: CAM means "operation not supported by any plugin", Topology means "runtime configuration not supported" |
| Impact | Semantic mapping between domains requires understanding which "unsupported" is meant |
| Resolution Candidate | Formal mapping in reconciliation; possibly domain-scoped types |
| Status | LOGGED |

---

### COL-2026-0003: CamGate Duplication

| Field | Value |
|-------|-------|
| Collision ID | COL-2026-0003 |
| Type | TERM_COLLISION |
| Terms Involved | green/yellow/red (validation gate), CamGate enum |
| Domains | CAM Runtime, CAM Capabilities |
| Description | Same traffic-light metaphor used in multiple places with potentially different semantics |
| Impact | Unclear whether all green/yellow/red usages have identical meaning |
| Resolution Candidate | Consolidate to single CamGate definition; all usages reference canonical |
| Status | LOGGED |

---

### COL-2026-0004: Geometry Layer Authority

| Field | Value |
|-------|-------|
| Collision ID | COL-2026-0004 |
| Type | AUTHORITY_OVERLAP |
| Terms Involved | geometry_data, geometry_presentation, resolve_geometry |
| Domains | CAM Runtime, Instrument Geometry, Export |
| Description | `resolve_geometry()` in CAM dispatcher has undeclared dependency on geometry authority; unclear whether it consumes or defines geometry |
| Impact | Potential Invariant 2 violation if runtime begins defining geometry semantics |
| Resolution Candidate | Explicit authority boundary in GEOMETRY_AUTHORITY_DECOMPOSITION.md (C0 doc exists) |
| Status | LOGGED |

---

### COL-2026-0005: Translator Lifecycle vs Governance Lifecycle

| Field | Value |
|-------|-------|
| Collision ID | COL-2026-0005 |
| Type | LIFECYCLE_CONFLICT |
| Terms Involved | translator maturity states, governance lifecycle states |
| Domains | CAM Translators, Governance |
| Description | Translator capabilities use maturity lifecycle (experimental/stable/deprecated) that parallels but does not reference governance lifecycle |
| Impact | Two parallel lifecycle systems may diverge; translator "stable" may not mean governance "canonical" |
| Resolution Candidate | Either unify lifecycles or explicitly document separation |
| Status | LOGGED |

---

### COL-2026-0006: Provenance Semantic Split

| Field | Value |
|-------|-------|
| Collision ID | COL-2026-0006 |
| Type | PROVENANCE_AMBIGUITY |
| Terms Involved | provenance (action log), provenance (epistemic warning), provenance (authority chain) |
| Domains | CAM Runtime, Governance, Audit |
| Description | "provenance" field in runtime results is a list of strings serving multiple purposes: action log ("what happened"), epistemic warning ("why this might be wrong"), authority chain ("who approved this") |
| Impact | Single provenance field conflates different provenance types defined in CANONICAL_PROVENANCE_MODEL.md |
| Resolution Candidate | Split into `action_provenance`, `epistemic_flags`, `authority_chain` per C0 provenance model |
| Status | LOGGED |

---

### COL-2026-0007: Tier Terminology Collision

| Field | Value |
|-------|-------|
| Collision ID | COL-2026-0007 |
| Type | TERM_COLLISION |
| Terms Involved | Tier 1/2/3 (governance hierarchy), Tier 1/2/3 (data promotion) |
| Domains | Governance, Ontology Stack |
| Description | CRITICAL: Both governance hierarchy and data promotion use "Tier 1/2/3" with completely different meanings. Governance: Structural Invariants / Domain Governance / Operational Policies. Data promotion: Canonical / Curated / Staging |
| Impact | Cross-document references using "Tier" are ambiguous |
| Resolution Candidate | Rename data promotion tiers to "stages" in future revision cycle (per governance decision) |
| Status | LOGGED — resolution approach decided but not implemented |

---

### COL-2026-0008: MaterialType Domain Meanings

| Field | Value |
|-------|-------|
| Collision ID | COL-2026-0008 |
| Type | TERM_COLLISION |
| Terms Involved | MaterialType |
| Domains | CAM, Wood Species, potentially others |
| Description | MaterialType may have domain-specific meanings (CAM: cutting material properties, Wood Species: species classification) |
| Impact | Unclear whether MaterialType is a single concept or domain-scoped |
| Resolution Candidate | Record as collision; likely outcome is prefixed/domain-scoped types |
| Status | LOGGED |

---

## Pending Investigation

Collisions to investigate (automated scan needed):

- [ ] IBG primitive vocabulary vs existing body geometry vocabulary
- [ ] bbox vs physical dimensions (measurement convention)
- [ ] serialization geometry vs canonical geometry
- [ ] runtime geometry vs source geometry
- [ ] morphology vs topology terminology

---

## Collision Statistics

| Type | Count |
|------|-------|
| TERM_COLLISION | 6 |
| AUTHORITY_OVERLAP | 1 |
| LIFECYCLE_CONFLICT | 1 |
| PROVENANCE_AMBIGUITY | 1 |
| **Total** | **9** |

---

## Related Documents

- `VOCABULARY_INVENTORY_C1.md` — per-term inventory
- `AUTHORITY_INVENTORY_C1.md` — authority assumption inventory
- `LIFECYCLE_INVENTORY_C1.md` — lifecycle system inventory
- `CANONICAL_ONTOLOGY_VOCABULARY.md` — canonical vocabulary registry
- `ONTOLOGY_DRIFT_CLASSIFICATIONS.md` — drift category definitions

---

*Semantic Collision Log — C1 Collection Phase*
