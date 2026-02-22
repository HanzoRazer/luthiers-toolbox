/**
 * SpectrumChartRenderer state composable.
 */
import { ref, type Ref } from 'vue'
import type { Chart } from 'chart.js'

// ============================================================================
// Types
// ============================================================================

export interface SpectrumChartStateReturn {
  chartCanvas: Ref<HTMLCanvasElement | null>
  showCoherence: Ref<boolean>
  logScale: Ref<boolean>
  showPeaks: Ref<boolean>
  parseError: Ref<string | null>
  originalRowCount: Ref<number>
  chartInstance: Ref<Chart | null>
}

// ============================================================================
// Composable
// ============================================================================

export function useSpectrumChartState(): SpectrumChartStateReturn {
  const chartCanvas = ref<HTMLCanvasElement | null>(null)
  const showCoherence = ref(true)
  const logScale = ref(false)
  const showPeaks = ref(true)
  const parseError = ref<string | null>(null)
  const originalRowCount = ref(0)
  const chartInstance = ref<Chart | null>(null)

  return {
    chartCanvas,
    showCoherence,
    logScale,
    showPeaks,
    parseError,
    originalRowCount,
    chartInstance
  }
}
