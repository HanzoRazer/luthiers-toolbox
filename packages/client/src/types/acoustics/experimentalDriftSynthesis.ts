/**
 * Experimental Drift Synthesis Types
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

import type { DriftDirection } from './experimentalDrift'

/**
 * Extended direction type for synthesis
 * "mixed" indicates multiple drift records with conflicting directions
 */
export type SynthesisDominantDirection = DriftDirection | 'mixed'

/**
 * Classification of a drift pattern observation
 */
export interface DriftPatternClassification {
  /** Field being tracked */
  field: string

  /** Observed direction */
  direction: DriftDirection

  /** Number of drift records showing this pattern */
  occurrences: number

  /** Prose description of the pattern */
  description: string
}

/**
 * Observation about drift behavior within a session
 */
export interface SessionDriftObservation {
  /** Session context identifier */
  sessionContext: string

  /** Number of drift records in this session */
  driftRecordCount: number

  /** Number of unique archives */
  archiveCount: number

  /** Dominant direction across records */
  dominantDirection: SynthesisDominantDirection

  /** Pattern descriptions */
  patterns: string[]
}

/**
 * Observation about drift behavior within a topology variant
 */
export interface VariantDriftObservation {
  /** Topology variant identifier */
  variantId: string

  /** Number of drift records for this variant */
  driftRecordCount: number

  /** Number of unique archives */
  archiveCount: number

  /** Dominant direction across records */
  dominantDirection: SynthesisDominantDirection

  /** Pattern descriptions */
  patterns: string[]
}

/**
 * Core experimental drift synthesis record
 *
 * Represents aggregate observational summary across multiple drift records.
 */
export interface ExperimentalDriftSynthesis {
  /** Unique synthesis identifier (prefix: drift-synthesis-) */
  synthesisId: string

  /** Session context if synthesis is session-scoped */
  sessionContext?: string

  /** Topology variant ID if synthesis is variant-scoped */
  topologyVariantId?: string

  /** Total archives contributing to this synthesis */
  archiveCount: number

  /** Total drift records analyzed */
  driftRecordCount: number

  /** Dominant patterns observed (prose descriptions) */
  dominantPatterns: string[]

  /** Overall dominant direction */
  dominantDirection: SynthesisDominantDirection

  /** Human-readable narrative describing the synthesis */
  narrative: string

  /** ISO timestamp when synthesis was computed */
  computedAtIso: string
}

/**
 * Summary of drift synthesis observations
 */
export interface ExperimentalDriftSynthesisSummary {
  /** Overall synthesis (if sufficient data) */
  overallSynthesis?: ExperimentalDriftSynthesis

  /** Per-session observations */
  sessionObservations: SessionDriftObservation[]

  /** Per-variant observations */
  variantObservations: VariantDriftObservation[]

  /** Sessions with insufficient data (<3 drift records) */
  insufficientSessions: string[]

  /** Variants with insufficient data (<3 drift records) */
  insufficientVariants: string[]
}

/**
 * Result of computing drift synthesis
 */
export interface DriftSynthesisResult {
  /** Main synthesis summary */
  summary: ExperimentalDriftSynthesisSummary

  /** Total drift records provided */
  totalDriftRecordsProvided: number

  /** Total drift records analyzed (after filtering) */
  totalDriftRecordsAnalyzed: number

  /** Warnings from processing */
  warnings: string[]

  /** ISO timestamp when synthesis was computed */
  computedAtIso: string
}
