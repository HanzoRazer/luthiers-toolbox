/**
 * ArtStudioHeadstock state composable.
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import type { BackplotLoop, BackplotMove, BackplotOverlay, BackplotFocusPoint, SimIssue } from '@/types/cam'
import type { RiskAnalytics } from '@/api/camRisk'
import { DEFAULT_DXF_PATH } from './headstockTypes'

export interface HeadstockStateReturn {
  // Design source
  headstockDxfPath: Ref<string>

  // Pipeline + backplot state
  results: Ref<Record<string, any> | null>
  selectedPathOpId: Ref<string | null>
  selectedOverlayOpId: Ref<string | null>
  showToolpath: Ref<boolean>
  focusPoint: Ref<BackplotFocusPoint | null>
  selectedIssueIndex: Ref<number | null>
  backplotLoops: Ref<BackplotLoop[]>

  // Risk state
  lastRiskAnalytics: Ref<RiskAnalytics | null>
  lastRiskReportError: Ref<string | null>
  lastRiskReportId: Ref<string | null>

  // Notes state
  noteEditorVisible: Ref<boolean>
  noteDraft: Ref<string>
  noteSaving: Ref<boolean>
  noteSaveError: Ref<string | null>

  // Computed
  backplotMoves: ComputedRef<BackplotMove[]>
  backplotOverlays: ComputedRef<BackplotOverlay[]>
  simIssues: ComputedRef<SimIssue[]>
}

export function useHeadstockState(): HeadstockStateReturn {
  // Design source
  const headstockDxfPath = ref(DEFAULT_DXF_PATH)

  // Pipeline + backplot state
  const results = ref<Record<string, any> | null>(null)
  const selectedPathOpId = ref<string | null>('headstock_adaptive')
  const selectedOverlayOpId = ref<string | null>('headstock_sim')
  const showToolpath = ref(true)
  const focusPoint = ref<BackplotFocusPoint | null>(null)
  const selectedIssueIndex = ref<number | null>(null)
  const backplotLoops = ref<BackplotLoop[]>([])

  // Risk state
  const lastRiskAnalytics = ref<RiskAnalytics | null>(null)
  const lastRiskReportError = ref<string | null>(null)
  const lastRiskReportId = ref<string | null>(null)

  // Notes state
  const noteEditorVisible = ref(false)
  const noteDraft = ref('')
  const noteSaving = ref(false)
  const noteSaveError = ref<string | null>(null)

  // Computed: backplot moves
  const backplotMoves = computed<BackplotMove[]>(() => {
    if (!results.value || !selectedPathOpId.value) return []
    const src = results.value[selectedPathOpId.value]
    if (!src || !Array.isArray(src.moves)) return []
    return src.moves as BackplotMove[]
  })

  // Computed: backplot overlays
  const backplotOverlays = computed<BackplotOverlay[]>(() => {
    const overlays: BackplotOverlay[] = []
    if (!results.value) return overlays

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

  // Computed: sim issues
  const simIssues = computed<SimIssue[]>(() => {
    if (!results.value || !selectedOverlayOpId.value) return []
    const simSrc = results.value[selectedOverlayOpId.value]
    return (simSrc?.issues || []) as SimIssue[]
  })

  return {
    headstockDxfPath,
    results,
    selectedPathOpId,
    selectedOverlayOpId,
    showToolpath,
    focusPoint,
    selectedIssueIndex,
    backplotLoops,
    lastRiskAnalytics,
    lastRiskReportError,
    lastRiskReportId,
    noteEditorVisible,
    noteDraft,
    noteSaving,
    noteSaveError,
    backplotMoves,
    backplotOverlays,
    simIssues
  }
}
