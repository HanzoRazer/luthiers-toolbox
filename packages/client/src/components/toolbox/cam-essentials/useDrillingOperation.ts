/**
 * Composable for Drilling operation (N06).
 * Modal drilling cycles (G81/G83) for hole arrays.
 */
import { ref, type Ref } from 'vue'
import { api } from '@/services/apiBase'
import { downloadFile, handleExportError } from './useGcodeExport'

// ============================================================================
// Types
// ============================================================================

export interface DrillingParams {
  cycle: 'G81' | 'G83'
  depth: number
  feed: number
  peck_q: number
  holesJson: string
}

export interface DrillingState {
  params: Ref<DrillingParams>
  exportGcode: () => Promise<void>
}

// ============================================================================
// Defaults
// ============================================================================

const DEFAULT_PARAMS: DrillingParams = {
  cycle: 'G81',
  depth: -10.0,
  feed: 300.0,
  peck_q: 2.0,
  holesJson: '[{"x":10,"y":10,"z":-10,"feed":300},{"x":30,"y":10,"z":-10,"feed":300}]'
}

// ============================================================================
// Composable
// ============================================================================

export function useDrillingOperation(): DrillingState {
  const params = ref<DrillingParams>({ ...DEFAULT_PARAMS })

  async function exportGcode(): Promise<void> {
    try {
      const holes = JSON.parse(params.value.holesJson)
      const body = {
        holes,
        cycle: params.value.cycle,
        peck_q: params.value.cycle === 'G83' ? params.value.peck_q : undefined,
        post: 'GRBL'
      }

      const response = await api('/api/cam/drilling/gcode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })

      const gcode = await response.text()
      downloadFile(gcode, `drilling_${params.value.cycle}.nc`)
    } catch (err) {
      handleExportError('Drilling', err)
    }
  }

  return {
    params,
    exportGcode
  }
}
