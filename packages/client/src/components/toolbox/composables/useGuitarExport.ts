/**
 * useGuitarExport - Composable for guitar dimension export operations
 *
 * Handles:
 * - JSON export
 * - CSV export
 * - Clipboard copy
 * - DXF/SVG generation via API
 */

import { ref } from 'vue'
import { api } from '@/services/apiBase'
import type { GuitarDimensions } from './useGuitarDimensions'

export interface ExportOptions {
  dimensions: GuitarDimensions
  guitarType: string
  units: 'mm' | 'inch'
  currentUnit: string
}

export function useGuitarExport() {
  const isExporting = ref(false)

  // Download helper
  function downloadBlob(blob: Blob, filename: string) {
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  // Export as JSON file
  function exportJSON(options: ExportOptions): boolean {
    try {
      const data = {
        type: options.guitarType,
        units: options.units,
        dimensions: options.dimensions,
        timestamp: new Date().toISOString(),
      }

      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      downloadBlob(blob, `guitar-dimensions-${Date.now()}.json`)
      return true
    } catch {
      return false
    }
  }

  // Export as CSV file
  function exportCSV(options: ExportOptions): boolean {
    try {
      const headers = ['Dimension', 'Value', 'Unit']
      const rows = [
        ['Body Length', options.dimensions.bodyLength, options.currentUnit],
        ['Upper Bout Width', options.dimensions.bodyWidthUpper, options.currentUnit],
        ['Lower Bout Width', options.dimensions.bodyWidthLower, options.currentUnit],
        ['Waist Width', options.dimensions.waistWidth, options.currentUnit],
        ['Body Depth', options.dimensions.bodyDepth, options.currentUnit],
        ['Scale Length', options.dimensions.scaleLength, options.currentUnit],
        ['Nut Width', options.dimensions.nutWidth, options.currentUnit],
        ['Bridge Spacing', options.dimensions.bridgeSpacing, options.currentUnit],
        ['Fret Count', options.dimensions.fretCount, 'frets'],
        ['Neck Angle', options.dimensions.neckAngle, 'degrees'],
      ]

      const csv = [headers, ...rows].map((row) => row.join(',')).join('\n')
      const blob = new Blob([csv], { type: 'text/csv' })
      downloadBlob(blob, `guitar-dimensions-${Date.now()}.csv`)
      return true
    } catch {
      return false
    }
  }

  // Copy to clipboard
  async function copyToClipboard(options: ExportOptions): Promise<boolean> {
    try {
      const text = Object.entries(options.dimensions)
        .map(([key, value]) => {
          const unit = key.includes('Angle')
            ? '°'
            : key === 'fretCount'
              ? ''
              : options.currentUnit
          return `${key}: ${value}${unit}`
        })
        .join('\n')

      await navigator.clipboard.writeText(text)
      return true
    } catch {
      return false
    }
  }

  // Generate and export DXF
  async function generateDXF(options: ExportOptions): Promise<{ success: boolean; error?: string }> {
    isExporting.value = true
    try {
      const response = await api('/api/guitar/design/parametric/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dimensions: options.dimensions,
          guitarType: options.guitarType.charAt(0).toUpperCase() + options.guitarType.slice(1),
          units: options.units,
          format: 'dxf',
          resolution: 48,
        }),
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`HTTP ${response.status}: ${errorText}`)
      }

      const blob = await response.blob()
      const filename =
        response.headers.get('content-disposition')?.split('filename=')[1]?.replace(/"/g, '') ||
        `guitar_body_${Date.now()}.dxf`
      downloadBlob(blob, filename)

      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      }
    } finally {
      isExporting.value = false
    }
  }

  // Generate and export SVG
  async function generateSVG(options: ExportOptions): Promise<{ success: boolean; error?: string }> {
    isExporting.value = true
    try {
      const response = await api('/api/guitar/design/parametric/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dimensions: options.dimensions,
          guitarType: options.guitarType.charAt(0).toUpperCase() + options.guitarType.slice(1),
          units: options.units,
          format: 'svg',
          resolution: 48,
        }),
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`HTTP ${response.status}: ${errorText}`)
      }

      const blob = await response.blob()
      const filename =
        response.headers.get('content-disposition')?.split('filename=')[1]?.replace(/"/g, '') ||
        `guitar_body_${Date.now()}.svg`
      downloadBlob(blob, filename)

      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      }
    } finally {
      isExporting.value = false
    }
  }

  return {
    isExporting,
    exportJSON,
    exportCSV,
    copyToClipboard,
    generateDXF,
    generateSVG,
  }
}
