/**
 * StratocasterNeckGenerator state composable.
 */
import { reactive, ref, type Ref } from 'vue'
import {
  getDefaultStratParams,
  type StratNeckGeometry,
  type StratNeckParameters,
  type StratValidationWarning
} from '@/utils/strat_neck_generator'
import type { StratNeckPreset } from './stratNeckTypes'

// ============================================================================
// Types
// ============================================================================

export interface StratNeckStateReturn {
  form: StratNeckParameters
  generatedGeometry: Ref<StratNeckGeometry | null>
  neckPresets: Ref<StratNeckPreset[]>
  selectedPresetId: Ref<string>
  presetLoadedMessage: Ref<string>
  originalPresetParams: Ref<StratNeckParameters | null>
  validationWarnings: Ref<StratValidationWarning[]>
}

// ============================================================================
// Composable
// ============================================================================

export function useStratNeckState(): StratNeckStateReturn {
  const form = reactive(getDefaultStratParams())
  const generatedGeometry = ref<StratNeckGeometry | null>(null)
  const neckPresets = ref<StratNeckPreset[]>([])
  const selectedPresetId = ref<string>('')
  const presetLoadedMessage = ref<string>('')
  const originalPresetParams = ref<StratNeckParameters | null>(null)
  const validationWarnings = ref<StratValidationWarning[]>([])

  return {
    form,
    generatedGeometry,
    neckPresets,
    selectedPresetId,
    presetLoadedMessage,
    originalPresetParams,
    validationWarnings
  }
}
