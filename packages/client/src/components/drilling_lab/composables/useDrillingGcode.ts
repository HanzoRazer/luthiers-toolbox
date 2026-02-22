/**
 * DrillingLab G-code composable.
 */
import { api } from '@/services/apiBase'
import type { Ref, ComputedRef } from 'vue'
import type { Hole, DrillParams } from './drillingLabTypes'

export interface DrillingGcodeReturn {
  generateGCodePreview: () => Promise<void>
  exportGCode: () => Promise<void>
  copyGCode: () => void
}

export function useDrillingGcode(
  params: Ref<DrillParams>,
  enabledHoles: ComputedRef<Hole[]>,
  gcodePreview: Ref<string>
): DrillingGcodeReturn {
  async function generateGCodePreview(): Promise<void> {
    if (enabledHoles.value.length === 0) {
      gcodePreview.value = '(No holes defined)'
      return
    }

    try {
      const body = {
        cycle: params.value.cycle,
        holes: enabledHoles.value.map((h) => ({ x: h.x, y: h.y })),
        depth: params.value.depth,
        retract: params.value.retract,
        feed: params.value.feedRate,
        safe_z: params.value.safeZ,
        post_id: params.value.postId,
        peck_depth: params.value.cycle === 'G83' ? params.value.peckDepth : undefined,
        thread_pitch: params.value.cycle === 'G84' ? params.value.threadPitch : undefined
      }

      const response = await api('/api/cam/drilling/gcode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      const data = await response.json()
      gcodePreview.value = data.gcode || '(Error generating G-code)'
    } catch (err) {
      console.error('G-code preview failed:', err)
      gcodePreview.value = '(Preview error - check console)'
    }
  }

  async function exportGCode(): Promise<void> {
    if (enabledHoles.value.length === 0) {
      alert('No holes to export')
      return
    }

    try {
      const body = {
        cycle: params.value.cycle,
        holes: enabledHoles.value.map((h) => ({ x: h.x, y: h.y })),
        depth: params.value.depth,
        retract: params.value.retract,
        feed: params.value.feedRate,
        safe_z: params.value.safeZ,
        post_id: params.value.postId,
        peck_depth: params.value.cycle === 'G83' ? params.value.peckDepth : undefined,
        thread_pitch: params.value.cycle === 'G84' ? params.value.threadPitch : undefined
      }

      const response = await api('/api/cam/drilling/gcode/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })

      if (!response.ok) {
        throw new Error(`Export failed: ${response.status}`)
      }

      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `drilling_${params.value.cycle}_${enabledHoles.value.length}holes.nc`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Export failed:', err)
      alert('Export failed. Check console for details.')
    }
  }

  function copyGCode(): void {
    navigator.clipboard
      .writeText(gcodePreview.value)
      .then(() => alert('G-code copied to clipboard'))
      .catch((err) => console.error('Copy failed:', err))
  }

  return {
    generateGCodePreview,
    exportGCode,
    copyGCode
  }
}
