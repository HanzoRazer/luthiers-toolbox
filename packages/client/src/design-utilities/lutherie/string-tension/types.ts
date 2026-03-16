/**
 * String Tension Calculator — Type Definitions
 *
 * The Production Shop
 * Part of the Lutherie Geometry calculator suite (CalculatorHub)
 *
 * Physics: T = UW × (2LF)² / 386.4
 *   T   = tension (lbs)
 *   UW  = unit weight (lbs/in)
 *   L   = vibrating length / scale length (in)
 *   F   = frequency (Hz)
 *   386.4 = gravitational constant in in/s²
 */

// ============================================================================
// STRING MATERIALS
// ============================================================================

export type StringMaterial =
  | 'plain_steel'
  | 'nickel_wound'
  | 'phosphor_bronze'
  | '80_20_bronze'
  | 'nylon_treble'
  | 'nylon_wound'

export interface MaterialInfo {
  id: StringMaterial
  label: string
  /** Whether this material uses the calculated (density-based) UW path */
  calculated: boolean
}

export const MATERIALS: MaterialInfo[] = [
  { id: 'plain_steel',      label: 'Plain steel',      calculated: true },
  { id: 'nickel_wound',     label: 'Nickel wound',     calculated: true },
  { id: 'phosphor_bronze',  label: 'Phos. bronze',     calculated: true },
  { id: '80_20_bronze',     label: '80/20 bronze',     calculated: true },
  { id: 'nylon_treble',     label: 'Nylon treble',     calculated: true },
  { id: 'nylon_wound',      label: 'Nylon wound',      calculated: true },
]

// ============================================================================
// INSTRUMENT TYPES
// ============================================================================

export type InstrumentType =
  | 'acoustic_pin'      // flat-top acoustic with pin bridge — Carruth thresholds apply
  | 'acoustic_classical'
  | 'electric'
  | 'bass'
  | 'mandolin'
  | 'ukulele'
  | 'banjo'
  | 'orchestral'
  | 'other'

export interface InstrumentTypeInfo {
  id: InstrumentType
  label: string
  /** Whether acoustic pin-bridge break angle thresholds (Carruth) apply */
  useCarruthThresholds: boolean
  /** Default break angle for structural output when no geometry is provided */
  defaultBreakAngleDeg: number
}

export const INSTRUMENT_TYPES: InstrumentTypeInfo[] = [
  { id: 'acoustic_pin',      label: 'Acoustic (pin bridge)',   useCarruthThresholds: true,  defaultBreakAngleDeg: 20 },
  { id: 'acoustic_classical',label: 'Classical / tied bridge', useCarruthThresholds: false, defaultBreakAngleDeg: 10 },
  { id: 'electric',          label: 'Electric',                useCarruthThresholds: false, defaultBreakAngleDeg: 10 },
  { id: 'bass',              label: 'Bass',                    useCarruthThresholds: false, defaultBreakAngleDeg: 8  },
  { id: 'mandolin',          label: 'Mandolin',                useCarruthThresholds: false, defaultBreakAngleDeg: 12 },
  { id: 'ukulele',           label: 'Ukulele',                 useCarruthThresholds: false, defaultBreakAngleDeg: 8  },
  { id: 'banjo',             label: 'Banjo',                   useCarruthThresholds: false, defaultBreakAngleDeg: 6  },
  { id: 'orchestral',        label: 'Orchestral (bowed)',      useCarruthThresholds: false, defaultBreakAngleDeg: 15 },
  { id: 'other',             label: 'Other / custom',          useCarruthThresholds: false, defaultBreakAngleDeg: 5  },
]

// ============================================================================
// PER-STRING SPEC
// ============================================================================

export type NoteName = 'C' | 'C#' | 'D' | 'D#' | 'E' | 'F' | 'F#' | 'G' | 'G#' | 'A' | 'A#' | 'B'

export interface StringSpec {
  /** Unique identifier within the set */
  id: number
  /** Note name */
  note: NoteName
  /** Octave (scientific pitch notation) */
  octave: number
  /** Gauge in thousandths of an inch (e.g. 9 = .009") */
  gauge: number
  /** String material */
  material: StringMaterial
  /**
   * Per-string scale length (inches). Used when multiScale = true.
   * When multiScale = false, the global scaleLength overrides this.
   */
  scaleLength: number
  /**
   * Unit weight override (lbs/in). When set, bypasses calculated UW.
   * Used for orchestral, lute, dulcimer, and validated reference sets.
   * Set to undefined to use the calculated value.
   */
  uwOverride?: number
  /**
   * Source label for uwOverride — shown as tooltip/footnote in UI.
   * e.g. "Achilles 2000 measured µ" or "Thomastik-Infeld Dominant ref"
   */
  uwSource?: string
}

// ============================================================================
// PER-STRING RESULT
// ============================================================================

export interface StringResult {
  /** String index (matches StringSpec.id) */
  id: number
  /** Computed tension in lbs */
  tensionLbs: number
  /** Computed tension in Newtons */
  tensionN: number
  /** Computed tension in kg-force */
  tensionKgf: number
  /** Unit weight used (lbs/in) — whether calculated or overridden */
  unitWeight: number
  /** True when uwOverride was used instead of calculated UW */
  isOverride: boolean
  /** Fundamental frequency (Hz) */
  frequency: number
  /** Effective scale length used (respects multiScale flag) */
  effectiveScaleLength: number
}

// ============================================================================
// SET-LEVEL ANALYSIS
// ============================================================================

export interface SetAnalysis {
  strings: StringResult[]
  /** Sum of all string tensions (lbs) */
  totalTensionLbs: number
  /** Average tension per string (lbs) */
  avgTensionLbs: number
  /** Balance score 0–1 based on coefficient of variation */
  balanceScore: number
  /**
   * Horizontal neck load ≈ ΣT (lbs).
   * Conservative first-order approximation — does not account for neck angle.
   * Will be updated in R-6 (neck angle calculator integration).
   */
  neckLoadLbs: number
  /**
   * Vertical top/bridge load = ΣT × sin(breakAngleDeg) (lbs).
   * Sourced from breakAngle.resolvedDeg when available, else manual input.
   */
  topLoadLbs: number
}

// ============================================================================
// BREAK ANGLE
// ============================================================================

/** Thresholds for acoustic pin-bridge (Carruth empirical) */
export const CARRUTH_MIN_DEG = 6.0
export const PRACTICAL_MIN_PROJECTION_MM = 1.6  // 1/16"
export const STEEP_MAX_DEG = 38.0

/**
 * Break angle state — two modes:
 *  - 'computed': resolved from POST /bridge/break-angle endpoint
 *  - 'manual':   user-entered value, no geometric validation
 */
export type BreakAngleMode = 'computed' | 'manual'

export interface BreakAngleState {
  mode: BreakAngleMode
  /** Manual input field (degrees) */
  manualDeg: number
  /** Geometry inputs for computed mode */
  geometry: {
    pinToSaddleCenterMm: number
    saddleProtrusionMm: number
    saddleSlotDepthMm: number
    saddleBlankHeightMm: number
  }
  /** Last result from the API (null until first call) */
  apiResult: BreakAngleApiResult | null
  /** Loading state */
  loading: boolean
  /** API error message */
  error: string | null
}

/** Shape of POST /bridge/break-angle response (v1 endpoint — known debt) */
export interface BreakAngleApiResult {
  break_angle_deg: number
  /** v1 ratings: optimal | acceptable | too_shallow | too_steep */
  rating: string
  pin_to_saddle_center_mm: number
  saddle_protrusion_mm: number
  energy_coupling: string
  risk_flags: Array<{
    code: string
    severity: string
    message: string
  }>
  recommendation: string | null
}

/** Resolved break angle result used downstream */
export interface ResolvedBreakAngle {
  /** Final angle value used for topLoad calculation */
  deg: number
  /** Source of the value */
  mode: BreakAngleMode
  /**
   * Carruth adequacy — only evaluated when instrumentType.useCarruthThresholds = true.
   * null when not applicable.
   */
  carruthAdequate: boolean | null
  /** v1 API rating when mode = 'computed'. null when manual. */
  apiRating: string | null
  /** Any risk flags from the API */
  riskFlags: BreakAngleApiResult['risk_flags']
  /** Human-readable status label */
  statusLabel: string
}

// ============================================================================
// DISPLAY UNITS
// ============================================================================

export type TensionUnit = 'lbs' | 'N' | 'kg'

// ============================================================================
// PRESET DEFINITION
// ============================================================================

export interface StringSetPreset {
  id: string
  category: PresetCategory
  label: string
  /** Scale length the preset was designed for (inches) */
  scaleLength: number
  /** Whether this preset uses per-string scale lengths */
  multiScale?: boolean
  /** True when uwOverride values are sourced from physical measurement */
  validated?: boolean
  /** Citation for validated presets */
  validationSource?: string
  /** Note about this preset (shown in UI) */
  note?: string
  /** Reference tensions from validation source (Newtons) */
  refTensionsN?: number[]
  strings: Omit<StringSpec, 'id'>[]
}

export type PresetCategory =
  | 'guitar'
  | 'mando'
  | 'uke'
  | 'folk'
  | 'orch'
  | 'validated'
