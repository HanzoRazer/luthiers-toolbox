/**
 * Composable for Contour Following operation (N10).
 * Linear contour following from point array.
 */
import { ref, type Ref } from 'vue'
import { api } from '@/services/apiBase'
import { downloadFile, handleExportError } from './useGcodeExport'

// ============================================================================
// Types
// ============================================================================

export interface ContourParams {
  pathJson: string
  depth: number
  feed: number
}

export interface ContourState {
  params: Ref<ContourParams>
  exportGcode: () => Promise<void>
}

// ============================================================================
// Defaults
// ============================================================================

const DEFAULT_PARAMS: ContourParams = {
  pathJson: '[{"x":0,"y":0},{"x":50,"y":0},{"x":50,"y":30},{"x":0,"y":30}]',
  depth: -3.0,
  feed: 1200.0
}

// ============================================================================
// Composable
// ============================================================================

export function useContourOperation(): ContourState {
  const params = ref<ContourParams>({ ...DEFAULT_PARAMS })

  async function exportGcode(): Promise<void> {
    try {
      const path = JSON.parse(params.value.pathJson)
      const body = {
        path,
        z: params.value.depth,
        feed: params.value.feed,
        post: 'GRBL'
      }

      const response = await api('/api/cam/toolpath/biarc/gcode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })

      const gcode = await response.text()
      downloadFile(gcode, 'contour_biarc.nc')
    } catch (err) {
      handleExportError('Contour', err)
    }
  }

  return {
    params,
    exportGcode
  }
}
