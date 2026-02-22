/**
 * Composable for contour G-code generation, preview, and statistics.
 * Extracted from SawContourPanel.vue
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import type { SawBlade } from './useSawBladeRegistry'
import type { ContourType } from './useSawContourPath'

// ==========================================================================
// Types
// ==========================================================================

export interface ContourGeometry {
  contourType: ContourType
  centerX: number
  centerY: number
  radius: number
}

export interface ContourParams {
  totalDepth: number
  depthPerPass: number
  rpm: number
  feedIpm: number
  safeZ: number
}

export interface ContourGcodeState {
  /** Generated G-code */
  gcode: Ref<string>
  /** Has G-code been generated */
  hasGcode: ComputedRef<boolean>
  /** Number of depth passes */
  depthPasses: ComputedRef<number>
  /** Total cut length (path * passes) */
  totalLengthMm: ComputedRef<number>
  /** Estimated time in seconds */
  estimatedTimeSec: ComputedRef<number>
  /** Truncated preview (first/last lines) */
  gcodePreview: ComputedRef<string>
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

export function useSawContourGcode(
  getGeometry: () => ContourGeometry,
  getParams: () => ContourParams,
  getBlade: () => SawBlade | null,
  getPathLengthMm: () => number
): ContourGcodeState {
  const gcode = ref('')

  // ==========================================================================
  // Computed
  // ==========================================================================

  const hasGcode = computed(() => gcode.value.length > 0)

  const depthPasses = computed(() => {
    const params = getParams()
    return Math.ceil(params.totalDepth / params.depthPerPass)
  })

  const totalLengthMm = computed(() => {
    return getPathLengthMm() * depthPasses.value
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

  // ==========================================================================
  // Methods
  // ==========================================================================

  function generateGcode() {
    const blade = getBlade()
    const geo = getGeometry()
    const params = getParams()
    const passes = depthPasses.value

    if (!blade) return

    const lines: string[] = []

    // Header
    lines.push('G21  ; Metric units')
    lines.push('G90  ; Absolute positioning')
    lines.push('G17  ; XY plane')
    lines.push(`(Saw Contour: ${geo.contourType})`)
    lines.push(`(Blade: ${blade.vendor} ${blade.model_code})`)
    lines.push(`(Total depth: ${params.totalDepth}mm in ${passes} passes)`)
    lines.push('')

    lines.push(`G0 Z${params.safeZ.toFixed(3)}  ; Safe Z`)

    // Generate contour moves
    for (let pass = 1; pass <= passes; pass++) {
      const depth = Math.min(pass * params.depthPerPass, params.totalDepth)
      lines.push(`; Pass ${pass} of ${passes} (depth: ${depth}mm)`)

      if (geo.contourType === 'circle') {
        const startX = geo.centerX + geo.radius
        const startY = geo.centerY

        lines.push(`G0 X${startX.toFixed(3)} Y${startY.toFixed(3)}  ; Move to start`)
        lines.push(`G1 Z${-depth.toFixed(3)} F${((params.feedIpm * 25.4) / 5).toFixed(1)}  ; Plunge`)
        lines.push(
          `G2 I${(-geo.radius).toFixed(3)} J0 F${(params.feedIpm * 25.4).toFixed(1)}  ; Cut circle`
        )
        lines.push(`G0 Z${params.safeZ.toFixed(3)}  ; Retract`)
      } else {
        // Arc or rosette - simplified
        lines.push(`; Contour path - simplified`)
        lines.push(`G0 X${geo.centerX.toFixed(3)} Y${geo.centerY.toFixed(3)}`)
        lines.push(`G1 Z${-depth.toFixed(3)} F${((params.feedIpm * 25.4) / 5).toFixed(1)}`)
        lines.push(`; (Arc/rosette moves would be generated here)`)
        lines.push(`G0 Z${params.safeZ.toFixed(3)}`)
      }
      lines.push('')
    }

    lines.push('M30  ; Program end')

    gcode.value = lines.join('\n')
  }

  function downloadGcode() {
    const blade = getBlade()
    const geo = getGeometry()
    const blob = new Blob([gcode.value], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `saw_contour_${geo.contourType}_${blade?.model_code || 'unknown'}.nc`
    a.click()
    URL.revokeObjectURL(url)
  }

  function clearGcode() {
    gcode.value = ''
  }

  return {
    gcode,
    hasGcode,
    depthPasses,
    totalLengthMm,
    estimatedTimeSec,
    gcodePreview,
    generateGcode,
    downloadGcode,
    clearGcode,
  }
}
