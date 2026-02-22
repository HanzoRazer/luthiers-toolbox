/**
 * Composable for Probe Patterns operation (N09).
 * Work offset establishment with touch probes.
 */
import { ref, type Ref } from 'vue'
import { api } from '@/services/apiBase'
import { downloadFile, handleExportError } from './useGcodeExport'

// ============================================================================
// Types
// ============================================================================

export type ProbePattern =
  | 'corner_outside'
  | 'corner_inside'
  | 'boss_circular'
  | 'hole_circular'
  | 'surface_z'

export interface ProbeParams {
  pattern: ProbePattern
  feed_probe: number
  safe_z: number
  diameter: number
  work_offset: number
}

export interface ProbeState {
  params: Ref<ProbeParams>
  exportGcode: () => Promise<void>
  exportSVG: () => Promise<void>
}

// ============================================================================
// Defaults
// ============================================================================

const DEFAULT_PARAMS: ProbeParams = {
  pattern: 'corner_outside',
  feed_probe: 100.0,
  safe_z: 10.0,
  diameter: 50.0,
  work_offset: 1
}

// ============================================================================
// Composable
// ============================================================================

export function useProbeOperation(): ProbeState {
  const params = ref<ProbeParams>({ ...DEFAULT_PARAMS })

  async function exportGcode(): Promise<void> {
    try {
      let endpoint = ''
      const body: Record<string, unknown> = {
        feed_probe: params.value.feed_probe,
        safe_z: params.value.safe_z,
        work_offset: params.value.work_offset,
        approach_distance: 10.0,
        retract_distance: 2.0
      }

      if (params.value.pattern.includes('corner')) {
        endpoint = '/api/cam/probe/corner'
        body.pattern = params.value.pattern
      } else if (params.value.pattern.includes('circular')) {
        endpoint = '/api/cam/probe/boss'
        body.pattern = params.value.pattern
        body.estimated_diameter = params.value.diameter
        body.estimated_center_x = 0.0
        body.estimated_center_y = 0.0
        body.probe_count = 4
      } else if (params.value.pattern === 'surface_z') {
        endpoint = '/api/cam/probe/surface_z'
        body.z_clearance = params.value.safe_z
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })

      const data = await response.json()
      downloadFile(data.gcode, `probe_${params.value.pattern}.nc`)
    } catch (err) {
      handleExportError('Probe', err)
    }
  }

  async function exportSVG(): Promise<void> {
    try {
      const body = {
        pattern: params.value.pattern,
        estimated_diameter: params.value.diameter
      }

      const response = await api('/api/cam/probe/svg_setup_sheet', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })

      const svg = await response.text()
      downloadFile(svg, `probe_setup_${params.value.pattern}.svg`)
    } catch (err) {
      handleExportError('Probe SVG', err)
    }
  }

  return {
    params,
    exportGcode,
    exportSVG
  }
}
