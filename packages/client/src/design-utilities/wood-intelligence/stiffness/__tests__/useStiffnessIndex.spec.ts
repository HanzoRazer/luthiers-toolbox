/**
 * BR-044A — frontend radiation-ratio reproduction proof.
 *
 * EVIDENCE ONLY. This spec changes no production behavior and asserts nothing
 * about what the frontend *should* do. It records what the shipped code does
 * now, so BR-044 can be classified from repository evidence rather than from
 * static reading.
 *
 * Two scales are in play and the distinction is the whole point:
 *
 *   canonical (BR-043, backend `TonewoodEntry.radiation_ratio`)  rr = c / rho
 *   frontend-local (`calcRadiationRatio`)                        rr = (c / rho) * 1000
 *
 * Characterisation assertions below are marked CHARACTERISATION. They pin
 * current behaviour and must NOT be read as desired behaviour — BR-044B may
 * legitimately invert them.
 *
 * See docs/remediation/BR-044A_FRONTEND_RADIATION_RATIO_PROOF.md
 */

import { describe, expect, it } from 'vitest'

import {
  calcRadiationRatio,
  calcSpeedOfSound,
  computeIndices,
} from '../useStiffnessIndex'
import type { TonewoodEntry } from '../tonewoodData'

/** Thresholds read from the shipped rating/colour branches (soundboardRating, rrColor). */
const BANDS = { excellent: 12.0, good: 10.5, acceptable: 9.0 } as const

/**
 * Independent reference implementation of the canonical BR-043 contract.
 * Deliberately NOT importing the frontend helper, so this cannot inherit the
 * defect it is meant to measure.
 */
function expectedUnscaledRadiationRatio(densityKgM3: number, modulusGPa: number): number {
  const c = Math.sqrt((modulusGPa * 1e9) / densityKgM3)
  return c / densityKgM3
}

function makeTonewoodFixture(
  densityKgM3: number,
  modulusGPa: number | null,
  name = 'fixture',
): TonewoodEntry {
  return {
    id: name.toLowerCase().replace(/\s+/g, '_'),
    name,
    densityKgM3,
    moeGpa: modulusGPa,
    speedOfSoundMs: null,
    parts: ['soundboard'],
  } as TonewoodEntry
}

/** Controlled fixtures. These are test data, not species-quality claims. */
const LOW = { rho: 890.0, e: 18.41, label: 'dense/low-rr' }
const MID = { rho: 500.0, e: 11.0, label: 'mid-rr' }
const HIGH = { rho: 350.0, e: 10.5, label: 'light/high-rr' }

describe('BR-044A · TC-01 producer magnitude', () => {
  it('CHARACTERISATION: emits ~11,870 for rho 415 / E 10.07, not ~11.87', () => {
    const c = calcSpeedOfSound(10.07, 415.0)
    const frontend = calcRadiationRatio(c, 415.0)
    const canonical = expectedUnscaledRadiationRatio(415.0, 10.07)

    expect(canonical).toBeCloseTo(11.87, 2)
    expect(frontend).toBeCloseTo(11870, 0)
    // The scale distinction, stated explicitly:
    expect(frontend).not.toBeCloseTo(canonical, 2)
  })
})

describe('BR-044A · TC-02 formula identity', () => {
  it('CHARACTERISATION: implements (c / rho) * 1000, established by arithmetic not labels', () => {
    const cases: Array<[number, number]> = [
      [415.0, 10.07],
      [350.0, 10.5],
      [890.0, 18.41],
    ]
    for (const [rho, e] of cases) {
      const c = calcSpeedOfSound(e, rho)
      expect(calcRadiationRatio(c, rho)).toBeCloseTo((c / rho) * 1000, 6)
      expect(calcRadiationRatio(c, rho)).not.toBeCloseTo(c / rho, 6)
    }
  })
})

describe('BR-044A · TC-03 threshold-scale comparison', () => {
  it('CHARACTERISATION: every produced value sits above the highest band', () => {
    for (const { rho, e } of [LOW, MID, HIGH]) {
      const rr = calcRadiationRatio(calcSpeedOfSound(e, rho), rho)
      expect(rr).toBeGreaterThan(BANDS.excellent)
      expect(rr).toBeGreaterThan(1000) // three orders above the band scale
    }
  })
})

describe('BR-044A · TC-04 representative low/mid/high woods', () => {
  it('canonical arithmetic separates the three fixtures across bands', () => {
    const canon = [LOW, MID, HIGH].map((f) => expectedUnscaledRadiationRatio(f.rho, f.e))
    // Strictly increasing — the fixtures genuinely straddle the bands.
    expect(canon[0]).toBeLessThan(canon[1])
    expect(canon[1]).toBeLessThan(canon[2])
    expect(canon[0]).toBeLessThan(BANDS.acceptable)
    expect(canon[2]).toBeGreaterThan(BANDS.excellent)
  })

  it('CHARACTERISATION: the shipped producer collapses all three to one rating', () => {
    const ratings = [LOW, MID, HIGH].map(
      (f) => computeIndices(makeTonewoodFixture(f.rho, f.e, f.label)).soundboardRating,
    )
    expect(ratings).toEqual(['Excellent', 'Excellent', 'Excellent'])
    expect(new Set(ratings).size).toBe(1) // zero discriminating power
  })
})

describe('BR-044A · TC-05 backend parity comparison', () => {
  it('CHARACTERISATION: frontend / canonical ratio is exactly 1000', () => {
    for (const { rho, e } of [LOW, MID, HIGH]) {
      const frontend = calcRadiationRatio(calcSpeedOfSound(e, rho), rho)
      const canonical = expectedUnscaledRadiationRatio(rho, e)
      expect(frontend / canonical).toBeCloseTo(1000, 6)
    }
  })
})

describe('BR-044A · TC-06 missing data', () => {
  it('CHARACTERISATION: absent MOE yields null indices and null rating', () => {
    const indices = computeIndices(makeTonewoodFixture(415.0, null, 'no-moe'))
    expect(indices.radiationRatio).toBeNull()
    expect(indices.soundboardRating).toBeNull()
  })
})
