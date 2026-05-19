/**
 * useExportDxf
 *
 * Calls POST /api/export/headstock-dxf with the current workspace state.
 * Wires into WorkspaceView via the export button (or a dedicated Export modal).
 *
 * Usage in WorkspaceView:
 *   const { exportDxf, previewing, previewPoints, exportOptions } = useExportDxf()
 *   // trigger download:
 *   await exportDxf(currentHS(), inlays, canvas)
 */

import { ref, reactive } from 'vue'
import type { HsModel, InlayLayer } from '@/types/headstock'
import type { KonvaCanvas } from './useKonvaCanvas'
import { buildTunerPositions } from './useParametric'
import { MM } from '@/assets/data/headstockData'
import type { ParametricParams, TunerPattern } from '@/types/headstock'
import Konva from 'konva'

const API_BASE = (import.meta.env.VITE_API_BASE ?? '') + '/api/export'

// ─── Export options (user-configurable in the UI) ─────────────────────────────
export interface ExportOptions {
  kerfMm:       number
  toolDiaMm:    number
  dogbone:      boolean
  includeInlays: boolean
  label:        string
}

// ─── Inlay pocket path extractor ──────────────────────────────────────────────
function inlayToPathD(layer: InlayLayer, canvas: KonvaCanvas): string | null {
  const ch = layer.node.children?.[0]
  if (!ch) return null

  const x  = canvas.c2px(layer.node.x())
  const y  = canvas.c2py(layer.node.y())
  const s  = layer.node.scaleX()
  const r  = layer.node.rotation() * Math.PI / 180

  // Rotate helper
  const rot = (px: number, py: number) => ({
    x: x + (px * Math.cos(r) - py * Math.sin(r)) * s,
    y: y + (px * Math.sin(r) + py * Math.cos(r)) * s,
  })

  if (ch instanceof Konva.Circle) {
    const radius = (ch as Konva.Circle).radius() * s
    return `M${(x-radius).toFixed(2)},${y.toFixed(2)} A${radius.toFixed(2)},${radius.toFixed(2)},0,1,0,${(x+radius).toFixed(2)},${y.toFixed(2)} A${radius.toFixed(2)},${radius.toFixed(2)},0,1,0,${(x-radius).toFixed(2)},${y.toFixed(2)} Z`
  }

  if (ch instanceof Konva.Rect) {
    const w = (ch as Konva.Rect).width() * s
    const h = (ch as Konva.Rect).height() * s
    const ox = (ch as Konva.Rect).offsetX() * s
    const oy = (ch as Konva.Rect).offsetY() * s
    const corners = [[-ox,-oy],[w-ox,-oy],[w-ox,h-oy],[-ox,h-oy]].map(([px,py]) => rot(px,py))
    return `M${corners.map(c=>`${c.x.toFixed(2)},${c.y.toFixed(2)}`).join('L')}Z`
  }

  if (ch instanceof Konva.Ellipse) {
    const rx = (ch as Konva.Ellipse).radiusX() * s
    const ry = (ch as Konva.Ellipse).radiusY() * s
    return `M${(x-rx).toFixed(2)},${y.toFixed(2)} A${rx.toFixed(2)},${ry.toFixed(2)},0,1,0,${(x+rx).toFixed(2)},${y.toFixed(2)} A${rx.toFixed(2)},${ry.toFixed(2)},0,1,0,${(x-rx).toFixed(2)},${y.toFixed(2)} Z`
  }

  if (ch instanceof Konva.Path) {
    // Already a path — apply transform manually via offscreen SVG
    const svgEl = document.createElementNS('http://www.w3.org/2000/svg','svg')
    svgEl.setAttribute('viewBox','0 0 200 320')
    svgEl.style.cssText='position:fixed;top:-9999px;visibility:hidden;width:200px;height:320px'
    const g = document.createElementNS('http://www.w3.org/2000/svg','g')
    g.setAttribute('transform',`translate(${x},${y}) rotate(${layer.node.rotation()}) scale(${s})`)
    const pe = document.createElementNS('http://www.w3.org/2000/svg','path') as SVGPathElement
    pe.setAttribute('d',(ch as Konva.Path).data())
    g.appendChild(pe); svgEl.appendChild(g); document.body.appendChild(svgEl)
    try {
      const len = pe.getTotalLength(), samp = Math.min(Math.ceil(len/3)+4, 256)
      let d = ''
      for(let i=0;i<=samp;i++){const pt=pe.getPointAtLength(i/samp*len);d+=(i===0?'M':'L')+pt.x.toFixed(2)+','+pt.y.toFixed(2)}
      document.body.removeChild(svgEl)
      return d + 'Z'
    } catch { document.body.removeChild(svgEl); return null }
  }

  return null
}

// ─── Main composable ──────────────────────────────────────────────────────────

export function useExportDxf() {
  const loading = ref(false)
  const error   = ref<string | null>(null)
  const previewPoints = ref<{x:number;y:number}[]>([])
  const previewBBox   = ref<{w_mm:number;h_mm:number} | null>(null)

  const exportOptions = reactive<ExportOptions>({
    kerfMm:        3.175,
    toolDiaMm:     3.175,
    dogbone:       true,
    includeInlays: true,
    label:         'Headstock',
  })

  // Build the POST body from current workspace state
  function buildPayload(
    hs: HsModel,
    inlays: any[],
    canvas: KonvaCanvas,
    tunerPositions?: {x:number;y:number}[],
  ) {
    const inlayPockets = exportOptions.includeInlays
      ? inlays.filter(l => l.visible).map(l => ({
          path_d: inlayToPathD(l, canvas) ?? '',
          depth: 2.0,
          label: l.name,
        })).filter(p => p.path_d)
      : []

    // Tuner holes — use provided positions or extract from model tuners
    const tuners = (tunerPositions ?? hs.tuners.map(([x,y]) => ({x,y}))).map(t => ({
      x: t.x,
      y: t.y,
      radius: 4.0,   // default peg hole — 0.86mm at current scale
    }))

    return {
      outline_path:  hs.path,
      tuner_holes:   tuners,
      inlay_pockets: inlayPockets,
      nut_x1:        hs.cx - hs.nw / 2,
      nut_x2:        hs.cx + hs.nw / 2,
      nut_y:         hs.nutY,
      nut_width_mm:  hs.nw * MM,
      kerf_mm:       exportOptions.kerfMm,
      dogbone:       exportOptions.dogbone,
      tool_dia_mm:   exportOptions.toolDiaMm,
      label:         exportOptions.label,
    }
  }

  async function fetchPreview(hs: HsModel, inlays: any[], canvas: KonvaCanvas) {
    loading.value = true; error.value = null
    try {
      const res = await fetch(`${API_BASE}/headstock-dxf/preview`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(buildPayload(hs, inlays, canvas)),
      })
      if (!res.ok) throw new Error(`Server ${res.status}`)
      const data = await res.json()
      previewPoints.value = data.outline ?? []
      previewBBox.value   = data.bounding_box ?? null
    } catch (e) {
      error.value = String(e)
    } finally {
      loading.value = false
    }
  }

  async function exportDxf(hs: HsModel, inlays: any[], canvas: KonvaCanvas) {
    loading.value = true; error.value = null
    try {
      const res = await fetch(`${API_BASE}/headstock-dxf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(buildPayload(hs, inlays, canvas)),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail ?? 'Export failed')
      }
      const blob = await res.blob()
      const label = exportOptions.label.toLowerCase().replace(/\s+/g, '-') || 'headstock'
      const a = Object.assign(document.createElement('a'), {
        href: URL.createObjectURL(blob),
        download: `${label}.dxf`,
      })
      a.click()
    } catch (e) {
      error.value = String(e)
    } finally {
      loading.value = false
    }
  }

  return { loading, error, exportOptions, previewPoints, previewBBox, fetchPreview, exportDxf }
}
