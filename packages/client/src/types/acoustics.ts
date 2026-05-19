/**
 * Acoustic State Types
 *
 * Dev Order 15: Normalized acoustic state model for bridging geometry
 * comparison and future target-matching / inverse-solver work.
 * Dev Order 28: Added provenance fields (speedOfSoundMps, estimateMethod).
 *
 * This is a descriptive model, not a solver. It represents known or
 * estimated acoustic values without claiming prediction accuracy.
 */

/**
 * Confidence level for acoustic estimates.
 * Most geometry-derived estimates should be 'low'.
 */
export type AcousticConfidence = 'unknown' | 'low' | 'medium' | 'high'

/**
 * Source of acoustic state data.
 */
export type AcousticStateSource =
  | 'geometry_estimate'
  | 'measured'
  | 'calibrated'
  | 'manual'
  | 'unknown'

/**
 * Geometry-like interface for acoustic state.
 * Decoupled from Vue component exports to keep domain types clean.
 */
export interface ApertureGeometryLike {
  aperture_type?: string
  area_mm2?: number
  perimeter_mm?: number
  equivalent_diameter_mm?: number
  characteristic_width_mm?: number | null
  path_length_mm?: number | null
  pa_ratio_mm_inv?: number | null
}

/**
 * Acoustic State model.
 *
 * Represents the acoustic state of an aperture configuration.
 * Bridges geometry comparison and future acoustic analysis without
 * prematurely committing to full Helmholtz, Q, or modal prediction engines.
 *
 * Key invariants:
 * - Confidence is mandatory (prevents overconfidence in estimates)
 * - Assumptions are mandatory (prevents estimated physics looking like measured truth)
 * - Geometry remains separate (ApertureGeometry is not merged into this)
 */
export interface AcousticState {
  /** Unique identifier for this state */
  id: string

  /** Human-readable label */
  label: string

  /** Source of this acoustic state */
  source: AcousticStateSource

  /** Confidence level in the acoustic estimates */
  confidence: AcousticConfidence

  /** Aperture type identifier */
  apertureType?: string

  /** Associated aperture geometry (reference, not merged) */
  apertureGeometry?: ApertureGeometryLike

  /** Body volume in liters (if known) */
  bodyVolumeLiters?: number

  /** Estimated Helmholtz frequency in Hz */
  estimatedHelmholtzHz?: number

  /** Estimated effective acoustic neck length in mm */
  estimatedEffectiveLengthMm?: number

  /** Speed of sound used for estimate (m/s) */
  speedOfSoundMps?: number

  /** Method used to generate the estimate */
  estimateMethod?: 'first_order_helmholtz' | string

  /** Estimated Q factor */
  qEstimate?: number

  /** Estimated acoustic loss/resistance */
  lossEstimate?: number

  /** Assumptions that apply to this state (mandatory) */
  assumptions: string[]

  /** Optional warnings about this state */
  warnings?: string[]
}
