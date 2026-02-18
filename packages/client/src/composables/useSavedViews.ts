/**
 * useSavedViews - Composable for managing saved filter views
 *
 * Extracted from RiskDashboardCrossLab.vue to enable reuse across
 * any dashboard or listing page that needs saved filter presets.
 *
 * Features:
 * - localStorage persistence with configurable key
 * - CRUD operations (create, rename, duplicate, delete)
 * - Default view management
 * - Search/filter saved views by name, description, tags
 * - Sort modes (default priority, name, created, lastUsed)
 * - Import/export as JSON
 * - Recently used views tracking
 */

import { computed, ref, type Ref } from 'vue'

// ────────────────────────────────────────────────────────────────────────────
// Types
// ────────────────────────────────────────────────────────────────────────────

export interface SavedView {
  id: string
  name: string
  /** Arbitrary filter key-value pairs */
  filters: Record<string, string>
  description?: string
  tags?: string[]
  createdAt: string
  lastUsedAt?: string | null
  isDefault?: boolean
}

export type ViewSortMode = 'default' | 'name' | 'created' | 'lastUsed'

export interface UseSavedViewsOptions {
  /** localStorage key for persistence */
  storageKey: string
  /** Get current filters to save - called when creating a new view */
  getCurrentFilters: () => Record<string, string>
  /** Called when a view is applied */
  onApply?: (filters: Record<string, string>) => void
}

// ────────────────────────────────────────────────────────────────────────────
// Composable
// ────────────────────────────────────────────────────────────────────────────

export function useSavedViews(options: UseSavedViewsOptions) {
  const { storageKey, getCurrentFilters, onApply } = options

  // ─────────────────────────────────────────────────────────────────────────
  // State
  // ─────────────────────────────────────────────────────────────────────────

  const savedViews = ref<SavedView[]>([])

  // Create form
  const newViewName = ref('')
  const newViewDescription = ref('')
  const newViewTags = ref('')
  const saveError = ref<string | null>(null)
  const saveHint = ref('')

  // View list filters
  const viewSearch = ref('')
  const viewTagFilter = ref('')
  const viewSortMode = ref<ViewSortMode>('default')

  // Import file input ref (for triggering file dialog)
  const importInputRef = ref<HTMLInputElement | null>(null)

  // ─────────────────────────────────────────────────────────────────────────
  // Helpers
  // ─────────────────────────────────────────────────────────────────────────

  function makeViewId(): string {
    return `view_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
  }

  function nowIso(): string {
    return new Date().toISOString()
  }

  function parseTags(input: string): string[] {
    if (!input.trim()) return []
    return input
      .split(',')
      .map((s) => s.trim())
      .filter((s) => s.length > 0)
  }

  function parseTime(t?: string | null): number {
    if (!t) return 0
    const d = Date.parse(t)
    return isNaN(d) ? 0 : d
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Persistence
  // ─────────────────────────────────────────────────────────────────────────

  /**
   * Known legacy filter field names that should be migrated to `filters` object.
   * RiskDashboardCrossLab used: lane, preset, jobHint, since, until
   */
  const LEGACY_FILTER_FIELDS = ['lane', 'preset', 'jobHint', 'since', 'until']

  /**
   * Detect if a view object is in legacy format (filter fields at top level)
   * vs new format (filter fields nested in `filters` object)
   */
  function isLegacyFormat(v: Record<string, unknown>): boolean {
    // If it has a `filters` object, it's new format
    if (v.filters && typeof v.filters === 'object') {
      return false
    }
    // If any legacy field exists at top level, it's legacy format
    return LEGACY_FILTER_FIELDS.some((field) => field in v)
  }

  /**
   * Migrate a legacy view to new format by moving filter fields into `filters` object
   */
  function migrateLegacyView(v: Record<string, unknown>): SavedView {
    const filters: Record<string, string> = {}

    // Extract legacy filter fields
    for (const field of LEGACY_FILTER_FIELDS) {
      if (field in v && v[field]) {
        filters[field] = String(v[field])
      }
    }

    return {
      id: String(v.id || makeViewId()),
      name: String(v.name || 'Unnamed'),
      filters,
      description: String(v.description || ''),
      tags: Array.isArray(v.tags)
        ? (v.tags as string[]).map(String).filter((t) => t.trim().length > 0)
        : [],
      createdAt: String(v.createdAt || nowIso()),
      lastUsedAt: v.lastUsedAt ? String(v.lastUsedAt) : null,
      isDefault: Boolean(v.isDefault),
    }
  }

  function loadSavedViews(): void {
    try {
      const raw = localStorage.getItem(storageKey)
      if (!raw) {
        savedViews.value = []
        return
      }
      const parsed = JSON.parse(raw)
      if (Array.isArray(parsed)) {
        let needsMigration = false

        savedViews.value = parsed
          .filter((v: unknown) => v && typeof v === 'object')
          .map((v: Record<string, unknown>) => {
            // Check if this view needs migration from legacy format
            if (isLegacyFormat(v)) {
              needsMigration = true
              return migrateLegacyView(v)
            }

            // New format - just normalize
            return {
              id: String(v.id || makeViewId()),
              name: String(v.name || 'Unnamed'),
              filters: (v.filters as Record<string, string>) || {},
              description: String(v.description || ''),
              tags: Array.isArray(v.tags)
                ? (v.tags as string[]).map(String).filter((t) => t.trim().length > 0)
                : [],
              createdAt: String(v.createdAt || nowIso()),
              lastUsedAt: v.lastUsedAt ? String(v.lastUsedAt) : null,
              isDefault: Boolean(v.isDefault),
            }
          })

        // If any views were migrated, persist the new format
        if (needsMigration) {
          console.log(`[useSavedViews] Migrated ${savedViews.value.length} views from legacy format`)
          persistSavedViews()
        }
      } else {
        savedViews.value = []
      }
    } catch (err) {
      console.error('Failed to load saved views', err)
      savedViews.value = []
    }
  }

  function persistSavedViews(): void {
    try {
      localStorage.setItem(storageKey, JSON.stringify(savedViews.value))
    } catch (err) {
      console.error('Failed to persist saved views', err)
    }
  }

  // ─────────────────────────────────────────────────────────────────────────
  // CRUD Operations
  // ─────────────────────────────────────────────────────────────────────────

  function saveCurrentView(): boolean {
    saveError.value = null
    saveHint.value = ''

    const name = newViewName.value.trim()
    if (!name) {
      saveError.value = 'Name is required.'
      return false
    }

    const existing = savedViews.value.find(
      (v) => v.name.toLowerCase() === name.toLowerCase()
    )
    if (existing) {
      saveError.value = 'A view with this name already exists.'
      return false
    }

    const now = nowIso()
    const view: SavedView = {
      id: makeViewId(),
      name,
      filters: getCurrentFilters(),
      description: newViewDescription.value.trim() || '',
      tags: parseTags(newViewTags.value),
      createdAt: now,
      lastUsedAt: null,
      isDefault: savedViews.value.length === 0,
    }

    savedViews.value = [...savedViews.value, view]
    persistSavedViews()

    // Clear form
    newViewName.value = ''
    newViewDescription.value = ''
    newViewTags.value = ''
    saveHint.value = 'View saved.'

    return true
  }

  function applySavedView(view: SavedView): void {
    // Update last used timestamp
    const now = nowIso()
    savedViews.value = savedViews.value.map((v) =>
      v.id === view.id ? { ...v, lastUsedAt: now } : v
    )
    persistSavedViews()

    // Notify parent to apply filters
    if (onApply) {
      onApply(view.filters)
    }
  }

  function renameView(id: string): void {
    const view = savedViews.value.find((v) => v.id === id)
    if (!view) return

    const newName = window.prompt('Rename view:', view.name)
    if (newName === null) return

    const trimmed = newName.trim()
    if (!trimmed) {
      saveError.value = 'Name cannot be empty.'
      return
    }

    const exists = savedViews.value.find(
      (v) => v.id !== id && v.name.toLowerCase() === trimmed.toLowerCase()
    )
    if (exists) {
      saveError.value = 'Another view already uses that name.'
      return
    }

    savedViews.value = savedViews.value.map((v) =>
      v.id === id ? { ...v, name: trimmed } : v
    )
    persistSavedViews()
    saveHint.value = 'View renamed.'
    saveError.value = null
  }

  function duplicateView(id: string): void {
    const original = savedViews.value.find((v) => v.id === id)
    if (!original) return

    const now = nowIso()
    const baseName = `${original.name} copy`
    let candidate = baseName
    let counter = 2
    while (
      savedViews.value.some(
        (v) => v.name.toLowerCase() === candidate.toLowerCase()
      )
    ) {
      candidate = `${baseName} ${counter}`
      counter += 1
    }

    const clone: SavedView = {
      ...original,
      id: makeViewId(),
      name: candidate,
      createdAt: now,
      lastUsedAt: null,
      isDefault: false,
    }

    savedViews.value = [...savedViews.value, clone]
    persistSavedViews()
    saveHint.value = 'View duplicated.'
    saveError.value = null
  }

  function deleteSavedView(id: string): void {
    const wasDefault = savedViews.value.find((v) => v.id === id)?.isDefault
    savedViews.value = savedViews.value.filter((v) => v.id !== id)

    if (wasDefault && savedViews.value.length > 0) {
      // Clear default flag (let user re-select)
      savedViews.value = savedViews.value.map((v) => ({
        ...v,
        isDefault: false,
      }))
    }

    persistSavedViews()
  }

  function setDefaultView(id: string): void {
    let found = false
    savedViews.value = savedViews.value.map((v) => {
      if (v.id === id) {
        found = true
        return { ...v, isDefault: true }
      }
      return { ...v, isDefault: false }
    })

    if (found) {
      persistSavedViews()
      saveHint.value = 'Default view updated.'
      saveError.value = null
    }
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Computed
  // ─────────────────────────────────────────────────────────────────────────

  const canSaveCurrentView = computed(() => {
    return !!newViewName.value.trim()
  })

  const defaultViewLabel = computed(() => {
    const d = savedViews.value.find((v) => v.isDefault)
    return d ? d.name : 'none'
  })

  const defaultView = computed(() => {
    return savedViews.value.find((v) => v.isDefault) || null
  })

  const allViewTags = computed<string[]>(() => {
    const set = new Set<string>()
    for (const v of savedViews.value) {
      if (Array.isArray(v.tags)) {
        for (const tag of v.tags) {
          const t = tag.trim()
          if (t) set.add(t)
        }
      }
    }
    return Array.from(set).sort((a, b) => a.localeCompare(b))
  })

  function viewMatchesFilter(view: SavedView): boolean {
    const s = viewSearch.value.trim().toLowerCase()
    const tagFilter = viewTagFilter.value.trim()

    if (tagFilter) {
      const tags = view.tags || []
      if (!tags.some((t) => t === tagFilter)) {
        return false
      }
    }

    if (!s) return true

    const haystackParts: string[] = []
    haystackParts.push(view.name || '')
    if (view.description) haystackParts.push(view.description)
    if (view.tags && view.tags.length) haystackParts.push(view.tags.join(' '))

    const haystack = haystackParts.join(' ').toLowerCase()
    return haystack.includes(s)
  }

  const sortedViews = computed<SavedView[]>(() => {
    const base = savedViews.value.filter(viewMatchesFilter)
    const arr = [...base]

    if (viewSortMode.value === 'name') {
      return arr.sort((a, b) =>
        a.name.toLowerCase().localeCompare(b.name.toLowerCase())
      )
    }

    if (viewSortMode.value === 'created') {
      return arr.sort(
        (a, b) => parseTime(b.createdAt) - parseTime(a.createdAt)
      )
    }

    if (viewSortMode.value === 'lastUsed') {
      return arr.sort((a, b) => {
        const at = parseTime(a.lastUsedAt || a.createdAt)
        const bt = parseTime(b.lastUsedAt || b.createdAt)
        return bt - at
      })
    }

    // Default: default view first, then by lastUsed/created, then by name
    return arr.sort((a, b) => {
      if (a.isDefault && !b.isDefault) return -1
      if (!a.isDefault && b.isDefault) return 1

      const at = parseTime(a.lastUsedAt || a.createdAt)
      const bt = parseTime(b.lastUsedAt || b.createdAt)
      if (bt !== at) return bt - at

      return a.name.toLowerCase().localeCompare(b.name.toLowerCase())
    })
  })

  const recentViews = computed<SavedView[]>(() => {
    const withTime = savedViews.value
      .map((v) => ({
        view: v,
        t: parseTime(v.lastUsedAt || v.createdAt),
      }))
      .filter((x) => x.t > 0)
    withTime.sort((a, b) => b.t - a.t)
    return withTime.slice(0, 5).map((x) => x.view)
  })

  // ─────────────────────────────────────────────────────────────────────────
  // Import/Export
  // ─────────────────────────────────────────────────────────────────────────

  function triggerImport(): void {
    if (importInputRef.value) {
      importInputRef.value.value = ''
      importInputRef.value.click()
    }
  }

  function handleImportFile(event: Event): void {
    const input = event.target as HTMLInputElement
    const file = input.files && input.files[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = () => {
      try {
        const text = String(reader.result || '')
        const data = JSON.parse(text)
        if (!Array.isArray(data)) {
          saveError.value = 'Invalid views file (expected an array).'
          return
        }

        const incoming: SavedView[] = data
          .filter((v: unknown) => v && typeof v === 'object')
          .map((v: Record<string, unknown>) => ({
            id: String(v.id || makeViewId()),
            name: String(v.name || 'Unnamed view'),
            filters: (v.filters as Record<string, string>) || {},
            description: String(v.description || ''),
            tags: Array.isArray(v.tags)
              ? (v.tags as string[]).map(String).filter((t) => t.trim().length > 0)
              : [],
            createdAt: String(v.createdAt || nowIso()),
            lastUsedAt: v.lastUsedAt ? String(v.lastUsedAt) : null,
            isDefault: Boolean(v.isDefault),
          }))

        // Merge by name (incoming overwrites)
        const byName = new Map<string, SavedView>()
        for (const v of savedViews.value) {
          byName.set(v.name.toLowerCase(), v)
        }
        for (const v of incoming) {
          byName.set(v.name.toLowerCase(), v)
        }

        const merged = Array.from(byName.values())

        // Ensure only one default
        let defaultSeen = false
        const normalized = merged.map((v) => {
          if (v.isDefault) {
            if (defaultSeen) {
              return { ...v, isDefault: false }
            }
            defaultSeen = true
            return v
          }
          return v
        })

        savedViews.value = normalized
        persistSavedViews()
        saveError.value = null
        saveHint.value = 'Views imported.'
      } catch (err) {
        console.error('Failed to import views', err)
        saveError.value = 'Failed to import views.'
      }
    }
    reader.readAsText(file)
  }

  function exportViews(): void {
    if (!savedViews.value.length) return
    try {
      const blob = new Blob([JSON.stringify(savedViews.value, null, 2)], {
        type: 'application/json',
      })
      const stamp = new Date().toISOString().replace(/[:.]/g, '-')
      const filename = `saved_views_${stamp}.json`
      const url = URL.createObjectURL(blob)

      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Failed to export views', err)
      saveError.value = 'Failed to export views.'
    }
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Tooltip helper
  // ─────────────────────────────────────────────────────────────────────────

  function viewTooltip(view: SavedView): string {
    const parts: string[] = []
    for (const [key, val] of Object.entries(view.filters)) {
      if (val) parts.push(`${key}=${val}`)
    }
    if (view.description) parts.push(`desc=${view.description}`)
    if (view.tags && view.tags.length) {
      parts.push(`tags=${view.tags.join(', ')}`)
    }
    return parts.length ? parts.join(' · ') : 'No filters'
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Time formatting helpers
  // ─────────────────────────────────────────────────────────────────────────

  function formatMetaTime(ts?: string | null): string {
    if (!ts) return '—'
    try {
      const d = new Date(ts)
      return d.toLocaleString()
    } catch {
      return ts
    }
  }

  function formatRelativeTime(ts?: string | null): string {
    if (!ts) return 'unknown'
    const t = Date.parse(ts)
    if (isNaN(t)) return ts
    const now = Date.now()
    const diffMs = now - t
    const diffSec = Math.floor(diffMs / 1000)
    const diffMin = Math.floor(diffSec / 60)
    const diffHr = Math.floor(diffMin / 60)
    const diffDay = Math.floor(diffHr / 24)

    if (diffDay > 0) return `${diffDay}d ago`
    if (diffHr > 0) return `${diffHr}h ago`
    if (diffMin > 0) return `${diffMin}m ago`
    return 'just now'
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Return public API
  // ─────────────────────────────────────────────────────────────────────────

  return {
    // State
    savedViews,
    newViewName,
    newViewDescription,
    newViewTags,
    saveError,
    saveHint,
    viewSearch,
    viewTagFilter,
    viewSortMode,
    importInputRef,

    // Computed
    canSaveCurrentView,
    defaultViewLabel,
    defaultView,
    allViewTags,
    sortedViews,
    recentViews,

    // Methods
    loadSavedViews,
    saveCurrentView,
    applySavedView,
    renameView,
    duplicateView,
    deleteSavedView,
    setDefaultView,
    triggerImport,
    handleImportFile,
    exportViews,
    viewTooltip,
    formatMetaTime,
    formatRelativeTime,
  }
}
