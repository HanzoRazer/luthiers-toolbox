# Provenance Inventory — Acoustics/Observational

**Sprint:** Acoustics/Observational  
**Terminal:** 4  
**Date:** 2026-05-18  
**Status:** Non-authoritative inventory artifact

---

## Authority Statement

This inventory documents observed provenance usage. It does not:
- Unify provenance models
- Enforce provenance requirements
- Rename provenance fields
- Resolve semantic splits

Provenance overloading is recorded, not corrected.

---

## Acoustic-Local Provenance Categories

For acoustics inventory, classify provenance using acoustic-local categories first:

- **observational_provenance** — measurement capture metadata
- **epistemic_provenance** — confidence and assumption tracking
- **snapshot_provenance** — diagnostic snapshot references
- **estimate_provenance** — estimate source/method/confidence
- **archive_provenance** — archive-level provenance reminders

These map later to the C0 canonical provenance model. Do not collapse them during C1.

---

## Inventory Entries

### provenanceReminder

```
provenance_term: provenanceReminder
local_meaning: Human-readable notice that measurements are observational only
candidate_type: archive_provenance
stored_as: string field on archive/snapshot records
source_locations:
  - packages/client/src/types/acoustics/measurementArchive.ts:163 (MeasurementArchiveRecord.provenanceReminder)
  - packages/client/src/utils/acoustics/diagnosticSnapshot.ts:23-24 (PROVENANCE_REMINDER constant)
  - packages/client/src/types/diagnosticSnapshot.ts
required_fields: Required on MeasurementArchiveRecord, DiagnosticSnapshot
consumers: MeasurementArchivePreviewCard.vue, DiagnosticSnapshotCard.vue, DiagnosticNarrativeCard.vue
loss_risk: Low — always populated from constants
notes: Documentation provenance. Does not track derivation chain.
```

### diagnosticSnapshotReference

```
provenance_term: diagnosticSnapshotReference
local_meaning: Reference linking measurement to its diagnostic snapshot context
candidate_type: snapshot_provenance
stored_as: MeasurementArchiveSnapshotReference object
source_locations:
  - packages/client/src/types/acoustics/measurementArchive.ts:26-31 (interface)
  - packages/client/src/types/acoustics/measurementArchive.ts:93 (field on MeasurementArchiveMeasurement)
required_fields: snapshotId (optional), schemaVersion, kind, createdAtIso
consumers: Archive validation, future traceability queries
loss_risk: Medium — optional field, may be omitted
notes: Creates provenance chain from measurement to diagnostic context without duplicating snapshot data.
```

### estimateSource

```
provenance_term: estimateSource
local_meaning: Identifier for the source that generated an acoustic estimate
candidate_type: estimate_provenance
stored_as: string field
source_locations:
  - packages/client/src/types/acoustics/measurementArchive.ts:90 (MeasurementArchiveMeasurement.estimateSource)
  - packages/client/src/components/shared/acoustics/CalibrationResidualCard.vue:116 (preview.provenance?.estimateSource)
required_fields: Optional
consumers: CalibrationResidualCard provenance display
loss_risk: Medium — optional field
notes: Part of estimate provenance triple: estimateSource, estimateMethod, estimateConfidence
```

### estimateMethod

```
provenance_term: estimateMethod
local_meaning: Method used to generate acoustic estimate
candidate_type: estimate_provenance
stored_as: string field ('first_order_helmholtz' | string)
source_locations:
  - packages/client/src/types/acoustics.ts:86 (AcousticState.estimateMethod)
  - packages/client/src/types/estimateAssumptions.ts:20 (EstimateAssumptionSummary.method)
required_fields: Optional on AcousticState
consumers: EstimateAssumptionSummaryCard, CalibrationResidualCard
loss_risk: Medium — optional field
notes: Documents how estimate was computed. Part of estimate provenance.
```

### source (MeasurementSource)

```
provenance_term: source (MeasurementSource)
local_meaning: Origin of measurement data (tap_tone, impedance_tube, etc.)
candidate_type: observational_provenance
stored_as: MeasurementSource union type
source_locations:
  - packages/client/src/types/acoustics/measurementArchive.ts:36-42 (type definition)
  - packages/client/src/types/acoustics/measurementArchive.ts:78 (required field)
required_fields: Required on MeasurementArchiveMeasurement
consumers: Archive validation, measurement classification
loss_risk: Low — required field
notes: Captures instrument/method used for physical measurement.
```

### method (MeasurementMethod)

```
provenance_term: method (MeasurementMethod)
local_meaning: Technique used to obtain measurement (fft_peak_detection, etc.)
candidate_type: observational_provenance
stored_as: MeasurementMethod union type
source_locations:
  - packages/client/src/types/acoustics/measurementArchive.ts:47-53 (type definition)
  - packages/client/src/types/acoustics/measurementArchive.ts:81 (required field)
required_fields: Required on MeasurementArchiveMeasurement
consumers: Archive validation, analysis classification
loss_risk: Low — required field
notes: Captures analysis technique, not physical instrument.
```

### measuredAtIso

```
provenance_term: measuredAtIso
local_meaning: ISO 8601 timestamp when measurement was taken
candidate_type: observational_provenance
stored_as: string (ISO date)
source_locations:
  - packages/client/src/types/acoustics/measurementArchive.ts:63 (required field)
required_fields: Required on MeasurementArchiveMeasurement
consumers: Archive chronology, session reconstruction
loss_risk: Low — required field
notes: Temporal provenance for measurement ordering.
```

### createdAtIso

```
provenance_term: createdAtIso
local_meaning: ISO 8601 timestamp when archive/snapshot was created
candidate_type: archive_provenance
stored_as: string (ISO date)
source_locations:
  - packages/client/src/types/acoustics/measurementArchive.ts:140 (MeasurementArchiveMetadata)
  - packages/client/src/utils/acoustics/diagnosticSnapshot.ts:101 (DiagnosticSnapshot)
required_fields: Required
consumers: Archive indexing, export metadata
loss_risk: Low — auto-generated
notes: Distinct from measuredAtIso. Archive creation time, not measurement time.
```

### confidence (as provenance)

```
provenance_term: confidence (epistemic)
local_meaning: Epistemic certainty level attached to estimate
candidate_type: epistemic_provenance
stored_as: AcousticConfidence union type
source_locations:
  - packages/client/src/types/acoustics.ts:65 (required field on AcousticState)
  - packages/client/src/types/estimateAssumptions.ts:22
required_fields: Required on AcousticState
consumers: All acoustic state displays
loss_risk: Low — mandatory field
notes: Epistemic provenance. Documents certainty level of estimates.
```

### assumptions (as provenance)

```
provenance_term: assumptions
local_meaning: List of epistemic caveats explaining estimate basis
candidate_type: epistemic_provenance
stored_as: string[]
source_locations:
  - packages/client/src/types/acoustics.ts:95 (required field on AcousticState)
  - packages/client/src/utils/acoustics/acousticState.ts:15-21 (DEFAULT_GEOMETRY_ASSUMPTIONS)
required_fields: Required on AcousticState
consumers: EstimateAssumptionSummaryCard, CalibrationResidualCard
loss_risk: Low — mandatory field with defaults
notes: Epistemic provenance. Prevents estimated physics looking like measured truth.
```

---

## Provenance Category Summary

| Category | Terms | Required Fields | Loss Risk |
|----------|-------|-----------------|-----------|
| observational_provenance | source, method, measuredAtIso | 3 | Low |
| epistemic_provenance | confidence, assumptions | 2 | Low |
| snapshot_provenance | diagnosticSnapshotReference | 0 | Medium |
| estimate_provenance | estimateSource, estimateMethod | 0 | Medium |
| archive_provenance | provenanceReminder, createdAtIso | 2 | Low |

---

## Summary

| Metric | Count |
|--------|-------|
| Provenance terms inventoried | 11 |
| Observational provenance | 3 |
| Epistemic provenance | 2 |
| Snapshot provenance | 1 |
| Estimate provenance | 2 |
| Archive provenance | 3 |
| Semantic splits identified | 1 (source used both as MeasurementSource and AcousticStateSource) |
| Loss risks | 2 (diagnosticSnapshotReference, estimateSource/estimateMethod optional) |

---

## Notes

1. Provenance is well-structured in acoustics domain with clear categories.

2. The estimate provenance triple (estimateSource, estimateMethod, estimateConfidence) is optional, creating potential loss risk.

3. No "lineage" usage found in acoustics domain. Lineage appears in RMOS presets (cross-domain).

4. `source` term overloaded: MeasurementSource (measurement origin) vs AcousticStateSource (state derivation). Different semantic intent, same field name in different contexts.
