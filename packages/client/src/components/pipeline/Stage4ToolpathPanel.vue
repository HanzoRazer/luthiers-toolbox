<template>
  <div class="stage-panel">
    <h2>⚙️ Stage 4: Adaptive Pocket Toolpath</h2>

    <div class="params-grid">
      <div class="control-group">
        <label>Tool Diameter (mm)</label>
        <input
          :value="params.tool_d"
          type="number"
          step="0.5"
          min="1"
          @input="updateParam('tool_d', parseFloat(($event.target as HTMLInputElement).value))"
        >
      </div>
      <div class="control-group">
        <label>Stepover (%)</label>
        <input
          :value="stepoverPercentDisplay"
          type="number"
          step="5"
          min="10"
          max="100"
          @input="updateStepoverPercent(parseFloat(($event.target as HTMLInputElement).value))"
        >
        <small>{{ params.stepover.toFixed(2) }} of tool diameter</small>
      </div>
      <div class="control-group">
        <label>Stepdown (mm)</label>
        <input
          :value="params.stepdown"
          type="number"
          step="0.5"
          min="0.5"
          @input="updateParam('stepdown', parseFloat(($event.target as HTMLInputElement).value))"
        >
      </div>
      <div class="control-group">
        <label>Margin (mm)</label>
        <input
          :value="params.margin"
          type="number"
          step="0.1"
          min="0"
          @input="updateParam('margin', parseFloat(($event.target as HTMLInputElement).value))"
        >
      </div>
      <div class="control-group">
        <label>Strategy</label>
        <select
          :value="params.strategy"
          @change="updateParam('strategy', ($event.target as HTMLSelectElement).value)"
        >
          <option>Spiral</option>
          <option>Lanes</option>
        </select>
      </div>
      <div class="control-group">
        <label>Feed XY (mm/min)</label>
        <input
          :value="params.feed_xy"
          type="number"
          step="100"
          min="100"
          @input="updateParam('feed_xy', parseFloat(($event.target as HTMLInputElement).value))"
        >
      </div>
    </div>

    <div class="action-buttons">
      <button
        class="btn btn-primary"
        :disabled="loading"
        @click="emit('submit')"
      >
        {{ loading ? '⏳ Generating...' : '⚡ Generate Toolpath' }}
      </button>
    </div>

    <!-- Toolpath Results -->
    <div
      v-if="result"
      class="toolpath-results"
    >
      <div class="status-badge passed">
        <span class="status-icon">✅</span>
        <span class="status-text">Toolpath Generated</span>
      </div>

      <div class="summary-grid">
        <div class="stat-card neutral">
          <div class="stat-value">
            {{ result.stats.length_mm.toFixed(1) }}
          </div>
          <div class="stat-label">
            LENGTH (mm)
          </div>
        </div>
        <div class="stat-card info">
          <div class="stat-value">
            {{ result.stats.time_min.toFixed(2) }}
          </div>
          <div class="stat-label">
            TIME (min)
          </div>
        </div>
        <div class="stat-card info">
          <div class="stat-value">
            {{ result.moves.length }}
          </div>
          <div class="stat-label">
            MOVES
          </div>
        </div>
        <div class="stat-card info">
          <div class="stat-value">
            {{ (result.stats.volume_mm3 / 1000).toFixed(1) }}
          </div>
          <div class="stat-label">
            VOLUME (cm³)
          </div>
        </div>
      </div>

      <div class="action-buttons">
        <button
          class="btn btn-secondary"
          @click="emit('download-json')"
        >
          📥 Download JSON
        </button>
        <button
          class="btn btn-primary"
          @click="emit('export-gcode')"
        >
          📄 Export G-code
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

// Types
interface AdaptiveParams {
  tool_d: number
  stepover: number
  stepdown: number
  margin: number
  strategy: string
  feed_xy: number
}

interface ToolpathMove {
  type: string
  x?: number
  y?: number
  z?: number
}

interface ToolpathResult {
  stats: {
    length_mm: number
    time_min: number
    volume_mm3: number
  }
  moves: ToolpathMove[]
}

// Props
interface Props {
  params: AdaptiveParams
  result: ToolpathResult | null
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
})

// Emits
const emit = defineEmits<{
  'update:params': [params: AdaptiveParams]
  'submit': []
  'download-json': []
  'export-gcode': []
}>()

// Computed: stepover percentage display
const stepoverPercentDisplay = computed(() => {
  return Math.round(props.params.stepover * 100)
})

// Helpers
function updateParam<K extends keyof AdaptiveParams>(key: K, value: AdaptiveParams[K]) {
  emit('update:params', { ...props.params, [key]: value })
}

function updateStepoverPercent(percent: number) {
  const stepover = percent / 100
  emit('update:params', { ...props.params, stepover })
}
</script>

<style scoped>
.stage-panel {
  animation: fadeIn 0.3s;
}

.params-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 15px;
  margin: 20px 0;
}

.control-group {
  margin: 15px 0;
}

.control-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #333;
}

.control-group input,
.control-group select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1em;
}

.control-group small {
  display: block;
  margin-top: 5px;
  color: #666;
  font-size: 0.85em;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 15px 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 1.2em;
  font-weight: bold;
}

.status-badge.passed {
  background: #4CAF50;
  color: white;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 15px;
  margin: 20px 0;
}

.stat-card {
  padding: 20px;
  border-radius: 8px;
  text-align: center;
  background: #f5f5f5;
}

.stat-card.info { border-left: 4px solid #2196F3; }
.stat-card.neutral { border-left: 4px solid #9e9e9e; }

.stat-value {
  font-size: 2.5em;
  font-weight: bold;
  margin-bottom: 5px;
}

.stat-label {
  color: #666;
  font-size: 0.9em;
}

.action-buttons {
  display: flex;
  gap: 15px;
  margin: 30px 0;
  justify-content: center;
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

.btn-secondary {
  background: #9e9e9e;
  color: white;
}

.btn-secondary:hover {
  background: #757575;
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
