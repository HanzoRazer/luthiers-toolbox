<template>
  <div class="adaptive-bench-lab">
    <h2>Adaptive Benchmark Lab (N16)</h2>
    <p class="subtitle">
      Performance profiling for adaptive spiral algorithms • Trochoidal corner visualization
    </p>

    <div class="lab-grid">
      <!-- Left: Parameters & Controls -->
      <div class="params-panel">
        <h3>Test Parameters</h3>

        <div class="param-group">
          <h4>Geometry</h4>
          <label>
            Width (mm):
            <input
              v-model.number="width"
              type="number"
              step="10"
              min="10"
            >
          </label>
          <label>
            Height (mm):
            <input
              v-model.number="height"
              type="number"
              step="10"
              min="10"
            >
          </label>
        </div>

        <div class="param-group">
          <h4>Tool</h4>
          <label>
            Tool Diameter (mm):
            <input
              v-model.number="toolDia"
              type="number"
              step="0.5"
              min="1"
            >
          </label>
          <label>
            Stepover (mm):
            <input
              v-model.number="stepover"
              type="number"
              step="0.1"
              min="0.1"
            >
          </label>
        </div>

        <div class="param-group">
          <h4>Spiral Options</h4>
          <label>
            Corner Fillet (mm):
            <input
              v-model.number="cornerFillet"
              type="number"
              step="0.1"
              min="0"
            >
          </label>
        </div>

        <div class="param-group">
          <h4>Trochoid Options</h4>
          <label>
            Loop Pitch (mm):
            <input
              v-model.number="loopPitch"
              type="number"
              step="0.1"
              min="0.1"
            >
          </label>
          <label>
            Amplitude (mm):
            <input
              v-model.number="amplitude"
              type="number"
              step="0.1"
              min="0"
            >
          </label>
        </div>

        <div class="param-group">
          <h4>Benchmark</h4>
          <label>
            Runs:
            <input
              v-model.number="benchRuns"
              type="number"
              step="10"
              min="1"
            >
          </label>
        </div>

        <div class="actions">
          <button
            :disabled="loading"
            class="btn-primary"
            @click="generateSpiral"
          >
            {{ loading ? 'Generating...' : 'Generate Spiral' }}
          </button>
          <button
            :disabled="loading"
            class="btn-primary"
            @click="generateTrochoid"
          >
            {{ loading ? 'Generating...' : 'Generate Trochoid' }}
          </button>
          <button
            :disabled="loading"
            class="btn-secondary"
            @click="runBenchmark"
          >
            {{ loading ? 'Running...' : 'Run Benchmark' }}
          </button>
        </div>
      </div>

      <!-- Right: Visualization & Results -->
      <div class="output-panel">
        <h3>Visualization</h3>

        <div
          v-if="error"
          class="error-banner"
        >
          <strong>⚠️ Error:</strong> {{ error }}
        </div>

        <div
          v-if="svgContent"
          class="svg-viewer"
          v-html="svgContent"
        />

        <div
          v-if="benchResult"
          class="bench-results"
        >
          <h4>Benchmark Results</h4>
          <div class="stats-grid">
            <div class="stat">
              <div class="stat-label">
                Total Time
              </div>
              <div class="stat-value">
                {{ benchResult.total_ms.toFixed(2) }} ms
              </div>
            </div>
            <div class="stat">
              <div class="stat-label">
                Average Time
              </div>
              <div class="stat-value">
                {{ benchResult.avg_ms.toFixed(3) }} ms
              </div>
            </div>
            <div class="stat">
              <div class="stat-label">
                Runs
              </div>
              <div class="stat-value">
                {{ benchResult.runs }}
              </div>
            </div>
            <div class="stat">
              <div class="stat-label">
                Geometry
              </div>
              <div class="stat-value">
                {{ benchResult.width }}×{{ benchResult.height }} mm
              </div>
            </div>
          </div>
        </div>

        <div
          v-if="!svgContent && !benchResult && !error"
          class="placeholder"
        >
          <p>Select an action to visualize spiral or trochoid paths, or run performance benchmark.</p>
        </div>
      </div>
    </div>

    <section class="info-section">
      <h3>ℹ️ About N16 Benchmark Suite</h3>
      <div class="info-grid">
        <div class="info-card">
          <h4>📐 Offset Spiral</h4>
          <p>Generates inward offset rings stitched into continuous spiral path. Tests adaptive toolpath algorithm performance.</p>
        </div>
        <div class="info-card">
          <h4>🌀 Trochoidal Corners</h4>
          <p>Small sine-modulated loops around corners to reduce chip load. Illustrates corner load management technique.</p>
        </div>
        <div class="info-card">
          <h4>⚡ Performance Benchmark</h4>
          <p>Measures algorithm execution time over multiple runs. Helps validate Module L.3 performance characteristics.</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

// Parameters
const width = ref(100)
const height = ref(60)
const toolDia = ref(6.0)
const stepover = ref(2.4)
const cornerFillet = ref(0.6)
const loopPitch = ref(2.5)
const amplitude = ref(0.4)
const benchRuns = ref(20)

// State
const loading = ref(false)
const error = ref('')
const svgContent = ref('')
const benchResult = ref<{
  runs: number
  total_ms: number
  avg_ms: number
  width: number
  height: number
} | null>(null)

// Generate Spiral
async function generateSpiral() {
  loading.value = true
  error.value = ''
  svgContent.value = ''
  benchResult.value = null

  try {
    const req = {
      width: width.value,
      height: height.value,
      tool_dia: toolDia.value,
      stepover: stepover.value,
      corner_fillet: cornerFillet.value
    }

    const response = await fetch('/api/cam/adaptive2/offset_spiral.svg', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req)
    })

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`)
    }

    const svg = await response.text()
    svgContent.value = svg

  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}

// Generate Trochoid
async function generateTrochoid() {
  loading.value = true
  error.value = ''
  svgContent.value = ''
  benchResult.value = null

  try {
    const req = {
      width: width.value,
      height: height.value,
      tool_dia: toolDia.value,
      loop_pitch: loopPitch.value,
      amp: amplitude.value
    }

    const response = await fetch('/api/cam/adaptive2/trochoid_corners.svg', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req)
    })

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`)
    }

    const svg = await response.text()
    svgContent.value = svg

  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}

// Run Benchmark
async function runBenchmark() {
  loading.value = true
  error.value = ''
  svgContent.value = ''
  benchResult.value = null

  try {
    const req = {
      width: width.value,
      height: height.value,
      tool_dia: toolDia.value,
      stepover: stepover.value,
      runs: benchRuns.value
    }

    const response = await fetch('/api/cam/adaptive2/bench', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req)
    })

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`)
    }

    const result = await response.json()
    benchResult.value = result

  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.adaptive-bench-lab {
  padding: 1rem;
  max-width: 1400px;
  margin: 0 auto;
}

.subtitle {
  color: #666;
  margin-bottom: 1.5rem;
}

.lab-grid {
  display: grid;
  grid-template-columns: 400px 1fr;
  gap: 2rem;
  margin-bottom: 2rem;
}

.params-panel, .output-panel {
  background: #f9f9f9;
  padding: 1.5rem;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.param-group {
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e0e0e0;
}

.param-group:last-child {
  border-bottom: none;
}

h3 {
  margin-top: 0;
  color: #333;
  font-size: 1.2rem;
}

h4 {
  margin: 0 0 0.5rem 0;
  color: #555;
  font-size: 0.95rem;
  font-weight: 600;
}

label {
  display: block;
  margin-bottom: 0.75rem;
  font-size: 0.9rem;
  color: #555;
}

input[type="number"] {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 0.9rem;
  margin-top: 0.25rem;
}

.actions {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.btn-primary, .btn-secondary {
  width: 100%;
  padding: 0.75rem;
  border: none;
  border-radius: 4px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-secondary {
  background: #64748b;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #475569;
}

.btn-primary:disabled, .btn-secondary:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

.error-banner {
  background: #fef2f2;
  border: 1px solid #fca5a5;
  color: #991b1b;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.svg-viewer {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 1rem;
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.svg-viewer :deep(svg) {
  max-width: 100%;
  height: auto;
}

.bench-results {
  background: #f1f5f9;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  padding: 1rem;
  margin-top: 1rem;
}

.bench-results h4 {
  margin-top: 0;
  margin-bottom: 1rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.stat {
  background: white;
  padding: 0.75rem;
  border-radius: 4px;
  border: 1px solid #e2e8f0;
}

.stat-label {
  font-size: 0.8rem;
  color: #64748b;
  margin-bottom: 0.25rem;
}

.stat-value {
  font-size: 1.1rem;
  font-weight: 600;
  color: #0f172a;
}

.placeholder {
  text-align: center;
  padding: 3rem 1rem;
  color: #64748b;
}

.info-section {
  margin-top: 3rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.info-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1.5rem;
}

.info-card h4 {
  margin-top: 0;
  margin-bottom: 0.75rem;
  color: #0f172a;
}

.info-card p {
  margin: 0;
  color: #64748b;
  font-size: 0.9rem;
  line-height: 1.5;
}

@media (max-width: 1024px) {
  .lab-grid {
    grid-template-columns: 1fr;
  }
}
</style>
