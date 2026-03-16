// packages/client/src/design-utilities/wood-intelligence/composables/useTonewoods.ts
/**
 * useTonewoods (MAT-004/005)
 *
 * Replaces hardcoded wood species data across the frontend with live registry data.
 *
 * Migration targets (MAT-005):
 *   StiffnessIndexPanel.vue  — was using HARDCODED_TONEWOODS (26 entries)
 *   BraceSinglePanel.vue     — was using COMMON_WOODS (9 entries, density only)
 *   art-studio.ts COMMON_WOODS — 9 hardcoded entries
 *
 * After this composable is adopted:
 *   - StiffnessIndexPanel gets the full 71-entry curated set with acoustic indices
 *   - BraceSinglePanel gets live density data
 *   - InstrumentMaterialSelector gets filterable, role-scoped species lists
 *
 * API: GET /api/registry/tonewoods
 * Falls back to empty list + error flag when backend unavailable.
 *
 * See docs/PLATFORM_ARCHITECTURE.md — Layer 3 / Utilities (Wood Intelligence).
 */

import { ref, computed, readonly } from 'vue'
import { api } from '@/services/apiBase'

// ---------------------------------------------------------------------------
// Types — mirror backend TonewoodEntry and sub-models
// ---------------------------------------------------------------------------

export interface MachiningNotes {
  burn_risk:    'low' | 'medium' | 'high'
  tearout_risk: 'low' | 'medium' | 'high'
  dust_hazard:  'low' | 'medium' | 'high'
  notes?: string | null
}

export interface TonewoodEntry {
  id: string
  name: string
  scientific_name?: string | null
  guitar_relevance: 'primary' | 'established' | 'emerging' | 'exotic'
  tier: 'tier_1' | 'tier_2'

  // Physical
  density_kg_m3?: number | null
  specific_gravity?: number | null
  janka_hardness_lbf?: number | null

  // Acoustic / structural
  modulus_of_elasticity_gpa?: number | null
  modulus_of_rupture_mpa?: number | null
  speed_of_sound_m_s?: number | null
  acoustic_impedance?: number | null

  // Tonal
  grain?: string | null
  tone_character?: string | null
  typical_uses: string[]
  sustainability?: string | null

  // Machining
  machining_notes?: MachiningNotes | null

  // Computed acoustic indices (from backend @computed_field)
  speed_of_sound_computed_m_s?: number | null
  radiation_ratio?: number | null
  specific_moe?: number | null
  ashby_index?: number | null
  acoustic_impedance_mrayl?: number | null
  has_acoustic_data: boolean
}

export interface TonewoodsResponse {
  tonewoods: TonewoodEntry[]
  total_count: number
  tier_1_count: number
  tier_2_count: number
  with_acoustic_data: number
}

// ---------------------------------------------------------------------------
// Role labels (matches backend ROLE_LABELS)
// ---------------------------------------------------------------------------

export const ROLE_LABELS: Record<string, string> = {
  soundboard:    'Soundboard / Top',
  top:           'Top',
  body_top:      'Body Top',
  back_sides:    'Back & Sides',
  neck:          'Neck',
  neck_laminate: 'Neck Laminate',
  fretboard:     'Fretboard',
  bridge:        'Bridge',
  bracing:       'Bracing',
  body:          'Body',
  decorative:    'Decorative / Accent',
  nuts:          'Nut / Saddle',
}

// MaterialSelection field → role mapping (matches backend MATERIAL_SELECTION_ROLES)
export const SELECTION_ROLE_MAP: Record<string, string> = {
  top:        'soundboard',
  back_sides: 'back_sides',
  neck:       'neck',
  fretboard:  'fretboard',
  bridge:     'bridge',
  brace_stock:'bracing',
}

// ---------------------------------------------------------------------------
// Module-level cache (shared across all composable instances)
// ---------------------------------------------------------------------------

const _cache = ref<TonewoodEntry[] | null>(null)
const _isLoading = ref(false)
const _error = ref<string | null>(null)

// ---------------------------------------------------------------------------
// Composable
// ---------------------------------------------------------------------------

export function useTonewoods() {

  /**
   * Load all tonewoods from the registry API.
   * Cached after first load — subsequent calls are instant.
   */
  async function loadTonewoods(forceRefresh = false): Promise<void> {
    if (_cache.value && !forceRefresh) return
    if (_isLoading.value) return

    _isLoading.value = true
    _error.value = null
    try {
      const response = await api('/api/registry/tonewoods')
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      const data: TonewoodsResponse = await response.json()
      _cache.value = data.tonewoods
    } catch (err) {
      _error.value = err instanceof Error ? err.message : 'Failed to load tonewoods'
      if (!_cache.value) _cache.value = []
    } finally {
      _isLoading.value = false
    }
  }

  /**
   * Load tonewoods filtered by instrument role from the API.
   * Returns only entries with `role` in their typical_uses.
   */
  async function loadTonewoodsForRole(role: string): Promise<TonewoodEntry[]> {
    try {
      const response = await api(`/api/registry/tonewoods?role=${encodeURIComponent(role)}`)
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      const data: TonewoodsResponse = await response.json()
      return data.tonewoods
    } catch (err) {
      _error.value = err instanceof Error ? err.message : 'Failed to load tonewoods'
      return []
    }
  }

  // --- Computed views of cached data ---

  const allTonewoods = computed<TonewoodEntry[]>(() => _cache.value ?? [])
  const isLoading = readonly(_isLoading)
  const error = readonly(_error)
  const isLoaded = computed(() => _cache.value !== null)
  const withAcousticData = computed(() => allTonewoods.value.filter(e => e.has_acoustic_data))

  /**
   * Filter cached tonewoods by role.
   * Uses client-side filter on cached data — use loadTonewoodsForRole() for server-side.
   */
  function forRole(role: string): TonewoodEntry[] {
    return allTonewoods.value.filter(e => e.typical_uses.includes(role))
  }

  /**
   * Get a tonewood by species ID.
   */
  function getById(id: string): TonewoodEntry | undefined {
    return allTonewoods.value.find(e => e.id === id)
  }

  /**
   * Compute plate mass for a given blank.
   * Used by StiffnessIndexPanel plate mass calculator.
   */
  function plateMassGrams(
    entry: TonewoodEntry,
    thicknessMm: number,
    widthMm: number,
    lengthMm: number,
  ): number | null {
    if (!entry.density_kg_m3) return null
    const volumeCm3 = (thicknessMm / 10) * (widthMm / 10) * (lengthMm / 10)
    const densityGPerCm3 = entry.density_kg_m3 / 1000
    return Math.round(volumeCm3 * densityGPerCm3 * 10) / 10
  }

  /**
   * Format a species for display in a select/dropdown.
   * Includes density hint for easier identification.
   */
  function formatForSelect(entry: TonewoodEntry): string {
    const density = entry.density_kg_m3 ? ` (${entry.density_kg_m3} kg/m³)` : ''
    return `${entry.name}${density}`
  }

  /**
   * Convert TonewoodEntry to the shape expected by BraceSinglePanel COMMON_WOODS.
   * Enables drop-in replacement of hardcoded array.
   */
  function toBracingWoodEntry(entry: TonewoodEntry): { name: string; density: number } {
    return {
      name: entry.name,
      density: entry.density_kg_m3 ?? 400,
    }
  }

  return {
    // State
    allTonewoods,
    isLoading,
    error,
    isLoaded,
    withAcousticData,

    // Actions
    loadTonewoods,
    loadTonewoodsForRole,

    // Queries
    forRole,
    getById,

    // Utilities
    plateMassGrams,
    formatForSelect,
    toBracingWoodEntry,

    // Constants
    ROLE_LABELS,
    SELECTION_ROLE_MAP,
  }
}
