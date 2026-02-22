/**
 * Composable for Drill Pattern operation (N07).
 * Generate drilling patterns (grid, circle, line).
 */
import { ref, type Ref } from 'vue'
import { downloadFile, handleExportError } from './useGcodeExport'

// ============================================================================
// Types
// ============================================================================

export interface GridPattern {
  rows: number
  cols: number
  dx: number
  dy: number
}

export interface CirclePattern {
  count: number
  radius: number
  start_angle_deg: number
}

export interface LinePattern {
  count: number
  dx: number
  dy: number
}

export interface PatternParams {
  type: 'grid' | 'circle' | 'line'
  grid: GridPattern
  circle: CirclePattern
  line: LinePattern
  depth: number
  feed: number
}

export interface PatternState {
  params: Ref<PatternParams>
  exportGcode: () => Promise<void>
}

// ============================================================================
// Defaults
// ============================================================================

const DEFAULT_PARAMS: PatternParams = {
  type: 'grid',
  grid: { rows: 3, cols: 4, dx: 10.0, dy: 10.0 },
  circle: { count: 6, radius: 20.0, start_angle_deg: 0.0 },
  line: { count: 5, dx: 5.0, dy: 0.0 },
  depth: -10.0,
  feed: 300.0
}

// ============================================================================
// Composable
// ============================================================================

export function usePatternOperation(): PatternState {
  const params = ref<PatternParams>({ ...DEFAULT_PARAMS })

  async function exportGcode(): Promise<void> {
    try {
      const patternSpec: Record<string, unknown> = {
        type: params.value.type,
        origin_x: 0.0,
        origin_y: 0.0
      }

      if (params.value.type === 'grid') {
        patternSpec.grid = params.value.grid
      } else if (params.value.type === 'circle') {
        patternSpec.circle = params.value.circle
      } else if (params.value.type === 'line') {
        patternSpec.line = params.value.line
      }

      const drillParams = {
        z: String(params.value.depth),
        feed: String(params.value.feed),
        cycle: 'G81',
        post: 'GRBL'
      }

      const queryString = new URLSearchParams(drillParams).toString()
      const url = `/api/cam/drilling/pattern/gcode?${queryString}`

      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(patternSpec)
      })

      const gcode = await response.text()
      downloadFile(gcode, `pattern_${params.value.type}.nc`)
    } catch (err) {
      handleExportError('Pattern', err)
    }
  }

  return {
    params,
    exportGcode
  }
}
