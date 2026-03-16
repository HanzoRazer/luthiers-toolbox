<!--
  BlueprintSavePanel.vue (BLUE-003/004)

  Stage 5 of Blueprint Lab — "Save to Project"

  This panel appears after the 4-phase blueprint pipeline completes.
  It shows the builder what was detected and lets them confirm saving
  the geometry into their active Instrument Project.

  Wiring into BlueprintLab.vue:
    1. Import this component
    2. Import useBlueprintProjectWrite
    3. Show this panel when currentPhase >= 4 (pipeline complete)
    4. Pass the active projectId from useInstrumentProject

  Provenance displayed:
    - source (photo / dxf / manual)
    - confidence from Phase 1 AI
    - what was detected (classification, scale, centerline, body dimensions)
    - notes from the pipeline

  After save:
    - Shows success summary
    - Blueprint geometry is persisted in Project.data.blueprint_geometry
    - Builder can continue to Instrument Hub

  See docs/PLATFORM_ARCHITECTURE.md — Layer 2 / Blueprint.
-->

<template>
  <div class="bsp">
    <!-- Header -->
    <div class="bsp-header">
      <div class="bsp-stage-badge">5</div>
      <div>
        <h2 class="bsp-title">Save to Project</h2>
        <p class="bsp-subtitle">Commit blueprint geometry into your instrument project</p>
      </div>
    </div>

    <!-- No project warning -->
    <div v-if="!projectId" class="bsp-warning">
      <span class="bsp-warning-icon">⚠️</span>
      <div>
        <strong>No active project.</strong>
        <p>Open or create a project to save blueprint geometry. Blueprint results will be lost when you leave this page.</p>
      </div>
    </div>

    <!-- Detected geometry summary -->
    <div v-else class="bsp-summary">
      <div class="bsp-summary-title">What was detected</div>
      <div class="bsp-summary-grid">
        <div class="bsp-item">
          <span class="bsp-item-label">Instrument</span>
          <span class="bsp-item-value" :class="instrumentClass">
            {{ instrumentClassificationLabel }}
          </span>
        </div>
        <div class="bsp-item">
          <span class="bsp-item-label">Confidence</span>
          <span class="bsp-item-value" :class="confidenceClass">
            {{ confidenceLabel }}
          </span>
        </div>
        <div class="bsp-item" v-if="hasScaleLength">
          <span class="bsp-item-label">Scale length</span>
          <span class="bsp-item-value bsp-mono">{{ scaleLengthLabel }}</span>
        </div>
        <div class="bsp-item" v-if="hasBodyDims">
          <span class="bsp-item-label">Body size</span>
          <span class="bsp-item-value bsp-mono">{{ bodyDimsLabel }}</span>
        </div>
        <div class="bsp-item">
          <span class="bsp-item-label">Centerline</span>
          <span class="bsp-item-value" :class="centerlineClass">
            {{ centerlineLabel }}
          </span>
        </div>
        <div class="bsp-item">
          <span class="bsp-item-label">Source</span>
          <span class="bsp-item-value bsp-mono">{{ sourceLabel }}</span>
        </div>
      </div>

      <!-- Pipeline notes -->
      <div v-if="pipelineNotes.length" class="bsp-notes">
        <div class="bsp-notes-title">Pipeline notes</div>
        <ul>
          <li v-for="(note, i) in pipelineNotes" :key="i">{{ note }}</li>
        </ul>
      </div>

      <!-- Instrument type override -->
      <div class="bsp-override">
        <label class="bsp-label">Instrument type</label>
        <select v-model="instrumentTypeOverride" class="bsp-select">
          <option value="">Use AI detection ({{ instrumentClassificationLabel }})</option>
          <option value="acoustic_guitar">Acoustic Guitar</option>
          <option value="electric_guitar">Electric Guitar</option>
          <option value="bass">Bass Guitar</option>
          <option value="classical">Classical Guitar</option>
          <option value="archtop">Archtop Guitar</option>
          <option value="violin">Violin / Viola</option>
          <option value="mandolin">Mandolin</option>
          <option value="ukulele">Ukulele</option>
          <option value="banjo">Banjo</option>
          <option value="custom">Custom</option>
        </select>
        <p class="bsp-hint">Correct if AI classification was wrong.</p>
      </div>
    </div>

    <!-- Already saved state -->
    <div v-if="wasSaved && lastResult" class="bsp-success">
      <div class="bsp-success-icon">✅</div>
      <div>
        <strong>Blueprint geometry saved.</strong>
        <p>{{ lastResult.message }}</p>
        <p class="bsp-success-detail">
          Instrument: {{ lastResult.instrument_classification || 'Unknown' }} ·
          Confidence: {{ (lastResult.confidence * 100).toFixed(0) }}% ·
          Centerline: {{ lastResult.centerline_detected ? 'detected' : 'estimated' }}
        </p>
      </div>
    </div>

    <!-- Error state -->
    <div v-if="saveError" class="bsp-error">
      <span class="bsp-error-icon">❌</span>
      <div>
        <strong>Save failed.</strong>
        <p>{{ saveError }}</p>
      </div>
    </div>

    <!-- Actions -->
    <div class="bsp-actions">
      <button
        v-if="projectId && !wasSaved"
        class="bsp-btn bsp-btn--primary"
        :disabled="isSaving"
        @click="handleSave"
      >
        <span v-if="isSaving">Saving…</span>
        <span v-else>Save Blueprint to Project</span>
      </button>

      <button
        v-if="wasSaved"
        class="bsp-btn bsp-btn--secondary"
        @click="$emit('go-to-hub')"
      >
        Open Instrument Hub →
      </button>

      <button
        v-if="wasSaved"
        class="bsp-btn bsp-btn--ghost"
        @click="clearSaveState"
      >
        Save again
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useBlueprintProjectWrite, type BlueprintPipelineOutputs } from './composables/useBlueprintProjectWrite'

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

const props = defineProps<{
  /** Active project UUID — null if no project is open */
  projectId: string | null
  /** Assembled pipeline outputs from useBlueprintWorkflow */
  pipelineOutputs: BlueprintPipelineOutputs
  /** Notes from the pipeline phases */
  pipelineNotes?: string[]
  /** Detected body dimensions summary */
  bodyLengthMm?: number | null
  lowerBoutMm?: number | null
  scaleLengthMm?: number | null
  /** Phase 1 classification */
  instrumentClassification?: string | null
  /** Phase 1 confidence 0-1 */
  confidence?: number
  /** Source: 'photo' | 'dxf' | 'manual' */
  source?: string
  /** Whether centerline was detected */
  centerlineDetected?: boolean
}>()

const emit = defineEmits<{
  (e: 'saved', result: { projectId: string; instrumentClassification: string | null }): void
  (e: 'go-to-hub'): void
}>()

// ---------------------------------------------------------------------------
// Local state
// ---------------------------------------------------------------------------

const instrumentTypeOverride = ref<string>('')

const {
  isSaving, saveError, lastSaveResult, wasSaved,
  saveToProject, clearSaveState,
} = useBlueprintProjectWrite()

const lastResult = lastSaveResult

// ---------------------------------------------------------------------------
// Computed display values
// ---------------------------------------------------------------------------

const instrumentClassificationLabel = computed(() => {
  const raw = props.instrumentClassification
  if (!raw) return 'Not detected'
  const labels: Record<string, string> = {
    acoustic_guitar: 'Acoustic Guitar', electric_guitar: 'Electric Guitar',
    bass: 'Bass Guitar', classical: 'Classical', archtop: 'Archtop',
    violin: 'Violin', mandolin: 'Mandolin', ukulele: 'Ukulele',
    banjo: 'Banjo', custom: 'Custom',
  }
  return labels[raw] ?? raw
})

const instrumentClass = computed(() =>
  props.instrumentClassification ? 'bsp-item-value--ok' : 'bsp-item-value--warn'
)

const confidenceLabel = computed(() => {
  const c = props.confidence ?? 0
  if (c >= 0.8) return `High (${(c * 100).toFixed(0)}%)`
  if (c >= 0.5) return `Medium (${(c * 100).toFixed(0)}%)`
  if (c > 0) return `Low (${(c * 100).toFixed(0)}%)`
  return 'Unknown'
})

const confidenceClass = computed(() => {
  const c = props.confidence ?? 0
  if (c >= 0.8) return 'bsp-item-value--ok'
  if (c >= 0.5) return 'bsp-item-value--warn'
  return 'bsp-item-value--bad'
})

const hasScaleLength = computed(() => !!props.scaleLengthMm)
const scaleLengthLabel = computed(() =>
  props.scaleLengthMm ? `${props.scaleLengthMm.toFixed(1)} mm` : '—'
)

const hasBodyDims = computed(() => !!(props.bodyLengthMm || props.lowerBoutMm))
const bodyDimsLabel = computed(() => {
  const parts: string[] = []
  if (props.bodyLengthMm) parts.push(`L: ${props.bodyLengthMm.toFixed(0)}mm`)
  if (props.lowerBoutMm) parts.push(`W: ${props.lowerBoutMm.toFixed(0)}mm`)
  return parts.join(' · ') || '—'
})

const centerlineLabel = computed(() =>
  props.centerlineDetected ? 'Detected' : 'Estimated'
)
const centerlineClass = computed(() =>
  props.centerlineDetected ? 'bsp-item-value--ok' : 'bsp-item-value--warn'
)

const sourceLabel = computed(() => {
  const map: Record<string, string> = { photo: 'Photo / scan', dxf: 'DXF import', manual: 'Manual entry' }
  return map[props.source ?? 'photo'] ?? 'Photo / scan'
})

const pipelineNotes = computed(() => props.pipelineNotes ?? [])

// ---------------------------------------------------------------------------
// Actions
// ---------------------------------------------------------------------------

async function handleSave() {
  if (!props.projectId) return
  const result = await saveToProject(
    props.projectId,
    props.pipelineOutputs,
    instrumentTypeOverride.value || undefined,
  )
  if (result?.success) {
    emit('saved', {
      projectId: props.projectId,
      instrumentClassification: result.instrument_classification,
    })
  }
}
</script>

<style scoped>
.bsp { font-family: var(--font-sans, system-ui); padding: 1.5rem; display: flex; flex-direction: column; gap: 1.25rem; }
.bsp-header { display: flex; align-items: flex-start; gap: 1rem; }
.bsp-stage-badge { flex-shrink: 0; width: 2.5rem; height: 2.5rem; border-radius: 50%; background: linear-gradient(135deg, #667eea, #764ba2); color: white; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1.25rem; }
.bsp-title { margin: 0 0 0.25rem; font-size: 1.4rem; font-weight: 600; }
.bsp-subtitle { margin: 0; font-size: 0.9rem; color: var(--color-text-secondary); }
.bsp-warning { display: flex; gap: 0.75rem; align-items: flex-start; padding: 1rem; background: var(--color-background-warning); border-radius: 0.5rem; }
.bsp-warning-icon { font-size: 1.5rem; }
.bsp-summary { background: var(--color-background-secondary); border-radius: 0.5rem; padding: 1rem 1.25rem; }
.bsp-summary-title { font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--color-text-tertiary); margin-bottom: 0.75rem; }
.bsp-summary-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 0.5rem 1.5rem; margin-bottom: 1rem; }
.bsp-item { display: flex; flex-direction: column; gap: 0.15rem; }
.bsp-item-label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--color-text-tertiary); }
.bsp-item-value { font-size: 0.9rem; font-weight: 500; }
.bsp-item-value--ok { color: #1D9E75; }
.bsp-item-value--warn { color: #BA7517; }
.bsp-item-value--bad { color: #D85A30; }
.bsp-mono { font-family: var(--font-mono, monospace); }
.bsp-notes { margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid var(--color-border-tertiary); font-size: 0.8rem; color: var(--color-text-secondary); }
.bsp-notes-title { font-weight: 500; margin-bottom: 0.25rem; }
.bsp-notes ul { margin: 0; padding-left: 1.25rem; }
.bsp-notes li { margin-bottom: 0.15rem; }
.bsp-override { display: flex; flex-direction: column; gap: 0.25rem; padding-top: 1rem; border-top: 1px solid var(--color-border-tertiary); }
.bsp-label { font-size: 0.8rem; font-weight: 500; }
.bsp-select { padding: 0.35rem 0.5rem; border: 0.5px solid var(--color-border-secondary); border-radius: 0.35rem; background: var(--color-background-primary); font-family: inherit; font-size: 0.875rem; width: 100%; max-width: 360px; }
.bsp-hint { margin: 0.15rem 0 0; font-size: 0.75rem; color: var(--color-text-tertiary); }
.bsp-success { display: flex; gap: 0.75rem; align-items: flex-start; padding: 1rem; background: #E1F5EE; border-radius: 0.5rem; }
.bsp-success-icon { font-size: 1.25rem; }
.bsp-success-detail { font-size: 0.8rem; color: #085041; margin: 0.25rem 0 0; font-family: var(--font-mono, monospace); }
.bsp-error { display: flex; gap: 0.75rem; padding: 1rem; background: var(--color-background-danger); border-radius: 0.5rem; }
.bsp-error-icon { font-size: 1.25rem; }
.bsp-actions { display: flex; gap: 0.75rem; flex-wrap: wrap; }
.bsp-btn { padding: 0.5rem 1.25rem; border-radius: 0.5rem; border: none; font-family: inherit; font-size: 0.9rem; font-weight: 500; cursor: pointer; transition: background 0.15s; }
.bsp-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.bsp-btn--primary { background: linear-gradient(135deg, #667eea, #764ba2); color: white; }
.bsp-btn--primary:hover:not(:disabled) { filter: brightness(1.1); }
.bsp-btn--secondary { background: #1D9E75; color: white; }
.bsp-btn--secondary:hover { background: #17846A; }
.bsp-btn--ghost { background: var(--color-background-secondary); color: var(--color-text-primary); border: 0.5px solid var(--color-border-secondary); }
.bsp-btn--ghost:hover { background: var(--color-background-tertiary); }
</style>
