# C2 Provenance Collapse Risks

```
C2-C — CONSTITUTIONAL ARBITRATION PHASE
PROVENANCE COLLAPSE ANALYSIS
AUTHORITY ESCALATION PREVENTION
```

**Phase:** C2-C  
**Owner:** Terminal 4 (Provenance/Observational)  
**Date:** 2026-05-18  
**Status:** Analysis Complete — Critical Constitutional Document

---

## 1. Purpose

This document identifies and analyzes provenance collapse risks.

These are the mechanisms by which:
- Provenance categories merge inappropriately
- Authority-state escalates without governance
- Derivation chains become invisible
- Constitutional traceability fails

---

## 2. Collapse Severity Classification

| Severity | Definition | Constitutional Impact |
|----------|------------|----------------------|
| **CRITICAL** | Immediate authority ambiguity | Constitutional violation |
| **HIGH** | Likely authority escalation | Governance integrity at risk |
| **MEDIUM** | Possible semantic drift | Traceability degradation |
| **LOW** | Minor clarity reduction | Documentation concern |

---

## 3. Critical Collapse Risks

### 3.1 CRITICAL: All Provenance → Generic Source

```
COLLAPSE: Multiple provenance types merged into single "source" field
SEVERITY: CRITICAL
MECHANISM: Schema simplification loses category distinctions
```

**Before Collapse:**
```
{
  "authority_provenance": { "ratified_by": "MRP", "date": "..." },
  "derivation_provenance": { "source": "body_outline", "algorithm": "..." },
  "epistemic_provenance": { "confidence": "medium", "assumptions": [...] }
}
```

**After Collapse:**
```
{
  "source": "body_outline"  // ALL provenance information lost
}
```

**Constitutional Violation:**
- Cannot distinguish authority from derivation
- Cannot trace ratification
- Cannot assess confidence
- Cannot verify assumptions

**Prevention:**
- Provenance categories must remain structurally distinct
- "source" field alone is insufficient
- Category-specific fields required

---

### 3.2 CRITICAL: Derivation → Authority Escalation

```
COLLAPSE: Derived values treated as canonical authority
SEVERITY: CRITICAL
MECHANISM: Silent authority escalation through usage
```

**Escalation Pathway:**
```
1. Value derived from authoritative source
2. Value cached for convenience
3. Value consumed by downstream system
4. Downstream system treats as authoritative
5. Original derivation chain invisible
6. Value now appears canonical
```

**Example (IBG Zone Radius):**
```
STEP 1: zone_radius computed from body_outline (PROV_DERIVATION)
STEP 2: zone_radius cached in morphology descriptor
STEP 3: Export bridge reads cached zone_radius
STEP 4: Translator outputs zone_radius
STEP 5: External system imports as "body radius"
STEP 6: "body radius" appears authoritative
```

**Constitutional Violation:**
- Computation treated as ratification
- Derivation treated as definition
- No governance trail

**Prevention:**
- Derivation provenance must persist through caching
- Authority-state must persist: `derived` cannot become `canonical`
- Consumer systems must honor provenance type

---

### 3.3 CRITICAL: Sandbox → Authoritative Escape

```
COLLAPSE: Pre-governance vocabulary treated as ratified
SEVERITY: CRITICAL
MECHANISM: Sandbox data enters production without governance gate
```

**Escape Pathway:**
```
1. IBG creates vocabulary in sandbox
2. IBG data propagates through export
3. Export consumers treat as production data
4. Production systems consume without sandbox marker
5. Vocabulary appears canonical
```

**Example (IBG Morphology Class):**
```
STEP 1: BodyMorphologyClass created (sandbox)
STEP 2: MorphologyDescriptor references class
STEP 3: IBGMorphologyExtension carries to export
STEP 4: Export drops sandbox marker
STEP 5: "rounded_acoustic" appears canonical
STEP 6: Other systems depend on "rounded_acoustic" as truth
```

**Constitutional Violation:**
- Pre-governance treated as governance
- No ratification occurred
- Sandbox containment breached

**Prevention:**
- Sandbox authority-state must persist through all paths
- `advisory_only: true` must propagate
- Governance gate required for sandbox graduation

---

## 4. High Collapse Risks

### 4.1 HIGH: Observational ↔ Epistemic Collapse

```
COLLAPSE: Measurement origin merges with confidence tracking
SEVERITY: HIGH
MECHANISM: "What was measured" confused with "how confident"
```

**Collapse Example:**
```
// INCORRECT: Merged
{
  "measurement": {
    "value": 440,
    "source": "tap_tone",      // observational
    "confidence": "high"        // epistemic
  }
}

// CORRECT: Separate
{
  "observational": { "source": "tap_tone", "method": "fft" },
  "epistemic": { "confidence": "high", "assumptions": [] }
}
```

**Risk:**
- Source quality confused with measurement quality
- Cannot separately assess observation vs confidence
- Epistemic degradation invisible

**Prevention:**
- Observational and epistemic provenance must be distinct objects
- Different semantic questions require different categories

---

### 4.2 HIGH: Runtime ↔ Authority Collapse

```
COLLAPSE: Execution state treated as governance truth
SEVERITY: HIGH
MECHANISM: "What ran" becomes "what is canonical"
```

**Collapse Example:**
```
// Runtime result
operation_result = { "success": true, "output": geometry }

// INCORRECT: Treated as authority
canonical_geometry = operation_result.output  // NO!
```

**Constitutional Violation:**
- Execution does not create ratification
- Runtime ≠ Governance
- Hard invariant: `observationalOnly: Literal[True]`

**Prevention:**
- Runtime results carry PROV_RUNTIME, not PROV_AUTHORITY
- Runtime systems enforce `observationalOnly`
- Execution scaffolds do not define truth

---

### 4.3 HIGH: Export ↔ Canonical Collapse

```
COLLAPSE: Serialization format treated as truth source
SEVERITY: HIGH
MECHANISM: "What was exported" becomes "what is"
```

**Collapse Example:**
```
// Export produces DXF file
dxf_file = translator.export(geometry)

// INCORRECT: DXF treated as authority
imported_geometry = parse_dxf(dxf_file)  // treated as canonical

// File becomes "source of truth" instead of representation
```

**Constitutional Violation:**
- Format does not define semantics
- Serialization is transformation, not definition
- Re-import loses provenance

**Prevention:**
- Export carries PROV_TRANSFORMATION
- Serializers are non-authority (quarantine enforcement)
- Format output is representation, not truth

---

## 5. Medium Collapse Risks

### 5.1 MEDIUM: Chain Collapse (Derivation History Lost)

```
COLLAPSE: Derivation chain compressed to single step
SEVERITY: MEDIUM
MECHANISM: Intermediate derivations invisible
```

**Example:**
```
// Full chain
authoritative_body → zone_detection → zone_radius → morphology_class

// Collapsed chain
authoritative_body → morphology_class  // Intermediate steps lost
```

**Risk:**
- Cannot trace individual derivation decisions
- Cannot assess where uncertainty entered
- Cannot verify intermediate steps

**Prevention:**
- Each derivation step carries own provenance
- Chain references preserved, not compressed

---

### 5.2 MEDIUM: Boundary Collapse (Consumer Becomes Authority)

```
COLLAPSE: Consumer system starts defining consumed domain
SEVERITY: MEDIUM
MECHANISM: Consumer-without-authority pattern violated
```

**Example:**
```
// Acoustics consumes geometry (healthy)
acoustic_state.apertureGeometry = geometry_consumer_view

// COLLAPSE: Acoustics starts defining geometry
acoustic_state.canonical_aperture = {...}  // NO!
```

**Risk:**
- Consumer becomes de facto authority
- Domain boundaries violated
- Ownership confusion

**Prevention:**
- Consumer interface contracts
- `observationalOnly` markers
- Explicit non-goal documentation

---

## 6. Collapse Detection Signals

### 6.1 Red Flags

| Signal | Indicates | Action |
|--------|-----------|--------|
| Derived value without PROV_DERIVATION | Missing provenance | Flag for review |
| Cached value without source reference | Chain broken | Flag for review |
| Sandbox data without advisory marker | Escape risk | Block propagation |
| Generic "source" field without category | Type collapse | Require category |
| Runtime result treated as canonical | Authority escalation | Enforce observationalOnly |

### 6.2 Structural Detection

```python
# Detection: Missing derivation provenance
if value.is_derived and not value.has_provenance(PROV_DERIVATION):
    raise ProvenanceViolation("Derived value missing derivation provenance")

# Detection: Sandbox escape
if value.authority_state == "sandbox" and destination == "production":
    raise ProvenanceViolation("Sandbox data cannot enter production without gate")

# Detection: Authority escalation
if source.authority_state == "derived" and target.authority_state == "canonical":
    raise ProvenanceViolation("Derived cannot escalate to canonical")
```

---

## 7. Most Dangerous Collapse

### 7.1 The Silent Escalation

```
The repository's greatest remaining constitutional risk:

Derived provenance silently mutating into authority provenance
```

### 7.2 Why This Is Most Dangerous

| Factor | Severity |
|--------|----------|
| Often invisible | Users don't see provenance loss |
| Gradual accumulation | Each step seems reasonable |
| Usage implies authority | "We always use this value" |
| Cache accelerates | Cached value appears stable |
| Training hardens | ML training creates weight |

### 7.3 Complete Escalation Pathway

```
STAGE 1: DERIVATION
  authoritative_body_outline
  └─ PROV_DERIVATION: compute_zone_radius()
     └─ zone_radius (derived, confidence: medium)

STAGE 2: CACHING
  zone_radius cached for performance
  └─ PROV_ARCHIVE added
  └─ PROV_DERIVATION... still present? Maybe.

STAGE 3: CONSUMPTION
  export_bridge reads cached zone_radius
  └─ Original provenance... present? Maybe not.

STAGE 4: PROPAGATION
  translator outputs zone_radius
  └─ Provenance in output? Probably not.

STAGE 5: EXTERNAL CONSUMPTION
  External system imports zone_radius
  └─ Treated as: authoritative body measurement
  └─ Actual status: derived value from sandbox

STAGE 6: COLLAPSE COMPLETE
  zone_radius = canonical body dimension (FALSE)
```

### 7.4 Prevention Strategy

| Stage | Prevention |
|-------|------------|
| Derivation | PROV_DERIVATION required, authority_state: derived |
| Caching | Preserve source provenance, authority-state |
| Consumption | Consumer honors provenance type |
| Propagation | Export preserves or documents provenance |
| External | Cannot control, but can document |

---

## 8. Collapse Prevention Rules

### 8.1 Category Preservation

```
RULE CP1: Provenance categories must remain structurally distinct
RULE CP2: "source" field alone is never sufficient
RULE CP3: Each category answers a distinct question
```

### 8.2 Authority-State Preservation

```
RULE AS1: Authority-state must propagate with data
RULE AS2: Authority-state can narrow (canonical → derived)
RULE AS3: Authority-state cannot escalate (derived → canonical)
RULE AS4: Sandbox cannot escape without governance gate
```

### 8.3 Chain Preservation

```
RULE CH1: Every derivation traces to source
RULE CH2: Intermediate steps visible
RULE CH3: Cache preserves source reference
RULE CH4: No orphan derivations
```

### 8.4 Escalation Prevention

```
RULE ES1: Usage frequency does not create authority
RULE ES2: Cache persistence does not create authority
RULE ES3: Training weight does not create authority
RULE ES4: Operational convenience does not create authority
RULE ES5: Serialization does not create authority
```

---

## 9. Collapse Risk Matrix

| Risk | Severity | Probability | Detection | Prevention |
|------|----------|-------------|-----------|------------|
| All → source | CRITICAL | Medium | Structural | Schema enforcement |
| Derivation → authority | CRITICAL | High | Behavioral | Provenance persistence |
| Sandbox → canonical | CRITICAL | Medium | Structural | Gate enforcement |
| Observational ↔ epistemic | HIGH | Medium | Structural | Category separation |
| Runtime ↔ authority | HIGH | Low | Structural | Hard invariants |
| Export ↔ canonical | HIGH | Medium | Behavioral | Role enforcement |
| Chain collapse | MEDIUM | High | Behavioral | Chain requirements |
| Boundary collapse | MEDIUM | Medium | Behavioral | Interface contracts |

---

## 10. Terminal Responsibilities

### 10.1 Terminal 4 (Owner)

- Monitor provenance collapse signals
- Validate category preservation
- Review escalation risks
- Maintain collapse prevention rules

### 10.2 All Terminals

| Terminal | Collapse Responsibility |
|----------|------------------------|
| Terminal 1 | Constitutional discipline |
| Terminal 2 | Runtime ↔ authority prevention |
| Terminal 3 | Geometry chain preservation |
| Terminal 5 | Export ↔ canonical prevention |

---

## 11. Related Documents

### Primary Document

- `C2_PROVENANCE_BOUNDARY_DECOMPOSITION.md` — Main decomposition

### Supporting Documents

- `C2_PROVENANCE_CATEGORY_APPENDIX.md` — Category definitions
- `C2_PROVENANCE_PROPAGATION_REQUIREMENTS.md` — Propagation rules

### Pattern Documents

- `CONSUMER_WITHOUT_AUTHORITY_PATTERN.md` — Boundary discipline
- `OBSERVATIONAL_SEMANTICS_BOUNDARY_NOTES.md` — Observation boundaries

---

*C2-C Provenance Collapse Risks — Authority Escalation Prevention*
