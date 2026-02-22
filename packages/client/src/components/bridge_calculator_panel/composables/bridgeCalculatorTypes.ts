/**
 * BridgeCalculatorPanel types and constants.
 */

export type UnitMode = 'mm' | 'inch'

export type UiFieldKey = 'scale' | 'spread' | 'compTreble' | 'compBass' | 'slotWidth' | 'slotLength'

export interface FamilyPreset {
  id: string
  label: string
  scaleLength: number
  stringSpread: number
  compTreble: number
  compBass: number
  slotWidth: number
  slotLength: number
}

export interface AdjustmentPreset {
  id: string
  label: string
  compAdjust?: number
  trebleAdjust?: number
  bassAdjust?: number
}

export interface Point2D {
  x: number
  y: number
}

export interface BridgeModel {
  units: UnitMode
  scaleLength: number
  stringSpread: number
  compTreble: number
  compBass: number
  slotWidth: number
  slotLength: number
  angleDeg: number
  endpoints: {
    treble: Point2D
    bass: Point2D
  }
  slotPolygon: Point2D[]
}

/** Fallback family presets when API unavailable */
export const FALLBACK_FAMILIES: FamilyPreset[] = [
  { id: 'les_paul', label: 'Les Paul (24.75")', scaleLength: 628.65, stringSpread: 52, compTreble: 1.5, compBass: 3, slotWidth: 3, slotLength: 75 },
  { id: 'strat_tele', label: 'Strat/Tele (25.5")', scaleLength: 647.7, stringSpread: 52.5, compTreble: 2, compBass: 3.5, slotWidth: 3, slotLength: 75 },
  { id: 'om', label: 'OM Acoustic (25.4")', scaleLength: 645.16, stringSpread: 54, compTreble: 2, compBass: 4.2, slotWidth: 3.2, slotLength: 80 },
  { id: 'dread', label: 'Dreadnought (25.4")', scaleLength: 645.16, stringSpread: 54, compTreble: 2, compBass: 4.5, slotWidth: 3.2, slotLength: 80 },
  { id: 'archtop', label: 'Archtop (25.0")', scaleLength: 635, stringSpread: 52, compTreble: 1.8, compBass: 3.2, slotWidth: 3, slotLength: 75 }
]

/** Fallback gauge presets */
export const FALLBACK_GAUGES: AdjustmentPreset[] = [
  { id: 'light', label: 'Light Gauge', trebleAdjust: -0.3, bassAdjust: -0.3 },
  { id: 'medium', label: 'Medium Gauge', trebleAdjust: 0, bassAdjust: 0 },
  { id: 'heavy', label: 'Heavy Gauge', trebleAdjust: 0.3, bassAdjust: 0.4 }
]

/** Fallback action presets */
export const FALLBACK_ACTIONS: AdjustmentPreset[] = [
  { id: 'low', label: 'Low Action', trebleAdjust: -0.2, bassAdjust: -0.2 },
  { id: 'standard', label: 'Standard Action', trebleAdjust: 0, bassAdjust: 0 },
  { id: 'high', label: 'High Action', trebleAdjust: 0.3, bassAdjust: 0.4 }
]

/** SVG padding for viewbox calculation */
export const SVG_PADDING = 10
