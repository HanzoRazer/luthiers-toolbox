# Measurement Archive Architecture

Dev Order 54 — Measurement archive infrastructure foundation.

## Purpose

Measurement archives preserve observational measurements and their provenance
for future reference. They do NOT store calibration outputs, predictions, or
recommendations.

**Core rule**: Archives preserve observations, not conclusions.

## Constraints

### Observational-Only

Archives capture what was measured, not what it means:
- Measured Helmholtz frequency (Hz)
- Measured Q factor
- Dominant spectral peak (Hz)
- Source and method metadata
- Timestamp and session context

Archives do NOT contain:
- Calibration coefficients
- Predicted performance
- Recommendation scores
- Optimization targets

### No Persistence Backend

All archive operations are client-side only:
- Archives serialize to JSON for file export
- No server upload endpoints
- No database storage
- No cloud sync

Users own their data through explicit file operations.

### Schema Versioning

Archive schema version: `measurement-archive.v1`

Schema changes require:
1. New version identifier
2. Migration path from previous versions
3. Validation for both old and new formats

## Archive Schema

### MeasurementArchiveRecord

```typescript
interface MeasurementArchiveRecord {
  archiveId: string
  metadata: MeasurementArchiveMetadata
  context: MeasurementArchiveContext
  measurements: MeasurementArchiveMeasurement[]
  provenanceReminder: string
  tags?: string[]
}
```

### Metadata

```typescript
interface MeasurementArchiveMetadata {
  schemaVersion: 'measurement-archive.v1'
  kind: 'aperture-measurement-archive'
  generatedBy: 'aperture-workspace'
  createdAtIso: string
  observationalOnly: true  // Always true
}
```

### Measurement Entry

```typescript
interface MeasurementArchiveMeasurement {
  measurementId: string
  measuredAtIso: string
  label?: string
  measuredHelmholtzHz?: number
  measuredQ?: number
  dominantPeakHz?: number
  source: MeasurementSource
  method: MeasurementMethod
  notes?: string
  warnings?: string[]
  estimateSource?: string
  diagnosticSnapshotReference?: MeasurementArchiveSnapshotReference
}
```

### Source Types

- `tap_tone` — tap tone analysis
- `impedance_tube` — impedance tube measurement
- `near_field_mic` — near-field microphone
- `manual_entry` — user-entered value
- `external_import` — imported from external system
- `unknown` — source not specified

### Method Types

- `fft_peak_detection` — FFT-based peak detection
- `swept_sine` — swept sine measurement
- `impulse_response` — impulse response analysis
- `manual_reading` — manual instrument reading
- `unknown` — method not specified

## Provenance Rules

### Every Archive Must Include

1. **Provenance reminder**: Human-readable notice that measurements are
   observational only and do not represent validated acoustic performance.

2. **Timestamp**: ISO 8601 timestamp for archive creation.

3. **Source attribution**: Every measurement must declare its source and method.

### Snapshot References

Archives may reference diagnostic snapshots for traceability:

```typescript
interface MeasurementArchiveSnapshotReference {
  snapshotId?: string
  schemaVersion?: string
  kind?: string
  createdAtIso?: string
}
```

This creates a provenance chain from measurement to diagnostic context
without duplicating snapshot data.

## Geometry Summary

Archives store lightweight geometry summaries, not full geometry payloads:

```typescript
interface MeasurementArchiveGeometrySummary {
  apertureType?: string
  areaMm2?: number
  equivalentDiameterMm?: number
  paRatioMmInv?: number
}
```

This provides sufficient context without duplicating the canonical
ApertureGeometry structure.

## Future Non-Goals

The following are explicitly out of scope for measurement archives:

1. **Calibration storage** — Calibration belongs in a separate system with
   different validation requirements.

2. **Prediction persistence** — Predictions are computed fresh from current
   models, not stored in archives.

3. **Cross-archive analysis** — Archives are individual records; aggregate
   analysis is a separate feature.

4. **Archive browser UI** — Archives are accessed through file operations;
   an in-app browser is not planned.

5. **Backend sync** — Archives remain client-local; cloud sync would require
   a different architecture.

## File Locations

- Types: `packages/client/src/types/acoustics/measurementArchive.ts`
- Utilities: `packages/client/src/utils/acoustics/measurementArchive.ts`
- Preview card: `packages/client/src/components/shared/acoustics/MeasurementArchivePreviewCard.vue`

## Related Documents

- [ARCHITECTURAL_BOUNDARIES.md](./ARCHITECTURAL_BOUNDARIES.md) — Layer boundaries
- [SNAPSHOT_EXCHANGE_ARCHITECTURE.md](./SNAPSHOT_EXCHANGE_ARCHITECTURE.md) — Snapshot subsystem
- [APERTURE_WORKSPACE_REFACTOR_STATUS.md](./APERTURE_WORKSPACE_REFACTOR_STATUS.md) — Refactor status
