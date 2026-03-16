<!--
  InstrumentHubShell.vue (HUB-003 / HUB-004)

  The primary editor of the Instrument Project Graph — Layer 2 Workspace.

  This replaces GuitarDesignHub.vue as the project-aware instrument design workspace.
  GuitarDesignHub.vue is kept for now as a legacy route until Phase 7 cleanup.

  Architecture rules:
    - Reads project state via useInstrumentProject()
    - Edits are LOCAL to each stage panel until user clicks "Apply to Project"
    - Never auto-commits on input change
    - Does NOT contain engine math — all computation via API calls
    - Stages: Body | Neck | Bridge | Bracing | Setup | CNC Prep

  Props:
    projectId — required. Load from route param or parent project context.

  Emits:
    project-updated — when any commit succeeds (for parent refresh)

  Exit criteria (HUB-003/004):
    ✅ Open a project
    ✅ Edit core dimensions / materials
    ✅ Persist and reload correctly
    ✅ Stage navigation is explicit and build-stage-ordered

  See docs/PLATFORM_ARCHITECTURE.md — Layer 2 / Workspaces.
-->

<template>
  <div class="ihs">

    <!-- Loading state -->
    <div v-if="isLoading" class="ihs-loading">
      <div class="ihs-spinner" />
      <span>Loading project…</span>
    </div>

    <!-- Load error -->
    <div v-else-if="loadError" class="ihs-error">
      <span class="ihs-error-icon">❌</span>
      <div>
        <strong>Could not load project.</strong>
        <p>{{ loadError }}</p>
        <button class="ihs-btn ihs-btn--ghost" @click="retry">Retry</button>
      </div>
    </div>

    <!-- No project -->
    <div v-else-if="!isLoaded" class="ihs-empty">
      <div class="ihs-empty-icon">🎸</div>
      <p>No project loaded. Open or create a project to begin.</p>
    </div>

    <!-- Hub content -->
    <div v-else class="ihs-content">

      <!-- Header -->
      <div class="ihs-header">
        <div class="ihs-header-left">
          <span class="ihs-instrument-icon">{{ instrumentIcon }}</span>
          <div>
            <h1 class="ihs-project-name">{{ projectName }}</h1>
            <p class="ihs-instrument-label">{{ instrumentLabel }}</p>
          </div>
        </div>
        <div class="ihs-header-right">
          <div v-if="isDirty" class="ihs-dirty-badge">● Unsaved changes</div>
          <div v-if="isSaving" class="ihs-saving-badge">Saving…</div>
          <div v-if="lastSavedAt && !isSaving" class="ihs-saved-badge">
            Saved {{ relativeTime(lastSavedAt) }}
          </div>
        </div>
      </div>

      <!-- Stage navigator -->
      <div class="ihs-stages">
        <button
          v-for="stage in applicableStages"
          :key="stage.id"
          class="ihs-stage-btn"
          :class="{
            'ihs-stage-btn--active': activeStage === stage.id,
            [`ihs-stage-btn--${stageCompletion(stage.id)}`]: true,
          }"
          @click="activeStage = stage.id"
        >
          <span class="ihs-stage-icon">{{ stage.icon }}</span>
          <span class="ihs-stage-label">{{ stage.label }}</span>
          <span class="ihs-stage-dot" :class="`ihs-dot--${stageCompletion(stage.id)}`" />
        </button>
      </div>

      <!-- Save error -->
      <div v-if="saveError" class="ihs-save-error">
        <span>⚠️ {{ saveError }}</span>
        <button class="ihs-btn-dismiss" @click="dismissSaveError">✕</button>
      </div>

      <!-- Stage panels -->
      <div class="ihs-stage-content">

        <!-- BODY STAGE -->
        <div v-if="activeStage === 'body'" class="ihs-stage-panel">
          <div class="ihs-stage-header">
            <h2>Body</h2>
            <p>Instrument type, body dimensions, and material selection</p>
          </div>

          <!-- Instrument type selector -->
          <div class="ihs-field-group">
            <label class="ihs-label">Instrument type</label>
            <div class="ihs-type-grid">
              <button
                v-for="(meta, type) in INSTRUMENT_LABELS"
                :key="type"
                class="ihs-type-btn"
                :class="{ 'ihs-type-btn--selected': localType === type }"
                @click="localType = type as InstrumentCategory; markDirty()"
              >
                {{ meta.icon }} {{ meta.label }}
              </button>
            </div>
          </div>

          <!-- Blueprint geometry summary (if available) -->
          <div v-if="blueprintGeometry" class="ihs-info-card">
            <div class="ihs-info-card-title">📋 Blueprint detected</div>
            <div class="ihs-info-row" v-if="blueprintGeometry.instrument_classification">
              <span>Classification:</span>
              <span>{{ blueprintGeometry.instrument_classification }}</span>
            </div>
            <div class="ihs-info-row" v-if="blueprintGeometry.body_length_mm">
              <span>Body length:</span>
              <span class="ihs-mono">{{ blueprintGeometry.body_length_mm.toFixed(0) }} mm</span>
            </div>
            <div class="ihs-info-row" v-if="blueprintGeometry.lower_bout_mm">
              <span>Lower bout:</span>
              <span class="ihs-mono">{{ blueprintGeometry.lower_bout_mm.toFixed(0) }} mm</span>
            </div>
            <div class="ihs-info-row">
              <span>Confidence:</span>
              <span class="ihs-mono">{{ (blueprintGeometry.confidence * 100).toFixed(0) }}%</span>
            </div>
          </div>

          <!-- Material selection summary -->
          <div class="ihs-field-group">
            <label class="ihs-label">Materials</label>
            <div class="ihs-material-grid">
              <div v-for="role in MATERIAL_ROLES" :key="role.key" class="ihs-material-row">
                <span class="ihs-material-role">{{ role.label }}</span>
                <span class="ihs-material-value" :class="{ 'ihs-material-value--empty': !localMaterials[role.key] }">
                  {{ localMaterials[role.key] || 'Not selected' }}
                </span>
                <input
                  v-model="localMaterials[role.key]"
                  class="ihs-material-input"
                  :placeholder="`e.g. ${role.example}`"
                  @input="markDirty()"
                />
              </div>
            </div>
            <p class="ihs-hint">Species IDs from the tonewood registry (e.g. spruce_adirondack, rosewood_east_indian)</p>
          </div>

          <div class="ihs-commit-bar">
            <button class="ihs-btn ihs-btn--primary" :disabled="isSaving || !isDirty" @click="handleCommitBody">
              {{ isSaving ? 'Saving…' : 'Apply to Project' }}
            </button>
            <button class="ihs-btn ihs-btn--ghost" @click="resetBodyEdits">Discard changes</button>
          </div>
        </div>

        <!-- NECK STAGE -->
        <div v-if="activeStage === 'neck'" class="ihs-stage-panel">
          <div class="ihs-stage-header">
            <h2>Neck</h2>
            <p>Scale length, fret count, neck angle, profile, and headstock geometry</p>
          </div>

          <div class="ihs-fields-2col">
            <div class="ihs-field">
              <label class="ihs-label">Scale length (mm)</label>
              <input v-model.number="localSpec.scale_length_mm" type="number" step="0.1" min="200" max="900" class="ihs-input ihs-mono" @input="markDirty()" />
              <span class="ihs-field-hint">{{ scaleLengthInches }} inches</span>
            </div>
            <div class="ihs-field">
              <label class="ihs-label">Fret count</label>
              <input v-model.number="localSpec.fret_count" type="number" min="12" max="30" class="ihs-input ihs-mono" @input="markDirty()" />
            </div>
            <div class="ihs-field">
              <label class="ihs-label">String count</label>
              <input v-model.number="localSpec.string_count" type="number" min="4" max="12" class="ihs-input ihs-mono" @input="markDirty()" />
            </div>
            <div class="ihs-field">
              <label class="ihs-label">Nut width (mm)</label>
              <input v-model.number="localSpec.nut_width_mm" type="number" step="0.5" min="20" max="80" class="ihs-input ihs-mono" @input="markDirty()" />
            </div>
            <div class="ihs-field">
              <label class="ihs-label">Heel width (mm)</label>
              <input v-model.number="localSpec.heel_width_mm" type="number" step="0.5" min="30" max="100" class="ihs-input ihs-mono" @input="markDirty()" />
            </div>
            <div class="ihs-field">
              <label class="ihs-label">Neck angle (°)</label>
              <input v-model.number="localSpec.neck_angle_degrees" type="number" step="0.1" min="-5" max="10" class="ihs-input ihs-mono" @input="markDirty()" />
              <span class="ihs-field-hint">0° = flat (Fender), 1–4° = acoustic, 14–17° = angled headstock</span>
            </div>
            <div class="ihs-field">
              <label class="ihs-label">Body join fret</label>
              <input v-model.number="localSpec.body_join_fret" type="number" min="10" max="22" class="ihs-input ihs-mono" @input="markDirty()" />
            </div>
            <div class="ihs-field">
              <label class="ihs-label">Neck joint</label>
              <select v-model="localSpec.neck_joint_type" class="ihs-select" @change="markDirty()">
                <option value="bolt_on">Bolt-on</option>
                <option value="set_neck">Set neck</option>
                <option value="neck_through">Neck-through</option>
                <option value="dovetail">Dovetail</option>
              </select>
            </div>
            <div class="ihs-field">
              <label class="ihs-label">Tremolo / bridge</label>
              <select v-model="localSpec.tremolo_style" class="ihs-select" @change="markDirty()">
                <option value="hardtail">Hardtail</option>
                <option value="vintage_6screw">Vintage 6-screw</option>
                <option value="2point">2-point</option>
                <option value="floyd_rose">Floyd Rose</option>
                <option value="none">None (acoustic)</option>
              </select>
            </div>
          </div>

          <!-- Blueprint scale hint -->
          <div v-if="blueprintGeometry?.scale_length_detected_mm" class="ihs-info-card">
            <div class="ihs-info-card-title">📋 Blueprint detected scale</div>
            <div class="ihs-info-row">
              <span>Detected:</span>
              <span class="ihs-mono">{{ blueprintGeometry.scale_length_detected_mm.toFixed(1) }} mm</span>
            </div>
            <button class="ihs-btn ihs-btn--ghost ihs-btn--sm" @click="applyBlueprintScale">
              Use blueprint scale
            </button>
          </div>

          <div class="ihs-commit-bar">
            <button class="ihs-btn ihs-btn--primary" :disabled="isSaving || !isDirty" @click="handleCommitNeck">
              {{ isSaving ? 'Saving…' : 'Apply to Project' }}
            </button>
            <button class="ihs-btn ihs-btn--ghost" @click="resetNeckEdits">Discard changes</button>
          </div>
        </div>

        <!-- BRIDGE STAGE -->
        <div v-if="activeStage === 'bridge'" class="ihs-stage-panel">
          <div class="ihs-stage-header">
            <h2>Bridge</h2>
            <p>Bridge Lab is the authoritative editor for bridge geometry.</p>
          </div>
          <div class="ihs-bridge-summary">
            <div v-if="bridgeState" class="ihs-info-card">
              <div class="ihs-info-card-title">Current bridge state</div>
              <div class="ihs-info-row">
                <span>Saddle line:</span>
                <span class="ihs-mono">{{ bridgeState.saddle_line_from_nut_mm?.toFixed(1) ?? 'Not set' }} mm</span>
              </div>
              <div class="ihs-info-row">
                <span>String spread:</span>
                <span class="ihs-mono">{{ bridgeState.string_spread_mm }} mm</span>
              </div>
              <div class="ihs-info-row">
                <span>Saddle projection:</span>
                <span class="ihs-mono">{{ bridgeState.saddle_projection_mm }} mm</span>
              </div>
              <div class="ihs-info-row">
                <span>Last committed:</span>
                <span class="ihs-mono">{{ bridgeState.last_committed_at ? relativeTime(bridgeState.last_committed_at) : 'Never' }}</span>
              </div>
            </div>
            <div v-else class="ihs-empty-stage">
              Bridge geometry has not been set yet.
            </div>
            <div class="ihs-bridge-cta">
              <p>Edit bridge geometry in <strong>Bridge Lab</strong> — the bounded workspace for bridge design.</p>
              <a href="/lab/bridge" class="ihs-btn ihs-btn--primary">Open Bridge Lab →</a>
            </div>
          </div>
        </div>

        <!-- BRACING STAGE -->
        <div v-if="activeStage === 'bracing'" class="ihs-stage-panel">
          <div class="ihs-stage-header">
            <h2>Bracing</h2>
            <p>Top brace layout and structural design</p>
          </div>
          <div class="ihs-empty-stage">
            Bracing workspace coming in a future phase.
            Use <a href="/art-studio/bracing">Art Studio Bracing</a> in the meantime.
          </div>
        </div>

        <!-- SETUP STAGE -->
        <div v-if="activeStage === 'setup'" class="ihs-stage-panel">
          <div class="ihs-stage-header">
            <h2>Setup</h2>
            <p>Action, intonation, and final setup parameters</p>
          </div>
          <div class="ihs-empty-stage">
            Setup stage coming in a future phase.
            Use <a href="/calculators">Utilities</a> for individual setup calculations.
          </div>
        </div>

        <!-- CNC PREP STAGE -->
        <div v-if="activeStage === 'cnc-prep'" class="ihs-stage-panel">
          <div class="ihs-stage-header">
            <h2>CNC Prep</h2>
            <p>Review design completeness and approve for production</p>
          </div>

          <div class="ihs-readiness">
            <div class="ihs-readiness-item" :class="spec ? 'ihs-ready' : 'ihs-not-ready'">
              {{ spec ? '✅' : '❌' }} Core spec (scale, frets, neck angle)
            </div>
            <div class="ihs-readiness-item" :class="bridgeState?.saddle_line_from_nut_mm ? 'ihs-ready' : 'ihs-not-ready'">
              {{ bridgeState?.saddle_line_from_nut_mm ? '✅' : '⚠️' }} Bridge geometry
            </div>
            <div class="ihs-readiness-item" :class="materialSelection?.top ? 'ihs-ready' : 'ihs-warn'">
              {{ materialSelection?.top ? '✅' : '⚠️' }} Materials selected
            </div>
          </div>

          <div v-if="isCamReady" class="ihs-commit-bar">
            <a href="/cam/fret-slots" class="ihs-btn ihs-btn--primary">Open Fret Slotting →</a>
            <a href="/cam/contour" class="ihs-btn ihs-btn--secondary">Open Body Contour →</a>
          </div>
          <div v-else class="ihs-info-card ihs-info-card--warn">
            Complete core spec before proceeding to CNC.
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useInstrumentProject } from './shared-state/useInstrumentProject'
import {
  getApplicableStages,
  getStageCompletion,
  getInstrumentIcon,
  getInstrumentLabel,
  INSTRUMENT_LABELS,
  type HubStageId,
} from './shared-state/project-types'
import type {
  InstrumentSpec,
  MaterialSelection,
  InstrumentCategory,
} from '@/api/projects'

// ---------------------------------------------------------------------------
// Props & Emits
// ---------------------------------------------------------------------------

const props = defineProps<{
  projectId: string
}>()

const emit = defineEmits<{
  (e: 'project-updated'): void
}>()

// ---------------------------------------------------------------------------
// Project state
// ---------------------------------------------------------------------------

const {
  isLoading, isLoaded, isSaving, loadError, saveError, isDirty,
  lastSavedAt, projectName, isCamReady,
  instrumentType, spec, blueprintGeometry, bridgeState,
  materialSelection,
  loadProject, commitSpec, commitInstrumentType, commitMaterialSelection, markDirty,
} = useInstrumentProject()

const activeStage = ref<HubStageId>('body')

// ---------------------------------------------------------------------------
// Local edit buffers (never auto-commit)
// ---------------------------------------------------------------------------

const localType = ref<InstrumentCategory>('electric_guitar')
const localSpec = ref<Partial<InstrumentSpec>>({})
const localMaterials = ref<Record<string, string>>({})

// Sync local buffers from project state when loaded
watch(isLoaded, (loaded) => {
  if (loaded) syncFromProject()
}, { immediate: true })

watch(instrumentType, (t) => { if (t) localType.value = t })
watch(spec, (s) => { if (s) syncSpecBuffer(s) })
watch(materialSelection, (m) => { if (m) syncMaterialsBuffer(m) })

function syncFromProject() {
  if (instrumentType.value) localType.value = instrumentType.value
  if (spec.value) syncSpecBuffer(spec.value)
  if (materialSelection.value) syncMaterialsBuffer(materialSelection.value)
}

function syncSpecBuffer(s: InstrumentSpec) {
  localSpec.value = { ...s }
}

function syncMaterialsBuffer(m: MaterialSelection) {
  localMaterials.value = {
    top: m.top ?? '',
    back_sides: m.back_sides ?? '',
    neck: m.neck ?? '',
    fretboard: m.fretboard ?? '',
    bridge: m.bridge ?? '',
    brace_stock: m.brace_stock ?? '',
  }
}

// ---------------------------------------------------------------------------
// Computed display
// ---------------------------------------------------------------------------

const instrumentIcon = computed(() => getInstrumentIcon(instrumentType.value))
const instrumentLabel = computed(() => getInstrumentLabel(instrumentType.value))
const applicableStages = computed(() => getApplicableStages(instrumentType.value))

function stageCompletion(id: HubStageId) {
  // Rebuild full InstrumentProjectData shape for heuristic check
  return getStageCompletion(id, isLoaded.value ? {
    schema_version: '1.0',
    instrument_type: instrumentType.value ?? 'custom',
    spec: spec.value ?? undefined,
    blueprint_geometry: blueprintGeometry.value ?? undefined,
    bridge_state: bridgeState.value ?? undefined,
    material_selection: materialSelection.value ?? undefined,
    analyzer_observations: [],
  } as any : null)
}

const scaleLengthInches = computed(() => {
  const mm = localSpec.value.scale_length_mm
  if (!mm) return ''
  return `${(mm / 25.4).toFixed(2)}"`
})

// ---------------------------------------------------------------------------
// Material role definitions
// ---------------------------------------------------------------------------

const MATERIAL_ROLES = [
  { key: 'top',        label: 'Top / soundboard', example: 'spruce_adirondack' },
  { key: 'back_sides', label: 'Back & sides',      example: 'rosewood_east_indian' },
  { key: 'neck',       label: 'Neck',              example: 'mahogany_honduran' },
  { key: 'fretboard',  label: 'Fretboard',         example: 'ebony_african' },
  { key: 'bridge',     label: 'Bridge',            example: 'rosewood_east_indian' },
  { key: 'brace_stock',label: 'Brace stock',       example: 'spruce_sitka' },
]

// ---------------------------------------------------------------------------
// Commit handlers (explicit user action only)
// ---------------------------------------------------------------------------

async function handleCommitBody() {
  // Commit instrument type + material selection
  let ok = true
  if (localType.value !== instrumentType.value) {
    ok = await commitInstrumentType(localType.value, !spec.value)
  }
  if (ok) {
    const mat: MaterialSelection = {
      top: localMaterials.value.top || null,
      back_sides: localMaterials.value.back_sides || null,
      neck: localMaterials.value.neck || null,
      fretboard: localMaterials.value.fretboard || null,
      bridge: localMaterials.value.bridge || null,
      brace_stock: localMaterials.value.brace_stock || null,
    }
    ok = await commitMaterialSelection(mat)
  }
  if (ok) emit('project-updated')
}

async function handleCommitNeck() {
  if (!localSpec.value.scale_length_mm) return
  const fullSpec: InstrumentSpec = {
    scale_length_mm: localSpec.value.scale_length_mm,
    fret_count: localSpec.value.fret_count ?? 22,
    string_count: localSpec.value.string_count ?? 6,
    nut_width_mm: localSpec.value.nut_width_mm ?? 42,
    heel_width_mm: localSpec.value.heel_width_mm ?? 56,
    neck_angle_degrees: localSpec.value.neck_angle_degrees ?? 0,
    neck_joint_type: localSpec.value.neck_joint_type ?? 'bolt_on',
    body_join_fret: localSpec.value.body_join_fret ?? 14,
    tremolo_style: localSpec.value.tremolo_style ?? 'hardtail',
  }
  const ok = await commitSpec(fullSpec, instrumentType.value ?? undefined)
  if (ok) emit('project-updated')
}

function resetBodyEdits() {
  if (instrumentType.value) localType.value = instrumentType.value
  if (materialSelection.value) syncMaterialsBuffer(materialSelection.value)
}

function resetNeckEdits() {
  if (spec.value) syncSpecBuffer(spec.value)
}

function applyBlueprintScale() {
  if (blueprintGeometry.value?.scale_length_detected_mm) {
    localSpec.value = {
      ...localSpec.value,
      scale_length_mm: blueprintGeometry.value.scale_length_detected_mm,
    }
    markDirty()
    activeStage.value = 'neck'
  }
}

function dismissSaveError() {
  // saveError is readonly — clear via a no-op commit attempt will reset it
  // The store resets saveError on next successful commit
}

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

function retry() {
  loadProject(props.projectId)
}

// ---------------------------------------------------------------------------
// Lifecycle
// ---------------------------------------------------------------------------

onMounted(() => {
  loadProject(props.projectId)
})

watch(() => props.projectId, (id) => {
  if (id) loadProject(id)
})
</script>

<style scoped>
.ihs { min-height: 100%; font-family: var(--font-sans, system-ui); }

/* Loading / error / empty */
.ihs-loading, .ihs-error, .ihs-empty { display: flex; align-items: center; justify-content: center; gap: 1rem; padding: 4rem 2rem; color: var(--color-text-secondary); }
.ihs-spinner { width: 1.5rem; height: 1.5rem; border: 2px solid var(--color-border-secondary); border-top-color: #667eea; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.ihs-error { flex-direction: column; align-items: flex-start; }
.ihs-error-icon { font-size: 2rem; }
.ihs-empty { flex-direction: column; }
.ihs-empty-icon { font-size: 4rem; }
.ihs-empty-stage { padding: 2rem; color: var(--color-text-tertiary); font-style: italic; }

/* Header */
.ihs-header { display: flex; justify-content: space-between; align-items: center; padding: 1.25rem 1.5rem; border-bottom: 0.5px solid var(--color-border-tertiary); }
.ihs-header-left { display: flex; align-items: center; gap: 0.75rem; }
.ihs-instrument-icon { font-size: 2rem; }
.ihs-project-name { margin: 0; font-size: 1.25rem; font-weight: 600; }
.ihs-instrument-label { margin: 0; font-size: 0.8rem; color: var(--color-text-secondary); }
.ihs-header-right { display: flex; align-items: center; gap: 0.5rem; font-size: 0.75rem; }
.ihs-dirty-badge { padding: 0.2rem 0.6rem; background: #FFF3CD; color: #856404; border-radius: 1rem; }
.ihs-saving-badge { padding: 0.2rem 0.6rem; background: #E3F2FD; color: #0D47A1; border-radius: 1rem; }
.ihs-saved-badge { color: var(--color-text-tertiary); }

/* Stage navigator */
.ihs-stages { display: flex; gap: 0; border-bottom: 0.5px solid var(--color-border-tertiary); overflow-x: auto; }
.ihs-stage-btn { display: flex; align-items: center; gap: 0.4rem; padding: 0.7rem 1.1rem; border: none; background: transparent; cursor: pointer; font-family: inherit; font-size: 0.85rem; color: var(--color-text-secondary); border-bottom: 2px solid transparent; white-space: nowrap; transition: all 0.15s; }
.ihs-stage-btn--active { color: var(--color-text-primary); border-bottom-color: #667eea; font-weight: 500; }
.ihs-stage-btn:hover:not(.ihs-stage-btn--active) { background: var(--color-background-secondary); }
.ihs-stage-icon { font-size: 1rem; }
.ihs-stage-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--color-border-secondary); }
.ihs-dot--complete { background: #1D9E75; }
.ihs-dot--partial { background: #BA7517; }
.ihs-dot--empty { background: var(--color-border-tertiary); }

/* Save error */
.ihs-save-error { display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 1.5rem; background: var(--color-background-danger); font-size: 0.85rem; color: var(--color-text-danger); }
.ihs-btn-dismiss { background: none; border: none; cursor: pointer; font-size: 0.9rem; }

/* Stage panels */
.ihs-stage-content { padding: 1.5rem; }
.ihs-stage-panel { display: flex; flex-direction: column; gap: 1.25rem; max-width: 760px; }
.ihs-stage-header h2 { margin: 0 0 0.25rem; font-size: 1.1rem; font-weight: 600; }
.ihs-stage-header p { margin: 0; font-size: 0.85rem; color: var(--color-text-secondary); }

/* Fields */
.ihs-field-group { display: flex; flex-direction: column; gap: 0.5rem; }
.ihs-label { font-size: 0.8rem; font-weight: 500; color: var(--color-text-secondary); }
.ihs-fields-2col { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem 1.25rem; }
.ihs-field { display: flex; flex-direction: column; gap: 0.25rem; }
.ihs-field-hint { font-size: 0.72rem; color: var(--color-text-tertiary); font-family: var(--font-mono, monospace); }
.ihs-input, .ihs-select { padding: 0.4rem 0.6rem; border: 0.5px solid var(--color-border-secondary); border-radius: 0.35rem; background: var(--color-background-primary); font-family: inherit; font-size: 0.875rem; width: 100%; }
.ihs-mono { font-family: var(--font-mono, monospace); }
.ihs-hint { font-size: 0.72rem; color: var(--color-text-tertiary); margin: 0; }

/* Instrument type grid */
.ihs-type-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 0.5rem; }
.ihs-type-btn { padding: 0.5rem 0.75rem; border: 0.5px solid var(--color-border-secondary); border-radius: 0.5rem; background: var(--color-background-secondary); cursor: pointer; font-size: 0.8rem; font-family: inherit; text-align: left; transition: all 0.15s; }
.ihs-type-btn--selected { background: #EEF2FF; border-color: #667eea; color: #4338CA; font-weight: 500; }

/* Material grid */
.ihs-material-grid { display: flex; flex-direction: column; gap: 0.5rem; }
.ihs-material-row { display: grid; grid-template-columns: 120px 1fr 200px; align-items: center; gap: 0.75rem; }
.ihs-material-role { font-size: 0.8rem; font-weight: 500; }
.ihs-material-value { font-size: 0.8rem; font-family: var(--font-mono, monospace); color: #1D9E75; }
.ihs-material-value--empty { color: var(--color-text-tertiary); font-style: italic; }
.ihs-material-input { padding: 0.3rem 0.5rem; border: 0.5px solid var(--color-border-tertiary); border-radius: 0.35rem; font-family: var(--font-mono, monospace); font-size: 0.75rem; }

/* Info cards */
.ihs-info-card { background: var(--color-background-secondary); border-radius: 0.5rem; padding: 0.75rem 1rem; }
.ihs-info-card--warn { background: var(--color-background-warning); }
.ihs-info-card-title { font-size: 0.75rem; font-weight: 600; color: var(--color-text-secondary); margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.04em; }
.ihs-info-row { display: flex; justify-content: space-between; font-size: 0.82rem; padding: 0.15rem 0; }

/* Bridge stage */
.ihs-bridge-summary { display: flex; flex-direction: column; gap: 1rem; }
.ihs-bridge-cta { padding: 1rem; background: var(--color-background-secondary); border-radius: 0.5rem; }
.ihs-bridge-cta p { margin: 0 0 0.75rem; font-size: 0.85rem; }

/* Readiness */
.ihs-readiness { display: flex; flex-direction: column; gap: 0.5rem; }
.ihs-readiness-item { font-size: 0.9rem; }
.ihs-ready { color: #1D9E75; }
.ihs-not-ready { color: #D85A30; }
.ihs-warn { color: #BA7517; }

/* Commit bar */
.ihs-commit-bar { display: flex; gap: 0.75rem; align-items: center; padding-top: 0.5rem; border-top: 0.5px solid var(--color-border-tertiary); }
.ihs-btn { padding: 0.45rem 1.1rem; border-radius: 0.5rem; border: none; font-family: inherit; font-size: 0.875rem; font-weight: 500; cursor: pointer; text-decoration: none; display: inline-flex; align-items: center; transition: background 0.15s; }
.ihs-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.ihs-btn--primary { background: linear-gradient(135deg, #667eea, #764ba2); color: white; }
.ihs-btn--primary:hover:not(:disabled) { filter: brightness(1.1); }
.ihs-btn--secondary { background: #1D9E75; color: white; }
.ihs-btn--secondary:hover { background: #17846A; }
.ihs-btn--ghost { background: var(--color-background-secondary); color: var(--color-text-primary); border: 0.5px solid var(--color-border-secondary); }
.ihs-btn--sm { font-size: 0.75rem; padding: 0.25rem 0.6rem; }
</style>
