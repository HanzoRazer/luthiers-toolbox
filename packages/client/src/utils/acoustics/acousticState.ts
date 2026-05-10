/**
 * Acoustic State Utilities
 *
 * Dev Order 15: Helper functions for creating and working with AcousticState.
 */

import type {
  AcousticState,
  ApertureGeometryLike,
} from '@/types/acoustics'

/**
 * Default assumptions for geometry-derived acoustic state.
 */
const DEFAULT_GEOMETRY_ASSUMPTIONS: string[] = [
  'Geometry-derived state only',
  'No body volume attached',
  'No calibrated acoustic model applied',
  'No measured response data attached',
]

/**
 * Create an acoustic state from aperture geometry.
 *
 * This creates a low-confidence, geometry-estimate state.
 * It does not compute acoustic predictions - it scaffolds the
 * acoustic state for future solver integration.
 */
export function createGeometryAcousticState(params: {
  id: string
  label: string
  apertureGeometry: ApertureGeometryLike
  bodyVolumeLiters?: number
  assumptions?: string[]
  warnings?: string[]
}): AcousticState {
  const {
    id,
    label,
    apertureGeometry,
    bodyVolumeLiters,
    assumptions = [],
    warnings,
  } = params

  // Merge default assumptions with any custom ones
  const mergedAssumptions = [
    ...DEFAULT_GEOMETRY_ASSUMPTIONS.filter(
      (a) => !assumptions.some((custom) => custom.toLowerCase().includes(a.toLowerCase().split(' ')[0]))
    ),
    ...assumptions,
  ]

  // If body volume is provided, remove the "No body volume attached" assumption
  const finalAssumptions = bodyVolumeLiters
    ? mergedAssumptions.filter((a) => !a.includes('No body volume'))
    : mergedAssumptions

  return {
    id,
    label,
    source: 'geometry_estimate',
    confidence: 'low',
    apertureType: apertureGeometry.aperture_type,
    apertureGeometry,
    bodyVolumeLiters,
    assumptions: finalAssumptions,
    warnings,
  }
}

/**
 * Check if an acoustic state has any estimated acoustic values.
 *
 * Returns true if any of the acoustic estimate fields are present:
 * - estimatedHelmholtzHz
 * - estimatedEffectiveLengthMm
 * - qEstimate
 * - lossEstimate
 */
export function hasEstimatedAcoustics(state: AcousticState): boolean {
  return (
    state.estimatedHelmholtzHz !== undefined ||
    state.estimatedEffectiveLengthMm !== undefined ||
    state.qEstimate !== undefined ||
    state.lossEstimate !== undefined
  )
}

/**
 * Get a human-readable confidence label.
 */
export function getConfidenceLabel(confidence: AcousticState['confidence']): string {
  switch (confidence) {
    case 'high':
      return 'High'
    case 'medium':
      return 'Medium'
    case 'low':
      return 'Low'
    case 'unknown':
    default:
      return 'Unknown'
  }
}

/**
 * Get a human-readable source label.
 */
export function getSourceLabel(source: AcousticState['source']): string {
  switch (source) {
    case 'geometry_estimate':
      return 'Geometry Estimate'
    case 'measured':
      return 'Measured'
    case 'calibrated':
      return 'Calibrated'
    case 'manual':
      return 'Manual Entry'
    case 'unknown':
    default:
      return 'Unknown'
  }
}
