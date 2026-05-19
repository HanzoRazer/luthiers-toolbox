# C1 Domain Health Matrix

**Status:** C1 OBSERVATIONAL — NOT EVALUATIVE  
**Date:** 2026-05-18  
**Purpose:** Characterize governance health across domains for federation visibility  
**Authority:** OBSERVATIONAL ONLY — does not rank or punish

---

## Observational Principle

```
This matrix characterizes stabilization visibility.
This matrix does not evaluate domain quality.
```

Health classifications are derived from inventory evidence with brief justification. This is a federation observability artifact, not a report card.

---

## Domain Health Matrix

| Domain | Inventory Coverage | Governance Health | Pressure Type | Collision Severity | Authority Risk | C1 Status |
|--------|-------------------|-------------------|---------------|-------------------|----------------|-----------|
| Acoustics | HIGH | HIGH | disciplined consumer | LOW | LOW | COMPLETE |
| Runtime/CAM | HIGH | MEDIUM-HIGH | operational authority consumption | MEDIUM | HIGH | COMPLETE |
| Geometry/Topology | HIGH | LOW-MEDIUM | unresolved authority origin | HIGH | CRITICAL | COMPLETE |
| IBG | HIGH | EXPERIMENTAL | ontology incubation pressure | HIGH | HIGH | COMPLETE (sandbox) |
| Governance | HIGH | MEDIUM | arbitration pressure | MEDIUM | MEDIUM | COMPLETE |
| Export | LOW | UNKNOWN | serialization authority | UNKNOWN | MEDIUM (inferred) | PARTIAL |
| RMOS | LOW | UNKNOWN | workflow authority | UNKNOWN | UNKNOWN | PARTIAL |
| Vectorizer | LOW | UNKNOWN | extraction authority | UNKNOWN | MEDIUM (inferred) | PARTIAL |
| MRP | LOW | UNKNOWN | reconstruction authority | UNKNOWN | UNKNOWN | PARTIAL |

---

## Health Justifications

### Acoustics — HIGH

**Rationale:**
- Bounded authority: measurement semantics clearly separated from prediction
- Explicit assumptions: observer_id, device_id, capture_timestamp documented
- Clean provenance decomposition: all entries map to single provenance types
- Low collision density: no overlapping vocabulary with other domains
- No implicit ontology escalation observed

**Supporting evidence:** PROVENANCE_INVENTORY_C1, AUTHORITY_INVENTORY_C1

**Governance implication:** Reference model for disciplined consumer behavior.

---

### Runtime/CAM — MEDIUM-HIGH

**Rationale:**
- Strong structural safety: hard invariants via Pydantic Literal types
- Explicit dispatch semantics: 5-stage chain with provenance
- Registered authority: CAM Runtime Dispatcher in CANONICAL_AUTHORITY_MAP
- DEDUCTION: Undeclared geometry authority dependency (ASM-2026-0001)
- DEDUCTION: Validation gate duplication (COL-2026-0003)

**Supporting evidence:** RUNTIME_ASSUMPTION_INVENTORY, SEMANTIC_COLLISION_LOG, C1_GOVERNANCE_INVENTORY

**Governance implication:** Operationally mature but with hidden authority dependencies that must be declared.

---

### Geometry/Topology — LOW-MEDIUM

**Rationale:**
- Unresolved authority origin: multiple systems claim geometry concerns
- High collision density: geometry_data vs geometry_presentation unresolved
- Cross-domain dependency: CAM, Export, Visualization, Topology, Morphology, IBG
- C0 decomposition exists: 5-layer model created but not yet operational
- CRITICAL: Central unresolved dependency for repository

**Supporting evidence:** COL-2026-0004, GEOMETRY_AUTHORITY_DECOMPOSITION, C1_STRATEGIC_FINDINGS

**Governance implication:** Requires priority C2 reconciliation. Touches all manufacturing domains.

---

### IBG — EXPERIMENTAL

**Rationale:**
- Classified as sandbox/pre-governance: not mainline authority
- High semantic pressure: zone Y-ranges, variant rules, primitive grammar
- Active ontology incubation: structural constraints emerging
- Morphology Harvest normalization: classification pressure observed
- Contained but pressurizing: sandbox boundary holding but under strain

**Supporting evidence:** AUTHORITY_INVENTORY_C1 (sandbox classification), C1_STRATEGIC_FINDINGS (Finding 5)

**Governance implication:** High-pressure experimental semantic surface. Must be federated, not suppressed.

---

### Governance — MEDIUM

**Rationale:**
- Self-referential complexity: governance documents define governance vocabulary
- Tier terminology collision: CRITICAL collision affects multiple documents
- C0 stabilization achieved: constitutional layer created
- Active semantic infrastructure: C0 documents exert semantic pressure
- Meta-governance gap: governance systems not fully inventoried until now

**Supporting evidence:** C1_GOVERNANCE_INVENTORY, COL-2026-0007

**Governance implication:** Governance must govern itself. C1_GOVERNANCE_INVENTORY closes visibility gap.

---

### Export — UNKNOWN (LOW coverage)

**Rationale:**
- Inventory coverage insufficient for characterization
- Inferred authority risk: serialization may redefine geometry semantics
- DXF writer centralization incomplete (per CLAUDE.md)
- Export-time normalization potential not yet observed

**Supporting evidence:** CLAUDE.md DXF blocking infrastructure note

**Governance implication:** Requires C1 inventory completion before health assessment.

---

### RMOS — UNKNOWN (LOW coverage)

**Rationale:**
- Inventory coverage insufficient for characterization
- Workflow semantics not inventoried
- Authority relationship to manufacturing not documented
- Potential lifecycle vocabulary collision unverified

**Supporting evidence:** None (inventory gap)

**Governance implication:** Requires C1 inventory completion before health assessment.

---

### Vectorizer — UNKNOWN (LOW coverage)

**Rationale:**
- Inventory coverage insufficient for characterization
- Extraction authority assumptions not documented
- Primitive geometry semantics not inventoried
- Relationship to canonical geometry unclear

**Supporting evidence:** None (inventory gap)

**Governance implication:** Requires C1 inventory completion before health assessment.

---

### MRP — UNKNOWN (LOW coverage)

**Rationale:**
- Inventory coverage insufficient for characterization
- Reconstruction authority not documented
- Relationship to morphology and IBG unclear
- Promotion/lifecycle semantics not inventoried

**Supporting evidence:** None (inventory gap)

**Governance implication:** Requires C1 inventory completion before health assessment.

---

## Coverage Summary

| Coverage Level | Count | Domains |
|----------------|-------|---------|
| HIGH | 5 | Acoustics, Runtime/CAM, Geometry/Topology, IBG, Governance |
| LOW | 4 | Export, RMOS, Vectorizer, MRP |

---

## Collision Severity Summary

| Severity | Count | Domains |
|----------|-------|---------|
| LOW | 1 | Acoustics |
| MEDIUM | 2 | Runtime/CAM, Governance |
| HIGH | 2 | Geometry/Topology, IBG |
| UNKNOWN | 4 | Export, RMOS, Vectorizer, MRP |

---

## Authority Risk Summary

| Risk Level | Count | Domains |
|------------|-------|---------|
| LOW | 1 | Acoustics |
| MEDIUM | 2 | Governance, Export (inferred), Vectorizer (inferred) |
| HIGH | 2 | Runtime/CAM, IBG |
| CRITICAL | 1 | Geometry/Topology |
| UNKNOWN | 2 | RMOS, MRP |

---

## Pressure Type Distribution

| Pressure Type | Count | Domains |
|---------------|-------|---------|
| disciplined consumer | 1 | Acoustics |
| operational authority consumption | 1 | Runtime/CAM |
| unresolved authority origin | 1 | Geometry/Topology |
| ontology incubation pressure | 1 | IBG |
| arbitration pressure | 1 | Governance |
| serialization authority | 1 | Export |
| workflow authority | 1 | RMOS |
| extraction authority | 1 | Vectorizer |
| reconstruction authority | 1 | MRP |

---

## C2 Priority Implications

Based on C1 observations, C2 reconciliation priority appears to be:

| Priority | Domain | Rationale |
|----------|--------|-----------|
| 1 | Geometry/Topology | Central unresolved dependency, CRITICAL authority risk |
| 2 | Tier Terminology | Affects Governance, Promotion, Scripts — CRITICAL collision |
| 3 | IBG Federation | High-pressure incubation surface, must be federated |
| 4 | Runtime/CAM Authority | Hidden dependencies must be declared |
| 5 | Under-inventoried domains | Export, RMOS, Vectorizer, MRP need C1 completion |

**Note:** This is observational priority inference, not C2 planning. C2 arbitration has not begun.

---

## Observational Integrity Statement

```
This matrix characterizes C1 coverage and health observations.
Health classifications are evidence-derived, not evaluative.
Domains are not ranked or punished.
Under-inventoried domains are marked, not penalized.
```

---

## Related Documents

- `C1_INVENTORY_INDEX.md` — inventory navigation
- `C1_STRATEGIC_FINDINGS.md` — synthesis layer
- `SEMANTIC_COLLISION_LOG.md` — collision evidence
- `AUTHORITY_INVENTORY_C1.md` — authority evidence

---

*C1 Domain Health Matrix — Observational Phase*
