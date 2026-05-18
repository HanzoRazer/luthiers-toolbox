# C2 Provenance Category Appendix

```
C2-C — CONSTITUTIONAL ARBITRATION PHASE
PROVENANCE CATEGORY DEEPENING
7 CATEGORIES + 5 AUTHORITY-STATES
```

**Phase:** C2-C  
**Owner:** Terminal 4 (Provenance/Observational)  
**Date:** 2026-05-18  
**Status:** Appendix Complete — Supporting Document

---

## 1. Purpose

This appendix deepens provenance category analysis for constitutional arbitration.

It provides:
- Detailed category definitions
- Boundary specifications
- Composition rules
- Cross-domain evidence

---

## 2. Category 1: Authority Provenance (PROV_AUTHORITY)

### 2.1 Definition

```
Authority provenance traces governance ratification.
It answers: "Who has constitutional right to assert this truth?"
```

### 2.2 Characteristics

| Aspect | Specification |
|--------|---------------|
| Creation | Human ratification or constitutional process |
| Modification | Governance-controlled only |
| Consumption | All layers may consume |
| Escalation | Terminal authority — nothing escalates TO authority |

### 2.3 Required Fields

| Field | Purpose | Required |
|-------|---------|----------|
| `ratification_date` | When ratified | YES |
| `ratification_authority` | Who ratified | YES |
| `constitutional_basis` | Which invariant/decision | YES |
| `scope` | What domain it covers | YES |

### 2.4 Evidence

**MRP 7M Registry:**
```
Term: morphology
Declared owner: MRP
Governance tier: 2
Constitutional basis: 7M registration
```

### 2.5 Anti-Patterns

```
ANTI-PATTERN: Derived value claiming PROV_AUTHORITY
ANTI-PATTERN: Runtime state claiming PROV_AUTHORITY
ANTI-PATTERN: Serialization creating PROV_AUTHORITY
```

---

## 3. Category 2: Observational Provenance (PROV_OBSERVATIONAL)

### 3.1 Definition

```
Observational provenance traces measurement origin.
It answers: "Where/how was this observed?"
```

### 3.2 Characteristics

| Aspect | Specification |
|--------|---------------|
| Creation | Physical measurement or observation |
| Modification | Re-measurement only |
| Consumption | Derivation and analysis |
| Escalation | May inform authority, does not create it |

### 3.3 Required Fields

| Field | Purpose | Required |
|-------|---------|----------|
| `observation_source` | What produced the observation | YES |
| `observation_method` | How it was observed | YES |
| `observation_timestamp` | When observed | YES |
| `observer_context` | Environmental conditions | RECOMMENDED |

### 3.4 Evidence

**Acoustics MeasurementArchive:**
```typescript
MeasurementSource: 'tap_tone' | 'impedance_tube' | 'near_field_mic' | ...
MeasurementMethod: 'fft_peak_detection' | 'swept_sine' | 'impulse_response' | ...
measuredAtIso: string  // ISO timestamp
```

### 3.5 Boundary with Epistemic

```
Observational: What was measured
Epistemic: How confident we are in the measurement

These must NOT collapse.
```

---

## 4. Category 3: Epistemic Provenance (PROV_EPISTEMIC)

### 4.1 Definition

```
Epistemic provenance traces confidence and assumptions.
It answers: "How certain are we in this value?"
```

### 4.2 Characteristics

| Aspect | Specification |
|--------|---------------|
| Creation | Assessment of certainty |
| Modification | Re-assessment |
| Consumption | Decision-making systems |
| Escalation | May degrade through derivation |

### 4.3 Required Fields

| Field | Purpose | Required |
|-------|---------|----------|
| `confidence` | Certainty level | YES |
| `assumptions` | Epistemic caveats | YES |
| `uncertainty_source` | Why uncertain | RECOMMENDED |

### 4.4 Evidence

**Acoustics AcousticState:**
```typescript
confidence: AcousticConfidence  // 'unknown' | 'low' | 'medium' | 'high'
assumptions: string[]  // Mandatory field
```

### 4.5 Degradation Rule

```
When observation becomes estimate:
- Confidence typically degrades
- Assumptions accumulate
- Epistemic provenance must update

Derivation from 'high' confidence does not inherit 'high' confidence.
```

---

## 5. Category 4: Estimate Provenance (PROV_DERIVATION)

### 5.1 Definition

```
Estimate provenance traces derivation chains.
It answers: "How was this value computed?"
```

### 5.2 Characteristics

| Aspect | Specification |
|--------|---------------|
| Creation | Computation from other values |
| Modification | Re-computation |
| Consumption | Downstream derivation or display |
| Escalation | PROHIBITED — derivation does not create authority |

### 5.3 Required Fields

| Field | Purpose | Required |
|-------|---------|----------|
| `derivation_source` | What it was derived from | YES |
| `derivation_algorithm` | How it was computed | YES |
| `derivation_version` | Algorithm version | RECOMMENDED |

### 5.4 Evidence

**Acoustics Helmholtz Estimate:**
```typescript
estimateSource: 'geometry'
estimateMethod: 'helmholtz_formula_v1'
estimatedHelmholtzHz: number
// Must carry confidence and assumptions
```

### 5.5 Chain Visibility Rule

```
Every derivation must be traceable to:
- An authoritative source, OR
- An observational source

Orphan derivations are constitutional violations.
```

---

## 6. Category 5: Runtime Provenance (PROV_RUNTIME)

### 6.1 Definition

```
Runtime provenance traces execution history.
It answers: "What execution path produced this?"
```

### 6.2 Characteristics

| Aspect | Specification |
|--------|---------------|
| Creation | Execution events |
| Modification | Re-execution |
| Consumption | Debugging and audit |
| Escalation | PROHIBITED — execution does not create authority |

### 6.3 Required Fields

| Field | Purpose | Required |
|-------|---------|----------|
| `execution_context` | Runtime environment | YES |
| `execution_timestamp` | When executed | YES |
| `execution_path` | Operation sequence | RECOMMENDED |

### 6.4 Evidence

**CAM RuntimeResultBase:**
```python
observationalOnly: Literal[True]  # Hard invariant
provenance: List[ProvenanceEntry]  # Execution trail
```

### 6.5 Non-Authority Rule

```
Runtime execution does not create governance authority.
Runtime results are observational scaffolds, not canonical truth.
```

---

## 7. Category 6: Archive Provenance (PROV_ARCHIVE)

### 7.1 Definition

```
Archive provenance traces persistence lineage.
It answers: "When/how was this stored?"
```

### 7.2 Characteristics

| Aspect | Specification |
|--------|---------------|
| Creation | Persistence event |
| Modification | Archive update |
| Consumption | Retrieval systems |
| Escalation | PROHIBITED — storage does not create authority |

### 7.3 Required Fields

| Field | Purpose | Required |
|-------|---------|----------|
| `archived_at` | When persisted | YES |
| `archive_location` | Where stored | YES |
| `archive_format` | Storage format | RECOMMENDED |

### 7.4 Evidence

**MeasurementArchive:**
```typescript
createdAtIso: string
schemaVersion: 'measurement-archive.v1'
kind: 'aperture-measurement-archive'
```

### 7.5 Cache Rule

```
Caching a derived value does not escalate its authority.
Cached values must preserve source provenance.
```

---

## 8. Category 7: Export Provenance (PROV_TRANSFORMATION)

### 8.1 Definition

```
Export provenance traces serialization transformations.
It answers: "How was this exported/transformed for output?"
```

### 8.2 Characteristics

| Aspect | Specification |
|--------|---------------|
| Creation | Serialization/export event |
| Modification | Re-export |
| Consumption | External systems |
| Escalation | PROHIBITED — format does not create authority |

### 8.3 Required Fields

| Field | Purpose | Required |
|-------|---------|----------|
| `export_format` | Target format | YES |
| `export_timestamp` | When exported | YES |
| `source_provenance` | What was exported | YES |

### 8.4 Evidence

**DXF Translator:**
```
Export format: R2000 (AC1015)
Entities: LWPOLYLINE
Role: serializer — encodes, does not define
```

### 8.5 Format Non-Authority Rule

```
Serialization format does not define semantic truth.
Export is PROV_TRANSFORMATION, not PROV_AUTHORITY.
```

---

## 9. Authority-State Categories (5)

### 9.1 Canonical

```
Definition: Constitutionally ratified truth
Provenance requirement: PROV_AUTHORITY
Advisory status: advisory_only: false
```

### 9.2 Sandbox

```
Definition: Pre-governance experimental
Provenance requirement: PROV_DERIVATION (typical)
Advisory status: advisory_only: true (mandatory)
```

### 9.3 Advisory

```
Definition: Consumable but non-authoritative
Provenance requirement: Any
Advisory status: advisory_only: true
```

### 9.4 Operational

```
Definition: Runtime-scoped validity
Provenance requirement: PROV_RUNTIME
Advisory status: Varies by context
```

### 9.5 Derived

```
Definition: Computed from authoritative source
Provenance requirement: PROV_DERIVATION
Advisory status: Depends on use case
```

---

## 10. Category Composition Rules

### 10.1 Sequential Composition

| First | Then | Result | Permitted |
|-------|------|--------|-----------|
| PROV_OBSERVATIONAL | PROV_DERIVATION | Derived observation | YES |
| PROV_AUTHORITY | PROV_DERIVATION | Derived authority | YES |
| PROV_DERIVATION | PROV_TRANSFORMATION | Exported derivation | YES |
| PROV_RUNTIME | PROV_ARCHIVE | Archived execution | YES |

### 10.2 Parallel Composition

| Category A | Category B | Result | Permitted |
|------------|------------|--------|-----------|
| PROV_DERIVATION | PROV_EPISTEMIC | Derived with confidence | YES |
| PROV_RUNTIME | PROV_TRANSFORMATION | Runtime export | YES |
| PROV_OBSERVATIONAL | PROV_EPISTEMIC | Observation with confidence | YES |

### 10.3 Prohibited Compositions

| Attempted | Reason |
|-----------|--------|
| Any → PROV_AUTHORITY | Authority requires ratification |
| PROV_TRANSFORMATION → Source | Format cannot define source |
| PROV_ARCHIVE → Source | Storage cannot define source |

---

## 11. Cross-Domain Evidence Summary

### 11.1 Acoustics Domain

| Provenance | Evidence |
|------------|----------|
| PROV_OBSERVATIONAL | MeasurementSource, MeasurementMethod |
| PROV_EPISTEMIC | AcousticConfidence, assumptions |
| PROV_DERIVATION | estimateSource, estimateMethod |
| PROV_ARCHIVE | createdAtIso, schemaVersion |

### 11.2 CAM Runtime

| Provenance | Evidence |
|------------|----------|
| PROV_RUNTIME | provenance list, operation chain |
| PROV_TRANSFORMATION | translator output |

### 11.3 Export/Serialization

| Provenance | Evidence |
|------------|----------|
| PROV_TRANSFORMATION | DXF format, JSON format |
| PROV_ARCHIVE | file persistence |

---

## 12. Related Documents

### Primary Document

- `C2_PROVENANCE_BOUNDARY_DECOMPOSITION.md` — Main decomposition

### C1 Evidence

- `acoustics_observational/PROVENANCE_INVENTORY.md` — Acoustics provenance categories
- `C1_STRATEGIC_FINDINGS.md` — Provenance decomposition validated

---

*C2-C Provenance Category Appendix — Category Deepening Complete*
