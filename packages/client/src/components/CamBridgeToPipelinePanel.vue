<!--
Luthier's Tool Box - CNC Guitar Lutherie CAD/CAM Toolbox
CamBridgeToPipelinePanel - Save BridgeLab configurations as pipeline presets

Part of Phase 25.0: Pipeline Preset Integration
Repository: HanzoRazer/luthiers-toolbox
Created: January 2025

Features:
- Save current BridgeLab config as named preset
- Save & Run workflow (save + immediate execution)
- Spec builder from machine-aware parameters
- JSON preview of pipeline operations
- Post-processor and machine selection
-->

<script setup lang="ts">
import { api } from '@/services/apiBase';
import { ref, computed } from 'vue'

const props = defineProps<{
  machine: any
  adaptiveUnits: string
  toolD: number
  stepoverPct: number
  stepdown: number
  feedXY: number
  geometryLayer: string
  selectedPostId: string | null
}>()

const emit = defineEmits<{
  (e: 'preset-saved', id: string): void
  (e: 'preset-run-result', result: any): void
}>()

const name = ref('')
const postIdLocal = ref(props.selectedPostId || '')
const machineIdLocal = ref(props.machine?.id || '')
const saving = ref(false)
const error = ref('')
const success = ref('')
const successId = ref('')
const lastRunId = ref('')

const spec = computed(() => ({
  ops: [
    { step: 'dxf_preflight', layer: props.geometryLayer || 'geometry' },
    { step: 'adaptive_plan', tool_d: props.toolD, stepover: props.stepoverPct / 100, stepdown: props.stepdown },
    { step: 'adaptive_plan_run', feed_xy: props.feedXY },
    { step: 'export_post', post_id: postIdLocal.value },
    { step: 'simulate_gcode' }
  ],
  tool_d: props.toolD,
  units: props.adaptiveUnits,
  geometry_layer: props.geometryLayer || 'geometry',
  machine_id: machineIdLocal.value,
  post_id: postIdLocal.value
}))

const prettySpec = computed(() => JSON.stringify(spec.value, null, 2))

async function savePreset(runAfterSave = false) {
  if (!name.value.trim()) {
    error.value = 'Preset name is required'
    return
  }

  saving.value = true
  error.value = ''
  success.value = ''
  successId.value = ''
  lastRunId.value = ''

  try {
    const response = await api('/api/cam/pipeline/presets', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: name.value.trim(),
        spec: spec.value
      })
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }

    const result = await response.json()
    const presetId = result.id || result.preset_id
    successId.value = presetId
    success.value = `Preset saved: ${presetId}`
    emit('preset-saved', presetId)

    if (runAfterSave) {
      await runPreset(presetId)
    }
  } catch (err: any) {
    error.value = `Failed to save preset: ${err.message}`
  } finally {
    saving.value = false
  }
}

async function runPreset(presetId: string) {
  saving.value = true
  error.value = ''

  try {
    const response = await api(`/api/cam/pipeline/presets/${presetId}/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }

    const result = await response.json()
    lastRunId.value = result.run_id || 'completed'
    success.value += ` | Run completed: ${lastRunId.value}`
    emit('preset-run-result', result)
  } catch (err: any) {
    error.value = `Failed to run preset: ${err.message}`
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="cam-bridge-to-pipeline-panel">
    <h3>Save as Pipeline Preset</h3>
    
    <div class="form-group">
      <label for="preset-name">Preset Name:</label>
      <input
        id="preset-name"
        v-model="name"
        type="text"
        placeholder="e.g., Bridge Pocket 6mm"
        :disabled="saving"
      >
    </div>

    <div class="form-group">
      <label for="post-id">Post Processor:</label>
      <input
        id="post-id"
        v-model="postIdLocal"
        type="text"
        placeholder="e.g., GRBL"
        :disabled="saving"
      >
    </div>

    <div class="form-group">
      <label for="machine-id">Machine ID:</label>
      <input
        id="machine-id"
        v-model="machineIdLocal"
        type="text"
        placeholder="e.g., shapeoko_pro"
        :disabled="saving"
      >
    </div>

    <div class="button-group">
      <button
        :disabled="saving || !name.trim()"
        @click="savePreset(false)"
      >
        {{ saving ? 'Saving...' : 'Save preset' }}
      </button>
      <button
        :disabled="saving || !name.trim()"
        class="primary"
        @click="savePreset(true)"
      >
        {{ saving ? 'Saving...' : 'Save & Run' }}
      </button>
    </div>

    <div
      v-if="error"
      class="error-message"
    >
      {{ error }}
    </div>
    <div
      v-if="success"
      class="success-message"
    >
      {{ success }}
    </div>

    <details class="spec-preview">
      <summary>Spec Preview</summary>
      <pre>{{ prettySpec }}</pre>
    </details>
  </div>
</template>

<style scoped>
.cam-bridge-to-pipeline-panel {
  padding: 1rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: #f9f9f9;
  margin-top: 1rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.25rem;
  font-weight: 600;
}

.form-group input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.button-group {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

button {
  padding: 0.5rem 1rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: white;
  cursor: pointer;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

button.primary {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

button.primary:hover:not(:disabled) {
  background: #0056b3;
}

.error-message {
  padding: 0.5rem;
  background: #fee;
  border: 1px solid #fcc;
  border-radius: 4px;
  color: #c00;
  margin-bottom: 1rem;
}

.success-message {
  padding: 0.5rem;
  background: #efe;
  border: 1px solid #cfc;
  border-radius: 4px;
  color: #060;
  margin-bottom: 1rem;
}

.spec-preview {
  margin-top: 1rem;
}

.spec-preview pre {
  background: #fff;
  padding: 1rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 0.85rem;
}
</style>
