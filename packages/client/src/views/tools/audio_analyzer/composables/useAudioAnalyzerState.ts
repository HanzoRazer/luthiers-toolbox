/**
 * AudioAnalyzer base state composable.
 */
import { ref, shallowRef } from 'vue'
import type { Ref, ShallowRef } from 'vue'
import type { NormalizedPack, SelectedPeak } from './audioAnalyzerTypes'

// ============================================================================
// Types
// ============================================================================

export interface AudioAnalyzerStateReturn {
  pack: ShallowRef<NormalizedPack | null>
  err: Ref<string>
  activePath: Ref<string>
  kindFilter: Ref<string>
  selectedPeak: Ref<SelectedPeak | null>
  audioJumpError: Ref<string>
  resetError: () => void
}

// ============================================================================
// Composable
// ============================================================================

export function useAudioAnalyzerState(): AudioAnalyzerStateReturn {
  const pack = shallowRef<NormalizedPack | null>(null)
  const err = ref<string>('')
  const activePath = ref<string>('')
  const kindFilter = ref<string>('')
  const selectedPeak = ref<SelectedPeak | null>(null)
  const audioJumpError = ref<string>('')

  function resetError(): void {
    err.value = ''
  }

  return {
    pack,
    err,
    activePath,
    kindFilter,
    selectedPeak,
    audioJumpError,
    resetError
  }
}
