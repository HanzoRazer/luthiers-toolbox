/**
 * Composable for RiskDashboard navigation actions.
 */
import { useRouter } from 'vue-router'
import type { Bucket } from '@/components/dashboard'
import type { Ref } from 'vue'

// ============================================================================
// Types
// ============================================================================

export interface RiskNavigationState {
  goToLab: (bucket: Bucket) => void
}

export interface UseRiskNavigationOptions {
  jobFilter: Ref<string>
}

// ============================================================================
// Composable
// ============================================================================

export function useRiskNavigation(
  options: UseRiskNavigationOptions
): RiskNavigationState {
  const { jobFilter } = options
  const router = useRouter()

  function goToLab(bucket: Bucket): void {
    const lane = bucket.lane.toLowerCase()
    const preset = bucket.preset
    const jobHint = jobFilter.value || ''

    const query: Record<string, string> = {}
    if (preset && preset !== '(none)') query.preset = preset
    if (lane) query.lane = lane
    if (jobHint) query.job_hint = jobHint

    if (lane.startsWith('rosette')) {
      router.push({
        path: '/art-studio',
        query: {
          tab: 'compare',
          ...query
        }
      })
    } else if (lane.startsWith('adaptive')) {
      router.push({
        path: '/lab/adaptive',
        query
      })
    } else if (lane.startsWith('relief')) {
      router.push({
        path: '/lab/relief',
        query
      })
    } else if (lane.startsWith('pipeline')) {
      router.push({
        path: '/lab/pipeline',
        query
      })
    } else {
      router.push({
        path: '/lab/risk-dashboard',
        query
      })
    }
  }

  return {
    goToLab
  }
}
