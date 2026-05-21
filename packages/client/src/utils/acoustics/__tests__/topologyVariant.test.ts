/**
 * Topology Variant Utilities Tests
 *
 * Dev Order 66: Test coverage for experimental topology variant framework
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  generateTopologyVariantId,
  createTopologyVariant,
  validateTopologyVariant,
  getTopologyVariantDisplayLabel,
  getTopologyVariantStrategySummary,
  createTopologyVariantSummary,
  formatVariantTimestamp,
  checkSharedTopologyVariant,
  getCategoryDisplayLabel,
  sortTopologyVariantsByDate,
  filterVariantsByCategory,
  filterVariantsByTag,
  getAllExperimentTags,
} from '../topologyVariant'
import type { TopologyVariant } from '@/types/acoustics/topologyVariant'

describe('topologyVariant utilities', () => {
  describe('generateTopologyVariantId', () => {
    beforeEach(() => {
      vi.useFakeTimers()
    })

    afterEach(() => {
      vi.useRealTimers()
    })

    it('generates ID with correct format', () => {
      vi.setSystemTime(new Date('2026-05-20T14:30:45'))
      const id = generateTopologyVariantId()
      expect(id).toBe('topology-variant-20260520-143045')
    })

    it('pads single-digit values', () => {
      vi.setSystemTime(new Date('2026-01-05T09:05:03'))
      const id = generateTopologyVariantId()
      expect(id).toBe('topology-variant-20260105-090503')
    })
  })

  describe('createTopologyVariant', () => {
    beforeEach(() => {
      vi.useFakeTimers()
      vi.setSystemTime(new Date('2026-05-20T12:00:00'))
    })

    afterEach(() => {
      vi.useRealTimers()
    })

    it('creates variant with required fields', () => {
      const variant = createTopologyVariant('Carlos Jumbo dual-spiral')

      expect(variant.schemaVersion).toBe('topology-variant.v1')
      expect(variant.variantId).toBe('topology-variant-20260520-120000')
      expect(variant.title).toBe('Carlos Jumbo dual-spiral')
      // Timestamp is ISO so compare date prefix (timezone-agnostic)
      expect(variant.createdAtIso).toMatch(/^2026-05-20T/)
    })

    it('accepts overrides', () => {
      const variant = createTopologyVariant('Test Variant', {
        category: 'aperture',
        bodyFamily: 'Jumbo',
        apertureStrategy: 'triple spiral',
        experimentTags: ['experiment-1', 'test'],
      })

      expect(variant.title).toBe('Test Variant')
      expect(variant.category).toBe('aperture')
      expect(variant.bodyFamily).toBe('Jumbo')
      expect(variant.apertureStrategy).toBe('triple spiral')
      expect(variant.experimentTags).toEqual(['experiment-1', 'test'])
    })
  })

  describe('validateTopologyVariant', () => {
    const validVariant: TopologyVariant = {
      schemaVersion: 'topology-variant.v1',
      variantId: 'topology-variant-20260520-120000',
      title: 'Test Variant',
      createdAtIso: '2026-05-20T12:00:00.000Z',
    }

    it('validates a complete variant', () => {
      const result = validateTopologyVariant(validVariant)
      expect(result.valid).toBe(true)
      expect(result.errors).toHaveLength(0)
    })

    it('rejects non-object data', () => {
      const result = validateTopologyVariant(null)
      expect(result.valid).toBe(false)
      expect(result.errors).toContain('Data must be an object')
    })

    it('rejects invalid schemaVersion', () => {
      const result = validateTopologyVariant({
        ...validVariant,
        schemaVersion: 'wrong-version',
      })
      expect(result.valid).toBe(false)
      expect(result.errors[0]).toContain('schemaVersion')
    })

    it('rejects missing title', () => {
      const result = validateTopologyVariant({
        ...validVariant,
        title: '',
      })
      expect(result.valid).toBe(false)
      expect(result.errors).toContain('Missing or invalid title')
    })

    it('rejects invalid category', () => {
      const result = validateTopologyVariant({
        ...validVariant,
        category: 'invalid-category',
      })
      expect(result.valid).toBe(false)
      expect(result.errors[0]).toContain('Invalid category')
    })

    it('validates all category values', () => {
      const categories = ['body', 'shell', 'aperture', 'bracing', 'bridge', 'tornavoz', 'combined']
      for (const category of categories) {
        const result = validateTopologyVariant({ ...validVariant, category })
        expect(result.valid).toBe(true)
      }
    })

    it('rejects non-string strategy fields', () => {
      const result = validateTopologyVariant({
        ...validVariant,
        bodyFamily: 123,
      })
      expect(result.valid).toBe(false)
      expect(result.errors).toContain('bodyFamily must be a string')
    })

    it('rejects non-array experimentTags', () => {
      const result = validateTopologyVariant({
        ...validVariant,
        experimentTags: 'not-an-array',
      })
      expect(result.valid).toBe(false)
      expect(result.errors).toContain('experimentTags must be an array')
    })

    it('warns on sparse variant without strategies or description', () => {
      const result = validateTopologyVariant(validVariant)
      expect(result.valid).toBe(true)
      expect(result.warnings).toContain('Variant has no strategy descriptors or description')
    })

    it('does not warn when variant has strategies', () => {
      const result = validateTopologyVariant({
        ...validVariant,
        bodyFamily: 'Carlos Jumbo',
      })
      expect(result.valid).toBe(true)
      expect(result.warnings).toHaveLength(0)
    })
  })

  describe('getTopologyVariantDisplayLabel', () => {
    it('returns title when present', () => {
      const variant: TopologyVariant = {
        schemaVersion: 'topology-variant.v1',
        variantId: 'topology-variant-20260520-120000',
        title: 'My Variant',
        createdAtIso: '2026-05-20T12:00:00.000Z',
      }
      expect(getTopologyVariantDisplayLabel(variant)).toBe('My Variant')
    })

    it('returns variantId when title is empty', () => {
      const variant: TopologyVariant = {
        schemaVersion: 'topology-variant.v1',
        variantId: 'topology-variant-20260520-120000',
        title: '',
        createdAtIso: '2026-05-20T12:00:00.000Z',
      }
      expect(getTopologyVariantDisplayLabel(variant)).toBe('topology-variant-20260520-120000')
    })
  })

  describe('getTopologyVariantStrategySummary', () => {
    it('returns strategy summary from multiple fields', () => {
      const variant: TopologyVariant = {
        schemaVersion: 'topology-variant.v1',
        variantId: 'test',
        title: 'Test',
        createdAtIso: '2026-05-20T12:00:00.000Z',
        bodyFamily: 'Carlos Jumbo',
        apertureStrategy: 'dual-spiral',
      }
      const summary = getTopologyVariantStrategySummary(variant)
      expect(summary).toBe('Carlos Jumbo · dual-spiral')
    })

    it('returns truncated description when no strategies', () => {
      const variant: TopologyVariant = {
        schemaVersion: 'topology-variant.v1',
        variantId: 'test',
        title: 'Test',
        createdAtIso: '2026-05-20T12:00:00.000Z',
        description: 'A very long description that exceeds fifty characters and should be truncated',
      }
      const summary = getTopologyVariantStrategySummary(variant)
      expect(summary).toHaveLength(53)
      expect(summary.endsWith('...')).toBe(true)
    })

    it('returns fallback message when empty', () => {
      const variant: TopologyVariant = {
        schemaVersion: 'topology-variant.v1',
        variantId: 'test',
        title: 'Test',
        createdAtIso: '2026-05-20T12:00:00.000Z',
      }
      expect(getTopologyVariantStrategySummary(variant)).toBe('No strategies defined')
    })
  })

  describe('createTopologyVariantSummary', () => {
    it('creates summary from variant', () => {
      const variant: TopologyVariant = {
        schemaVersion: 'topology-variant.v1',
        variantId: 'topology-variant-20260520-120000',
        title: 'Test Variant',
        createdAtIso: '2026-05-20T12:00:00.000Z',
        category: 'aperture',
        description: 'Test description',
        experimentTags: ['tag1', 'tag2'],
      }
      const summary = createTopologyVariantSummary(variant)

      expect(summary.variantId).toBe('topology-variant-20260520-120000')
      expect(summary.title).toBe('Test Variant')
      expect(summary.category).toBe('aperture')
      expect(summary.tagCount).toBe(2)
      expect(summary.hasDescription).toBe(true)
    })
  })

  describe('formatVariantTimestamp', () => {
    it('formats valid ISO timestamp', () => {
      const formatted = formatVariantTimestamp('2026-05-20T12:00:00.000Z')
      expect(formatted).toContain('2026')
      expect(formatted).toContain('May')
    })

    it('returns Unknown for invalid timestamp', () => {
      expect(formatVariantTimestamp('invalid')).toBe('Unknown')
      expect(formatVariantTimestamp('')).toBe('Unknown')
    })
  })

  describe('checkSharedTopologyVariant', () => {
    it('detects shared variants', () => {
      const result = checkSharedTopologyVariant(
        ['variant-1', 'variant-2'],
        ['variant-2', 'variant-3']
      )
      expect(result.shared).toBe(true)
      expect(result.sharedIds).toEqual(['variant-2'])
    })

    it('returns false when no shared variants', () => {
      const result = checkSharedTopologyVariant(
        ['variant-1'],
        ['variant-2']
      )
      expect(result.shared).toBe(false)
      expect(result.sharedIds).toEqual([])
    })

    it('handles undefined refs', () => {
      expect(checkSharedTopologyVariant(undefined, ['variant-1'])).toEqual({
        shared: false,
        sharedIds: [],
      })
      expect(checkSharedTopologyVariant(['variant-1'], undefined)).toEqual({
        shared: false,
        sharedIds: [],
      })
    })

    it('handles empty arrays', () => {
      expect(checkSharedTopologyVariant([], ['variant-1'])).toEqual({
        shared: false,
        sharedIds: [],
      })
    })
  })

  describe('getCategoryDisplayLabel', () => {
    it('returns display labels for all categories', () => {
      expect(getCategoryDisplayLabel('body')).toBe('Body')
      expect(getCategoryDisplayLabel('shell')).toBe('Shell/Radius')
      expect(getCategoryDisplayLabel('aperture')).toBe('Aperture')
      expect(getCategoryDisplayLabel('bracing')).toBe('Bracing')
      expect(getCategoryDisplayLabel('bridge')).toBe('Bridge/Plate')
      expect(getCategoryDisplayLabel('tornavoz')).toBe('Tornavoz/Liner')
      expect(getCategoryDisplayLabel('combined')).toBe('Combined')
    })

    it('returns Uncategorized for undefined', () => {
      expect(getCategoryDisplayLabel(undefined)).toBe('Uncategorized')
    })
  })

  describe('sortTopologyVariantsByDate', () => {
    it('sorts by date descending (newest first)', () => {
      const variants: TopologyVariant[] = [
        { schemaVersion: 'topology-variant.v1', variantId: 'old', title: 'Old', createdAtIso: '2026-01-01T00:00:00Z' },
        { schemaVersion: 'topology-variant.v1', variantId: 'new', title: 'New', createdAtIso: '2026-05-20T00:00:00Z' },
        { schemaVersion: 'topology-variant.v1', variantId: 'mid', title: 'Mid', createdAtIso: '2026-03-15T00:00:00Z' },
      ]
      const sorted = sortTopologyVariantsByDate(variants)

      expect(sorted[0].variantId).toBe('new')
      expect(sorted[1].variantId).toBe('mid')
      expect(sorted[2].variantId).toBe('old')
    })

    it('handles invalid timestamps', () => {
      const variants: TopologyVariant[] = [
        { schemaVersion: 'topology-variant.v1', variantId: 'valid', title: 'Valid', createdAtIso: '2026-05-20T00:00:00Z' },
        { schemaVersion: 'topology-variant.v1', variantId: 'invalid', title: 'Invalid', createdAtIso: 'invalid' },
      ]
      const sorted = sortTopologyVariantsByDate(variants)

      expect(sorted[0].variantId).toBe('valid')
      expect(sorted[1].variantId).toBe('invalid')
    })
  })

  describe('filterVariantsByCategory', () => {
    it('filters by category', () => {
      const variants: TopologyVariant[] = [
        { schemaVersion: 'topology-variant.v1', variantId: '1', title: 'A', createdAtIso: '', category: 'aperture' },
        { schemaVersion: 'topology-variant.v1', variantId: '2', title: 'B', createdAtIso: '', category: 'bracing' },
        { schemaVersion: 'topology-variant.v1', variantId: '3', title: 'C', createdAtIso: '', category: 'aperture' },
      ]
      const filtered = filterVariantsByCategory(variants, 'aperture')

      expect(filtered).toHaveLength(2)
      expect(filtered[0].variantId).toBe('1')
      expect(filtered[1].variantId).toBe('3')
    })
  })

  describe('filterVariantsByTag', () => {
    it('filters by tag substring match', () => {
      const variants: TopologyVariant[] = [
        { schemaVersion: 'topology-variant.v1', variantId: '1', title: 'A', createdAtIso: '', experimentTags: ['experiment-1', 'test'] },
        { schemaVersion: 'topology-variant.v1', variantId: '2', title: 'B', createdAtIso: '', experimentTags: ['production'] },
        { schemaVersion: 'topology-variant.v1', variantId: '3', title: 'C', createdAtIso: '', experimentTags: ['experiment-2'] },
      ]
      const filtered = filterVariantsByTag(variants, 'experiment')

      expect(filtered).toHaveLength(2)
      expect(filtered[0].variantId).toBe('1')
      expect(filtered[1].variantId).toBe('3')
    })

    it('is case-insensitive', () => {
      const variants: TopologyVariant[] = [
        { schemaVersion: 'topology-variant.v1', variantId: '1', title: 'A', createdAtIso: '', experimentTags: ['TEST'] },
      ]
      const filtered = filterVariantsByTag(variants, 'test')

      expect(filtered).toHaveLength(1)
    })
  })

  describe('getAllExperimentTags', () => {
    it('collects unique tags sorted alphabetically', () => {
      const variants: TopologyVariant[] = [
        { schemaVersion: 'topology-variant.v1', variantId: '1', title: 'A', createdAtIso: '', experimentTags: ['zebra', 'apple'] },
        { schemaVersion: 'topology-variant.v1', variantId: '2', title: 'B', createdAtIso: '', experimentTags: ['apple', 'mango'] },
      ]
      const tags = getAllExperimentTags(variants)

      expect(tags).toEqual(['apple', 'mango', 'zebra'])
    })

    it('handles variants without tags', () => {
      const variants: TopologyVariant[] = [
        { schemaVersion: 'topology-variant.v1', variantId: '1', title: 'A', createdAtIso: '' },
        { schemaVersion: 'topology-variant.v1', variantId: '2', title: 'B', createdAtIso: '', experimentTags: ['test'] },
      ]
      const tags = getAllExperimentTags(variants)

      expect(tags).toEqual(['test'])
    })
  })
})
