/**
 * RosetteCompare API actions composable.
 */
import type { Ref } from 'vue'
import axios from 'axios'
import type {
  RosetteJob,
  RosetteCompareResult,
  RosetteDiffSummary
} from './rosetteCompareTypes'

// ============================================================================
// Types
// ============================================================================

export interface RosetteCompareActionsReturn {
  reloadJobs: () => Promise<void>
  runCompare: () => Promise<void>
  saveSnapshot: () => Promise<void>
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Calculate risk score from diff summary.
 * Formula: base_score = abs(segments_delta) / max(seg_a, seg_b) * 50
 *          radius_contribution = abs(inner_delta + outer_delta) / 10 * 50
 *          risk_score = clamp(base_score + radius_contribution, 0, 100)
 */
function calculateRiskScore(diff: RosetteDiffSummary): number {
  const segA = diff.segments_a || 0
  const segB = diff.segments_b || 0
  const maxSeg = Math.max(segA, segB)
  const segDelta = Math.abs(diff.segments_delta || 0)

  const innerDelta = Math.abs(diff.inner_radius_delta || 0)
  const outerDelta = Math.abs(diff.outer_radius_delta || 0)

  const baseScore = maxSeg > 0 ? (segDelta / maxSeg) * 50 : 0
  const radiusScore = ((innerDelta + outerDelta) / 10) * 50

  const totalScore = baseScore + radiusScore
  return Math.min(Math.max(totalScore, 0), 100)
}

// ============================================================================
// Composable
// ============================================================================

export function useRosetteCompareActions(
  jobs: Ref<RosetteJob[]>,
  jobsLoading: Ref<boolean>,
  jobsError: Ref<string | null>,
  selectedJobIdA: Ref<string>,
  selectedJobIdB: Ref<string>,
  compareResult: Ref<RosetteCompareResult | null>,
  compareLoading: Ref<boolean>,
  saveSnapshotLoading: Ref<boolean>,
  setStatus: (msg: string, isError?: boolean) => void
): RosetteCompareActionsReturn {
  /**
   * Reload jobs list from API.
   */
  async function reloadJobs(): Promise<void> {
    jobsLoading.value = true
    jobsError.value = null
    try {
      const res = await axios.get<RosetteJob[]>('/api/art/rosette/jobs', {
        params: { limit: 50 }
      })
      jobs.value = res.data || []
    } catch (err) {
      console.error('Failed to load rosette jobs', err)
      jobsError.value = 'Failed to load rosette jobs.'
    } finally {
      jobsLoading.value = false
    }
  }

  /**
   * Run comparison between selected jobs.
   */
  async function runCompare(): Promise<void> {
    if (!selectedJobIdA.value || !selectedJobIdB.value) {
      setStatus('Please select both A and B jobs.', true)
      return
    }
    setStatus('')
    compareLoading.value = true
    compareResult.value = null
    try {
      const payload = {
        job_id_a: selectedJobIdA.value,
        job_id_b: selectedJobIdB.value
      }
      const res = await axios.post<RosetteCompareResult>('/api/art/rosette/compare', payload)
      compareResult.value = res.data
      setStatus('Compare complete.', false)
    } catch (err: any) {
      console.error('Compare failed', err)
      const msg = err?.response?.data?.detail || 'Failed to compare rosette jobs.'
      setStatus(msg, true)
    } finally {
      compareLoading.value = false
    }
  }

  /**
   * Save comparison snapshot to risk timeline.
   */
  async function saveSnapshot(): Promise<void> {
    if (!compareResult.value) {
      setStatus('No comparison result to save.', true)
      return
    }

    saveSnapshotLoading.value = true
    setStatus('')

    const riskScore = calculateRiskScore(compareResult.value.diff_summary)

    try {
      const payload = {
        job_id_a: compareResult.value.diff_summary.job_id_a,
        job_id_b: compareResult.value.diff_summary.job_id_b,
        risk_score: riskScore,
        diff_summary: compareResult.value.diff_summary,
        lane: 'production',
        note: null
      }

      const res = await axios.post('/api/art/rosette/compare/snapshot', payload)
      console.log('Snapshot saved:', res.data)
      setStatus(`✓ Saved to Risk Timeline (risk: ${riskScore.toFixed(1)}%)`, false)
    } catch (err: any) {
      console.error('Failed to save snapshot:', err)
      const msg = err?.response?.data?.detail || 'Failed to save comparison snapshot.'
      setStatus(msg, true)
    } finally {
      saveSnapshotLoading.value = false
    }
  }

  return {
    reloadJobs,
    runCompare,
    saveSnapshot
  }
}
