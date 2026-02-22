/**
 * LesPaulNeckGenerator type definitions.
 */
import type {
  NeckGeometry,
  NeckParameters,
  ValidationWarning
} from '../../../../utils/neck_generator'

// Re-export from neck_generator for convenience
export type { NeckGeometry, NeckParameters, ValidationWarning }

// ============================================================================
// Preset Types
// ============================================================================

export interface NeckPreset {
  id: string
  name: string
  neck_params?: NeckParameters
}
