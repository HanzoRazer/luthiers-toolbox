/**
 * Experimental Drift Synthesis Tests
 *
 * Dev Order 72: Session-level drift synthesis
 *
 * Required test categories:
 * 1. insufficient data below 3 drift records
 * 2. synthesis groups by session
 * 3. synthesis groups by topology variant
 * 4. dominant upward synthesis
 * 5. dominant downward synthesis
 * 6. dominant stable synthesis
 * 7. dominant variable synthesis
 * 8. mixed-direction synthesis
 * 9. sparse drift records skipped safely
 * 10. invalid drift records excluded
 * 11. duplicate drift records ignored
 * 12. narrative avoids forbidden language
 * 13. synthesis preserves input immutability
 * 14. missing references handled safely
 * 15. stable ordering preserved
 */

import { describe, it, expect } from 'vitest'
import type { ExperimentalDriftRecord, DriftDirection } from '../../../types/acoustics/experimentalDrift'
import {
  MINIMUM_SYNTHESIS_RECORDS,
  hasSufficientDriftSynthesisData,
  deduplicateDriftRecords,
  isValidDriftRecord,
  filterValidDriftRecords,
  groupDriftRecordsBySession,
  groupDriftRecordsByVariant,
  classifyDominantDriftDirection,
  summarizeDriftPatterns,
  buildDriftSynthesisNarrative,
  computeExperimentalDriftSynthesis,
  getSynthesisForSession,
  getSynthesisForVariant,
} from '../experimentalDriftSynthesis'

function createMockDriftRecord(
  id: string,
  overrides: {
    field?: string
    direction?: DriftDirection
    sampleCount?: number
    archiveIds?: string[]
    sessionContext?: string
    variantId?: string
    contextType?: 'session' | 'variant' | 'chronological'
    contextId?: string
  } = {}
): ExperimentalDriftRecord {
  return {
    driftId: id,
    archiveIds: overrides.archiveIds ?? ['a1', 'a2', 'a3'],
    observedField: overrides.field ?? 'measuredHelmholtzHz',
    direction: overrides.direction ?? 'stable',
    sampleCount: overrides.sampleCount ?? 3,
    timelinePoints: [
      {
        archiveId: 'a1',
        value: 100,
        sessionContext: overrides.sessionContext,
        variantId: overrides.variantId,
      },
      {
        archiveId: 'a2',
        value: 110,
        deltaFromPrevious: 10,
        percentDeltaFromPrevious: 0.1,
        sessionContext: overrides.sessionContext,
        variantId: overrides.variantId,
      },
      {
        archiveId: 'a3',
        value: 120,
        deltaFromPrevious: 10,
        percentDeltaFromPrevious: 0.09,
        sessionContext: overrides.sessionContext,
        variantId: overrides.variantId,
      },
    ],
    narrative: `${overrides.field ?? 'measuredHelmholtzHz'} ${overrides.direction ?? 'stable'} drift`,
    contextType: overrides.contextType,
    contextId: overrides.contextId,
    computedAtIso: new Date().toISOString(),
  }
}

function createInvalidDriftRecord(): unknown {
  return {
    // Missing required fields
    driftId: 'invalid',
  }
}

describe('experimentalDriftSynthesis', () => {
  describe('constants', () => {
    it('should require minimum 3 drift records for synthesis', () => {
      expect(MINIMUM_SYNTHESIS_RECORDS).toBe(3)
    })
  })

  describe('hasSufficientDriftSynthesisData', () => {
    it('should return false for fewer than 3 drift records', () => {
      expect(hasSufficientDriftSynthesisData([])).toBe(false)
      expect(hasSufficientDriftSynthesisData([createMockDriftRecord('d1')])).toBe(false)
      expect(
        hasSufficientDriftSynthesisData([
          createMockDriftRecord('d1'),
          createMockDriftRecord('d2'),
        ])
      ).toBe(false)
    })

    it('should return true for 3 or more drift records', () => {
      const records = [
        createMockDriftRecord('d1'),
        createMockDriftRecord('d2'),
        createMockDriftRecord('d3'),
      ]
      expect(hasSufficientDriftSynthesisData(records)).toBe(true)
    })
  })

  describe('deduplicateDriftRecords', () => {
    it('should remove duplicate drift records by driftId', () => {
      const records = [
        createMockDriftRecord('d1'),
        createMockDriftRecord('d1'), // duplicate
        createMockDriftRecord('d2'),
      ]

      const deduplicated = deduplicateDriftRecords(records)

      expect(deduplicated.length).toBe(2)
      expect(deduplicated.map((r) => r.driftId)).toEqual(['d1', 'd2'])
    })
  })

  describe('isValidDriftRecord', () => {
    it('should return true for valid drift records', () => {
      expect(isValidDriftRecord(createMockDriftRecord('d1'))).toBe(true)
    })

    it('should return false for invalid drift records', () => {
      expect(isValidDriftRecord(createInvalidDriftRecord())).toBe(false)
      expect(isValidDriftRecord(null)).toBe(false)
      expect(isValidDriftRecord(undefined)).toBe(false)
      expect(isValidDriftRecord({})).toBe(false)
    })
  })

  describe('filterValidDriftRecords', () => {
    it('should exclude invalid drift records', () => {
      const records = [
        createMockDriftRecord('d1'),
        createInvalidDriftRecord() as ExperimentalDriftRecord,
        createMockDriftRecord('d2'),
      ]

      const { valid, warnings } = filterValidDriftRecords(records)

      expect(valid.length).toBe(2)
      expect(warnings.length).toBe(1)
      expect(warnings[0]).toContain('invalid')
    })
  })

  describe('groupDriftRecordsBySession', () => {
    it('should group drift records by session context', () => {
      const records = [
        createMockDriftRecord('d1', { sessionContext: 'session-A' }),
        createMockDriftRecord('d2', { sessionContext: 'session-A' }),
        createMockDriftRecord('d3', { sessionContext: 'session-B' }),
      ]

      const groups = groupDriftRecordsBySession(records)

      expect(groups.get('session-A')?.length).toBe(2)
      expect(groups.get('session-B')?.length).toBe(1)
    })

    it('should handle records without session context', () => {
      const records = [
        createMockDriftRecord('d1', { sessionContext: undefined }),
        createMockDriftRecord('d2', { sessionContext: 'session-A' }),
      ]

      const groups = groupDriftRecordsBySession(records)

      expect(groups.get('__none__')?.length).toBe(1)
      expect(groups.get('session-A')?.length).toBe(1)
    })

    it('should use contextId for session-type records', () => {
      const records = [
        createMockDriftRecord('d1', { contextType: 'session', contextId: 'ctx-session-1' }),
        createMockDriftRecord('d2', { contextType: 'session', contextId: 'ctx-session-1' }),
      ]

      const groups = groupDriftRecordsBySession(records)

      expect(groups.get('ctx-session-1')?.length).toBe(2)
    })
  })

  describe('groupDriftRecordsByVariant', () => {
    it('should group drift records by topology variant', () => {
      const records = [
        createMockDriftRecord('d1', { variantId: 'v1' }),
        createMockDriftRecord('d2', { variantId: 'v1' }),
        createMockDriftRecord('d3', { variantId: 'v2' }),
      ]

      const groups = groupDriftRecordsByVariant(records)

      expect(groups.get('v1')?.length).toBe(2)
      expect(groups.get('v2')?.length).toBe(1)
    })

    it('should handle records without variant reference', () => {
      const records = [
        createMockDriftRecord('d1', { variantId: undefined }),
        createMockDriftRecord('d2', { variantId: 'v1' }),
      ]

      const groups = groupDriftRecordsByVariant(records)

      expect(groups.get('__none__')?.length).toBe(1)
      expect(groups.get('v1')?.length).toBe(1)
    })
  })

  describe('classifyDominantDriftDirection', () => {
    it('should classify as upward when majority is upward', () => {
      const records = [
        createMockDriftRecord('d1', { direction: 'upward' }),
        createMockDriftRecord('d2', { direction: 'upward' }),
        createMockDriftRecord('d3', { direction: 'stable' }),
      ]

      expect(classifyDominantDriftDirection(records)).toBe('upward')
    })

    it('should classify as downward when majority is downward', () => {
      const records = [
        createMockDriftRecord('d1', { direction: 'downward' }),
        createMockDriftRecord('d2', { direction: 'downward' }),
        createMockDriftRecord('d3', { direction: 'stable' }),
      ]

      expect(classifyDominantDriftDirection(records)).toBe('downward')
    })

    it('should classify as stable when majority is stable', () => {
      const records = [
        createMockDriftRecord('d1', { direction: 'stable' }),
        createMockDriftRecord('d2', { direction: 'stable' }),
        createMockDriftRecord('d3', { direction: 'upward' }),
      ]

      expect(classifyDominantDriftDirection(records)).toBe('stable')
    })

    it('should classify as variable when majority is variable', () => {
      const records = [
        createMockDriftRecord('d1', { direction: 'variable' }),
        createMockDriftRecord('d2', { direction: 'variable' }),
        createMockDriftRecord('d3', { direction: 'stable' }),
      ]

      expect(classifyDominantDriftDirection(records)).toBe('variable')
    })

    it('should classify as mixed when no clear majority', () => {
      const records = [
        createMockDriftRecord('d1', { direction: 'upward' }),
        createMockDriftRecord('d2', { direction: 'downward' }),
        createMockDriftRecord('d3', { direction: 'stable' }),
        createMockDriftRecord('d4', { direction: 'variable' }),
      ]

      expect(classifyDominantDriftDirection(records)).toBe('mixed')
    })
  })

  describe('summarizeDriftPatterns', () => {
    it('should summarize patterns by field and direction', () => {
      const records = [
        createMockDriftRecord('d1', { field: 'measuredHelmholtzHz', direction: 'upward' }),
        createMockDriftRecord('d2', { field: 'measuredHelmholtzHz', direction: 'upward' }),
        createMockDriftRecord('d3', { field: 'measuredPeakHz', direction: 'stable' }),
      ]

      const patterns = summarizeDriftPatterns(records)

      expect(patterns.length).toBe(2)
      expect(patterns[0].field).toBe('measuredHelmholtzHz')
      expect(patterns[0].direction).toBe('upward')
      expect(patterns[0].occurrences).toBe(2)
    })

    it('should generate prose descriptions', () => {
      const records = [
        createMockDriftRecord('d1', { field: 'measuredHelmholtzHz', direction: 'upward' }),
        createMockDriftRecord('d2', { field: 'measuredHelmholtzHz', direction: 'upward' }),
      ]

      const patterns = summarizeDriftPatterns(records)

      expect(patterns[0].description).toContain('upward')
      expect(patterns[0].description).toContain('Helmholtz')
      expect(patterns[0].description).toContain('repeated')
    })
  })

  describe('buildDriftSynthesisNarrative', () => {
    it('should generate upward narrative', () => {
      const narrative = buildDriftSynthesisNarrative(
        'upward',
        ['repeated upward Helmholtz drift'],
        5,
        10
      )

      expect(narrative).toContain('predominantly upward')
    })

    it('should generate mixed narrative', () => {
      const narrative = buildDriftSynthesisNarrative(
        'mixed',
        ['upward Helmholtz drift', 'downward Peak drift'],
        4,
        8
      )

      expect(narrative).toContain('mixed directional behavior')
    })

    it('should include context label when provided', () => {
      const narrative = buildDriftSynthesisNarrative(
        'stable',
        ['stable damping'],
        3,
        6,
        'session-experimental-1'
      )

      expect(narrative).toContain('In session-experimental-1')
    })
  })

  describe('computeExperimentalDriftSynthesis', () => {
    it('should compute overall synthesis with sufficient data', () => {
      const records = [
        createMockDriftRecord('d1', { direction: 'upward' }),
        createMockDriftRecord('d2', { direction: 'upward' }),
        createMockDriftRecord('d3', { direction: 'stable' }),
      ]

      const result = computeExperimentalDriftSynthesis(records)

      expect(result.summary.overallSynthesis).toBeDefined()
      expect(result.summary.overallSynthesis?.dominantDirection).toBe('upward')
    })

    it('should not produce overall synthesis with insufficient data', () => {
      const records = [
        createMockDriftRecord('d1'),
        createMockDriftRecord('d2'),
      ]

      const result = computeExperimentalDriftSynthesis(records)

      expect(result.summary.overallSynthesis).toBeUndefined()
    })

    it('should produce session observations', () => {
      const records = [
        createMockDriftRecord('d1', { sessionContext: 'session-A' }),
        createMockDriftRecord('d2', { sessionContext: 'session-A' }),
        createMockDriftRecord('d3', { sessionContext: 'session-A' }),
      ]

      const result = computeExperimentalDriftSynthesis(records)

      expect(result.summary.sessionObservations.length).toBe(1)
      expect(result.summary.sessionObservations[0].sessionContext).toBe('session-A')
    })

    it('should produce variant observations', () => {
      const records = [
        createMockDriftRecord('d1', { variantId: 'v1' }),
        createMockDriftRecord('d2', { variantId: 'v1' }),
        createMockDriftRecord('d3', { variantId: 'v1' }),
      ]

      const result = computeExperimentalDriftSynthesis(records)

      expect(result.summary.variantObservations.length).toBe(1)
      expect(result.summary.variantObservations[0].variantId).toBe('v1')
    })

    it('should track insufficient sessions', () => {
      const records = [
        createMockDriftRecord('d1', { sessionContext: 'session-small' }),
        createMockDriftRecord('d2', { sessionContext: 'session-small' }),
        createMockDriftRecord('d3', { sessionContext: 'session-large' }),
        createMockDriftRecord('d4', { sessionContext: 'session-large' }),
        createMockDriftRecord('d5', { sessionContext: 'session-large' }),
      ]

      const result = computeExperimentalDriftSynthesis(records)

      expect(result.summary.insufficientSessions).toContain('session-small')
    })

    it('should ignore duplicate drift records', () => {
      const records = [
        createMockDriftRecord('d1'),
        createMockDriftRecord('d1'), // duplicate
        createMockDriftRecord('d2'),
        createMockDriftRecord('d3'),
      ]

      const result = computeExperimentalDriftSynthesis(records)

      expect(result.totalDriftRecordsProvided).toBe(4)
      expect(result.totalDriftRecordsAnalyzed).toBe(3)
    })

    it('should exclude invalid drift records', () => {
      const records = [
        createMockDriftRecord('d1'),
        createInvalidDriftRecord() as ExperimentalDriftRecord,
        createMockDriftRecord('d2'),
        createMockDriftRecord('d3'),
      ]

      const result = computeExperimentalDriftSynthesis(records)

      expect(result.totalDriftRecordsAnalyzed).toBe(3)
      expect(result.warnings.length).toBe(1)
    })

    it('should not mutate input array', () => {
      const records = [
        createMockDriftRecord('d3'),
        createMockDriftRecord('d1'),
        createMockDriftRecord('d2'),
      ]

      const originalOrder = records.map((r) => r.driftId)

      computeExperimentalDriftSynthesis(records)

      const afterOrder = records.map((r) => r.driftId)
      expect(afterOrder).toEqual(originalOrder)
    })

    it('should handle records with missing references safely', () => {
      const records = [
        createMockDriftRecord('d1', { sessionContext: undefined, variantId: undefined }),
        createMockDriftRecord('d2', { sessionContext: undefined, variantId: undefined }),
        createMockDriftRecord('d3', { sessionContext: undefined, variantId: undefined }),
      ]

      // Should not throw
      const result = computeExperimentalDriftSynthesis(records)
      expect(result.summary.overallSynthesis).toBeDefined()
    })
  })

  describe('getSynthesisForSession / getSynthesisForVariant', () => {
    it('should retrieve session observation', () => {
      const records = [
        createMockDriftRecord('d1', { sessionContext: 'session-A' }),
        createMockDriftRecord('d2', { sessionContext: 'session-A' }),
        createMockDriftRecord('d3', { sessionContext: 'session-A' }),
      ]

      const result = computeExperimentalDriftSynthesis(records)
      const sessionObs = getSynthesisForSession(result, 'session-A')

      expect(sessionObs).toBeDefined()
      expect(sessionObs?.sessionContext).toBe('session-A')
    })

    it('should retrieve variant observation', () => {
      const records = [
        createMockDriftRecord('d1', { variantId: 'v1' }),
        createMockDriftRecord('d2', { variantId: 'v1' }),
        createMockDriftRecord('d3', { variantId: 'v1' }),
      ]

      const result = computeExperimentalDriftSynthesis(records)
      const variantObs = getSynthesisForVariant(result, 'v1')

      expect(variantObs).toBeDefined()
      expect(variantObs?.variantId).toBe('v1')
    })
  })

  describe('observational language compliance', () => {
    const FORBIDDEN_WORDS = [
      'improve',
      'improved',
      'improves',
      'improvement',
      'optimize',
      'optimized',
      'optimizes',
      'optimization',
      'better',
      'best',
      'fix',
      'fixed',
      'fixes',
      'recommend',
      'recommended',
      'recommends',
      'recommendation',
      'validate',
      'validated',
      'validates',
      'validation',
      'correct',
      'corrected',
      'corrects',
    ]

    it('should not use forbidden language in upward synthesis narrative', () => {
      const narrative = buildDriftSynthesisNarrative(
        'upward',
        ['repeated upward Helmholtz drift'],
        5,
        10
      )

      for (const word of FORBIDDEN_WORDS) {
        expect(narrative.toLowerCase()).not.toContain(word)
      }
    })

    it('should not use forbidden language in mixed synthesis narrative', () => {
      const narrative = buildDriftSynthesisNarrative(
        'mixed',
        ['upward Helmholtz', 'downward Peak'],
        4,
        8
      )

      for (const word of FORBIDDEN_WORDS) {
        expect(narrative.toLowerCase()).not.toContain(word)
      }
    })

    it('should not use forbidden language in overall synthesis', () => {
      const records = [
        createMockDriftRecord('d1', { direction: 'upward' }),
        createMockDriftRecord('d2', { direction: 'upward' }),
        createMockDriftRecord('d3', { direction: 'upward' }),
      ]

      const result = computeExperimentalDriftSynthesis(records)
      const narrative = result.summary.overallSynthesis?.narrative ?? ''

      for (const word of FORBIDDEN_WORDS) {
        expect(narrative.toLowerCase()).not.toContain(word)
      }
    })

    it('should use observational language in pattern descriptions', () => {
      const records = [
        createMockDriftRecord('d1', { field: 'measuredHelmholtzHz', direction: 'upward' }),
        createMockDriftRecord('d2', { field: 'measuredHelmholtzHz', direction: 'upward' }),
      ]

      const patterns = summarizeDriftPatterns(records)

      for (const pattern of patterns) {
        expect(pattern.description).toMatch(/drift|behavior|movement|observed|repeated|stable|variable/)
      }
    })
  })

  describe('stable ordering', () => {
    it('should maintain consistent pattern ordering by occurrence count', () => {
      const records = [
        createMockDriftRecord('d1', { field: 'measuredHelmholtzHz', direction: 'upward' }),
        createMockDriftRecord('d2', { field: 'measuredHelmholtzHz', direction: 'upward' }),
        createMockDriftRecord('d3', { field: 'measuredHelmholtzHz', direction: 'upward' }),
        createMockDriftRecord('d4', { field: 'measuredPeakHz', direction: 'stable' }),
      ]

      const patterns = summarizeDriftPatterns(records)

      // Helmholtz should come first (3 occurrences) then Peak (1 occurrence)
      expect(patterns[0].field).toBe('measuredHelmholtzHz')
      expect(patterns[0].occurrences).toBe(3)
    })
  })
})
