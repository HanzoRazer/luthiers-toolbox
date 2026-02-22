/**
 * Composable for SawLabDashboard filtering.
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import type { DashboardSummary, RunSummaryItem, RiskBucketId } from '@/api/sawLab'

// ============================================================================
// Types
// ============================================================================

export interface RiskCounts {
  unknown: number
  green: number
  yellow: number
  orange: number
  red: number
}

export interface SawDashboardFiltersState {
  riskFilter: Ref<RiskBucketId | 'all'>
  statusFilter: Ref<string>
  filteredRuns: ComputedRef<RunSummaryItem[]>
  riskCounts: ComputedRef<RiskCounts>
  clearFilters: () => void
}

// ============================================================================
// Composable
// ============================================================================

export function useSawDashboardFilters(
  dashboard: Ref<DashboardSummary | null>
): SawDashboardFiltersState {
  const riskFilter = ref<RiskBucketId | 'all'>('all')
  const statusFilter = ref('all')

  const filteredRuns = computed(() => {
    if (!dashboard.value) return []

    let runs = dashboard.value.runs

    // Filter by risk
    if (riskFilter.value !== 'all') {
      runs = runs.filter(r => r.risk_bucket.id === riskFilter.value)
    }

    // Filter by status
    if (statusFilter.value !== 'all') {
      runs = runs.filter(r => r.status === statusFilter.value)
    }

    return runs
  })

  const riskCounts = computed<RiskCounts>(() => {
    const counts: RiskCounts = {
      unknown: 0,
      green: 0,
      yellow: 0,
      orange: 0,
      red: 0
    }

    dashboard.value?.runs.forEach(run => {
      const bucket = run.risk_bucket.id as RiskBucketId
      if (bucket in counts) {
        counts[bucket]++
      }
    })

    return counts
  })

  function clearFilters(): void {
    riskFilter.value = 'all'
    statusFilter.value = 'all'
  }

  return {
    riskFilter,
    statusFilter,
    filteredRuns,
    riskCounts,
    clearFilters
  }
}
