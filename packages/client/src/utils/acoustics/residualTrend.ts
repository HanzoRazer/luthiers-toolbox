/**
 * Residual Trend Utilities
 *
 * Dev Order 31: Summarize residual direction consistency.
 * Observational only — does NOT calibrate, correct, or recommend changes.
 *
 * Sign interpretation (residual = measured - estimated):
 * - positive residual: measured > estimated, estimate is low
 * - negative residual: measured < estimated, estimate is high
 * - zero residual: measured ≈ estimated
 */

import type { CalibrationResidualPreview } from '@/types/calibrationResiduals'
import type { ResidualTrendDirection, ResidualTrendSummary } from '@/types/residualTrend'

/**
 * Summarize residual trend from a calibration residual preview.
 */
export function summarizeResidualTrend(params: {
  id: string
  label: string
  preview: CalibrationResidualPreview
}): ResidualTrendSummary {
  const { id, label, preview } = params

  const available = preview.residuals.filter(
    (r) => r.available && r.residual !== undefined
  )

  const availableResidualCount = available.length
  let positiveResidualCount = 0
  let negativeResidualCount = 0
  let zeroResidualCount = 0

  for (const r of available) {
    const residual = r.residual!
    if (residual > 0) {
      positiveResidualCount++
    } else if (residual < 0) {
      negativeResidualCount++
    } else {
      zeroResidualCount++
    }
  }

  let direction: ResidualTrendDirection
  let message: string

  if (availableResidualCount === 0) {
    direction = 'insufficient_data'
    message = 'No paired residuals are available for trend interpretation.'
  } else if (positiveResidualCount > 0 && negativeResidualCount === 0) {
    direction = 'estimate_low'
    message = 'Measurements are higher than estimates for available paired metrics.'
  } else if (negativeResidualCount > 0 && positiveResidualCount === 0) {
    direction = 'estimate_high'
    message = 'Measurements are lower than estimates for available paired metrics.'
  } else if (positiveResidualCount > 0 && negativeResidualCount > 0) {
    direction = 'mixed'
    message = 'Residual directions are mixed across available paired metrics.'
  } else {
    // Zero-only residuals
    direction = 'mixed'
    message = 'Available residuals are near zero under current assumptions.'
  }

  const caution =
    'Trend indicators are observational only and do not recommend corrections. ' +
    'A consistent trend may indicate assumption mismatch, measurement mismatch, or limits of the first-order estimate.'

  return {
    id,
    label,
    direction,
    availableResidualCount,
    positiveResidualCount,
    negativeResidualCount,
    zeroResidualCount,
    message,
    caution,
  }
}

/**
 * Get display label for trend direction.
 */
export function getTrendDirectionLabel(direction: ResidualTrendDirection): string {
  switch (direction) {
    case 'insufficient_data':
      return 'Insufficient Data'
    case 'estimate_low':
      return 'Estimate Low'
    case 'estimate_high':
      return 'Estimate High'
    case 'mixed':
      return 'Mixed Trend'
  }
}
