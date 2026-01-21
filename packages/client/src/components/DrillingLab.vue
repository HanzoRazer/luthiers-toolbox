<template>
  <div class="drilling-lab">
    <!-- Header -->
    <div class="lab-header">
      <h2>🔩 Drilling Lab</h2>
      <div class="header-actions">
        <button
          class="btn-primary"
          :disabled="holes.length === 0"
          @click="exportGCode"
        >
          <span class="icon">📥</span> Export G-Code
        </button>
        <button
          class="btn-secondary"
          @click="clearAll"
        >
          <span class="icon">🗑️</span> Clear
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <div class="lab-content">
      <!-- Left Panel -->
      <div class="left-panel">
        <!-- Tool Setup -->
        <section class="panel-section">
          <h3>Tool Setup</h3>
          <div class="tool-type-selector">
            <label
              v-for="tool in toolTypes"
              :key="tool.value"
            >
              <input
                v-model="params.toolType"
                type="radio"
                :value="tool.value"
                @change="updatePreview"
              >
              <span>{{ tool.label }}</span>
            </label>
          </div>

          <div class="form-group">
            <label>Tool Diameter (mm)</label>
            <input
              v-model.number="params.toolDiameter"
              type="number"
              step="0.1"
              min="0.1"
              @input="updatePreview"
            >
          </div>

          <div class="form-group">
            <label>Spindle RPM</label>
            <input
              v-model.number="params.spindleRpm"
              type="number"
              step="100"
              min="100"
              @input="updatePreview"
            >
          </div>

          <div class="form-group">
            <label>Feed Rate (mm/min)</label>
            <input
              v-model.number="params.feedRate"
              type="number"
              step="10"
              min="10"
              @input="updatePreview"
            >
          </div>
        </section>

        <!-- Cycle Type -->
        <section class="panel-section">
          <h3>Cycle Type</h3>
          <div class="cycle-selector">
            <label
              v-for="cycle in cycleTypes"
              :key="cycle.value"
            >
              <input
                v-model="params.cycle"
                type="radio"
                :value="cycle.value"
                @change="updatePreview"
              >
              <span>{{ cycle.label }}</span>
              <small>{{ cycle.description }}</small>
            </label>
          </div>

          <div
            v-if="params.cycle === 'G83'"
            class="form-group"
          >
            <label>Peck Depth (mm)</label>
            <input
              v-model.number="params.peckDepth"
              type="number"
              step="1"
              min="1"
              @input="updatePreview"
            >
          </div>

          <div
            v-if="params.cycle === 'G84'"
            class="form-group"
          >
            <label>Thread Pitch (mm)</label>
            <input
              v-model.number="params.threadPitch"
              type="number"
              step="0.1"
              min="0.1"
              @input="updatePreview"
            >
          </div>
        </section>

        <!-- Depth Settings -->
        <section class="panel-section">
          <h3>Depth Settings</h3>
          <div class="form-group">
            <label>Hole Depth (mm, negative)</label>
            <input
              v-model.number="params.depth"
              type="number"
              step="1"
              max="0"
              @input="updatePreview"
            >
          </div>

          <div class="form-group">
            <label>Retract Plane (mm)</label>
            <input
              v-model.number="params.retract"
              type="number"
              step="1"
              min="0"
              @input="updatePreview"
            >
          </div>

          <div class="form-group">
            <label>Safe Z (mm)</label>
            <input
              v-model.number="params.safeZ"
              type="number"
              step="1"
              min="0"
              @input="updatePreview"
            >
          </div>
        </section>

        <!-- Pattern Generator -->
        <section class="panel-section">
          <h3>Pattern Generator</h3>
          <select
            v-model="patternType"
            class="pattern-selector"
          >
            <option value="manual">
              Manual (Click Canvas)
            </option>
            <option value="linear">
              Linear Array
            </option>
            <option value="circular">
              Circular Pattern
            </option>
            <option value="grid">
              Grid Array
            </option>
            <option value="csv">
              CSV Import
            </option>
          </select>

          <!-- Linear Pattern -->
          <div
            v-if="patternType === 'linear'"
            class="pattern-controls"
          >
            <div class="form-group">
              <label>Direction</label>
              <select v-model="linearPattern.direction">
                <option value="x">
                  Horizontal (X)
                </option>
                <option value="y">
                  Vertical (Y)
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>Start Position</label>
              <div class="input-group">
                <input
                  v-model.number="linearPattern.startX"
                  type="number"
                  step="1"
                  placeholder="X"
                >
                <input
                  v-model.number="linearPattern.startY"
                  type="number"
                  step="1"
                  placeholder="Y"
                >
              </div>
            </div>
            <div class="form-group">
              <label>Spacing (mm)</label>
              <input
                v-model.number="linearPattern.spacing"
                type="number"
                step="1"
                min="1"
              >
            </div>
            <div class="form-group">
              <label>Count</label>
              <input
                v-model.number="linearPattern.count"
                type="number"
                step="1"
                min="1"
              >
            </div>
            <button
              class="btn-generate"
              @click="generateLinearPattern"
            >
              Generate
            </button>
          </div>

          <!-- Circular Pattern -->
          <div
            v-if="patternType === 'circular'"
            class="pattern-controls"
          >
            <div class="form-group">
              <label>Center Position</label>
              <div class="input-group">
                <input
                  v-model.number="circularPattern.centerX"
                  type="number"
                  step="1"
                  placeholder="X"
                >
                <input
                  v-model.number="circularPattern.centerY"
                  type="number"
                  step="1"
                  placeholder="Y"
                >
              </div>
            </div>
            <div class="form-group">
              <label>Radius (mm)</label>
              <input
                v-model.number="circularPattern.radius"
                type="number"
                step="1"
                min="1"
              >
            </div>
            <div class="form-group">
              <label>Count</label>
              <input
                v-model.number="circularPattern.count"
                type="number"
                step="1"
                min="3"
              >
            </div>
            <div class="form-group">
              <label>Start Angle (°)</label>
              <input
                v-model.number="circularPattern.startAngle"
                type="number"
                step="1"
              >
            </div>
            <button
              class="btn-generate"
              @click="generateCircularPattern"
            >
              Generate
            </button>
          </div>

          <!-- Grid Pattern -->
          <div
            v-if="patternType === 'grid'"
            class="pattern-controls"
          >
            <div class="form-group">
              <label>Start Position</label>
              <div class="input-group">
                <input
                  v-model.number="gridPattern.startX"
                  type="number"
                  step="1"
                  placeholder="X"
                >
                <input
                  v-model.number="gridPattern.startY"
                  type="number"
                  step="1"
                  placeholder="Y"
                >
              </div>
            </div>
            <div class="form-group">
              <label>Spacing</label>
              <div class="input-group">
                <input
                  v-model.number="gridPattern.spacingX"
                  type="number"
                  step="1"
                  placeholder="X"
                >
                <input
                  v-model.number="gridPattern.spacingY"
                  type="number"
                  step="1"
                  placeholder="Y"
                >
              </div>
            </div>
            <div class="form-group">
              <label>Grid Size</label>
              <div class="input-group">
                <input
                  v-model.number="gridPattern.countX"
                  type="number"
                  step="1"
                  min="1"
                  placeholder="Cols"
                >
                <input
                  v-model.number="gridPattern.countY"
                  type="number"
                  step="1"
                  min="1"
                  placeholder="Rows"
                >
              </div>
            </div>
            <button
              class="btn-generate"
              @click="generateGridPattern"
            >
              Generate
            </button>
          </div>

          <!-- CSV Import -->
          <div
            v-if="patternType === 'csv'"
            class="pattern-controls"
          >
            <textarea
              v-model="csvInput"
              rows="6"
              placeholder="x,y&#10;10,10&#10;30,10&#10;50,10"
              class="csv-input"
            />
            <button
              class="btn-generate"
              @click="importCsv"
            >
              Import CSV
            </button>
            <small class="hint">Format: x,y (one hole per line)</small>
          </div>
        </section>

        <!-- Hole List -->
        <section class="panel-section hole-list">
          <h3>Holes ({{ holes.length }})</h3>
          <div class="hole-items">
            <div
              v-for="(hole, index) in holes"
              :key="index"
              :class="['hole-item', { selected: selectedHole === index }]"
              @click="selectHole(index)"
            >
              <input
                v-model="hole.enabled"
                type="checkbox"
                @click.stop
                @change="updatePreview"
              >
              <div class="hole-info">
                <strong>H{{ index + 1 }}</strong>
                <small>X{{ hole.x.toFixed(1) }} Y{{ hole.y.toFixed(1) }}</small>
              </div>
              <button
                class="btn-remove"
                @click.stop="removeHole(index)"
              >
                ✕
              </button>
            </div>
          </div>
        </section>

        <!-- Post Processor -->
        <section class="panel-section">
          <h3>Post Processor</h3>
          <select
            v-model="params.postId"
            class="post-selector"
            @change="updatePreview"
          >
            <option value="GRBL">
              GRBL (Expanded)
            </option>
            <option value="LinuxCNC">
              LinuxCNC (Modal)
            </option>
            <option value="Mach4">
              Mach4 (Modal)
            </option>
            <option value="PathPilot">
              PathPilot (Modal)
            </option>
            <option value="Haas">
              Haas (Modal)
            </option>
          </select>
        </section>
      </div>

      <!-- Canvas Preview -->
      <div class="canvas-container">
        <canvas
          ref="canvas"
          width="600"
          height="600"
          @click="onCanvasClick"
          @mousemove="onCanvasHover"
        />

        <!-- Stats Overlay -->
        <div class="stats-overlay">
          <div class="stat">
            <strong>Holes:</strong> {{ enabledHoles.length }}
          </div>
          <div class="stat">
            <strong>Depth:</strong> {{ totalDepth.toFixed(1) }} mm
          </div>
          <div class="stat">
            <strong>Time:</strong> {{ estimatedTime.toFixed(1) }} min
          </div>
        </div>
      </div>
    </div>

    <!-- G-Code Preview (Collapsible) -->
    <div
      class="bottom-panel"
      :class="{ collapsed: gcodeCollapsed }"
    >
      <div
        class="panel-header"
        @click="gcodeCollapsed = !gcodeCollapsed"
      >
        <h3>G-Code Preview</h3>
        <div class="panel-actions">
          <button
            class="btn-icon"
            title="Copy to clipboard"
            @click.stop="copyGCode"
          >
            📋
          </button>
          <button class="btn-icon toggle">
            {{ gcodeCollapsed ? '▲' : '▼' }}
          </button>
        </div>
      </div>
      <div
        v-if="!gcodeCollapsed"
        class="gcode-content"
      >
        <pre>{{ gcodePreview }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'

interface Hole {
  x: number
  y: number
  enabled: boolean
}

// Tool types
const toolTypes = [
  { value: 'drill', label: 'Drill' },
  { value: 'tap', label: 'Tap' },
  { value: 'spot', label: 'Spot Drill' },
  { value: 'boring', label: 'Boring Bar' }
]

// Cycle types
const cycleTypes = [
  { value: 'G81', label: 'G81', description: 'Simple Drill' },
  { value: 'G83', label: 'G83', description: 'Peck Drill' },
  { value: 'G73', label: 'G73', description: 'Chip Break' },
  { value: 'G84', label: 'G84', description: 'Tapping' },
  { value: 'G85', label: 'G85', description: 'Boring' }
]

// State
const params = ref({
  toolType: 'drill',
  toolDiameter: 6.0,
  spindleRpm: 3000,
  feedRate: 300,
  cycle: 'G81',
  depth: -15,
  retract: 2,
  safeZ: 10,
  peckDepth: 5,
  threadPitch: 1.0,
  postId: 'GRBL'
})

const holes = ref<Hole[]>([])
const selectedHole = ref<number | null>(null)
const patternType = ref('manual')

// Pattern generators
const linearPattern = ref({
  direction: 'x',
  startX: 10,
  startY: 10,
  spacing: 20,
  count: 3
})

const circularPattern = ref({
  centerX: 50,
  centerY: 50,
  radius: 30,
  count: 6,
  startAngle: 0
})

const gridPattern = ref({
  startX: 10,
  startY: 10,
  spacingX: 20,
  spacingY: 20,
  countX: 3,
  countY: 2
})

const csvInput = ref('')
const gcodePreview = ref('(No holes defined)')
const gcodeCollapsed = ref(false)

// Canvas
const canvas = ref<HTMLCanvasElement | null>(null)

// Computed
const enabledHoles = computed(() => holes.value.filter(h => h.enabled))

const totalDepth = computed(() => {
  return enabledHoles.value.length * Math.abs(params.value.depth)
})

const estimatedTime = computed(() => {
  const holesCount = enabledHoles.value.length
  if (holesCount === 0) return 0

  // Simple time estimation
  const rapidTime = holesCount * 2 // 2 seconds per hole for rapids
  const drillTime = totalDepth.value / (params.value.feedRate / 60) // depth / feed_per_second

  let peckTime = 0
  if (params.value.cycle === 'G83' && params.value.peckDepth > 0) {
    const pecksPerHole = Math.ceil(Math.abs(params.value.depth) / params.value.peckDepth)
    peckTime = holesCount * pecksPerHole * 1 // 1 second per peck retract
  }

  return (rapidTime + drillTime + peckTime) / 60 // Convert to minutes
})

// Methods
function onCanvasClick(event: MouseEvent) {
  if (patternType.value !== 'manual') return

  const rect = canvas.value!.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top

  // Convert canvas coordinates to mm (canvas is 600×600, representing 100×100mm)
  const mmX = (x / 600) * 100
  const mmY = (y / 600) * 100

  holes.value.push({
    x: Math.round(mmX * 10) / 10,
    y: Math.round(mmY * 10) / 10,
    enabled: true
  })

  updatePreview()
}

function onCanvasHover(event: MouseEvent) {
  if (!canvas.value) return
  // Could add hover preview here
}

function selectHole(index: number) {
  selectedHole.value = index === selectedHole.value ? null : index
}

function removeHole(index: number) {
  holes.value.splice(index, 1)
  if (selectedHole.value === index) {
    selectedHole.value = null
  }
  updatePreview()
}

function clearAll() {
  if (holes.value.length === 0 || confirm('Clear all holes?')) {
    holes.value = []
    selectedHole.value = null
    updatePreview()
  }
}

function generateLinearPattern() {
  holes.value = []
  const { direction, startX, startY, spacing, count } = linearPattern.value

  for (let i = 0; i < count; i++) {
    if (direction === 'x') {
      holes.value.push({
        x: startX + i * spacing,
        y: startY,
        enabled: true
      })
    } else {
      holes.value.push({
        x: startX,
        y: startY + i * spacing,
        enabled: true
      })
    }
  }

  updatePreview()
}

function generateCircularPattern() {
  holes.value = []
  const { centerX, centerY, radius, count, startAngle } = circularPattern.value

  for (let i = 0; i < count; i++) {
    const angle = (startAngle + (360 / count) * i) * (Math.PI / 180)
    holes.value.push({
      x: Math.round((centerX + radius * Math.cos(angle)) * 10) / 10,
      y: Math.round((centerY + radius * Math.sin(angle)) * 10) / 10,
      enabled: true
    })
  }

  updatePreview()
}

function generateGridPattern() {
  holes.value = []
  const { startX, startY, spacingX, spacingY, countX, countY } = gridPattern.value

  for (let row = 0; row < countY; row++) {
    for (let col = 0; col < countX; col++) {
      holes.value.push({
        x: startX + col * spacingX,
        y: startY + row * spacingY,
        enabled: true
      })
    }
  }

  updatePreview()
}

function importCsv() {
  holes.value = []
  const lines = csvInput.value.trim().split('\n')

  for (const line of lines) {
    const [xStr, yStr] = line.split(',').map(s => s.trim())
    const x = parseFloat(xStr)
    const y = parseFloat(yStr)

    if (!isNaN(x) && !isNaN(y)) {
      holes.value.push({ x, y, enabled: true })
    }
  }

  updatePreview()
}

async function updatePreview() {
  drawCanvas()
  await generateGCodePreview()
}

function drawCanvas() {
  if (!canvas.value) return

  const ctx = canvas.value.getContext('2d')
  if (!ctx) return

  const width = 600
  const height = 600

  // Clear
  ctx.clearRect(0, 0, width, height)

  // Background
  ctx.fillStyle = '#f8f9fa'
  ctx.fillRect(0, 0, width, height)

  // Grid
  ctx.strokeStyle = '#dee2e6'
  ctx.lineWidth = 1
  for (let i = 0; i <= 10; i++) {
    const pos = (i / 10) * width
    ctx.beginPath()
    ctx.moveTo(pos, 0)
    ctx.lineTo(pos, height)
    ctx.stroke()
    ctx.beginPath()
    ctx.moveTo(0, pos)
    ctx.lineTo(width, pos)
    ctx.stroke()
  }

  // Draw holes
  holes.value.forEach((hole, index) => {
    const canvasX = (hole.x / 100) * width
    const canvasY = (hole.y / 100) * height

    // Hole circle
    ctx.beginPath()
    ctx.arc(canvasX, canvasY, 8, 0, 2 * Math.PI)
    ctx.fillStyle = hole.enabled ? '#0ea5e9' : '#94a3b8'
    ctx.fill()
    ctx.strokeStyle = selectedHole.value === index ? '#f59e0b' : '#0c4a6e'
    ctx.lineWidth = selectedHole.value === index ? 3 : 2
    ctx.stroke()

    // Label
    ctx.fillStyle = '#1e293b'
    ctx.font = 'bold 12px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(`H${index + 1}`, canvasX, canvasY - 12)
  })

  // Axis labels
  ctx.fillStyle = '#64748b'
  ctx.font = '12px sans-serif'
  ctx.textAlign = 'left'
  ctx.fillText('0 mm', 5, height - 5)
  ctx.textAlign = 'right'
  ctx.fillText('100 mm', width - 5, height - 5)
  ctx.textAlign = 'left'
  ctx.fillText('100 mm', 5, 15)
}

async function generateGCodePreview() {
  if (enabledHoles.value.length === 0) {
    gcodePreview.value = '(No holes defined)'
    return
  }

  try {
    const body = {
      cycle: params.value.cycle,
      holes: enabledHoles.value.map(h => ({ x: h.x, y: h.y })),
      depth: params.value.depth,
      retract: params.value.retract,
      feed: params.value.feedRate,
      safe_z: params.value.safeZ,
      post_id: params.value.postId,
      peck_depth: params.value.cycle === 'G83' ? params.value.peckDepth : undefined,
      thread_pitch: params.value.cycle === 'G84' ? params.value.threadPitch : undefined
    }

    const response = await fetch('/api/cam/drill/gcode', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`)
    }

    const data = await response.json()
    gcodePreview.value = data.gcode || '(Error generating G-code)'
  } catch (err) {
    console.error('G-code preview failed:', err)
    gcodePreview.value = '(Preview error - check console)'
  }
}

async function exportGCode() {
  if (enabledHoles.value.length === 0) {
    alert('No holes to export')
    return
  }

  try {
    const body = {
      cycle: params.value.cycle,
      holes: enabledHoles.value.map(h => ({ x: h.x, y: h.y })),
      depth: params.value.depth,
      retract: params.value.retract,
      feed: params.value.feedRate,
      safe_z: params.value.safeZ,
      post_id: params.value.postId,
      peck_depth: params.value.cycle === 'G83' ? params.value.peckDepth : undefined,
      thread_pitch: params.value.cycle === 'G84' ? params.value.threadPitch : undefined
    }

    const response = await fetch('/api/cam/drill/gcode/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })

    if (!response.ok) {
      throw new Error(`Export failed: ${response.status}`)
    }

    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `drilling_${params.value.cycle}_${enabledHoles.value.length}holes.nc`
    a.click()
    URL.revokeObjectURL(url)
  } catch (err) {
    console.error('Export failed:', err)
    alert('Export failed. Check console for details.')
  }
}

function copyGCode() {
  navigator.clipboard.writeText(gcodePreview.value)
    .then(() => alert('G-code copied to clipboard'))
    .catch(err => console.error('Copy failed:', err))
}

// Lifecycle
onMounted(() => {
  updatePreview()
})

// Watch for parameter changes
watch(params, () => updatePreview(), { deep: true })
</script>

<style scoped>
.drilling-lab {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #ffffff;
}

.lab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 2px solid #e2e8f0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.lab-header h2 {
  margin: 0;
  font-size: 1.5rem;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-primary, .btn-secondary {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s;
}

.btn-primary {
  background: #22c55e;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #16a34a;
}

.btn-primary:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

.btn-secondary {
  background: #ef4444;
  color: white;
}

.btn-secondary:hover {
  background: #dc2626;
}

.lab-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.left-panel {
  width: 350px;
  overflow-y: auto;
  border-right: 2px solid #e2e8f0;
  background: #f8f9fa;
}

.panel-section {
  padding: 1rem;
  border-bottom: 1px solid #e2e8f0;
}

.panel-section h3 {
  margin: 0 0 0.75rem 0;
  font-size: 1rem;
  color: #1e293b;
}

.tool-type-selector, .cycle-selector {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.tool-type-selector label, .cycle-selector label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 4px;
  transition: background 0.2s;
}

.tool-type-selector label:hover, .cycle-selector label:hover {
  background: #e2e8f0;
}

.cycle-selector label {
  flex-direction: column;
  align-items: flex-start;
}

.cycle-selector label small {
  color: #64748b;
  font-size: 0.75rem;
}

.form-group {
  margin-bottom: 0.75rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.25rem;
  font-size: 0.875rem;
  color: #475569;
  font-weight: 500;
}

.form-group input,
.form-group select,
.pattern-selector,
.post-selector {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  font-size: 0.875rem;
}

.input-group {
  display: flex;
  gap: 0.5rem;
}

.input-group input {
  flex: 1;
}

.pattern-controls {
  margin-top: 1rem;
}

.btn-generate {
  width: 100%;
  padding: 0.5rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
  margin-top: 0.5rem;
}

.btn-generate:hover {
  background: #2563eb;
}

.csv-input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.875rem;
  resize: vertical;
}

.hint {
  display: block;
  margin-top: 0.25rem;
  color: #64748b;
  font-size: 0.75rem;
}

.hole-list .hole-items {
  max-height: 300px;
  overflow-y: auto;
}

.hole-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
}

.hole-item:hover {
  background: #e2e8f0;
}

.hole-item.selected {
  background: #dbeafe;
  border: 1px solid #3b82f6;
}

.hole-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.hole-info strong {
  font-size: 0.875rem;
}

.hole-info small {
  color: #64748b;
  font-size: 0.75rem;
}

.btn-remove {
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 0.25rem 0.5rem;
  cursor: pointer;
  font-size: 0.75rem;
}

.btn-remove:hover {
  background: #dc2626;
}

.canvas-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  position: relative;
}

canvas {
  border: 2px solid #cbd5e1;
  border-radius: 8px;
  cursor: crosshair;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.stats-overlay {
  position: absolute;
  top: 2rem;
  right: 2rem;
  background: rgba(255, 255, 255, 0.95);
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.stat {
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}

.stat:last-child {
  margin-bottom: 0;
}

.stat strong {
  color: #1e293b;
}

.bottom-panel {
  border-top: 2px solid #e2e8f0;
  background: #f8f9fa;
  transition: all 0.3s;
}

.bottom-panel.collapsed {
  max-height: 50px;
}

.bottom-panel .panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1.5rem;
  cursor: pointer;
  user-select: none;
}

.bottom-panel .panel-header:hover {
  background: #e2e8f0;
}

.bottom-panel h3 {
  margin: 0;
  font-size: 1rem;
}

.panel-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-icon {
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  transition: background 0.2s;
}

.btn-icon:hover {
  background: #cbd5e1;
}

.gcode-content {
  padding: 1rem 1.5rem;
  max-height: 300px;
  overflow-y: auto;
}

.gcode-content pre {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  line-height: 1.5;
  color: #1e293b;
  white-space: pre-wrap;
}
</style>
