/**
 * RosetteCompare path coloring composable.
 */
import { computed, type Ref, type ComputedRef } from 'vue'
import type { RosetteCompareResult, RosettePath } from './rosetteCompareTypes'

// ============================================================================
// Types
// ============================================================================

export interface RosetteComparePathsReturn {
  viewBoxUnion: ComputedRef<string>
  commonPathCount: ComputedRef<number>
  unchangedPathsA: ComputedRef<RosettePath[]>
  addedPathsA: ComputedRef<RosettePath[]>
  unchangedPathsB: ComputedRef<RosettePath[]>
  addedPathsB: ComputedRef<RosettePath[]>
  polylinePoints: (pts: [number, number][]) => string
}

// ============================================================================
// Composable
// ============================================================================

export function useRosetteComparePaths(
  compareResult: Ref<RosetteCompareResult | null>
): RosetteComparePathsReturn {
  /**
   * Compute SVG viewBox from union bounding box.
   */
  const viewBoxUnion = computed(() => {
    if (!compareResult.value) return '-60 -60 120 120'
    const u = compareResult.value.diff_summary.bbox_union
    const pad = 5
    const width = u[2] - u[0] || 1
    const height = u[3] - u[1] || 1
    const x = u[0] - pad
    const y = u[1] - pad
    const w = width + pad * 2
    const h = height + pad * 2
    return `${x} ${y} ${w} ${h}`
  })

  /**
   * Common path count between A and B (minimum of both).
   */
  const commonPathCount = computed(() => {
    if (!compareResult.value) return 0
    return Math.min(
      compareResult.value.job_a.paths.length,
      compareResult.value.job_b.paths.length
    )
  })

  /**
   * Unchanged paths in A (common segment count).
   */
  const unchangedPathsA = computed(() => {
    if (!compareResult.value) return []
    return compareResult.value.job_a.paths.slice(0, commonPathCount.value)
  })

  /**
   * Added paths in A (A has more segments than B).
   */
  const addedPathsA = computed(() => {
    if (!compareResult.value) return []
    return compareResult.value.job_a.paths.slice(commonPathCount.value)
  })

  /**
   * Unchanged paths in B (common segment count).
   */
  const unchangedPathsB = computed(() => {
    if (!compareResult.value) return []
    return compareResult.value.job_b.paths.slice(0, commonPathCount.value)
  })

  /**
   * Added paths in B (B has more segments than A).
   */
  const addedPathsB = computed(() => {
    if (!compareResult.value) return []
    return compareResult.value.job_b.paths.slice(commonPathCount.value)
  })

  /**
   * Convert points array to SVG polyline points string.
   */
  function polylinePoints(pts: [number, number][]): string {
    return pts.map(([x, y]) => `${x},${y}`).join(' ')
  }

  return {
    viewBoxUnion,
    commonPathCount,
    unchangedPathsA,
    addedPathsA,
    unchangedPathsB,
    addedPathsB,
    polylinePoints
  }
}
