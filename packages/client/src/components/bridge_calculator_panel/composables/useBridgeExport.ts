/**
 * BridgeCalculatorPanel export operations composable.
 */
import type { Ref, ComputedRef } from 'vue'
import { api } from '@/services/apiBase'
import type { UnitMode, UiFieldKey, Point2D, BridgeModel } from './bridgeCalculatorTypes'

export interface BridgeExportReturn {
  currentModel: () => BridgeModel
  copyJSON: () => Promise<void>
  downloadSVG: () => void
  exportDXF: () => Promise<void>
  fmt: (value: number) => string
}

export function useBridgeExport(
  ui: Record<UiFieldKey, number>,
  unitMode: ComputedRef<UnitMode>,
  angleDeg: ComputedRef<number>,
  treble: ComputedRef<Point2D>,
  bass: ComputedRef<Point2D>,
  slotPoly: ComputedRef<Point2D[]>,
  svgViewBox: ComputedRef<string>,
  svgH: ComputedRef<number>,
  scale: ComputedRef<number>,
  slotPolygonPoints: ComputedRef<string>,
  exporting: Ref<boolean>,
  statusMessage: Ref<string | null>,
  emit: (event: 'dxf-generated', file: File) => void
): BridgeExportReturn {
  /**
   * Round to 2 decimal places.
   */
  function round2(value: number): number {
    return Math.round(value * 100) / 100
  }

  /**
   * Round to 3 decimal places.
   */
  function round3(value: number): number {
    return Math.round(value * 1000) / 1000
  }

  /**
   * Format number with 2 decimal places.
   */
  function fmt(value: number): string {
    return value.toFixed(2)
  }

  /**
   * Build current bridge model for export.
   */
  function currentModel(): BridgeModel {
    return {
      units: unitMode.value,
      scaleLength: round2(ui.scale),
      stringSpread: round2(ui.spread),
      compTreble: round2(ui.compTreble),
      compBass: round2(ui.compBass),
      slotWidth: round2(ui.slotWidth),
      slotLength: round2(ui.slotLength),
      angleDeg: round3(angleDeg.value),
      endpoints: {
        treble: { x: round3(treble.value.x), y: round3(treble.value.y) },
        bass: { x: round3(bass.value.x), y: round3(bass.value.y) }
      },
      slotPolygon: slotPoly.value.map((p) => ({ x: round3(p.x), y: round3(p.y) }))
    }
  }

  /**
   * Copy model JSON to clipboard.
   */
  async function copyJSON(): Promise<void> {
    try {
      await navigator.clipboard?.writeText(JSON.stringify(currentModel(), null, 2))
      statusMessage.value = 'Model JSON copied to clipboard.'
    } catch (error) {
      console.error('Clipboard error', error)
      statusMessage.value = 'Unable to copy JSON — clipboard permissions denied.'
    }
  }

  /**
   * Download SVG preview file.
   */
  function downloadSVG(): void {
    const vb = svgViewBox.value.split(' ').map(Number)
    const svg = `<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="${vb.join(' ')}">
  <line x1="0" y1="${-svgH.value / 2}" x2="0" y2="${svgH.value / 2}" stroke="#cbd5f5" stroke-dasharray="2,2" stroke-width="0.3"/>
  <line x1="${scale.value}" y1="-3" x2="${scale.value}" y2="3" stroke="#94a3b8" stroke-width="0.4"/>
  <line x1="${treble.value.x}" y1="${treble.value.y}" x2="${bass.value.x}" y2="${bass.value.y}" stroke="#0ea5e9" stroke-width="0.7"/>
  <polygon points="${slotPolygonPoints.value}" fill="rgba(14,165,233,0.2)" stroke="#0284c7" stroke-width="0.5"/>
</svg>`
    const blob = new Blob([svg], { type: 'image/svg+xml' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `bridge_saddle_${unitMode.value}.svg`
    a.click()
    URL.revokeObjectURL(url)
  }

  /**
   * Export DXF file via API.
   */
  async function exportDXF(): Promise<void> {
    try {
      exporting.value = true
      statusMessage.value = null
      const model = currentModel()
      const payload = {
        geometry: model,
        filename: `bridge_${model.scaleLength.toFixed(1)}${model.units}_ct${model.compTreble.toFixed(1)}_cb${model.compBass.toFixed(1)}`
      }
      const response = await api('/api/cam/bridge/export_dxf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      if (!response.ok) {
        throw new Error(await response.text())
      }
      const blob = await response.blob()
      const fileName = `${payload.filename}.dxf`
      const file = new File([blob], fileName, { type: 'application/dxf' })
      emit('dxf-generated', file)

      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = fileName
      a.click()
      URL.revokeObjectURL(url)

      statusMessage.value = `DXF exported: ${fileName}`
    } catch (error) {
      console.error('DXF export error', error)
      statusMessage.value = `DXF export failed: ${error instanceof Error ? error.message : error}`
    } finally {
      exporting.value = false
    }
  }

  return {
    currentModel,
    copyJSON,
    downloadSVG,
    exportDXF,
    fmt
  }
}
