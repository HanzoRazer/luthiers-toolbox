/**
 * Evidence Review Types
 *
 * Dev Order 76: Measurement Lab evidence review workspace
 *
 * Reviews are observational workflow annotations that allow experimental
 * records to be grouped, inspected, flagged, and comparatively reviewed.
 *
 * OBSERVATIONAL ONLY:
 * - Reviews do NOT establish authority
 * - Reviews do NOT validate or approve
 * - Reviews do NOT canonize or certify
 * - Reviews do NOT imply production-readiness
 *
 * Allowed states: reviewed, flagged, needs-followup, repeat-observed
 * Forbidden states: approved, validated, accepted, canonical, certified, verified
 *
 * Schema: evidence-review.v1
 * Storage: in-memory only (no persistence backend)
 */

/**
 * Target types that reviews can attach to
 */
export type EvidenceReviewTargetType =
  | 'archive'
  | 'topologyVariant'
  | 'correlation'
  | 'driftRecord'
  | 'driftSynthesis'

/**
 * Observational review states
 *
 * These describe workflow status, not approval or validation.
 */
export type EvidenceReviewState =
  | 'reviewed'
  | 'flagged'
  | 'needs-followup'
  | 'repeat-observed'

/**
 * Target reference for a review
 */
export interface EvidenceReviewTarget {
  /** Type of the target record */
  targetType: EvidenceReviewTargetType

  /** ID of the target record */
  targetId: string
}

/**
 * Core evidence review record
 *
 * Represents an observational workflow annotation attached to
 * a Measurement Lab record.
 */
export interface EvidenceReviewRecord {
  /** Unique review identifier */
  reviewId: string

  /** Type of the target record */
  targetType: EvidenceReviewTargetType

  /** ID of the target record */
  targetId: string

  /** Observational review state */
  reviewState: EvidenceReviewState

  /** Optional review notes */
  notes?: string

  /** Optional tags for categorization */
  tags?: string[]

  /** ISO timestamp when review was created */
  createdAt: string
}

/**
 * Review flag for quick filtering
 */
export interface EvidenceReviewFlag {
  /** Review state */
  state: EvidenceReviewState

  /** Human-readable label */
  label: string
}

/**
 * Summary of reviews for a target type or state
 */
export interface EvidenceReviewSummary {
  /** Grouping key (target type or review state) */
  groupKey: string

  /** Human-readable group label */
  groupLabel: string

  /** Number of reviews in this group */
  reviewCount: number

  /** Unique target IDs with reviews */
  targetIds: string[]
}
