/**
 * ArtStudioRelief backplot computed values composable.
 */
import { computed, type Ref, type ComputedRef } from 'vue'
import type { BackplotMove, BackplotOverlay, SimIssue } from '@/types/cam'

// ============================================================================
// Types
// ============================================================================

export interface ArtStudioReliefBackplotReturn {
  backplotMoves: ComputedRef<BackplotMove[]>
  backplotOverlays: ComputedRef<BackplotOverlay[]>
  simIssues: ComputedRef<SimIssue[]>
}

// ============================================================================
// Composable
// ============================================================================

export function useArtStudioReliefBackplot(
  results: Ref<Record<string, any> | null>,
  selectedPathOpId: Ref<string | null>,
  selectedOverlayOpId: Ref<string | null>
): ArtStudioReliefBackplotReturn {
  /**
   * Extract moves from the selected path operation.
   */
  const backplotMoves = computed<BackplotMove[]>(() => {
    if (!results.value || !selectedPathOpId.value) return []
    const src = results.value[selectedPathOpId.value]
    if (!src || !Array.isArray(src.moves)) return []
    return src.moves as BackplotMove[]
  })

  /**
   * Build overlay list from both path and sim operations.
   */
  const backplotOverlays = computed<BackplotOverlay[]>(() => {
    const overlays: BackplotOverlay[] = []
    if (!results.value) return overlays

    // Path overlays
    if (selectedPathOpId.value) {
      const src = results.value[selectedPathOpId.value]
      if (src && Array.isArray(src.overlays)) {
        overlays.push(
          ...src.overlays.map((o: any) => ({
            type: o.type || 'overlay',
            x: Number(o.x ?? 0),
            y: Number(o.y ?? 0),
            radius: typeof o.radius === 'number' ? o.radius : 1.5,
            severity: o.severity,
            feed_pct: o.feed_pct
          }))
        )
      }
    }

    // Sim issue overlays
    if (selectedOverlayOpId.value) {
      const simSrc = results.value[selectedOverlayOpId.value]
      const issues = (simSrc?.issues || []) as SimIssue[]
      overlays.push(
        ...issues.map((iss) => ({
          type: iss.type || 'sim_issue',
          x: iss.x,
          y: iss.y,
          radius: 2.5,
          severity: iss.severity
        }))
      )
    }

    return overlays
  })

  /**
   * Extract simulation issues.
   */
  const simIssues = computed<SimIssue[]>(() => {
    if (!results.value || !selectedOverlayOpId.value) return []
    const simSrc = results.value[selectedOverlayOpId.value]
    return (simSrc?.issues || []) as SimIssue[]
  })

  return {
    backplotMoves,
    backplotOverlays,
    simIssues
  }
}
