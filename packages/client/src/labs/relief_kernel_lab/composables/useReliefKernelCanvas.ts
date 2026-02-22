/**
 * ReliefKernelLab canvas composable.
 */
import { ref, onMounted, type Ref } from 'vue'
import type { HeightmapData, FinishingResult, SimBridgeOutput } from './reliefKernelTypes'

export interface ReliefKernelCanvasReturn {
  canvas: Ref<HTMLCanvasElement | null>
  drawCanvas: () => void
}

export function useReliefKernelCanvas(
  map: Ref<HeightmapData | null>,
  result: Ref<FinishingResult | null>,
  reliefSimBridgeOut: Ref<SimBridgeOutput | null>
): ReliefKernelCanvasReturn {
  const canvas = ref<HTMLCanvasElement | null>(null)
  let ctx: CanvasRenderingContext2D | null = null

  onMounted(() => {
    if (canvas.value) {
      ctx = canvas.value.getContext('2d')
    }
  })

  function drawCanvas(): void {
    if (!ctx || !canvas.value || !map.value) return

    const w = map.value.width
    const h = map.value.height
    canvas.value.width = w
    canvas.value.height = h

    // Background
    ctx.fillStyle = '#111'
    ctx.fillRect(0, 0, w, h)

    // Geometry outline (gray)
    ctx.strokeStyle = '#666'
    ctx.lineWidth = 1
    ctx.strokeRect(0, 0, w, h)

    // Toolpath (blue)
    if (result.value?.moves) {
      ctx.strokeStyle = '#3b82f6'
      ctx.lineWidth = 1
      ctx.beginPath()
      let started = false
      for (const m of result.value.moves) {
        if (m.x !== undefined && m.y !== undefined) {
          const px = (m.x - map.value.origin_x) / map.value.cell_size_xy
          const py = (m.y - map.value.origin_y) / map.value.cell_size_xy
          if (!started) {
            ctx.moveTo(px, py)
            started = true
          } else {
            ctx.lineTo(px, py)
          }
        }
      }
      ctx.stroke()
    }

    // Draw sim bridge overlays (load hotspots)
    if (reliefSimBridgeOut.value?.overlays) {
      for (const ov of reliefSimBridgeOut.value.overlays) {
        const px = (ov.x - map.value.origin_x) / map.value.cell_size_xy
        const py = (ov.y - map.value.origin_y) / map.value.cell_size_xy

        if (ov.type === 'load_hotspot') {
          const intensity = ov.intensity ?? 0.5
          const alpha = Math.min(intensity, 1.0)
          ctx.fillStyle = `rgba(255, 140, 0, ${alpha})`
          ctx.fillRect(px - 1, py - 1, 2, 2)
        }
      }
    }

    // Draw sim bridge issues (thin floor zones)
    if (reliefSimBridgeOut.value?.issues) {
      for (const issue of reliefSimBridgeOut.value.issues) {
        const px = (issue.x - map.value.origin_x) / map.value.cell_size_xy
        const py = (issue.y - map.value.origin_y) / map.value.cell_size_xy

        if (issue.type === 'thin_floor') {
          ctx.strokeStyle = '#ef4444'
          ctx.lineWidth = 1
          ctx.beginPath()
          ctx.arc(px, py, 3, 0, Math.PI * 2)
          ctx.stroke()
        }
      }
    }
  }

  return {
    canvas,
    drawCanvas
  }
}
