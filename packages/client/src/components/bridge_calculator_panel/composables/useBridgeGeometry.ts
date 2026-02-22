/**
 * BridgeCalculatorPanel geometry calculations composable.
 */
import { computed, type ComputedRef } from 'vue'
import type { Point2D, UiFieldKey } from './bridgeCalculatorTypes'
import { SVG_PADDING } from './bridgeCalculatorTypes'

export interface BridgeGeometryReturn {
  scale: ComputedRef<number>
  spread: ComputedRef<number>
  Ct: ComputedRef<number>
  Cb: ComputedRef<number>
  angleDeg: ComputedRef<number>
  treble: ComputedRef<Point2D>
  bass: ComputedRef<Point2D>
  slotPoly: ComputedRef<Point2D[]>
  svgH: ComputedRef<number>
  svgViewBox: ComputedRef<string>
  slotPolygonPoints: ComputedRef<string>
}

export function useBridgeGeometry(
  ui: Record<UiFieldKey, number>
): BridgeGeometryReturn {
  const scale = computed(() => ui.scale)
  const spread = computed(() => ui.spread)
  const Ct = computed(() => ui.compTreble)
  const Cb = computed(() => ui.compBass)

  const angleDeg = computed(() =>
    Math.atan((Cb.value - Ct.value) / Math.max(spread.value, 1e-6)) * (180 / Math.PI)
  )

  const treble = computed<Point2D>(() => ({
    x: scale.value + Ct.value,
    y: -spread.value / 2
  }))

  const bass = computed<Point2D>(() => ({
    x: scale.value + Cb.value,
    y: spread.value / 2
  }))

  const slotPoly = computed<Point2D[]>(() => {
    const x1 = treble.value.x
    const y1 = treble.value.y
    const x2 = bass.value.x
    const y2 = bass.value.y
    const dx = x2 - x1
    const dy = y2 - y1
    const length = Math.hypot(dx, dy) || 1
    const nx = -dy / length
    const ny = dx / length
    const halfWidth = ui.slotWidth / 2
    const mx = (x1 + x2) / 2
    const my = (y1 + y2) / 2
    const tx = dx / length
    const ty = dy / length
    const halfLen = ui.slotLength / 2

    const A = { x: mx - halfLen * tx + halfWidth * nx, y: my - halfLen * ty + halfWidth * ny }
    const B = { x: mx + halfLen * tx + halfWidth * nx, y: my + halfLen * ty + halfWidth * ny }
    const C = { x: mx + halfLen * tx - halfWidth * nx, y: my + halfLen * ty - halfWidth * ny }
    const D = { x: mx - halfLen * tx - halfWidth * nx, y: my - halfLen * ty - halfWidth * ny }
    return [A, B, C, D]
  })

  const svgH = computed(() => spread.value + SVG_PADDING * 2)

  const svgViewBox = computed(() => {
    const minX = Math.min(0, treble.value.x, bass.value.x) - SVG_PADDING
    const minY = -spread.value / 2 - SVG_PADDING
    const width = (Math.max(treble.value.x, bass.value.x) + SVG_PADDING) - minX
    const height = svgH.value
    return `${minX} ${minY} ${width} ${height}`
  })

  const slotPolygonPoints = computed(() =>
    slotPoly.value.map((p) => `${p.x},${p.y}`).join(' ')
  )

  return {
    scale,
    spread,
    Ct,
    Cb,
    angleDeg,
    treble,
    bass,
    slotPoly,
    svgH,
    svgViewBox,
    slotPolygonPoints
  }
}
