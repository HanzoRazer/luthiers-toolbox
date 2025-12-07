<template>
  <div class="sim-lab">
    <!-- Header -->
    <div class="header">
      <h2 class="title">
        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
        </svg>
        SimLab — Animated G-code Playback
      </h2>
      <div class="subtitle">Visualize, validate, and analyze toolpaths in real-time</div>
    </div>

    <!-- Controls Panel -->
    <div class="controls-panel">
      <div class="control-group">
        <label class="control-label">Safe Z</label>
        <input 
          type="number" 
          v-model.number="safeZ" 
          step="0.1" 
          class="control-input"
          title="Minimum safe Z height for rapids"
        >
        <span class="control-unit">{{ units }}</span>
      </div>

      <div class="control-group">
        <label class="control-label">Units</label>
        <select v-model="units" class="control-select">
          <option value="mm">Millimeters</option>
          <option value="inch">Inches</option>
        </select>
      </div>

      <div class="control-group">
        <label class="control-label">Feed XY</label>
        <input 
          type="number" 
          v-model.number="feedXY" 
          step="100" 
          class="control-input"
          title="XY feedrate"
        >
        <span class="control-unit">{{ units }}/min</span>
      </div>

      <div class="control-group">
        <label class="control-label">Feed Z</label>
        <input 
          type="number" 
          v-model.number="feedZ" 
          step="50" 
          class="control-input"
          title="Z plunge feedrate"
        >
        <span class="control-unit">{{ units }}/min</span>
      </div>
    </div>

    <!-- G-code Input -->
    <div class="gcode-section">
      <div class="section-header">
        <label class="section-title">G-code Input</label>
        <div class="section-actions">
          <button @click="loadSample" class="btn-secondary btn-sm">
            Load Sample
          </button>
          <button @click="clearCode" class="btn-secondary btn-sm">
            Clear
          </button>
          <button @click="pasteFromClipboard" class="btn-secondary btn-sm">
            📋 Paste
          </button>
        </div>
      </div>
      <textarea 
        v-model="gcode" 
        class="gcode-textarea"
        placeholder="Paste G-code here or load a sample..."
        spellcheck="false"
      ></textarea>
      <div class="gcode-stats">
        {{ gcode.split('\n').length }} lines
      </div>
    </div>

    <!-- Simulation Actions -->
    <div class="action-row">
      <button @click="runSimulation" class="btn-primary" :disabled="isSimulating || !gcode.trim()">
        <span v-if="!isSimulating">▶ Run Simulation</span>
        <span v-else>⏳ Simulating...</span>
      </button>
      <button @click="exportCSV" class="btn-secondary" :disabled="!simulationData">
        📥 Export CSV
      </button>
      <button @click="copyToClipboard" class="btn-secondary" :disabled="!simulationData">
        📋 Copy Summary
      </button>
    </div>

    <!-- Summary Cards -->
    <div v-if="summary" class="summary-grid">
      <div class="summary-card">
        <div class="summary-label">Total XY Distance</div>
        <div class="summary-value">{{ summary.total_xy_mm?.toFixed(2) || '0.00' }} mm</div>
      </div>
      <div class="summary-card">
        <div class="summary-label">Total Z Distance</div>
        <div class="summary-value">{{ summary.total_z_mm?.toFixed(2) || '0.00' }} mm</div>
      </div>
      <div class="summary-card">
        <div class="summary-label">Estimated Time</div>
        <div class="summary-value">{{ summary.est_minutes?.toFixed(2) || '0.00' }} min</div>
      </div>
      <div class="summary-card">
        <div class="summary-label">Move Count</div>
        <div class="summary-value">{{ summary.move_count || 0 }}</div>
      </div>
      <div class="summary-card" :class="safety?.safe ? 'safe' : 'unsafe'">
        <div class="summary-label">Safety Status</div>
        <div class="summary-value">
          {{ safety?.safe ? '✓ SAFE' : '⚠ ISSUES' }}
        </div>
      </div>
      <div class="summary-card" :class="issues.length > 0 ? 'warning' : ''">
        <div class="summary-label">Issues</div>
        <div class="summary-value">{{ issues.length }}</div>
      </div>
    </div>

    <!-- Issues Panel -->
    <div v-if="issues.length > 0" class="issues-panel">
      <div class="panel-header">
        <span class="panel-title">⚠ Safety Issues ({{ issues.length }})</span>
        <button @click="showIssuesDetail = !showIssuesDetail" class="btn-link">
          {{ showIssuesDetail ? 'Hide' : 'Show' }} Details
        </button>
      </div>
      <div v-if="showIssuesDetail" class="issues-list">
        <div v-for="issue in issues" :key="issue.index" class="issue-item" :class="issue.severity">
          <div class="issue-badge">{{ issue.severity?.toUpperCase() }}</div>
          <div class="issue-content">
            <div class="issue-type">{{ issue.type }}</div>
            <div class="issue-msg">{{ issue.msg }}</div>
            <div class="issue-meta">Move #{{ issue.index }} | Line {{ issue.line }}</div>
          </div>
          <button @click="jumpToMove(issue.index)" class="btn-link">
            Jump to move
          </button>
        </div>
      </div>
    </div>

    <!-- Playback Controls -->
    <div v-if="moves.length > 0" class="playback-section">
      <div class="playback-controls">
        <button @click="togglePlayback" class="btn-playback">
          <span v-if="!isPlaying">▶</span>
          <span v-else>⏸</span>
        </button>
        <button @click="resetPlayback" class="btn-secondary btn-sm">
          ⏮ Reset
        </button>
        <button @click="stepBackward" class="btn-secondary btn-sm" :disabled="currentFrame === 0">
          ⏪
        </button>
        <button @click="stepForward" class="btn-secondary btn-sm" :disabled="currentFrame >= moves.length - 1">
          ⏩
        </button>
        
        <div class="speed-control">
          <label class="speed-label">Speed</label>
          <input 
            type="range" 
            v-model.number="playbackSpeed" 
            min="0.1" 
            max="10" 
            step="0.1" 
            class="speed-slider"
          >
          <span class="speed-value">{{ playbackSpeed.toFixed(1) }}×</span>
        </div>
      </div>

      <div class="scrubber-section">
        <input 
          type="range" 
          v-model.number="currentFrame" 
          min="0" 
          :max="moves.length - 1" 
          class="scrubber"
          @input="onScrub"
        >
        <div class="scrubber-info">
          <span>Frame {{ currentFrame + 1 }} / {{ moves.length }}</span>
          <span v-if="currentMove">
            {{ currentMove.code }} | 
            X={{ currentMove.x?.toFixed(3) || 0 }} 
            Y={{ currentMove.y?.toFixed(3) || 0 }} 
            Z={{ currentMove.z?.toFixed(3) || 0 }}
          </span>
        </div>
      </div>
    </div>

    <!-- Canvas Visualization -->
    <div class="canvas-section">
      <canvas 
        ref="canvasRef" 
        class="visualization-canvas"
        @mousedown="onCanvasMouseDown"
        @mousemove="onCanvasMouseMove"
        @mouseup="onCanvasMouseUp"
        @wheel="onCanvasWheel"
      ></canvas>
      <div class="canvas-overlay">
        <div class="canvas-legend">
          <div class="legend-item">
            <span class="legend-color rapid"></span>
            <span>G0 (Rapid)</span>
          </div>
          <div class="legend-item">
            <span class="legend-color feed"></span>
            <span>G1 (Feed)</span>
          </div>
          <div class="legend-item">
            <span class="legend-color arc"></span>
            <span>G2/G3 (Arc)</span>
          </div>
        </div>
        <div class="canvas-controls">
          <button @click="resetView" class="btn-canvas">Reset View</button>
          <button @click="fitToCanvas" class="btn-canvas">Fit</button>
          <button @click="toggleGrid" class="btn-canvas">Grid {{ showGrid ? 'On' : 'Off' }}</button>
        </div>
      </div>
    </div>

    <!-- Current Move Info -->
    <div v-if="currentMove" class="move-info-panel">
      <div class="move-info-header">Current Move</div>
      <div class="move-info-grid">
        <div class="move-info-item">
          <span class="move-info-label">Command:</span>
          <span class="move-info-value">{{ currentMove.code }}</span>
        </div>
        <div class="move-info-item">
          <span class="move-info-label">X:</span>
          <span class="move-info-value">{{ currentMove.x?.toFixed(4) || 0 }} {{ units }}</span>
        </div>
        <div class="move-info-item">
          <span class="move-info-label">Y:</span>
          <span class="move-info-value">{{ currentMove.y?.toFixed(4) || 0 }} {{ units }}</span>
        </div>
        <div class="move-info-item">
          <span class="move-info-label">Z:</span>
          <span class="move-info-value">{{ currentMove.z?.toFixed(4) || 0 }} {{ units }}</span>
        </div>
        <div class="move-info-item">
          <span class="move-info-label">Distance XY:</span>
          <span class="move-info-value">{{ currentMove.dxy?.toFixed(3) || 0 }} {{ units }}</span>
        </div>
        <div class="move-info-item">
          <span class="move-info-label">Distance Z:</span>
          <span class="move-info-value">{{ Math.abs(currentMove.dz || 0).toFixed(3) }} {{ units }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

/**
 * SimLab Component (Patch I1 - Enhanced)
 * 
 * Advanced G-code visualization and validation tool with:
 * - Real-time animated playback with variable speed (0.1x-10x)
 * - Interactive canvas with pan/zoom
 * - Safety validation with detailed issue reporting
 * - CSV export for analysis
 * - Frame-by-frame scrubbing
 * - Visual legend and grid overlay
 * 
 * Enhanced Features:
 * - Smooth animations with RAF
 * - Canvas interaction (pan, zoom, reset)
 * - Keyboard shortcuts
 * - Clipboard integration
 * - Sample G-code loader
 * - Responsive layout
 */

// ===== State =====
const gcode = ref<string>('')
const safeZ = ref<number>(5.0)
const units = ref<'mm' | 'inch'>('mm')
const feedXY = ref<number>(1200)
const feedZ = ref<number>(600)

const isSimulating = ref<boolean>(false)
const simulationData = ref<any>(null)
const summary = ref<any>(null)
const safety = ref<any>(null)
const issues = ref<any[]>([])
const moves = ref<any[]>([])

const currentFrame = ref<number>(0)
const isPlaying = ref<boolean>(false)
const playbackSpeed = ref<number>(1.0)
const showIssuesDetail = ref<boolean>(false)
const showGrid = ref<boolean>(true)

// ===== Canvas State =====
const canvasRef = ref<HTMLCanvasElement | null>(null)
let ctx: CanvasRenderingContext2D | null = null
let animationFrameId: number | null = null

const viewState = ref({
  offsetX: 0,
  offsetY: 0,
  scale: 1.0,
  isDragging: false,
  dragStartX: 0,
  dragStartY: 0
})

// ===== Computed =====
const currentMove = computed(() => {
  if (currentFrame.value >= 0 && currentFrame.value < moves.value.length) {
    return moves.value[currentFrame.value]
  }
  return null
})

// ===== Sample G-code =====
const SAMPLE_GCODE = `(Sample Pocket Toolpath)
G0 Z5.0000
G0 X0.0000 Y0.0000
G1 Z-2.0000 F600
G1 X50.0000 Y0.0000 F1200
G1 X50.0000 Y30.0000
G1 X0.0000 Y30.0000
G1 X0.0000 Y0.0000
G0 Z5.0000
G0 X5.0000 Y5.0000
G1 Z-2.0000 F600
G1 X45.0000 Y5.0000 F1200
G1 X45.0000 Y25.0000
G1 X5.0000 Y25.0000
G1 X5.0000 Y5.0000
G0 Z5.0000
M5
M2`

// ===== Lifecycle =====
onMounted(() => {
  initCanvas()
  loadSample()
  setupKeyboardShortcuts()
})

onUnmounted(() => {
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId)
  }
  window.removeEventListener('keydown', handleKeydown)
})

// ===== Canvas Initialization =====
function initCanvas() {
  const canvas = canvasRef.value
  if (!canvas) return

  const dpr = window.devicePixelRatio || 1
  const rect = canvas.getBoundingClientRect()
  
  canvas.width = rect.width * dpr
  canvas.height = rect.height * dpr
  
  ctx = canvas.getContext('2d')
  if (ctx) {
    ctx.scale(dpr, dpr)
    renderCanvas()
  }
}

// ===== Simulation =====
async function runSimulation() {
  if (!gcode.value.trim()) return

  isSimulating.value = true
  
  try {
    const response = await fetch('/api/cam/simulate_gcode', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        gcode: gcode.value,
        safe_z: safeZ.value,
        units: units.value,
        feed_xy: feedXY.value,
        feed_z: feedZ.value
      })
    })

    if (!response.ok) {
      throw new Error(`Simulation failed: ${response.statusText}`)
    }

    simulationData.value = await response.json()
    moves.value = simulationData.value.moves || []
    issues.value = simulationData.value.issues || []
    summary.value = simulationData.value.summary || null
    safety.value = simulationData.value.safety || null

    currentFrame.value = 0
    isPlaying.value = false
    
    fitToCanvas()
    renderCanvas()
    
  } catch (error) {
    console.error('Simulation error:', error)
    alert(`Simulation failed: ${error}`)
  } finally {
    isSimulating.value = false
  }
}

// ===== Export Functions =====
async function exportCSV() {
  if (!simulationData.value) return

  try {
    const response = await fetch('/api/cam/simulate_gcode', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        gcode: gcode.value,
        safe_z: safeZ.value,
        units: units.value,
        as_csv: true
      })
    })

    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'simulation.csv'
    a.click()
    URL.revokeObjectURL(url)
  } catch (error) {
    console.error('CSV export error:', error)
  }
}

async function copyToClipboard() {
  if (!summary.value) return

  const text = `G-code Simulation Summary
Total XY: ${summary.value.total_xy_mm?.toFixed(2)} mm
Total Z: ${summary.value.total_z_mm?.toFixed(2)} mm
Time: ${summary.value.est_minutes?.toFixed(2)} min
Moves: ${summary.value.move_count}
Safety: ${safety.value?.safe ? 'SAFE' : 'ISSUES DETECTED'}
Issues: ${issues.value.length}`

  try {
    await navigator.clipboard.writeText(text)
    alert('Summary copied to clipboard!')
  } catch (error) {
    console.error('Copy failed:', error)
  }
}

async function pasteFromClipboard() {
  try {
    const text = await navigator.clipboard.readText()
    if (text) {
      gcode.value = text
    }
  } catch (error) {
    console.error('Paste failed:', error)
  }
}

// ===== Playback Controls =====
function togglePlayback() {
  isPlaying.value = !isPlaying.value
  
  if (isPlaying.value) {
    animate()
  } else if (animationFrameId) {
    cancelAnimationFrame(animationFrameId)
    animationFrameId = null
  }
}

function animate() {
  if (!isPlaying.value) return

  const step = Math.max(1, Math.floor(playbackSpeed.value))
  currentFrame.value = Math.min(moves.value.length - 1, currentFrame.value + step)

  renderCanvas()

  if (currentFrame.value >= moves.value.length - 1) {
    isPlaying.value = false
    return
  }

  animationFrameId = requestAnimationFrame(animate)
}

function resetPlayback() {
  currentFrame.value = 0
  isPlaying.value = false
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId)
    animationFrameId = null
  }
  renderCanvas()
}

function stepForward() {
  if (currentFrame.value < moves.value.length - 1) {
    currentFrame.value++
    renderCanvas()
  }
}

function stepBackward() {
  if (currentFrame.value > 0) {
    currentFrame.value--
    renderCanvas()
  }
}

function jumpToMove(index: number) {
  currentFrame.value = Math.max(0, Math.min(moves.value.length - 1, index))
  renderCanvas()
}

function onScrub() {
  if (isPlaying.value) {
    isPlaying.value = false
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId)
      animationFrameId = null
    }
  }
  renderCanvas()
}

// ===== Canvas Rendering =====
function renderCanvas() {
  if (!ctx || !canvasRef.value) return

  const canvas = canvasRef.value
  const width = canvas.clientWidth
  const height = canvas.clientHeight

  // Clear
  ctx.clearRect(0, 0, width, height)

  // Background
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, width, height)

  // Grid
  if (showGrid.value) {
    drawGrid(ctx, width, height)
  }

  // Transform
  ctx.save()
  ctx.translate(viewState.value.offsetX, viewState.value.offsetY)
  ctx.scale(viewState.value.scale, viewState.value.scale)

  // Draw toolpath
  drawToolpath(ctx)

  ctx.restore()
}

function drawGrid(ctx: CanvasRenderingContext2D, width: number, height: number) {
  ctx.strokeStyle = '#f0f0f0'
  ctx.lineWidth = 1

  const gridSize = 50 * viewState.value.scale
  const offsetX = viewState.value.offsetX % gridSize
  const offsetY = viewState.value.offsetY % gridSize

  for (let x = offsetX; x < width; x += gridSize) {
    ctx.beginPath()
    ctx.moveTo(x, 0)
    ctx.lineTo(x, height)
    ctx.stroke()
  }

  for (let y = offsetY; y < height; y += gridSize) {
    ctx.beginPath()
    ctx.moveTo(0, y)
    ctx.lineTo(width, y)
    ctx.stroke()
  }
}

function drawToolpath(ctx: CanvasRenderingContext2D) {
  if (moves.value.length === 0) return

  let prevX = 0, prevY = 0

  for (let i = 0; i <= currentFrame.value && i < moves.value.length; i++) {
    const move = moves.value[i]
    const x = move.x ?? prevX
    const y = move.y ?? prevY
    const code = move.code || 'G1'

    // Color by move type
    if (code === 'G0') {
      ctx.strokeStyle = '#ef4444' // Red for rapids
    } else if (code === 'G2' || code === 'G3') {
      ctx.strokeStyle = '#8b5cf6' // Purple for arcs
    } else {
      ctx.strokeStyle = '#3b82f6' // Blue for feeds
    }

    ctx.lineWidth = 2
    ctx.beginPath()
    ctx.moveTo(prevX, prevY)
    ctx.lineTo(x, y)
    ctx.stroke()

    prevX = x
    prevY = y
  }

  // Draw tool position
  if (currentMove.value) {
    const x = currentMove.value.x ?? 0
    const y = currentMove.value.y ?? 0
    
    ctx.fillStyle = '#10b981' // Green
    ctx.beginPath()
    ctx.arc(x, y, 4 / viewState.value.scale, 0, Math.PI * 2)
    ctx.fill()
  }
}

function fitToCanvas() {
  if (moves.value.length === 0 || !canvasRef.value) return

  const xs = moves.value.map(m => m.x ?? 0)
  const ys = moves.value.map(m => m.y ?? 0)
  
  const minX = Math.min(...xs)
  const maxX = Math.max(...xs)
  const minY = Math.min(...ys)
  const maxY = Math.max(...ys)

  const width = maxX - minX
  const height = maxY - minY

  const canvas = canvasRef.value
  const padding = 40

  const scaleX = (canvas.clientWidth - padding * 2) / width
  const scaleY = (canvas.clientHeight - padding * 2) / height
  
  viewState.value.scale = Math.min(scaleX, scaleY, 5)
  viewState.value.offsetX = padding - minX * viewState.value.scale
  viewState.value.offsetY = padding - minY * viewState.value.scale

  renderCanvas()
}

function resetView() {
  viewState.value.offsetX = 0
  viewState.value.offsetY = 0
  viewState.value.scale = 1.0
  renderCanvas()
}

function toggleGrid() {
  showGrid.value = !showGrid.value
  renderCanvas()
}

// ===== Canvas Interaction =====
function onCanvasMouseDown(e: MouseEvent) {
  viewState.value.isDragging = true
  viewState.value.dragStartX = e.clientX - viewState.value.offsetX
  viewState.value.dragStartY = e.clientY - viewState.value.offsetY
}

function onCanvasMouseMove(e: MouseEvent) {
  if (!viewState.value.isDragging) return

  viewState.value.offsetX = e.clientX - viewState.value.dragStartX
  viewState.value.offsetY = e.clientY - viewState.value.dragStartY
  
  renderCanvas()
}

function onCanvasMouseUp() {
  viewState.value.isDragging = false
}

function onCanvasWheel(e: WheelEvent) {
  e.preventDefault()
  
  const delta = e.deltaY > 0 ? 0.9 : 1.1
  const newScale = viewState.value.scale * delta
  
  if (newScale >= 0.1 && newScale <= 10) {
    viewState.value.scale = newScale
    renderCanvas()
  }
}

// ===== Utility Functions =====
function loadSample() {
  gcode.value = SAMPLE_GCODE
}

function clearCode() {
  gcode.value = ''
  simulationData.value = null
  moves.value = []
  issues.value = []
  summary.value = null
  safety.value = null
  currentFrame.value = 0
  renderCanvas()
}

function setupKeyboardShortcuts() {
  window.addEventListener('keydown', handleKeydown)
}

function handleKeydown(e: KeyboardEvent) {
  if (e.target instanceof HTMLTextAreaElement || e.target instanceof HTMLInputElement) {
    return
  }

  switch (e.key) {
    case ' ':
      e.preventDefault()
      if (moves.value.length > 0) {
        togglePlayback()
      }
      break
    case 'ArrowLeft':
      e.preventDefault()
      stepBackward()
      break
    case 'ArrowRight':
      e.preventDefault()
      stepForward()
      break
    case 'r':
    case 'R':
      if (e.ctrlKey || e.metaKey) {
        e.preventDefault()
        resetPlayback()
      }
      break
  }
}

// ===== Watchers =====
watch(currentFrame, () => {
  renderCanvas()
})
</script>

<style scoped>
.sim-lab {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* Header */
.header {
  margin-bottom: 24px;
}

.title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 24px;
  font-weight: 700;
  color: #111827;
  margin: 0 0 8px 0;
}

.icon {
  width: 32px;
  height: 32px;
  color: #3b82f6;
}

.subtitle {
  color: #6b7280;
  font-size: 14px;
}

/* Controls Panel */
.controls-panel {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
  margin-bottom: 20px;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.control-label {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  min-width: 60px;
}

.control-input {
  flex: 1;
  padding: 6px 10px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 14px;
}

.control-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.control-select {
  flex: 1;
  padding: 6px 10px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 14px;
  background: white;
}

.control-unit {
  font-size: 12px;
  color: #6b7280;
  min-width: 50px;
}

/* G-code Section */
.gcode-section {
  margin-bottom: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.section-actions {
  display: flex;
  gap: 8px;
}

.gcode-textarea {
  width: 100%;
  height: 200px;
  padding: 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  resize: vertical;
}

.gcode-textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.gcode-stats {
  margin-top: 4px;
  font-size: 12px;
  color: #6b7280;
}

/* Action Row */
.action-row {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

/* Buttons */
.btn-primary {
  padding: 10px 20px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-primary:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 10px 20px;
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-secondary:hover:not(:disabled) {
  background: #e5e7eb;
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 13px;
}

.btn-link {
  background: none;
  border: none;
  color: #3b82f6;
  cursor: pointer;
  font-size: 13px;
  text-decoration: underline;
}

.btn-link:hover {
  color: #2563eb;
}

/* Summary Grid */
.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}

.summary-card {
  padding: 16px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.summary-card.safe {
  background: #ecfdf5;
  border-color: #10b981;
}

.summary-card.unsafe {
  background: #fef2f2;
  border-color: #ef4444;
}

.summary-card.warning {
  background: #fffbeb;
  border-color: #f59e0b;
}

.summary-label {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.summary-value {
  font-size: 20px;
  font-weight: 700;
  color: #111827;
}

/* Issues Panel */
.issues-panel {
  background: #fffbeb;
  border: 1px solid #fbbf24;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #92400e;
}

.issues-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.issue-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  background: white;
  border-radius: 6px;
}

.issue-item.error {
  border-left: 3px solid #ef4444;
}

.issue-item.warning {
  border-left: 3px solid #f59e0b;
}

.issue-badge {
  padding: 2px 8px;
  background: #fbbf24;
  color: #92400e;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
}

.issue-item.error .issue-badge {
  background: #ef4444;
  color: white;
}

.issue-content {
  flex: 1;
}

.issue-type {
  font-size: 13px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 4px;
}

.issue-msg {
  font-size: 13px;
  color: #374151;
  margin-bottom: 4px;
}

.issue-meta {
  font-size: 12px;
  color: #6b7280;
}

/* Playback Section */
.playback-section {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
}

.playback-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.btn-playback {
  width: 48px;
  height: 48px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 50%;
  font-size: 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.btn-playback:hover {
  background: #2563eb;
}

.speed-control {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.speed-label {
  font-size: 13px;
  color: #374151;
  font-weight: 500;
}

.speed-slider {
  width: 150px;
}

.speed-value {
  font-size: 13px;
  font-weight: 600;
  color: #111827;
  min-width: 40px;
}

/* Scrubber */
.scrubber-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.scrubber {
  width: 100%;
  height: 8px;
  -webkit-appearance: none;
  appearance: none;
  background: #e5e7eb;
  border-radius: 4px;
  outline: none;
}

.scrubber::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  background: #3b82f6;
  border-radius: 50%;
  cursor: pointer;
}

.scrubber::-moz-range-thumb {
  width: 20px;
  height: 20px;
  background: #3b82f6;
  border-radius: 50%;
  cursor: pointer;
  border: none;
}

.scrubber-info {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #6b7280;
}

/* Canvas Section */
.canvas-section {
  position: relative;
  margin-bottom: 20px;
}

.visualization-canvas {
  width: 100%;
  height: 500px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  cursor: move;
}

.canvas-overlay {
  position: absolute;
  top: 12px;
  left: 12px;
  right: 12px;
  display: flex;
  justify-content: space-between;
  pointer-events: none;
}

.canvas-legend {
  background: rgba(255, 255, 255, 0.95);
  padding: 12px;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  pointer-events: auto;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 12px;
}

.legend-item:last-child {
  margin-bottom: 0;
}

.legend-color {
  width: 20px;
  height: 3px;
  border-radius: 2px;
}

.legend-color.rapid {
  background: #ef4444;
}

.legend-color.feed {
  background: #3b82f6;
}

.legend-color.arc {
  background: #8b5cf6;
}

.canvas-controls {
  display: flex;
  gap: 8px;
  pointer-events: auto;
}

.btn-canvas {
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.btn-canvas:hover {
  background: white;
}

/* Move Info Panel */
.move-info-panel {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
}

.move-info-header {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 12px;
}

.move-info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
}

.move-info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.move-info-label {
  font-size: 12px;
  color: #6b7280;
}

.move-info-value {
  font-size: 13px;
  font-weight: 600;
  color: #111827;
  font-family: 'Courier New', monospace;
}

/* Responsive */
@media (max-width: 768px) {
  .controls-panel {
    grid-template-columns: 1fr;
  }
  
  .summary-grid {
    grid-template-columns: 1fr;
  }
  
  .playback-controls {
    flex-wrap: wrap;
  }
  
  .speed-control {
    width: 100%;
    margin-left: 0;
  }
}
</style>
