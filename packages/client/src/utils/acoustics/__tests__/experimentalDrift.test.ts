/**
 * Experimental Drift Tests
 *
 * Dev Order 70: Experimental drift timeline workspace
 *
 * Tests drift computation, narrative generation, and observational semantics.
 * Target: 18-22 tests including forbidden language audit.
 */

import { describe, it, expect } from 'vitest'
import type { MeasurementArchiveRecord } from '../../../types/acoustics/measurementArchive'
import type { DriftDirection } from '../../../types/acoustics/experimentalDrift'
import {
  MINIMUM_DRIFT_SAMPLE_SIZE,
  DRIFT_DIRECTION_THRESHOLD,
  DRIFT_TRACKABLE_FIELDS,
  hasSufficientDriftData,
  sortArchivesChronologically,
  extractComparableFieldSeries,
  classifyDriftDirection,
  buildDriftNarrative,
  groupArchivesByVariantTimeline,
  groupArchivesBySessionTimeline,
  buildDriftSequences,
  computeExperimentalDrift,
  filterDriftsByDirection,
  filterDriftsByField,
  getDriftsForContext,
} from '../experimentalDrift'

function createMockArchive(
  id: string,
  overrides: {
    timestamp?: string
    helmholtzHz?: number
    peakHz?: number
    dampingFactor?: number
    q?: number
    variantRefs?: string[]
    sessionContext?: string
  } = {}
): MeasurementArchiveRecord {
  return {
    archiveId: id,
    schemaVersion: 'measurement-archive.v1',
    status: 'active',
    metadata: {
      createdAtIso: overrides.timestamp ?? new Date().toISOString(),
    },
    measurements: {
      measuredHelmholtzHz: overrides.helmholtzHz,
      measuredPeakHz: overrides.peakHz,
      measuredDampingFactor: overrides.dampingFactor,
      measuredQ: overrides.q,
    },
    topologyVariantReferences: overrides.variantRefs,
    context: {
      sessionContext: overrides.sessionContext,
    },
  } as MeasurementArchiveRecord
}

describe('experimentalDrift', () => {
  describe('constants', () => {
    it('should have minimum sample size of 3', () => {
      expect(MINIMUM_DRIFT_SAMPLE_SIZE).toBe(3)
    })

    it('should have drift direction threshold of 5%', () => {
      expect(DRIFT_DIRECTION_THRESHOLD).toBe(0.05)
    })

    it('should track measuredHelmholtzHz, measuredPeakHz, measuredDampingFactor, measuredQ', () => {
      expect(DRIFT_TRACKABLE_FIELDS).toContain('measuredHelmholtzHz')
      expect(DRIFT_TRACKABLE_FIELDS).toContain('measuredPeakHz')
      expect(DRIFT_TRACKABLE_FIELDS).toContain('measuredDampingFactor')
      expect(DRIFT_TRACKABLE_FIELDS).toContain('measuredQ')
      expect(DRIFT_TRACKABLE_FIELDS.length).toBe(4)
    })
  })

  describe('hasSufficientDriftData', () => {
    it('should return false for fewer than 3 archives', () => {
      expect(hasSufficientDriftData([])).toBe(false)
      expect(hasSufficientDriftData([createMockArchive('a1')])).toBe(false)
      expect(hasSufficientDriftData([createMockArchive('a1'), createMockArchive('a2')])).toBe(false)
    })

    it('should return true for 3 or more archives', () => {
      const archives = [createMockArchive('a1'), createMockArchive('a2'), createMockArchive('a3')]
      expect(hasSufficientDriftData(archives)).toBe(true)
    })
  })

  describe('sortArchivesChronologically', () => {
    it('should sort archives by createdAtIso', () => {
      const archives = [
        createMockArchive('a3', { timestamp: '2026-01-03T00:00:00Z' }),
        createMockArchive('a1', { timestamp: '2026-01-01T00:00:00Z' }),
        createMockArchive('a2', { timestamp: '2026-01-02T00:00:00Z' }),
      ]

      const sorted = sortArchivesChronologically(archives)

      expect(sorted[0].archiveId).toBe('a1')
      expect(sorted[1].archiveId).toBe('a2')
      expect(sorted[2].archiveId).toBe('a3')
    })

    it('should not mutate original array', () => {
      const archives = [
        createMockArchive('a2', { timestamp: '2026-01-02T00:00:00Z' }),
        createMockArchive('a1', { timestamp: '2026-01-01T00:00:00Z' }),
      ]

      sortArchivesChronologically(archives)

      expect(archives[0].archiveId).toBe('a2')
    })
  })

  describe('extractComparableFieldSeries', () => {
    it('should extract field values with archives', () => {
      const archives = [
        createMockArchive('a1', { helmholtzHz: 100 }),
        createMockArchive('a2', { helmholtzHz: 110 }),
        createMockArchive('a3', { helmholtzHz: undefined }),
      ]

      const series = extractComparableFieldSeries(archives, 'measuredHelmholtzHz')

      expect(series.length).toBe(2)
      expect(series[0].value).toBe(100)
      expect(series[1].value).toBe(110)
    })

    it('should skip archives with undefined field values', () => {
      const archives = [
        createMockArchive('a1', { helmholtzHz: undefined }),
        createMockArchive('a2', { helmholtzHz: 100 }),
      ]

      const series = extractComparableFieldSeries(archives, 'measuredHelmholtzHz')

      expect(series.length).toBe(1)
      expect(series[0].archive.archiveId).toBe('a2')
    })
  })

  describe('classifyDriftDirection', () => {
    it('should classify as stable for <5% change', () => {
      expect(classifyDriftDirection(0)).toBe('stable')
      expect(classifyDriftDirection(0.04)).toBe('stable')
      expect(classifyDriftDirection(-0.04)).toBe('stable')
      expect(classifyDriftDirection(0.049)).toBe('stable')
    })

    it('should classify as upward for >=5% positive change', () => {
      expect(classifyDriftDirection(0.05)).toBe('upward')
      expect(classifyDriftDirection(0.1)).toBe('upward')
      expect(classifyDriftDirection(0.5)).toBe('upward')
    })

    it('should classify as downward for >=5% negative change', () => {
      expect(classifyDriftDirection(-0.05)).toBe('downward')
      expect(classifyDriftDirection(-0.1)).toBe('downward')
      expect(classifyDriftDirection(-0.5)).toBe('downward')
    })
  })

  describe('buildDriftNarrative', () => {
    it('should generate upward narrative', () => {
      const narrative = buildDriftNarrative('measuredHelmholtzHz', 'upward', 0.1, 5)
      expect(narrative).toBe(
        'measuredHelmholtzHz shifted upward by 10.0% across 5 sequential observations'
      )
    })

    it('should generate downward narrative', () => {
      const narrative = buildDriftNarrative('measuredPeakHz', 'downward', -0.08, 4)
      expect(narrative).toBe(
        'measuredPeakHz shifted downward by 8.0% across 4 sequential observations'
      )
    })

    it('should generate stable narrative', () => {
      const narrative = buildDriftNarrative('measuredQ', 'stable', 0.02, 3)
      expect(narrative).toBe('measuredQ remained stable (2.0% variation) across 3 sequential observations')
    })
  })

  describe('groupArchivesByVariantTimeline', () => {
    it('should group archives by variant ID', () => {
      const archives = [
        createMockArchive('a1', { variantRefs: ['v1'] }),
        createMockArchive('a2', { variantRefs: ['v1'] }),
        createMockArchive('a3', { variantRefs: ['v2'] }),
      ]

      const groups = groupArchivesByVariantTimeline(archives)

      expect(groups.get('v1')?.length).toBe(2)
      expect(groups.get('v2')?.length).toBe(1)
    })

    it('should handle archives without variant refs', () => {
      const archives = [
        createMockArchive('a1', { variantRefs: undefined }),
        createMockArchive('a2', { variantRefs: [] }),
      ]

      const groups = groupArchivesByVariantTimeline(archives)

      expect(groups.get('__none__')?.length).toBe(2)
    })
  })

  describe('groupArchivesBySessionTimeline', () => {
    it('should group archives by session context', () => {
      const archives = [
        createMockArchive('a1', { sessionContext: 'session-A' }),
        createMockArchive('a2', { sessionContext: 'session-A' }),
        createMockArchive('a3', { sessionContext: 'session-B' }),
      ]

      const groups = groupArchivesBySessionTimeline(archives)

      expect(groups.get('session-A')?.length).toBe(2)
      expect(groups.get('session-B')?.length).toBe(1)
    })

    it('should handle archives without session context', () => {
      const archives = [
        createMockArchive('a1', { sessionContext: undefined }),
        createMockArchive('a2', { sessionContext: 'session-A' }),
      ]

      const groups = groupArchivesBySessionTimeline(archives)

      expect(groups.get('__none__')?.length).toBe(1)
      expect(groups.get('session-A')?.length).toBe(1)
    })
  })

  describe('buildDriftSequences', () => {
    it('should build chronological sequence from all archives', () => {
      const archives = [
        createMockArchive('a1', { timestamp: '2026-01-01T00:00:00Z' }),
        createMockArchive('a2', { timestamp: '2026-01-02T00:00:00Z' }),
        createMockArchive('a3', { timestamp: '2026-01-03T00:00:00Z' }),
      ]

      const sequences = buildDriftSequences(archives, 'chronological')

      expect(sequences.length).toBe(1)
      expect(sequences[0].contextType).toBe('chronological')
      expect(sequences[0].archiveCount).toBe(3)
    })

    it('should skip contexts with fewer than 3 archives', () => {
      const archives = [
        createMockArchive('a1', { variantRefs: ['v1'] }),
        createMockArchive('a2', { variantRefs: ['v1'] }),
      ]

      const sequences = buildDriftSequences(archives, 'variant')

      expect(sequences.length).toBe(0)
    })
  })

  describe('computeExperimentalDrift', () => {
    it('should compute drift for trackable fields', () => {
      const archives = [
        createMockArchive('a1', {
          timestamp: '2026-01-01T00:00:00Z',
          helmholtzHz: 100,
          peakHz: 200,
        }),
        createMockArchive('a2', {
          timestamp: '2026-01-02T00:00:00Z',
          helmholtzHz: 110,
          peakHz: 210,
        }),
        createMockArchive('a3', {
          timestamp: '2026-01-03T00:00:00Z',
          helmholtzHz: 120,
          peakHz: 220,
        }),
      ]

      const result = computeExperimentalDrift(archives, 'chronological')

      expect(result.drifts.length).toBeGreaterThan(0)
      expect(result.totalArchivesAnalyzed).toBe(3)
      expect(result.computedAtIso).toBeDefined()
    })

    it('should track insufficient contexts', () => {
      const archives = [
        createMockArchive('a1', { variantRefs: ['v1'] }),
        createMockArchive('a2', { variantRefs: ['v2'] }),
      ]

      const result = computeExperimentalDrift(archives, 'variant')

      expect(result.insufficientContexts.length).toBeGreaterThan(0)
    })

    it('should generate summaries by context', () => {
      const archives = [
        createMockArchive('a1', {
          timestamp: '2026-01-01T00:00:00Z',
          helmholtzHz: 100,
        }),
        createMockArchive('a2', {
          timestamp: '2026-01-02T00:00:00Z',
          helmholtzHz: 110,
        }),
        createMockArchive('a3', {
          timestamp: '2026-01-03T00:00:00Z',
          helmholtzHz: 120,
        }),
      ]

      const result = computeExperimentalDrift(archives, 'chronological')

      expect(result.summaries.length).toBe(1)
      expect(result.summaries[0].contextType).toBe('chronological')
    })
  })

  describe('filter utilities', () => {
    it('should filter drifts by direction', () => {
      const archives = [
        createMockArchive('a1', { timestamp: '2026-01-01T00:00:00Z', helmholtzHz: 100 }),
        createMockArchive('a2', { timestamp: '2026-01-02T00:00:00Z', helmholtzHz: 120 }),
        createMockArchive('a3', { timestamp: '2026-01-03T00:00:00Z', helmholtzHz: 140 }),
      ]

      const result = computeExperimentalDrift(archives, 'chronological')
      const upward = filterDriftsByDirection(result.drifts, 'upward')

      expect(upward.every((d) => d.direction === 'upward')).toBe(true)
    })

    it('should filter drifts by field', () => {
      const archives = [
        createMockArchive('a1', {
          timestamp: '2026-01-01T00:00:00Z',
          helmholtzHz: 100,
          peakHz: 200,
        }),
        createMockArchive('a2', {
          timestamp: '2026-01-02T00:00:00Z',
          helmholtzHz: 120,
          peakHz: 220,
        }),
        createMockArchive('a3', {
          timestamp: '2026-01-03T00:00:00Z',
          helmholtzHz: 140,
          peakHz: 240,
        }),
      ]

      const result = computeExperimentalDrift(archives, 'chronological')
      const helmholtz = filterDriftsByField(result.drifts, 'measuredHelmholtzHz')

      expect(helmholtz.every((d) => d.observedField === 'measuredHelmholtzHz')).toBe(true)
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
      'cause',
      'causes',
      'caused',
      'causation',
    ]

    it('should not use forbidden language in upward narrative', () => {
      const narrative = buildDriftNarrative('measuredHelmholtzHz', 'upward', 0.2, 5)

      for (const word of FORBIDDEN_WORDS) {
        expect(narrative.toLowerCase()).not.toContain(word)
      }
    })

    it('should not use forbidden language in downward narrative', () => {
      const narrative = buildDriftNarrative('measuredHelmholtzHz', 'downward', -0.15, 4)

      for (const word of FORBIDDEN_WORDS) {
        expect(narrative.toLowerCase()).not.toContain(word)
      }
    })

    it('should not use forbidden language in stable narrative', () => {
      const narrative = buildDriftNarrative('measuredQ', 'stable', 0.01, 3)

      for (const word of FORBIDDEN_WORDS) {
        expect(narrative.toLowerCase()).not.toContain(word)
      }
    })

    it('should use observational language in drift records', () => {
      const archives = [
        createMockArchive('a1', { timestamp: '2026-01-01T00:00:00Z', helmholtzHz: 100 }),
        createMockArchive('a2', { timestamp: '2026-01-02T00:00:00Z', helmholtzHz: 130 }),
        createMockArchive('a3', { timestamp: '2026-01-03T00:00:00Z', helmholtzHz: 160 }),
      ]

      const result = computeExperimentalDrift(archives, 'chronological')

      for (const drift of result.drifts) {
        for (const word of FORBIDDEN_WORDS) {
          expect(drift.narrative.toLowerCase()).not.toContain(word)
        }

        expect(drift.narrative).toMatch(/shifted|remained stable|observed|showed/)
      }
    })
  })

  describe('timeline point deltas', () => {
    it('should compute delta from previous point', () => {
      const archives = [
        createMockArchive('a1', { timestamp: '2026-01-01T00:00:00Z', helmholtzHz: 100 }),
        createMockArchive('a2', { timestamp: '2026-01-02T00:00:00Z', helmholtzHz: 110 }),
        createMockArchive('a3', { timestamp: '2026-01-03T00:00:00Z', helmholtzHz: 105 }),
      ]

      const result = computeExperimentalDrift(archives, 'chronological')
      const helmholtzDrift = result.drifts.find((d) => d.observedField === 'measuredHelmholtzHz')

      expect(helmholtzDrift).toBeDefined()
      expect(helmholtzDrift!.timelinePoints[0].deltaFromPrevious).toBeUndefined()
      expect(helmholtzDrift!.timelinePoints[1].deltaFromPrevious).toBe(10)
      expect(helmholtzDrift!.timelinePoints[2].deltaFromPrevious).toBe(-5)
    })

    it('should compute percent delta from previous point', () => {
      const archives = [
        createMockArchive('a1', { timestamp: '2026-01-01T00:00:00Z', helmholtzHz: 100 }),
        createMockArchive('a2', { timestamp: '2026-01-02T00:00:00Z', helmholtzHz: 110 }),
      ]

      const result = computeExperimentalDrift([
        ...archives,
        createMockArchive('a3', { timestamp: '2026-01-03T00:00:00Z', helmholtzHz: 120 }),
      ], 'chronological')

      const helmholtzDrift = result.drifts.find((d) => d.observedField === 'measuredHelmholtzHz')

      expect(helmholtzDrift!.timelinePoints[1].percentDeltaFromPrevious).toBeCloseTo(0.1)
    })
  })
})
