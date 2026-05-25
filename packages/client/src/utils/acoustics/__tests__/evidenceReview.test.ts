/**
 * Evidence Review Tests
 *
 * Dev Order 76: Measurement Lab evidence review workspace
 *
 * Tests review creation, validation, filtering, and observational semantics.
 *
 * Required test cases:
 * 1. valid review creation
 * 2. invalid review state rejected
 * 3. forbidden review states rejected
 * 4. whitespace-only targetId rejected
 * 5. notes trimmed safely
 * 6. tags normalized/deduped
 * 7. immutable input preservation
 * 8. filter by state
 * 9. filter by target
 * 10. dedupe review IDs
 * 11. label generation stable
 * 12. forbidden language absent
 * 13. no approval/canonical semantics
 * 14. missing optional fields handled safely
 * 15. review summaries stable
 */

import { describe, it, expect } from 'vitest'
import type {
  EvidenceReviewRecord,
  EvidenceReviewTargetType,
  EvidenceReviewState,
} from '../../../types/acoustics/evidenceReview'
import {
  VALID_REVIEW_TARGET_TYPES,
  VALID_REVIEW_STATES,
  FORBIDDEN_REVIEW_STATES,
  isValidReviewTargetType,
  isValidReviewState,
  isForbiddenReviewState,
  normalizeReviewTags,
  validateEvidenceReview,
  createEvidenceReview,
  normalizeEvidenceReview,
  filterReviewsByTarget,
  filterReviewsByTargetId,
  filterReviewsByState,
  summarizeReviewsByTargetType,
  summarizeReviewsByState,
  dedupeEvidenceReviews,
  buildEvidenceReviewLabel,
  getTargetTypeLabel,
  getReviewStateLabel,
} from '../evidenceReview'

/**
 * Create a mock review for testing
 */
function createMockReview(
  id: string,
  overrides: Partial<EvidenceReviewRecord> = {}
): EvidenceReviewRecord {
  return {
    reviewId: id,
    targetType: 'archive',
    targetId: 'archive-001',
    reviewState: 'reviewed',
    createdAt: new Date().toISOString(),
    ...overrides,
  }
}

describe('evidenceReview', () => {
  describe('VALID_REVIEW_TARGET_TYPES', () => {
    it('should include all expected target types', () => {
      expect(VALID_REVIEW_TARGET_TYPES).toContain('archive')
      expect(VALID_REVIEW_TARGET_TYPES).toContain('topologyVariant')
      expect(VALID_REVIEW_TARGET_TYPES).toContain('correlation')
      expect(VALID_REVIEW_TARGET_TYPES).toContain('driftRecord')
      expect(VALID_REVIEW_TARGET_TYPES).toContain('driftSynthesis')
      expect(VALID_REVIEW_TARGET_TYPES.length).toBe(5)
    })
  })

  describe('VALID_REVIEW_STATES', () => {
    it('should include all observational review states', () => {
      expect(VALID_REVIEW_STATES).toContain('reviewed')
      expect(VALID_REVIEW_STATES).toContain('flagged')
      expect(VALID_REVIEW_STATES).toContain('needs-followup')
      expect(VALID_REVIEW_STATES).toContain('repeat-observed')
      expect(VALID_REVIEW_STATES.length).toBe(4)
    })
  })

  describe('FORBIDDEN_REVIEW_STATES', () => {
    it('should include all authority/approval states', () => {
      expect(FORBIDDEN_REVIEW_STATES).toContain('approved')
      expect(FORBIDDEN_REVIEW_STATES).toContain('validated')
      expect(FORBIDDEN_REVIEW_STATES).toContain('accepted')
      expect(FORBIDDEN_REVIEW_STATES).toContain('canonical')
      expect(FORBIDDEN_REVIEW_STATES).toContain('certified')
      expect(FORBIDDEN_REVIEW_STATES).toContain('verified')
    })
  })

  describe('isValidReviewTargetType', () => {
    it('should return true for valid target types', () => {
      expect(isValidReviewTargetType('archive')).toBe(true)
      expect(isValidReviewTargetType('driftRecord')).toBe(true)
    })

    it('should return false for invalid target types', () => {
      expect(isValidReviewTargetType('invalid')).toBe(false)
      expect(isValidReviewTargetType('')).toBe(false)
      expect(isValidReviewTargetType('ARCHIVE')).toBe(false)
    })
  })

  describe('isValidReviewState', () => {
    it('should return true for valid states', () => {
      expect(isValidReviewState('reviewed')).toBe(true)
      expect(isValidReviewState('flagged')).toBe(true)
      expect(isValidReviewState('needs-followup')).toBe(true)
      expect(isValidReviewState('repeat-observed')).toBe(true)
    })

    it('should return false for invalid states', () => {
      expect(isValidReviewState('invalid')).toBe(false)
      expect(isValidReviewState('')).toBe(false)
      expect(isValidReviewState('REVIEWED')).toBe(false)
    })
  })

  describe('isForbiddenReviewState', () => {
    it('should return true for forbidden states', () => {
      expect(isForbiddenReviewState('approved')).toBe(true)
      expect(isForbiddenReviewState('validated')).toBe(true)
      expect(isForbiddenReviewState('canonical')).toBe(true)
      expect(isForbiddenReviewState('certified')).toBe(true)
    })

    it('should return true for case variations of forbidden states', () => {
      expect(isForbiddenReviewState('APPROVED')).toBe(true)
      expect(isForbiddenReviewState('Validated')).toBe(true)
    })

    it('should return false for allowed states', () => {
      expect(isForbiddenReviewState('reviewed')).toBe(false)
      expect(isForbiddenReviewState('flagged')).toBe(false)
    })
  })

  describe('normalizeReviewTags', () => {
    it('should split comma-separated tags', () => {
      const result = normalizeReviewTags('foo, bar, baz')
      expect(result).toEqual(['foo', 'bar', 'baz'])
    })

    it('should trim whitespace from tags', () => {
      const result = normalizeReviewTags('  foo  ,  bar  ')
      expect(result).toEqual(['foo', 'bar'])
    })

    it('should remove empty tags', () => {
      const result = normalizeReviewTags('foo, , bar, , ')
      expect(result).toEqual(['foo', 'bar'])
    })

    it('should deduplicate tags', () => {
      const result = normalizeReviewTags('foo, bar, foo, baz, bar')
      expect(result).toEqual(['foo', 'bar', 'baz'])
    })

    it('should handle array input', () => {
      const result = normalizeReviewTags(['foo', ' bar ', 'foo'])
      expect(result).toEqual(['foo', 'bar'])
    })

    it('should handle empty input', () => {
      expect(normalizeReviewTags('')).toEqual([])
      expect(normalizeReviewTags([])).toEqual([])
    })
  })

  describe('validateEvidenceReview', () => {
    it('should return null for valid review', () => {
      const review = createMockReview('r1')
      expect(validateEvidenceReview(review)).toBeNull()
    })

    it('should reject missing target type', () => {
      const review = { targetId: 'id', reviewState: 'reviewed' }
      expect(validateEvidenceReview(review)).toBe('Target type is required')
    })

    it('should reject invalid target type', () => {
      const review = {
        targetType: 'invalid' as EvidenceReviewTargetType,
        targetId: 'id',
        reviewState: 'reviewed' as EvidenceReviewState,
      }
      expect(validateEvidenceReview(review)).toBe('Invalid target type: invalid')
    })

    it('should reject missing target ID', () => {
      const review = {
        targetType: 'archive' as EvidenceReviewTargetType,
        reviewState: 'reviewed' as EvidenceReviewState,
      }
      expect(validateEvidenceReview(review)).toBe('Target ID is required')
    })

    it('should reject whitespace-only target ID', () => {
      const review = {
        targetType: 'archive' as EvidenceReviewTargetType,
        targetId: '   ',
        reviewState: 'reviewed' as EvidenceReviewState,
      }
      expect(validateEvidenceReview(review)).toBe('Target ID is required')
    })

    it('should reject missing review state', () => {
      const review = {
        targetType: 'archive' as EvidenceReviewTargetType,
        targetId: 'id',
      }
      expect(validateEvidenceReview(review)).toBe('Review state is required')
    })

    it('should reject forbidden review states', () => {
      const review = {
        targetType: 'archive' as EvidenceReviewTargetType,
        targetId: 'id',
        reviewState: 'approved' as EvidenceReviewState,
      }
      expect(validateEvidenceReview(review)).toBe('Forbidden review state: approved')
    })

    it('should reject invalid review state', () => {
      const review = {
        targetType: 'archive' as EvidenceReviewTargetType,
        targetId: 'id',
        reviewState: 'invalid' as EvidenceReviewState,
      }
      expect(validateEvidenceReview(review)).toBe('Invalid review state: invalid')
    })
  })

  describe('createEvidenceReview', () => {
    it('should create valid review with required fields', () => {
      const review = createEvidenceReview({
        targetType: 'archive',
        targetId: 'archive-001',
        reviewState: 'reviewed',
      })

      expect(review.reviewId).toMatch(/^review-/)
      expect(review.targetType).toBe('archive')
      expect(review.targetId).toBe('archive-001')
      expect(review.reviewState).toBe('reviewed')
      expect(review.createdAt).toBeDefined()
      expect(review.notes).toBeUndefined()
      expect(review.tags).toBeUndefined()
    })

    it('should trim target ID', () => {
      const review = createEvidenceReview({
        targetType: 'archive',
        targetId: '  archive-001  ',
        reviewState: 'reviewed',
      })

      expect(review.targetId).toBe('archive-001')
    })

    it('should trim notes', () => {
      const review = createEvidenceReview({
        targetType: 'archive',
        targetId: 'id',
        reviewState: 'flagged',
        notes: '  Needs investigation  ',
      })

      expect(review.notes).toBe('Needs investigation')
    })

    it('should omit notes if empty after trimming', () => {
      const review = createEvidenceReview({
        targetType: 'archive',
        targetId: 'id',
        reviewState: 'reviewed',
        notes: '   ',
      })

      expect(review.notes).toBeUndefined()
    })

    it('should normalize tags', () => {
      const review = createEvidenceReview({
        targetType: 'driftRecord',
        targetId: 'drift-001',
        reviewState: 'repeat-observed',
        tags: 'stable, trend, stable',
      })

      expect(review.tags).toEqual(['stable', 'trend'])
    })

    it('should omit tags if empty after normalization', () => {
      const review = createEvidenceReview({
        targetType: 'archive',
        targetId: 'id',
        reviewState: 'reviewed',
        tags: '  ,  ,  ',
      })

      expect(review.tags).toBeUndefined()
    })

    it('should throw for forbidden review state', () => {
      expect(() =>
        createEvidenceReview({
          targetType: 'archive',
          targetId: 'id',
          reviewState: 'approved' as EvidenceReviewState,
        })
      ).toThrow('Forbidden review state: approved')
    })

    it('should throw for invalid review state', () => {
      expect(() =>
        createEvidenceReview({
          targetType: 'archive',
          targetId: 'id',
          reviewState: 'invalid' as EvidenceReviewState,
        })
      ).toThrow('Invalid review state: invalid')
    })

    it('should not mutate input params', () => {
      const params = {
        targetType: 'archive' as EvidenceReviewTargetType,
        targetId: '  archive-001  ',
        reviewState: 'reviewed' as EvidenceReviewState,
        notes: '  notes  ',
        tags: 'foo, bar',
      }

      const originalTargetId = params.targetId
      const originalNotes = params.notes
      const originalTags = params.tags

      createEvidenceReview(params)

      expect(params.targetId).toBe(originalTargetId)
      expect(params.notes).toBe(originalNotes)
      expect(params.tags).toBe(originalTags)
    })
  })

  describe('normalizeEvidenceReview', () => {
    it('should not mutate input', () => {
      const original = createMockReview('r1', { notes: '  notes  ' })
      const originalNotes = original.notes

      normalizeEvidenceReview(original)

      expect(original.notes).toBe(originalNotes)
    })

    it('should trim target ID', () => {
      const review = createMockReview('r1', { targetId: '  archive-001  ' })
      const normalized = normalizeEvidenceReview(review)

      expect(normalized.targetId).toBe('archive-001')
    })

    it('should trim notes', () => {
      const review = createMockReview('r1', { notes: '  observation  ' })
      const normalized = normalizeEvidenceReview(review)

      expect(normalized.notes).toBe('observation')
    })

    it('should remove notes if empty after trimming', () => {
      const review = createMockReview('r1', { notes: '   ' })
      const normalized = normalizeEvidenceReview(review)

      expect(normalized.notes).toBeUndefined()
    })

    it('should normalize tags', () => {
      const review = createMockReview('r1', { tags: ['foo', ' bar ', 'foo'] })
      const normalized = normalizeEvidenceReview(review)

      expect(normalized.tags).toEqual(['foo', 'bar'])
    })

    it('should remove tags if empty after normalization', () => {
      const review = createMockReview('r1', { tags: ['', '  '] })
      const normalized = normalizeEvidenceReview(review)

      expect(normalized.tags).toBeUndefined()
    })
  })

  describe('filterReviewsByTarget', () => {
    it('should filter reviews by target type', () => {
      const reviews = [
        createMockReview('r1', { targetType: 'archive' }),
        createMockReview('r2', { targetType: 'driftRecord' }),
        createMockReview('r3', { targetType: 'archive' }),
      ]

      const archiveReviews = filterReviewsByTarget(reviews, 'archive')

      expect(archiveReviews.length).toBe(2)
      expect(archiveReviews.every((r) => r.targetType === 'archive')).toBe(true)
    })

    it('should return empty array if no matches', () => {
      const reviews = [createMockReview('r1', { targetType: 'archive' })]

      const result = filterReviewsByTarget(reviews, 'correlation')

      expect(result).toEqual([])
    })

    it('should not mutate input array', () => {
      const reviews = [
        createMockReview('r1', { targetType: 'archive' }),
        createMockReview('r2', { targetType: 'driftRecord' }),
      ]

      const originalLength = reviews.length

      filterReviewsByTarget(reviews, 'archive')

      expect(reviews.length).toBe(originalLength)
    })
  })

  describe('filterReviewsByTargetId', () => {
    it('should filter reviews by target ID', () => {
      const reviews = [
        createMockReview('r1', { targetId: 'archive-001' }),
        createMockReview('r2', { targetId: 'archive-002' }),
        createMockReview('r3', { targetId: 'archive-001' }),
      ]

      const result = filterReviewsByTargetId(reviews, 'archive-001')

      expect(result.length).toBe(2)
      expect(result.every((r) => r.targetId === 'archive-001')).toBe(true)
    })
  })

  describe('filterReviewsByState', () => {
    it('should filter reviews by review state', () => {
      const reviews = [
        createMockReview('r1', { reviewState: 'reviewed' }),
        createMockReview('r2', { reviewState: 'flagged' }),
        createMockReview('r3', { reviewState: 'reviewed' }),
      ]

      const reviewedReviews = filterReviewsByState(reviews, 'reviewed')

      expect(reviewedReviews.length).toBe(2)
      expect(reviewedReviews.every((r) => r.reviewState === 'reviewed')).toBe(true)
    })

    it('should return empty array if no matches', () => {
      const reviews = [createMockReview('r1', { reviewState: 'reviewed' })]

      const result = filterReviewsByState(reviews, 'flagged')

      expect(result).toEqual([])
    })

    it('should not mutate input array', () => {
      const reviews = [
        createMockReview('r1', { reviewState: 'reviewed' }),
        createMockReview('r2', { reviewState: 'flagged' }),
      ]

      const originalLength = reviews.length

      filterReviewsByState(reviews, 'reviewed')

      expect(reviews.length).toBe(originalLength)
    })
  })

  describe('summarizeReviewsByTargetType', () => {
    it('should summarize reviews by target type', () => {
      const reviews = [
        createMockReview('r1', { targetType: 'archive', targetId: 'a1' }),
        createMockReview('r2', { targetType: 'archive', targetId: 'a2' }),
        createMockReview('r3', { targetType: 'archive', targetId: 'a1' }),
        createMockReview('r4', { targetType: 'driftRecord', targetId: 'd1' }),
      ]

      const summaries = summarizeReviewsByTargetType(reviews)

      const archiveSummary = summaries.find((s) => s.groupKey === 'archive')
      expect(archiveSummary).toBeDefined()
      expect(archiveSummary!.reviewCount).toBe(3)
      expect(archiveSummary!.targetIds).toContain('a1')
      expect(archiveSummary!.targetIds).toContain('a2')
      expect(archiveSummary!.targetIds.length).toBe(2)

      const driftSummary = summaries.find((s) => s.groupKey === 'driftRecord')
      expect(driftSummary).toBeDefined()
      expect(driftSummary!.reviewCount).toBe(1)
    })

    it('should return empty array for no reviews', () => {
      expect(summarizeReviewsByTargetType([])).toEqual([])
    })

    it('should not mutate input array', () => {
      const reviews = [createMockReview('r1'), createMockReview('r2')]
      const originalLength = reviews.length

      summarizeReviewsByTargetType(reviews)

      expect(reviews.length).toBe(originalLength)
    })
  })

  describe('summarizeReviewsByState', () => {
    it('should summarize reviews by review state', () => {
      const reviews = [
        createMockReview('r1', { reviewState: 'reviewed', targetId: 'a1' }),
        createMockReview('r2', { reviewState: 'reviewed', targetId: 'a2' }),
        createMockReview('r3', { reviewState: 'flagged', targetId: 'a3' }),
      ]

      const summaries = summarizeReviewsByState(reviews)

      const reviewedSummary = summaries.find((s) => s.groupKey === 'reviewed')
      expect(reviewedSummary).toBeDefined()
      expect(reviewedSummary!.reviewCount).toBe(2)

      const flaggedSummary = summaries.find((s) => s.groupKey === 'flagged')
      expect(flaggedSummary).toBeDefined()
      expect(flaggedSummary!.reviewCount).toBe(1)
    })

    it('should return empty array for no reviews', () => {
      expect(summarizeReviewsByState([])).toEqual([])
    })
  })

  describe('dedupeEvidenceReviews', () => {
    it('should remove duplicate review IDs', () => {
      const reviews = [
        createMockReview('r1'),
        createMockReview('r2'),
        createMockReview('r1'),
        createMockReview('r3'),
      ]

      const deduped = dedupeEvidenceReviews(reviews)

      expect(deduped.length).toBe(3)
      expect(deduped.map((r) => r.reviewId)).toEqual(['r1', 'r2', 'r3'])
    })

    it('should keep first occurrence', () => {
      const reviews = [
        createMockReview('r1', { notes: 'first' }),
        createMockReview('r1', { notes: 'second' }),
      ]

      const deduped = dedupeEvidenceReviews(reviews)

      expect(deduped.length).toBe(1)
      expect(deduped[0].notes).toBe('first')
    })

    it('should allow multiple reviews per target (dedupe by reviewId only)', () => {
      const reviews = [
        createMockReview('r1', { targetId: 'archive-001', reviewState: 'reviewed' }),
        createMockReview('r2', { targetId: 'archive-001', reviewState: 'flagged' }),
      ]

      const deduped = dedupeEvidenceReviews(reviews)

      expect(deduped.length).toBe(2)
    })

    it('should not mutate input array', () => {
      const reviews = [
        createMockReview('r1'),
        createMockReview('r1'),
        createMockReview('r2'),
      ]

      const originalLength = reviews.length

      dedupeEvidenceReviews(reviews)

      expect(reviews.length).toBe(originalLength)
    })
  })

  describe('buildEvidenceReviewLabel', () => {
    it('should build label with state and target', () => {
      const review = createMockReview('r1', {
        targetType: 'archive',
        targetId: 'archive-001',
        reviewState: 'flagged',
      })

      const label = buildEvidenceReviewLabel(review)

      expect(label).toBe('[flagged] archive:archive-001')
    })

    it('should produce stable output for same input', () => {
      const review = createMockReview('r1')

      const label1 = buildEvidenceReviewLabel(review)
      const label2 = buildEvidenceReviewLabel(review)

      expect(label1).toBe(label2)
    })
  })

  describe('getTargetTypeLabel', () => {
    it('should return human-readable labels', () => {
      expect(getTargetTypeLabel('archive')).toBe('Archive')
      expect(getTargetTypeLabel('topologyVariant')).toBe('Topology Variant')
      expect(getTargetTypeLabel('correlation')).toBe('Correlation')
      expect(getTargetTypeLabel('driftRecord')).toBe('Drift Record')
      expect(getTargetTypeLabel('driftSynthesis')).toBe('Drift Synthesis')
    })
  })

  describe('getReviewStateLabel', () => {
    it('should return human-readable labels', () => {
      expect(getReviewStateLabel('reviewed')).toBe('Reviewed')
      expect(getReviewStateLabel('flagged')).toBe('Flagged')
      expect(getReviewStateLabel('needs-followup')).toBe('Needs Follow-up')
      expect(getReviewStateLabel('repeat-observed')).toBe('Repeat Observed')
    })
  })

  describe('missing optional fields', () => {
    it('should handle review without notes', () => {
      const review = createMockReview('r1')
      delete review.notes

      expect(() => normalizeEvidenceReview(review)).not.toThrow()
      expect(filterReviewsByState([review], 'reviewed').length).toBe(1)
    })

    it('should handle review without tags', () => {
      const review = createMockReview('r1')
      delete review.tags

      const normalized = normalizeEvidenceReview(review)
      expect(normalized.tags).toBeUndefined()
    })

    it('should preserve all fields through normalize', () => {
      const review: EvidenceReviewRecord = {
        reviewId: 'r1',
        targetType: 'driftRecord',
        targetId: 'drift-001',
        reviewState: 'repeat-observed',
        notes: 'Stable pattern',
        tags: ['stable', 'consistent'],
        createdAt: '2026-05-22T12:00:00Z',
      }

      const normalized = normalizeEvidenceReview(review)

      expect(normalized.reviewId).toBe(review.reviewId)
      expect(normalized.targetType).toBe(review.targetType)
      expect(normalized.targetId).toBe(review.targetId)
      expect(normalized.reviewState).toBe(review.reviewState)
      expect(normalized.createdAt).toBe(review.createdAt)
    })
  })

  describe('observational language compliance', () => {
    const FORBIDDEN_WORDS = [
      'approved',
      'validated',
      'accepted',
      'canonical',
      'production-ready',
      'certified',
      'verified',
      'correct',
      'optimal',
      'improve',
      'improved',
      'optimization',
      'recommend',
      'recommendation',
    ]

    it('buildEvidenceReviewLabel should not contain forbidden language', () => {
      for (const state of VALID_REVIEW_STATES) {
        const review = createMockReview('r1', { reviewState: state })
        const label = buildEvidenceReviewLabel(review)

        for (const word of FORBIDDEN_WORDS) {
          expect(label.toLowerCase()).not.toContain(word)
        }
      }
    })

    it('getTargetTypeLabel should not contain forbidden language', () => {
      for (const targetType of VALID_REVIEW_TARGET_TYPES) {
        const label = getTargetTypeLabel(targetType)

        for (const word of FORBIDDEN_WORDS) {
          expect(label.toLowerCase()).not.toContain(word)
        }
      }
    })

    it('getReviewStateLabel should not contain forbidden language', () => {
      for (const state of VALID_REVIEW_STATES) {
        const label = getReviewStateLabel(state)

        for (const word of FORBIDDEN_WORDS) {
          expect(label.toLowerCase()).not.toContain(word)
        }
      }
    })

    it('validateEvidenceReview error messages should not contain forbidden language', () => {
      const errorCases = [
        { targetId: 'id', reviewState: 'reviewed' },
        { targetType: 'invalid', targetId: 'id', reviewState: 'reviewed' },
        { targetType: 'archive', reviewState: 'reviewed' },
        { targetType: 'archive', targetId: 'id' },
        { targetType: 'archive', targetId: 'id', reviewState: 'invalid' },
      ]

      for (const testCase of errorCases) {
        const error = validateEvidenceReview(testCase as Partial<EvidenceReviewRecord>)
        if (error) {
          for (const word of FORBIDDEN_WORDS) {
            expect(error.toLowerCase()).not.toContain(word)
          }
        }
      }
    })

    it('VALID_REVIEW_STATES should contain only observational states', () => {
      for (const state of VALID_REVIEW_STATES) {
        expect(isForbiddenReviewState(state)).toBe(false)
      }
    })

    it('should reject all FORBIDDEN_REVIEW_STATES', () => {
      for (const state of FORBIDDEN_REVIEW_STATES) {
        expect(isForbiddenReviewState(state)).toBe(true)
      }
    })
  })
})
