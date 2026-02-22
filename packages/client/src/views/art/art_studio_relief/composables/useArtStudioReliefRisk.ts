/**
 * ArtStudioRelief risk analytics composable.
 */
import type { SimIssue } from '@/types/cam'
import type { RiskAnalytics, RiskBackplotMoveOut } from '@/api/camRisk'
import { SEVERITY_OPTIONS, type SeverityOption } from './artStudioReliefTypes'
import type { Ref } from 'vue'

// ============================================================================
// Types
// ============================================================================

export interface BackplotSnapshot {
  moves: RiskBackplotMoveOut[]
  overlays: Record<string, unknown>[]
  meta: Record<string, unknown>
}

export interface ArtStudioReliefRiskReturn {
  computeRiskAnalytics: (issues: (SimIssue & { extra_time_s?: number })[]) => RiskAnalytics
  buildReliefBackplotSnapshot: () => BackplotSnapshot | null
}

// ============================================================================
// Helpers
// ============================================================================

function formatDuration(sec: number): string {
  if (!sec || sec <= 0) return '0 s'
  const whole = Math.round(sec)
  const minutes = Math.floor(whole / 60)
  const seconds = whole % 60
  if (minutes === 0) return `${seconds} s`
  return `${minutes} min ${seconds} s`
}

// ============================================================================
// Composable
// ============================================================================

export function useArtStudioReliefRisk(
  results: Ref<Record<string, any> | null>,
  selectedPathOpId: Ref<string | null>,
  selectedOverlayOpId: Ref<string | null>
): ArtStudioReliefRiskReturn {
  /**
   * Compute risk analytics from simulation issues.
   */
  function computeRiskAnalytics(
    issues: (SimIssue & { extra_time_s?: number })[]
  ): RiskAnalytics {
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
      const extra =
        typeof (iss as any).extra_time_s === 'number' ? (iss as any).extra_time_s : 0
      totalExtra += extra
    }

    const riskScore =
      counts.critical * 5 +
      counts.high * 3 +
      counts.medium * 2 +
      counts.low * 1 +
      counts.info * 0.5

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
   * Build backplot snapshot payload for relief job.
   */
  function buildReliefBackplotSnapshot(): BackplotSnapshot | null {
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
        source: 'ArtStudioRelief',
        path_op_id: selectedPathOpId.value,
        overlay_op_id: selectedOverlayOpId.value
      }
    }
  }

  return {
    computeRiskAnalytics,
    buildReliefBackplotSnapshot
  }
}
