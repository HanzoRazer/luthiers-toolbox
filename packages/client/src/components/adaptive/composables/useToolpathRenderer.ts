/**
 * Composable for toolpath canvas rendering.
 * Handles drawing geometry, toolpaths, overlays, and heatmaps.
 */
import { ref, type Ref } from 'vue'

export interface Move {
  code: string
  x?: number
  y?: number
  f?: number
  meta?: {
    slowdown?: number
    trochoid?: boolean
    limit?: 'feed_cap' | 'accel' | 'jerk' | 'none'
    radius_mm?: number
  }
  _len_mm?: number
}

export interface Overlay {
  kind: 'tight_radius' | 'slowdown' | 'fillet'
  x: number
  y: number
  r?: number
}

export interface HudVisibility {
  showTight: boolean
  showSlow: boolean
  showFillets: boolean
  showBottleneckMap: boolean
}

export interface ToolpathRendererState {
  overlays: Ref<Overlay[]>
  showTight: Ref<boolean>
  showSlow: Ref<boolean>
  showFillets: Ref<boolean>
  showBottleneckMap: Ref<boolean>
  draw: (canvas: HTMLCanvasElement, moves: Move[], geometry: { minx: number; miny: number; maxx: number; maxy: number }) => void
}

export function useToolpathRenderer(): ToolpathRendererState {
  const overlays = ref<Overlay[]>([])
  const showTight = ref(true)
  const showSlow = ref(true)
  const showFillets = ref(true)
  const showBottleneckMap = ref(true)

  function draw(
    canvas: HTMLCanvasElement,
    moves: Move[],
    geometry: { minx: number; miny: number; maxx: number; maxy: number } = { minx: 0, miny: 0, maxx: 100, maxy: 60 }
  ) {
    const ctx = canvas.getContext('2d')!
    const dpr = window.devicePixelRatio || 1
    canvas.width = canvas.clientWidth * dpr
    canvas.height = canvas.clientHeight * dpr
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    ctx.clearRect(0, 0, canvas.clientWidth, canvas.clientHeight)

    // Simple fit to canvas
    const W = canvas.clientWidth
    const H = canvas.clientHeight
    const box = geometry
    const sx = W / (box.maxx - box.minx + 20)
    const sy = H / (box.maxy - box.miny + 20)
    const s = Math.min(sx, sy) * 0.9
    const ox = 10
    const oy = H - 10
    ctx.translate(ox, oy)
    ctx.scale(s, -s)

    // Draw geometry outline
    ctx.strokeStyle = '#94a3b8'
    ctx.lineWidth = 1 / s
    ctx.beginPath()
    ctx.rect(box.minx, box.miny, box.maxx - box.minx, box.maxy - box.miny)
    ctx.stroke()

    // Draw toolpath with conditional visualization
    if (moves.length > 0) {
      let last: { x: number; y: number } | null = null

      if (showBottleneckMap.value) {
        // Pass 1: Bottleneck map - color by meta.limit
        last = null
        for (const m of moves) {
          if ((m.code === 'G1' || m.code === 'G2' || m.code === 'G3') && 'x' in m && 'y' in m) {
            if (last) {
              const lim = m.meta?.limit || 'none'
              const col =
                lim === 'feed_cap' ? '#f59e0b' : // orange (amber-500)
                lim === 'accel' ? '#14b8a6' : // teal (teal-500)
                lim === 'jerk' ? '#ec4899' : // pink (pink-500)
                null
              if (col) {
                ctx.strokeStyle = col
                ctx.lineWidth = 2 / s
                ctx.beginPath()
                ctx.moveTo(last.x, last.y)
                ctx.lineTo(m.x!, m.y!)
                ctx.stroke()
              }
            }
            last = { x: m.x!, y: m.y! }
          } else if ('x' in m && 'y' in m) {
            last = { x: m.x!, y: m.y! }
          }
        }
      } else {
        // Pass 1: slowdown heatmap for non-trochoid segments
        last = null
        for (const m of moves) {
          if ((m.code === 'G0' || m.code === 'G1') && 'x' in m && 'y' in m) {
            if (last && m.code === 'G1' && !m.meta?.trochoid) {
              const slowdown = m.meta?.slowdown ?? 1.0
              const t = Math.min(1, Math.max(0, (1.0 - slowdown) / 0.6))

              let r: number, g: number, b: number
              if (t < 0.5) {
                const t2 = t * 2
                r = Math.round(14 + (245 - 14) * t2)
                g = Math.round(165 + (158 - 165) * t2)
                b = Math.round(233 + (11 - 233) * t2)
              } else {
                const t2 = (t - 0.5) * 2
                r = Math.round(245 + (239 - 245) * t2)
                g = Math.round(158 + (68 - 158) * t2)
                b = Math.round(11 + (68 - 11) * t2)
              }

              ctx.strokeStyle = `rgb(${r},${g},${b})`
              ctx.lineWidth = 1.2 / s
              ctx.beginPath()
              ctx.moveTo(last.x, last.y)
              ctx.lineTo(m.x!, m.y!)
              ctx.stroke()
            }
            last = { x: m.x!, y: m.y! }
          } else if ('x' in m && 'y' in m) {
            last = { x: m.x!, y: m.y! }
          }
        }
      }

      // Pass 2: trochoid arcs in purple
      last = null
      for (const m of moves) {
        if ((m.code === 'G2' || m.code === 'G3') && m.meta?.trochoid && 'x' in m && 'y' in m) {
          if (last) {
            ctx.strokeStyle = '#7c3aed' // purple (violet-600)
            ctx.lineWidth = 1.5 / s
            ctx.beginPath()
            ctx.moveTo(last.x, last.y)
            ctx.lineTo(m.x!, m.y!)
            ctx.stroke()
          }
          last = { x: m.x!, y: m.y! }
        } else if ('x' in m && 'y' in m) {
          last = { x: m.x!, y: m.y! }
        }
      }

      // Draw entry point (green)
      const first = moves.find((m) => 'x' in m && 'y' in m)
      if (first && first.x !== undefined && first.y !== undefined) {
        ctx.fillStyle = '#10b981'
        ctx.beginPath()
        ctx.arc(first.x, first.y, 2 / s, 0, Math.PI * 2)
        ctx.fill()
      }
    }

    // Draw HUD overlays
    for (const ovl of overlays.value) {
      if (!('x' in ovl && 'y' in ovl)) continue
      const x = ovl.x
      const y = ovl.y

      if (ovl.kind === 'tight_radius' && showTight.value) {
        ctx.strokeStyle = '#ef4444'
        ctx.lineWidth = 1.5 / s
        ctx.beginPath()
        ctx.arc(x, y, ovl.r || 2, 0, Math.PI * 2)
        ctx.stroke()
      } else if (ovl.kind === 'slowdown' && showSlow.value) {
        ctx.fillStyle = '#f97316'
        ctx.beginPath()
        const sz = 2 / s
        ctx.rect(x - sz, y - sz, sz * 2, sz * 2)
        ctx.fill()
      } else if (ovl.kind === 'fillet' && showFillets.value) {
        ctx.fillStyle = '#10b981'
        ctx.beginPath()
        ctx.arc(x, y, 1.5 / s, 0, Math.PI * 2)
        ctx.fill()
      }
    }
  }

  return {
    overlays,
    showTight,
    showSlow,
    showFillets,
    showBottleneckMap,
    draw,
  }
}
