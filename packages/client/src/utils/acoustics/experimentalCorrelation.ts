/**
 * Experimental Correlation Utilities
 *
 * Dev Order 68: Computed observational correlations
 *
 * Analyzes archives grouped by topology variant to detect
 * residual patterns. All correlations are observational only —
 * no causation, optimization, or recommendation semantics.
 *
 * Minimum sample size: 3 archives per variant
 * Below threshold: "insufficient evidence for correlation"
 */

import type {
  ExperimentalCorrelation,
  CorrelationConfidenceBand,
  VariantCorrelationSummary,
  CorrelationComputeResult,
} from '@/types/acoustics/experimentalCorrelation'
import type { MeasurementArchiveRecord } from '@/types/acoustics/measurementArchive'
import type { TopologyVariant } from '@/types/acoustics/topologyVariant'
import { groupArchivesByTopologyVariant } from './topologyVariant'

/** Minimum archives required for correlation detection */
const MIN_SAMPLE_SIZE = 3

/** Fields we analyze for correlation patterns */
const ANALYZABLE_FIELDS = [
  'measuredHelmholtzHz',
  'measuredPeakHz',
  'measuredDampingFactor',
  'measuredQ',
] as const

type AnalyzableField = typeof ANALYZABLE_FIELDS[number]

/** Minimum measurements for non-sparse archive */
const MIN_MEASUREMENTS_FOR_NON_SPARSE = 3

/**
 * Dev Order 69: Validate an archive is structurally valid for correlation
 *
 * Invalid if:
 *   - Wrong schema version
 *   - Missing required archive ID
 *   - Malformed measurements array (not an array or sections missing)
 */
export function isValidArchiveForCorrelation(archive: unknown): archive is MeasurementArchiveRecord {
  if (!archive || typeof archive !== 'object') return false
  const a = archive as Record<string, unknown>

  // Required archiveId
  if (typeof a.archiveId !== 'string' || !a.archiveId) return false

  // Must be measurement-archive kind
  if (a.kind !== 'measurement-archive') return false

  // Schema version check
  const metadata = a.metadata as Record<string, unknown> | undefined
  if (!metadata || metadata.schemaVersion !== 'measurement-archive.v1') return false

  // Sections must be array
  if (!Array.isArray(a.sections)) return false

  // Each section must have measurements array
  for (const section of a.sections) {
    if (!section || typeof section !== 'object') return false
    if (!Array.isArray((section as Record<string, unknown>).measurements)) return false
  }

  return true
}

/**
 * Dev Order 69: Check if an archive is sparse (fewer than MIN_MEASUREMENTS_FOR_NON_SPARSE measurements)
 */
export function isSparseArchive(archive: MeasurementArchiveRecord): boolean {
  let count = 0
  for (const section of archive.sections) {
    count += section.measurements.length
    if (count >= MIN_MEASUREMENTS_FOR_NON_SPARSE) return false
  }
  return count < MIN_MEASUREMENTS_FOR_NON_SPARSE
}

/**
 * Dev Order 69: Filter archives to only valid, non-sparse records
 *
 * Returns tuple of [validArchives, warnings]
 */
export function filterCorrelatableArchives(
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
      warnings.push(`Archive '${archive.archiveId}' is sparse (fewer than ${MIN_MEASUREMENTS_FOR_NON_SPARSE} measurements)`)
    }
    valid.push(archive)
  }

  return { valid, warnings }
}

/**
 * Dev Order 69: Deduplicate archives by archiveId to prevent inflated counts
 */
export function deduplicateArchives(
  archives: MeasurementArchiveRecord[]
): MeasurementArchiveRecord[] {
  const seen = new Set<string>()
  const result: MeasurementArchiveRecord[] = []

  for (const archive of archives) {
    if (!seen.has(archive.archiveId)) {
      seen.add(archive.archiveId)
      result.push(archive)
    }
  }

  return result
}

/**
 * Generate a unique correlation ID
 */
export function generateCorrelationId(): string {
  const timestamp = Date.now().toString(36)
  const random = Math.random().toString(36).substring(2, 6)
  return `corr-${timestamp}-${random}`
}

/**
 * Determine confidence band based on sample count
 *
 * Dev Order 69 thresholds:
 *   low = 3 archives
 *   limited = 4–5 archives
 *   emerging = 6+ archives
 */
export function determineConfidenceBand(sampleCount: number): CorrelationConfidenceBand {
  if (sampleCount >= 6) return 'emerging'
  if (sampleCount >= 4) return 'limited'
  return 'low'
}

/**
 * Extract numeric values for a field from archive measurements
 */
function extractFieldValues(
  archives: MeasurementArchiveRecord[],
  field: string
): number[] {
  const values: number[] = []

  for (const archive of archives) {
    for (const section of archive.sections) {
      for (const measurement of section.measurements) {
        if (measurement.property === field && typeof measurement.value === 'number') {
          values.push(measurement.value)
        }
      }
    }
  }

  return values
}

/**
 * Compute basic statistics for a set of values
 */
function computeStats(values: number[]): {
  mean: number
  stdDev: number
  min: number
  max: number
  range: number
} | null {
  if (values.length === 0) return null

  const mean = values.reduce((a, b) => a + b, 0) / values.length
  const squaredDiffs = values.map(v => Math.pow(v - mean, 2))
  const variance = squaredDiffs.reduce((a, b) => a + b, 0) / values.length
  const stdDev = Math.sqrt(variance)
  const min = Math.min(...values)
  const max = Math.max(...values)

  return { mean, stdDev, min, max, range: max - min }
}

/**
 * Detect pattern tendency from values relative to a baseline
 */
function detectTendency(
  values: number[],
  baselineMean: number
): 'higher' | 'lower' | 'shifted' | 'variable' | null {
  if (values.length === 0) return null

  const stats = computeStats(values)
  if (!stats) return null

  const meanDiff = stats.mean - baselineMean
  const threshold = baselineMean * 0.05 // 5% threshold

  // High variance = variable
  const cv = stats.stdDev / stats.mean // coefficient of variation
  if (cv > 0.15) return 'variable'

  if (meanDiff > threshold) return 'higher'
  if (meanDiff < -threshold) return 'lower'
  if (Math.abs(meanDiff) > threshold * 0.5) return 'shifted'

  return null
}

/**
 * Generate observational narrative for a correlation
 * Uses only allowed language: correlates with, observed alongside, appears with, repeatedly observed
 */
function generateCorrelationNarrative(
  variantTitle: string,
  field: string,
  pattern: string,
  sampleCount: number,
  confidenceBand: CorrelationConfidenceBand
): string {
  const fieldLabel = getFieldDisplayLabel(field)
  const confidenceQualifier = getConfidenceQualifier(confidenceBand)

  if (pattern === 'higher') {
    return `${variantTitle} ${confidenceQualifier} correlates with higher ${fieldLabel} values (observed across ${sampleCount} archives).`
  }
  if (pattern === 'lower') {
    return `${variantTitle} ${confidenceQualifier} correlates with lower ${fieldLabel} values (observed across ${sampleCount} archives).`
  }
  if (pattern === 'shifted') {
    return `${variantTitle} appears with shifted ${fieldLabel} distribution (observed alongside ${sampleCount} archives).`
  }
  if (pattern === 'variable') {
    return `${variantTitle} correlates with variable ${fieldLabel} behavior (repeatedly observed across ${sampleCount} archives).`
  }

  return `${variantTitle} observed alongside ${fieldLabel} measurements in ${sampleCount} archives.`
}

/**
 * Get human-readable field label
 */
function getFieldDisplayLabel(field: string): string {
  const labels: Record<string, string> = {
    measuredHelmholtzHz: 'Helmholtz frequency',
    measuredPeakHz: 'peak frequency',
    measuredDampingFactor: 'damping factor',
    measuredQ: 'Q factor',
  }
  return labels[field] ?? field
}

/**
 * Get confidence qualifier for narrative
 */
function getConfidenceQualifier(band: CorrelationConfidenceBand): string {
  switch (band) {
    case 'emerging':
      return 'repeatedly'
    case 'limited':
      return 'tentatively'
    default:
      return 'preliminarily'
  }
}

/**
 * Compute correlations for a single variant across its archives
 */
function computeVariantCorrelations(
  variantId: string,
  variantTitle: string,
  archives: MeasurementArchiveRecord[],
  allArchives: MeasurementArchiveRecord[]
): ExperimentalCorrelation[] {
  const correlations: ExperimentalCorrelation[] = []

  if (archives.length < MIN_SAMPLE_SIZE) {
    return correlations
  }

  const confidenceBand = determineConfidenceBand(archives.length)

  // Compute baseline from all archives
  for (const field of ANALYZABLE_FIELDS) {
    const variantValues = extractFieldValues(archives, field)
    const allValues = extractFieldValues(allArchives, field)

    if (variantValues.length < MIN_SAMPLE_SIZE || allValues.length === 0) {
      continue
    }

    const allStats = computeStats(allValues)
    if (!allStats) continue

    const tendency = detectTendency(variantValues, allStats.mean)
    if (!tendency) continue

    const narrative = generateCorrelationNarrative(
      variantTitle,
      field,
      tendency,
      archives.length,
      confidenceBand
    )

    correlations.push({
      correlationId: generateCorrelationId(),
      sourceVariantId: variantId,
      archiveIds: archives.map(a => a.archiveId),
      observedField: field,
      observedPattern: tendency,
      sampleCount: archives.length,
      confidenceBand,
      narrative,
      computedAtIso: new Date().toISOString(),
    })
  }

  return correlations
}

/**
 * Compute all correlations from archives and variants
 *
 * Groups archives by topology variant, analyzes residual patterns,
 * and generates observational correlation records.
 *
 * Dev Order 69: Filters invalid archives, deduplicates by ID,
 * and handles sparse data safely.
 */
export function computeCorrelations(
  archives: MeasurementArchiveRecord[],
  variants: TopologyVariant[]
): CorrelationComputeResult {
  const correlations: ExperimentalCorrelation[] = []
  const insufficientVariants: string[] = []

  // Dev Order 69: Deduplicate to prevent inflated counts
  const dedupedArchives = deduplicateArchives(archives)

  // Dev Order 69: Filter to valid archives only (invalid ones are silently skipped)
  const { valid: validArchives } = filterCorrelatableArchives(dedupedArchives)

  // Group archives by variant
  const archivesByVariant = groupArchivesByTopologyVariant(validArchives)

  // Process each variant group
  for (const [variantId, variantArchives] of archivesByVariant) {
    // Skip the __none__ group (archives without variant refs)
    if (variantId === '__none__') continue

    const variant = variants.find(v => v.variantId === variantId)
    const variantTitle = variant?.title ?? variantId

    if (variantArchives.length < MIN_SAMPLE_SIZE) {
      insufficientVariants.push(variantId)
      continue
    }

    const variantCorrelations = computeVariantCorrelations(
      variantId,
      variantTitle,
      variantArchives,
      validArchives
    )

    correlations.push(...variantCorrelations)
  }

  return {
    correlations,
    insufficientVariants,
    totalArchivesAnalyzed: validArchives.length,
    computedAtIso: new Date().toISOString(),
  }
}

/**
 * Create summary of correlations for a variant
 */
export function createVariantCorrelationSummary(
  variantId: string,
  variantTitle: string,
  correlations: ExperimentalCorrelation[]
): VariantCorrelationSummary {
  const variantCorrelations = correlations.filter(c => c.sourceVariantId === variantId)

  if (variantCorrelations.length === 0) {
    return {
      variantId,
      variantTitle,
      correlationCount: 0,
      archiveCount: 0,
      confidenceBand: 'low',
    }
  }

  // Find dominant pattern (most common observed pattern)
  const patternCounts = new Map<string, number>()
  for (const c of variantCorrelations) {
    const count = patternCounts.get(c.observedPattern) ?? 0
    patternCounts.set(c.observedPattern, count + 1)
  }

  let dominantPattern: string | undefined
  let maxCount = 0
  for (const [pattern, count] of patternCounts) {
    if (count > maxCount) {
      maxCount = count
      dominantPattern = pattern
    }
  }

  // Use highest confidence band from correlations
  const bands: CorrelationConfidenceBand[] = variantCorrelations.map(c => c.confidenceBand)
  const highestBand = bands.includes('emerging') ? 'emerging' :
    bands.includes('limited') ? 'limited' : 'low'

  // Get unique archive count
  const archiveIds = new Set<string>()
  for (const c of variantCorrelations) {
    for (const id of c.archiveIds) {
      archiveIds.add(id)
    }
  }

  return {
    variantId,
    variantTitle,
    correlationCount: variantCorrelations.length,
    archiveCount: archiveIds.size,
    dominantPattern,
    confidenceBand: highestBand,
  }
}

/**
 * Get all variant summaries from correlations
 */
export function getAllVariantCorrelationSummaries(
  correlations: ExperimentalCorrelation[],
  variants: TopologyVariant[]
): VariantCorrelationSummary[] {
  const summaries: VariantCorrelationSummary[] = []

  // Get unique variant IDs from correlations
  const variantIds = new Set(
    correlations
      .map(c => c.sourceVariantId)
      .filter((id): id is string => id !== undefined)
  )

  for (const variantId of variantIds) {
    const variant = variants.find(v => v.variantId === variantId)
    const summary = createVariantCorrelationSummary(
      variantId,
      variant?.title ?? variantId,
      correlations
    )
    summaries.push(summary)
  }

  // Sort by correlation count descending
  return summaries.sort((a, b) => b.correlationCount - a.correlationCount)
}

/**
 * Check if we have sufficient data for correlations
 *
 * Dev Order 69: Uses deduplication and validation before checking
 */
export function hasSufficientDataForCorrelations(
  archives: MeasurementArchiveRecord[]
): boolean {
  // Dev Order 69: Deduplicate and filter
  const dedupedArchives = deduplicateArchives(archives)
  const { valid: validArchives } = filterCorrelatableArchives(dedupedArchives)

  const archivesByVariant = groupArchivesByTopologyVariant(validArchives)

  for (const [variantId, variantArchives] of archivesByVariant) {
    if (variantId !== '__none__' && variantArchives.length >= MIN_SAMPLE_SIZE) {
      return true
    }
  }

  return false
}

/**
 * Get the minimum sample size constant
 */
export function getMinSampleSize(): number {
  return MIN_SAMPLE_SIZE
}

/**
 * Format confidence band for display
 */
export function formatConfidenceBand(band: CorrelationConfidenceBand): string {
  switch (band) {
    case 'emerging':
      return 'Emerging'
    case 'limited':
      return 'Limited'
    default:
      return 'Low'
  }
}

/**
 * Get gate level for confidence band
 */
export function getConfidenceBandGate(band: CorrelationConfidenceBand): 'green' | 'yellow' | 'red' {
  switch (band) {
    case 'emerging':
      return 'green'
    case 'limited':
      return 'yellow'
    default:
      return 'red'
  }
}
