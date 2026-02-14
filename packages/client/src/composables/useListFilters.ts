/**
 * Generic composable for list filtering, sorting, and search.
 * Domain-agnostic — works with any row type that has an `id` field.
 *
 * Extracted & genericized from useCandidateFilters (RMOS domain).
 */
import { computed, ref, watch } from 'vue'

// ---- Public types ----

export type SortDirection = 'asc' | 'desc'

export interface SortConfig<K extends string = string> {
  key: K
  direction: SortDirection
}

/** Minimum contract a row must satisfy. */
export interface FilterableRow {
  id: string
  [key: string]: unknown
}

/** Persisted user preferences for a filterable list. */
export interface FilterPrefs {
  categoryFilter: string
  statusFilter: string
  searchText: string
  showSelectedOnly: boolean
  compact: boolean
  sortKey: string
}

// ---- Composable options ----

export interface UseListFiltersOptions {
  /** Unique key supplier for localStorage persistence (e.g. a run-id). */
  persistenceKey?: () => string
  /** Category filter values (first entry = default "show all"). */
  categoryValues?: readonly string[]
  /** Status filter values (first entry = default "show all"). */
  statusValues?: readonly string[]
  /** Fields on the row to include in free-text search. */
  searchableFields?: string[]
}

const DEFAULTS: Required<UseListFiltersOptions> = {
  persistenceKey: () => 'unknown',
  categoryValues: ['ALL'],
  statusValues: ['ALL'],
  searchableFields: ['id'],
}

// ---- Composable ----

export function useListFilters<T extends FilterableRow>(
  options: UseListFiltersOptions = {},
) {
  const opts = { ...DEFAULTS, ...options } as Required<UseListFiltersOptions>

  // --- State ---
  const categoryFilter = ref(opts.categoryValues[0] ?? 'ALL')
  const statusFilter = ref(opts.statusValues[0] ?? 'ALL')
  const showSelectedOnly = ref(false)
  const searchText = ref('')
  const compact = ref(false)
  const sortKey = ref('id')

  // --- Persistence ---
  const PREF_KEY = computed(() => `list:filters:prefs:${opts.persistenceKey()}`)

  function readPrefs(): FilterPrefs | null {
    try {
      const raw = localStorage.getItem(PREF_KEY.value)
      if (!raw) return null
      const obj = JSON.parse(raw) as Partial<FilterPrefs>
      return {
        categoryFilter: obj.categoryFilter ?? opts.categoryValues[0] ?? 'ALL',
        statusFilter: obj.statusFilter ?? opts.statusValues[0] ?? 'ALL',
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
        categoryFilter: categoryFilter.value,
        statusFilter: statusFilter.value,
        searchText: searchText.value,
        showSelectedOnly: showSelectedOnly.value,
        compact: compact.value,
        sortKey: sortKey.value,
      })
    }, 250)
  }

  watch(
    [categoryFilter, statusFilter, searchText, showSelectedOnly, compact, sortKey],
    schedulePrefsSave,
  )

  function loadPrefs() {
    const prefs = readPrefs()
    if (prefs) {
      categoryFilter.value = prefs.categoryFilter
      statusFilter.value = prefs.statusFilter
      searchText.value = prefs.searchText
      showSelectedOnly.value = prefs.showSelectedOnly
      compact.value = prefs.compact
      sortKey.value = prefs.sortKey
    }
  }

  function resetPrefs() {
    categoryFilter.value = opts.categoryValues[0] ?? 'ALL'
    statusFilter.value = opts.statusValues[0] ?? 'ALL'
    searchText.value = ''
    showSelectedOnly.value = false
    compact.value = false
    sortKey.value = 'id'
    schedulePrefsSave()
  }

  // --- Filtering ---

  function clearFilters() {
    categoryFilter.value = opts.categoryValues[0] ?? 'ALL'
    statusFilter.value = opts.statusValues[0] ?? 'ALL'
    searchText.value = ''
  }

  function normalize(s: unknown): string {
    return String(s ?? '').trim().toLowerCase()
  }

  function matchesSearch(row: T, query: string): boolean {
    if (!query) return true
    const hay = opts.searchableFields
      .map((f) => normalize((row as Record<string, unknown>)[f]))
      .join(' | ')
    return hay.includes(query)
  }

  /**
   * Filter rows by category, status, selection, and free-text search.
   *
   * @param rows        - Full row list
   * @param selectedIds - Currently selected ids (for "show selected only")
   * @param categoryField - Row field to match against `categoryFilter`
   * @param statusField   - Row field to match against `statusFilter`
   */
  function filterRows(
    rows: T[],
    selectedIds: Set<string>,
    categoryField: keyof T = 'category' as keyof T,
    statusField: keyof T = 'status' as keyof T,
  ): T[] {
    const q = normalize(searchText.value)
    const catAll = opts.categoryValues[0] ?? 'ALL'
    const statAll = opts.statusValues[0] ?? 'ALL'

    return rows.filter((row) => {
      // Category filter
      if (categoryFilter.value !== catAll) {
        const val = normalize(row[categoryField])
        if (val !== normalize(categoryFilter.value)) return false
      }

      // Status filter
      if (statusFilter.value !== statAll) {
        const val = normalize(row[statusField])
        if (val !== normalize(statusFilter.value)) return false
      }

      // Selected only
      if (showSelectedOnly.value && !selectedIds.has(row.id)) return false

      // Free-text search
      if (!matchesSearch(row, q)) return false

      return true
    })
  }

  // --- Sorting ---

  function sortRows(rows: T[], key?: string, direction?: SortDirection): T[] {
    const sk = key ?? sortKey.value
    const isDesc = direction === 'desc' || sk.endsWith('_desc')
    const baseKey = sk.replace(/_desc$/, '')

    return [...rows].sort((a, b) => {
      const aVal = normalize((a as Record<string, unknown>)[baseKey])
      const bVal = normalize((b as Record<string, unknown>)[baseKey])
      const cmp = aVal.localeCompare(bVal)
      return isDesc ? -cmp : cmp
    })
  }

  return {
    // State
    categoryFilter,
    statusFilter,
    showSelectedOnly,
    searchText,
    compact,
    sortKey,

    // Methods
    loadPrefs,
    resetPrefs,
    clearFilters,
    filterRows,
    sortRows,
    normalize,
    matchesSearch,
  }
}
