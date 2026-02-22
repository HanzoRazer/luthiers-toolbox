/**
 * ArtStudioCanvas interaction composable.
 */
import type { Ref } from 'vue'
import type { MLPoint } from './artStudioCanvasTypes'

export interface CanvasInteractionReturn {
  screenToWorld: (screenX: number, screenY: number) => MLPoint
  onWheel: (e: WheelEvent) => void
  onMouseDown: (e: MouseEvent) => void
  onMouseMove: (e: MouseEvent) => void
  onMouseUp: () => void
  resetView: () => void
  zoomIn: () => void
  zoomOut: () => void
}

export function useCanvasInteraction(
  canvasRef: Ref<HTMLCanvasElement | null>,
  zoom: Ref<number>,
  panX: Ref<number>,
  panY: Ref<number>,
  isDragging: Ref<boolean>,
  lastMouse: Ref<{ x: number; y: number }>,
  mouseCoords: Ref<MLPoint | null>,
  draw: () => void
): CanvasInteractionReturn {
  function screenToWorld(screenX: number, screenY: number): MLPoint {
    const canvas = canvasRef.value
    if (!canvas) return { x: 0, y: 0 }

    const rect = canvas.getBoundingClientRect()
    const x = (screenX - rect.left - canvas.width / 2 - panX.value) / zoom.value
    const y = -(screenY - rect.top - canvas.height / 2 - panY.value) / zoom.value

    return { x, y }
  }

  function onWheel(e: WheelEvent): void {
    e.preventDefault()

    const delta = e.deltaY > 0 ? 0.9 : 1.1
    const newZoom = Math.max(0.1, Math.min(10, zoom.value * delta))

    // Zoom towards mouse position
    const worldBefore = screenToWorld(e.clientX, e.clientY)
    zoom.value = newZoom
    const worldAfter = screenToWorld(e.clientX, e.clientY)

    panX.value += (worldAfter.x - worldBefore.x) * zoom.value
    panY.value -= (worldAfter.y - worldBefore.y) * zoom.value

    draw()
  }

  function onMouseDown(e: MouseEvent): void {
    if (e.button === 0) {
      isDragging.value = true
      lastMouse.value = { x: e.clientX, y: e.clientY }
    }
  }

  function onMouseMove(e: MouseEvent): void {
    // Update coordinates display
    mouseCoords.value = screenToWorld(e.clientX, e.clientY)

    if (isDragging.value) {
      const dx = e.clientX - lastMouse.value.x
      const dy = e.clientY - lastMouse.value.y

      panX.value += dx
      panY.value += dy

      lastMouse.value = { x: e.clientX, y: e.clientY }
      draw()
    }
  }

  function onMouseUp(): void {
    isDragging.value = false
  }

  function resetView(): void {
    zoom.value = 1
    panX.value = 0
    panY.value = 0
    draw()
  }

  function zoomIn(): void {
    zoom.value = Math.min(10, zoom.value * 1.2)
    draw()
  }

  function zoomOut(): void {
    zoom.value = Math.max(0.1, zoom.value / 1.2)
    draw()
  }

  return {
    screenToWorld,
    onWheel,
    onMouseDown,
    onMouseMove,
    onMouseUp,
    resetView,
    zoomIn,
    zoomOut
  }
}
