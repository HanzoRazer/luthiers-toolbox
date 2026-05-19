/**
 * Calibration Readiness Types
 *
 * Dev Order 22: Calibration readiness layer.
 * Evaluates whether data is sufficient for future calibration.
 * Does NOT perform calibration or prediction.
 */

/**
 * Gate levels for calibration readiness.
 */
export type CalibrationReadinessGate = 'green' | 'yellow' | 'red'

/**
 * Individual diagnostic result.
 */
export interface CalibrationReadinessDiagnostic {
  id: string
  gate: CalibrationReadinessGate
  message: string
  recommendedAction?: string
}

/**
 * Full calibration readiness evaluation result.
 */
export interface CalibrationReadiness {
  overallGate: CalibrationReadinessGate
  diagnostics: CalibrationReadinessDiagnostic[]
  readyForCalibration: boolean
  missingFields: string[]
  warnings: string[]
}
