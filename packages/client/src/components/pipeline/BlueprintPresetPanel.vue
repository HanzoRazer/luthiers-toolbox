<template>
  <div
    class="stage-panel blueprint-preset"
  >
    <h2>Blueprint to Adaptive Preset (Phase 27.0)</h2>
    <p class="stage-description">
      Upload a blueprint image and run one-click Blueprint to Adaptive pipeline directly.
      Generate toolpath preview and send to Art Studio for refinement.
    </p>

    <div class="preset-grid">
      <!-- File Upload -->
      <div>
        <h3 class="section-title">Blueprint Image</h3>
        <input
          type="file"
          accept="image/*"
          class="file-input"
          @change="onFileChange"
        >
        <div
          v-if="file"
          class="file-selected"
        >
          {{ file.name }}
        </div>
      </div>

      <!-- Tool Configuration (extracted child component) -->
      <ToolConfigGrid
        :config="config"
        @update:config="emit('update:config', $event)"
      />

      <!-- Actions -->
      <div>
        <h3 class="section-title">Actions</h3>
        <div class="action-stack">
          <button
            class="btn btn-primary full-width"
            :disabled="!file || running"
            @click="runPipeline"
          >
            {{ running ? 'Running...' : 'Run Blueprint to Adaptive' }}
          </button>
          <button
            class="btn btn-art-studio full-width"
            :disabled="!pipelineResponse"
            @click="sendToArtStudio"
          >
            Send to Art Studio
          </button>
        </div>
        <div
          v-if="lastExport"
          class="export-success"
        >
          Sent {{ lastExport }}
        </div>
        <div
          v-if="error"
          class="error-message"
        >
          {{ error }}
        </div>
      </div>

      <!-- Stats -->
      <PipelineStatsGrid
        v-if="stats"
        :stats="stats"
      />

      <!-- Toolpath Preview (extracted child component) -->
      <ToolpathPreviewSvg
        :moves="pipelineMoves"
        placeholder-text="Run Blueprint to Adaptive to see toolpath"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * BlueprintPresetPanel.vue - Blueprint to Adaptive pipeline UI
 *
 * REFACTORED: Child components extracted for decomposition:
 * - ToolConfigGrid: Tool configuration form inputs
 * - ToolpathPreviewSvg: SVG preview with segment normalization
 * - PipelineStatsGrid: Stats display grid
 */
import { ref } from 'vue'
import { api } from '@/services/apiBase'
import {
  PipelineStatsGrid,
  ToolConfigGrid,
  ToolpathPreviewSvg,
  type ToolConfig,
  type MovePoint,
} from './blueprint-preset'

const ARTSTUDIO_ADAPTIVE_KEY = 'ltb:artstudio:lastAdaptiveRequest'

// Props - use ToolConfig from child component
interface Props {
  config: ToolConfig
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  'update:config': [config: ToolConfig]
}>()

// Local state
const file = ref<File | null>(null)
const running = ref(false)
const error = ref<string | null>(null)
const pipelineResponse = ref<any | null>(null)
const stats = ref<any | null>(null)
const pipelineMoves = ref<MovePoint[]>([])
const lastExport = ref<string | null>(null)

// Handlers
function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  file.value = input.files?.[0] || null
  error.value = null
}

async function runPipeline() {
  if (!file.value) {
    error.value = 'Select a blueprint file first.'
    return
  }

  running.value = true
  error.value = null
  pipelineResponse.value = null
  stats.value = null
  pipelineMoves.value = []

  try {
    const form = new FormData()
    form.append('file', file.value)
    form.append('tool_d', String(props.config.tool_d))
    form.append('stepover', String(props.config.stepover))
    form.append('stepdown', String(props.config.stepdown))
    form.append('margin', String(props.config.margin))
    form.append('safe_z', String(props.config.safe_z))
    form.append('z_rough', String(props.config.z_rough))
    form.append('feed_xy', String(props.config.feed_xy))

    const res = await api('/api/pipeline/blueprint_to_adaptive', {
      method: 'POST',
      body: form
    })

    if (!res.ok) throw new Error('Blueprint to Adaptive failed')

    const data = await res.json()
    pipelineResponse.value = data
    stats.value = data.plan?.stats || null
    pipelineMoves.value = data.plan?.moves || []
  } catch (err: any) {
    console.error('Blueprint to Adaptive pipeline error', err)
    error.value = err?.message || String(err)
  } finally {
    running.value = false
  }
}

function sendToArtStudio() {
  const source = pipelineResponse.value?.adaptive_request || null

  if (!source) {
    error.value = 'No Adaptive request available. Run Blueprint to Adaptive first.'
    return
  }

  try {
    localStorage.setItem(ARTSTUDIO_ADAPTIVE_KEY, JSON.stringify(source))
    const ts = new Date().toLocaleTimeString()
    lastExport.value = 'at ' + ts
    window.location.href = '/art-studio'
  } catch (err) {
    console.error('Failed to export to Art Studio', err)
    error.value = 'Failed to save Adaptive request for Art Studio.'
  }
}
</script>

<style scoped>
.blueprint-preset {
  margin-top: 40px;
  border: 2px solid #9C27B0;
  animation: fadeIn 0.3s;
}

.stage-description {
  color: #666;
  margin-bottom: 20px;
}

.preset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.section-title {
  font-size: 1.1em;
  margin-bottom: 10px;
}

.file-input {
  display: block;
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.file-selected {
  margin-top: 10px;
  color: #4CAF50;
}

.action-stack {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.full-width {
  width: 100%;
}

.btn-art-studio {
  background: #9C27B0;
  color: white;
}

.btn-art-studio:hover:not(:disabled) {
  background: #7B1FA2;
}

.export-success {
  margin-top: 10px;
  font-size: 0.9em;
  color: #4CAF50;
}

.error-message {
  margin-top: 10px;
  padding: 10px;
  background: #ffebee;
  border-radius: 4px;
  color: #c62828;
  font-size: 0.9em;
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 1em;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary {
  background: #2196F3;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #1976D2;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
