/**
 * Estimate Assumption Summary Types
 *
 * Dev Order 28: Consolidated assumption summary for first-order estimates.
 * Documents provenance without implying calibration accuracy.
 */

export interface EstimateAssumptionSummary {
  id: string
  label: string

  estimateAvailable: boolean

  estimatedHelmholtzHz?: number

  bodyVolumeLiters?: number
  effectiveLengthMm?: number
  speedOfSoundMps?: number

  source?: string
  method?: string
  confidence?: string

  assumptions: string[]
  warnings: string[]
}
