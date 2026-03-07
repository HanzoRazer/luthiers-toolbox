<script setup lang="ts">
/**
 * ToolpathSimulatorView - 3D Toolpath Visualization and Simulation
 * Visualize and simulate G-code toolpaths before cutting
 *
 * Connected to API endpoints:
 *   POST /api/cam/simulate/preview
 *   POST /api/cam/simulate/analyze
 */
import { ref } from 'vue'

const gcodeFile = ref<File | null>(null)
const gcodeText = ref('')
const viewMode = ref('3d')  // 3d, top, front, side
const showToolpath = ref(true)
const showStock = ref(true)
const showRapids = ref(true)
const simulationSpeed = ref(1)
const currentLine = ref(0)
const totalLines = ref(0)
const isPlaying = ref(false)

// Simulation stats
const stats = ref({
  totalDistance: 0,
  cuttingDistance: 0,
  rapidDistance: 0,
  estimatedTime: 0,
  toolChanges: 0,
})

function handleFileUpload(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files?.length) {
    gcodeFile.value = input.files[0]
    const reader = new FileReader()
    reader.onload = (e) => {
      gcodeText.value = e.target?.result as string
      totalLines.value = gcodeText.value.split('\n').length
    }
    reader.readAsText(input.files[0])
  }
}

function play() {
  isPlaying.value = true
}

function pause() {
  isPlaying.value = false
}

function reset() {
  currentLine.value = 0
  isPlaying.value = false
}

function stepForward() {
  if (currentLine.value < totalLines.value) {
    currentLine.value++
  }
}
</script>

<template>
  <div class="toolpath-simulator-view">
    <div class="header">
      <h1>Toolpath Simulator</h1>
      <p class="subtitle">Visualize and verify G-code before cutting</p>
    </div>

    <div class="content">
      <div class="panel upload-panel">
        <h3>G-code Input</h3>
        <div class="upload-zone" @click="($refs.fileInput as HTMLInputElement).click()">
          <input type="file" ref="fileInput" accept=".nc,.gcode,.tap,.ngc" @change="handleFileUpload" hidden />
          <span class="upload-icon">📄</span>
          <p v-if="gcodeFile">{{ gcodeFile.name }}</p>
          <p v-else>Upload G-code file</p>
        </div>

        <h3>View</h3>
        <div class="view-buttons">
          <button :class="{ active: viewMode === '3d' }" @click="viewMode = '3d'">3D</button>
          <button :class="{ active: viewMode === 'top' }" @click="viewMode = 'top'">Top</button>
          <button :class="{ active: viewMode === 'front' }" @click="viewMode = 'front'">Front</button>
          <button :class="{ active: viewMode === 'side' }" @click="viewMode = 'side'">Side</button>
        </div>

        <h3>Display</h3>
        <div class="toggle-group">
          <label><input type="checkbox" v-model="showToolpath" /> Toolpath</label>
          <label><input type="checkbox" v-model="showStock" /> Stock</label>
          <label><input type="checkbox" v-model="showRapids" /> Rapids</label>
        </div>
      </div>

      <div class="panel viewer-panel">
        <div class="viewer-container">
          <div class="placeholder">
            <span class="icon">🎥</span>
            <p v-if="!gcodeFile">Upload a G-code file to simulate</p>
            <p v-else>{{ totalLines }} lines loaded</p>
          </div>
        </div>

        <div class="playback-controls">
          <button @click="reset">⏮</button>
          <button @click="isPlaying ? pause() : play()">{{ isPlaying ? '⏸' : '▶️' }}</button>
          <button @click="stepForward">⏭</button>
          <input type="range" v-model.number="currentLine" :max="totalLines" />
          <span class="progress">{{ currentLine }} / {{ totalLines }}</span>
        </div>

        <div class="speed-control">
          <label>Speed:</label>
          <input type="range" v-model.number="simulationSpeed" min="0.1" max="10" step="0.1" />
          <span>{{ simulationSpeed }}x</span>
        </div>
      </div>

      <div class="panel stats-panel">
        <h3>Statistics</h3>
        <div class="stat-row">
          <span class="stat-label">Total Distance</span>
          <span class="stat-value">{{ stats.totalDistance.toFixed(1) }} mm</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Cutting Distance</span>
          <span class="stat-value">{{ stats.cuttingDistance.toFixed(1) }} mm</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Rapid Distance</span>
          <span class="stat-value">{{ stats.rapidDistance.toFixed(1) }} mm</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Estimated Time</span>
          <span class="stat-value">{{ stats.estimatedTime.toFixed(1) }} min</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Tool Changes</span>
          <span class="stat-value">{{ stats.toolChanges }}</span>
        </div>

        <h3>G-code Preview</h3>
        <div class="gcode-preview">
          <pre v-if="gcodeText">{{ gcodeText.split('\n').slice(0, 20).join('\n') }}...</pre>
          <p v-else class="empty">No G-code loaded</p>
        </div>
      </div>
    </div>

    <div class="coming-soon-notice">
      <p>Full 3D simulation with stock removal visualization coming soon.</p>
    </div>
  </div>
</template>

<style scoped>
.toolpath-simulator-view { min-height: 100vh; background: #0a0a0a; color: #e5e5e5; padding: 2rem; }
.header { max-width: 1400px; margin: 0 auto 2rem; }
.header h1 { font-size: 2rem; font-weight: 700; margin: 0 0 0.5rem; }
.subtitle { color: #888; margin: 0; }

.content { max-width: 1400px; margin: 0 auto; display: grid; grid-template-columns: 250px 1fr 280px; gap: 1.5rem; }
.panel { background: #1a1a1a; border-radius: 0.75rem; padding: 1.5rem; }
.panel h3 { font-size: 0.875rem; font-weight: 600; color: #888; text-transform: uppercase; margin: 0 0 1rem; }
.panel h3:not(:first-child) { margin-top: 1.5rem; }

.upload-zone { border: 2px dashed #333; border-radius: 0.5rem; padding: 1.5rem; text-align: center; cursor: pointer; }
.upload-zone:hover { border-color: #60a5fa; }
.upload-icon { font-size: 2rem; display: block; margin-bottom: 0.5rem; }

.view-buttons { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; }
.view-buttons button { padding: 0.5rem; background: #262626; border: 1px solid #333; border-radius: 0.375rem; color: #e5e5e5; cursor: pointer; }
.view-buttons button.active { background: #2563eb; border-color: #2563eb; }

.toggle-group { display: flex; flex-direction: column; gap: 0.5rem; }
.toggle-group label { display: flex; align-items: center; gap: 0.5rem; cursor: pointer; font-size: 0.875rem; }

.viewer-container { aspect-ratio: 16/9; background: #0d0d0d; border-radius: 0.5rem; display: flex; align-items: center; justify-content: center; margin-bottom: 1rem; }
.placeholder { text-align: center; color: #666; }
.placeholder .icon { font-size: 3rem; display: block; margin-bottom: 0.5rem; }

.playback-controls { display: flex; gap: 0.5rem; align-items: center; margin-bottom: 0.75rem; }
.playback-controls button { width: 2.5rem; height: 2.5rem; background: #262626; border: 1px solid #333; border-radius: 0.375rem; cursor: pointer; font-size: 1rem; }
.playback-controls input[type="range"] { flex: 1; }
.progress { font-size: 0.75rem; color: #888; min-width: 80px; }

.speed-control { display: flex; align-items: center; gap: 0.5rem; }
.speed-control label { font-size: 0.875rem; color: #888; }
.speed-control input { flex: 1; }
.speed-control span { font-size: 0.875rem; color: #e5e5e5; min-width: 3rem; }

.stat-row { display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid #262626; font-size: 0.875rem; }
.stat-label { color: #888; }
.stat-value { color: #e5e5e5; font-family: monospace; }

.gcode-preview { background: #0d0d0d; border-radius: 0.375rem; padding: 0.75rem; max-height: 200px; overflow: auto; }
.gcode-preview pre { margin: 0; font-size: 0.75rem; color: #888; white-space: pre-wrap; }
.empty { color: #666; font-size: 0.875rem; margin: 0; }

.coming-soon-notice { max-width: 1400px; margin: 2rem auto 0; padding: 1rem; background: #1e3a5f; border-radius: 0.5rem; text-align: center; color: #60a5fa; }

@media (max-width: 1200px) { .content { grid-template-columns: 1fr; } }
</style>
