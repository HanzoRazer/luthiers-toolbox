/**
 * Composable for adaptive toolpath generation.
 */
import { ref, type Ref } from 'vue'
import { api } from '@/services/apiBase'
import { DEFAULT_ADAPTIVE_PARAMS, type AdaptiveParams } from './bridgeLabTypes'

// ============================================================================
// Types
// ============================================================================

export interface AdaptiveToolpathState {
  adaptiveParams: Ref<AdaptiveParams>
  adaptiveRunning: Ref<boolean>
  sendToAdaptive: () => Promise<void>
}

// ============================================================================
// Composable
// ============================================================================

export function useAdaptiveToolpath(
  dxfFile: Ref<File | null>,
  currentStage: Ref<number>,
  toolpathResult: Ref<any>
): AdaptiveToolpathState {
  const adaptiveParams = ref<AdaptiveParams>({ ...DEFAULT_ADAPTIVE_PARAMS })
  const adaptiveRunning = ref(false)

  async function sendToAdaptive(): Promise<void> {
    if (!dxfFile.value) return

    adaptiveRunning.value = true
    currentStage.value = 2

    try {
      const formData = new FormData()
      formData.append('file', dxfFile.value)
      formData.append('units', adaptiveParams.value.units)
      formData.append('tool_d', adaptiveParams.value.tool_d.toString())
      formData.append('geometry_layer', adaptiveParams.value.geometry_layer)
      formData.append('stepover', adaptiveParams.value.stepover.toString())
      formData.append('stepdown', adaptiveParams.value.stepdown.toString())
      formData.append('margin', adaptiveParams.value.margin.toString())
      formData.append('strategy', adaptiveParams.value.strategy)
      formData.append('feed_xy', adaptiveParams.value.feed_xy.toString())
      formData.append('safe_z', adaptiveParams.value.safe_z.toString())
      formData.append('z_rough', adaptiveParams.value.z_rough.toString())

      const response = await api('/api/cam/dxf_adaptive_plan_run', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        throw new Error(`Adaptive planning failed: ${response.statusText}`)
      }

      toolpathResult.value = await response.json()
      currentStage.value = 3
    } catch (error) {
      console.error('Adaptive error:', error)
      alert(`Toolpath generation failed: ${error}`)
    } finally {
      adaptiveRunning.value = false
    }
  }

  return {
    adaptiveParams,
    adaptiveRunning,
    sendToAdaptive
  }
}
