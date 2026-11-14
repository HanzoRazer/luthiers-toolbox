/**
 * Composable for SawLabDashboard modal management.
 */
import { ref, type Ref } from 'vue'
import type { RunSummaryItem } from '@/api/sawLab'

// ============================================================================
// Types
// ============================================================================

export interface SawDashboardModalsState {
  selectedRun: Ref<RunSummaryItem | null>
  riskActionsRun: Ref<RunSummaryItem | null>
  openRunDetail: (run: RunSummaryItem) => void
  closeRunDetail: () => void
  openRiskActions: (run: RunSummaryItem) => void
  closeRiskActions: () => void
}

// ============================================================================
// Composable
// ============================================================================

export function useSawDashboardModals(): SawDashboardModalsState {
  const selectedRun = ref<RunSummaryItem | null>(null)
  const riskActionsRun = ref<RunSummaryItem | null>(null)

  function openRunDetail(run: RunSummaryItem): void {
    selectedRun.value = run
    riskActionsRun.value = null // Close risk actions if open
  }

  function closeRunDetail(): void {
    selectedRun.value = null
  }

  function openRiskActions(run: RunSummaryItem): void {
    riskActionsRun.value = run
    selectedRun.value = null // Close run detail if open
  }

  function closeRiskActions(): void {
    riskActionsRun.value = null
  }

  return {
    selectedRun,
    riskActionsRun,
    openRunDetail,
    closeRunDetail,
    openRiskActions,
    closeRiskActions
  }
}
