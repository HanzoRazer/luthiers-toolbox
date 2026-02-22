/**
 * AdaptiveKernelLab preview composable.
 */
import { computed, type Ref, type ComputedRef } from 'vue'
import type { AdaptivePlanOut } from '@/api/adaptive'
import type { PreviewLoop, ToolpathSegment, ViewBox } from './adaptiveKernelTypes'

// ============================================================================
// Types
// ============================================================================

export interface AdaptiveKernelPreviewReturn {
  previewLoops: ComputedRef<PreviewLoop[]>
  previewOverlays: ComputedRef<any[]>
  viewBox: ComputedRef<ViewBox>
  previewToolpathSegments: ComputedRef<ToolpathSegment[]>
}

// ============================================================================
// Composable
// ============================================================================

export function useAdaptiveKernelPreview(
  loopsText: Ref<string>,
  result: Ref<AdaptivePlanOut | null>
): AdaptiveKernelPreviewReturn {
  /**
   * Parse loops from JSON text for preview.
   */
  const previewLoops = computed<PreviewLoop[]>(() => {
    try {
      const parsed = JSON.parse(loopsText.value || '[]')
      if (!Array.isArray(parsed)) return []
      return parsed.map((l: any) => ({
        pts: (l.pts || []).map((p: any) => [Number(p[0]), Number(p[1])]) as [
          number,
          number
        ][]
      }))
    } catch {
      return []
    }
  })

  /**
   * Get overlays from result.
   */
  const previewOverlays = computed(() => result.value?.overlays || [])

  /**
   * Calculate viewBox from loops.
   */
  const viewBox = computed<ViewBox>(() => {
    const loops = previewLoops.value
    if (!loops.length) return { x: 0, y: 0, w: 100, h: 60 }

    const xs: number[] = []
    const ys: number[] = []
    loops.forEach((l) =>
      l.pts.forEach(([x, y]) => {
        xs.push(x)
        ys.push(y)
      })
    )
    const minX = Math.min(...xs)
    const maxX = Math.max(...xs)
    const minY = Math.min(...ys)
    const maxY = Math.max(...ys)
    const pad = 5
    return {
      x: minX - pad,
      y: minY - pad,
      w: maxX - minX + 2 * pad,
      h: maxY - minY + 2 * pad
    }
  })

  /**
   * Build toolpath segments from result moves.
   */
  const previewToolpathSegments = computed<ToolpathSegment[]>(() => {
    const r = result.value
    if (!r || !Array.isArray(r.moves)) return []

    const segments: ToolpathSegment[] = []
    let current: [number, number][] = []
    let currentKind: 'rapid' | 'cut' | null = null

    const moves = r.moves as any[]

    for (const mv of moves) {
      const x = mv.x
      const y = mv.y

      if (typeof x !== 'number' || typeof y !== 'number') {
        // break path when there's no XY
        if (current.length > 1 && currentKind) {
          segments.push({ pts: current, kind: currentKind })
        }
        current = []
        currentKind = null
        continue
      }

      // classify move kind: simple heuristic
      const code = (mv.code || '').toUpperCase()
      const z = typeof mv.z === 'number' ? mv.z : null

      let kind: 'rapid' | 'cut'
      if (code === 'G0' || (z !== null && z > 0)) {
        kind = 'rapid'
      } else {
        kind = 'cut'
      }

      // if kind changes, finalize previous segment
      if (currentKind !== null && kind !== currentKind && current.length > 1) {
        segments.push({ pts: current, kind: currentKind })
        current = []
      }

      currentKind = kind
      current.push([x, y])
    }

    if (current.length > 1 && currentKind) {
      segments.push({ pts: current, kind: currentKind })
    }

    return segments
  })

  return {
    previewLoops,
    previewOverlays,
    viewBox,
    previewToolpathSegments
  }
}
