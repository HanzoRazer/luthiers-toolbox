/**
 * useRosetteCompareCanvas.ts - Canvas drawing composable for rosette comparison
 * Extracted from RosetteComparePanel.vue
 */
import { ref, type Ref, watch, onMounted } from 'vue'
import type { GeometryPayload } from './useRosetteCompareApi'

export interface UseRosetteCompareCanvasOptions {
  baselineColor?: string
  currentColor?: string
}

export function useRosetteCompareCanvas(
  baselineGeometry: Ref<GeometryPayload | null>,
  currentGeometry: Ref<GeometryPayload | null>,
  options: UseRosetteCompareCanvasOptions = {}
) {
  const baselineCanvasRef = ref<HTMLCanvasElement | null>(null)
  const currentCanvasRef = ref<HTMLCanvasElement | null>(null)

  const defaultBaselineColor = options.baselineColor || '#111827'
  const defaultCurrentColor = options.currentColor || '#2563eb'

  /**
   * Map meta.color or color strings to actual stroke colors.
   */
  function colorForPath(path: any, fallback: string): string {
    const metaColor = path?.meta?.color || path?.color
    switch (metaColor) {
      case 'green':
        return '#22c55e' // added
      case 'red':
        return '#ef4444' // removed
      case 'gray':
        return '#6b7280' // unchanged
      default:
        return fallback
    }
  }

  function drawGeometryOnCanvas(
    canvas: HTMLCanvasElement | null,
    geometry: GeometryPayload | null,
    defaultStroke: string
  ) {
    if (!canvas || !geometry) return
    const paths = geometry.paths || geometry.loops || []
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const w = canvas.width
    const h = canvas.height
    ctx.clearRect(0, 0, w, h)
    ctx.save()
    ctx.fillStyle = '#f9fafb'
    ctx.fillRect(0, 0, w, h)

    // compute bounding box
    let minX = Infinity,
      minY = Infinity,
      maxX = -Infinity,
      maxY = -Infinity

    for (const path of paths) {
      const pts = path.points || path.pts || []
      for (const p of pts) {
        if (!Array.isArray(p) || p.length < 2) continue
        const x = Number(p[0])
        const y = Number(p[1])
        if (!isFinite(x) || !isFinite(y)) continue
        if (x < minX) minX = x
        if (y < minY) minY = y
        if (x > maxX) maxX = x
        if (y > maxY) maxY = y
      }
    }

    if (!isFinite(minX) || !isFinite(minY) || !isFinite(maxX) || !isFinite(maxY)) {
      ctx.restore()
      return
    }

    const dx = maxX - minX || 1
    const dy = maxY - minY || 1

    const margin = 10
    const scale = Math.min((w - 2 * margin) / dx, (h - 2 * margin) / dy)

    ctx.translate(w / 2, h / 2)
    // flip Y axis
    ctx.scale(scale, -scale)
    ctx.translate(-(minX + maxX) / 2, -(minY + maxY) / 2)

    for (const path of paths) {
      const pts = path.points || path.pts || []
      let started = false
      ctx.beginPath()

      // set color per path based on meta.color or fallback
      ctx.strokeStyle = colorForPath(path, defaultStroke)
      ctx.lineWidth = ctx.strokeStyle === '#6b7280' ? 1 : 1.5

      for (const p of pts) {
        if (!Array.isArray(p) || p.length < 2) continue
        const x = Number(p[0])
        const y = Number(p[1])
        if (!started) {
          ctx.moveTo(x, y)
          started = true
        } else {
          ctx.lineTo(x, y)
        }
      }
      if (started) {
        ctx.closePath()
        ctx.stroke()
      }
    }

    ctx.restore()
  }

  function drawCanvases(currentGeomOverride: GeometryPayload | null = null) {
    drawGeometryOnCanvas(
      baselineCanvasRef.value,
      baselineGeometry.value,
      defaultBaselineColor
    )
    drawGeometryOnCanvas(
      currentCanvasRef.value,
      currentGeomOverride || currentGeometry.value,
      defaultCurrentColor
    )
  }

  // Auto-redraw when geometries change
  watch(
    () => baselineGeometry.value,
    () => drawCanvases(),
    { deep: true }
  )

  watch(
    () => currentGeometry.value,
    () => drawCanvases(),
    { deep: true }
  )

  return {
    baselineCanvasRef,
    currentCanvasRef,
    drawCanvases,
    drawGeometryOnCanvas,
    colorForPath
  }
}
