/**
 * StratocasterNeckGenerator composables barrel export.
 */

// Types
export type {
  StratNeckGeometry,
  StratNeckParameters,
  StratValidationWarning,
  StratNeckProfile,
  StratNeckPreset
} from './stratNeckTypes'

// State
export { useStratNeckState } from './useStratNeckState'
export type { StratNeckStateReturn } from './useStratNeckState'

// Presets
export { useStratNeckPresets } from './useStratNeckPresets'
export type { StratNeckPresetsReturn } from './useStratNeckPresets'

// Actions
export { useStratNeckActions } from './useStratNeckActions'
export type { StratNeckActionsReturn } from './useStratNeckActions'
