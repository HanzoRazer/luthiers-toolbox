/**
 * Composable for candidate list filtering logic.
 * Extracted from ManufacturingCandidateList.vue
 */
import { computed, ref, watch } from 'vue'

export type DecisionFilter = 'ALL' | 'UNDECIDED' | 'GREEN' | 'YELLOW' | 'RED'
export type StatusFilter = 'ALL' | 'PROPOSED' | 'ACCEPTED' | 'REJECTED'
export type SortKey = 'id' | 'id_desc' | 'created' | 'created_desc' | 'decided_at' | 'decided_at_desc' | 'decided_by' | 'decided_by_desc' | 'status' | 'decision'

export interface CandidateRow {
  candidate_id: string
  decision?: string | null
  decision_note?: string | null
  decided_by?: string | null
  decided_at_utc?: string | null
  advisory_id?: string | null
  status?: string | null
  // Allow additional properties for type compatibility with extended types
  [key: string]: unknown
}

export interface FilterPrefs {
  decisionFilter: string
  statusFilter: string
  searchText: string
  showSelectedOnly: boolean
  compact: boolean
  sortKey: string
}

export function useCandidateFilters(runId: () => string) {
  const decisionFilter = ref<DecisionFilter>('ALL')
  const statusFilter = ref<StatusFilter>('ALL')
  const showSelectedOnly = ref(false)
  const searchText = ref('')
  const filterDecidedBy = ref<string>('ALL')
  const filterOnlyMine = ref(false)
  const compact = ref(false)
  const sortKey = ref<SortKey>('id')

  // Preferences persistence
  const PREF_KEY = computed(() => `rmos:candidates:prefs:${runId() || 'unknown'}`)

  function readPrefs(): FilterPrefs | null {
    try {
      const raw = localStorage.getItem(PREF_KEY.value)
      if (!raw) return null
      const obj = JSON.parse(raw) as Partial<FilterPrefs>
      if (!obj) return null
      return {
        decisionFilter: obj.decisionFilter ?? 'ALL',
        statusFilter: obj.statusFilter ?? 'ALL',
        searchText: obj.searchText ?? '',
        showSelectedOnly: obj.showSelectedOnly ?? false,
        compact: obj.compact ?? false,
        sortKey: obj.sortKey ?? 'id',
      }
    } catch {
      return null
    }
  }

  function writePrefs(p: FilterPrefs) {
    try {
      localStorage.setItem(PREF_KEY.value, JSON.stringify(p))
    } catch {
      /* ignore */
    }
  }

  let prefsTimer: number | null = null
  function schedulePrefsSave() {
    if (prefsTimer) window.clearTimeout(prefsTimer)
    prefsTimer = window.setTimeout(() => {
      writePrefs({
        decisionFilter: decisionFilter.value,
        statusFilter: statusFilter.value,
        searchText: searchText.value,
        showSelectedOnly: showSelectedOnly.value,
        compact: compact.value,
        sortKey: sortKey.value,
      })
    }, 250)
  }

  // Watch for changes and persist
  watch([decisionFilter, statusFilter, searchText, showSelectedOnly, compact, sortKey], schedulePrefsSave)

  function loadPrefs() {
    const prefs = readPrefs()
    if (prefs) {
      decisionFilter.value = prefs.decisionFilter as DecisionFilter
      statusFilter.value = prefs.statusFilter as StatusFilter
      searchText.value = prefs.searchText
      showSelectedOnly.value = prefs.showSelectedOnly
      compact.value = prefs.compact
      sortKey.value = prefs.sortKey as SortKey
    }
  }

  function resetPrefs() {
    decisionFilter.value = 'ALL'
    statusFilter.value = 'ALL'
    searchText.value = ''
    showSelectedOnly.value = false
    compact.value = false
    sortKey.value = 'id'
    schedulePrefsSave()
  }

  function clearFilters() {
    decisionFilter.value = 'ALL'
    statusFilter.value = 'ALL'
    searchText.value = ''
    filterDecidedBy.value = 'ALL'
    filterOnlyMine.value = false
  }

  function quickUndecided() {
    decisionFilter.value = 'UNDECIDED'
    statusFilter.value = 'ALL'
    searchText.value = ''
  }

  // Audit sort cycling
  const AUDIT_SORT_CYCLE: SortKey[] = ['decided_at_desc', 'decided_at', 'decided_by', 'decided_by_desc']

  function cycleAuditSort() {
    const current = sortKey.value
    const idx = AUDIT_SORT_CYCLE.indexOf(current)
    if (idx === -1) {
      sortKey.value = 'decided_at_desc'
    } else if (idx === AUDIT_SORT_CYCLE.length - 1) {
      sortKey.value = 'id'
    } else {
      sortKey.value = AUDIT_SORT_CYCLE[idx + 1]
    }
  }

  const auditSortLabel = computed(() => {
    const sk = sortKey.value
    if (sk === 'decided_at_desc') return 'Time ↓'
    if (sk === 'decided_at') return 'Time ↑'
    if (sk === 'decided_by') return 'Operator A→Z'
    if (sk === 'decided_by_desc') return 'Operator Z→A'
    return 'none'
  })

  const auditSortArrow = computed(() => {
    const sk = sortKey.value
    if (sk === 'decided_at_desc' || sk === 'decided_by_desc') return '↓'
    if (sk === 'decided_at' || sk === 'decided_by') return '↑'
    return ''
  })

  // Filter helpers
  function normalize(s: unknown): string {
    return String(s ?? '').trim().toLowerCase()
  }

  function matchesSearch<T extends CandidateRow>(c: T, q: string): boolean {
    if (!q) return true
    const hay = [
      c.candidate_id,
      c.advisory_id ?? '',
      c.decision_note ?? '',
      c.decided_by ?? '',
    ].map(normalize).join(' | ')
    return hay.includes(q)
  }

  function filterCandidates<T extends CandidateRow>(
    candidates: T[],
    selectedIds: Set<string>,
    effectiveOperatorId: string
  ): T[] {
    const q = normalize(searchText.value)
    return candidates.filter((c) => {
      // Decision filter
      if (decisionFilter.value !== 'ALL') {
        if (decisionFilter.value === 'UNDECIDED' && c.decision != null) return false
        if (decisionFilter.value === 'GREEN' && c.decision !== 'GREEN') return false
        if (decisionFilter.value === 'YELLOW' && c.decision !== 'YELLOW') return false
        if (decisionFilter.value === 'RED' && c.decision !== 'RED') return false
      }

      // Status filter
      if (statusFilter.value !== 'ALL') {
        if (statusFilter.value === 'PROPOSED' && c.status !== 'PROPOSED') return false
        if (statusFilter.value === 'ACCEPTED' && c.status !== 'ACCEPTED') return false
        if (statusFilter.value === 'REJECTED' && c.status !== 'REJECTED') return false
      }

      // Decided-by filter
      if (filterDecidedBy.value !== 'ALL') {
        const v = (c.decided_by ?? '').trim()
        if (v !== filterDecidedBy.value) return false
      }

      // Only mine filter
      if (filterOnlyMine.value && effectiveOperatorId) {
        const v = (c.decided_by ?? '').trim()
        if (v !== effectiveOperatorId) return false
      }

      // Selected only
      if (showSelectedOnly.value && !selectedIds.has(c.candidate_id)) return false

      // Search
      if (!matchesSearch(c, q)) return false

      return true
    })
  }

  function sortCandidates<T extends CandidateRow>(candidates: T[]): T[] {
    const sk = sortKey.value
    return [...candidates].sort((a, b) => {
      switch (sk) {
        case 'id':
          return a.candidate_id.localeCompare(b.candidate_id)
        case 'id_desc':
          return b.candidate_id.localeCompare(a.candidate_id)
        case 'decided_at':
          return (a.decided_at_utc ?? '').localeCompare(b.decided_at_utc ?? '')
        case 'decided_at_desc':
          return (b.decided_at_utc ?? '').localeCompare(a.decided_at_utc ?? '')
        case 'decided_by':
          return (a.decided_by ?? '').localeCompare(b.decided_by ?? '')
        case 'decided_by_desc':
          return (b.decided_by ?? '').localeCompare(a.decided_by ?? '')
        case 'decision':
          return (a.decision ?? '').localeCompare(b.decision ?? '')
        case 'status':
          return (a.status ?? '').localeCompare(b.status ?? '')
        default:
          return 0
      }
    })
  }

  return {
    // State
    decisionFilter,
    statusFilter,
    showSelectedOnly,
    searchText,
    filterDecidedBy,
    filterOnlyMine,
    compact,
    sortKey,

    // Computed
    auditSortLabel,
    auditSortArrow,

    // Methods
    loadPrefs,
    resetPrefs,
    clearFilters,
    quickUndecided,
    cycleAuditSort,
    filterCandidates,
    sortCandidates,
    normalize,
    matchesSearch,
  }
}
