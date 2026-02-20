/**
 * Composable for batch statistics and slice path generation.
 * Extracted from SawBatchPanel.vue
 */
import { computed, type ComputedRef } from 'vue'
import type { SawBlade } from './useSawBladeRegistry'

// ==========================================================================
// Types
// ==========================================================================

export interface SlicePath {
  x1: number
  y1: number
  x2: number
  y2: number
}

export interface BatchParams {
  numSlices: number
  sliceSpacing: number
  sliceLength: number
  startX: number
  startY: number
  orientation: 'horizontal' | 'vertical'
  totalDepth: number
  depthPerPass: number
  feedIpm: number
}

export interface BatchStatsState {
  /** Number of depth passes per slice */
  depthPasses: ComputedRef<number>
  /** Total passes (slices * depth passes) */
  totalPasses: ComputedRef<number>
  /** Total cutting length in mm */
  totalLengthMm: ComputedRef<number>
  /** Estimated cutting time in seconds */
  estimatedTimeSec: ComputedRef<number>
  /** Total material volume removed in mm³ */
  totalVolumeMm3: ComputedRef<number>
  /** Kerf loss volume in mm³ */
  kerfLossMm3: ComputedRef<number>
  /** Array of slice paths for preview */
  slicePaths: ComputedRef<SlicePath[]>
  /** SVG viewBox for path preview */
  svgViewBox: ComputedRef<string>
  /** Format seconds to human-readable time */
  formatTime: (seconds: number) => string
}

// ==========================================================================
// Composable
// ==========================================================================

export function useSawBatchStats(
  getParams: () => BatchParams,
  getBlade: () => SawBlade | null
): BatchStatsState {
  // ==========================================================================
  // Computed
  // ==========================================================================

  const depthPasses = computed(() => {
    const params = getParams()
    return Math.ceil(params.totalDepth / params.depthPerPass)
  })

  const totalPasses = computed(() => {
    const params = getParams()
    return params.numSlices * depthPasses.value
  })

  const totalLengthMm = computed(() => {
    const params = getParams()
    return params.sliceLength * params.numSlices * depthPasses.value
  })

  const estimatedTimeSec = computed(() => {
    const params = getParams()
    const feedMmMin = params.feedIpm * 25.4
    const cuttingTime = (totalLengthMm.value / feedMmMin) * 60
    // Add overhead for retracts and rapids
    const overheadTime = totalPasses.value * 3 // 3s per pass
    return cuttingTime + overheadTime
  })

  const totalVolumeMm3 = computed(() => {
    const blade = getBlade()
    if (!blade) return 0
    const params = getParams()
    return params.sliceLength * blade.kerf_mm * params.totalDepth * params.numSlices
  })

  const kerfLossMm3 = computed(() => {
    return totalVolumeMm3.value // All material is kerf loss in slicing
  })

  const slicePaths = computed<SlicePath[]>(() => {
    const params = getParams()
    const paths: SlicePath[] = []

    for (let i = 0; i < params.numSlices; i++) {
      if (params.orientation === 'horizontal') {
        paths.push({
          x1: params.startX,
          y1: params.startY + i * params.sliceSpacing,
          x2: params.startX + params.sliceLength,
          y2: params.startY + i * params.sliceSpacing,
        })
      } else {
        paths.push({
          x1: params.startX + i * params.sliceSpacing,
          y1: params.startY,
          x2: params.startX + i * params.sliceSpacing,
          y2: params.startY + params.sliceLength,
        })
      }
    }
    return paths
  })

  const svgViewBox = computed(() => {
    if (slicePaths.value.length === 0) return '0 0 200 200'

    const allX = slicePaths.value.flatMap((s) => [s.x1, s.x2])
    const allY = slicePaths.value.flatMap((s) => [s.y1, s.y2])

    const padding = 30
    const minX = Math.min(...allX) - padding
    const minY = Math.min(...allY) - padding
    const maxX = Math.max(...allX) + padding
    const maxY = Math.max(...allY) + padding

    return `${minX} ${minY} ${maxX - minX} ${maxY - minY}`
  })

  // ==========================================================================
  // Utilities
  // ==========================================================================

  function formatTime(seconds: number): string {
    const min = Math.floor(seconds / 60)
    const sec = Math.floor(seconds % 60)
    return `${min}m ${sec}s`
  }

  return {
    depthPasses,
    totalPasses,
    totalLengthMm,
    estimatedTimeSec,
    totalVolumeMm3,
    kerfLossMm3,
    slicePaths,
    svgViewBox,
    formatTime,
  }
}
