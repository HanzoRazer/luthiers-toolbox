/**
 * Measured Response Utilities
 *
 * Dev Order 19: Helper functions for measured acoustic response.
 */

import type { MeasuredResponse } from '@/types/measurements'

/**
 * Create an empty measured response placeholder.
 */
export function createEmptyMeasuredResponse(params: {
  id: string
  label: string
  attachedTo?: 'reference' | 'candidate' | 'comparison' | 'unknown'
}): MeasuredResponse {
  return {
    id: params.id,
    label: params.label,
    source: 'manual',
    method: 'unknown',
    notes: ['No measured response data attached yet.'],
    attachedTo: params.attachedTo ?? 'unknown',
  }
}

/**
 * Check if a measured response has any actual measurement data.
 *
 * Returns true if any of:
 * - measuredHelmholtzHz
 * - measuredQ
 * - dominantPeakHz
 * is defined.
 */
export function hasMeasuredResponseData(response: MeasuredResponse): boolean {
  return (
    response.measuredHelmholtzHz !== undefined ||
    response.measuredQ !== undefined ||
    response.dominantPeakHz !== undefined
  )
}

/**
 * Get human-readable source label.
 */
export function getMeasurementSourceLabel(source: MeasuredResponse['source']): string {
  switch (source) {
    case 'manual':
      return 'Manual Entry'
    case 'tap_tone_pi':
      return 'tap_tone_pi'
    case 'imported_file':
      return 'Imported File'
    case 'unknown':
    default:
      return 'Unknown'
  }
}

/**
 * Get human-readable method label.
 */
export function getMeasurementMethodLabel(method: MeasuredResponse['method']): string {
  switch (method) {
    case 'tap_test':
      return 'Tap Test'
    case 'sine_sweep':
      return 'Sine Sweep'
    case 'impulse_response':
      return 'Impulse Response'
    case 'manual_observation':
      return 'Manual Observation'
    case 'unknown':
    default:
      return 'Unknown'
  }
}
