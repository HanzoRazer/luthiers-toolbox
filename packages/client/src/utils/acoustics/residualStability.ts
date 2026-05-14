/**
 * Residual Stability Utilities
 *
 * Dev Order 32: Classify residual pattern stability.
 * Qualitative and observational only — does NOT validate, calibrate, or correct.
 *
 * Levels:
 * - insufficient: no residuals available
 * - sparse: only one residual, cannot assess pattern
 * - stable: directionally consistent, no large residuals
 * - volatile: mixed direction or large residuals present
 */

import type { ResidualInterpretationSummary } from '@/types/residualInterpretation'
import type { ResidualTrendSummary } from '@/types/residualTrend'
import type { ResidualStabilityLevel, ResidualStabilitySummary } from '@/types/residualStability'

/**
 * Classify residual stability from interpretation and trend summaries.
 */
export function classifyResidualStability(params: {
  id: string
  label: string
  interpretation: ResidualInterpretationSummary
  trend: ResidualTrendSummary
}): ResidualStabilitySummary {
  const { id, label, interpretation, trend } = params

  // Count magnitude levels from interpretation items
  let largeResidualCount = 0
  let moderateResidualCount = 0
  let smallResidualCount = 0

  for (const item of interpretation.items) {
    switch (item.level) {
      case 'large':
        largeResidualCount++
        break
      case 'moderate':
        moderateResidualCount++
        break
      case 'small':
        smallResidualCount++
        break
      // insufficient_data items are not counted for magnitude
    }
  }

  const availableResidualCount = trend.availableResidualCount
  const trendDirection = trend.direction

  let level: ResidualStabilityLevel
  let message: string
  let caution: string

  if (availableResidualCount === 0) {
    level = 'insufficient'
    message = 'No residuals are available for stability classification.'
    caution = 'Attach estimates and measurements to enable residual analysis.'
  } else if (availableResidualCount === 1) {
    level = 'sparse'
    message = 'Only one residual is available; pattern stability cannot be assessed.'
    caution = 'Additional paired metrics would improve pattern assessment.'
  } else if (largeResidualCount > 0) {
    level = 'volatile'
    message = 'Residuals include large divergences under current assumptions.'
    caution =
      'Volatile patterns may reflect inconsistent measurements, incompatible assumptions, or limits of the estimate model.'
  } else if (trendDirection === 'mixed') {
    level = 'volatile'
    message = 'Residuals appear mixed or divergent in direction under current assumptions.'
    caution =
      'Volatile patterns may reflect inconsistent measurements, incompatible assumptions, or limits of the estimate model.'
  } else if (trendDirection === 'estimate_low' || trendDirection === 'estimate_high') {
    level = 'stable'
    message = 'Residuals appear directionally consistent under current assumptions.'
    caution =
      'Stable does not mean correct; residuals may share the same assumption bias.'
  } else {
    // Fallback for edge cases (e.g., all zero residuals classified as mixed)
    level = 'stable'
    message = 'Residuals appear consistent under current assumptions.'
    caution =
      'Stable does not mean correct; residuals may share the same assumption bias.'
  }

  const notes: string[] = [
    'Stability classification is qualitative and observational only.',
    'It does not validate or calibrate the model.',
  ]

  return {
    id,
    label,
    level,
    availableResidualCount,
    largeResidualCount,
    moderateResidualCount,
    smallResidualCount,
    trendDirection,
    message,
    caution,
    notes,
  }
}

/**
 * Get display label for stability level.
 */
export function getStabilityLevelLabel(level: ResidualStabilityLevel): string {
  switch (level) {
    case 'insufficient':
      return 'Insufficient'
    case 'sparse':
      return 'Sparse'
    case 'stable':
      return 'Stable Pattern'
    case 'volatile':
      return 'Volatile Pattern'
  }
}

/**
 * Get gate color for stability level.
 */
export function getStabilityGateColor(
  level: ResidualStabilityLevel
): 'green' | 'yellow' | 'red' {
  switch (level) {
    case 'stable':
      return 'green'
    case 'volatile':
      return 'red'
    case 'insufficient':
    case 'sparse':
      return 'yellow'
  }
}
