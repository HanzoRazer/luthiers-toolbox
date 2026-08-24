/**
 * Composable for Retract Patterns operation (N08).
 * Safe retract strategies for tool changes.
 */
import { ref, type Ref } from 'vue'
import { api } from '@/services/apiBase'
import { downloadFile, handleExportError, readGcodeOrThrow } from './useGcodeExport'

// ============================================================================
// Types
// ============================================================================

export type RetractStrategy = 'direct' | 'ramped' | 'helical'

export interface RetractParams {
  strategy: RetractStrategy
  current_z: number
  safe_z: number
  ramp_feed: number
  helix_radius: number
  helix_pitch: number
}

export interface RetractState {
  params: Ref<RetractParams>
  exportGcode: () => Promise<void>
}

// ============================================================================
// Defaults
// ============================================================================

const DEFAULT_PARAMS: RetractParams = {
  strategy: 'direct',
  current_z: -10.0,
  safe_z: 5.0,
  ramp_feed: 600.0,
  helix_radius: 5.0,
  helix_pitch: 1.0
}

// ============================================================================
// Composable
// ============================================================================

export function useRetractOperation(): RetractState {
  const params = ref<RetractParams>({ ...DEFAULT_PARAMS })

  async function exportGcode(): Promise<void> {
    try {
      // /gcode takes query params, not a JSON body. Sending JSON was ignored
      // by FastAPI and silently used defaults.
      const query = new URLSearchParams({
        strategy: params.value.strategy,
        current_z: String(params.value.current_z),
        safe_z: String(params.value.safe_z),
        ramp_feed: String(params.value.ramp_feed),
        helix_radius: String(params.value.helix_radius),
        helix_pitch: String(params.value.helix_pitch)
      })

      const response = await api(`/api/cam/retract/gcode?${query.toString()}`, {
        method: 'POST'
      })

      const gcode = await readGcodeOrThrow(response, 'Retract')
      downloadFile(gcode, `retract_${params.value.strategy}.nc`)
    } catch (err) {
      handleExportError('Retract', err)
    }
  }

  return {
    params,
    exportGcode
  }
}
