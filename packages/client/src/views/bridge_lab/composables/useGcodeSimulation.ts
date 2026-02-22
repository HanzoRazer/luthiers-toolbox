/**
 * Composable for G-code simulation functionality.
 */
import { ref, type Ref } from 'vue'
import { api } from '@/services/apiBase'
import type { AdaptiveParams } from './bridgeLabTypes'

// ============================================================================
// Types
// ============================================================================

export interface GcodeSimulationState {
  simRunning: Ref<boolean>
  onGcodeFileChange: (event: Event) => void
  simulateGcode: () => Promise<void>
}

// ============================================================================
// Composable
// ============================================================================

export function useGcodeSimulation(
  gcodeFile: Ref<File | null>,
  simResult: Ref<any>,
  adaptiveParams: Ref<AdaptiveParams>,
  currentStage: Ref<number>
): GcodeSimulationState {
  const simRunning = ref(false)

  function onGcodeFileChange(event: Event): void {
    const input = event.target as HTMLInputElement
    gcodeFile.value = input.files?.[0] ?? null
    simResult.value = null
  }

  async function simulateGcode(): Promise<void> {
    if (!gcodeFile.value) return

    simRunning.value = true
    currentStage.value = 4

    try {
      const formData = new FormData()
      formData.append('file', gcodeFile.value)
      formData.append('units', adaptiveParams.value.units)

      const response = await api('/api/cam/simulate_gcode', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        throw new Error(`Simulation failed: ${response.statusText}`)
      }

      simResult.value = await response.json()
    } catch (error) {
      console.error('Simulation error:', error)
      alert(`G-code simulation failed: ${error}`)
    } finally {
      simRunning.value = false
    }
  }

  return {
    simRunning,
    onGcodeFileChange,
    simulateGcode
  }
}
