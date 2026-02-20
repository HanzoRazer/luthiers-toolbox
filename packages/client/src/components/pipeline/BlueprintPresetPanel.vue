<template>
  <div
    class="stage-panel blueprint-preset"
  >
    <h2>🎨 Blueprint → Adaptive Preset (Phase 27.0)</h2>
    <p class="stage-description">
      Upload a blueprint image and run one-click Blueprint → Adaptive pipeline directly.
      Generate toolpath preview and send to Art Studio for refinement.
    </p>

    <div class="preset-grid">
      <!-- File Upload -->
      <div>
        <h3 class="section-title">📄 Blueprint Image</h3>
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
          ✅ {{ file.name }}
        </div>
      </div>

      <!-- Tool Configuration -->
      <div>
        <h3 class="section-title">🔧 Tool Configuration</h3>
        <div class="tool-grid">
          <label class="input-label">
            <span>Tool Ø (mm)</span>
            <input
              :value="config.tool_d"
              type="number"
              step="0.1"
              class="input-field"
              @input="updateConfig('tool_d', parseFloat(($event.target as HTMLInputElement).value))"
            >
          </label>
          <label class="input-label">
            <span>Stepover</span>
            <input
              :value="config.stepover"
              type="number"
              step="0.05"
              class="input-field"
              @input="updateConfig('stepover', parseFloat(($event.target as HTMLInputElement).value))"
            >
          </label>
          <label class="input-label">
            <span>Stepdown</span>
            <input
              :value="config.stepdown"
              type="number"
              step="0.1"
              class="input-field"
              @input="updateConfig('stepdown', parseFloat(($event.target as HTMLInputElement).value))"
            >
          </label>
          <label class="input-label">
            <span>Margin</span>
            <input
              :value="config.margin"
              type="number"
              step="0.1"
              class="input-field"
              @input="updateConfig('margin', parseFloat(($event.target as HTMLInputElement).value))"
            >
          </label>
          <label class="input-label">
            <span>Safe Z</span>
            <input
              :value="config.safe_z"
              type="number"
              step="0.1"
              class="input-field"
              @input="updateConfig('safe_z', parseFloat(($event.target as HTMLInputElement).value))"
            >
          </label>
          <label class="input-label">
            <span>Z Rough</span>
            <input
              :value="config.z_rough"
              type="number"
              step="0.1"
              class="input-field"
              @input="updateConfig('z_rough', parseFloat(($event.target as HTMLInputElement).value))"
            >
          </label>
          <label class="input-label span-2">
            <span>Feed XY</span>
            <input
              :value="config.feed_xy"
              type="number"
              step="10"
              class="input-field"
              @input="updateConfig('feed_xy', parseFloat(($event.target as HTMLInputElement).value))"
            >
          </label>
        </div>
      </div>

      <!-- Actions -->
      <div>
        <h3 class="section-title">⚡ Actions</h3>
        <div class="action-stack">
          <button
            class="btn btn-primary full-width"
            :disabled="!file || running"
            @click="runPipeline"
          >
            {{ running ? '⏳ Running...' : '🚀 Run Blueprint → Adaptive' }}
          </button>
          <button
            class="btn btn-art-studio full-width"
            :disabled="!pipelineResponse"
            @click="sendToArtStudio"
          >
            🎨 Send to Art Studio
          </button>
        </div>
        <div
          v-if="lastExport"
          class="export-success"
        >
          ✅ Sent {{ lastExport }}
        </div>
        <div
          v-if="error"
          class="error-message"
        >
          ❌ {{ error }}
        </div>
      </div>

      <!-- Stats -->
      <div v-if="stats">
        <h3 class="section-title">📊 Stats</h3>
        <div class="stats-grid">
          <div class="stat-box">
            <span class="stat-label">Moves:</span>
            <strong class="stat-value">{{ stats.move_count }}</strong>
          </div>
          <div
            v-if="stats.length_mm"
            class="stat-box"
          >
            <span class="stat-label">Length:</span>
            <strong class="stat-value">{{ stats.length_mm }} mm</strong>
          </div>
          <div
            v-if="stats.area_mm2"
            class="stat-box"
          >
            <span class="stat-label">Area:</span>
            <strong class="stat-value">{{ stats.area_mm2 }} mm²</strong>
          </div>
          <div
            v-if="stats.time_s"
            class="stat-box"
          >
            <span class="stat-label">Time:</span>
            <strong class="stat-value">{{ stats.time_s }} s</strong>
          </div>
        </div>
      </div>

      <!-- Toolpath Preview -->
      <div class="span-2">
        <h3 class="section-title">🔍 Toolpath Preview</h3>
        <div class="preview-container">
          <svg
            v-if="previewSegments.length"
            viewBox="0 0 100 100"
            preserveAspectRatio="xMidYMid meet"
            class="preview-svg"
          >
            <polyline
              v-for="(seg, idx) in previewSegments"
              :key="idx"
              :points="segToPoints(seg)"
              fill="none"
              stroke="lime"
              stroke-width="0.4"
            />
          </svg>
          <div
            v-else
            class="preview-placeholder"
          >
            Run Blueprint → Adaptive to see toolpath
          </div>
        </div>
        <div
          v-if="previewSegments.length"
          class="preview-footer"
        >
          {{ previewSegments.length }} segments
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { api } from '@/services/apiBase'

const ARTSTUDIO_ADAPTIVE_KEY = 'ltb:artstudio:lastAdaptiveRequest'

// Types
interface BlueprintConfig {
  tool_d: number
  stepover: number
  stepdown: number
  margin: number
  safe_z: number
  z_rough: number
  feed_xy: number
}

interface Segment {
  x1: number
  y1: number
  x2: number
  y2: number
}

// Props
interface Props {
  config: BlueprintConfig
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  'update:config': [config: BlueprintConfig]
}>()

// Local state
const file = ref<File | null>(null)
const running = ref(false)
const error = ref<string | null>(null)
const pipelineResponse = ref<any | null>(null)
const stats = ref<any | null>(null)
const previewSegments = ref<Segment[]>([])
const lastExport = ref<string | null>(null)

// Config update helper
function updateConfig<K extends keyof BlueprintConfig>(key: K, value: BlueprintConfig[K]) {
  emit('update:config', { ...props.config, [key]: value })
}

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
  previewSegments.value = []

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

    if (!res.ok) throw new Error('Blueprint → Adaptive failed')

    const data = await res.json()
    pipelineResponse.value = data
    stats.value = data.plan?.stats || null

    const segs = movesToSegments(data.plan?.moves || [])
    previewSegments.value = normalizeSegments(segs)
  } catch (err: any) {
    console.error('Blueprint → Adaptive pipeline error', err)
    error.value = err?.message || String(err)
  } finally {
    running.value = false
  }
}

function sendToArtStudio() {
  const source = pipelineResponse.value?.adaptive_request || null

  if (!source) {
    error.value = 'No Adaptive request available. Run Blueprint → Adaptive first.'
    return
  }

  try {
    localStorage.setItem(ARTSTUDIO_ADAPTIVE_KEY, JSON.stringify(source))
    const ts = new Date().toLocaleTimeString()
    lastExport.value = `at ${ts}`
    window.location.href = '/art-studio'
  } catch (err) {
    console.error('Failed to export to Art Studio', err)
    error.value = 'Failed to save Adaptive request for Art Studio.'
  }
}

// Toolpath preview helpers
function movesToSegments(moves: any[]): Segment[] {
  const segs: Segment[] = []
  let last = { x: 0, y: 0, has: false }

  for (const m of moves) {
    const x = typeof m.x === 'number' ? m.x : last.x
    const y = typeof m.y === 'number' ? m.y : last.y
    if (last.has) {
      segs.push({ x1: last.x, y1: last.y, x2: x, y2: y })
    }
    last = { x, y, has: true }
  }
  return segs
}

function normalizeSegments(segs: Segment[]): Segment[] {
  if (!segs.length) return []
  let minX = segs[0].x1, maxX = segs[0].x1
  let minY = segs[0].y1, maxY = segs[0].y1

  for (const s of segs) {
    minX = Math.min(minX, s.x1, s.x2)
    maxX = Math.max(maxX, s.x1, s.x2)
    minY = Math.min(minY, s.y1, s.y2)
    maxY = Math.max(maxY, s.y1, s.y2)
  }

  const dx = maxX - minX || 1
  const dy = maxY - minY || 1
  const scale = 90 / Math.max(dx, dy)
  const offsetX = (100 - dx * scale) / 2
  const offsetY = (100 - dy * scale) / 2

  return segs.map((s) => ({
    x1: (s.x1 - minX) * scale + offsetX,
    y1: 100 - ((s.y1 - minY) * scale + offsetY),
    x2: (s.x2 - minX) * scale + offsetX,
    y2: 100 - ((s.y2 - minY) * scale + offsetY)
  }))
}

function segToPoints(seg: Segment): string {
  return `${seg.x1},${seg.y1} ${seg.x2},${seg.y2}`
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

.tool-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.input-label {
  display: flex;
  flex-direction: column;
}

.input-label span {
  font-size: 0.9em;
  color: #666;
}

.input-field {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.span-2 {
  grid-column: span 2;
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

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  font-size: 0.9em;
}

.stat-box {
  padding: 10px;
  background: #f5f5f5;
  border-radius: 4px;
}

.stat-label {
  color: #666;
}

.stat-value {
  display: block;
  font-size: 1.2em;
  margin-top: 5px;
}

.preview-container {
  width: 100%;
  height: 300px;
  background: #1a1a1a;
  border-radius: 8px;
  position: relative;
  overflow: hidden;
}

.preview-svg {
  width: 100%;
  height: 100%;
}

.preview-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  font-size: 0.9em;
}

.preview-footer {
  margin-top: 10px;
  text-align: center;
  font-size: 0.9em;
  color: #666;
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
