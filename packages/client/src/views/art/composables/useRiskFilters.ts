/**
 * Composable for risk dashboard filter management.
 * Handles filter state, URL sync, quick ranges, and lane presets.
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import { useRouter, useRoute } from 'vue-router'

export type QuickRangeMode = '' | 'all' | 'last7' | 'last30' | 'last90' | 'year'

export interface LanePresetDef {
  id: string
  label: string
  lane: string
  preset: string
  defaultQuickRange?: QuickRangeMode
  badge?: string
}

export interface RiskFiltersState {
  laneFilter: Ref<string>
  presetFilter: Ref<string>
  jobFilter: Ref<string>
  since: Ref<string>
  until: Ref<string>
  quickRangeMode: Ref<QuickRangeMode>
  lanePresets: Ref<LanePresetDef[]>
  hasAnyFilter: ComputedRef<boolean>
  currentQuickRangeLabel: ComputedRef<string>
  getCurrentFilters: () => Record<string, string>
  applyFilters: (filters: Record<string, string>) => void
  applyQuickRange: (mode: QuickRangeMode) => void
  applyLanePreset: (id: string) => void
  clearAllFilters: () => void
  applyQueryToFilters: () => void
  syncFiltersToQuery: () => void
  filtersAreEmpty: () => boolean
}

const QUICK_RANGE_MODES = [
  { id: 'all' as QuickRangeMode, label: 'All' },
  { id: 'last7' as QuickRangeMode, label: 'Last 7d' },
  { id: 'last30' as QuickRangeMode, label: 'Last 30d' },
  { id: 'last90' as QuickRangeMode, label: 'Last 90d' },
  { id: 'year' as QuickRangeMode, label: 'This year' },
]

const DEFAULT_LANE_PRESETS: LanePresetDef[] = [
  { id: 'rosette_safe_30', label: 'Rosette · Safe (30d)', lane: 'Rosette', preset: 'Safe', defaultQuickRange: 'last30', badge: 'Rosette' },
  { id: 'adaptive_aggressive_30', label: 'Adaptive · Aggressive (30d)', lane: 'Adaptive', preset: 'Aggressive', defaultQuickRange: 'last30', badge: 'Adaptive' },
  { id: 'relief_safe_90', label: 'Relief · Safe (90d)', lane: 'Relief', preset: 'Safe', defaultQuickRange: 'last90', badge: 'Relief' },
  { id: 'pipeline_any_30', label: 'Pipeline · Any (30d)', lane: 'Pipeline', preset: '', defaultQuickRange: 'last30', badge: 'Pipeline' },
]

function toIsoDate(d: Date): string {
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

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

export function useRiskFilters(): RiskFiltersState {
  const router = useRouter()
  const route = useRoute()

  const laneFilter = ref('')
  const presetFilter = ref('')
  const jobFilter = ref('')
  const since = ref('')
  const until = ref('')
  const quickRangeMode = ref<QuickRangeMode>('')
  const lanePresets = ref<LanePresetDef[]>(DEFAULT_LANE_PRESETS)

  const hasAnyFilter = computed(() => {
    return !!laneFilter.value || !!presetFilter.value || !!jobFilter.value || !!since.value || !!until.value
  })

  const currentQuickRangeLabel = computed(() => {
    const entry = QUICK_RANGE_MODES.find((m) => m.id === quickRangeMode.value)
    return entry ? entry.label : 'Custom'
  })

  function getCurrentFilters(): Record<string, string> {
    return {
      lane: laneFilter.value,
      preset: presetFilter.value,
      jobHint: jobFilter.value,
      since: since.value,
      until: until.value,
    }
  }

  function applyFilters(filters: Record<string, string>) {
    laneFilter.value = filters.lane || ''
    presetFilter.value = filters.preset || ''
    jobFilter.value = filters.jobHint || ''
    since.value = filters.since || ''
    until.value = filters.until || ''
    quickRangeMode.value = !since.value && !until.value ? 'all' : ''
    syncFiltersToQuery()
  }

  function applyQuickRange(mode: QuickRangeMode) {
    const { start, end } = computeDateRange(mode)
    quickRangeMode.value = mode
    since.value = start
    until.value = end
    syncFiltersToQuery()
  }

  function applyLanePreset(id: string) {
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
  }

  function clearAllFilters() {
    laneFilter.value = ''
    presetFilter.value = ''
    jobFilter.value = ''
    since.value = ''
    until.value = ''
    quickRangeMode.value = 'all'
    syncFiltersToQuery()
  }

  function applyQueryToFilters() {
    const q = route.query
    laneFilter.value = typeof q.lane === 'string' ? q.lane : ''
    presetFilter.value = typeof q.preset === 'string' ? q.preset : ''
    jobFilter.value = typeof q.job_hint === 'string' ? q.job_hint : ''
    since.value = typeof q.since === 'string' ? q.since : ''
    until.value = typeof q.until === 'string' ? q.until : ''
    quickRangeMode.value = !since.value && !until.value ? 'all' : ''
  }

  function syncFiltersToQuery() {
    const q: Record<string, string> = {}
    if (laneFilter.value.trim()) q.lane = laneFilter.value.trim()
    if (presetFilter.value.trim()) q.preset = presetFilter.value.trim()
    if (jobFilter.value.trim()) q.job_hint = jobFilter.value.trim()
    if (since.value.trim()) q.since = since.value.trim()
    if (until.value.trim()) q.until = until.value.trim()
    router.replace({ query: q }).catch(() => {})
  }

  function filtersAreEmpty(): boolean {
    return !laneFilter.value && !presetFilter.value && !jobFilter.value && !since.value && !until.value
  }

  return {
    laneFilter,
    presetFilter,
    jobFilter,
    since,
    until,
    quickRangeMode,
    lanePresets,
    hasAnyFilter,
    currentQuickRangeLabel,
    getCurrentFilters,
    applyFilters,
    applyQuickRange,
    applyLanePreset,
    clearAllFilters,
    applyQueryToFilters,
    syncFiltersToQuery,
    filtersAreEmpty,
  }
}
