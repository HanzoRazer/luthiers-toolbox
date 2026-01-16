import { describe, it, expect } from 'vitest'
import { findSiblingPeaksRelpath } from '../packHelpers'

describe('findSiblingPeaksRelpath', () => {
  it('returns analysis.json path for spectrum.csv', () => {
    expect(findSiblingPeaksRelpath('spectra/points/A1/spectrum.csv'))
      .toBe('spectra/points/A1/analysis.json')
  })

  it('handles deeper nested paths', () => {
    expect(findSiblingPeaksRelpath('data/session/spectra/points/B2/spectrum.csv'))
      .toBe('data/session/spectra/points/B2/analysis.json')
  })

  it('returns null for non-spectrum.csv paths', () => {
    expect(findSiblingPeaksRelpath('spectra/points/A1/coherence.csv')).toBeNull()
    expect(findSiblingPeaksRelpath('spectra/points/A1/spectrum.json')).toBeNull()
    expect(findSiblingPeaksRelpath('some/other/file.csv')).toBeNull()
  })

  it('returns null for empty or undefined input', () => {
    expect(findSiblingPeaksRelpath('')).toBeNull()
    expect(findSiblingPeaksRelpath(undefined as any)).toBeNull()
    expect(findSiblingPeaksRelpath(null as any)).toBeNull()
  })

  it('handles edge case: just spectrum.csv', () => {
    expect(findSiblingPeaksRelpath('spectrum.csv')).toBeNull()
    expect(findSiblingPeaksRelpath('/spectrum.csv')).toBe('/analysis.json')
  })
})
