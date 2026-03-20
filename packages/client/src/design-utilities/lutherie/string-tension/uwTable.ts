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
import stringGaugeData from '@/data/string-gauges.json'

// ============================================================================
// DENSITY CONSTANTS (from JSON)
// ============================================================================

const STEEL_DENSITY = stringGaugeData.densities.steel_lb_in3
const NYLON_DENSITY = stringGaugeData.densities.nylon_lb_in3

// ============================================================================
// WOUND STRING TABLE (from JSON)
// Format: gauge → [nickel_wound, phosphor_bronze, 80_20_bronze] (lbs/in)
// ============================================================================

const WOUND_TABLE: Record<number, [number, number, number]> = Object.fromEntries(
  Object.entries(stringGaugeData.woundTable)
    .filter(([k]) => !k.startsWith('$'))
    .map(([k, v]) => [Number(k), v as [number, number, number]])
)

// Nylon wound (classical bass strings) — empirical approximation
const NYLON_WOUND_TABLE: Record<number, number> = Object.fromEntries(
  Object.entries(stringGaugeData.nylonWoundTable)
    .filter(([k]) => !k.startsWith('$'))
    .map(([k, v]) => [Number(k), v as number])
)

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
