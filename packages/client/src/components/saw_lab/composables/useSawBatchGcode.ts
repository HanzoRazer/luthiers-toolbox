/**
 * Composable for batch G-code generation, preview, and download.
 * Extracted from SawBatchPanel.vue
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import type { SawBlade } from './useSawBladeRegistry'
import type { SlicePath } from './useSawBatchStats'

// ==========================================================================
// Types
// ==========================================================================

export interface BatchGcodeParams {
  numSlices: number
  sliceLength: number
  sliceSpacing: number
  totalDepth: number
  depthPerPass: number
  feedIpm: number
  safeZ: number
}

export interface BatchGcodeState {
  /** Generated G-code */
  gcode: Ref<string>
  /** Has G-code been generated */
  hasGcode: ComputedRef<boolean>
  /** Truncated preview (first/last lines) */
  gcodePreview: ComputedRef<string>
  /** Generate batch G-code */
  generateBatchGcode: () => void
  /** Download G-code as .nc file */
  downloadGcode: () => void
  /** Clear generated G-code */
  clearGcode: () => void
}

// ==========================================================================
// Composable
// ==========================================================================

export function useSawBatchGcode(
  getParams: () => BatchGcodeParams,
  getBlade: () => SawBlade | null,
  getMaterial: () => string,
  getSlicePaths: () => SlicePath[],
  getDepthPasses: () => number,
  getTotalLengthMm: () => number
): BatchGcodeState {
  const gcode = ref<string>('')

  // ==========================================================================
  // Computed
  // ==========================================================================

  const hasGcode = computed(() => gcode.value.length > 0)

  const gcodePreview = computed(() => {
    if (!gcode.value) return ''
    const lines = gcode.value.split('\n')
    return lines.slice(0, 20).join('\n') + '\n...\n' + lines.slice(-5).join('\n')
  })

  // ==========================================================================
  // Methods
  // ==========================================================================

  function generateBatchGcode() {
    const blade = getBlade()
    const params = getParams()
    const material = getMaterial()
    const slicePaths = getSlicePaths()
    const depthPasses = getDepthPasses()
    const totalLengthMm = getTotalLengthMm()

    if (!blade) return

    const lines: string[] = []

    // Header
    lines.push('G21  ; Metric units')
    lines.push('G90  ; Absolute positioning')
    lines.push('G17  ; XY plane')
    lines.push(`(Saw Batch: ${params.numSlices} slices)`)
    lines.push(`(Blade: ${blade.vendor} ${blade.model_code})`)
    lines.push(`(Material: ${material})`)
    lines.push(`(Total length: ${totalLengthMm.toFixed(0)}mm)`)
    lines.push('')

    lines.push(`G0 Z${params.safeZ.toFixed(3)}  ; Safe Z`)
    lines.push('')

    // Process each slice
    slicePaths.forEach((slice, sliceIdx) => {
      lines.push(`; === Slice ${sliceIdx + 1} of ${params.numSlices} ===`)
      lines.push(`G0 X${slice.x1.toFixed(3)} Y${slice.y1.toFixed(3)}  ; Move to slice start`)

      // Multi-pass depth for this slice
      for (let pass = 1; pass <= depthPasses; pass++) {
        const depth = Math.min(pass * params.depthPerPass, params.totalDepth)
        lines.push(`; Pass ${pass}/${depthPasses} (depth: ${depth}mm)`)
        lines.push(
          `G1 Z${-depth.toFixed(3)} F${((params.feedIpm * 25.4) / 5).toFixed(1)}  ; Plunge`
        )
        lines.push(
          `G1 X${slice.x2.toFixed(3)} Y${slice.y2.toFixed(3)} F${(params.feedIpm * 25.4).toFixed(1)}  ; Cut`
        )
        lines.push(`G0 Z${params.safeZ.toFixed(3)}  ; Retract`)

        if (pass < depthPasses) {
          lines.push(`G0 X${slice.x1.toFixed(3)} Y${slice.y1.toFixed(3)}  ; Return to start`)
        }
      }
      lines.push('')
    })

    // Footer
    lines.push(`G0 Z${params.safeZ.toFixed(3)}  ; Final retract`)
    lines.push('M30  ; Program end')

    gcode.value = lines.join('\n')
  }

  function downloadGcode() {
    const blade = getBlade()
    const params = getParams()
    const blob = new Blob([gcode.value], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `saw_batch_${params.numSlices}slices_${blade?.model_code || 'unknown'}.nc`
    a.click()
    URL.revokeObjectURL(url)
  }

  function clearGcode() {
    gcode.value = ''
  }

  return {
    gcode,
    hasGcode,
    gcodePreview,
    generateBatchGcode,
    downloadGcode,
    clearGcode,
  }
}
