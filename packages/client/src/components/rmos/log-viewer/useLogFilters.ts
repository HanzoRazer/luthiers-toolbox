/**
 * Composable for RMOS log viewer filters.
 */
import { ref, computed, watch, type Ref, type ComputedRef } from 'vue'
import { getSoftCap, setSoftCap, resetSoftCap } from '@/api/rmosLogsClient'

// ============================================================================
// Types
// ============================================================================

export interface LogFilters {
  mode: string
  status: string
  risk_level: string
  tool_id: string
  source: string
}

export interface FilterParams {
  mode?: string
  status?: string
  risk_level?: string
  tool_id?: string
  source?: string
}

export interface LogFiltersState {
  filters: Ref<LogFilters>
  softCapValue: Ref<number>
  filterParams: ComputedRef<FilterParams>
  loadSoftCapForFilter: () => void
  resetCapForFilter: () => void
}

// ============================================================================
// Composable
// ============================================================================

export function useLogFilters(): LogFiltersState {
  const filters = ref<LogFilters>({
    mode: '',
    status: '',
    risk_level: '',
    tool_id: '',
    source: ''
  })

  const softCapValue = ref(25)

  const filterParams = computed<FilterParams>(() => ({
    mode: filters.value.mode || undefined,
    status: filters.value.status || undefined,
    risk_level: filters.value.risk_level || undefined,
    tool_id: filters.value.tool_id || undefined,
    source: filters.value.source || undefined
  }))

  function loadSoftCapForFilter(): void {
    softCapValue.value = getSoftCap(filters.value.mode, filters.value.source)
  }

  function resetCapForFilter(): void {
    resetSoftCap(filters.value.mode, filters.value.source)
    loadSoftCapForFilter()
  }

  // Save soft cap when changed
  watch(softCapValue, (val) => {
    setSoftCap(val, filters.value.mode, filters.value.source)
  })

  // Reload soft cap when mode/source filters change
  watch(
    () => [filters.value.mode, filters.value.source],
    () => {
      loadSoftCapForFilter()
    }
  )

  return {
    filters,
    softCapValue,
    filterParams,
    loadSoftCapForFilter,
    resetCapForFilter
  }
}
