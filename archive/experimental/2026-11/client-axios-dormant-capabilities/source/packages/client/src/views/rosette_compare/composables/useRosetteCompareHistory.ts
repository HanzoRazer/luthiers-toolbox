/**
 * RosetteCompare history sidebar composable.
 */
import { computed, type Ref, type ComputedRef } from 'vue'
import axios from 'axios'
import type { CompareSnapshot, GroupedSnapshots } from './rosetteCompareTypes'

// ============================================================================
// Types
// ============================================================================

export interface RosetteCompareHistoryReturn {
  // Computed
  groupedSnapshots: ComputedRef<Record<string, GroupedSnapshots>>
  averageRisk: ComputedRef<number>
  lowRiskCount: ComputedRef<number>
  mediumRiskCount: ComputedRef<number>
  highRiskCount: ComputedRef<number>

  // Actions
  toggleHistorySidebar: () => void
  toggleGroup: (groupKey: string) => void
  loadHistory: () => Promise<void>
  exportHistoryCSV: () => Promise<void>
}

// ============================================================================
// Composable
// ============================================================================

export function useRosetteCompareHistory(
  selectedJobIdA: Ref<string>,
  selectedJobIdB: Ref<string>,
  showHistory: Ref<boolean>,
  historySnapshots: Ref<CompareSnapshot[]>,
  historyLoading: Ref<boolean>,
  expandedGroups: Ref<Set<string>>,
  setStatus: (msg: string, isError?: boolean) => void
): RosetteCompareHistoryReturn {
  /**
   * Group snapshots by preset pair.
   */
  const groupedSnapshots = computed(() => {
    if (!historySnapshots.value.length) return {}

    const groups: Record<string, GroupedSnapshots> = {}

    historySnapshots.value.forEach(snapshot => {
      const presetA = snapshot.diff_summary.preset_a || 'Unknown'
      const presetB = snapshot.diff_summary.preset_b || 'Unknown'
      const groupKey = `${presetA} vs ${presetB}`

      if (!groups[groupKey]) {
        groups[groupKey] = {
          presetLabel: groupKey,
          snapshots: [],
          avgRisk: 0
        }
      }

      groups[groupKey].snapshots.push(snapshot)
    })

    // Calculate average risk for each group
    Object.values(groups).forEach(group => {
      const totalRisk = group.snapshots.reduce((sum, s) => sum + s.risk_score, 0)
      group.avgRisk = group.snapshots.length > 0 ? totalRisk / group.snapshots.length : 0
    })

    return groups
  })

  /**
   * Average risk across all snapshots.
   */
  const averageRisk = computed(() => {
    if (!historySnapshots.value.length) return 0
    const total = historySnapshots.value.reduce((sum, s) => sum + s.risk_score, 0)
    return total / historySnapshots.value.length
  })

  /**
   * Count of low risk snapshots (< 40).
   */
  const lowRiskCount = computed(() => {
    return historySnapshots.value.filter(s => s.risk_score < 40).length
  })

  /**
   * Count of medium risk snapshots (40-70).
   */
  const mediumRiskCount = computed(() => {
    return historySnapshots.value.filter(s => s.risk_score >= 40 && s.risk_score < 70).length
  })

  /**
   * Count of high risk snapshots (>= 70).
   */
  const highRiskCount = computed(() => {
    return historySnapshots.value.filter(s => s.risk_score >= 70).length
  })

  /**
   * Toggle history sidebar visibility.
   */
  function toggleHistorySidebar(): void {
    showHistory.value = !showHistory.value
    if (showHistory.value && selectedJobIdA.value && selectedJobIdB.value) {
      loadHistory()
    }
  }

  /**
   * Toggle preset group expansion.
   */
  function toggleGroup(groupKey: string): void {
    if (expandedGroups.value.has(groupKey)) {
      expandedGroups.value.delete(groupKey)
    } else {
      expandedGroups.value.add(groupKey)
    }
    // Force reactivity update
    expandedGroups.value = new Set(expandedGroups.value)
  }

  /**
   * Load comparison history from backend.
   */
  async function loadHistory(): Promise<void> {
    if (!selectedJobIdA.value || !selectedJobIdB.value) return

    historyLoading.value = true
    try {
      const res = await axios.get<CompareSnapshot[]>('/api/art/rosette/compare/snapshots', {
        params: {
          job_id_a: selectedJobIdA.value,
          job_id_b: selectedJobIdB.value,
          limit: 50
        }
      })
      historySnapshots.value = res.data || []
    } catch (err) {
      console.error('Failed to load history:', err)
      historySnapshots.value = []
    } finally {
      historyLoading.value = false
    }
  }

  /**
   * Export history as CSV.
   */
  async function exportHistoryCSV(): Promise<void> {
    if (!selectedJobIdA.value || !selectedJobIdB.value) return

    try {
      const params = new URLSearchParams({
        job_id_a: selectedJobIdA.value,
        job_id_b: selectedJobIdB.value,
        limit: '100'
      })

      // Open CSV in new tab (browser will download it)
      window.open(`/api/art/rosette/compare/export_csv?${params.toString()}`, '_blank')
    } catch (err) {
      console.error('Failed to export CSV:', err)
      setStatus('Failed to export CSV.', true)
    }
  }

  return {
    // Computed
    groupedSnapshots,
    averageRisk,
    lowRiskCount,
    mediumRiskCount,
    highRiskCount,

    // Actions
    toggleHistorySidebar,
    toggleGroup,
    loadHistory,
    exportHistoryCSV
  }
}
