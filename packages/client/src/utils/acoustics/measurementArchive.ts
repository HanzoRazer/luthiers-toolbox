/**
 * Measurement Archive Utilities
 *
 * Dev Order 60: Core archive creation, validation, and export utilities.
 * Dev Order 61: Timezone fix (UTC methods in filename generation).
 * Dev Order 62: Evidence index utilities (sorting, grouping, filtering).
 * Dev Order 63: Pairwise archive comparison utilities.
 *
 * All operations are observational only — no calibration, prediction, or mutation.
 */

import type {
  MeasurementArchiveRecord,
  MeasurementArchiveValidationResult,
  MeasurementArchiveContext,
  MeasurementArchiveSection,
  MeasurementArchiveExportOptions,
} from '@/types/acoustics/measurementArchive'
import type { DiagnosticSnapshot } from '@/types/diagnosticSnapshot'

/**
 * Generate a unique archive ID
 */
export function generateArchiveId(): string {
  const timestamp = Date.now().toString(36)
  const random = Math.random().toString(36).substring(2, 8)
  return `archive-${timestamp}-${random}`
}

/**
 * Build a measurement archive filename using UTC timestamps
 */
export function buildMeasurementArchiveFilename(
  archive: MeasurementArchiveRecord,
  extension: string = 'json'
): string {
  const date = new Date(archive.metadata.createdAtIso)
  const year = date.getUTCFullYear()
  const month = String(date.getUTCMonth() + 1).padStart(2, '0')
  const day = String(date.getUTCDate()).padStart(2, '0')
  const hours = String(date.getUTCHours()).padStart(2, '0')
  const minutes = String(date.getUTCMinutes()).padStart(2, '0')

  const label =
    archive.context.referenceLabel ?? archive.context.candidateLabel ?? 'measurement'
  const sanitizedLabel = label.replace(/[^a-zA-Z0-9-_]/g, '_').substring(0, 30)

  return `${sanitizedLabel}_${year}${month}${day}_${hours}${minutes}.${extension}`
}

/**
 * Create a new measurement archive
 */
export function createMeasurementArchive(
  context: MeasurementArchiveContext,
  sections: MeasurementArchiveSection[],
  snapshot?: DiagnosticSnapshot,
  options?: { tags?: string[]; experimentTags?: string[]; notes?: string }
): MeasurementArchiveRecord {
  return {
    archiveId: generateArchiveId(),
    kind: 'measurement-archive',
    metadata: {
      schemaVersion: 'measurement-archive.v1',
      createdAtIso: new Date().toISOString(),
      sourceApplication: 'luthiers-toolbox-client',
      tags: options?.tags,
      experimentTags: options?.experimentTags,
      notes: options?.notes,
    },
    context,
    sections,
    snapshot,
  }
}

/**
 * Validate an imported archive
 * @param data - The data to validate
 * @param existingArchiveIds - Optional set of existing archive IDs for duplicate detection
 */
export function validateMeasurementArchive(
  data: unknown,
  existingArchiveIds?: Set<string>
): MeasurementArchiveValidationResult {
  const errors: string[] = []
  const warnings: string[] = []

  if (typeof data !== 'object' || data === null) {
    return { valid: false, errors: ['Invalid data: expected object'], warnings }
  }

  const record = data as Record<string, unknown>

  // Check required fields
  if (record.kind !== 'measurement-archive') {
    errors.push(`Invalid kind: expected 'measurement-archive', got '${record.kind}'`)
  }

  const metadata = record.metadata as Record<string, unknown> | undefined
  if (!metadata) {
    errors.push('Missing metadata')
  } else {
    if (metadata.schemaVersion !== 'measurement-archive.v1') {
      errors.push(`Unsupported schema version: ${metadata.schemaVersion}`)
    }
    if (typeof metadata.createdAtIso !== 'string') {
      errors.push('Missing or invalid createdAtIso')
    }
  }

  if (!record.archiveId || typeof record.archiveId !== 'string') {
    errors.push('Missing or invalid archiveId')
  } else if (existingArchiveIds?.has(record.archiveId)) {
    warnings.push(`Duplicate archive ID detected: ${record.archiveId}`)
  }

  if (!Array.isArray(record.sections)) {
    errors.push('Missing or invalid sections array')
  } else if (record.sections.length === 0) {
    warnings.push('Archive contains no measurement sections')
  } else {
    // Count total measurements for sparse detection
    const measurementCount = record.sections.reduce(
      (sum: number, s: unknown) =>
        sum + (Array.isArray((s as Record<string, unknown>)?.measurements)
          ? ((s as Record<string, unknown>).measurements as unknown[]).length
          : 0),
      0
    )
    if (measurementCount < 3) {
      warnings.push(`Sparse archive: only ${measurementCount} measurement${measurementCount !== 1 ? 's' : ''} found`)
    }
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings,
    metadata: metadata
      ? {
          schemaVersion: metadata.schemaVersion as string | undefined,
          kind: record.kind as string | undefined,
          sectionCount: Array.isArray(record.sections) ? record.sections.length : undefined,
          createdAtIso: metadata.createdAtIso as string | undefined,
        }
      : undefined,
  }
}

/**
 * Export archive to JSON string
 */
export function exportMeasurementArchive(
  archive: MeasurementArchiveRecord,
  options?: MeasurementArchiveExportOptions
): string {
  const exportData = options?.includeSnapshot === false ? { ...archive, snapshot: undefined } : archive
  return JSON.stringify(exportData, null, options?.pretty ? 2 : undefined)
}

/**
 * Parse and validate archive from JSON string
 */
export function parseMeasurementArchive(
  json: string
): { archive: MeasurementArchiveRecord | null; validation: MeasurementArchiveValidationResult } {
  try {
    const data = JSON.parse(json)
    const validation = validateMeasurementArchive(data)
    return {
      archive: validation.valid ? (data as MeasurementArchiveRecord) : null,
      validation,
    }
  } catch (e) {
    return {
      archive: null,
      validation: {
        valid: false,
        errors: [`JSON parse error: ${e instanceof Error ? e.message : 'Unknown error'}`],
        warnings: [],
      },
    }
  }
}

// ============================================================================
// Dev Order 62: Evidence Index Utilities
// ============================================================================

/**
 * Sort archives by timestamp (newest first)
 * Handles missing/invalid timestamps by treating them as epoch 0.
 */
export function sortMeasurementArchivesByTimestamp(
  archives: MeasurementArchiveRecord[],
  direction: 'asc' | 'desc' = 'desc'
): MeasurementArchiveRecord[] {
  return [...archives].sort((a, b) => {
    const timeA = Date.parse(a.metadata?.createdAtIso ?? '') || 0
    const timeB = Date.parse(b.metadata?.createdAtIso ?? '') || 0
    return direction === 'desc' ? timeB - timeA : timeA - timeB
  })
}

/**
 * Group archives by measurement method (derived from section labels)
 */
export function groupMeasurementArchivesByMethod(
  archives: MeasurementArchiveRecord[]
): Map<string, MeasurementArchiveRecord[]> {
  const groups = new Map<string, MeasurementArchiveRecord[]>()

  for (const archive of archives) {
    const methods = archive.sections.map((s) => s.label).join(', ') || 'Unknown'
    const existing = groups.get(methods) ?? []
    groups.set(methods, [...existing, archive])
  }

  return groups
}

/**
 * Group archives by experiment tag
 */
export function groupMeasurementArchivesByExperimentTag(
  archives: MeasurementArchiveRecord[]
): Map<string, MeasurementArchiveRecord[]> {
  const groups = new Map<string, MeasurementArchiveRecord[]>()

  for (const archive of archives) {
    const tags = archive.metadata.experimentTags ?? ['Untagged']
    for (const tag of tags) {
      const existing = groups.get(tag) ?? []
      groups.set(tag, [...existing, archive])
    }
  }

  return groups
}

/**
 * Filter archives that reference a specific snapshot
 */
export function filterMeasurementArchivesBySnapshotReference(
  archives: MeasurementArchiveRecord[],
  snapshotId: string
): MeasurementArchiveRecord[] {
  return archives.filter((a) => a.snapshot?.id === snapshotId)
}

/**
 * Evidence summary for an archive collection
 */
export interface MeasurementArchiveEvidenceSummary {
  totalArchives: number
  dateRange: { earliest: string; latest: string } | null
  methodsUsed: string[]
  experimentTags: string[]
  sparseArchives: string[]
  notes: string[]
}

/**
 * Create evidence summary from archive collection
 */
export function createEvidenceSummary(
  archives: MeasurementArchiveRecord[]
): MeasurementArchiveEvidenceSummary {
  if (archives.length === 0) {
    return {
      totalArchives: 0,
      dateRange: null,
      methodsUsed: [],
      experimentTags: [],
      sparseArchives: [],
      notes: [],
    }
  }

  const sorted = sortMeasurementArchivesByTimestamp(archives, 'asc')
  const methods = new Set<string>()
  const tags = new Set<string>()
  const sparseArchives: string[] = []
  const notes: string[] = []

  for (const archive of archives) {
    for (const section of archive.sections) {
      methods.add(section.label)
    }
    for (const tag of archive.metadata.experimentTags ?? []) {
      tags.add(tag)
    }

    // Detect sparse archives (few measurements)
    const measurementCount = archive.sections.reduce((sum, s) => sum + s.measurements.length, 0)
    if (measurementCount < 3) {
      sparseArchives.push(archive.archiveId)
    }

    if (archive.metadata.notes) {
      notes.push(archive.metadata.notes)
    }
  }

  return {
    totalArchives: archives.length,
    dateRange: {
      earliest: sorted[0].metadata.createdAtIso,
      latest: sorted[sorted.length - 1].metadata.createdAtIso,
    },
    methodsUsed: Array.from(methods),
    experimentTags: Array.from(tags),
    sparseArchives,
    notes,
  }
}

// ============================================================================
// Dev Order 63: Pairwise Archive Comparison Utilities
// ============================================================================

/**
 * Property residual — divergence between two archives on a single property
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
 * Archive comparison result
 */
export interface ArchiveComparisonResult {
  archiveIdA: string
  archiveIdB: string
  status: 'comparable' | 'partial' | 'insufficient'
  residuals: PropertyResidual[]
  warnings: string[]
  notes: string[]
}

/**
 * Compare two archives and compute residuals
 */
export function compareArchives(
  archiveA: MeasurementArchiveRecord,
  archiveB: MeasurementArchiveRecord
): ArchiveComparisonResult {
  const residuals: PropertyResidual[] = []
  const warnings: string[] = []
  const notes: string[] = []

  // Build measurement maps
  const measurementsA = new Map<string, { value: number; unit: string; label: string }>()
  const measurementsB = new Map<string, { value: number; unit: string; label: string }>()

  for (const section of archiveA.sections) {
    for (const m of section.measurements) {
      measurementsA.set(m.property, { value: m.value, unit: m.unit, label: section.label })
    }
  }

  for (const section of archiveB.sections) {
    for (const m of section.measurements) {
      measurementsB.set(m.property, { value: m.value, unit: m.unit, label: section.label })
    }
  }

  // Find common properties
  const commonProperties = new Set<string>()
  for (const key of measurementsA.keys()) {
    if (measurementsB.has(key)) {
      commonProperties.add(key)
    }
  }

  // Compute residuals for common properties
  const priorityOrder = ['measuredHelmholtzHz', 'measuredQFactor', 'dominantPeakHz']
  const sortedProperties = Array.from(commonProperties).sort((a, b) => {
    const idxA = priorityOrder.indexOf(a)
    const idxB = priorityOrder.indexOf(b)
    if (idxA >= 0 && idxB >= 0) return idxA - idxB
    if (idxA >= 0) return -1
    if (idxB >= 0) return 1
    return a.localeCompare(b)
  })

  for (const property of sortedProperties) {
    const mA = measurementsA.get(property)!
    const mB = measurementsB.get(property)!

    const difference = mB.value - mA.value
    const percentDifference = mA.value !== 0 ? (difference / mA.value) * 100 : null

    residuals.push({
      property,
      label: formatPropertyLabel(property),
      valueA: mA.value,
      valueB: mB.value,
      difference,
      percentDifference,
      unit: mA.unit,
    })
  }

  // Detect asymmetries
  const onlyInA = Array.from(measurementsA.keys()).filter((k) => !measurementsB.has(k))
  const onlyInB = Array.from(measurementsB.keys()).filter((k) => !measurementsA.has(k))

  if (onlyInA.length > 0) {
    warnings.push(`Properties only in Archive A: ${onlyInA.join(', ')}`)
  }
  if (onlyInB.length > 0) {
    warnings.push(`Properties only in Archive B: ${onlyInB.join(', ')}`)
  }

  // Determine status
  let status: 'comparable' | 'partial' | 'insufficient'
  if (residuals.length >= 3) {
    status = 'comparable'
  } else if (residuals.length > 0) {
    status = 'partial'
  } else {
    status = 'insufficient'
  }

  // Add notes
  if (archiveA.metadata.notes) {
    notes.push(`Archive A: ${archiveA.metadata.notes}`)
  }
  if (archiveB.metadata.notes) {
    notes.push(`Archive B: ${archiveB.metadata.notes}`)
  }

  return {
    archiveIdA: archiveA.archiveId,
    archiveIdB: archiveB.archiveId,
    status,
    residuals,
    warnings,
    notes,
  }
}

/**
 * Interpret residual magnitude
 */
export function interpretResidualMagnitude(
  percentDifference: number | null
): 'small' | 'moderate' | 'large' | 'unknown' {
  if (percentDifference === null) return 'unknown'
  const abs = Math.abs(percentDifference)
  if (abs < 5) return 'small'
  if (abs < 15) return 'moderate'
  return 'large'
}

/**
 * Generate comparison narrative
 */
export function generateComparisonNarrative(result: ArchiveComparisonResult): string {
  if (result.status === 'insufficient') {
    return 'Insufficient comparable data between the two archives. Consider aligning measurement methods.'
  }

  const parts: string[] = []

  if (result.residuals.length > 0) {
    const primary = result.residuals[0]
    const magnitude = interpretResidualMagnitude(primary.percentDifference)

    if (magnitude === 'small') {
      parts.push(
        `${primary.label} shows small divergence (${primary.difference >= 0 ? '+' : ''}${primary.difference.toFixed(1)} ${primary.unit}).`
      )
    } else if (magnitude === 'moderate') {
      parts.push(
        `${primary.label} shows moderate divergence (${primary.difference >= 0 ? '+' : ''}${primary.difference.toFixed(1)} ${primary.unit}, ${primary.percentDifference?.toFixed(1)}%).`
      )
    } else if (magnitude === 'large') {
      parts.push(
        `${primary.label} shows large divergence (${primary.difference >= 0 ? '+' : ''}${primary.difference.toFixed(1)} ${primary.unit}, ${primary.percentDifference?.toFixed(1)}%). This may indicate significant experimental variance.`
      )
    }
  }

  if (result.warnings.length > 0) {
    parts.push('Some properties could not be compared due to measurement asymmetry.')
  }

  if (result.status === 'partial') {
    parts.push('Comparison is partial due to limited overlapping measurements.')
  }

  return parts.join(' ') || 'Comparison complete.'
}

/**
 * Format archive timestamp for display
 */
export function formatArchiveTimestamp(isoString: string): string {
  const date = new Date(isoString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/**
 * Format property name to human-readable label
 */
function formatPropertyLabel(property: string): string {
  const labels: Record<string, string> = {
    measuredHelmholtzHz: 'Helmholtz (Hz)',
    measuredQFactor: 'Q Factor',
    dominantPeakHz: 'Dominant Peak (Hz)',
    bodyVolumeCm3: 'Body Volume (cm³)',
    apertureAreaMm2: 'Aperture Area (mm²)',
  }
  return labels[property] ?? property.replace(/([A-Z])/g, ' $1').trim()
}

// ============================================================================
// Dev Order 64: QA & UX Stabilization Utilities
// ============================================================================

/**
 * Get display label for an archive
 */
export function getMeasurementArchiveDisplayLabel(record: MeasurementArchiveRecord): string {
  return (
    record.context.referenceLabel ??
    record.context.candidateLabel ??
    record.archiveId
  )
}

/**
 * Check if two archives have comparable measurement fields
 */
export function hasComparableMeasurementFields(
  a: MeasurementArchiveRecord,
  b: MeasurementArchiveRecord
): boolean {
  const propsA = new Set<string>()
  const propsB = new Set<string>()

  for (const section of a.sections) {
    for (const m of section.measurements) {
      if (typeof m.value === 'number') {
        propsA.add(m.property)
      }
    }
  }

  for (const section of b.sections) {
    for (const m of section.measurements) {
      if (typeof m.value === 'number') {
        propsB.add(m.property)
      }
    }
  }

  for (const prop of propsA) {
    if (propsB.has(prop)) {
      return true
    }
  }

  return false
}

/**
 * Detect if an archive ID already exists in a list
 */
export function detectDuplicateArchiveId(
  archives: MeasurementArchiveRecord[],
  newArchive: MeasurementArchiveRecord
): boolean {
  return archives.some((a) => a.archiveId === newArchive.archiveId)
}

/**
 * Dedupe measurement archives by archiveId (keeps first occurrence)
 */
export function dedupeMeasurementArchives(
  records: MeasurementArchiveRecord[]
): MeasurementArchiveRecord[] {
  const seen = new Set<string>()
  const result: MeasurementArchiveRecord[] = []

  for (const record of records) {
    if (!seen.has(record.archiveId)) {
      seen.add(record.archiveId)
      result.push(record)
    }
  }

  return result
}

/**
 * Merge result with duplicate detection metadata
 */
export interface MergeMeasurementArchivesResult {
  merged: MeasurementArchiveRecord[]
  duplicatesDetected: string[]
  invalidSkipped: number
}

/**
 * Merge measurement archive lists with duplicate detection
 * Does not mutate input arrays.
 * Preserves existing order when timestamps are equal.
 * Rejects/skips invalid archive records.
 */
export function mergeMeasurementArchiveLists(
  existing: MeasurementArchiveRecord[],
  incoming: MeasurementArchiveRecord[]
): MergeMeasurementArchivesResult {
  const existingIds = new Set(existing.map((a) => a.archiveId))
  const merged: MeasurementArchiveRecord[] = [...existing]
  const duplicatesDetected: string[] = []
  let invalidSkipped = 0

  for (const record of incoming) {
    // Skip invalid records
    if (!record.archiveId || record.kind !== 'measurement-archive') {
      invalidSkipped++
      continue
    }

    // Detect duplicates
    if (existingIds.has(record.archiveId)) {
      duplicatesDetected.push(record.archiveId)
      continue
    }

    existingIds.add(record.archiveId)
    merged.push(record)
  }

  return {
    merged,
    duplicatesDetected,
    invalidSkipped,
  }
}

/**
 * Validate archive is safe for use (defensive check)
 */
export function isValidArchiveRecord(record: unknown): record is MeasurementArchiveRecord {
  if (typeof record !== 'object' || record === null) return false

  const r = record as Record<string, unknown>
  if (typeof r.archiveId !== 'string') return false
  if (r.kind !== 'measurement-archive') return false
  if (typeof r.metadata !== 'object' || r.metadata === null) return false
  if (!Array.isArray(r.sections)) return false

  return true
}

/**
 * Safe timestamp parser with fallback
 */
export function safeParseArchiveTimestamp(isoString: string | undefined): number {
  if (!isoString) return 0
  const parsed = Date.parse(isoString)
  return isNaN(parsed) ? 0 : parsed
}
