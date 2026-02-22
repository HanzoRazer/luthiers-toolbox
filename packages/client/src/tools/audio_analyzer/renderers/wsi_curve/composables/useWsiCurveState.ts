/**
 * WsiCurveRenderer state composable.
 */
import { ref, type Ref } from 'vue'

export interface WsiCurveStateReturn {
  showCohMean: Ref<boolean>
  showPhaseDisorder: Ref<boolean>
  shadeAdmissible: Ref<boolean>
  parseError: Ref<string | null>
  emphasizeSelectionPoint: Ref<boolean>
}

export function useWsiCurveState(): WsiCurveStateReturn {
  const showCohMean = ref(true)
  const showPhaseDisorder = ref(true)
  const shadeAdmissible = ref(true)
  const parseError = ref<string | null>(null)
  const emphasizeSelectionPoint = ref(true)

  return {
    showCohMean,
    showPhaseDisorder,
    shadeAdmissible,
    parseError,
    emphasizeSelectionPoint
  }
}
