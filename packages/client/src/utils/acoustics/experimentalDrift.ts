/**
 * Experimental Drift Utilities
 *
 * Dev Order 70: Experimental drift timeline workspace
 *
 * Drift represents measured acoustic change observed across sequential archives.
 * Drift is observational only — it describes temporal patterns without implying
 * causation, optimization, or design superiority.
 *
 * OBSERVATIONAL ONLY:
 * - Drift does NOT imply improvement or degradation
 * - No optimization, recommendation, or prediction semantics
 * - No authority claims about acoustic behavior
 *
 * Allowed language: shifted, diverged, stabilized, observed, repeatedly observed
 * Forbidden language: improved, optimized, better, fixed, recommended, validated
 *
 * Schema: experimental-drift.v1
 * Storage: in-memory only (no persistence backend)
 */

import type { MeasurementArchiveRecord } from '../../types/acoustics/measurementArchive'
import type {
  DriftDirection,
  DriftContextType,
  DriftTimelinePoint,
  DriftFieldChange,
  DriftSequence,
  ExperimentalDriftRecord,
  ExperimentalDriftSummary,
  DriftComputeResult,
} from '../../types/acoustics/experimentalDrift'
import {
  isValidArchiveForCorrelation,
  isSparseArchive,
  deduplicateArchives,
} from './experimentalCorrelation'

/** Minimum archives required for drift detection */
export const MINIMUM_DRIFT_SAMPLE_SIZE = 3

/** Threshold for drift direction classification (5%) */
export const DRIFT_DIRECTION_THRESHOLD = 0.05

/** Threshold for variable detection via standard deviation (10%) */
export const DRIFT_VARIABLE_STDEV_THRESHOLD = 0.10

/** Minimum sign reversals for variable classification */
export const DRIFT_VARIABLE_REVERSAL_THRESHOLD = 2

/** Fields eligible for drift tracking */
export const DRIFT_TRACKABLE_FIELDS = [
  'measuredHelmholtzHz',
  'measuredPeakHz',
  'measuredDampingFactor',
  'measuredQ',
] as const

export type DriftTrackableField = (typeof DRIFT_TRACKABLE_FIELDS)[number]

/**
 * Check if archives have sufficient data for drift detection
 * Dev Order 71: Uses deduplication and validation
 */
export function hasSufficientDriftData(archives: MeasurementArchiveRecord[]): boolean {
  const { archives: prepared } = prepareDriftableArchives(archives)
  return prepared.length >= MINIMUM_DRIFT_SAMPLE_SIZE
}

/**
 * Re-export correlation validators for external use
 */
export { isValidArchiveForCorrelation, isSparseArchive, deduplicateArchives }

/**
 * Sort archives chronologically by createdAtIso
 */
export function sortArchivesChronologically(
  archives: MeasurementArchiveRecord[]
): MeasurementArchiveRecord[] {
  return [...archives].sort((a, b) => {
    const aTime = a.metadata?.createdAtIso ?? ''
    const bTime = b.metadata?.createdAtIso ?? ''
    return aTime.localeCompare(bTime)
  })
}

/**
 * Extract a numeric field value from an archive
 */
function extractFieldValue(
  archive: MeasurementArchiveRecord,
  field: DriftTrackableField
): number | undefined {
  const measurements = archive.measurements
  if (!measurements) return undefined

  switch (field) {
    case 'measuredHelmholtzHz':
      return measurements.measuredHelmholtzHz
    case 'measuredPeakHz':
      return measurements.measuredPeakHz
    case 'measuredDampingFactor':
      return measurements.measuredDampingFactor
    case 'measuredQ':
      return measurements.measuredQ
    default:
      return undefined
  }
}

/**
 * Extract a comparable field series from archives
 * Returns archives paired with their field values (excludes undefined)
 */
export function extractComparableFieldSeries(
  archives: MeasurementArchiveRecord[],
  field: DriftTrackableField
): Array<{ archive: MeasurementArchiveRecord; value: number }> {
  const result: Array<{ archive: MeasurementArchiveRecord; value: number }> = []

  for (const archive of archives) {
    const value = extractFieldValue(archive, field)
    if (value !== undefined) {
      result.push({ archive, value })
    }
  }

  return result
}

/**
 * Count sign reversals in sequential deltas
 * A reversal occurs when delta changes from positive to negative or vice versa
 */
export function countSignReversals(points: DriftTimelinePoint[]): number {
  if (points.length < 3) return 0

  let reversals = 0
  let prevSign: number | null = null

  for (let i = 1; i < points.length; i++) {
    const delta = points[i].deltaFromPrevious
    if (delta === undefined || delta === 0) continue

    const currentSign = delta > 0 ? 1 : -1
    if (prevSign !== null && currentSign !== prevSign) {
      reversals++
    }
    prevSign = currentSign
  }

  return reversals
}

/**
 * Calculate standard deviation of percent deltas
 */
export function calculatePercentDeltaStdev(points: DriftTimelinePoint[]): number {
  const percentDeltas: number[] = []

  for (const point of points) {
    if (point.percentDeltaFromPrevious !== undefined) {
      percentDeltas.push(point.percentDeltaFromPrevious)
    }
  }

  if (percentDeltas.length < 2) return 0

  const mean = percentDeltas.reduce((sum, v) => sum + v, 0) / percentDeltas.length
  const squaredDiffs = percentDeltas.map((v) => (v - mean) ** 2)
  const variance = squaredDiffs.reduce((sum, v) => sum + v, 0) / percentDeltas.length

  return Math.sqrt(variance)
}

/**
 * Check if timeline shows variable behavior
 * Variable = 2+ sign reversals OR stdev of percent deltas > 10%
 */
export function isVariableDrift(points: DriftTimelinePoint[]): boolean {
  const reversals = countSignReversals(points)
  if (reversals >= DRIFT_VARIABLE_REVERSAL_THRESHOLD) return true

  const stdev = calculatePercentDeltaStdev(points)
  if (stdev > DRIFT_VARIABLE_STDEV_THRESHOLD) return true

  return false
}

/**
 * Classify drift direction based on net percentage change and timeline variability
 * Uses 5% threshold: <5% = stable, >=5% = directional
 * Variable detection: 2+ sign reversals OR stdev > 10%
 */
export function classifyDriftDirection(
  netPercentDelta: number,
  points?: DriftTimelinePoint[]
): DriftDirection {
  // Check for variable behavior first if points provided
  if (points && points.length >= 3 && isVariableDrift(points)) {
    return 'variable'
  }

  const absChange = Math.abs(netPercentDelta)

  if (absChange < DRIFT_DIRECTION_THRESHOLD) {
    return 'stable'
  }

  return netPercentDelta > 0 ? 'upward' : 'downward'
}

/**
 * Generate drift ID
 */
function generateDriftId(): string {
  return `drift-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

/**
 * Generate sequence ID
 */
function generateSequenceId(): string {
  return `seq-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

/**
 * Build drift timeline points from a field series
 */
function buildTimelinePoints(
  series: Array<{ archive: MeasurementArchiveRecord; value: number }>
): DriftTimelinePoint[] {
  const points: DriftTimelinePoint[] = []

  for (let i = 0; i < series.length; i++) {
    const { archive, value } = series[i]
    const point: DriftTimelinePoint = {
      archiveId: archive.archiveId,
      timestamp: archive.metadata?.createdAtIso,
      value,
      variantId: archive.topologyVariantReferences?.[0],
      sessionContext: archive.context?.sessionContext,
    }

    if (i > 0) {
      const prevValue = series[i - 1].value
      point.deltaFromPrevious = value - prevValue
      point.percentDeltaFromPrevious = prevValue !== 0 ? (value - prevValue) / prevValue : 0
    }

    points.push(point)
  }

  return points
}

/**
 * Compute field change summary
 */
function computeFieldChange(
  field: string,
  points: DriftTimelinePoint[]
): DriftFieldChange | undefined {
  if (points.length < 2) return undefined

  const startValue = points[0].value
  const endValue = points[points.length - 1].value
  const netDelta = endValue - startValue
  const netPercentDelta = startValue !== 0 ? netDelta / startValue : 0

  return {
    field,
    startValue,
    endValue,
    netDelta,
    netPercentDelta,
    direction: classifyDriftDirection(netPercentDelta, points),
  }
}

/**
 * Build narrative describing the observed drift
 * Uses observational-only language
 */
export function buildDriftNarrative(
  field: string,
  direction: DriftDirection,
  netPercentDelta: number,
  sampleCount: number
): string {
  const percentStr = (Math.abs(netPercentDelta) * 100).toFixed(1)

  switch (direction) {
    case 'upward':
      return `${field} shifted upward by ${percentStr}% across ${sampleCount} sequential observations`
    case 'downward':
      return `${field} shifted downward by ${percentStr}% across ${sampleCount} sequential observations`
    case 'stable':
      return `${field} remained stable (${percentStr}% variation) across ${sampleCount} sequential observations`
    case 'variable':
      return `${field} showed variable behavior across ${sampleCount} sequential observations`
    default:
      return `${field} observed across ${sampleCount} sequential observations`
  }
}

/**
 * Group archives by topology variant for drift analysis
 */
export function groupArchivesByVariantTimeline(
  archives: MeasurementArchiveRecord[]
): Map<string, MeasurementArchiveRecord[]> {
  const groups = new Map<string, MeasurementArchiveRecord[]>()

  for (const archive of archives) {
    const refs = archive.topologyVariantReferences
    if (!refs || refs.length === 0) {
      const existing = groups.get('__none__') ?? []
      existing.push(archive)
      groups.set('__none__', existing)
      continue
    }

    for (const variantId of refs) {
      const existing = groups.get(variantId) ?? []
      existing.push(archive)
      groups.set(variantId, existing)
    }
  }

  return groups
}

/**
 * Group archives by session context for drift analysis
 */
export function groupArchivesBySessionTimeline(
  archives: MeasurementArchiveRecord[]
): Map<string, MeasurementArchiveRecord[]> {
  const groups = new Map<string, MeasurementArchiveRecord[]>()

  for (const archive of archives) {
    const sessionContext = archive.context?.sessionContext ?? '__none__'
    const existing = groups.get(sessionContext) ?? []
    existing.push(archive)
    groups.set(sessionContext, existing)
  }

  return groups
}

/**
 * Dev Order 71: Filter archives to valid, non-sparse records for drift analysis
 * Reuses correlation validators for consistency
 */
export function filterDriftableArchives(
  archives: MeasurementArchiveRecord[]
): { valid: MeasurementArchiveRecord[]; warnings: string[] } {
  const valid: MeasurementArchiveRecord[] = []
  const warnings: string[] = []

  for (const archive of archives) {
    if (!isValidArchiveForCorrelation(archive)) {
      warnings.push(`Archive skipped: invalid structure`)
      continue
    }
    if (isSparseArchive(archive)) {
      warnings.push(
        `Archive '${archive.archiveId}' is sparse — included but flagged`
      )
    }
    valid.push(archive)
  }

  return { valid, warnings }
}

/**
 * Dev Order 71: Prepare archives for drift analysis
 * Deduplicates first, then filters invalid archives, then sorts chronologically
 */
export function prepareDriftableArchives(
  archives: MeasurementArchiveRecord[]
): { archives: MeasurementArchiveRecord[]; warnings: string[] } {
  // Deduplicate first
  const deduplicated = deduplicateArchives(archives)

  // Filter invalid/sparse
  const { valid, warnings } = filterDriftableArchives(deduplicated)

  // Sort chronologically
  const sorted = sortArchivesChronologically(valid)

  return { archives: sorted, warnings }
}

/**
 * Build drift sequences from grouped archives
 */
export function buildDriftSequences(
  archives: MeasurementArchiveRecord[],
  contextType: DriftContextType
): DriftSequence[] {
  const sequences: DriftSequence[] = []

  let groups: Map<string, MeasurementArchiveRecord[]>

  switch (contextType) {
    case 'variant':
      groups = groupArchivesByVariantTimeline(archives)
      break
    case 'session':
      groups = groupArchivesBySessionTimeline(archives)
      break
    case 'chronological':
      groups = new Map([['all', archives]])
      break
    default:
      groups = new Map([['all', archives]])
  }

  for (const [contextId, groupArchives] of groups) {
    const sorted = sortArchivesChronologically(groupArchives)

    if (sorted.length >= MINIMUM_DRIFT_SAMPLE_SIZE) {
      sequences.push({
        sequenceId: generateSequenceId(),
        contextId,
        contextLabel:
          contextId === '__none__'
            ? 'No context'
            : contextId === 'all'
              ? 'All archives'
              : contextId,
        contextType,
        archiveIds: sorted.map((a) => a.archiveId),
        archiveCount: sorted.length,
      })
    }
  }

  return sequences
}

/**
 * Compute drift for a single field across a sequence
 */
function computeDriftForField(
  archives: MeasurementArchiveRecord[],
  field: DriftTrackableField,
  contextId: string,
  contextType: DriftContextType
): ExperimentalDriftRecord | undefined {
  const sorted = sortArchivesChronologically(archives)
  const series = extractComparableFieldSeries(sorted, field)

  if (series.length < MINIMUM_DRIFT_SAMPLE_SIZE) {
    return undefined
  }

  const points = buildTimelinePoints(series)
  const change = computeFieldChange(field, points)

  if (!change) return undefined

  return {
    driftId: generateDriftId(),
    archiveIds: series.map((s) => s.archive.archiveId),
    observedField: field,
    direction: change.direction,
    sampleCount: series.length,
    timelinePoints: points,
    narrative: buildDriftNarrative(field, change.direction, change.netPercentDelta, series.length),
    contextId,
    contextType,
    computedAtIso: new Date().toISOString(),
  }
}

/**
 * Determine dominant direction from a set of drift records
 */
function computeDominantDirection(drifts: ExperimentalDriftRecord[]): DriftDirection {
  if (drifts.length === 0) return 'stable'

  const counts = { upward: 0, downward: 0, stable: 0, variable: 0 }

  for (const drift of drifts) {
    counts[drift.direction]++
  }

  const max = Math.max(counts.upward, counts.downward, counts.stable, counts.variable)

  if (counts.upward === max) return 'upward'
  if (counts.downward === max) return 'downward'
  if (counts.stable === max) return 'stable'
  return 'variable'
}

/**
 * Compute experimental drift from archives
 *
 * Main entry point for drift analysis. Analyzes all trackable fields
 * across different context groupings (variant, session, chronological).
 *
 * Dev Order 71: Archives are deduplicated and filtered before analysis.
 * Does not mutate input array.
 */
export function computeExperimentalDrift(
  archives: MeasurementArchiveRecord[],
  contextType: DriftContextType = 'chronological'
): DriftComputeResult {
  const totalArchivesProvided = archives.length

  // Dev Order 71: Deduplicate, filter, and sort archives
  const { archives: preparedArchives, warnings } = prepareDriftableArchives(archives)

  const drifts: ExperimentalDriftRecord[] = []
  const summaries: ExperimentalDriftSummary[] = []
  const insufficientContexts: string[] = []

  let groups: Map<string, MeasurementArchiveRecord[]>

  switch (contextType) {
    case 'variant':
      groups = groupArchivesByVariantTimeline(preparedArchives)
      break
    case 'session':
      groups = groupArchivesBySessionTimeline(preparedArchives)
      break
    case 'chronological':
      groups = new Map([['all', preparedArchives]])
      break
    default:
      groups = new Map([['all', preparedArchives]])
  }

  for (const [contextId, groupArchives] of groups) {
    const sorted = sortArchivesChronologically(groupArchives)

    if (sorted.length < MINIMUM_DRIFT_SAMPLE_SIZE) {
      insufficientContexts.push(contextId)
      continue
    }

    const contextDrifts: ExperimentalDriftRecord[] = []

    for (const field of DRIFT_TRACKABLE_FIELDS) {
      const drift = computeDriftForField(sorted, field, contextId, contextType)
      if (drift) {
        drifts.push(drift)
        contextDrifts.push(drift)
      }
    }

    if (contextDrifts.length > 0) {
      const uniqueArchiveIds = new Set<string>()
      for (const d of contextDrifts) {
        for (const id of d.archiveIds) {
          uniqueArchiveIds.add(id)
        }
      }

      summaries.push({
        contextId,
        contextLabel:
          contextId === '__none__'
            ? 'No context'
            : contextId === 'all'
              ? 'All archives'
              : contextId,
        contextType,
        driftCount: contextDrifts.length,
        archiveCount: uniqueArchiveIds.size,
        dominantDirection: computeDominantDirection(contextDrifts),
      })
    }
  }

  return {
    drifts,
    summaries,
    insufficientContexts,
    totalArchivesAnalyzed: preparedArchives.length,
    totalArchivesProvided,
    warnings,
    computedAtIso: new Date().toISOString(),
  }
}

/**
 * Filter drifts by direction
 */
export function filterDriftsByDirection(
  drifts: ExperimentalDriftRecord[],
  direction: DriftDirection
): ExperimentalDriftRecord[] {
  return drifts.filter((d) => d.direction === direction)
}

/**
 * Filter drifts by field
 */
export function filterDriftsByField(
  drifts: ExperimentalDriftRecord[],
  field: DriftTrackableField
): ExperimentalDriftRecord[] {
  return drifts.filter((d) => d.observedField === field)
}

/**
 * Get drift records for a specific context
 */
export function getDriftsForContext(
  drifts: ExperimentalDriftRecord[],
  contextId: string
): ExperimentalDriftRecord[] {
  return drifts.filter((d) => d.contextId === contextId)
}
