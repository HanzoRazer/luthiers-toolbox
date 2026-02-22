/**
 * ArtStudioCanvas state composable.
 */
import { ref, type Ref } from 'vue'
import type { MLPoint } from './artStudioCanvasTypes'

export interface CanvasStateReturn {
  containerRef: Ref<HTMLDivElement | null>
  canvasRef: Ref<HTMLCanvasElement | null>
  ctx: Ref<CanvasRenderingContext2D | null>
  zoom: Ref<number>
  panX: Ref<number>
  panY: Ref<number>
  isDragging: Ref<boolean>
  lastMouse: Ref<{ x: number; y: number }>
  mouseCoords: Ref<MLPoint | null>
}

export function useCanvasState(): CanvasStateReturn {
  const containerRef = ref<HTMLDivElement | null>(null)
  const canvasRef = ref<HTMLCanvasElement | null>(null)
  const ctx = ref<CanvasRenderingContext2D | null>(null)

  const zoom = ref(1)
  const panX = ref(0)
  const panY = ref(0)
  const isDragging = ref(false)
  const lastMouse = ref({ x: 0, y: 0 })
  const mouseCoords = ref<MLPoint | null>(null)

  return {
    containerRef,
    canvasRef,
    ctx,
    zoom,
    panX,
    panY,
    isDragging,
    lastMouse,
    mouseCoords
  }
}
