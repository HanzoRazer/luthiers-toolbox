/**
 * StratocasterNeckGenerator type definitions.
 */
import type {
  StratNeckGeometry,
  StratNeckParameters,
  StratValidationWarning,
  StratNeckProfile
} from '@/utils/strat_neck_generator'

// Re-export from strat_neck_generator for convenience
export type {
  StratNeckGeometry,
  StratNeckParameters,
  StratValidationWarning,
  StratNeckProfile
}

// ============================================================================
// Preset Types
// ============================================================================

export interface StratNeckPreset {
  id: string
  name: string
  description?: string
  neck_params?: StratNeckParameters
}
