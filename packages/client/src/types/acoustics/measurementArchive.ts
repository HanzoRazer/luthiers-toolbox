/**
 * Measurement Archive Types
 *
 * Dev Order 54: Measurement archive infrastructure foundation.
 *
 * Archives preserve observational measurements and provenance.
 * They do NOT store calibration outputs, predictions, or recommendations.
 *
 * Core rule: archives preserve observations, not conclusions.
 */

/**
 * Lightweight geometry summary for archive context.
 * Avoids full geometry payload duplication.
 */
export interface MeasurementArchiveGeometrySummary {
  apertureType?: string
  areaMm2?: number
  equivalentDiameterMm?: number
  paRatioMmInv?: number
}

/**
 * Reference to a diagnostic snapshot for traceability.
 */
export interface MeasurementArchiveSnapshotReference {
  snapshotId?: string
  schemaVersion?: string
  kind?: string
  createdAtIso?: string
}

/**
 * Source information for a measurement.
 */
export type MeasurementSource =
  | 'tap_tone'
  | 'impedance_tube'
  | 'near_field_mic'
  | 'manual_entry'
  | 'external_import'
  | 'unknown'

/**
 * Method used to obtain the measurement.
 */
export type MeasurementMethod =
  | 'fft_peak_detection'
  | 'swept_sine'
  | 'impulse_response'
  | 'manual_reading'
  | 'unknown'

/**
 * A single measurement record within an archive.
 * Field names align with existing AcousticState where applicable.
 */
export interface MeasurementArchiveMeasurement {
  /** Unique ID for this measurement within the archive */
  measurementId: string

  /** ISO timestamp when measurement was taken */
  measuredAtIso: string

  /** Human-readable label */
  label?: string

  /** Measured Helmholtz frequency in Hz */
  measuredHelmholtzHz?: number

  /** Measured Q factor */
  measuredQ?: number

  /** Dominant spectral peak frequency in Hz */
  dominantPeakHz?: number

  /** Source of this measurement */
  source: MeasurementSource

  /** Method used to obtain the measurement */
  method: MeasurementMethod

  /** Free-form notes */
  notes?: string

  /** Warnings about this measurement */
  warnings?: string[]

  /** Provenance: estimate source if comparison was made */
  estimateSource?: string

  /** Provenance: reference to diagnostic snapshot */
  diagnosticSnapshotReference?: MeasurementArchiveSnapshotReference
}

/**
 * Context for the measurement session.
 * Captures experimental conditions without full geometry duplication.
 */
export interface MeasurementArchiveContext {
  /** Reference aperture geometry summary */
  referenceGeometry?: MeasurementArchiveGeometrySummary

  /** Candidate aperture geometry summary */
  candidateGeometry?: MeasurementArchiveGeometrySummary

  /** Reference aperture label */
  referenceLabel?: string

  /** Candidate aperture label */
  candidateLabel?: string

  /** Measurement session start timestamp */
  sessionStartIso?: string

  /** Measurement session end timestamp */
  sessionEndIso?: string

  /** Environmental notes (temperature, humidity, etc.) */
  environmentNotes?: string

  /** Equipment notes */
  equipmentNotes?: string
}

/**
 * Archive metadata.
 */
export interface MeasurementArchiveMetadata {
  /** Archive schema version */
  schemaVersion: 'measurement-archive.v1'

  /** Archive kind identifier */
  kind: 'aperture-measurement-archive'

  /** System that generated this archive */
  generatedBy: 'aperture-workspace'

  /** ISO timestamp when archive was created */
  createdAtIso: string

  /** Observational-only flag (always true) */
  observationalOnly: true

  /**
   * Optional experiment tags for grouping and filtering.
   * Examples: spiral-14mm, triple-spiral, domed-island, tornavoz
   * NOT ontology authority — for local organization only.
   *
   * Dev Order 62: Added for evidence continuity.
   */
  experimentTags?: string[]
}

/**
 * Complete measurement archive record.
 */
export interface MeasurementArchiveRecord {
  /** Unique archive ID */
  archiveId: string

  /** Archive metadata */
  metadata: MeasurementArchiveMetadata

  /** Measurement session context */
  context: MeasurementArchiveContext

  /** Archived measurements */
  measurements: MeasurementArchiveMeasurement[]

  /** Provenance reminder */
  provenanceReminder: string

  /** Optional tags for future indexing */
  tags?: string[]
}

/**
 * Lightweight index entry for archive lookup.
 * NOT database indexing — for future archive listing compatibility.
 */
export interface MeasurementArchiveIndexEntry {
  archiveId: string
  createdAtIso: string
  measurementCount: number
  referenceLabel?: string
  candidateLabel?: string
  tags?: string[]
}

/**
 * Archive index structure.
 */
export interface MeasurementArchiveIndex {
  schemaVersion: 'measurement-archive-index.v1'
  entries: MeasurementArchiveIndexEntry[]
  lastUpdatedIso: string
}

/**
 * Validation result for archive schema.
 */
export interface MeasurementArchiveValidationResult {
  valid: boolean
  schemaVersion?: string
  measurementCount?: number
  errors: string[]
  warnings: string[]
}
