/**
 * Experimental Drift Synthesis Utilities
 *
 * Dev Order 72: Session-level drift synthesis
 *
 * Synthesis summarizes repeated observational patterns across multiple
 * drift records. It is aggregate observational context — not conclusions,
 * proofs, or recommendations.
 *
 * OBSERVATIONAL ONLY:
 * - Synthesis does NOT imply improvement or optimization
 * - No causal inference
 * - No predictive modeling
 * - No recommendation authority
 *
 * Allowed language: observed, repeatedly observed, shifted, diverged, stable, variable, mixed
 * Forbidden language: improved, optimized, better, fixed, recommended, validated, corrected, best
 *
 * Schema: experimental-drift-synthesis.v1
 * Storage: in-memory only (no persistence backend)
 */

import type { ExperimentalDriftRecord, DriftDirection } from '../../types/acoustics/experimentalDrift'
import type {
  SynthesisDominantDirection,
  DriftPatternClassification,
  SessionDriftObservation,
  VariantDriftObservation,
  ExperimentalDriftSynthesis,
  ExperimentalDriftSynthesisSummary,
  DriftSynthesisResult,
} from '../../types/acoustics/experimentalDriftSynthesis'

/** Minimum drift records required for synthesis */
export const MINIMUM_SYNTHESIS_RECORDS = 3

/**
 * Check if drift records have sufficient data for synthesis
 */
export function hasSufficientDriftSynthesisData(
  driftRecords: ExperimentalDriftRecord[]
): boolean {
  return driftRecords.length >= MINIMUM_SYNTHESIS_RECORDS
}

/**
 * Generate synthesis ID
 */
function generateSynthesisId(): string {
  const now = new Date()
  const timestamp = now.toISOString().replace(/[-:T]/g, '').slice(0, 14)
  return `drift-synthesis-${timestamp}`
}

/**
 * Deduplicate drift records by driftId
 */
export function deduplicateDriftRecords(
  records: ExperimentalDriftRecord[]
): ExperimentalDriftRecord[] {
  const seen = new Set<string>()
  const result: ExperimentalDriftRecord[] = []

  for (const record of records) {
    if (!seen.has(record.driftId)) {
      seen.add(record.driftId)
      result.push(record)
    }
  }

  return result
}

/**
 * Validate a drift record is structurally valid
 */
export function isValidDriftRecord(record: unknown): record is ExperimentalDriftRecord {
  if (!record || typeof record !== 'object') return false
  const r = record as Record<string, unknown>

  if (typeof r.driftId !== 'string' || !r.driftId) return false
  if (typeof r.observedField !== 'string') return false
  if (typeof r.direction !== 'string') return false
  if (typeof r.sampleCount !== 'number') return false
  if (!Array.isArray(r.archiveIds)) return false

  return true
}

/**
 * Filter valid drift records
 */
export function filterValidDriftRecords(
  records: ExperimentalDriftRecord[]
): { valid: ExperimentalDriftRecord[]; warnings: string[] } {
  const valid: ExperimentalDriftRecord[] = []
  const warnings: string[] = []

  for (const record of records) {
    if (!isValidDriftRecord(record)) {
      warnings.push('Drift record skipped: invalid structure')
      continue
    }
    valid.push(record)
  }

  return { valid, warnings }
}

/**
 * Group drift records by session context
 */
export function groupDriftRecordsBySession(
  records: ExperimentalDriftRecord[]
): Map<string, ExperimentalDriftRecord[]> {
  const groups = new Map<string, ExperimentalDriftRecord[]>()

  for (const record of records) {
    // Use contextId if available, otherwise check timelinePoints for sessionContext
    let sessionContext = '__none__'

    if (record.contextType === 'session' && record.contextId) {
      sessionContext = record.contextId
    } else if (record.timelinePoints.length > 0) {
      const firstPoint = record.timelinePoints[0]
      if (firstPoint.sessionContext) {
        sessionContext = firstPoint.sessionContext
      }
    }

    const existing = groups.get(sessionContext) ?? []
    existing.push(record)
    groups.set(sessionContext, existing)
  }

  return groups
}

/**
 * Group drift records by topology variant
 */
export function groupDriftRecordsByVariant(
  records: ExperimentalDriftRecord[]
): Map<string, ExperimentalDriftRecord[]> {
  const groups = new Map<string, ExperimentalDriftRecord[]>()

  for (const record of records) {
    let variantId = '__none__'

    if (record.contextType === 'variant' && record.contextId) {
      variantId = record.contextId
    } else if (record.timelinePoints.length > 0) {
      const firstPoint = record.timelinePoints[0]
      if (firstPoint.variantId) {
        variantId = firstPoint.variantId
      }
    }

    const existing = groups.get(variantId) ?? []
    existing.push(record)
    groups.set(variantId, existing)
  }

  return groups
}

/**
 * Classify dominant direction from multiple drift records
 * "mixed" indicates conflicting directions
 */
export function classifyDominantDriftDirection(
  records: ExperimentalDriftRecord[]
): SynthesisDominantDirection {
  if (records.length === 0) return 'stable'

  const counts: Record<DriftDirection, number> = {
    upward: 0,
    downward: 0,
    stable: 0,
    variable: 0,
  }

  for (const record of records) {
    counts[record.direction]++
  }

  const total = records.length
  const maxCount = Math.max(counts.upward, counts.downward, counts.stable, counts.variable)

  // If no clear majority (less than 50%), classify as mixed
  if (maxCount < total / 2) {
    return 'mixed'
  }

  if (counts.upward === maxCount) return 'upward'
  if (counts.downward === maxCount) return 'downward'
  if (counts.stable === maxCount) return 'stable'
  return 'variable'
}

/**
 * Build prose description for a drift pattern
 */
function buildPatternDescription(
  field: string,
  direction: DriftDirection,
  occurrences: number
): string {
  const fieldName = field.replace('measured', '').replace(/Hz$/, '')

  switch (direction) {
    case 'upward':
      return occurrences > 1
        ? `repeated upward ${fieldName} drift`
        : `upward ${fieldName} drift`
    case 'downward':
      return occurrences > 1
        ? `repeated downward ${fieldName} drift`
        : `downward ${fieldName} drift`
    case 'stable':
      return `stable ${fieldName} behavior`
    case 'variable':
      return `variable ${fieldName} movement`
    default:
      return `observed ${fieldName} drift`
  }
}

/**
 * Summarize drift patterns from records
 */
export function summarizeDriftPatterns(
  records: ExperimentalDriftRecord[]
): DriftPatternClassification[] {
  const fieldDirectionCounts = new Map<string, Map<DriftDirection, number>>()

  for (const record of records) {
    const field = record.observedField
    const direction = record.direction

    if (!fieldDirectionCounts.has(field)) {
      fieldDirectionCounts.set(field, new Map())
    }

    const directionMap = fieldDirectionCounts.get(field)!
    directionMap.set(direction, (directionMap.get(direction) ?? 0) + 1)
  }

  const patterns: DriftPatternClassification[] = []

  for (const [field, directionMap] of fieldDirectionCounts) {
    // Find dominant direction for this field
    let maxDirection: DriftDirection = 'stable'
    let maxCount = 0

    for (const [direction, count] of directionMap) {
      if (count > maxCount) {
        maxCount = count
        maxDirection = direction
      }
    }

    patterns.push({
      field,
      direction: maxDirection,
      occurrences: maxCount,
      description: buildPatternDescription(field, maxDirection, maxCount),
    })
  }

  // Sort by occurrences descending
  patterns.sort((a, b) => b.occurrences - a.occurrences)

  return patterns
}

/**
 * Extract dominant pattern descriptions
 */
function extractDominantPatterns(
  patterns: DriftPatternClassification[]
): string[] {
  // Take top patterns (those with multiple occurrences or top 3)
  const dominant = patterns
    .filter((p) => p.occurrences >= 2)
    .slice(0, 5)
    .map((p) => p.description)

  if (dominant.length === 0 && patterns.length > 0) {
    return patterns.slice(0, 3).map((p) => p.description)
  }

  return dominant
}

/**
 * Count unique archives from drift records
 */
function countUniqueArchives(records: ExperimentalDriftRecord[]): number {
  const archiveIds = new Set<string>()

  for (const record of records) {
    for (const id of record.archiveIds) {
      archiveIds.add(id)
    }
  }

  return archiveIds.size
}

/**
 * Build synthesis narrative
 * Uses observational-only language
 */
export function buildDriftSynthesisNarrative(
  dominantDirection: SynthesisDominantDirection,
  patterns: string[],
  recordCount: number,
  archiveCount: number,
  contextLabel?: string
): string {
  const contextPrefix = contextLabel ? `In ${contextLabel}, ` : ''

  if (patterns.length === 0) {
    return `${contextPrefix}${recordCount} drift observations across ${archiveCount} archives showed ${dominantDirection} overall behavior.`
  }

  const patternSummary = patterns.slice(0, 3).join(', ')

  switch (dominantDirection) {
    case 'upward':
      return `${contextPrefix}drift observations showed predominantly upward shifts. Patterns observed: ${patternSummary}.`
    case 'downward':
      return `${contextPrefix}drift observations showed predominantly downward shifts. Patterns observed: ${patternSummary}.`
    case 'stable':
      return `${contextPrefix}drift observations remained relatively stable. Patterns observed: ${patternSummary}.`
    case 'variable':
      return `${contextPrefix}drift observations showed variable behavior. Patterns observed: ${patternSummary}.`
    case 'mixed':
      return `${contextPrefix}drift observations showed mixed directional behavior across fields. Patterns observed: ${patternSummary}.`
    default:
      return `${contextPrefix}${recordCount} drift observations across ${archiveCount} archives. Patterns observed: ${patternSummary}.`
  }
}

/**
 * Build synthesis for a group of drift records
 */
function buildSynthesisForGroup(
  records: ExperimentalDriftRecord[],
  contextType?: 'session' | 'variant',
  contextId?: string
): ExperimentalDriftSynthesis {
  const patterns = summarizeDriftPatterns(records)
  const dominantPatterns = extractDominantPatterns(patterns)
  const dominantDirection = classifyDominantDriftDirection(records)
  const archiveCount = countUniqueArchives(records)

  const contextLabel = contextId && contextId !== '__none__' ? contextId : undefined

  return {
    synthesisId: generateSynthesisId(),
    sessionContext: contextType === 'session' ? contextId : undefined,
    topologyVariantId: contextType === 'variant' ? contextId : undefined,
    archiveCount,
    driftRecordCount: records.length,
    dominantPatterns,
    dominantDirection,
    narrative: buildDriftSynthesisNarrative(
      dominantDirection,
      dominantPatterns,
      records.length,
      archiveCount,
      contextLabel
    ),
    computedAtIso: new Date().toISOString(),
  }
}

/**
 * Build session observation from drift records
 */
function buildSessionObservation(
  sessionContext: string,
  records: ExperimentalDriftRecord[]
): SessionDriftObservation {
  const patterns = summarizeDriftPatterns(records)
  const dominantPatterns = extractDominantPatterns(patterns)

  return {
    sessionContext,
    driftRecordCount: records.length,
    archiveCount: countUniqueArchives(records),
    dominantDirection: classifyDominantDriftDirection(records),
    patterns: dominantPatterns,
  }
}

/**
 * Build variant observation from drift records
 */
function buildVariantObservation(
  variantId: string,
  records: ExperimentalDriftRecord[]
): VariantDriftObservation {
  const patterns = summarizeDriftPatterns(records)
  const dominantPatterns = extractDominantPatterns(patterns)

  return {
    variantId,
    driftRecordCount: records.length,
    archiveCount: countUniqueArchives(records),
    dominantDirection: classifyDominantDriftDirection(records),
    patterns: dominantPatterns,
  }
}

/**
 * Compute experimental drift synthesis
 *
 * Main entry point. Analyzes drift records to produce session-level
 * and variant-level synthesis summaries.
 *
 * Does not mutate input array.
 */
export function computeExperimentalDriftSynthesis(
  driftRecords: ExperimentalDriftRecord[]
): DriftSynthesisResult {
  const totalProvided = driftRecords.length

  // Deduplicate and filter
  const deduplicated = deduplicateDriftRecords(driftRecords)
  const { valid, warnings } = filterValidDriftRecords(deduplicated)

  const sessionObservations: SessionDriftObservation[] = []
  const variantObservations: VariantDriftObservation[] = []
  const insufficientSessions: string[] = []
  const insufficientVariants: string[] = []

  // Overall synthesis (if sufficient data)
  let overallSynthesis: ExperimentalDriftSynthesis | undefined

  if (valid.length >= MINIMUM_SYNTHESIS_RECORDS) {
    overallSynthesis = buildSynthesisForGroup(valid)
  }

  // Session grouping
  const sessionGroups = groupDriftRecordsBySession(valid)
  for (const [sessionContext, records] of sessionGroups) {
    if (records.length >= MINIMUM_SYNTHESIS_RECORDS) {
      sessionObservations.push(buildSessionObservation(sessionContext, records))
    } else {
      insufficientSessions.push(sessionContext)
    }
  }

  // Variant grouping
  const variantGroups = groupDriftRecordsByVariant(valid)
  for (const [variantId, records] of variantGroups) {
    if (records.length >= MINIMUM_SYNTHESIS_RECORDS) {
      variantObservations.push(buildVariantObservation(variantId, records))
    } else {
      insufficientVariants.push(variantId)
    }
  }

  return {
    summary: {
      overallSynthesis,
      sessionObservations,
      variantObservations,
      insufficientSessions,
      insufficientVariants,
    },
    totalDriftRecordsProvided: totalProvided,
    totalDriftRecordsAnalyzed: valid.length,
    warnings,
    computedAtIso: new Date().toISOString(),
  }
}

/**
 * Get synthesis for a specific session
 */
export function getSynthesisForSession(
  result: DriftSynthesisResult,
  sessionContext: string
): SessionDriftObservation | undefined {
  return result.summary.sessionObservations.find(
    (obs) => obs.sessionContext === sessionContext
  )
}

/**
 * Get synthesis for a specific variant
 */
export function getSynthesisForVariant(
  result: DriftSynthesisResult,
  variantId: string
): VariantDriftObservation | undefined {
  return result.summary.variantObservations.find(
    (obs) => obs.variantId === variantId
  )
}
