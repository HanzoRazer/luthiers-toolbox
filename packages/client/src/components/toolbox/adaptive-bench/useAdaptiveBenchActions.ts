/**
 * useAdaptiveBenchActions.ts - API actions composable
 * Extracted from AdaptiveBenchLab.vue
 */
import { ref, type Ref } from 'vue'
import { api } from '@/services/apiBase'

export interface BenchResult {
  runs: number
  total_ms: number
  avg_ms: number
  width: number
  height: number
}

export interface BenchParams {
  width: number
  height: number
  toolDia: number
  stepover: number
  cornerFillet: number
  loopPitch: number
  amplitude: number
  benchRuns: number
}

export function useAdaptiveBenchActions(params: Ref<BenchParams>) {
  const loading = ref(false)
  const error = ref('')
  const svgContent = ref('')
  const benchResult = ref<BenchResult | null>(null)

  function resetState() {
    error.value = ''
    svgContent.value = ''
    benchResult.value = null
  }

  async function generateSpiral() {
    loading.value = true
    resetState()

    try {
      const req = {
        width: params.value.width,
        height: params.value.height,
        tool_dia: params.value.toolDia,
        stepover: params.value.stepover,
        corner_fillet: params.value.cornerFillet
      }

      const response = await api('/api/cam/adaptive2/offset_spiral.svg', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req)
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`)
      }

      svgContent.value = await response.text()
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  async function generateTrochoid() {
    loading.value = true
    resetState()

    try {
      const req = {
        width: params.value.width,
        height: params.value.height,
        tool_dia: params.value.toolDia,
        loop_pitch: params.value.loopPitch,
        amp: params.value.amplitude
      }

      const response = await api('/api/cam/adaptive2/trochoid_corners.svg', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req)
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`)
      }

      svgContent.value = await response.text()
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  async function runBenchmark() {
    loading.value = true
    resetState()

    try {
      const req = {
        width: params.value.width,
        height: params.value.height,
        tool_dia: params.value.toolDia,
        stepover: params.value.stepover,
        runs: params.value.benchRuns
      }

      const response = await api('/api/cam/adaptive2/bench', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req)
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`)
      }

      benchResult.value = await response.json()
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    error,
    svgContent,
    benchResult,
    generateSpiral,
    generateTrochoid,
    runBenchmark
  }
}
