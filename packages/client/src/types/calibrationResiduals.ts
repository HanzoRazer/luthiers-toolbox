/**
 * Calibration Residual Types
 *
 * Dev Order 23: Calibration residual preview.
 * Dev Order 29: Added estimate provenance annotation.
 * Displays gap between estimated acoustic state and measured response.
 * Does NOT calibrate, fit, correct, or predict.
 */

/**
 * Individual residual for a single metric.
 */
export interface CalibrationResidual {
  id: string
  label: string
  estimatedValue?: number
  measuredValue?: number
  residual?: number
  percentResidual?: number | null
  unit?: string
  available: boolean
  message?: string
}

/**
 * Estimate provenance for residual annotation.
 * Dev Order 29: Makes residuals traceable to their estimate assumptions.
 */
export interface ResidualEstimateProvenance {
  estimateMethod?: string
  estimateSource?: string
  estimateConfidence?: string
  estimateAssumptions: string[]
  estimateWarnings: string[]
}

/**
 * Full residual preview for one aperture.
 */
export interface CalibrationResidualPreview {
  id: string
  label: string
  residuals: CalibrationResidual[]
  hasAvailableResiduals: boolean
  notes: string[]
  provenance?: ResidualEstimateProvenance
}
