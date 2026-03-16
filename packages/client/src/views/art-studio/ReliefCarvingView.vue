<script setup lang="ts">
/**
 * ReliefCarvingView - 3D Relief Carving Designer
 * Manufacturing operation — nav moved to CAM Tools section (CU-A3). Route path unchanged.
 *
 * Connected to API endpoints:
 *   POST /api/cam/relief/map_from_heightfield
 *   POST /api/cam/relief/roughing
 *   POST /api/cam/relief/finishing
 *   POST /api/cam/relief/sim_bridge
 */
import { ref, computed } from 'vue'

// API base
const API_BASE = '/api/cam/relief'

// Form state
const reliefDepth = ref(3)
const toolDiameter = ref(3.175)
const stepover = ref(0.4)
const stepdown = ref(0.5)
const feedRate = ref(1000)
const feedRateZ = ref(300)
const safeZ = ref(4.0)
const scallop = ref(0.05)
const pattern = ref<'RasterX' | 'RasterY'>('RasterX')
const toolpathType = ref<'roughing' | 'finishing'>('roughing')

// File upload state
const selectedFile = ref<File | null>(null)
const heightmapPath = ref('')
const isDragging = ref(false)

// API response state
const zGrid = ref<number[][] | null>(null)
const gridStats = ref<{ width: number; height: number; z_min: number; z_max: number } | null>(null)
const toolpathMoves = ref<any[]>([])
const toolpathStats = ref<{ move_count: number; length_xy: number; min_z: number; max_z: number; est_time_s: number } | null>(null)
const simIssues = ref<any[]>([])
const simStats = ref<any | null>(null)

// Loading states
const isLoadingMap = ref(false)
const isGenerating = ref(false)
const isSimulating = ref(false)
const error = ref('')

// Computed
const hasZGrid = computed(() => zGrid.value !== null)
const hasToolpath = computed(() => toolpathMoves.value.length > 0)

// Risk indicators from simulation
const riskIndicators = computed(() => {
  if (!simStats.value) {
    return [
      { label: 'Tool engagement', status: 'pending', message: 'Run simulation' },
      { label: 'Depth of cut', status: 'pending', message: 'Run simulation' },
      { label: 'Surface finish', status: 'pending', message: 'Run simulation' },
    ]
  }

  const issues = simIssues.value
  const stats = simStats.value

  return [
    {
      label: 'Tool engagement',
      status: stats.max_load_index > 2.0 ? 'danger' : stats.max_load_index > 1.0 ? 'warning' : 'safe',
      message: `Load index: ${stats.max_load_index.toFixed(2)}`,
    },
    {
      label: 'Floor thickness',
      status: stats.min_floor_thickness < 0.3 ? 'danger' : stats.min_floor_thickness < 0.6 ? 'warning' : 'safe',
      message: `Min: ${stats.min_floor_thickness.toFixed(2)}mm`,
    },
    {
      label: 'Surface finish',
      status: scallop.value > 0.1 ? 'warning' : 'safe',
      message: `Scallop: ${scallop.value.toFixed(3)}mm`,
    },
  ]
})

// File handling
function onDragOver(e: DragEvent) {
  e.preventDefault()
  isDragging.value = true
}

function onDragLeave() {
  isDragging.value = false
}

function onDrop(e: DragEvent) {
  e.preventDefault()
  isDragging.value = false
  const files = e.dataTransfer?.files
  if (files && files.length > 0) {
    handleFile(files[0])
  }
}

function onFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files && input.files.length > 0) {
    handleFile(input.files[0])
  }
}

function handleFile(file: File) {
  const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/bmp']
  if (!validTypes.includes(file.type)) {
    error.value = 'Please upload a PNG, JPG, or BMP image'
    return
  }
  selectedFile.value = file
  error.value = ''
  // For demo, we'll use a placeholder path - in production this would upload to server
  heightmapPath.value = `uploads/${file.name}`
}

// API calls
async function loadHeightmap() {
  if (!selectedFile.value) {
    error.value = 'Please select a heightmap image first'
    return
  }

  isLoadingMap.value = true
  error.value = ''

  try {
    // In a real implementation, we'd first upload the file
    // For now, use a demo heightmap path or uploaded file path
    const response = await fetch(`${API_BASE}/map_from_heightfield`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        heightmap_path: heightmapPath.value,
        units: 'mm',
        z_min: 0,
        z_max: -reliefDepth.value,
        sample_pitch_xy: 0.3,
        smooth_sigma: 1.0,
      }),
    })

    if (!response.ok) {
      const err = await response.json()
      throw new Error(err.detail || 'Failed to load heightmap')
    }

    const data = await response.json()
    zGrid.value = data.z_grid
    gridStats.value = {
      width: data.width,
      height: data.height,
      z_min: data.z_min,
      z_max: data.z_max,
    }
  } catch (e: any) {
    error.value = e.message || 'Failed to load heightmap'
  } finally {
    isLoadingMap.value = false
  }
}

async function generateToolpath() {
  if (!zGrid.value) {
    error.value = 'Please load a heightmap first'
    return
  }

  isGenerating.value = true
  error.value = ''

  try {
    const endpoint = toolpathType.value === 'roughing' ? '/roughing' : '/finishing'
    const payload: any = {
      z_grid: zGrid.value,
      origin_x: 0,
      origin_y: 0,
      cell_size_xy: 0.3,
      units: 'mm',
      tool_d: toolDiameter.value,
      stepdown: stepdown.value,
      safe_z: safeZ.value,
      feed_xy: feedRate.value,
      feed_z: feedRateZ.value,
    }

    if (toolpathType.value === 'finishing') {
      payload.scallop_height = scallop.value
      payload.pattern = pattern.value
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })

    if (!response.ok) {
      const err = await response.json()
      throw new Error(err.detail || 'Failed to generate toolpath')
    }

    const data = await response.json()
    toolpathMoves.value = data.moves
    toolpathStats.value = data.stats

    // Auto-run simulation after toolpath generation
    await runSimulation()
  } catch (e: any) {
    error.value = e.message || 'Failed to generate toolpath'
  } finally {
    isGenerating.value = false
  }
}

async function runSimulation() {
  if (toolpathMoves.value.length === 0) {
    return
  }

  isSimulating.value = true

  try {
    const response = await fetch(`${API_BASE}/sim_bridge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        moves: toolpathMoves.value,
        stock_thickness: reliefDepth.value + 1,
        origin_x: 0,
        origin_y: 0,
        cell_size_xy: 0.5,
        units: 'mm',
        min_floor_thickness: 0.6,
        high_load_index: 2.0,
        med_load_index: 1.0,
      }),
    })

    if (!response.ok) {
      const err = await response.json()
      throw new Error(err.detail || 'Simulation failed')
    }

    const data = await response.json()
    simIssues.value = data.issues
    simStats.value = data.stats
  } catch (e: any) {
    console.error('Simulation error:', e)
  } finally {
    isSimulating.value = false
  }
}
</script>

<template>
  <div class="relief-carving-view">
    <header class="view-header">
      <h1>3D Relief Carving</h1>
      <p class="subtitle">Design and machine stunning relief carvings for rosettes, logos, and decorative elements</p>
    </header>

    <div v-if="error" class="error-banner">
      {{ error }}
      <button @click="error = ''" class="dismiss-btn">&times;</button>
    </div>

    <div class="content-grid">
      <section class="panel upload-panel">
        <h2>Import Heightmap</h2>
        <div
          class="upload-zone"
          :class="{ dragging: isDragging, 'has-file': selectedFile }"
          @dragover="onDragOver"
          @dragleave="onDragLeave"
          @drop="onDrop"
          @click="($refs.fileInput as HTMLInputElement)?.click()"
        >
          <input
            ref="fileInput"
            type="file"
            accept=".png,.jpg,.jpeg,.bmp"
            style="display: none"
            @change="onFileSelect"
          />
          <div v-if="selectedFile" class="file-info">
            <span class="icon">✓</span>
            <p class="filename">{{ selectedFile.name }}</p>
            <p class="hint">{{ (selectedFile.size / 1024).toFixed(1) }} KB</p>
          </div>
          <div v-else class="upload-placeholder">
            <span class="icon">🎨</span>
            <p>Drop grayscale heightmap</p>
            <p class="hint">PNG, JPG, or BMP (white=high, black=low)</p>
          </div>
        </div>
        <button
          class="btn-secondary"
          :disabled="!selectedFile || isLoadingMap"
          @click="loadHeightmap"
        >
          {{ isLoadingMap ? 'Loading...' : 'Load Heightmap' }}
        </button>

        <div v-if="gridStats" class="grid-stats">
          <p><strong>Grid:</strong> {{ gridStats.width }} × {{ gridStats.height }}</p>
          <p><strong>Z Range:</strong> {{ gridStats.z_min.toFixed(2) }} to {{ gridStats.z_max.toFixed(2) }} mm</p>
        </div>
      </section>

      <section class="panel params-panel">
        <h2>Carving Parameters</h2>
        <div class="param-group">
          <label>
            Relief Depth (mm)
            <input v-model.number="reliefDepth" type="number" step="0.5" min="0.5" max="25" />
          </label>
          <label>
            Tool Diameter (mm)
            <input v-model.number="toolDiameter" type="number" step="0.125" min="0.5" max="12" />
          </label>
          <label>
            Stepdown (mm)
            <input v-model.number="stepdown" type="number" step="0.1" min="0.1" max="5" />
          </label>
          <label>
            Feed Rate XY (mm/min)
            <input v-model.number="feedRate" type="number" step="100" min="100" max="5000" />
          </label>
          <label>
            Feed Rate Z (mm/min)
            <input v-model.number="feedRateZ" type="number" step="50" min="50" max="1000" />
          </label>
        </div>

        <div class="toolpath-type">
          <label>
            <input type="radio" v-model="toolpathType" value="roughing" />
            Roughing
          </label>
          <label>
            <input type="radio" v-model="toolpathType" value="finishing" />
            Finishing
          </label>
        </div>

        <div v-if="toolpathType === 'finishing'" class="param-group finishing-params">
          <label>
            Scallop Height (mm)
            <input v-model.number="scallop" type="number" step="0.01" min="0.01" max="0.5" />
          </label>
          <label>
            Pattern
            <select v-model="pattern">
              <option value="RasterX">Raster X</option>
              <option value="RasterY">Raster Y</option>
            </select>
          </label>
        </div>

        <button
          class="btn-primary"
          :disabled="!hasZGrid || isGenerating"
          @click="generateToolpath"
        >
          {{ isGenerating ? 'Generating...' : `Generate ${toolpathType === 'roughing' ? 'Roughing' : 'Finishing'}` }}
        </button>
      </section>

      <section class="panel preview-panel">
        <h2>Toolpath Preview</h2>
        <div class="preview-container">
          <div v-if="!hasToolpath" class="preview-placeholder">
            <span>{{ hasZGrid ? 'Click Generate to create toolpath' : 'Load a heightmap first' }}</span>
          </div>
          <div v-else class="toolpath-info">
            <div class="stat-grid">
              <div class="stat">
                <span class="stat-value">{{ toolpathStats?.move_count.toLocaleString() }}</span>
                <span class="stat-label">Moves</span>
              </div>
              <div class="stat">
                <span class="stat-value">{{ (toolpathStats?.length_xy || 0).toFixed(1) }}</span>
                <span class="stat-label">Length (mm)</span>
              </div>
              <div class="stat">
                <span class="stat-value">{{ ((toolpathStats?.est_time_s || 0) / 60).toFixed(1) }}</span>
                <span class="stat-label">Est. Time (min)</span>
              </div>
              <div class="stat">
                <span class="stat-value">{{ toolpathStats?.min_z.toFixed(2) }}</span>
                <span class="stat-label">Min Z (mm)</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="panel risk-panel">
        <h2>Risk Analysis {{ isSimulating ? '(Running...)' : '' }}</h2>
        <div class="risk-indicators">
          <div
            v-for="indicator in riskIndicators"
            :key="indicator.label"
            class="risk-item"
            :class="indicator.status"
          >
            <span class="indicator"></span>
            <span class="risk-label">{{ indicator.label }}:</span>
            <span class="risk-message">{{ indicator.message }}</span>
          </div>
        </div>

        <div v-if="simIssues.length > 0" class="issues-list">
          <h3>Issues ({{ simIssues.length }})</h3>
          <ul>
            <li v-for="(issue, i) in simIssues.slice(0, 5)" :key="i" :class="issue.severity">
              {{ issue.type }}: {{ issue.note || `at (${issue.x.toFixed(1)}, ${issue.y.toFixed(1)})` }}
            </li>
            <li v-if="simIssues.length > 5" class="more">
              ... and {{ simIssues.length - 5 }} more
            </li>
          </ul>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.relief-carving-view {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.view-header {
  margin-bottom: 2rem;
}

.view-header h1 {
  font-size: 1.75rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #64748b;
}

.error-banner {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  margin-bottom: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dismiss-btn {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  color: #dc2626;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.panel {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  padding: 1.5rem;
}

.panel h2 {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #1e293b;
}

.upload-zone {
  border: 2px dashed #cbd5e1;
  border-radius: 0.5rem;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 1rem;
}

.upload-zone:hover,
.upload-zone.dragging {
  border-color: #2563eb;
  background: #eff6ff;
}

.upload-zone.has-file {
  border-color: #10b981;
  background: #ecfdf5;
}

.upload-placeholder .icon,
.file-info .icon {
  font-size: 2rem;
  display: block;
  margin-bottom: 0.5rem;
}

.file-info .icon {
  color: #10b981;
}

.filename {
  font-weight: 600;
  color: #1e293b;
}

.upload-placeholder .hint,
.file-info .hint {
  font-size: 0.875rem;
  color: #94a3b8;
}

.grid-stats {
  margin-top: 1rem;
  padding: 0.75rem;
  background: #f8fafc;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.grid-stats p {
  margin: 0.25rem 0;
}

.param-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.param-group label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.875rem;
  color: #475569;
}

.param-group input,
.param-group select {
  padding: 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.toolpath-type {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 1rem;
  padding: 0.75rem;
  background: #f8fafc;
  border-radius: 0.375rem;
}

.toolpath-type label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.875rem;
}

.finishing-params {
  padding: 0.75rem;
  background: #f0f9ff;
  border-radius: 0.375rem;
  margin-bottom: 1rem;
}

.btn-primary,
.btn-secondary {
  width: 100%;
  padding: 0.75rem;
  border: none;
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #2563eb;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled,
.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f1f5f9;
  color: #475569;
  margin-bottom: 0.5rem;
}

.btn-secondary:hover:not(:disabled) {
  background: #e2e8f0;
}

.preview-container {
  aspect-ratio: 4/3;
  background: #f8fafc;
  border-radius: 0.375rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-placeholder {
  color: #94a3b8;
  text-align: center;
  padding: 1rem;
}

.toolpath-info {
  width: 100%;
  padding: 1rem;
}

.stat-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.stat {
  text-align: center;
  padding: 1rem;
  background: white;
  border-radius: 0.375rem;
  border: 1px solid #e2e8f0;
}

.stat-value {
  display: block;
  font-size: 1.5rem;
  font-weight: 700;
  color: #1e293b;
}

.stat-label {
  font-size: 0.75rem;
  color: #64748b;
  text-transform: uppercase;
}

.risk-indicators {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.risk-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  padding: 0.5rem;
  background: #f8fafc;
  border-radius: 0.375rem;
}

.risk-item .indicator {
  width: 0.75rem;
  height: 0.75rem;
  border-radius: 50%;
  flex-shrink: 0;
}

.risk-label {
  font-weight: 500;
}

.risk-message {
  color: #64748b;
  margin-left: auto;
}

.risk-item.safe .indicator { background: #10b981; }
.risk-item.warning .indicator { background: #f59e0b; }
.risk-item.danger .indicator { background: #ef4444; }
.risk-item.pending .indicator { background: #94a3b8; }

.issues-list {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.issues-list h3 {
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.issues-list ul {
  list-style: none;
  padding: 0;
  margin: 0;
  font-size: 0.8125rem;
}

.issues-list li {
  padding: 0.25rem 0;
  color: #64748b;
}

.issues-list li.high,
.issues-list li.critical { color: #dc2626; }
.issues-list li.medium { color: #d97706; }
.issues-list li.more { font-style: italic; }
</style>
