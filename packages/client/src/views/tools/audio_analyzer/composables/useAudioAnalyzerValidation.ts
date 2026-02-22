/**
 * AudioAnalyzer validation display composable.
 */
import { computed } from 'vue'
import type { ShallowRef, ComputedRef } from 'vue'
import type { NormalizedPack } from './audioAnalyzerTypes'

// ============================================================================
// Types
// ============================================================================

export interface AudioAnalyzerValidationReturn {
  validationStatusClass: ComputedRef<string>
  validationIcon: ComputedRef<string>
}

// ============================================================================
// Composable
// ============================================================================

export function useAudioAnalyzerValidation(
  pack: ShallowRef<NormalizedPack | null>,
  styles: Record<string, string>
): AudioAnalyzerValidationReturn {
  const validationStatusClass = computed(() => {
    if (!pack.value?.validation) return styles.validationUnknownBorder
    return pack.value.validation.passed ? styles.validationPass : styles.validationFail
  })

  const validationIcon = computed(() => {
    if (!pack.value?.validation) return '❓'
    return pack.value.validation.passed ? '✅' : '❌'
  })

  return {
    validationStatusClass,
    validationIcon
  }
}
