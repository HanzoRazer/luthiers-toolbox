/**
 * Composable for RiskDashboard filter state and URL synchronization.
 */
import { ref, computed, watch, type Ref, type ComputedRef } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { toIsoDate } from './riskFormatters'

// ============================================================================
// Types
// ============================================================================

export type QuickRangeMode = '' | 'all' | 'last7' | 'last30' | 'last90' | 'year'

export interface LanePresetDef {
  id: string
  label: string
  lane: string
  preset: string
  defaultQuickRange?: QuickRangeMode
  badge?: string
}

export interface QuickRangeDef {
  id: QuickRangeMode
  label: string
}

export interface RiskFiltersState {
  laneFilter: Ref<string>
  presetFilter: Ref<string>
  jobFilter: Ref<string>
  since: Ref<string>
  until: Ref<string>
  quickRangeMode: Ref<QuickRangeMode>
  hasAnyFilter: ComputedRef<boolean>
  currentQuickRangeLabel: ComputedRef<string>
  quickRangeModes: QuickRangeDef[]
  lanePresets: Ref<LanePresetDef[]>
  applyQuickRange: (mode: QuickRangeMode) => void
  applyLanePreset: (id: string) => void
  clearAllFilters: () => void
  getCurrentFilters: () => Record<string, string>
  handleApplyFilters: (filters: Record<string, string>) => void
  syncFiltersToQuery: () => void
  applyQueryToFilters: () => void
  filtersAreEmpty: () => boolean
}

// ============================================================================
// Composable
// ============================================================================

export function useRiskFilters(
  onFiltersChanged?: () => void
): RiskFiltersState {
  const router = useRouter()
  const route = useRoute()

  // Filter state
  const laneFilter = ref('')
  const presetFilter = ref('')
  const jobFilter = ref('')
  const since = ref('')
  const until = ref('')
  const quickRangeMode = ref<QuickRangeMode>('')

  // Quick range definitions
  const quickRangeModes: QuickRangeDef[] = [
    { id: 'all', label: 'All' },
    { id: 'last7', label: 'Last 7d' },
    { id: 'last30', label: 'Last 30d' },
    { id: 'last90', label: 'Last 90d' },
    { id: 'year', label: 'This year' }
  ]

  // Lane preset definitions
  const lanePresets = ref<LanePresetDef[]>([
    {
      id: 'rosette_safe_30',
      label: 'Rosette · Safe (30d)',
      lane: 'Rosette',
      preset: 'Safe',
      defaultQuickRange: 'last30',
      badge: 'Rosette'
    },
    {
      id: 'adaptive_aggressive_30',
      label: 'Adaptive · Aggressive (30d)',
      lane: 'Adaptive',
      preset: 'Aggressive',
      defaultQuickRange: 'last30',
      badge: 'Adaptive'
    },
    {
      id: 'relief_safe_90',
      label: 'Relief · Safe (90d)',
      lane: 'Relief',
      preset: 'Safe',
      defaultQuickRange: 'last90',
      badge: 'Relief'
    },
    {
      id: 'pipeline_any_30',
      label: 'Pipeline · Any (30d)',
      lane: 'Pipeline',
      preset: '',
      defaultQuickRange: 'last30',
      badge: 'Pipeline'
    }
  ])

  const hasAnyFilter = computed(() => {
    return (
      !!laneFilter.value ||
      !!presetFilter.value ||
      !!jobFilter.value ||
      !!since.value ||
      !!until.value
    )
  })

  const currentQuickRangeLabel = computed(() => {
    const entry = quickRangeModes.find((m) => m.id === quickRangeMode.value)
    return entry ? entry.label : 'Custom'
  })

  function computeDateRange(mode: QuickRangeMode): { start: string; end: string } {
    const today = new Date()
    let start = ''
    let end = ''

    if (mode === 'all') {
      start = ''
      end = ''
    } else if (mode === 'last7') {
      const d = new Date(today)
      d.setDate(d.getDate() - 7)
      start = toIsoDate(d)
      end = toIsoDate(today)
    } else if (mode === 'last30') {
      const d = new Date(today)
      d.setDate(d.getDate() - 30)
      start = toIsoDate(d)
      end = toIsoDate(today)
    } else if (mode === 'last90') {
      const d = new Date(today)
      d.setDate(d.getDate() - 90)
      start = toIsoDate(d)
      end = toIsoDate(today)
    } else if (mode === 'year') {
      const yearStart = new Date(today.getFullYear(), 0, 1)
      start = toIsoDate(yearStart)
      end = toIsoDate(today)
    }

    return { start, end }
  }

  function applyQuickRange(mode: QuickRangeMode): void {
    const { start, end } = computeDateRange(mode)
    quickRangeMode.value = mode
    since.value = start
    until.value = end
    syncFiltersToQuery()
    onFiltersChanged?.()
  }

  function applyLanePreset(id: string): void {
    const preset = lanePresets.value.find((p) => p.id === id)
    if (!preset) return

    laneFilter.value = preset.lane || ''
    presetFilter.value = preset.preset || ''

    const mode = preset.defaultQuickRange || 'last30'
    const { start, end } = computeDateRange(mode)
    quickRangeMode.value = mode
    since.value = start
    until.value = end

    syncFiltersToQuery()
    onFiltersChanged?.()
  }

  function clearAllFilters(): void {
    laneFilter.value = ''
    presetFilter.value = ''
    jobFilter.value = ''
    since.value = ''
    until.value = ''
    quickRangeMode.value = 'all'
    syncFiltersToQuery()
    onFiltersChanged?.()
  }

  function getCurrentFilters(): Record<string, string> {
    return {
      lane: laneFilter.value,
      preset: presetFilter.value,
      jobHint: jobFilter.value,
      since: since.value,
      until: until.value
    }
  }

  function handleApplyFilters(filters: Record<string, string>): void {
    laneFilter.value = filters.lane || ''
    presetFilter.value = filters.preset || ''
    jobFilter.value = filters.jobHint || ''
    since.value = filters.since || ''
    until.value = filters.until || ''
    quickRangeMode.value = !since.value && !until.value ? 'all' : ''
    syncFiltersToQuery()
    onFiltersChanged?.()
  }

  function syncFiltersToQuery(): void {
    const q: Record<string, string> = {}

    if (laneFilter.value) q.lane = laneFilter.value
    if (presetFilter.value) q.preset = presetFilter.value
    if (jobFilter.value) q.job_hint = jobFilter.value
    if (since.value) q.since = since.value
    if (until.value) q.until = until.value

    router.replace({ query: q }).catch(() => {})
  }

  function applyQueryToFilters(): void {
    const q = route.query

    laneFilter.value = typeof q.lane === 'string' ? q.lane : ''
    presetFilter.value = typeof q.preset === 'string' ? q.preset : ''
    jobFilter.value = typeof q.job_hint === 'string' ? q.job_hint : ''
    since.value = typeof q.since === 'string' ? q.since : ''
    until.value = typeof q.until === 'string' ? q.until : ''

    quickRangeMode.value = ''
    if (!since.value && !until.value) {
      quickRangeMode.value = 'all'
    }
  }

  function filtersAreEmpty(): boolean {
    return (
      !laneFilter.value &&
      !presetFilter.value &&
      !jobFilter.value &&
      !since.value &&
      !until.value
    )
  }

  // Watch for manual filter changes
  watch(
    () => [laneFilter.value, presetFilter.value, jobFilter.value],
    () => {
      syncFiltersToQuery()
    }
  )

  watch(
    () => [since.value, until.value],
    () => {
      if (since.value || until.value) {
        quickRangeMode.value = ''
      } else {
        quickRangeMode.value = 'all'
      }
      syncFiltersToQuery()
    }
  )

  return {
    laneFilter,
    presetFilter,
    jobFilter,
    since,
    until,
    quickRangeMode,
    hasAnyFilter,
    currentQuickRangeLabel,
    quickRangeModes,
    lanePresets,
    applyQuickRange,
    applyLanePreset,
    clearAllFilters,
    getCurrentFilters,
    handleApplyFilters,
    syncFiltersToQuery,
    applyQueryToFilters,
    filtersAreEmpty
  }
}
