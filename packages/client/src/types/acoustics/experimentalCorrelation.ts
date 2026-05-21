/**
 * Experimental Correlation Types
 *
 * Dev Order 68: Experimental correlation workspace
 *
 * Correlations are computed observations about patterns between
 * topology variants and residual behavior across multiple archives.
 *
 * OBSERVATIONAL ONLY:
 * - Correlation does NOT imply causation
 * - No optimization, recommendation, or validation semantics
 * - No authority claims about acoustic behavior
 *
 * Schema: experimental-correlation.v1
 * Storage: in-memory only (no persistence backend)
 */

/**
 * Confidence band for correlation strength
 * Based on sample count and consistency
 */
export type CorrelationConfidenceBand = 'low' | 'limited' | 'emerging'

/**
 * Core experimental correlation record
 *
 * Represents an observed pattern between a topology variant
 * (or session context) and residual behavior across archives.
 */
export interface ExperimentalCorrelation {
  /** Unique correlation identifier */
  correlationId: string

  /** Source topology variant ID (if variant-based correlation) */
  sourceVariantId?: string

  /** Source session context (if session-based correlation) */
  sourceSessionId?: string

  /** Archive IDs that contribute to this correlation */
  archiveIds: string[]

  /** The measurement field where the pattern was observed */
  observedField: string

  /** Human-readable pattern description (e.g., "higher values", "shifted peak") */
  observedPattern: string

  /** Number of archives in the sample */
  sampleCount: number

  /** Confidence band based on sample size and consistency */
  confidenceBand: CorrelationConfidenceBand

  /** Human-readable narrative describing the correlation */
  narrative: string

  /** ISO timestamp when correlation was computed */
  computedAtIso: string
}

/**
 * Summary of correlations for a variant
 */
export interface VariantCorrelationSummary {
  variantId: string
  variantTitle: string
  correlationCount: number
  archiveCount: number
  dominantPattern?: string
  confidenceBand: CorrelationConfidenceBand
}

/**
 * Result of computing correlations from archives
 */
export interface CorrelationComputeResult {
  correlations: ExperimentalCorrelation[]
  insufficientVariants: string[]
  totalArchivesAnalyzed: number
  computedAtIso: string
}
