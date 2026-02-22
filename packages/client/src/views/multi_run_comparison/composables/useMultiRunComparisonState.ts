/**
 * MultiRunComparisonView state composable.
 */
import { ref, type Ref } from 'vue'
import type { Preset, ComparisonResult } from './multiRunComparisonTypes'

// ============================================================================
// Types
// ============================================================================

export interface MultiRunComparisonStateReturn {
  allPresets: Ref<Preset[]>
  selectedPresetIds: Ref<string[]>
  loading: Ref<boolean>
  errorMessage: Ref<string>
  comparisonResult: Ref<ComparisonResult | null>
  timeChartCanvas: Ref<HTMLCanvasElement | null>
}

// ============================================================================
// Composable
// ============================================================================

export function useMultiRunComparisonState(): MultiRunComparisonStateReturn {
  const allPresets = ref<Preset[]>([])
  const selectedPresetIds = ref<string[]>([])
  const loading = ref(false)
  const errorMessage = ref<string>('')
  const comparisonResult = ref<ComparisonResult | null>(null)
  const timeChartCanvas = ref<HTMLCanvasElement | null>(null)

  return {
    allPresets,
    selectedPresetIds,
    loading,
    errorMessage,
    comparisonResult,
    timeChartCanvas
  }
}
