# Epistemic Status Schema Implications Review

**Version:** 1.0.0  
**Date:** 2026-05-24  
**Status:** Analysis memo (not constitutional doctrine)  
**Scope:** Theoretical implications for future implementation

---

## Purpose

This document analyzes the schema, export, UI, and propagation implications of ADR-0011 (Measurement Authority) and ADR-0012 (Epistemic Status Taxonomy).

**This is NOT constitutional doctrine.** It is a supporting analysis to inform future implementation decisions. Schema structures, field names, and propagation mechanics discussed here are illustrative, not normative.

---

## 1. Potential Schema Implications

### 1.1 Artifact-Level Status Tracking

Future artifact schemas may include epistemic status metadata:

```
Potential future fields may include:

epistemicStatus: string
  - One of: OBSERVED, DERIVED, ESTIMATED, PREDICTED, 
    HEURISTIC, OPERATOR_ANNOTATED, EXTERNALLY_SOURCED

epistemicStatusReason: string
  - Human-readable explanation of status assignment

epistemicStatusTimestamp: ISO8601
  - When status was assigned/last verified
```

### 1.2 Provenance Chain Status Tracking

Provenance chains may need to track status at each transformation:

```
Potential future structure may include:

provenanceChain: [
  {
    step: 0,
    operation: "capture",
    inputStatus: null,
    outputStatus: "OBSERVED",
    timestamp: "2026-05-24T14:30:00Z"
  },
  {
    step: 1,
    operation: "fft",
    inputStatus: "OBSERVED",
    outputStatus: "DERIVED",
    timestamp: "2026-05-24T14:30:01Z"
  },
  {
    step: 2,
    operation: "peak_detection",
    inputStatus: "DERIVED",
    outputStatus: "DERIVED",
    timestamp: "2026-05-24T14:30:02Z"
  }
]
```

### 1.3 Field-Level Status Tracking

For artifacts with mixed-status fields, per-field tracking may be needed:

```
Potential future structure may include:

woodProperties: {
  fundamental_hz: {
    value: 203.1,
    epistemicStatus: "DERIVED"
  },
  radiation_coefficient: {
    value: 11.2,
    epistemicStatus: "ESTIMATED"
  },
  quality_grade: {
    value: "A",
    epistemicStatus: "HEURISTIC"
  },
  specimen_label: {
    value: "SP_001",
    epistemicStatus: "OPERATOR_ANNOTATED"
  }
}
```

---

## 2. Potential Export Implications

### 2.1 viewer_pack_v1 Extensions

Future viewer_pack exports may need epistemic metadata:

```
Potential future export structure may include:

{
  "schema_version": "2.0.0",
  "epistemicMetadata": {
    "captureStatus": "OBSERVED",
    "derivedFieldsStatus": "DERIVED",
    "estimatedFieldsStatus": "ESTIMATED",
    "advisoryExcluded": true
  },
  "measurements": { ... },
  "derived": { ... }
}
```

### 2.2 Cross-Boundary Status Preservation

When artifacts flow to luthiers-toolbox:

```
Potential future contract may include:

exportContract: {
  preserveEpistemicStatus: true,
  allowedStatusElevation: false,
  externalSourceMarking: "required"
}
```

### 2.3 Import Status Assignment

When importing external data:

```
Potential future import behavior may include:

- All imported data defaults to EXTERNALLY_SOURCED
- Re-measurement may upgrade to OBSERVED
- Import source must be recorded in provenance
```

---

## 3. Potential UI Implications

### 3.1 Status-Aware Display Components

Future UI components may need status-aware rendering:

```
Potential future component patterns may include:

<MeasurementDisplay 
  value={203.1} 
  unit="Hz" 
  status="DERIVED"
  showStatusBadge={true}
/>

Renders as:
┌────────────────────────┐
│ 203.1 Hz  [Computed]   │
└────────────────────────┘
```

### 3.2 Mixed-Status Displays

When displaying artifacts with multiple status levels:

```
Potential future display pattern may include:

┌─────────────────────────────────────┐
│ Specimen: SP_001                    │
│                                     │
│ Fundamental: 203.1 Hz [Measured]    │
│ Radiation: 11.2 [Estimated]         │
│ Quality: A [Advisory]               │
│                                     │
│ ⓘ This display includes estimated  │
│   and advisory values               │
└─────────────────────────────────────┘
```

### 3.3 Status Filtering

Users may want to filter by epistemic status:

```
Potential future filter options may include:

☑ Show measured values
☑ Show computed values
☐ Show estimated values
☐ Show advisory values
```

---

## 4. Potential Propagation Implications

### 4.1 Status Computation Rules

When combining data sources:

```
Potential future computation rules may include:

function computeResultStatus(inputs: EpistemicStatus[]): EpistemicStatus {
  // Lowest authority wins
  const priority = {
    OBSERVED: 7,
    DERIVED: 6,
    ESTIMATED: 5,
    PREDICTED: 4,
    EXTERNALLY_SOURCED: 3,
    OPERATOR_ANNOTATED: 2,
    HEURISTIC: 1
  };
  
  return inputs.reduce((lowest, current) => 
    priority[current] < priority[lowest] ? current : lowest
  );
}
```

### 4.2 Transform Status Rules

When applying transforms:

```
Potential future transform rules may include:

OBSERVED + deterministic_transform → DERIVED
OBSERVED + inference → ESTIMATED
DERIVED + model → PREDICTED
Any + advisory_interpretation → HEURISTIC
```

### 4.3 Forbidden Elevations

Implementation must prevent:

```
Potential future validation rules may include:

function validateStatusTransition(from: EpistemicStatus, to: EpistemicStatus): boolean {
  const elevationAttempt = 
    (from === 'HEURISTIC' && to !== 'HEURISTIC') ||
    (from === 'PREDICTED' && to === 'OBSERVED') ||
    (from === 'ESTIMATED' && to === 'DERIVED') ||
    (from === 'ESTIMATED' && to === 'OBSERVED');
    
  return !elevationAttempt;
}
```

---

## 5. Potential Historical Learning Implications

### 5.1 Anti-Laundering in Historical Systems

Future historical learning systems must prevent authority laundering:

```
Potential future anti-laundering rules may include:

- Repeated HEURISTIC observations remain HEURISTIC
- Statistical patterns derived from HEURISTIC data are HEURISTIC
- Operator trust accumulation does not change epistemic status
- Historical frequency does not elevate authority
```

### 5.2 Historical Status Tracking

```
Potential future historical schema may include:

historicalPattern: {
  pattern_id: "wolf_at_247hz",
  occurrence_count: 15,
  first_observed: "2026-01-15",
  epistemicStatus: "HEURISTIC",  // Does NOT elevate
  operator_trust_level: 0.85,    // Tracked separately
  canonical: false               // FORBIDDEN to be true
}
```

---

## 6. Implementation Considerations

### 6.1 Backward Compatibility

Existing artifacts without epistemic status may need:

```
Potential future migration approach may include:

- Default existing viewer_pack_v1 to DERIVED
- Default existing measurements to OBSERVED if provenance complete
- Default advisory outputs to HEURISTIC
- Require explicit status on new artifacts
```

### 6.2 Performance Considerations

Per-field status tracking adds overhead:

```
Potential future optimization approaches may include:

- Artifact-level status for homogeneous artifacts
- Field-level status only when mixed
- Status inheritance from container when uniform
- Lazy status computation on export
```

### 6.3 Validation Requirements

Future CI may validate:

```
Potential future CI checks may include:

- All artifacts have epistemicStatus
- No forbidden status elevations in transforms
- Advisory outputs have HEURISTIC status
- viewer_pack_v1 excludes HEURISTIC fields
```

---

## 7. Open Questions for Future Dev Orders

The following questions are identified but not resolved here:

1. Should status be tracked at artifact, section, or field level?
2. How should status propagate through aggregation (averaging, statistical summary)?
3. Should confidence values be status-qualified (measurement confidence vs advisory confidence)?
4. How should external calibration data interact with EXTERNALLY_SOURCED status?
5. Should operator annotations carry operator identity for traceability?
6. How should status display vary by user expertise level?

---

## 8. Relationship to Constitutional Doctrine

This document analyzes implications but does NOT establish:

- Required schema fields
- Mandatory export formats
- UI implementation requirements
- Runtime validation rules

Those decisions belong to future Dev Orders after constitutional doctrine (ADR-0011, ADR-0012) is ratified and stable.

---

## References

- ADR-0011: Measurement Authority Constitutional Definition
- ADR-0012: Epistemic Status Taxonomy
- ADR-0010: Advisory Authority Constitutional Boundary
- ADR-0009: Advisory Boundary — Measurement vs Decision Support

---

**Document Version:** 1.0.0  
**Last Updated:** 2026-05-24  
**Owner:** tap-tone-pi governance  
**Status:** Analysis memo (not constitutional doctrine)
