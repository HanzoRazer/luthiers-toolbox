# C2 Provenance Propagation Requirements

```
C2-C — CONSTITUTIONAL ARBITRATION PHASE
PROVENANCE PROPAGATION RULES
TRACEABILITY CHAIN INTEGRITY
```

**Phase:** C2-C  
**Owner:** Terminal 4 (Provenance/Observational)  
**Date:** 2026-05-18  
**Status:** Requirements Complete — Supporting Document

---

## 1. Purpose

This document defines provenance propagation rules for constitutional arbitration.

It specifies:
- How provenance must propagate across boundaries
- What provenance is required at each transition
- How authority-state must persist
- Where escalation is prohibited

---

## 2. Propagation Principle

### Core Rule

```
Provenance must propagate through all transitions.
Provenance loss creates authority ambiguity.
Authority-state must persist through propagation.
```

### Propagation vs Escalation

```
Propagation: Provenance travels with data
Escalation: Authority-state changes upward

Propagation is required.
Escalation is prohibited.
```

---

## 3. Geometry Layer Propagation

### 3.1 Authoritative → Operational

```
┌─────────────────┐     ┌─────────────────┐
│ authoritative   │ ──► │  operational    │
│ PROV_AUTHORITY  │     │  PROV_RUNTIME   │
│ canonical       │     │  operational    │
└─────────────────┘     └─────────────────┘
```

**Requirements:**
| Requirement | Purpose |
|-------------|---------|
| Reference to authority source | Trace back to ratification |
| Runtime context added | Document execution environment |
| Authority-state changes: canonical → operational | Scope narrowing permitted |

### 3.2 Authoritative → Derived

```
┌─────────────────┐     ┌─────────────────┐
│ authoritative   │ ──► │    derived      │
│ PROV_AUTHORITY  │     │ PROV_DERIVATION │
│ canonical       │     │    derived      │
└─────────────────┘     └─────────────────┘
```

**Requirements:**
| Requirement | Purpose |
|-------------|---------|
| Derivation source references authority | Chain integrity |
| Derivation algorithm documented | Reproducibility |
| PROV_EPISTEMIC added | Confidence tracking |
| Authority-state changes: canonical → derived | Expected degradation |

### 3.3 Derived → Presentation

```
┌─────────────────┐     ┌─────────────────┐
│    derived      │ ──► │  presentation   │
│ PROV_DERIVATION │     │  PROV_RUNTIME   │
│    derived      │     │  operational    │
└─────────────────┘     └─────────────────┘
```

**Requirements:**
| Requirement | Purpose |
|-------------|---------|
| Derivation chain preserved | Source traceability |
| Runtime transformation added | Document display transform |
| Presentation is ephemeral | No persistence as authority |

### 3.4 Derived → Serialized

```
┌─────────────────┐     ┌─────────────────┐
│    derived      │ ──► │   serialized    │
│ PROV_DERIVATION │     │ PROV_TRANSFORM  │
│    derived      │     │   serialized    │
└─────────────────┘     └─────────────────┘
```

**Requirements:**
| Requirement | Purpose |
|-------------|---------|
| Derivation chain preserved | Source traceability |
| Export format documented | Format provenance |
| Export does not create authority | Format is representation |

### 3.5 PROHIBITED: Derived → Authoritative

```
┌─────────────────┐  ✗  ┌─────────────────┐
│    derived      │ ──► │  authoritative  │
│ PROV_DERIVATION │     │ PROV_AUTHORITY  │
│    derived      │     │   canonical     │
└─────────────────┘     └─────────────────┘
```

**Prohibition:**
```
Derivation cannot escalate to authority.
Computation does not create ratification.
This is the most dangerous escalation path.
```

### 3.6 PROHIBITED: Sandbox → Any (without gate)

```
┌─────────────────┐  ✗  ┌─────────────────┐
│    sandbox      │ ──► │      any        │
│ PROV_DERIVATION │     │      any        │
│    sandbox      │     │   not-sandbox   │
└─────────────────┘     └─────────────────┘
```

**Prohibition:**
```
Sandbox cannot escape without governance gate.
Pre-governance vocabulary must not enter production paths.
```

---

## 4. High-Risk Path Requirements

### 4.1 IBG → Export

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│      IBG        │ ──► │   ExportBridge  │ ──► │   Translator    │
│ PROV_DERIVATION │     │ PROV_DERIVATION │     │ PROV_TRANSFORM  │
│    sandbox      │     │    sandbox      │     │    sandbox      │
│ advisory: true  │     │ advisory: true  │     │ advisory: true  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

**Mandatory Requirements:**

| Requirement | Implementation |
|-------------|----------------|
| Sandbox authority-state must persist | `authority_state: sandbox` at all stages |
| Advisory flag must persist | `advisory_only: true` at all stages |
| Derivation chain must be visible | `derivation_source: ibg_body_grid` |
| Export must not claim authority | Serializer role enforcement |

**Violation Examples:**

| Violation | Risk |
|-----------|------|
| IBG data without sandbox marker | Appears canonical |
| Advisory flag dropped | Consumer may treat as authoritative |
| Derivation source omitted | Chain integrity lost |

### 4.2 Derived → Cached

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    derived      │ ──► │     cache       │ ──► │    consumer     │
│ PROV_DERIVATION │     │ PROV_ARCHIVE    │     │ PROV_DERIVATION │
│    derived      │     │    derived      │     │    derived      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

**Mandatory Requirements:**

| Requirement | Implementation |
|-------------|----------------|
| Cache must preserve source provenance | `derivation_source` persisted |
| Cache must preserve authority-state | `authority_state: derived` persisted |
| Cache must add archive provenance | `cached_at`, `cache_location` |
| Consumer must not escalate | Derived authority-state inherited |

**Violation Examples:**

| Violation | Risk |
|-----------|------|
| Cache without source reference | Orphan value |
| Authority-state lost in cache | Escalation risk |
| Consumer treats cached as authoritative | Authority collapse |

### 4.3 Cross-Topology

```
┌─────────────────┐     ┌─────────────────┐
│ morphology_     │ ──► │  surface_       │
│    topology     │     │    topology     │
│ PROV_AUTHORITY  │     │ PROV_RUNTIME    │
│ canonical (MRP) │     │ operational(CAM)│
└─────────────────┘     └─────────────────┘
```

**Mandatory Requirements:**

| Requirement | Implementation |
|-------------|----------------|
| Source topology documented | `source_topology: morphology_topology` |
| Transformation documented | `topology_transition: mrp_to_cam` |
| Semantic boundary explicit | Different namespace = different semantics |
| Authority-state appropriate | MRP canonical vs CAM operational |

### 4.4 Runtime → Export

```
┌─────────────────┐     ┌─────────────────┐
│    runtime      │ ──► │     export      │
│ PROV_RUNTIME    │     │ PROV_TRANSFORM  │
│  operational    │     │   serialized    │
└─────────────────┘     └─────────────────┘
```

**Mandatory Requirements:**

| Requirement | Implementation |
|-------------|----------------|
| Runtime context preserved | `runtime_context` in export |
| Transformation documented | `export_format`, `export_timestamp` |
| Export is representation | Serializer role enforcement |
| Operational scope explicit | Not canonical authority |

### 4.5 Observation → Estimate

```
┌─────────────────┐     ┌─────────────────┐
│  observation    │ ──► │    estimate     │
│ PROV_OBSERV.    │     │ PROV_DERIVATION │
│ PROV_EPISTEMIC  │     │ PROV_EPISTEMIC  │
│ confidence:high │     │ confidence:low  │
└─────────────────┘     └─────────────────┘
```

**Mandatory Requirements:**

| Requirement | Implementation |
|-------------|----------------|
| Observation source cited | `derivation_source: observation` |
| Confidence degraded | Estimate typically lower confidence |
| Assumptions added | Estimation assumptions documented |
| Epistemic provenance updated | Reflects derivation uncertainty |

---

## 5. Downstream Propagation Rules

### 5.1 Permitted Downstream

| From | To | Constraint |
|------|-----|------------|
| PROV_AUTHORITY | PROV_DERIVATION | Source referenced |
| PROV_AUTHORITY | PROV_TRANSFORMATION | Source referenced |
| PROV_DERIVATION | PROV_DERIVATION | Chain visible |
| PROV_DERIVATION | PROV_TRANSFORMATION | Chain preserved |
| PROV_OBSERVATIONAL | PROV_DERIVATION | Observation cited |
| PROV_RUNTIME | PROV_ARCHIVE | Context preserved |

### 5.2 Prohibited Upstream

| From | To | Reason |
|------|-----|--------|
| PROV_DERIVATION | PROV_AUTHORITY | Computation ≠ ratification |
| PROV_TRANSFORMATION | PROV_AUTHORITY | Format ≠ truth |
| PROV_RUNTIME | PROV_AUTHORITY | Execution ≠ governance |
| PROV_ARCHIVE | PROV_AUTHORITY | Storage ≠ ratification |
| Any sandbox | Any canonical | Governance gate required |

---

## 6. Authority-State Propagation

### 6.1 State Transitions

| From State | To State | Permitted | Gate |
|------------|----------|-----------|------|
| canonical | derived | YES | — |
| canonical | operational | YES | — |
| derived | operational | YES | — |
| derived | serialized | YES | — |
| sandbox | advisory | YES | — |
| sandbox | canonical | NO | Governance gate |
| sandbox | derived | NO | Governance gate |
| advisory | canonical | NO | Ratification |
| operational | canonical | NO | Ratification |

### 6.2 State Persistence

```
Authority-state must persist through propagation.
State can narrow (canonical → derived).
State cannot escalate (derived → canonical).
```

---

## 7. Propagation Enforcement Points

### 7.1 Structural Enforcement

| Point | Mechanism | Location |
|-------|-----------|----------|
| observationalOnly | Pydantic Literal[True] | RuntimeResultBase |
| derivation_source | Required field | Derived value schemas |
| confidence | Required field | Epistemic schemas |
| assumptions | Required field | Epistemic schemas |

### 7.2 Documentary Enforcement

| Point | Mechanism | Location |
|-------|-----------|----------|
| advisory_only | Documented constraint | IBG systems |
| sandbox | Authority-state marker | IBG vocabulary |
| export_format | Documented | Translator output |

### 7.3 Proposed Enforcement

| Point | Mechanism | Status |
|-------|-----------|--------|
| propagation_chain | Required field | PROPOSED |
| authority_state | Required field | PROPOSED |
| sandbox_marker | Required on IBG | PROPOSED |

---

## 8. Propagation Verification Checklist

### 8.1 For Any Derived Value

- [ ] Has PROV_DERIVATION marker
- [ ] Has derivation_source reference
- [ ] Has derivation_algorithm documentation
- [ ] Has confidence marker
- [ ] Has assumptions list
- [ ] Does NOT claim PROV_AUTHORITY

### 8.2 For Any Cached Value

- [ ] Preserves source provenance
- [ ] Preserves authority-state
- [ ] Has PROV_ARCHIVE added
- [ ] References original source

### 8.3 For Any Export

- [ ] Has PROV_TRANSFORMATION marker
- [ ] Has export_format documented
- [ ] Preserves source provenance
- [ ] Does NOT claim authority

### 8.4 For Any Sandbox Data

- [ ] Has sandbox authority-state
- [ ] Has advisory_only: true
- [ ] Cannot escape without gate
- [ ] Derivation chain visible

---

## 9. Related Documents

### Primary Document

- `C2_PROVENANCE_BOUNDARY_DECOMPOSITION.md` — Main decomposition

### Supporting Documents

- `C2_PROVENANCE_CATEGORY_APPENDIX.md` — Category definitions
- `C2_PROVENANCE_COLLAPSE_RISKS.md` — Escalation surfaces

### C2-A/C2-B Foundation

- `C2_GEOMETRY_PROPAGATION_ANALYSIS.md` — Geometry paths
- `C2_TOPOLOGY_PROPAGATION_REVIEW.md` — Topology paths

---

*C2-C Provenance Propagation Requirements — Traceability Chain Integrity*
