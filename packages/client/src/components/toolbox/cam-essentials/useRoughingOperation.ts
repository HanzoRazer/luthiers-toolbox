/**
 * Composable for Roughing operation (N01).
 * Simple rectangular roughing for pocket clearing.
 */
import { ref, type Ref } from 'vue'
import { api } from '@/services/apiBase'
import { downloadFile, handleExportError } from './useGcodeExport'

// ============================================================================
// Types
// ============================================================================

export interface RoughingParams {
  width: number
  height: number
  stepdown: number
  stepover: number
  feed: number
  post: string
}

export interface RoughingState {
  params: Ref<RoughingParams>
  exportGcode: () => Promise<void>
}

// ============================================================================
// Defaults
// ============================================================================

const DEFAULT_PARAMS: RoughingParams = {
  width: 100.0,
  height: 60.0,
  stepdown: 3.0,
  stepover: 2.5,
  feed: 1200.0,
  post: 'GRBL'
}

// ============================================================================
// Composable
// ============================================================================

export function useRoughingOperation(): RoughingState {
  const params = ref<RoughingParams>({ ...DEFAULT_PARAMS })

  async function exportGcode(): Promise<void> {
    try {
      const response = await api('/api/cam/toolpath/roughing/gcode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params.value)
      })

      const gcode = await response.text()
      downloadFile(gcode, `roughing_${params.value.post}.nc`)
    } catch (err) {
      handleExportError('Roughing', err)
    }
  }

  return {
    params,
    exportGcode
  }
}
