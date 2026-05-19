/**
 * Residual Interpretation Utilities
 *
 * Dev Order 30: Qualitative residual magnitude interpretation.
 * Interpretive guidance only — does NOT calibrate, correct, or validate.
 *
 * Thresholds are provisional and are not calibrated acoustic acceptance criteria.
 */

import type { CalibrationResidualPreview, CalibrationResidual } from '@/types/calibrationResiduals'
import type {
  ResidualInterpretationLevel,
  ResidualInterpretationItem,
  ResidualInterpretationSummary,
} from '@/types/residualInterpretation'

/**
 * Provisional thresholds for percent residual interpretation.
 * These are UI guidance values, not validated acoustic standards.
 */
const THRESHOLD_SMALL = 5
const THRESHOLD_MODERATE = 15

/**
 * Interpret a single residual.
 */
function interpretResidual(residual: CalibrationResidual): ResidualInterpretationItem {
  const { id, label, residual: residualValue, percentResidual, unit, available } = residual

  if (!available) {
    return {
      id,
      label,
      level: 'insufficient_data',
      unit,
      message: 'Estimate and measurement pair unavailable.',
      caution: '',
    }
  }

  if (percentResidual !== null && percentResidual !== undefined) {
    const absPct = Math.abs(percentResidual)

    if (absPct <= THRESHOLD_SMALL) {
      return {
        id,
        label,
        level: 'small',
        residual: residualValue,
        percentResidual,
        unit,
        message: `Small residual (${absPct.toFixed(1)}%). Estimate and measurement are numerically close.`,
        caution:
          'Small residual means the values are close under current assumptions, not that the model is validated.',
      }
    }

    if (absPct <= THRESHOLD_MODERATE) {
      return {
        id,
        label,
        level: 'moderate',
        residual: residualValue,
        percentResidual,
        unit,
        message: `Moderate residual (${absPct.toFixed(1)}%). Notable difference between estimate and measurement.`,
        caution:
          'Moderate residual may reflect assumption sensitivity or measurement conditions.',
      }
    }

    return {
      id,
      label,
      level: 'large',
      residual: residualValue,
      percentResidual,
      unit,
      message: `Large residual (${absPct.toFixed(1)}%). Significant gap between estimate and measurement.`,
      caution:
        'Large residual may indicate incompatible assumptions, measurement mismatch, or limits of the first-order estimate.',
    }
  }

  if (residualValue !== undefined) {
    return {
      id,
      label,
      level: 'moderate',
      residual: residualValue,
      percentResidual: null,
      unit,
      message: 'Residual available but percent not computable.',
      caution:
        'Percent residual unavailable; interpretation based on absolute difference only.',
    }
  }

  return {
    id,
    label,
    level: 'insufficient_data',
    unit,
    message: 'Residual could not be computed.',
    caution: '',
  }
}

/**
 * Determine overall level from items (worst wins).
 */
function computeOverallLevel(items: ResidualInterpretationItem[]): ResidualInterpretationLevel {
  const levels: ResidualInterpretationLevel[] = items.map((i) => i.level)

  if (levels.includes('large')) return 'large'
  if (levels.includes('moderate')) return 'moderate'
  if (levels.includes('small')) return 'small'
  return 'insufficient_data'
}

/**
 * Interpret a calibration residual preview.
 */
export function interpretResidualPreview(params: {
  id: string
  label: string
  preview: CalibrationResidualPreview
}): ResidualInterpretationSummary {
  const { id, label, preview } = params

  const items = preview.residuals.map(interpretResidual)
  const overallLevel = computeOverallLevel(items)

  const notes: string[] = [
    'Thresholds are provisional and are not calibrated acoustic acceptance criteria.',
    'Interpretation does not modify estimates, measurements, or residuals.',
  ]

  return {
    id,
    label,
    items,
    overallLevel,
    notes,
  }
}

/**
 * Get display label for interpretation level.
 */
export function getInterpretationLevelLabel(level: ResidualInterpretationLevel): string {
  switch (level) {
    case 'insufficient_data':
      return 'Insufficient Data'
    case 'small':
      return 'Small Residual'
    case 'moderate':
      return 'Moderate Residual'
    case 'large':
      return 'Large Residual'
  }
}

/**
 * Get gate color for interpretation level.
 */
export function getInterpretationGateColor(
  level: ResidualInterpretationLevel
): 'green' | 'yellow' | 'red' {
  switch (level) {
    case 'small':
      return 'green'
    case 'moderate':
    case 'insufficient_data':
      return 'yellow'
    case 'large':
      return 'red'
  }
}
