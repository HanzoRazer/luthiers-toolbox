/**
 * ArtStudioRelief pipeline handlers composable.
 */
import type { Ref } from 'vue'
import type { PipelineRunIn, PipelineRunOut } from '@/api/pipeline'
import type { SimIssue, BackplotFocusPoint } from '@/types/cam'
import type { RiskAnalytics } from '@/api/camRisk'
import {
  postRiskReport,
  buildRiskReportPayload,
  patchRiskNotes,
  attachRiskBackplot
} from '@/api/camRisk'
import type { BackplotSnapshot } from './useArtStudioReliefRisk'

// ============================================================================
// Types
// ============================================================================

export interface ArtStudioReliefPipelineReturn {
  handleRun: (payload: PipelineRunIn) => void
  handleRunSuccess: (payload: PipelineRunIn, out: PipelineRunOut) => Promise<void>
  handleRunError: (payload: PipelineRunIn, err: string) => void
  openNoteEditor: () => void
  cancelNoteEditor: () => void
  saveNote: () => Promise<void>
  handleIssueFocusRequest: (payload: { index: number; issue: SimIssue }) => void
}

// ============================================================================
// Composable
// ============================================================================

export function useArtStudioReliefPipeline(
  reliefHeightmapPath: Ref<string>,
  results: Ref<Record<string, any> | null>,
  focusPoint: Ref<BackplotFocusPoint | null>,
  selectedIssueIndex: Ref<number | null>,
  lastRiskAnalytics: Ref<RiskAnalytics | null>,
  lastRiskReportError: Ref<string | null>,
  lastRiskReportId: Ref<string | null>,
  noteEditorVisible: Ref<boolean>,
  noteDraft: Ref<string>,
  noteSaving: Ref<boolean>,
  noteSaveError: Ref<string | null>,
  computeRiskAnalytics: (issues: (SimIssue & { extra_time_s?: number })[]) => RiskAnalytics,
  buildReliefBackplotSnapshot: () => BackplotSnapshot | null
): ArtStudioReliefPipelineReturn {
  /**
   * Handle pipeline run start (optional hook).
   */
  function handleRun(_payload: PipelineRunIn): void {
    // Optional: can add pre-run logic here
  }

  /**
   * Handle successful pipeline run.
   */
  async function handleRunSuccess(
    payload: PipelineRunIn,
    out: PipelineRunOut
  ): Promise<void> {
    results.value = out.results
    focusPoint.value = null
    selectedIssueIndex.value = null
    lastRiskReportError.value = null
    lastRiskReportId.value = null
    noteEditorVisible.value = false
    noteDraft.value = ''
    noteSaveError.value = null

    try {
      const simResult = out.results?.['relief_sim']
      const issues = (simResult?.issues || []) as (SimIssue & {
        extra_time_s?: number
      })[]

      const analytics = computeRiskAnalytics(issues)
      lastRiskAnalytics.value = analytics

      const jobId = `relief_${Date.now()}`

      const riskPayload = buildRiskReportPayload({
        jobId,
        pipelineId: 'artstudio_relief_v16',
        opId: 'relief_sim',
        machineProfileId: payload.context?.machine_profile_id || 'GUITAR_CNC_01',
        postPreset: payload.context?.post_preset || 'GRBL',
        designSource: payload.design?.source || 'heightmap',
        designPath:
          (payload.design as any)?.heightmap_path || reliefHeightmapPath.value,
        issues,
        analytics,
        meta: {
          source: 'ArtStudioReliefView'
        }
      })

      const stored = await postRiskReport(riskPayload)
      lastRiskReportId.value = stored.id

      // Attach backplot snapshot (non-fatal)
      try {
        const snapshot = buildReliefBackplotSnapshot()
        if (snapshot) {
          await attachRiskBackplot(stored.id, snapshot)
        }
      } catch (err: any) {
        console.warn(
          'Failed to attach relief backplot snapshot:',
          err?.message || err
        )
      }
    } catch (err: any) {
      console.error('Failed to submit relief risk report:', err)
      lastRiskReportError.value =
        err?.message || 'Failed to submit relief risk report'
    }
  }

  /**
   * Handle pipeline run error (optional hook).
   */
  function handleRunError(_payload: PipelineRunIn, _err: string): void {
    // Optional: can add error handling logic here
  }

  /**
   * Open note editor.
   */
  function openNoteEditor(): void {
    if (!lastRiskReportId.value) return
    noteEditorVisible.value = true
    noteSaveError.value = null
  }

  /**
   * Cancel note editor.
   */
  function cancelNoteEditor(): void {
    noteEditorVisible.value = false
    noteSaveError.value = null
  }

  /**
   * Save note to risk report.
   */
  async function saveNote(): Promise<void> {
    if (!lastRiskReportId.value) return
    noteSaving.value = true
    noteSaveError.value = null
    try {
      await patchRiskNotes(lastRiskReportId.value, noteDraft.value || '')
      noteEditorVisible.value = false
    } catch (err: any) {
      console.error('Failed to save relief note:', err)
      noteSaveError.value = err?.message || 'Failed to save note'
    } finally {
      noteSaving.value = false
    }
  }

  /**
   * Handle issue focus request from issues list.
   */
  function handleIssueFocusRequest(payload: {
    index: number
    issue: SimIssue
  }): void {
    selectedIssueIndex.value = payload.index
    focusPoint.value = {
      x: payload.issue.x,
      y: payload.issue.y
    }
  }

  return {
    handleRun,
    handleRunSuccess,
    handleRunError,
    openNoteEditor,
    cancelNoteEditor,
    saveNote,
    handleIssueFocusRequest
  }
}
