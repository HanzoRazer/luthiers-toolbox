/**
 * Measured Response Types
 *
 * Dev Order 19: Phase-3A measured data attachment scaffold.
 * Measured response is separate from geometry-derived AcousticState.
 */

/**
 * Source of measurement data.
 */
export type MeasurementSource =
  | 'manual'
  | 'tap_tone_pi'
  | 'imported_file'
  | 'unknown'

/**
 * Method used to capture measurement.
 */
export type MeasurementMethod =
  | 'tap_test'
  | 'sine_sweep'
  | 'impulse_response'
  | 'manual_observation'
  | 'unknown'

/**
 * Measured acoustic response data.
 *
 * This is separate from AcousticState:
 * - AcousticState = estimated/descriptive (geometry-derived)
 * - MeasuredResponse = observed/measured (actual measurements)
 *
 * No spectra arrays or raw FFT data in this model.
 */
export interface MeasuredResponse {
  /** Unique identifier */
  id: string

  /** Human-readable label */
  label: string

  /** Source of this measurement */
  source: MeasurementSource

  /** Method used to capture measurement */
  method: MeasurementMethod

  /** Measured Helmholtz resonance frequency in Hz */
  measuredHelmholtzHz?: number

  /** Measured Q factor */
  measuredQ?: number

  /** Dominant peak frequency in Hz */
  dominantPeakHz?: number

  /** Notes about this measurement */
  notes?: string[]

  /** Warnings about measurement quality or validity */
  warnings?: string[]

  /** What this measurement is attached to */
  attachedTo?: 'reference' | 'candidate' | 'comparison' | 'unknown'
}
