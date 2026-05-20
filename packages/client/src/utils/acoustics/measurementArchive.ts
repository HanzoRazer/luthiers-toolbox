/**
 * Measurement Archive Utilities
 *
 * Dev Order 54: Measurement archive infrastructure foundation.
 * Dev Order 60: Added createArchiveFromDiagnosticContext for full experimental capture.
 * Dev Order 61: Added type guard, hardened utilities, filename/download/parse helpers.
 * Dev Order 62: Added evidence index utilities (sorting, grouping, filtering).
 * Dev Order 63: Added pairwise archive comparison utilities for residual analysis.
 *
 * Helpers for creating, normalizing, and validating measurement archives.
 * Schema validation only — does not validate acoustic correctness.
 *
 * All archive operations are local-only and observational.
 * No calibration, prediction, or authority semantics.
 */

import type {
  MeasurementArchiveRecord,
  MeasurementArchiveMetadata,
  MeasurementArchiveContext,
  MeasurementArchiveMeasurement,
  MeasurementArchiveIndexEntry,
  MeasurementArchiveValidationResult,
  MeasurementArchiveGeometrySummary,
  MeasurementArchiveSnapshotReference,
  MeasurementSource,
  MeasurementMethod,
} from '@/types/acoustics/measurementArchive'
import type { MeasuredResponse } from '@/types/measurements'
import type { DiagnosticSnapshot } from '@/types/diagnosticSnapshot'
import type { ResidualCoherenceSummary } from '@/types/residualCoherence'
import type { DiagnosticNarrativeSummary } from '@/types/diagnosticNarrative'

/**
 * Generate a unique archive ID.
 */
function generateArchiveId(): string {
  const timestamp = Date.now().toString(36)
  const random = Math.random().toString(36).substring(2, 8)
  return `archive-${timestamp}-${random}`
}

/**
 * Generate a unique measurement ID.
 */
function generateMeasurementId(): string {
  const timestamp = Date.now().toString(36)
  const random = Math.random().toString(36).substring(2, 6)
  return `meas-${timestamp}-${random}`
}

/**
 * Create archive metadata with current timestamp.
 */
export function createArchiveMetadata(): MeasurementArchiveMetadata {
  return {
    schemaVersion: 'measurement-archive.v1',
    kind: 'aperture-measurement-archive',
    generatedBy: 'aperture-workspace',
    createdAtIso: new Date().toISOString(),
    observationalOnly: true,
  }
}

/**
 * Create an empty measurement archive record.
 */
export function createMeasurementArchiveRecord(
  context?: Partial<MeasurementArchiveContext>,
  tags?: string[]
): MeasurementArchiveRecord {
  return {
    archiveId: generateArchiveId(),
    metadata: createArchiveMetadata(),
    context: {
      sessionStartIso: new Date().toISOString(),
      ...context,
    },
    measurements: [],
    provenanceReminder:
      'This archive contains observational measurements only. ' +
      'Measurements are not calibrated predictions and do not represent validated acoustic performance.',
    tags,
  }
}

/**
 * Create a measurement entry for an archive.
 */
export function createMeasurementEntry(
  data: Omit<MeasurementArchiveMeasurement, 'measurementId' | 'measuredAtIso'> & {
    measuredAtIso?: string
  }
): MeasurementArchiveMeasurement {
  return {
    measurementId: generateMeasurementId(),
    measuredAtIso: data.measuredAtIso ?? new Date().toISOString(),
    ...data,
  }
}

/**
 * Create a geometry summary from aperture data.
 */
export function createGeometrySummary(
  apertureType?: string,
  areaMm2?: number,
  equivalentDiameterMm?: number,
  paRatioMmInv?: number
): MeasurementArchiveGeometrySummary {
  return {
    apertureType,
    areaMm2,
    equivalentDiameterMm,
    paRatioMmInv,
  }
}

/**
 * Create a snapshot reference for provenance tracking.
 */
export function createSnapshotReference(
  snapshotId?: string,
  schemaVersion?: string,
  kind?: string,
  createdAtIso?: string
): MeasurementArchiveSnapshotReference {
  return {
    snapshotId,
    schemaVersion,
    kind,
    createdAtIso,
  }
}

/**
 * Normalize a measurement archive record.
 * Ensures all required fields are present with defaults.
 */
export function normalizeMeasurementArchive(
  record: Partial<MeasurementArchiveRecord>
): MeasurementArchiveRecord {
  const metadata = record.metadata ?? createArchiveMetadata()

  return {
    archiveId: record.archiveId ?? generateArchiveId(),
    metadata: {
      schemaVersion: metadata.schemaVersion ?? 'measurement-archive.v1',
      kind: metadata.kind ?? 'aperture-measurement-archive',
      generatedBy: metadata.generatedBy ?? 'aperture-workspace',
      createdAtIso: metadata.createdAtIso ?? new Date().toISOString(),
      observationalOnly: true,
    },
    context: record.context ?? {},
    measurements: record.measurements ?? [],
    provenanceReminder:
      record.provenanceReminder ??
      'This archive contains observational measurements only.',
    tags: record.tags,
  }
}

/**
 * Validate a measurement archive record.
 * Schema validation only — does not validate acoustic correctness.
 */
export function validateMeasurementArchive(
  data: unknown
): MeasurementArchiveValidationResult {
  const errors: string[] = []
  const warnings: string[] = []

  if (!data || typeof data !== 'object') {
    return {
      valid: false,
      errors: ['Archive data must be an object'],
      warnings: [],
    }
  }

  const record = data as Record<string, unknown>

  // Check required fields
  if (!record.archiveId || typeof record.archiveId !== 'string') {
    errors.push('Missing or invalid archiveId')
  }

  if (!record.metadata || typeof record.metadata !== 'object') {
    errors.push('Missing or invalid metadata')
  } else {
    const meta = record.metadata as Record<string, unknown>

    if (meta.schemaVersion !== 'measurement-archive.v1') {
      errors.push(`Unsupported schema version: ${meta.schemaVersion}`)
    }

    if (meta.kind !== 'aperture-measurement-archive') {
      errors.push(`Unsupported archive kind: ${meta.kind}`)
    }

    if (meta.observationalOnly !== true) {
      errors.push('Archive must be observational only')
    }
  }

  if (!Array.isArray(record.measurements)) {
    errors.push('Missing or invalid measurements array')
  }

  // Validate measurements
  const measurements = record.measurements as unknown[]
  if (Array.isArray(measurements)) {
    measurements.forEach((m, i) => {
      if (!m || typeof m !== 'object') {
        errors.push(`Measurement ${i} is not an object`)
        return
      }

      const meas = m as Record<string, unknown>

      if (!meas.measurementId || typeof meas.measurementId !== 'string') {
        warnings.push(`Measurement ${i} missing measurementId`)
      }

      if (!meas.measuredAtIso || typeof meas.measuredAtIso !== 'string') {
        warnings.push(`Measurement ${i} missing measuredAtIso`)
      }

      if (!meas.source || typeof meas.source !== 'string') {
        warnings.push(`Measurement ${i} missing source`)
      }

      if (!meas.method || typeof meas.method !== 'string') {
        warnings.push(`Measurement ${i} missing method`)
      }
    })
  }

  const schemaVersion =
    record.metadata &&
    typeof record.metadata === 'object' &&
    'schemaVersion' in record.metadata
      ? String((record.metadata as Record<string, unknown>).schemaVersion)
      : undefined

  return {
    valid: errors.length === 0,
    schemaVersion,
    measurementCount: Array.isArray(record.measurements)
      ? record.measurements.length
      : 0,
    errors,
    warnings,
  }
}

/**
 * Create an index entry from an archive record.
 */
export function createArchiveIndexEntry(
  record: MeasurementArchiveRecord
): MeasurementArchiveIndexEntry {
  return {
    archiveId: record.archiveId,
    createdAtIso: record.metadata.createdAtIso,
    measurementCount: record.measurements.length,
    referenceLabel: record.context.referenceLabel,
    candidateLabel: record.context.candidateLabel,
    tags: record.tags,
  }
}

/**
 * Format timestamp for display.
 */
export function formatArchiveTimestamp(iso: string): string {
  const date = new Date(iso)
  if (isNaN(date.getTime())) return 'Invalid'
  return date.toLocaleString()
}

/**
 * Type guard for MeasurementArchiveRecord.
 * Validates structure without full schema validation.
 */
export function isMeasurementArchiveRecord(value: unknown): value is MeasurementArchiveRecord {
  if (!value || typeof value !== 'object') return false

  const record = value as Record<string, unknown>

  if (typeof record.archiveId !== 'string') return false
  if (!record.metadata || typeof record.metadata !== 'object') return false
  if (!Array.isArray(record.measurements)) return false
  if (typeof record.provenanceReminder !== 'string') return false

  const meta = record.metadata as Record<string, unknown>
  if (meta.schemaVersion !== 'measurement-archive.v1') return false
  if (meta.kind !== 'aperture-measurement-archive') return false
  if (meta.observationalOnly !== true) return false

  return true
}

/**
 * Build a standardized filename for archive export.
 * Format: measurement-archive-v1-{YYYYMMDD-HHmmss}.json
 */
export function buildMeasurementArchiveFilename(record: MeasurementArchiveRecord): string {
  const date = new Date(record.metadata.createdAtIso)
  if (isNaN(date.getTime())) {
    return `measurement-archive-v1-${record.archiveId}.json`
  }

  const pad = (n: number) => n.toString().padStart(2, '0')
  const timestamp = [
    date.getUTCFullYear(),
    pad(date.getUTCMonth() + 1),
    pad(date.getUTCDate()),
    '-',
    pad(date.getUTCHours()),
    pad(date.getUTCMinutes()),
    pad(date.getUTCSeconds()),
  ].join('')

  return `measurement-archive-v1-${timestamp}.json`
}

/**
 * Trigger browser download of archive as JSON file.
 * Local-only operation — no upload or persistence.
 */
export function downloadMeasurementArchiveJson(record: MeasurementArchiveRecord): void {
  const json = JSON.stringify(record, null, 2)
  const blob = new Blob([json], { type: 'application/json' })
  const url = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = url
  link.download = buildMeasurementArchiveFilename(record)
  link.click()

  URL.revokeObjectURL(url)
}

/**
 * Result of parsing archive JSON.
 */
export interface ParseMeasurementArchiveResult {
  success: boolean
  archive: MeasurementArchiveRecord | null
  validation: MeasurementArchiveValidationResult | null
  parseError: string | null
}

/**
 * Parse JSON text and validate as measurement archive.
 * Does not mutate input — returns a fresh validated object.
 */
export function parseMeasurementArchiveJson(text: string): ParseMeasurementArchiveResult {
  let parsed: unknown

  try {
    parsed = JSON.parse(text)
  } catch (e) {
    return {
      success: false,
      archive: null,
      validation: null,
      parseError: e instanceof Error ? e.message : 'Invalid JSON',
    }
  }

  const validation = validateMeasurementArchive(parsed)

  if (!validation.valid) {
    return {
      success: false,
      archive: null,
      validation,
      parseError: null,
    }
  }

  return {
    success: true,
    archive: parsed as MeasurementArchiveRecord,
    validation,
    parseError: null,
  }
}

/**
 * Summary of a measurement archive for display.
 */
export interface MeasurementArchiveSummary {
  archiveId: string
  schemaVersion: string
  createdAt: string
  measurementCount: number
  referenceLabel: string | null
  candidateLabel: string | null
  hasLinkedSnapshot: boolean
  tagCount: number
}

/**
 * Create a human-readable summary of an archive.
 */
export function summarizeMeasurementArchive(record: MeasurementArchiveRecord): MeasurementArchiveSummary {
  const hasLinkedSnapshot = record.measurements.some(
    (m) => m.diagnosticSnapshotReference?.snapshotId
  )

  return {
    archiveId: record.archiveId,
    schemaVersion: record.metadata.schemaVersion,
    createdAt: formatArchiveTimestamp(record.metadata.createdAtIso),
    measurementCount: record.measurements.length,
    referenceLabel: record.context.referenceLabel ?? null,
    candidateLabel: record.context.candidateLabel ?? null,
    hasLinkedSnapshot,
    tagCount: record.tags?.length ?? 0,
  }
}

/**
 * Result of archive creation from diagnostic context.
 */
export interface CreateArchiveResult {
  success: boolean
  archive: MeasurementArchiveRecord | null
  error: string | null
}

/**
 * Diagnostic context for archive creation.
 * Captures full experimental state for observational archival.
 */
export interface DiagnosticContextForArchive {
  referenceLabel?: string
  candidateLabel?: string
  referenceMeasured?: MeasuredResponse
  candidateMeasured?: MeasuredResponse
  referenceGeometry?: MeasurementArchiveGeometrySummary
  candidateGeometry?: MeasurementArchiveGeometrySummary
  referenceCoherence?: ResidualCoherenceSummary
  candidateCoherence?: ResidualCoherenceSummary
  referenceNarrative?: DiagnosticNarrativeSummary
  candidateNarrative?: DiagnosticNarrativeSummary
  linkedSnapshot?: DiagnosticSnapshot
  tags?: string[]
  notes?: string
}

/**
 * Map MeasuredResponse source to archive MeasurementSource.
 */
function mapMeasurementSource(source: MeasuredResponse['source']): MeasurementSource {
  switch (source) {
    case 'manual':
      return 'manual_entry'
    case 'tap_tone_pi':
      return 'tap_tone'
    case 'imported_file':
      return 'external_import'
    default:
      return 'unknown'
  }
}

/**
 * Map MeasuredResponse method to archive MeasurementMethod.
 */
function mapMeasurementMethod(method: MeasuredResponse['method']): MeasurementMethod {
  switch (method) {
    case 'tap_test':
      return 'fft_peak_detection'
    case 'sine_sweep':
      return 'swept_sine'
    case 'impulse_response':
      return 'impulse_response'
    case 'manual_observation':
      return 'manual_reading'
    default:
      return 'unknown'
  }
}

/**
 * Create measurement entry from MeasuredResponse.
 */
function createMeasurementFromResponse(
  measured: MeasuredResponse,
  role: 'reference' | 'candidate',
  coherence?: ResidualCoherenceSummary,
  narrative?: DiagnosticNarrativeSummary,
  snapshotRef?: MeasurementArchiveSnapshotReference
): MeasurementArchiveMeasurement {
  const warnings: string[] = [...(measured.warnings ?? [])]

  if (coherence) {
    warnings.push(`Coherence: ${coherence.level} — ${coherence.message}`)
  }

  const notes = measured.notes?.join('; ')
  const narrativeNote = narrative
    ? `Narrative: ${narrative.tone} — ${narrative.narrative}`
    : undefined

  return {
    measurementId: `meas-${Date.now().toString(36)}-${Math.random().toString(36).substring(2, 6)}`,
    measuredAtIso: new Date().toISOString(),
    label: `${role}: ${measured.label}`,
    measuredHelmholtzHz: measured.measuredHelmholtzHz,
    measuredQ: measured.measuredQ,
    dominantPeakHz: measured.dominantPeakHz,
    source: mapMeasurementSource(measured.source),
    method: mapMeasurementMethod(measured.method),
    notes: [notes, narrativeNote].filter(Boolean).join(' | ') || undefined,
    warnings: warnings.length > 0 ? warnings : undefined,
    diagnosticSnapshotReference: snapshotRef,
  }
}

/**
 * Check if measured response has meaningful data worth archiving.
 */
function hasMeaningfulMeasurement(measured?: MeasuredResponse): boolean {
  if (!measured) return false
  return (
    measured.measuredHelmholtzHz !== undefined ||
    measured.measuredQ !== undefined ||
    measured.dominantPeakHz !== undefined
  )
}

/**
 * Create a measurement archive from full diagnostic context.
 *
 * Dev Order 60: Captures measured responses, geometry summaries, residual interpretation,
 * coherence state, narrative context, and linked snapshot reference.
 * Dev Order 61: Returns CreateArchiveResult; requires at least one measurement.
 *
 * Observational only — does NOT predict, calibrate, or assert authority.
 */
export function tryCreateArchiveFromDiagnosticContext(
  context: DiagnosticContextForArchive
): CreateArchiveResult {
  const {
    referenceLabel,
    candidateLabel,
    referenceMeasured,
    candidateMeasured,
    referenceGeometry,
    candidateGeometry,
    referenceCoherence,
    candidateCoherence,
    referenceNarrative,
    candidateNarrative,
    linkedSnapshot,
    tags,
    notes,
  } = context

  const snapshotRef: MeasurementArchiveSnapshotReference | undefined = linkedSnapshot
    ? {
        snapshotId: linkedSnapshot.id,
        schemaVersion: linkedSnapshot.schemaVersion,
        kind: linkedSnapshot.kind,
        createdAtIso: linkedSnapshot.createdAtIso,
      }
    : undefined

  const measurements: MeasurementArchiveMeasurement[] = []

  if (referenceMeasured && hasMeaningfulMeasurement(referenceMeasured)) {
    measurements.push(
      createMeasurementFromResponse(
        referenceMeasured,
        'reference',
        referenceCoherence,
        referenceNarrative,
        snapshotRef
      )
    )
  }

  if (candidateMeasured && hasMeaningfulMeasurement(candidateMeasured)) {
    measurements.push(
      createMeasurementFromResponse(
        candidateMeasured,
        'candidate',
        candidateCoherence,
        candidateNarrative,
        snapshotRef
      )
    )
  }

  if (measurements.length === 0) {
    return {
      success: false,
      archive: null,
      error: 'No meaningful measurements to archive. At least one measurement with data is required.',
    }
  }

  const archiveContext: MeasurementArchiveContext = {
    sessionStartIso: new Date().toISOString(),
    referenceLabel: referenceLabel ?? referenceMeasured?.label,
    candidateLabel: candidateLabel ?? candidateMeasured?.label,
    referenceGeometry,
    candidateGeometry,
    environmentNotes: notes,
  }

  const archiveTags = [...(tags ?? [])]
  if (linkedSnapshot) {
    archiveTags.push(`snapshot:${linkedSnapshot.id}`)
  }

  const archive: MeasurementArchiveRecord = {
    archiveId: `archive-${Date.now().toString(36)}-${Math.random().toString(36).substring(2, 8)}`,
    metadata: {
      schemaVersion: 'measurement-archive.v1',
      kind: 'aperture-measurement-archive',
      generatedBy: 'aperture-workspace',
      createdAtIso: new Date().toISOString(),
      observationalOnly: true,
    },
    context: archiveContext,
    measurements,
    provenanceReminder:
      'This archive contains observational measurements only. ' +
      'Measurements are not calibrated predictions and do not represent validated acoustic performance. ' +
      'Coherence and narrative annotations are observational interpretations, not authoritative conclusions.',
    tags: archiveTags.length > 0 ? archiveTags : undefined,
  }

  return {
    success: true,
    archive,
    error: null,
  }
}

/**
 * Create a measurement archive from full diagnostic context.
 * Returns null if no meaningful measurements are present.
 *
 * @deprecated Use tryCreateArchiveFromDiagnosticContext for better error handling.
 */
export function createArchiveFromDiagnosticContext(
  context: DiagnosticContextForArchive
): MeasurementArchiveRecord | null {
  const result = tryCreateArchiveFromDiagnosticContext(context)
  return result.archive
}

// ---------------------------------------------------------------------------
// Dev Order 62: Evidence Index Utilities
// ---------------------------------------------------------------------------

/**
 * Sort order for archive timestamp sorting.
 */
export type ArchiveSortOrder = 'newest' | 'oldest'

/**
 * Sort archives by creation timestamp.
 * Returns a new array — does not mutate input.
 */
export function sortMeasurementArchivesByTimestamp(
  records: MeasurementArchiveRecord[],
  order: ArchiveSortOrder = 'newest'
): MeasurementArchiveRecord[] {
  return [...records].sort((a, b) => {
    const aTime = new Date(a.metadata.createdAtIso).getTime()
    const bTime = new Date(b.metadata.createdAtIso).getTime()

    // Handle invalid dates by putting them at the end
    if (isNaN(aTime) && isNaN(bTime)) return 0
    if (isNaN(aTime)) return 1
    if (isNaN(bTime)) return -1

    return order === 'newest' ? bTime - aTime : aTime - bTime
  })
}

/**
 * Group of archives by measurement method.
 */
export interface ArchiveMethodGroup {
  method: MeasurementMethod
  archives: MeasurementArchiveRecord[]
}

/**
 * Group archives by the measurement methods they contain.
 * An archive appears in multiple groups if it has multiple methods.
 * Returns a new structure — does not mutate input.
 */
export function groupMeasurementArchivesByMethod(
  records: MeasurementArchiveRecord[]
): ArchiveMethodGroup[] {
  const methodMap = new Map<MeasurementMethod, MeasurementArchiveRecord[]>()

  for (const record of records) {
    const methods = new Set<MeasurementMethod>()
    for (const m of record.measurements) {
      if (m.method) {
        methods.add(m.method)
      }
    }

    for (const method of methods) {
      const existing = methodMap.get(method) ?? []
      existing.push(record)
      methodMap.set(method, existing)
    }
  }

  const groups: ArchiveMethodGroup[] = []
  for (const [method, archives] of methodMap) {
    groups.push({ method, archives })
  }

  // Sort groups by method name for stable ordering
  groups.sort((a, b) => a.method.localeCompare(b.method))

  return groups
}

/**
 * Filter archives to those linked to a specific diagnostic snapshot.
 * Returns a new array — does not mutate input.
 */
export function filterMeasurementArchivesBySnapshotReference(
  records: MeasurementArchiveRecord[],
  snapshotId: string
): MeasurementArchiveRecord[] {
  return records.filter((record) =>
    record.measurements.some(
      (m) => m.diagnosticSnapshotReference?.snapshotId === snapshotId
    )
  )
}

/**
 * Extended summary with sparse detection for evidence index display.
 */
export interface MeasurementArchiveEvidenceSummary extends MeasurementArchiveSummary {
  /** Unique measurement methods in this archive */
  methods: MeasurementMethod[]

  /** Experiment tags from metadata */
  experimentTags: string[]

  /** Archive has sparse data (few measurements, missing context) */
  isSparse: boolean

  /** Warnings about incomplete data */
  sparseWarnings: string[]

  /** ISO timestamp for sorting */
  createdAtIso: string
}

/**
 * Create an evidence summary for display in the evidence index.
 * Includes sparse detection and method enumeration.
 */
export function createEvidenceSummary(
  record: MeasurementArchiveRecord
): MeasurementArchiveEvidenceSummary {
  const baseSummary = summarizeMeasurementArchive(record)

  const methods = new Set<MeasurementMethod>()
  for (const m of record.measurements) {
    if (m.method) {
      methods.add(m.method)
    }
  }

  const sparseWarnings: string[] = []

  // Check for sparse conditions
  if (record.measurements.length === 0) {
    sparseWarnings.push('No measurements')
  } else if (record.measurements.length === 1) {
    sparseWarnings.push('Single measurement only')
  }

  if (!record.context.referenceLabel && !record.context.candidateLabel) {
    sparseWarnings.push('Missing context labels')
  }

  const hasMeaningfulData = record.measurements.some(
    (m) =>
      m.measuredHelmholtzHz !== undefined ||
      m.measuredQ !== undefined ||
      m.dominantPeakHz !== undefined
  )
  if (!hasMeaningfulData && record.measurements.length > 0) {
    sparseWarnings.push('No frequency or Q data')
  }

  return {
    ...baseSummary,
    methods: Array.from(methods).sort(),
    experimentTags: record.metadata.experimentTags ?? [],
    isSparse: sparseWarnings.length > 0,
    sparseWarnings,
    createdAtIso: record.metadata.createdAtIso,
  }
}

/**
 * Group archives by experiment tag.
 * Archives without tags appear in a special "untagged" group.
 */
export interface ArchiveExperimentTagGroup {
  tag: string
  archives: MeasurementArchiveRecord[]
}

/**
 * Group archives by their experiment tags.
 * An archive appears in multiple groups if it has multiple tags.
 */
export function groupMeasurementArchivesByExperimentTag(
  records: MeasurementArchiveRecord[]
): ArchiveExperimentTagGroup[] {
  const tagMap = new Map<string, MeasurementArchiveRecord[]>()
  const untagged: MeasurementArchiveRecord[] = []

  for (const record of records) {
    const tags = record.metadata.experimentTags ?? []

    if (tags.length === 0) {
      untagged.push(record)
    } else {
      for (const tag of tags) {
        const existing = tagMap.get(tag) ?? []
        existing.push(record)
        tagMap.set(tag, existing)
      }
    }
  }

  const groups: ArchiveExperimentTagGroup[] = []

  // Add tagged groups sorted alphabetically
  const sortedTags = Array.from(tagMap.keys()).sort()
  for (const tag of sortedTags) {
    groups.push({ tag, archives: tagMap.get(tag)! })
  }

  // Add untagged group at the end if non-empty
  if (untagged.length > 0) {
    groups.push({ tag: '(untagged)', archives: untagged })
  }

  return groups
}

// ---------------------------------------------------------------------------
// Dev Order 63: Pairwise Archive Comparison Utilities
// ---------------------------------------------------------------------------

/**
 * Residual divergence for a single acoustic property.
 */
export interface PropertyResidual {
  property: string
  label: string
  valueA: number
  valueB: number
  difference: number
  percentDifference: number | null
  unit: string
}

/**
 * Result of comparing two measurement archives.
 * Ephemeral — not persisted or archived.
 */
export interface ArchiveComparisonResult {
  archiveIdA: string
  archiveIdB: string
  labelA: string
  labelB: string
  comparedAtIso: string

  /** Individual property residuals */
  residuals: PropertyResidual[]

  /** Overall comparison status */
  status: 'comparable' | 'partial' | 'insufficient'

  /** Human-readable summary notes */
  notes: string[]

  /** Warnings about data limitations */
  warnings: string[]
}

/**
 * Extract comparable acoustic values from an archive.
 * Returns aggregated values across all measurements.
 */
function extractAcousticValues(
  record: MeasurementArchiveRecord
): Map<string, { sum: number; count: number; unit: string; label: string }> {
  const values = new Map<string, { sum: number; count: number; unit: string; label: string }>()

  for (const m of record.measurements) {
    if (m.measuredHelmholtzHz !== undefined) {
      const existing = values.get('measuredHelmholtzHz') ?? { sum: 0, count: 0, unit: 'Hz', label: 'Helmholtz Frequency' }
      existing.sum += m.measuredHelmholtzHz
      existing.count++
      values.set('measuredHelmholtzHz', existing)
    }

    if (m.measuredQ !== undefined) {
      const existing = values.get('measuredQ') ?? { sum: 0, count: 0, unit: '', label: 'Q Factor' }
      existing.sum += m.measuredQ
      existing.count++
      values.set('measuredQ', existing)
    }

    if (m.dominantPeakHz !== undefined) {
      const existing = values.get('dominantPeakHz') ?? { sum: 0, count: 0, unit: 'Hz', label: 'Dominant Peak' }
      existing.sum += m.dominantPeakHz
      existing.count++
      values.set('dominantPeakHz', existing)
    }
  }

  return values
}

/**
 * Compare two measurement archives and compute residuals.
 *
 * Dev Order 63: Pairwise observational comparison.
 * Returns ephemeral comparison result — not persisted.
 *
 * Observational only — does NOT rank, prescribe, or canonize.
 */
export function compareArchives(
  archiveA: MeasurementArchiveRecord,
  archiveB: MeasurementArchiveRecord
): ArchiveComparisonResult {
  const valuesA = extractAcousticValues(archiveA)
  const valuesB = extractAcousticValues(archiveB)

  const residuals: PropertyResidual[] = []
  const notes: string[] = []
  const warnings: string[] = []

  // Find shared properties
  const sharedProperties = new Set<string>()
  for (const key of valuesA.keys()) {
    if (valuesB.has(key)) {
      sharedProperties.add(key)
    }
  }

  // Properties only in A
  for (const key of valuesA.keys()) {
    if (!valuesB.has(key)) {
      warnings.push(`${valuesA.get(key)!.label} present only in Archive A`)
    }
  }

  // Properties only in B
  for (const key of valuesB.keys()) {
    if (!valuesA.has(key)) {
      warnings.push(`${valuesB.get(key)!.label} present only in Archive B`)
    }
  }

  // Compute residuals for shared properties
  for (const property of sharedProperties) {
    const a = valuesA.get(property)!
    const b = valuesB.get(property)!

    const avgA = a.sum / a.count
    const avgB = b.sum / b.count
    const difference = avgB - avgA
    const percentDifference = avgA !== 0 ? (difference / avgA) * 100 : null

    residuals.push({
      property,
      label: a.label,
      valueA: avgA,
      valueB: avgB,
      difference,
      percentDifference,
      unit: a.unit,
    })
  }

  // Determine status
  let status: 'comparable' | 'partial' | 'insufficient'
  if (residuals.length === 0) {
    status = 'insufficient'
    notes.push('No comparable acoustic properties found between archives.')
  } else if (warnings.length > 0) {
    status = 'partial'
    notes.push(`${residuals.length} comparable properties, ${warnings.length} properties differ.`)
  } else {
    status = 'comparable'
    notes.push(`${residuals.length} properties compared.`)
  }

  // Add observational narrative
  if (residuals.length > 0) {
    const helmholtzResidual = residuals.find((r) => r.property === 'measuredHelmholtzHz')
    if (helmholtzResidual) {
      const direction = helmholtzResidual.difference > 0 ? 'higher' : 'lower'
      const magnitude = Math.abs(helmholtzResidual.difference).toFixed(1)
      notes.push(`Helmholtz frequency in Archive B is ${magnitude} Hz ${direction} than Archive A.`)
    }
  }

  const labelA = archiveA.context.referenceLabel ?? archiveA.context.candidateLabel ?? archiveA.archiveId
  const labelB = archiveB.context.referenceLabel ?? archiveB.context.candidateLabel ?? archiveB.archiveId

  return {
    archiveIdA: archiveA.archiveId,
    archiveIdB: archiveB.archiveId,
    labelA,
    labelB,
    comparedAtIso: new Date().toISOString(),
    residuals,
    status,
    notes,
    warnings,
  }
}

/**
 * Get an observational interpretation of residual magnitude.
 * Returns qualitative label without prescription.
 */
export function interpretResidualMagnitude(
  percentDifference: number | null
): 'insufficient_data' | 'small' | 'moderate' | 'large' {
  if (percentDifference === null) {
    return 'insufficient_data'
  }

  const magnitude = Math.abs(percentDifference)

  if (magnitude < 5) {
    return 'small'
  } else if (magnitude < 15) {
    return 'moderate'
  } else {
    return 'large'
  }
}

/**
 * Generate observational narrative for archive comparison.
 * Strictly descriptive — no prescriptions or rankings.
 */
export function generateComparisonNarrative(result: ArchiveComparisonResult): string {
  if (result.status === 'insufficient') {
    return 'Insufficient comparable data between the selected archives. Consider archives with overlapping measurement properties.'
  }

  const parts: string[] = []

  parts.push(`Comparison between "${result.labelA}" and "${result.labelB}".`)

  if (result.residuals.length > 0) {
    const significantResiduals = result.residuals.filter(
      (r) => r.percentDifference !== null && Math.abs(r.percentDifference) >= 5
    )

    if (significantResiduals.length === 0) {
      parts.push('Residual divergence is small across all compared properties.')
    } else {
      const largest = significantResiduals.reduce((max, r) =>
        Math.abs(r.percentDifference ?? 0) > Math.abs(max.percentDifference ?? 0) ? r : max
      )
      const direction = largest.difference > 0 ? 'higher' : 'lower'
      parts.push(
        `Most notable divergence in ${largest.label}: ${Math.abs(largest.percentDifference ?? 0).toFixed(1)}% ${direction} in Archive B.`
      )
    }
  }

  if (result.warnings.length > 0) {
    parts.push(`Note: ${result.warnings.length} property asymmetries detected.`)
  }

  return parts.join(' ')
}
