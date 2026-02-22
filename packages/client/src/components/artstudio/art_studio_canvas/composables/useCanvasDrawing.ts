/**
 * ArtStudioCanvas drawing composable.
 */
import type { Ref } from 'vue'
import type { MLPath, MLPoint } from './artStudioCanvasTypes'
import { COLORS } from './artStudioCanvasTypes'
import { useArtStudioEngine } from '@/stores/useArtStudioEngine'

export interface CanvasDrawingReturn {
  draw: () => void
}

export interface CanvasDrawingProps {
  showToolpaths?: boolean
  showFretboard?: boolean
  showFretSlots?: boolean
  gridSize?: number
}

export function useCanvasDrawing(
  canvasRef: Ref<HTMLCanvasElement | null>,
  ctx: Ref<CanvasRenderingContext2D | null>,
  zoom: Ref<number>,
  panX: Ref<number>,
  panY: Ref<number>,
  props: CanvasDrawingProps
): CanvasDrawingReturn {
  const engine = useArtStudioEngine()

  function draw(): void {
    if (!ctx.value || !canvasRef.value) return

    const canvas = canvasRef.value
    const context = ctx.value
    const w = canvas.width
    const h = canvas.height

    // Clear
    context.fillStyle = COLORS.background
    context.fillRect(0, 0, w, h)

    context.save()

    // Apply view transform (center origin, flip Y for CAD convention)
    context.translate(w / 2 + panX.value, h / 2 + panY.value)
    context.scale(zoom.value, -zoom.value)

    // Draw grid
    if (props.gridSize) {
      drawGrid(context, w, h)
    }

    // Draw origin crosshair
    drawOrigin(context)

    // Draw fretboard outline
    if (props.showFretboard && engine.fretboardOutline.value.length > 0) {
      drawFretboard(context)
    }

    // Draw fret slots
    if (props.showFretSlots && engine.fretSlots.value.length > 0) {
      drawFretSlots(context)
    }

    // Draw design paths with risk-based coloring (Wave 9)
    for (const path of engine.currentPaths.value) {
      const pathId = path.meta?.id as string | undefined
      const riskLevel = pathId ? engine.getPathRisk(pathId) : 'none'
      const strokeColor = engine.getRiskColor(riskLevel)
      drawPath(context, path, strokeColor, COLORS.pathFill)
    }

    // Draw toolpaths
    if (props.showToolpaths) {
      for (const path of engine.toolpaths.value) {
        drawPath(context, path, COLORS.toolpath, 'transparent', [4, 2])
      }
    }

    context.restore()
  }

  function drawGrid(context: CanvasRenderingContext2D, w: number, h: number): void {
    const gridSize = props.gridSize || 10
    const viewW = w / zoom.value
    const viewH = h / zoom.value

    context.strokeStyle = COLORS.grid
    context.lineWidth = 0.5 / zoom.value

    // Vertical lines
    const startX = Math.floor((-viewW / 2 - panX.value / zoom.value) / gridSize) * gridSize
    const endX = Math.ceil((viewW / 2 - panX.value / zoom.value) / gridSize) * gridSize

    for (let x = startX; x <= endX; x += gridSize) {
      const isMajor = x % (gridSize * 10) === 0
      context.strokeStyle = isMajor ? COLORS.gridMajor : COLORS.grid
      context.beginPath()
      context.moveTo(x, -viewH)
      context.lineTo(x, viewH)
      context.stroke()
    }

    // Horizontal lines
    const startY = Math.floor((-viewH / 2 + panY.value / zoom.value) / gridSize) * gridSize
    const endY = Math.ceil((viewH / 2 + panY.value / zoom.value) / gridSize) * gridSize

    for (let y = startY; y <= endY; y += gridSize) {
      const isMajor = y % (gridSize * 10) === 0
      context.strokeStyle = isMajor ? COLORS.gridMajor : COLORS.grid
      context.beginPath()
      context.moveTo(-viewW, y)
      context.lineTo(viewW, y)
      context.stroke()
    }
  }

  function drawOrigin(context: CanvasRenderingContext2D): void {
    const size = 10 / zoom.value

    context.strokeStyle = COLORS.origin
    context.lineWidth = 2 / zoom.value

    // X axis
    context.beginPath()
    context.moveTo(0, 0)
    context.lineTo(size, 0)
    context.stroke()

    // Y axis
    context.beginPath()
    context.moveTo(0, 0)
    context.lineTo(0, size)
    context.stroke()

    // Origin dot
    context.fillStyle = COLORS.origin
    context.beginPath()
    context.arc(0, 0, 2 / zoom.value, 0, Math.PI * 2)
    context.fill()
  }

  function drawPath(
    context: CanvasRenderingContext2D,
    path: MLPath,
    strokeColor: string,
    fillColor: string,
    lineDash: number[] = []
  ): void {
    if (!path.points.length) return

    context.beginPath()
    context.setLineDash(lineDash.map((d) => d / zoom.value))

    const [first, ...rest] = path.points
    context.moveTo(first.x, first.y)

    for (const pt of rest) {
      context.lineTo(pt.x, pt.y)
    }

    if (path.closed) {
      context.closePath()
    }

    if (fillColor !== 'transparent') {
      context.fillStyle = fillColor
      context.fill()
    }

    context.strokeStyle = strokeColor
    context.lineWidth = 1.5 / zoom.value
    context.stroke()

    context.setLineDash([])
  }

  function drawFretboard(context: CanvasRenderingContext2D): void {
    const outline = engine.fretboardOutline.value
    if (outline.length < 3) return

    context.beginPath()
    context.moveTo(outline[0].x, outline[0].y)

    for (let i = 1; i < outline.length; i++) {
      context.lineTo(outline[i].x, outline[i].y)
    }
    context.closePath()

    context.strokeStyle = COLORS.fretboard
    context.lineWidth = 2 / zoom.value
    context.stroke()
  }

  function drawFretSlots(context: CanvasRenderingContext2D): void {
    context.strokeStyle = COLORS.fretSlot
    context.lineWidth = 1 / zoom.value

    for (const slot of engine.fretSlots.value) {
      context.beginPath()
      context.moveTo(slot.left.x, slot.left.y)
      context.lineTo(slot.right.x, slot.right.y)
      context.stroke()
    }
  }

  return { draw }
}
