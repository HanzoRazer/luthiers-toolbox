# Lifecycle Inventory — Acoustics/Observational

**Sprint:** Acoustics/Observational  
**Terminal:** 4  
**Date:** 2026-05-18  
**Status:** Non-authoritative inventory artifact

---

## Authority Statement

This inventory documents observed lifecycle terms and state machines. It does not:
- Normalize lifecycle vocabulary
- Collapse duplicate state machines
- Migrate enums
- Enforce state transitions

Related terms are preserved separately for later reconciliation.

---

## Inventory Entries

### AcousticConfidence

```
term_or_state: AcousticConfidence
field_name: confidence
enum_or_literal: TypeScript union type
local_meaning: Epistemic certainty level for acoustic estimates
axis_candidate: epistemic
transition_rules: No formal transitions — set based on source type (geometry_estimate → low, measured → medium/high)
source_locations:
  - packages/client/src/types/acoustics.ts:16
enforcement_status: structural (mandatory field on AcousticState)
collision_risk: Cross-domain — blueprint confidence is numeric 0-1
notes: Values: 'unknown' | 'low' | 'medium' | 'high'. Epistemic axis, not workflow axis.
```

### AcousticStateSource

```
term_or_state: AcousticStateSource
field_name: source
enum_or_literal: TypeScript union type
local_meaning: Origin type for acoustic state data
axis_candidate: operational
transition_rules:
  - geometry_estimate → measured (when physical measurement obtained)
  - geometry_estimate → manual (when user attaches estimate)
  - geometry_estimate → calibrated (future — when calibration applied)
source_locations:
  - packages/client/src/types/acoustics.ts:21-27
enforcement_status: structural (mandatory field on AcousticState)
collision_risk: None identified
notes: Values: 'geometry_estimate' | 'measured' | 'calibrated' | 'manual' | 'unknown'. Represents data maturity.
```

### MeasurementSource

```
term_or_state: MeasurementSource
field_name: source
enum_or_literal: TypeScript union type
local_meaning: Physical source of measurement data
axis_candidate: operational
transition_rules: None — set once at measurement time, immutable
source_locations:
  - packages/client/src/types/acoustics/measurementArchive.ts:36-42
enforcement_status: structural (required field on MeasurementArchiveMeasurement)
collision_risk: Field name 'source' overloaded with AcousticStateSource
notes: Values: 'tap_tone' | 'impedance_tube' | 'near_field_mic' | 'manual_entry' | 'external_import' | 'unknown'
```

### MeasurementMethod

```
term_or_state: MeasurementMethod
field_name: method
enum_or_literal: TypeScript union type
local_meaning: Analysis technique used to obtain measurement
axis_candidate: operational
transition_rules: None — set once at measurement time, immutable
source_locations:
  - packages/client/src/types/acoustics/measurementArchive.ts:47-53
enforcement_status: structural (required field on MeasurementArchiveMeasurement)
collision_risk: None identified
notes: Values: 'fft_peak_detection' | 'swept_sine' | 'impulse_response' | 'manual_reading' | 'unknown'
```

### readinessLevel (gate color)

```
term_or_state: readinessLevel
field_name: readinessLevel
enum_or_literal: string (informal enum)
local_meaning: Gate color indicating calibration readiness state
axis_candidate: governance (observational gate)
transition_rules:
  - Derived from CalibrationReadiness.overallGate
  - No direct state machine — computed from input availability
source_locations:
  - packages/client/src/utils/acoustics/diagnosticSnapshot.ts:90
  - packages/client/src/utils/acoustics/diagnosticSnapshot.ts:157-169 (getSnapshotGateColor)
enforcement_status: advisory (optional field)
collision_risk: 'green' | 'yellow' | 'red' vocabulary shared with CAM validation_gate
notes: Observational readiness, not execution authorization. Does not authorize calibration.
```

### exportStatus

```
term_or_state: exportStatus
field_name: exportStatus
enum_or_literal: string literal
local_meaning: Export workflow state for diagnostic snapshot
axis_candidate: operational
transition_rules:
  - 'prepared_not_exported' → (user action) → 'exported' (not tracked in schema)
source_locations:
  - packages/client/src/utils/acoustics/diagnosticSnapshot.ts:225
enforcement_status: advisory
collision_risk: None identified
notes: Value: 'prepared_not_exported'. Export completion not tracked in schema — client-side file operation.
```

### observationalOnly

```
term_or_state: observationalOnly
field_name: observationalOnly
enum_or_literal: Literal[true] / boolean literal
local_meaning: Invariant flag — data is observational only
axis_candidate: governance
transition_rules: None — always true, cannot transition
source_locations:
  - packages/client/src/types/acoustics/measurementArchive.ts:144
  - packages/client/src/utils/acoustics/diagnosticSnapshot.ts:109
enforcement_status: structural (Pydantic Literal[True] in CAM, TypeScript literal in acoustics)
collision_risk: Cross-domain term — used in acoustics, CAM runtime, governance
notes: Not a lifecycle state — a structural invariant. Included because it gates other states.
```

---

## Axis Classification Summary

| Axis | Terms | Count |
|------|-------|-------|
| epistemic | AcousticConfidence | 1 |
| operational | AcousticStateSource, MeasurementSource, MeasurementMethod, exportStatus | 4 |
| governance | readinessLevel, observationalOnly | 2 |

---

## Summary

| Metric | Count |
|--------|-------|
| Lifecycle terms inventoried | 7 |
| Distinct state machines | 2 (AcousticStateSource transitions, readinessLevel derivation) |
| Axis candidates identified | 3 (epistemic, operational, governance) |
| Collision risks | 2 (source field overload, readinessLevel vocabulary) |
| Unenforced transitions | 1 (exportStatus completion not tracked) |

---

## Notes

1. Acoustics lifecycle is primarily operational, not governance. Terms track data maturity, not workflow state.

2. `source` field name is overloaded between MeasurementSource and AcousticStateSource — different types, same field name.

3. Gate colors ('green' | 'yellow' | 'red') are shared vocabulary with CAM validation_gate. Potential collision if semantics diverge.

4. No complex state machines — most lifecycle terms are set-once or computed.
