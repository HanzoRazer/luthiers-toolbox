/**
 * DrillingLab canvas composable.
 */
import type { Ref } from 'vue'
import type { Hole } from './drillingLabTypes'

export interface DrillingCanvasReturn {
  drawCanvas: () => void
  onCanvasClick: (event: MouseEvent) => void
  onCanvasHover: (event: MouseEvent) => void
}

export function useDrillingCanvas(
  canvas: Ref<HTMLCanvasElement | null>,
  holes: Ref<Hole[]>,
  selectedHole: Ref<number | null>,
  patternType: Ref<string>,
  updatePreview: () => void
): DrillingCanvasReturn {
  function drawCanvas(): void {
    if (!canvas.value) return

    const ctx = canvas.value.getContext('2d')
    if (!ctx) return

    const width = 600
    const height = 600

    // Clear
    ctx.clearRect(0, 0, width, height)

    // Background
    ctx.fillStyle = '#f8f9fa'
    ctx.fillRect(0, 0, width, height)

    // Grid
    ctx.strokeStyle = '#dee2e6'
    ctx.lineWidth = 1
    for (let i = 0; i <= 10; i++) {
      const pos = (i / 10) * width
      ctx.beginPath()
      ctx.moveTo(pos, 0)
      ctx.lineTo(pos, height)
      ctx.stroke()
      ctx.beginPath()
      ctx.moveTo(0, pos)
      ctx.lineTo(width, pos)
      ctx.stroke()
    }

    // Draw holes
    holes.value.forEach((hole, index) => {
      const canvasX = (hole.x / 100) * width
      const canvasY = (hole.y / 100) * height

      // Hole circle
      ctx.beginPath()
      ctx.arc(canvasX, canvasY, 8, 0, 2 * Math.PI)
      ctx.fillStyle = hole.enabled ? '#0ea5e9' : '#94a3b8'
      ctx.fill()
      ctx.strokeStyle = selectedHole.value === index ? '#f59e0b' : '#0c4a6e'
      ctx.lineWidth = selectedHole.value === index ? 3 : 2
      ctx.stroke()

      // Label
      ctx.fillStyle = '#1e293b'
      ctx.font = 'bold 12px sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText(`H${index + 1}`, canvasX, canvasY - 12)
    })

    // Axis labels
    ctx.fillStyle = '#64748b'
    ctx.font = '12px sans-serif'
    ctx.textAlign = 'left'
    ctx.fillText('0 mm', 5, height - 5)
    ctx.textAlign = 'right'
    ctx.fillText('100 mm', width - 5, height - 5)
    ctx.textAlign = 'left'
    ctx.fillText('100 mm', 5, 15)
  }

  function onCanvasClick(event: MouseEvent): void {
    if (patternType.value !== 'manual') return

    const rect = canvas.value!.getBoundingClientRect()
    const x = event.clientX - rect.left
    const y = event.clientY - rect.top

    // Convert canvas coordinates to mm (canvas is 600x600, representing 100x100mm)
    const mmX = (x / 600) * 100
    const mmY = (y / 600) * 100

    holes.value.push({
      x: Math.round(mmX * 10) / 10,
      y: Math.round(mmY * 10) / 10,
      enabled: true
    })

    updatePreview()
  }

  function onCanvasHover(_event: MouseEvent): void {
    if (!canvas.value) return
    // Could add hover preview here
  }

  return {
    drawCanvas,
    onCanvasClick,
    onCanvasHover
  }
}
