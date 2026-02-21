<template>
  <div :class="styles.drillingLab">
    <!-- Header -->
    <div :class="styles.labHeader">
      <h2>Drilling Lab</h2>
      <div :class="styles.headerActions">
        <button
          :class="styles.btnPrimary"
          :disabled="holes.length === 0"
          @click="exportGCode"
        >
          Export G-Code
        </button>
        <button
          :class="styles.btnSecondary"
          @click="clearAll"
        >
          Clear
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <div :class="styles.labContent">
      <!-- Left Panel -->
      <div :class="styles.leftPanel">
        <!-- Tool Setup -->
        <DrillToolSetup
          :styles="styles"
          v-model:tool-type="params.toolType"
          v-model:tool-diameter="params.toolDiameter"
          v-model:spindle-rpm="params.spindleRpm"
          v-model:feed-rate="params.feedRate"
          @update:tool-type="updatePreview"
          @update:tool-diameter="updatePreview"
          @update:spindle-rpm="updatePreview"
          @update:feed-rate="updatePreview"
        />

        <!-- Cycle Type -->
        <DrillCycleType
          :styles="styles"
          v-model:cycle-value="params.cycle"
          v-model:peck-depth="params.peckDepth"
          v-model:thread-pitch="params.threadPitch"
          @update:cycle-value="updatePreview"
          @update:peck-depth="updatePreview"
          @update:thread-pitch="updatePreview"
        />

        <!-- Depth Settings -->
        <DrillDepthSettings
          :styles="styles"
          v-model:depth="params.depth"
          v-model:retract="params.retract"
          v-model:safe-z="params.safeZ"
          @update:depth="updatePreview"
          @update:retract="updatePreview"
          @update:safe-z="updatePreview"
        />

        <!-- Pattern Generator -->
        <DrillPatternSelector
          :styles="styles"
          v-model:pattern-type="patternType"
          v-model:csv-input="csvInput"
          :linear-pattern="linearPattern"
          :circular-pattern="circularPattern"
          :grid-pattern="gridPattern"
          @generate-linear="generateLinearPattern"
          @generate-circular="generateCircularPattern"
          @generate-grid="generateGridPattern"
          @import-csv="importCsv"
        />

        <!-- Hole List -->
        <DrillHoleList
          :styles="styles"
          :holes="holes"
          :selected-hole="selectedHole"
          @select-hole="selectHole"
          @remove-hole="removeHole"
          @toggle-hole="toggleHole"
        />

        <!-- Post Processor -->
        <section :class="styles.panelSection">
          <h3>Post Processor</h3>
          <select
            v-model="params.postId"
            :class="styles.postSelector"
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
      <div :class="styles.canvasContainer">
        <canvas
          ref="canvas"
          width="600"
          height="600"
          @click="onCanvasClick"
          @mousemove="onCanvasHover"
        />

        <!-- Stats Overlay -->
        <div :class="styles.statsOverlay">
          <div :class="styles.stat">
            <strong>Holes:</strong> {{ enabledHoles.length }}
          </div>
          <div :class="styles.stat">
            <strong>Depth:</strong> {{ totalDepth.toFixed(1) }} mm
          </div>
          <div :class="styles.stat">
            <strong>Time:</strong> {{ estimatedTime.toFixed(1) }} min
          </div>
        </div>
      </div>
    </div>

    <!-- G-Code Preview (Collapsible) -->
    <div
      :class="[styles.bottomPanel, { [styles.bottomPanelCollapsed]: gcodeCollapsed }]"
    >
      <div
        :class="styles.panelHeader"
        @click="gcodeCollapsed = !gcodeCollapsed"
      >
        <h3>G-Code Preview</h3>
        <div :class="styles.panelActions">
          <button
            :class="styles.btnIcon"
            title="Copy to clipboard"
            @click.stop="copyGCode"
          >
            Copy
          </button>
          <button :class="styles.btnIcon">
            {{ gcodeCollapsed ? '▲' : '▼' }}
          </button>
        </div>
      </div>
      <div
        v-if="!gcodeCollapsed"
        :class="styles.gcodeContent"
      >
        <pre>{{ gcodePreview }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { api } from '@/services/apiBase';
import { ref, computed, onMounted, watch } from 'vue'
import styles from './DrillingLab.module.css'
import DrillToolSetup from './drilling/DrillToolSetup.vue'
import DrillCycleType from './drilling/DrillCycleType.vue'
import DrillDepthSettings from './drilling/DrillDepthSettings.vue'
import DrillPatternSelector from './drilling/DrillPatternSelector.vue'
import DrillHoleList from './drilling/DrillHoleList.vue'

interface Hole {
  x: number
  y: number
  enabled: boolean
}

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

function toggleHole(index: number, enabled: boolean) {
  holes.value[index].enabled = enabled
  updatePreview()
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

    const response = await api('/api/cam/drilling/gcode', {
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

    const response = await api('/api/cam/drilling/gcode/download', {
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
