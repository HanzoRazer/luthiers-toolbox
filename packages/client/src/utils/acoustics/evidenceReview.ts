/**
 * Evidence Review Utilities
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

import type {
  EvidenceReviewRecord,
  EvidenceReviewTargetType,
  EvidenceReviewState,
  EvidenceReviewSummary,
} from '../../types/acoustics/evidenceReview'

/** Valid target types for evidence reviews */
export const VALID_REVIEW_TARGET_TYPES: EvidenceReviewTargetType[] = [
  'archive',
  'topologyVariant',
  'correlation',
  'driftRecord',
  'driftSynthesis',
]

/** Valid observational review states */
export const VALID_REVIEW_STATES: EvidenceReviewState[] = [
  'reviewed',
  'flagged',
  'needs-followup',
  'repeat-observed',
]

/** Forbidden review states (approval/authority semantics) */
export const FORBIDDEN_REVIEW_STATES = [
  'approved',
  'validated',
  'accepted',
  'canonical',
  'production-ready',
  'certified',
  'verified',
  'correct',
  'optimal',
]

/**
 * Generate a unique review ID
 */
function generateReviewId(): string {
  return `review-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

/**
 * Check if a target type is valid
 */
export function isValidReviewTargetType(
  targetType: string
): targetType is EvidenceReviewTargetType {
  return VALID_REVIEW_TARGET_TYPES.includes(targetType as EvidenceReviewTargetType)
}

/**
 * Check if a review state is valid
 */
export function isValidReviewState(state: string): state is EvidenceReviewState {
  return VALID_REVIEW_STATES.includes(state as EvidenceReviewState)
}

/**
 * Check if a review state is forbidden
 */
export function isForbiddenReviewState(state: string): boolean {
  return FORBIDDEN_REVIEW_STATES.includes(state.toLowerCase())
}

/**
 * Normalize tags from comma-separated input or array
 * Trims whitespace, removes empty tags, deduplicates
 */
export function normalizeReviewTags(input: string | string[]): string[] {
  if (!input) {
    return []
  }

  const rawTags = typeof input === 'string' ? input.split(',') : input

  const tags = rawTags.map((tag) => tag.trim()).filter((tag) => tag.length > 0)

  return [...new Set(tags)]
}

/**
 * Validate an evidence review
 * Returns error message if invalid, null if valid
 */
export function validateEvidenceReview(review: Partial<EvidenceReviewRecord>): string | null {
  if (!review.targetType) {
    return 'Target type is required'
  }

  if (!isValidReviewTargetType(review.targetType)) {
    return `Invalid target type: ${review.targetType}`
  }

  if (
    !review.targetId ||
    typeof review.targetId !== 'string' ||
    review.targetId.trim().length === 0
  ) {
    return 'Target ID is required'
  }

  if (!review.reviewState) {
    return 'Review state is required'
  }

  if (isForbiddenReviewState(review.reviewState)) {
    return `Forbidden review state: ${review.reviewState}`
  }

  if (!isValidReviewState(review.reviewState)) {
    return `Invalid review state: ${review.reviewState}`
  }

  return null
}

/**
 * Create an evidence review
 * Returns the review or throws if validation fails
 */
export function createEvidenceReview(params: {
  targetType: EvidenceReviewTargetType
  targetId: string
  reviewState: EvidenceReviewState
  notes?: string
  tags?: string
}): EvidenceReviewRecord {
  const trimmedTargetId = params.targetId.trim()
  const trimmedNotes = params.notes?.trim()

  const review: EvidenceReviewRecord = {
    reviewId: generateReviewId(),
    targetType: params.targetType,
    targetId: trimmedTargetId,
    reviewState: params.reviewState,
    createdAt: new Date().toISOString(),
  }

  if (trimmedNotes && trimmedNotes.length > 0) {
    review.notes = trimmedNotes
  }

  if (params.tags) {
    const normalizedTags = normalizeReviewTags(params.tags)
    if (normalizedTags.length > 0) {
      review.tags = normalizedTags
    }
  }

  const error = validateEvidenceReview(review)
  if (error) {
    throw new Error(error)
  }

  return review
}

/**
 * Normalize an evidence review (immutable)
 * Trims notes, normalizes tags, preserves all fields
 */
export function normalizeEvidenceReview(review: EvidenceReviewRecord): EvidenceReviewRecord {
  const normalized: EvidenceReviewRecord = {
    ...review,
    targetId: review.targetId.trim(),
  }

  if (review.notes) {
    const trimmed = review.notes.trim()
    if (trimmed.length > 0) {
      normalized.notes = trimmed
    } else {
      delete normalized.notes
    }
  }

  if (review.tags && review.tags.length > 0) {
    const deduped = normalizeReviewTags(review.tags)
    if (deduped.length > 0) {
      normalized.tags = deduped
    } else {
      delete normalized.tags
    }
  }

  return normalized
}

/**
 * Filter reviews by target type
 */
export function filterReviewsByTarget(
  reviews: EvidenceReviewRecord[],
  targetType: EvidenceReviewTargetType
): EvidenceReviewRecord[] {
  return reviews.filter((review) => review.targetType === targetType)
}

/**
 * Filter reviews by target ID
 */
export function filterReviewsByTargetId(
  reviews: EvidenceReviewRecord[],
  targetId: string
): EvidenceReviewRecord[] {
  return reviews.filter((review) => review.targetId === targetId)
}

/**
 * Filter reviews by review state
 */
export function filterReviewsByState(
  reviews: EvidenceReviewRecord[],
  state: EvidenceReviewState
): EvidenceReviewRecord[] {
  return reviews.filter((review) => review.reviewState === state)
}

/**
 * Summarize reviews by target type
 */
export function summarizeReviewsByTargetType(
  reviews: EvidenceReviewRecord[]
): EvidenceReviewSummary[] {
  const summaryMap = new Map<EvidenceReviewTargetType, Set<string>>()

  for (const review of reviews) {
    const existing = summaryMap.get(review.targetType) ?? new Set<string>()
    existing.add(review.targetId)
    summaryMap.set(review.targetType, existing)
  }

  const summaries: EvidenceReviewSummary[] = []

  for (const [targetType, targetIds] of summaryMap) {
    summaries.push({
      groupKey: targetType,
      groupLabel: getTargetTypeLabel(targetType),
      reviewCount: reviews.filter((r) => r.targetType === targetType).length,
      targetIds: [...targetIds],
    })
  }

  return summaries
}

/**
 * Summarize reviews by review state
 */
export function summarizeReviewsByState(
  reviews: EvidenceReviewRecord[]
): EvidenceReviewSummary[] {
  const summaryMap = new Map<EvidenceReviewState, Set<string>>()

  for (const review of reviews) {
    const existing = summaryMap.get(review.reviewState) ?? new Set<string>()
    existing.add(review.targetId)
    summaryMap.set(review.reviewState, existing)
  }

  const summaries: EvidenceReviewSummary[] = []

  for (const [state, targetIds] of summaryMap) {
    summaries.push({
      groupKey: state,
      groupLabel: getReviewStateLabel(state),
      reviewCount: reviews.filter((r) => r.reviewState === state).length,
      targetIds: [...targetIds],
    })
  }

  return summaries
}

/**
 * Deduplicate reviews by reviewId
 * Keeps first occurrence of each reviewId
 */
export function dedupeEvidenceReviews(reviews: EvidenceReviewRecord[]): EvidenceReviewRecord[] {
  const seen = new Set<string>()
  const result: EvidenceReviewRecord[] = []

  for (const review of reviews) {
    if (!seen.has(review.reviewId)) {
      seen.add(review.reviewId)
      result.push(review)
    }
  }

  return result
}

/**
 * Build a display label for a review
 * Format: "[state] targetType:targetId"
 */
export function buildEvidenceReviewLabel(review: EvidenceReviewRecord): string {
  return `[${review.reviewState}] ${review.targetType}:${review.targetId}`
}

/**
 * Get human-readable label for target type
 */
export function getTargetTypeLabel(targetType: EvidenceReviewTargetType): string {
  switch (targetType) {
    case 'archive':
      return 'Archive'
    case 'topologyVariant':
      return 'Topology Variant'
    case 'correlation':
      return 'Correlation'
    case 'driftRecord':
      return 'Drift Record'
    case 'driftSynthesis':
      return 'Drift Synthesis'
    default:
      return targetType
  }
}

/**
 * Get human-readable label for review state
 */
export function getReviewStateLabel(state: EvidenceReviewState): string {
  switch (state) {
    case 'reviewed':
      return 'Reviewed'
    case 'flagged':
      return 'Flagged'
    case 'needs-followup':
      return 'Needs Follow-up'
    case 'repeat-observed':
      return 'Repeat Observed'
    default:
      return state
  }
}
