/**
 * Helmholtz estimate types
 *
 * Dev Order 27: First-order Helmholtz estimate helper.
 * Estimate helper, not calibrated prediction.
 */

export interface HelmholtzEstimateInput {
  areaMm2: number
  volumeLiters: number
  effectiveLengthMm: number
  speedOfSoundMps?: number
}

export interface HelmholtzEstimateResult {
  estimatedHelmholtzHz: number
  inputUsed: {
    areaMm2: number
    volumeLiters: number
    effectiveLengthMm: number
    speedOfSoundMps: number
  }
  assumptions: string[]
  warnings: string[]
  confidence: 'low'
  method: 'first_order_helmholtz'
}
