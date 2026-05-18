# C2 Provenance Boundary Decomposition

```
C2-C — CONSTITUTIONAL ARBITRATION PHASE
PROVENANCE BOUNDARY DECOMPOSITION
TRACEABILITY LAYER ARCHITECTURE
```

**Phase:** C2-C  
**Owner:** Terminal 4 (Provenance/Observational) Lead  
**Date:** 2026-05-18  
**Status:** Decomposition Complete — Awaiting Cross-Terminal Review

---

## 1. Authority Statement

This document decomposes provenance boundaries for constitutional arbitration.

This document does NOT:
- Unify provenance systems
- Centralize provenance authority
- Normalize provenance semantics
- Mandate implementation
- Create enforcement rules

This document DOES:
- Decompose provenance categories
- Map provenance to geometry layers
- Define propagation requirements
- Identify collapse risks
- Preserve provenance plurality

---

## 2. Constitutional Basis

### Core Principle

```
Provenance is not a metadata detail.
Provenance is the constitutional traceability layer
that prevents semantic authority collapse.
```

### C2-A/C2-B Foundation

| Phase | Established |
|-------|-------------|
| C2-A | 7 geometry authority layers |
| C2-B | 3 topology namespaces + continuity independence |
| C2-C | Provenance boundaries for all layers |

### Why Provenance Decomposition Is Required

Without provenance decomposition:
- Derived values silently escalate to authority
- Sandbox semantics acquire canonical status
- Observational data becomes definitional
- Runtime state becomes governance truth
- Export format becomes semantic authority

### Critical Insight

```
C2-A proved: geometry is not singular.
C2-B proved: topology is not singular.
C2-C proves: truth lineage is not singular.

Federated semantic systems
require federated provenance systems.
```

---

## 3. Provenance Category Decomposition

### 3.1 Candidate Provenance Classes (7)

| Category | Code | Purpose | Question Answered |
|----------|------|---------|-------------------|
| `authority_provenance` | `PROV_AUTHORITY` | Governance trail | "Who ratified this truth?" |
| `observational_provenance` | `PROV_OBSERVATIONAL` | Measurement origin | "Where/how was this observed?" |
| `epistemic_provenance` | `PROV_EPISTEMIC` | Confidence tracking | "How certain are we?" |
| `estimate_provenance` | `PROV_DERIVATION` | Derivation origin | "How was this computed?" |
| `runtime_provenance` | `PROV_RUNTIME` | Execution history | "What execution path was taken?" |
| `archive_provenance` | `PROV_ARCHIVE` | Persistence lineage | "When/how was this stored?" |
| `export_provenance` | `PROV_TRANSFORMATION` | Serialization trail | "How was this exported?" |

### 3.2 Category Status

```
These are constitutional candidate provenance classes.
They are NOT final canonical law.
C2-C validates and refines boundaries.
```

### 3.3 Category Independence

```
Each provenance category answers a distinct question.
Categories must NOT collapse into each other.
```

### 3.4 Type Incompatibility Matrix

| Type A | Type B | May Compose? | May Convert? |
|--------|--------|--------------|--------------|
| `PROV_OBSERVATIONAL` | `PROV_DERIVATION` | YES (sequential) | NO |
| `PROV_DERIVATION` | `PROV_AUTHORITY` | NO | NO |
| `PROV_TRANSFORMATION` | `PROV_AUTHORITY` | NO | NO |
| `PROV_RUNTIME` | `PROV_DERIVATION` | YES (parallel) | NO |
| `PROV_EPISTEMIC` | `PROV_AUTHORITY` | NO | NO |

---

## 4. Provenance vs Authority-State Distinction

### 4.1 Critical Separation

```
Provenance: where/how data emerged
Authority-state: governance legitimacy state
```

These are ORTHOGONAL axes. Both are required.

### 4.2 Authority-State Categories

| Authority-State | Meaning |
|-----------------|---------|
| `canonical` | Constitutionally ratified |
| `sandbox` | Pre-governance experimental |
| `advisory` | Consumable but non-authoritative |
| `operational` | Runtime-scoped validity |
| `derived` | Computed from authoritative source |

### 4.3 Why This Distinction Matters

```
Sandbox is NOT a provenance type.
Sandbox is a governance legitimacy state.
```

If sandbox becomes provenance:
- Provenance and authority-state collapse
- Sandbox data with good provenance appears canonical
- Authority boundaries become invisible

### 4.4 Correct Modeling

| Data | Provenance | Authority-State |
|------|------------|-----------------|
| IBG zone radius | PROV_DERIVATION | sandbox |
| Measured Helmholtz | PROV_OBSERVATIONAL | canonical |
| Cached dimension | PROV_ARCHIVE | derived |
| Exported DXF | PROV_TRANSFORMATION | serialized |

Both axes required. Neither subsumes the other.

---

## 5. Advisory-Only Relationship

### 5.1 Advisory Is Not Provenance

```
advisory_only is an authority constraint modifier.
It is NOT a provenance category.
```

### 5.2 Three Orthogonal Axes

| Axis | Purpose |
|------|---------|
| Provenance | Where information came from |
| Authority-state | What governance status it has |
| Advisory-only | What authority it may exert |

### 5.3 Correct Modeling

| Data | Provenance | Authority-State | Advisory |
|------|------------|-----------------|----------|
| IBG morphology class | PROV_DERIVATION | sandbox | advisory_only: true |
| Measured frequency | PROV_OBSERVATIONAL | canonical | advisory_only: false |
| Computed dimension | PROV_DERIVATION | derived | advisory_only: varies |

All three axes required for complete semantic classification.

---

## 6. Geometry Layer → Provenance Mapping

### 6.1 Mandatory Provenance Requirements

| Geometry Layer | Primary Provenance | Secondary Provenance | Authority-State |
|----------------|-------------------|---------------------|-----------------|
| authoritative_geometry | PROV_AUTHORITY | — | canonical |
| derived_geometry | PROV_DERIVATION | PROV_EPISTEMIC | derived |
| presentation_geometry | PROV_RUNTIME | PROV_TRANSFORMATION | operational |
| serialized_geometry | PROV_TRANSFORMATION | — | serialized |
| sandbox_geometry | PROV_DERIVATION | — | sandbox |
| operational_geometry | PROV_RUNTIME | — | operational |
| morphology_geometry | PROV_DERIVATION | PROV_OBSERVATIONAL | sandbox/derived |

### 6.2 Mapping Rationale

**authoritative_geometry:**
```
Must carry PROV_AUTHORITY because:
- Defines canonical truth
- Requires governance trail
- Must trace to ratification
```

**derived_geometry:**
```
Must carry PROV_DERIVATION + PROV_EPISTEMIC because:
- Computed from other sources
- Requires derivation chain
- Must carry confidence/assumptions
```

**sandbox_geometry:**
```
Must carry PROV_DERIVATION + sandbox authority-state because:
- Pre-governance status explicit
- Derivation chain required
- Cannot appear canonical
```

### 6.3 Layer Transition Rules

| From Layer | To Layer | Provenance Transition | Permitted? |
|------------|----------|----------------------|------------|
| authoritative → operational | PROV_AUTHORITY → PROV_RUNTIME | YES |
| authoritative → derived | PROV_AUTHORITY → PROV_DERIVATION | YES |
| derived → presentation | PROV_DERIVATION → PROV_TRANSFORMATION | YES |
| derived → authoritative | PROV_DERIVATION → PROV_AUTHORITY | NO |
| sandbox → any | sandbox → other authority-state | NO (governance gate) |

---

## 7. Topology Namespace → Provenance Mapping

### 7.1 Topology Provenance Requirements

| Topology Namespace | Required Provenance | Authority-State |
|--------------------|---------------------|-----------------|
| morphology_topology | PROV_AUTHORITY | canonical (MRP) |
| surface_topology | PROV_RUNTIME | operational (CAM) |
| manufacturing_topology | PROV_RUNTIME | operational (CAM) |
| manufacturing_continuity | PROV_RUNTIME | operational (CAM) |

### 7.2 Cross-Topology Provenance

When crossing topology namespaces:

```
Semantic boundary provenance required.
```

| Crossing | Provenance Requirement |
|----------|------------------------|
| morphology_topology → surface_topology | Transformation provenance |
| surface_topology → manufacturing_topology | Runtime derivation provenance |
| Any → export | Export provenance + source topology |

---

## 8. Propagation Provenance Requirements

### 8.1 IBG → Export Propagation

```
Sandbox containment provenance required.
```

| Requirement | Purpose |
|-------------|---------|
| Preserve sandbox authority-state | Prevent canonical appearance |
| Carry PROV_DERIVATION | Show derivation chain |
| Tag with advisory_only | Prevent authority consumption |

### 8.2 Derived → Cached Propagation

```
Derivation persistence provenance required.
```

| Requirement | Purpose |
|-------------|---------|
| Preserve PROV_DERIVATION | Maintain derivation chain |
| Carry PROV_EPISTEMIC | Preserve confidence/assumptions |
| Add PROV_ARCHIVE | Document persistence |

### 8.3 Cross-Topology Propagation

```
Semantic boundary provenance required.
```

| Requirement | Purpose |
|-------------|---------|
| Document source topology | Prevent semantic confusion |
| Document transformation | Track meaning change |
| Preserve authority-state | Prevent escalation |

### 8.4 Runtime → Export Propagation

```
Operational transformation provenance required.
```

| Requirement | Purpose |
|-------------|---------|
| Document runtime context | Track operational conditions |
| Preserve PROV_RUNTIME | Maintain execution trail |
| Add PROV_TRANSFORMATION | Document serialization |

### 8.5 Observation → Estimate Propagation

```
Epistemic degradation tracking required.
```

| Requirement | Purpose |
|-------------|---------|
| Document observation source | Preserve original provenance |
| Document estimation method | Track derivation |
| Carry PROV_EPISTEMIC | Reflect derivation uncertainty |
| Carry assumptions | Document estimation caveats |

---

## 9. Derivation Chain Integrity

### 9.1 Requirements

All derived values MUST carry:

| Requirement | Purpose | Enforcement |
|-------------|---------|-------------|
| `provenance_type: PROV_DERIVATION` | Type identification | Structural |
| `derivation_source` | What was derived from | Structural |
| `derivation_algorithm` | How it was derived | Advisory |
| `confidence` | Epistemic certainty | Structural |
| `assumptions` | Epistemic caveats | Structural |

### 9.2 Healthy vs Unhealthy Derivation

**Healthy Derivation:**
```
authoritative_geometry (body_outline)
  └─ PROV_DERIVATION: zone_radii
       derivation_source: body_outline
       derivation_algorithm: radial_distance_from_centerline
       confidence: medium
       assumptions: ["centerline is axis of symmetry"]
       authority_state: derived
```

**Unhealthy Derivation (PROHIBITED):**
```
zone_radii  ← NO provenance
  └─ treated as authoritative  ← CONSTITUTIONAL VIOLATION
```

---

## 10. Collapse Risk Analysis

### 10.1 Critical Collapse Risks

| Collapse | Severity | Mechanism |
|----------|----------|-----------|
| All provenance → generic source | CRITICAL | Single "source" field loses category distinctions |
| Derivation → authority | CRITICAL | Derived values treated as canonical |
| Sandbox → authoritative | CRITICAL | Pre-governance data treated as ratified |

### 10.2 High Collapse Risks

| Collapse | Severity | Mechanism |
|----------|----------|-----------|
| Observational ↔ epistemic | HIGH | Measurement origin merges with confidence |
| Runtime ↔ authority | HIGH | Execution state treated as governance |
| Export ↔ canonical | HIGH | Serialized format treated as truth |

### 10.3 Most Dangerous Collapse

```
Derived provenance silently mutating into authority provenance
```

This is the repository's greatest remaining constitutional risk.

**Mechanism:**
1. Derived value computed with PROV_DERIVATION
2. Value cached without provenance preservation
3. Cached value consumed by another system
4. Consuming system treats as authoritative
5. Authority provenance implicitly assumed

**Prevention:**
- Provenance must propagate through caching
- Derived authority-state must persist
- Consumers must not escalate authority-state

### 10.4 Authority Escalation Prevention Rules

```
RULE E1: Usage frequency does not create authority
RULE E2: Cache persistence does not create authority
RULE E3: Training weight does not create authority
RULE E4: Operational convenience does not create authority
RULE E5: Serialization does not create authority
```

---

## 11. Consumer-Without-Authority Pattern

### 11.1 Pattern Definition

```
A subsystem may consume values from another domain
without acquiring authority over that domain.

Consumption creates observation, not ownership.
```

### 11.2 Pattern Requirements

| Requirement | Implementation |
|-------------|----------------|
| Consumer interface | Explicit interface contract |
| Non-authority marker | `observationalOnly: true` |
| Snapshot semantics | Copy at point in time |
| Source reference | Citation of authoritative source |
| Non-mutation | Consumer may not modify source |

### 11.3 Reference Implementation (Acoustics)

```typescript
// Consumer interface — NOT authority
interface ApertureGeometryLike {
  diameterMm: number;
}

// Non-authority marker
observationalOnly: true  // structural invariant
```

---

## 12. Terminal Review Requirements

### Terminal 4 — Provenance/Observational (Owner)

- [x] Primary decomposition complete
- [x] Category boundaries defined
- [x] Geometry layer mapping complete
- [x] Propagation requirements documented
- [x] Collapse risks identified
- [ ] Cross-terminal feedback incorporation

### Terminal 1 — Governance Integration

- [ ] Validate constitutional discipline preserved
- [ ] Confirm provenance/authority-state separation
- [ ] Review collapse risk documentation
- [ ] Coordinate cross-terminal integration

### Terminal 2 — Runtime/CAM

- [ ] Validate runtime_provenance boundaries
- [ ] Review operational → serialized propagation
- [ ] Confirm topology provenance mapping
- [ ] Flag runtime collapse risks

### Terminal 3 — Geometry/Morphology/Topology

- [ ] Validate geometry layer → provenance mapping
- [ ] Review sandbox provenance requirements
- [ ] Confirm topology namespace provenance
- [ ] Flag geometry collapse risks

### Terminal 5 — Export/Serialization

- [ ] Validate export_provenance boundaries
- [ ] Review IBG → Export propagation
- [ ] Confirm serialization provenance
- [ ] Flag export collapse risks

---

## 13. Provenance Infrastructure Summary

### 13.1 Categories (7)

| Category | Code | Purpose |
|----------|------|---------|
| authority_provenance | PROV_AUTHORITY | Governance trail |
| observational_provenance | PROV_OBSERVATIONAL | Measurement origin |
| epistemic_provenance | PROV_EPISTEMIC | Confidence tracking |
| estimate_provenance | PROV_DERIVATION | Derivation origin |
| runtime_provenance | PROV_RUNTIME | Execution history |
| archive_provenance | PROV_ARCHIVE | Persistence lineage |
| export_provenance | PROV_TRANSFORMATION | Serialization trail |

### 13.2 Authority-States (5)

| State | Purpose |
|-------|---------|
| canonical | Ratified truth |
| sandbox | Pre-governance |
| advisory | Non-authoritative |
| operational | Runtime-scoped |
| derived | Computed |

### 13.3 Constraint Modifiers

| Modifier | Purpose |
|----------|---------|
| advisory_only | Authority constraint |

### 13.4 Geometry Mapping

| Layer | Provenance | Authority-State |
|-------|------------|-----------------|
| authoritative | PROV_AUTHORITY | canonical |
| derived | PROV_DERIVATION + PROV_EPISTEMIC | derived |
| presentation | PROV_RUNTIME | operational |
| serialized | PROV_TRANSFORMATION | serialized |
| sandbox | PROV_DERIVATION | sandbox |
| operational | PROV_RUNTIME | operational |
| morphology | PROV_DERIVATION | sandbox/derived |

---

## 14. Related Documents

### C2-C Documents

- `C2_PROVENANCE_CATEGORY_APPENDIX.md` — Category deepening
- `C2_PROVENANCE_PROPAGATION_REQUIREMENTS.md` — Propagation rules
- `C2_PROVENANCE_COLLAPSE_RISKS.md` — Escalation surfaces
- `packets/C2_PROVENANCE_ARBITRATION_PACKET_003.md` — Formal packet

### C2-A/C2-B Foundation

- `C2_GEOMETRY_AUTHORITY_FRAMEWORK.md` — Geometry layers
- `C2_TOPOLOGY_NAMESPACE_ARBITRATION.md` — Topology namespaces

### C1 Evidence

- `C1_STRATEGIC_FINDINGS.md` — Provenance decomposition findings
- `acoustics_observational/PROVENANCE_INVENTORY.md` — Acoustics provenance

### Pattern Documents

- `CONSUMER_WITHOUT_AUTHORITY_PATTERN.md` — Consumption discipline
- `OBSERVATIONAL_SEMANTICS_BOUNDARY_NOTES.md` — Boundary guidance

---

*C2-C Provenance Boundary Decomposition — Traceability Layer Architecture*
