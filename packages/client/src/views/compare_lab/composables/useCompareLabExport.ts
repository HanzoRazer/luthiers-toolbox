/**
 * CompareLab export composable.
 */
import type { Ref, ComputedRef } from 'vue'
import { downloadTextFile } from '@/utils/downloadBlob'
import type { DiffResult, ExportFormat } from './compareLabTypes'
import { STORAGE_KEYS } from './compareLabTypes'

// ============================================================================
// Types
// ============================================================================

export interface CompareLabExportReturn {
  executeExport: () => Promise<void>
  exportSvg: () => Promise<void>
  exportPng: () => Promise<void>
  exportCsv: () => Promise<void>
  downloadFile: (content: string, filename: string, mimeType: string) => void
}

// ============================================================================
// Composable
// ============================================================================

export function useCompareLabExport(
  diffResult: Ref<DiffResult | null>,
  exportFormat: Ref<ExportFormat>,
  exportInProgress: Ref<boolean>,
  exportPrefix: Ref<string>,
  exportFilename: ComputedRef<string>,
  showExportDialog: Ref<boolean>
): CompareLabExportReturn {
  /**
   * Download a file with given content.
   */
  function downloadFile(content: string, filename: string, mimeType: string): void {
    downloadTextFile(content, filename, mimeType)
  }

  /**
   * Export as SVG.
   */
  async function exportSvg(): Promise<void> {
    const svg = `<?xml version="1.0" encoding="UTF-8"?>
<!-- Luthier's Tool Box - Compare Lab Export -->
<!-- Baseline: ${diffResult.value?.baseline_name || 'baseline'} -->
<!-- Generated: ${new Date().toISOString()} -->
<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="800" viewBox="0 0 1600 800">
  <style>
    text { font-family: system-ui, sans-serif; font-size: 14px; }
    .title { font-size: 18px; font-weight: bold; }
  </style>

  <!-- Baseline Pane -->
  <g id="baseline">
    <rect x="10" y="10" width="780" height="780" fill="white" stroke="#333" stroke-width="2" />
    <text x="400" y="40" class="title" text-anchor="middle">Baseline</text>
    <text x="400" y="400" text-anchor="middle" fill="#999">Baseline geometry rendering placeholder</text>
  </g>

  <!-- Comparison Pane -->
  <g id="comparison">
    <rect x="810" y="10" width="780" height="780" fill="white" stroke="#333" stroke-width="2" />
    <text x="1200" y="40" class="title" text-anchor="middle">Comparison</text>
    <text x="1200" y="400" text-anchor="middle" fill="#999">Comparison geometry rendering placeholder</text>
  </g>
</svg>`

    downloadFile(svg, exportFilename.value, 'image/svg+xml')
  }

  /**
   * Export as PNG.
   */
  async function exportPng(): Promise<void> {
    const canvas = document.createElement('canvas')
    canvas.width = 1600
    canvas.height = 800
    const ctx = canvas.getContext('2d')

    if (!ctx) {
      throw new Error('Canvas context not available')
    }

    // Draw placeholder
    ctx.fillStyle = 'white'
    ctx.fillRect(0, 0, 1600, 800)
    ctx.fillStyle = '#333'
    ctx.font = '18px system-ui'
    ctx.textAlign = 'center'
    ctx.fillText('Baseline', 400, 40)
    ctx.fillText('Comparison', 1200, 40)
    ctx.strokeRect(10, 10, 780, 780)
    ctx.strokeRect(810, 10, 780, 780)

    return new Promise((resolve, reject) => {
      canvas.toBlob(blob => {
        if (!blob) {
          reject(new Error('Failed to create PNG blob'))
          return
        }
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = exportFilename.value
        a.click()
        URL.revokeObjectURL(url)
        resolve()
      }, 'image/png')
    })
  }

  /**
   * Export as CSV.
   */
  async function exportCsv(): Promise<void> {
    const rows = [
      ['Metric', 'Baseline', 'Comparison', 'Delta', 'Delta %'],
      ['Cycle Time (s)', '32.5', '28.1', '-4.4', '-13.5%'],
      ['Move Count', '156', '142', '-14', '-9.0%'],
      ['Issue Count', '0', '2', '+2', '+∞%'],
      ['Energy (J)', '850', '780', '-70', '-8.2%'],
      ['Max Deviation (%)', '0.5', '0.3', '-0.2', '-40.0%']
    ]

    const csv = rows.map(row => row.map(cell => `"${cell}"`).join(',')).join('\n')
    downloadFile(csv, exportFilename.value, 'text/csv')
  }

  /**
   * Execute export based on selected format.
   */
  async function executeExport(): Promise<void> {
    if (!diffResult.value) return

    // Persist prefix to localStorage
    if (exportPrefix.value.trim()) {
      localStorage.setItem(STORAGE_KEYS.EXPORT_PREFIX, exportPrefix.value.trim())
    }

    exportInProgress.value = true
    try {
      if (exportFormat.value === 'svg') {
        await exportSvg()
      } else if (exportFormat.value === 'png') {
        await exportPng()
      } else if (exportFormat.value === 'csv') {
        await exportCsv()
      }
      showExportDialog.value = false
    } catch (error) {
      console.error('Export failed:', error)
      alert(`Export failed: ${error}`)
    } finally {
      exportInProgress.value = false
    }
  }

  return {
    executeExport,
    exportSvg,
    exportPng,
    exportCsv,
    downloadFile
  }
}
