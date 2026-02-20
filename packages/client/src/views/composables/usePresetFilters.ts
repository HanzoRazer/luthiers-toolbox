/**
 * Composable for preset filtering with localStorage persistence.
 * Extracted from PresetHubView.vue
 */
import { ref, computed, watch, onMounted, type Ref, type ComputedRef } from 'vue'

// ==========================================================================
// Types
// ==========================================================================

export interface Preset {
  id: string
  name: string
  kind: 'cam' | 'export' | 'neck' | 'combo'
  description?: string
  tags?: string[]
  machine_id?: string
  post_id?: string
  units?: string
  job_source_id?: string
  cam_params?: Record<string, unknown>
  export_params?: Record<string, unknown>
  neck_params?: Record<string, unknown>
}

export interface TabConfig {
  kind: string
  label: string
  icon: string
}

export interface PresetFiltersState {
  /** Current active tab */
  activeTab: Ref<string>
  /** Search query string */
  searchQuery: Ref<string>
  /** Selected tag filter */
  selectedTag: Ref<string>
  /** All unique tags from presets */
  availableTags: ComputedRef<string[]>
  /** Filtered presets based on tab, search, and tag */
  filteredPresets: ComputedRef<Preset[]>
  /** Get count of presets for a tab */
  getTabCount: (kind: string) => number
  /** Load persisted filter state from localStorage */
  loadPersistedState: () => void
  /** Save current filter state to localStorage */
  savePersistedState: () => void
}

// ==========================================================================
// Constants
// ==========================================================================

export const TAB_CONFIG: TabConfig[] = [
  { kind: 'all', label: 'All', icon: '📚' },
  { kind: 'cam', label: 'CAM', icon: '⚙️' },
  { kind: 'export', label: 'Export', icon: '📤' },
  { kind: 'neck', label: 'Neck', icon: '🎸' },
  { kind: 'combo', label: 'Combo', icon: '🎯' },
]

const STORAGE_KEYS = {
  ACTIVE_TAB: 'presethub.activeTab',
  SEARCH_QUERY: 'presethub.searchQuery',
  SELECTED_TAG: 'presethub.selectedTag',
} as const

// ==========================================================================
// Composable
// ==========================================================================

export function usePresetFilters(
  getPresets: () => Preset[]
): PresetFiltersState {
  const activeTab = ref<string>('all')
  const searchQuery = ref('')
  const selectedTag = ref('')

  // ========================================================================
  // Persistence
  // ========================================================================

  function loadPersistedState() {
    try {
      const savedTab = localStorage.getItem(STORAGE_KEYS.ACTIVE_TAB)
      if (savedTab) activeTab.value = savedTab

      const savedSearch = localStorage.getItem(STORAGE_KEYS.SEARCH_QUERY)
      if (savedSearch) searchQuery.value = savedSearch

      const savedTag = localStorage.getItem(STORAGE_KEYS.SELECTED_TAG)
      if (savedTag) selectedTag.value = savedTag
    } catch (error) {
      console.error('Failed to load persisted state:', error)
    }
  }

  function savePersistedState() {
    try {
      localStorage.setItem(STORAGE_KEYS.ACTIVE_TAB, activeTab.value)
      localStorage.setItem(STORAGE_KEYS.SEARCH_QUERY, searchQuery.value)
      localStorage.setItem(STORAGE_KEYS.SELECTED_TAG, selectedTag.value)
    } catch (error) {
      console.error('Failed to save state:', error)
    }
  }

  // ========================================================================
  // Computed
  // ========================================================================

  const availableTags = computed(() => {
    const tagSet = new Set<string>()
    getPresets().forEach((p) => {
      if (p.tags) {
        p.tags.forEach((tag) => tagSet.add(tag))
      }
    })
    return Array.from(tagSet).sort()
  })

  const filteredPresets = computed(() => {
    let filtered = getPresets()

    // Filter by tab
    if (activeTab.value !== 'all') {
      filtered = filtered.filter((p) => p.kind === activeTab.value)
    }

    // Filter by search
    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      filtered = filtered.filter(
        (p) =>
          p.name.toLowerCase().includes(query) ||
          (p.description && p.description.toLowerCase().includes(query))
      )
    }

    // Filter by tag
    if (selectedTag.value) {
      filtered = filtered.filter(
        (p) => p.tags && p.tags.includes(selectedTag.value)
      )
    }

    return filtered
  })

  // ========================================================================
  // Methods
  // ========================================================================

  function getTabCount(kind: string): number {
    const presets = getPresets()
    if (kind === 'all') return presets.length
    return presets.filter((p) => p.kind === kind).length
  }

  // ========================================================================
  // Watchers
  // ========================================================================

  watch([activeTab, searchQuery, selectedTag], () => {
    savePersistedState()
  })

  return {
    activeTab,
    searchQuery,
    selectedTag,
    availableTags,
    filteredPresets,
    getTabCount,
    loadPersistedState,
    savePersistedState,
  }
}
