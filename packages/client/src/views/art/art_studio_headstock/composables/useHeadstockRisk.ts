/**
 * ArtStudioHeadstock risk analytics composable.
 */
import type { Ref } from 'vue'
import type { SimIssue } from '@/types/cam'
import type { PipelineRunIn, PipelineRunOut } from '@/api/pipeline'
import {
  postRiskReport,
  buildRiskReportPayload,
  attachRiskBackplot,
  type RiskAnalytics,
  type RiskBackplotMoveOut
} from '@/api/camRisk'
import type { SeverityOption, HeadstockBackplotSnapshot } from './headstockTypes'

export interface HeadstockRiskReturn {
  computeRiskAnalytics: (issues: (SimIssue & { extra_time_s?: number })[]) => RiskAnalytics
  handleRunSuccess: (payload: PipelineRunIn, out: PipelineRunOut) => Promise<void>
}

export function useHeadstockRisk(
  headstockDxfPath: Ref<string>,
  results: Ref<Record<string, any> | null>,
  selectedPathOpId: Ref<string | null>,
  selectedOverlayOpId: Ref<string | null>,
  focusPoint: Ref<{ x: number; y: number } | null>,
  selectedIssueIndex: Ref<number | null>,
  lastRiskAnalytics: Ref<RiskAnalytics | null>,
  lastRiskReportError: Ref<string | null>,
  lastRiskReportId: Ref<string | null>,
  noteEditorVisible: Ref<boolean>,
  noteDraft: Ref<string>,
  noteSaveError: Ref<string | null>
): HeadstockRiskReturn {
  /**
   * Format duration in seconds to human-readable string.
   */
  function formatDuration(sec: number): string {
    if (!sec || sec <= 0) return '0 s'
    const whole = Math.round(sec)
    const minutes = Math.floor(whole / 60)
    const seconds = whole % 60
    if (minutes === 0) return `${seconds} s`
    return `${minutes} min ${seconds} s`
  }

  /**
   * Compute risk analytics from simulation issues.
   */
  function computeRiskAnalytics(issues: (SimIssue & { extra_time_s?: number })[]): RiskAnalytics {
    const counts: Record<SeverityOption, number> = {
      info: 0,
      low: 0,
      medium: 0,
      high: 0,
      critical: 0
    }

    let totalExtra = 0

    for (const iss of issues) {
      const sev = (iss.severity || 'medium') as SeverityOption
      if (sev in counts) counts[sev] += 1
      const extra = typeof (iss as any).extra_time_s === 'number' ? (iss as any).extra_time_s : 0
      totalExtra += extra
    }

    const riskScore =
      counts.critical * 5 + counts.high * 3 + counts.medium * 2 + counts.low * 1 + counts.info * 0.5

    const totalIssues = issues.length

    return {
      total_issues: totalIssues,
      severity_counts: {
        info: counts.info,
        low: counts.low,
        medium: counts.medium,
        high: counts.high,
        critical: counts.critical
      },
      risk_score: riskScore,
      total_extra_time_s: totalExtra,
      total_extra_time_human: formatDuration(totalExtra)
    }
  }

  /**
   * Build backplot snapshot payload for this headstock job.
   */
  function buildHeadstockBackplotSnapshot(): HeadstockBackplotSnapshot | null {
    if (!results.value || !selectedPathOpId.value) return null
    const src = results.value[selectedPathOpId.value]
    if (!src || !Array.isArray(src.moves)) return null

    const moves: RiskBackplotMoveOut[] = (src.moves as any[]).map((mv) => ({
      code: mv.code ?? mv.g ?? null,
      x: typeof mv.x === 'number' ? mv.x : null,
      y: typeof mv.y === 'number' ? mv.y : null,
      z: typeof mv.z === 'number' ? mv.z : null,
      f: typeof mv.f === 'number' ? mv.f : null
    }))

    const overlays = Array.isArray(src.overlays) ? (src.overlays as any[]) : []

    return {
      moves,
      overlays,
      meta: {
        source: 'ArtStudioHeadstock',
        path_op_id: selectedPathOpId.value,
        overlay_op_id: selectedOverlayOpId.value
      }
    }
  }

  /**
   * Handle successful pipeline run.
   */
  async function handleRunSuccess(payload: PipelineRunIn, out: PipelineRunOut): Promise<void> {
    results.value = out.results
    focusPoint.value = null
    selectedIssueIndex.value = null
    lastRiskReportError.value = null
    lastRiskReportId.value = null
    noteEditorVisible.value = false
    noteDraft.value = ''
    noteSaveError.value = null

    try {
      const simResult = out.results?.['headstock_sim']
      const issues = (simResult?.issues || []) as (SimIssue & { extra_time_s?: number })[]

      const analytics = computeRiskAnalytics(issues)
      lastRiskAnalytics.value = analytics

      const jobId = `headstock_${Date.now()}`

      const riskPayload = buildRiskReportPayload({
        jobId,
        pipelineId: 'artstudio_headstock_v16',
        opId: 'headstock_sim',
        machineProfileId: payload.context?.machine_profile_id || 'GUITAR_CNC_01',
        postPreset: payload.context?.post_preset || 'GRBL',
        designSource: payload.design?.source || 'dxf',
        designPath: payload.design?.dxf_path || headstockDxfPath.value,
        issues,
        analytics,
        meta: {
          source: 'ArtStudioHeadstockView'
        }
      })

      const stored = await postRiskReport(riskPayload)
      lastRiskReportId.value = stored.id

      // Attach backplot snapshot (non-fatal)
      try {
        const snapshot = buildHeadstockBackplotSnapshot()
        if (snapshot) {
          await attachRiskBackplot(stored.id, snapshot)
        }
      } catch (err: any) {
        console.warn('Failed to attach headstock backplot snapshot:', err?.message || err)
      }
    } catch (err: any) {
      console.error('Failed to submit headstock risk report:', err)
      lastRiskReportError.value = err?.message || 'Failed to submit headstock risk report'
    }
  }

  return {
    computeRiskAnalytics,
    handleRunSuccess
  }
}
