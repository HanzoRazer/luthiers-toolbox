/**
 * LesPaulNeckGenerator state composable.
 */
import { reactive, ref, type Ref } from 'vue'
import {
  getDefaultLesPaulParams,
  type NeckGeometry,
  type NeckParameters,
  type ValidationWarning
} from '@/utils/neck_generator'
import type { NeckPreset } from './lesPaulNeckTypes'

// ============================================================================
// Types
// ============================================================================

export interface LesPaulNeckStateReturn {
  form: NeckParameters
  generatedGeometry: Ref<NeckGeometry | null>
  neckPresets: Ref<NeckPreset[]>
  selectedPresetId: Ref<string>
  presetLoadedMessage: Ref<string>
  originalPresetParams: Ref<NeckParameters | null>
  validationWarnings: Ref<ValidationWarning[]>
}

// ============================================================================
// Composable
// ============================================================================

export function useLesPaulNeckState(): LesPaulNeckStateReturn {
  const form = reactive(getDefaultLesPaulParams())
  const generatedGeometry = ref<NeckGeometry | null>(null)
  const neckPresets = ref<NeckPreset[]>([])
  const selectedPresetId = ref<string>('')
  const presetLoadedMessage = ref<string>('')
  const originalPresetParams = ref<NeckParameters | null>(null)
  const validationWarnings = ref<ValidationWarning[]>([])

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
