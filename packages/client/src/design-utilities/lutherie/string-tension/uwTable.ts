/**
 * String Unit Weight Reference Table
 *
 * The Production Shop — String Tension Calculator
 *
 * Sources:
 *   Plain steel, nylon: derived from material density + gauge diameter
 *     steel ρ = 0.2836 lb/in³, nylon ρ = 0.0412 lb/in³
 *   Wound strings: D'Addario published unit weight data
 *     [nickel_wound, phosphor_bronze, 80_20_bronze] per gauge
 *   Nylon wound (classical bass): empirical approximation
 *   Orchestral/lute/dulcimer: empirical UW calibrated to manufacturer
 *     medium-tension sets (Thomastik-Infeld Dominant, Savarez, etc.)
 *
 * Validated against:
 *   Achilles, D. "Tensions of Guitar Strings."
 *   Physics 398 EMI, UIUC, 2000.
 *   (Measured µ values used as uwOverride in validated presets)
 *
 * Unit weight formula for plain strings:
 *   UW = (π/4) × (gauge_in)² × density_lb_in3
 *   where gauge_in = gauge_thou / 1000
 */

import type { StringMaterial } from './types'

// ============================================================================
// DENSITY CONSTANTS
// ============================================================================

const STEEL_DENSITY = 0.2836   // lb/in³
const NYLON_DENSITY = 0.0412   // lb/in³

// ============================================================================
// WOUND STRING TABLE
// Format: gauge → [nickel_wound, phosphor_bronze, 80_20_bronze] (lbs/in)
// ============================================================================

const WOUND_TABLE: Record<number, [number, number, number]> = {
  17: [6.11e-5, 6.28e-5, 6.19e-5],
  20: [7.54e-5, 7.76e-5, 7.65e-5],
  22: [9.26e-5, 9.53e-5, 9.39e-5],
  24: [1.090e-4, 1.122e-4, 1.106e-4],
  26: [1.270e-4, 1.307e-4, 1.288e-4],
  28: [1.468e-4, 1.510e-4, 1.489e-4],
  30: [1.680e-4, 1.729e-4, 1.704e-4],
  32: [1.917e-4, 1.972e-4, 1.944e-4],
  34: [2.167e-4, 2.229e-4, 2.198e-4],
  36: [2.432e-4, 2.502e-4, 2.467e-4],
  38: [2.715e-4, 2.793e-4, 2.754e-4],
  40: [3.011e-4, 3.098e-4, 3.054e-4],
  42: [3.330e-4, 3.426e-4, 3.378e-4],
  44: [3.660e-4, 3.766e-4, 3.713e-4],
  46: [4.001e-4, 4.117e-4, 4.059e-4],
  48: [4.359e-4, 4.486e-4, 4.422e-4],
  52: [5.112e-4, 5.260e-4, 5.186e-4],
  54: [5.516e-4, 5.676e-4, 5.596e-4],
  56: [5.938e-4, 6.110e-4, 6.023e-4],
  59: [6.601e-4, 6.793e-4, 6.696e-4],
  60: [6.841e-4, 7.038e-4, 6.939e-4],
  64: [7.796e-4, 8.024e-4, 7.909e-4],
  68: [8.817e-4, 9.073e-4, 8.944e-4],
  72: [9.921e-4, 1.021e-3, 1.006e-3],
  80: [1.224e-3, 1.260e-3, 1.242e-3],
  90: [1.551e-3, 1.596e-3, 1.573e-3],
  100: [1.914e-3, 1.970e-3, 1.942e-3],
  105: [2.107e-3, 2.169e-3, 2.138e-3],
  110: [2.308e-3, 2.377e-3, 2.342e-3],
  130: [3.234e-3, 3.329e-3, 3.281e-3],
}

// Nylon wound (classical bass strings) — empirical approximation
const NYLON_WOUND_TABLE: Record<number, number> = {
  27: 6.5e-5,
  30: 8.6e-5,
  34: 1.09e-4,
  38: 1.36e-4,
  42: 1.67e-4,
  46: 2.02e-4,
}

// ============================================================================
// LINEAR INTERPOLATION HELPER
// ============================================================================

function interpolate(gauge: number, table: Record<number, number>): number
function interpolate(gauge: number, table: Record<number, [number, number, number]>): [number, number, number]
function interpolate(
  gauge: number,
  table: Record<number, number | [number, number, number]>
): number | [number, number, number] {
  const keys = Object.keys(table).map(Number).sort((a, b) => a - b)
  if (gauge <= keys[0]) return table[keys[0]]
  if (gauge >= keys[keys.length - 1]) return table[keys[keys.length - 1]]

  const lo = keys.filter(k => k <= gauge).pop()!
  const hi = keys.find(k => k > gauge)!
  const t = (gauge - lo) / (hi - lo)
  const lv = table[lo]
  const hv = table[hi]

  if (Array.isArray(lv) && Array.isArray(hv)) {
    return lv.map((v, i) => v * (1 - t) + (hv as [number, number, number])[i] * t) as [number, number, number]
  }
  return (lv as number) * (1 - t) + (hv as number) * t
}

// ============================================================================
// UNIT WEIGHT LOOKUP
// ============================================================================

/**
 * Calculate unit weight (lbs/in) for a plain string from density.
 */
export function calcPlainUW(gaugeThou: number, density: number): number {
  const gaugeIn = gaugeThou / 1000
  return (Math.PI / 4) * gaugeIn * gaugeIn * density
}

/**
 * Look up unit weight (lbs/in) for a given gauge and material.
 * Uses linear interpolation between table entries.
 *
 * For wound strings, interpolates within the D'Addario reference table.
 * For plain strings, derives from density formula.
 */
export function getUnitWeight(gaugeThou: number, material: StringMaterial): number {
  switch (material) {
    case 'plain_steel':
      return calcPlainUW(gaugeThou, STEEL_DENSITY)

    case 'nylon_treble':
      return calcPlainUW(gaugeThou, NYLON_DENSITY)

    case 'nylon_wound': {
      return interpolate(gaugeThou, NYLON_WOUND_TABLE) as number
    }

    case 'nickel_wound': {
      const row = interpolate(gaugeThou, WOUND_TABLE) as [number, number, number]
      return row[0]
    }

    case 'phosphor_bronze': {
      const row = interpolate(gaugeThou, WOUND_TABLE) as [number, number, number]
      return row[1]
    }

    case '80_20_bronze': {
      const row = interpolate(gaugeThou, WOUND_TABLE) as [number, number, number]
      return row[2]
    }
  }
}
