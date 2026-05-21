/**
 * Measurement Archive Types
 *
 * Dev Order 60: Types for measurement archive schema (measurement-archive.v1).
 * Dev Order 62: Added experimentTags for evidence index grouping.
 * Dev Order 66: Added topologyVariantReferences for variant linkage.
 *
 * Archives are durable, local-only, observational-only artifacts.
 * No calibration, prediction, or canonical authority.
 */

import type { DiagnosticSnapshot } from '@/types/diagnosticSnapshot'

/**
 * Measurement archive context — what was being measured and why
 */
export interface MeasurementArchiveContext {
  instrumentId?: string
  referenceLabel?: string
  candidateLabel?: string
  sessionContext?: string
  operator?: string
}

/**
 * Measurement archive metadata
 */
export interface MeasurementArchiveMetadata {
  schemaVersion: 'measurement-archive.v1'
  createdAtIso: string
  sourceApplication: string
  tags?: string[]
  experimentTags?: string[]
  notes?: string
}

/**
 * Measurement archive sections — groups of related measurements
 */
export interface MeasurementArchiveSection {
  sectionId: string
  label: string
  measurements: MeasurementArchiveMeasurement[]
}

/**
 * Individual measurement within a section
 */
export interface MeasurementArchiveMeasurement {
  property: string
  value: number
  unit: string
  confidence?: 'high' | 'medium' | 'low'
  notes?: string
}

/**
 * Complete measurement archive record
 */
export interface MeasurementArchiveRecord {
  archiveId: string
  kind: 'measurement-archive'
  metadata: MeasurementArchiveMetadata
  context: MeasurementArchiveContext
  sections: MeasurementArchiveSection[]
  snapshot?: DiagnosticSnapshot
  /**
   * Observational topology descriptors associated with this archive.
   * Indicates which experimental configuration(s) the archive was measured under.
   * Descriptive linkage only — not causal, not authoritative, not validated.
   * Dev Order 66: Added. Dev Order 67: Hardened.
   */
  topologyVariantReferences?: string[]
}

/**
 * Validation result for archive import
 */
export interface MeasurementArchiveValidationResult {
  valid: boolean
  errors: string[]
  warnings: string[]
  metadata?: {
    schemaVersion?: string
    kind?: string
    sectionCount?: number
    createdAtIso?: string
  }
}

/**
 * Archive export options
 */
export interface MeasurementArchiveExportOptions {
  includeSnapshot?: boolean
  pretty?: boolean
}
