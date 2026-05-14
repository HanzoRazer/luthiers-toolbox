/**
 * Estimate Assumption Summary Utilities
 *
 * Dev Order 28: Creates assumption summaries from AcousticState.
 * Reads provenance fields directly — does not infer from assumption strings.
 */

import type { AcousticState } from '@/types/acoustics'
import type { EstimateAssumptionSummary } from '@/types/estimateAssumptions'

/**
 * Create an estimate assumption summary from AcousticState.
 *
 * The summary documents the assumptions attached to the current estimate.
 * It does not compute or validate anything.
 */
export function createEstimateAssumptionSummary(params: {
  id: string
  label: string
  acousticState: AcousticState | null
}): EstimateAssumptionSummary {
  const { id, label, acousticState } = params

  if (!acousticState || acousticState.estimatedHelmholtzHz === undefined) {
    return {
      id,
      label,
      estimateAvailable: false,
      assumptions: [],
      warnings: [],
    }
  }

  return {
    id,
    label,
    estimateAvailable: true,
    estimatedHelmholtzHz: acousticState.estimatedHelmholtzHz,
    bodyVolumeLiters: acousticState.bodyVolumeLiters,
    effectiveLengthMm: acousticState.estimatedEffectiveLengthMm,
    speedOfSoundMps: acousticState.speedOfSoundMps,
    source: acousticState.source,
    method: acousticState.estimateMethod,
    confidence: acousticState.confidence,
    assumptions: acousticState.assumptions,
    warnings: acousticState.warnings ?? [],
  }
}
