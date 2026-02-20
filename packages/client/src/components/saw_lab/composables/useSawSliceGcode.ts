/**
 * Composable for G-code generation, preview, and statistics.
 * Extracted from SawSlicePanel.vue
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import type { SawBlade } from './useSawBladeRegistry'

// ==========================================================================
// Types
// ==========================================================================

export interface SliceGeometry {
  startX: number
  startY: number
  endX: number
  endY: number
}

export interface SliceParams {
  totalDepth: number
  depthPerPass: number
  rpm: number
  feedIpm: number
  safeZ: number
}

export interface GcodeState {
  /** Generated G-code */
  gcode: Ref<string>
  /** Has G-code been generated */
  hasGcode: ComputedRef<boolean>
  /** Path length in mm */
  pathLengthMm: ComputedRef<number>
  /** Number of depth passes */
  depthPasses: ComputedRef<number>
  /** Total cut length (path * passes) */
  totalLengthMm: ComputedRef<number>
  /** Estimated time in seconds */
  estimatedTimeSec: ComputedRef<number>
  /** Truncated preview (first/last lines) */
  gcodePreview: ComputedRef<string>
  /** SVG viewBox string */
  svgViewBox: ComputedRef<string>
  /** Generate G-code from current params */
  generateGcode: () => void
  /** Download G-code as .nc file */
  downloadGcode: () => void
  /** Clear generated G-code */
  clearGcode: () => void
}

// ==========================================================================
// Composable
// ==========================================================================

export function useSawSliceGcode(
  getGeometry: () => SliceGeometry,
  getParams: () => SliceParams,
  getBlade: () => SawBlade | null,
  getMaterial: () => string
): GcodeState {
  const gcode = ref<string>('')

  // ==========================================================================
  // Computed
  // ==========================================================================

  const hasGcode = computed(() => gcode.value.length > 0)

  const pathLengthMm = computed(() => {
    const geo = getGeometry()
    const dx = geo.endX - geo.startX
    const dy = geo.endY - geo.startY
    return Math.sqrt(dx * dx + dy * dy)
  })

  const depthPasses = computed(() => {
    const params = getParams()
    return Math.ceil(params.totalDepth / params.depthPerPass)
  })

  const totalLengthMm = computed(() => {
    return pathLengthMm.value * depthPasses.value
  })

  const estimatedTimeSec = computed(() => {
    const params = getParams()
    // Convert IPM to mm/min
    const feedMmMin = params.feedIpm * 25.4
    // Time = distance / speed
    return (totalLengthMm.value / feedMmMin) * 60
  })

  const gcodePreview = computed(() => {
    if (!gcode.value) return ''
    const lines = gcode.value.split('\n')
    return lines.slice(0, 20).join('\n') + '\n...\n' + lines.slice(-5).join('\n')
  })

  const svgViewBox = computed(() => {
    const geo = getGeometry()
    const padding = 20
    const minX = Math.min(geo.startX, geo.endX) - padding
    const minY = Math.min(geo.startY, geo.endY) - padding
    const maxX = Math.max(geo.startX, geo.endX) + padding
    const maxY = Math.max(geo.startY, geo.endY) + padding
    return `${minX} ${minY} ${maxX - minX} ${maxY - minY}`
  })

  // ==========================================================================
  // Methods
  // ==========================================================================

  function generateGcode() {
    const blade = getBlade()
    const geo = getGeometry()
    const params = getParams()
    const material = getMaterial()
    const passes = depthPasses.value

    if (!blade) return

    const lines: string[] = []

    // Header
    lines.push('G21  ; Metric units')
    lines.push('G90  ; Absolute positioning')
    lines.push('G17  ; XY plane')
    lines.push(`(Saw Slice: ${blade.vendor} ${blade.model_code})`)
    lines.push(`(Material: ${material})`)
    lines.push(`(Total depth: ${params.totalDepth}mm in ${passes} passes)`)
    lines.push('')

    // Rapid to start
    lines.push(`G0 Z${params.safeZ.toFixed(3)}  ; Safe Z`)
    lines.push(`G0 X${geo.startX.toFixed(3)} Y${geo.startY.toFixed(3)}  ; Move to start`)
    lines.push('')

    // Multi-pass depth
    for (let pass = 1; pass <= passes; pass++) {
      const depth = Math.min(pass * params.depthPerPass, params.totalDepth)
      lines.push(`; Pass ${pass} of ${passes} (depth: ${depth}mm)`)
      lines.push(`G1 Z${-depth.toFixed(3)} F${((params.feedIpm * 25.4) / 5).toFixed(1)}  ; Plunge`)
      lines.push(
        `G1 X${geo.endX.toFixed(3)} Y${geo.endY.toFixed(3)} F${(params.feedIpm * 25.4).toFixed(1)}  ; Cut`
      )
      lines.push(`G0 Z${params.safeZ.toFixed(3)}  ; Retract`)

      if (pass < passes) {
        lines.push(`G0 X${geo.startX.toFixed(3)} Y${geo.startY.toFixed(3)}  ; Return to start`)
      }
      lines.push('')
    }

    // Footer
    lines.push(`G0 Z${params.safeZ.toFixed(3)}  ; Final retract`)
    lines.push('M30  ; Program end')

    gcode.value = lines.join('\n')
  }

  function downloadGcode() {
    const blade = getBlade()
    const blob = new Blob([gcode.value], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `saw_slice_${blade?.model_code || 'unknown'}.nc`
    a.click()
    URL.revokeObjectURL(url)
  }

  function clearGcode() {
    gcode.value = ''
  }

  return {
    gcode,
    hasGcode,
    pathLengthMm,
    depthPasses,
    totalLengthMm,
    estimatedTimeSec,
    gcodePreview,
    svgViewBox,
    generateGcode,
    downloadGcode,
    clearGcode,
  }
}
