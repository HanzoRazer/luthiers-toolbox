<template>
  <div class="stage-panel">
    <h2>🔗 Stage 3: Contour Reconstruction</h2>

    <div class="reconstruction-controls">
      <div class="control-group">
        <label>Layer Name</label>
        <input
          :value="params.layer_name"
          type="text"
          placeholder="Contours"
          @input="updateParam('layer_name', ($event.target as HTMLInputElement).value)"
        >
      </div>
      <div class="control-group">
        <label>Tolerance (mm)</label>
        <input
          :value="params.tolerance"
          type="number"
          step="0.05"
          min="0.05"
          max="1.0"
          @input="updateParam('tolerance', parseFloat(($event.target as HTMLInputElement).value))"
        >
      </div>
      <div class="control-group">
        <label>Min Loop Points</label>
        <input
          :value="params.min_loop_points"
          type="number"
          min="3"
          @input="updateParam('min_loop_points', parseInt(($event.target as HTMLInputElement).value))"
        >
      </div>
    </div>

    <div class="action-buttons">
      <button
        class="btn btn-primary"
        :disabled="loading"
        @click="emit('submit')"
      >
        {{ loading ? '⏳ Reconstructing...' : '🔗 Reconstruct Contours' }}
      </button>
    </div>

    <!-- Reconstruction Results -->
    <div
      v-if="result"
      class="reconstruction-results"
    >
      <div class="status-badge passed">
        <span class="status-icon">✅</span>
        <span class="status-text">{{ result.message }}</span>
      </div>

      <div class="summary-grid">
        <div class="stat-card neutral">
          <div class="stat-value">
            {{ result.loops.length }}
          </div>
          <div class="stat-label">
            LOOPS FOUND
          </div>
        </div>
        <div class="stat-card info">
          <div class="stat-value">
            {{ result.stats.lines_found }}
          </div>
          <div class="stat-label">
            LINES
          </div>
        </div>
        <div class="stat-card info">
          <div class="stat-value">
            {{ result.stats.splines_found }}
          </div>
          <div class="stat-label">
            SPLINES
          </div>
        </div>
        <div class="stat-card info">
          <div class="stat-value">
            {{ result.stats.edges_built }}
          </div>
          <div class="stat-label">
            EDGES
          </div>
        </div>
      </div>

      <!-- Warnings -->
      <div
        v-if="result.warnings.length > 0"
        class="warnings-section"
      >
        <h3>⚠️ Warnings</h3>
        <ul>
          <li
            v-for="(warning, idx) in result.warnings"
            :key="idx"
          >
            {{ warning }}
          </li>
        </ul>
      </div>

      <!-- Loop Info -->
      <div class="loops-section">
        <h3>Extracted Loops</h3>
        <div
          v-for="(loop, idx) in result.loops"
          :key="idx"
          class="loop-card"
        >
          <div class="loop-header">
            <strong>Loop {{ idx + 1 }}</strong>
            <span
              v-if="idx === result.outer_loop_idx"
              class="badge-outer"
            >OUTER</span>
            <span
              v-else
              class="badge-island"
            >ISLAND</span>
          </div>
          <div class="loop-info">
            Points: {{ loop.pts.length }}
          </div>
        </div>
      </div>

      <div class="action-buttons">
        <button
          class="btn btn-primary"
          @click="emit('continue')"
        >
          ➡️ Continue to Adaptive Pocket
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Types
interface ReconstructionParams {
  layer_name: string
  tolerance: number
  min_loop_points: number
}

interface Loop {
  pts: Array<{ x: number; y: number }>
}

interface ReconstructionResult {
  message: string
  loops: Loop[]
  outer_loop_idx: number
  warnings: string[]
  stats: {
    lines_found: number
    splines_found: number
    edges_built: number
  }
}

// Props
interface Props {
  params: ReconstructionParams
  result: ReconstructionResult | null
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
})

// Emits
const emit = defineEmits<{
  'update:params': [params: ReconstructionParams]
  'submit': []
  'continue': []
}>()

// Helpers
function updateParam<K extends keyof ReconstructionParams>(key: K, value: ReconstructionParams[K]) {
  emit('update:params', { ...props.params, [key]: value })
}
</script>

<style scoped>
.stage-panel {
  animation: fadeIn 0.3s;
}

.reconstruction-controls {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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

.control-group input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1em;
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

.warnings-section {
  margin: 20px 0;
  padding: 15px;
  background: #fff3e0;
  border-radius: 8px;
}

.warnings-section ul {
  margin: 10px 0 0 20px;
}

.loops-section {
  margin: 20px 0;
}

.loop-card {
  padding: 15px;
  background: #f5f5f5;
  border-radius: 8px;
  margin: 10px 0;
}

.loop-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 5px;
}

.badge-outer {
  padding: 3px 8px;
  background: #4CAF50;
  color: white;
  border-radius: 4px;
  font-size: 0.85em;
}

.badge-island {
  padding: 3px 8px;
  background: #ff9800;
  color: white;
  border-radius: 4px;
  font-size: 0.85em;
}

.loop-info {
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

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
