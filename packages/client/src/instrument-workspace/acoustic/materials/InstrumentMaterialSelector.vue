<!--
  InstrumentMaterialSelector.vue (MAT-006)

  Materials selection panel for Instrument Hub — Body stage.

  Replaces the plain text-input material entry in InstrumentHubShell.vue
  with a proper species browser backed by GET /api/registry/tonewoods.

  Features:
    - Species browser filtered by instrument role (top, back/sides, neck, etc.)
    - Shows acoustic indices inline (radiation ratio, density)
    - Selection written into MaterialSelection project state via useInstrumentProject
    - Falls back gracefully when API is unavailable (shows text input)

  Usage in InstrumentHubShell.vue (Body stage):
    <InstrumentMaterialSelector
      :current-selection="materialSelection"
      @update="handleMaterialUpdate"
    />

  See docs/PLATFORM_ARCHITECTURE.md — Layer 2 / Instrument Hub.
-->

<template>
  <div class="ims">
    <!-- Loading / error states -->
    <div v-if="isLoading" class="ims-loading">
      <span class="ims-spinner" />
      Loading tonewood database…
    </div>

    <div v-if="error" class="ims-error-banner">
      ⚠️ Could not load tonewood database. Using manual entry.
    </div>

    <!-- Role rows -->
    <div class="ims-roles">
      <div
        v-for="role in visibleRoles"
        :key="role.field"
        class="ims-role-row"
        :class="{ 'ims-role-row--active': activeField === role.field }"
      >
        <!-- Role header -->
        <div class="ims-role-header" @click="toggleField(role.field)">
          <span class="ims-role-label">{{ role.label }}</span>
          <div class="ims-role-value" :class="{ 'ims-role-value--set': currentSelection[role.field] }">
            {{ displayName(role.field) || 'Not selected' }}
          </div>
          <span class="ims-expand-icon">{{ activeField === role.field ? '▲' : '▼' }}</span>
        </div>

        <!-- Species browser (expanded) -->
        <div v-if="activeField === role.field" class="ims-browser">

          <!-- Search -->
          <div class="ims-search-row">
            <input
              v-model="searchQuery"
              class="ims-search"
              :placeholder="`Search ${role.label.toLowerCase()}…`"
              @input="searchQuery = ($event.target as HTMLInputElement).value"
            />
            <button
              v-if="currentSelection[role.field]"
              class="ims-clear-btn"
              @click="clearSelection(role.field)"
            >
              Clear
            </button>
          </div>

          <!-- Species list -->
          <div class="ims-species-list">
            <div
              v-for="entry in filteredSpecies(role)"
              :key="entry.id"
              class="ims-species-item"
              :class="{ 'ims-species-item--selected': currentSelection[role.field] === entry.id }"
              @click="selectSpecies(role.field, entry.id)"
            >
              <div class="ims-species-name">
                {{ entry.name }}
                <span class="ims-species-tier" :class="`ims-tier--${entry.tier}`">
                  {{ entry.tier === 'tier_1' ? '★' : '◆' }}
                </span>
              </div>
              <div class="ims-species-meta">
                <span v-if="entry.density_kg_m3" class="ims-mono">
                  {{ entry.density_kg_m3 }} kg/m³
                </span>
                <span
                  v-if="entry.radiation_ratio"
                  class="ims-mono ims-rr"
                  :title="'Radiation ratio (Schelleng c/ρ × 10⁶) — higher = more projecting'"
                >
                  RR {{ entry.radiation_ratio.toFixed(1) }}
                </span>
                <span v-if="entry.tone_character" class="ims-tone">
                  {{ entry.tone_character }}
                </span>
              </div>
              <div v-if="entry.machining_notes" class="ims-species-risks">
                <span
                  v-if="entry.machining_notes.burn_risk !== 'low'"
                  class="ims-risk-badge"
                  :class="`ims-risk--${entry.machining_notes.burn_risk}`"
                >
                  burn {{ entry.machining_notes.burn_risk }}
                </span>
                <span
                  v-if="entry.machining_notes.tearout_risk !== 'low'"
                  class="ims-risk-badge"
                  :class="`ims-risk--${entry.machining_notes.tearout_risk}`"
                >
                  tearout {{ entry.machining_notes.tearout_risk }}
                </span>
              </div>
            </div>

            <!-- Empty state -->
            <div v-if="filteredSpecies(role).length === 0" class="ims-empty">
              <span v-if="isLoading">Loading…</span>
              <span v-else-if="searchQuery">No matches for "{{ searchQuery }}"</span>
              <span v-else>No species available for this role.</span>
            </div>
          </div>

          <!-- Manual entry fallback -->
          <div class="ims-manual">
            <input
              class="ims-manual-input"
              :value="currentSelection[role.field] || ''"
              placeholder="Or type species ID directly…"
              @change="selectSpecies(role.field, ($event.target as HTMLInputElement).value)"
            />
            <span class="ims-manual-hint">Species ID from the tonewood registry</span>
          </div>

        </div>
      </div>
    </div>

    <!-- Summary row when all collapsed -->
    <div v-if="!activeField && selectedCount > 0" class="ims-summary">
      {{ selectedCount }} of {{ visibleRoles.length }} materials selected
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useTonewoods, type TonewoodEntry, SELECTION_ROLE_MAP, ROLE_LABELS } from '../composables/useTonewoods'
import type { MaterialSelection } from '@/api/projects'

// ---------------------------------------------------------------------------
// Props & Emits
// ---------------------------------------------------------------------------

const props = defineProps<{
  currentSelection: MaterialSelection | null
  /** Instrument type — filters which roles are shown */
  instrumentType?: string | null
}>()

const emit = defineEmits<{
  (e: 'update', selection: MaterialSelection): void
}>()

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

const activeField = ref<string | null>(null)
const searchQuery = ref('')

const { allTonewoods, isLoading, error, loadTonewoods, getById } = useTonewoods()

// Local copy of selection — emits on change, does not auto-commit
const localSelection = ref<Record<string, string>>({})

watch(() => props.currentSelection, (sel) => {
  if (sel) {
    localSelection.value = {
      top:        sel.top        ?? '',
      back_sides: sel.back_sides ?? '',
      neck:       sel.neck       ?? '',
      fretboard:  sel.fretboard  ?? '',
      bridge:     sel.bridge     ?? '',
      brace_stock:sel.brace_stock ?? '',
    }
  }
}, { immediate: true })

// ---------------------------------------------------------------------------
// Roles definition
// ---------------------------------------------------------------------------

const ALL_ROLES = [
  { field: 'top',         label: 'Top / Soundboard', role: 'soundboard'  },
  { field: 'back_sides',  label: 'Back & Sides',      role: 'back_sides'  },
  { field: 'neck',        label: 'Neck',              role: 'neck'        },
  { field: 'fretboard',   label: 'Fretboard',         role: 'fretboard'   },
  { field: 'bridge',      label: 'Bridge',            role: 'bridge'      },
  { field: 'brace_stock', label: 'Brace Stock',       role: 'bracing'     },
]

// Hide soundboard/bracing for electric/bass (they don't have tops or bracing)
const visibleRoles = computed(() => {
  const t = props.instrumentType
  if (t === 'electric_guitar' || t === 'bass') {
    return ALL_ROLES.filter(r => !['top', 'brace_stock'].includes(r.field))
  }
  return ALL_ROLES
})

// ---------------------------------------------------------------------------
// Computed
// ---------------------------------------------------------------------------

const currentSelection = computed<Record<string, string>>(() => localSelection.value)

const selectedCount = computed(() =>
  visibleRoles.value.filter(r => currentSelection.value[r.field]).length
)

function filteredSpecies(role: { field: string; role: string }): TonewoodEntry[] {
  const forRole = allTonewoods.value.filter(e => e.typical_uses.includes(role.role))
  if (!searchQuery.value) return forRole
  const q = searchQuery.value.toLowerCase()
  return forRole.filter(e =>
    e.name.toLowerCase().includes(q) ||
    e.id.toLowerCase().includes(q) ||
    (e.tone_character ?? '').toLowerCase().includes(q)
  )
}

function displayName(field: string): string {
  const id = currentSelection.value[field]
  if (!id) return ''
  const entry = getById(id)
  return entry ? entry.name : id
}

// ---------------------------------------------------------------------------
// Actions
// ---------------------------------------------------------------------------

function toggleField(field: string): void {
  activeField.value = activeField.value === field ? null : field
  searchQuery.value = ''
}

function selectSpecies(field: string, id: string): void {
  localSelection.value = { ...localSelection.value, [field]: id }
  emit('update', buildSelection())
}

function clearSelection(field: string): void {
  localSelection.value = { ...localSelection.value, [field]: '' }
  emit('update', buildSelection())
}

function buildSelection(): MaterialSelection {
  return {
    top:         localSelection.value.top        || null,
    back_sides:  localSelection.value.back_sides || null,
    neck:        localSelection.value.neck       || null,
    fretboard:   localSelection.value.fretboard  || null,
    bridge:      localSelection.value.bridge     || null,
    brace_stock: localSelection.value.brace_stock || null,
  }
}

// ---------------------------------------------------------------------------
// Lifecycle
// ---------------------------------------------------------------------------

onMounted(() => loadTonewoods())
</script>

<style scoped>
.ims { display: flex; flex-direction: column; gap: 0.25rem; font-family: var(--font-sans, system-ui); }

.ims-loading { display: flex; align-items: center; gap: 0.5rem; font-size: 0.82rem; color: var(--color-text-secondary); padding: 0.5rem; }
.ims-spinner { width: 0.9rem; height: 0.9rem; border: 1.5px solid var(--color-border-secondary); border-top-color: #667eea; border-radius: 50%; animation: spin 0.8s linear infinite; flex-shrink: 0; }
@keyframes spin { to { transform: rotate(360deg); } }
.ims-error-banner { font-size: 0.78rem; color: #D85A30; padding: 0.4rem 0.6rem; background: #FEF2F2; border-radius: 0.35rem; }

/* Role rows */
.ims-roles { display: flex; flex-direction: column; gap: 0.2rem; }
.ims-role-row { border: 0.5px solid var(--color-border-tertiary); border-radius: 0.4rem; overflow: hidden; }
.ims-role-row--active { border-color: #667eea; }
.ims-role-header { display: grid; grid-template-columns: 110px 1fr auto; align-items: center; gap: 0.75rem; padding: 0.45rem 0.75rem; cursor: pointer; background: var(--color-background-secondary); }
.ims-role-header:hover { background: var(--color-background-tertiary); }
.ims-role-label { font-size: 0.78rem; font-weight: 500; white-space: nowrap; }
.ims-role-value { font-size: 0.78rem; color: var(--color-text-tertiary); font-style: italic; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ims-role-value--set { color: #1D9E75; font-style: normal; font-family: var(--font-mono, monospace); }
.ims-expand-icon { font-size: 0.65rem; color: var(--color-text-tertiary); }

/* Browser */
.ims-browser { padding: 0.6rem 0.75rem; display: flex; flex-direction: column; gap: 0.5rem; border-top: 0.5px solid var(--color-border-tertiary); }
.ims-search-row { display: flex; gap: 0.5rem; }
.ims-search { flex: 1; padding: 0.3rem 0.5rem; border: 0.5px solid var(--color-border-secondary); border-radius: 0.3rem; font-size: 0.8rem; font-family: inherit; }
.ims-clear-btn { padding: 0.3rem 0.6rem; border: 0.5px solid var(--color-border-secondary); border-radius: 0.3rem; background: transparent; font-size: 0.75rem; cursor: pointer; color: #D85A30; }

/* Species list */
.ims-species-list { max-height: 220px; overflow-y: auto; display: flex; flex-direction: column; gap: 0.15rem; }
.ims-species-item { padding: 0.4rem 0.6rem; border-radius: 0.3rem; cursor: pointer; border: 0.5px solid transparent; transition: all 0.1s; }
.ims-species-item:hover { background: var(--color-background-secondary); }
.ims-species-item--selected { background: #EEF2FF; border-color: #667eea; }
.ims-species-name { display: flex; align-items: center; gap: 0.4rem; font-size: 0.82rem; font-weight: 500; }
.ims-species-tier { font-size: 0.65rem; }
.ims-tier--tier_1 { color: #BA7517; }
.ims-tier--tier_2 { color: #6B7280; }
.ims-species-meta { display: flex; gap: 0.75rem; font-size: 0.72rem; color: var(--color-text-tertiary); margin-top: 0.1rem; flex-wrap: wrap; }
.ims-mono { font-family: var(--font-mono, monospace); }
.ims-rr { color: #1D9E75; }
.ims-tone { font-style: italic; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 180px; }
.ims-species-risks { display: flex; gap: 0.35rem; margin-top: 0.2rem; flex-wrap: wrap; }
.ims-risk-badge { font-size: 0.65rem; padding: 0.1rem 0.35rem; border-radius: 0.2rem; }
.ims-risk--medium { background: #FEF3C7; color: #92400E; }
.ims-risk--high { background: #FEE2E2; color: #991B1B; }
.ims-empty { padding: 0.75rem; font-size: 0.8rem; color: var(--color-text-tertiary); text-align: center; font-style: italic; }

/* Manual entry */
.ims-manual { display: flex; flex-direction: column; gap: 0.2rem; padding-top: 0.4rem; border-top: 0.5px dashed var(--color-border-tertiary); }
.ims-manual-input { padding: 0.3rem 0.5rem; border: 0.5px solid var(--color-border-tertiary); border-radius: 0.3rem; font-size: 0.78rem; font-family: var(--font-mono, monospace); }
.ims-manual-hint { font-size: 0.68rem; color: var(--color-text-tertiary); }

/* Summary */
.ims-summary { font-size: 0.75rem; color: var(--color-text-tertiary); text-align: right; padding: 0.2rem 0; }
</style>
