/**
 * First-order Helmholtz frequency estimate utility
 *
 * Dev Order 27: First-order Helmholtz estimate helper.
 *
 * Formula:
 *   f_H = (c / 2π) × √(A / (V × L_eff))
 *
 * Where:
 *   c = speed of sound, m/s
 *   A = aperture area, m²
 *   V = body volume, m³
 *   L_eff = effective neck length, m
 *
 * This is a first-order estimate only. Not calibrated prediction.
 */

import type { HelmholtzEstimateInput, HelmholtzEstimateResult } from '@/types/helmholtz'

const DEFAULT_SPEED_OF_SOUND_MPS = 343

/**
 * Estimate Helmholtz frequency from aperture geometry and body parameters.
 *
 * Returns null if any required value is invalid (zero or negative).
 */
export function estimateHelmholtzFrequency(
  input: HelmholtzEstimateInput
): HelmholtzEstimateResult | null {
  const { areaMm2, volumeLiters, effectiveLengthMm } = input
  const speedOfSoundMps = input.speedOfSoundMps ?? DEFAULT_SPEED_OF_SOUND_MPS

  if (areaMm2 <= 0 || volumeLiters <= 0 || effectiveLengthMm <= 0 || speedOfSoundMps <= 0) {
    return null
  }

  const areaM2 = areaMm2 * 1e-6
  const volumeM3 = volumeLiters * 1e-3
  const effectiveLengthM = effectiveLengthMm * 1e-3

  const frequencyHz =
    (speedOfSoundMps / (2 * Math.PI)) * Math.sqrt(areaM2 / (volumeM3 * effectiveLengthM))

  const assumptions: string[] = [
    'First-order Helmholtz resonator model',
    `Body volume: ${volumeLiters.toFixed(1)} L`,
    `Effective length: ${effectiveLengthMm.toFixed(1)} mm`,
    `Speed of sound: ${speedOfSoundMps.toFixed(0)} m/s`,
  ]

  const warnings: string[] = [
    'No calibration applied',
    'Effective length strongly affects result',
    'Body volume should be measured, not guessed',
    'Multi-aperture and cavity coupling not modeled',
    'This estimate does not include two-cavity coupling, modal interaction, or tornavoz effects',
  ]

  return {
    estimatedHelmholtzHz: frequencyHz,
    inputUsed: {
      areaMm2,
      volumeLiters,
      effectiveLengthMm,
      speedOfSoundMps,
    },
    assumptions,
    warnings,
    confidence: 'low',
    method: 'first_order_helmholtz',
  }
}

export function getDefaultSpeedOfSound(): number {
  return DEFAULT_SPEED_OF_SOUND_MPS
}
