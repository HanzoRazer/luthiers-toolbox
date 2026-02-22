/**
 * Composable for SawLabDashboard state and data loading.
 */
import { ref, type Ref } from 'vue'
import { getDashboardRuns, type DashboardSummary } from '@/api/sawLab'

// ============================================================================
// Types
// ============================================================================

export interface SawDashboardState {
  dashboard: Ref<DashboardSummary | null>
  loading: Ref<boolean>
  error: Ref<string | null>
  lastUpdated: Ref<Date | null>
  limit: Ref<number>
  loadDashboard: () => Promise<void>
}

// ============================================================================
// Composable
// ============================================================================

export function useSawDashboard(): SawDashboardState {
  const dashboard = ref<DashboardSummary | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const lastUpdated = ref<Date | null>(null)
  const limit = ref(50)

  async function loadDashboard(): Promise<void> {
    loading.value = true
    error.value = null

    try {
      dashboard.value = await getDashboardRuns(limit.value)
      lastUpdated.value = new Date()
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } }; message?: string }
      error.value = axiosErr.response?.data?.detail || axiosErr.message || 'Failed to load dashboard'
      console.error('Dashboard load error:', err)
    } finally {
      loading.value = false
    }
  }

  return {
    dashboard,
    loading,
    error,
    lastUpdated,
    limit,
    loadDashboard
  }
}
