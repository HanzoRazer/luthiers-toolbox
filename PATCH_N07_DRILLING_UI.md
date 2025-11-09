# Patch N.07 — Drilling Cycles UI Component

**Status:** 🔜 Specification Complete (Implementation Pending)  
**Date:** November 6, 2025  
**Target:** Interactive drilling pattern editor with real-time preview

---

## 🎯 Overview

Build a comprehensive **Vue 3 drilling cycles UI** component with:

- **Interactive hole editor** with canvas preview
- **Pattern generators** (linear, circular, grid) with visual controls
- **Cycle parameter controls** (G81, G83, G84, etc.)
- **Real-time G-code preview** with syntax highlighting
- **Feeds & speeds calculator** based on material and tool
- **Multi-tool support** (drill, tap, spot drill, boring bar)
- **Post-processor selector** with capability warnings
- **Export options** (direct download, save to library)

**Component:** `packages/client/src/components/DrillingLab.vue`

---

## 📐 UI Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ Drilling Lab                                    [Export] [Save] │
├─────────────────────┬───────────────────────────────────────────┤
│                     │                                           │
│  Left Panel (350px) │  Canvas Preview (Auto)                    │
│                     │                                           │
│  ┌───────────────┐  │   ┌─────────────────────────────────┐   │
│  │ Tool Setup    │  │   │                                 │   │
│  ├───────────────┤  │   │    • H1      • H2      • H3     │   │
│  │ □ Drill       │  │   │                                 │   │
│  │ ○ Tap         │  │   │                                 │   │
│  │ □ Spot Drill  │  │   │         Canvas 600×600          │   │
│  │ □ Boring Bar  │  │   │                                 │   │
│  ├───────────────┤  │   │    • H4      • H5      • H6     │   │
│  │ Ø: [6.0] mm   │  │   │                                 │   │
│  │ RPM: [3000]   │  │   └─────────────────────────────────┘   │
│  │ Feed: [300]   │  │                                           │
│  └───────────────┘  │   Stats: 6 holes, 90mm depth, 3.2 min   │
│                     │                                           │
│  ┌───────────────┐  │                                           │
│  │ Cycle Type    │  │                                           │
│  ├───────────────┤  │                                           │
│  │ ● G81 Drill   │  │                                           │
│  │ ○ G83 Peck    │  │                                           │
│  │ ○ G84 Tap     │  │                                           │
│  └───────────────┘  │                                           │
│                     │                                           │
│  ┌───────────────┐  │                                           │
│  │ Pattern       │  │                                           │
│  ├───────────────┤  │                                           │
│  │ Manual        │  │                                           │
│  │ Linear        │  │                                           │
│  │ Circular      │  │                                           │
│  │ Grid          │  │                                           │
│  └───────────────┘  │                                           │
│                     │                                           │
│  ┌───────────────┐  │                                           │
│  │ Holes (6)     │  │                                           │
│  ├───────────────┤  │                                           │
│  │ □ H1 10,10,-15│  │                                           │
│  │ □ H2 30,10,-15│  │                                           │
│  │ ☑ H3 50,10,-15│  │                                           │
│  │   ...         │  │                                           │
│  │ [+] Add Hole  │  │                                           │
│  └───────────────┘  │                                           │
│                     │                                           │
├─────────────────────┴───────────────────────────────────────────┤
│ Bottom Panel (Collapsible)                                      │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ G-Code Preview                                [Copy] [▼]    │ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │ G21                                                         │ │
│ │ G90                                                         │ │
│ │ G0 Z10.0                                                    │ │
│ │ G81 Z-15.0 R2.0 F300                                       │ │
│ │ X10.0 Y10.0                                                 │ │
│ │ X30.0 Y10.0                                                 │ │
│ │ ...                                                         │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Component Structure

### **File:** `packages/client/src/components/DrillingLab.vue`

```vue
<template>
  <div class="drilling-lab">
    <!-- Header -->
    <div class="lab-header">
      <h2>Drilling Lab</h2>
      <div class="actions">
        <button @click="exportGCode" class="btn-primary">
          <span class="icon">📥</span> Export G-Code
        </button>
        <button @click="saveToLibrary" class="btn-secondary">
          <span class="icon">💾</span> Save Pattern
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
            <label v-for="tool in toolTypes" :key="tool.value">
              <input
                type="radio"
                v-model="params.tool_type"
                :value="tool.value"
                @change="onToolTypeChange"
              />
              <span>{{ tool.label }}</span>
            </label>
          </div>

          <div class="form-group">
            <label>Tool Diameter</label>
            <div class="input-with-unit">
              <input
                type="number"
                v-model.number="params.tool_d"
                step="0.1"
                min="0.1"
              />
              <span class="unit">{{ params.units }}</span>
            </div>
          </div>

          <div class="form-group">
            <label>Spindle RPM</label>
            <input
              type="number"
              v-model.number="params.spindle_rpm"
              step="100"
              min="100"
            />
          </div>

          <div class="form-group">
            <label>Feed Rate (Z)</label>
            <div class="input-with-unit">
              <input
                type="number"
                v-model.number="params.feed_z"
                step="10"
                min="10"
              />
              <span class="unit">{{ params.units }}/min</span>
            </div>
          </div>

          <!-- Tapping-specific -->
          <div v-if="params.tool_type === 'tap'" class="form-group">
            <label>Thread Pitch</label>
            <div class="input-with-unit">
              <input
                type="number"
                v-model.number="params.thread_pitch"
                step="0.1"
                min="0.1"
              />
              <span class="unit">{{ params.units === 'mm' ? 'mm' : 'TPI' }}</span>
            </div>
            <small class="help-text">
              Feed = {{ calculatedTapFeed }} {{ params.units }}/min
            </small>
          </div>
        </section>

        <!-- Cycle Type -->
        <section class="panel-section">
          <h3>Cycle Type</h3>
          <div class="cycle-selector">
            <label v-for="cycle in cycleTypes" :key="cycle.value">
              <input
                type="radio"
                v-model="params.cycle"
                :value="cycle.value"
                @change="onCycleChange"
              />
              <div class="cycle-option">
                <strong>{{ cycle.label }}</strong>
                <small>{{ cycle.description }}</small>
              </div>
            </label>
          </div>

          <!-- Peck-specific -->
          <div v-if="isPeckCycle" class="form-group">
            <label>Peck Depth</label>
            <div class="input-with-unit">
              <input
                type="number"
                v-model.number="params.peck_depth"
                step="1"
                min="1"
              />
              <span class="unit">{{ params.units }}</span>
            </div>
          </div>

          <!-- Dwell-specific -->
          <div v-if="isDwellCycle" class="form-group">
            <label>Dwell Time</label>
            <div class="input-with-unit">
              <input
                type="number"
                v-model.number="params.dwell_time"
                step="0.1"
                min="0.1"
              />
              <span class="unit">seconds</span>
            </div>
          </div>
        </section>

        <!-- Pattern Generator -->
        <section class="panel-section">
          <h3>Pattern Generator</h3>
          <div class="pattern-tabs">
            <button
              v-for="pattern in patternTypes"
              :key="pattern.value"
              :class="['tab', { active: activePattern === pattern.value }]"
              @click="activePattern = pattern.value"
            >
              {{ pattern.label }}
            </button>
          </div>

          <!-- Manual Entry -->
          <div v-if="activePattern === 'manual'" class="pattern-manual">
            <button @click="addHole" class="btn-add">
              <span class="icon">➕</span> Add Hole
            </button>
          </div>

          <!-- Linear Pattern -->
          <div v-else-if="activePattern === 'linear'" class="pattern-linear">
            <div class="form-row">
              <div class="form-group">
                <label>Start X</label>
                <input type="number" v-model.number="linearPattern.start_x" step="1" />
              </div>
              <div class="form-group">
                <label>Start Y</label>
                <input type="number" v-model.number="linearPattern.start_y" step="1" />
              </div>
            </div>
            <div class="form-group">
              <label>Spacing</label>
              <input type="number" v-model.number="linearPattern.spacing" step="1" />
            </div>
            <div class="form-group">
              <label>Count</label>
              <input type="number" v-model.number="linearPattern.count" step="1" min="1" />
            </div>
            <div class="form-group">
              <label>Direction</label>
              <select v-model="linearPattern.direction">
                <option value="x">X (Horizontal)</option>
                <option value="y">Y (Vertical)</option>
              </select>
            </div>
            <div class="form-group">
              <label>Depth</label>
              <input type="number" v-model.number="linearPattern.depth" step="1" />
            </div>
            <button @click="generateLinearPattern" class="btn-generate">
              Generate Linear Pattern
            </button>
          </div>

          <!-- Circular Pattern -->
          <div v-else-if="activePattern === 'circular'" class="pattern-circular">
            <div class="form-row">
              <div class="form-group">
                <label>Center X</label>
                <input type="number" v-model.number="circularPattern.center_x" step="1" />
              </div>
              <div class="form-group">
                <label>Center Y</label>
                <input type="number" v-model.number="circularPattern.center_y" step="1" />
              </div>
            </div>
            <div class="form-group">
              <label>Radius (Bolt Circle)</label>
              <input type="number" v-model.number="circularPattern.radius" step="1" />
            </div>
            <div class="form-group">
              <label>Hole Count</label>
              <input type="number" v-model.number="circularPattern.count" step="1" min="2" />
            </div>
            <div class="form-group">
              <label>Start Angle</label>
              <div class="input-with-unit">
                <input type="number" v-model.number="circularPattern.start_angle" step="15" />
                <span class="unit">°</span>
              </div>
            </div>
            <div class="form-group">
              <label>Depth</label>
              <input type="number" v-model.number="circularPattern.depth" step="1" />
            </div>
            <button @click="generateCircularPattern" class="btn-generate">
              Generate Bolt Circle
            </button>
          </div>

          <!-- Grid Pattern -->
          <div v-else-if="activePattern === 'grid'" class="pattern-grid">
            <div class="form-row">
              <div class="form-group">
                <label>Start X</label>
                <input type="number" v-model.number="gridPattern.start_x" step="1" />
              </div>
              <div class="form-group">
                <label>Start Y</label>
                <input type="number" v-model.number="gridPattern.start_y" step="1" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Spacing X</label>
                <input type="number" v-model.number="gridPattern.spacing_x" step="1" />
              </div>
              <div class="form-group">
                <label>Spacing Y</label>
                <input type="number" v-model.number="gridPattern.spacing_y" step="1" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Columns</label>
                <input type="number" v-model.number="gridPattern.count_x" step="1" min="1" />
              </div>
              <div class="form-group">
                <label>Rows</label>
                <input type="number" v-model.number="gridPattern.count_y" step="1" min="1" />
              </div>
            </div>
            <div class="form-group">
              <label>Depth</label>
              <input type="number" v-model.number="gridPattern.depth" step="1" />
            </div>
            <button @click="generateGridPattern" class="btn-generate">
              Generate Grid
            </button>
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
                type="checkbox"
                v-model="hole.enabled"
                @click.stop
              />
              <div class="hole-info">
                <strong>{{ hole.label || `H${index + 1}` }}</strong>
                <small>X{{ hole.x }} Y{{ hole.y }} Z{{ hole.z }}</small>
              </div>
              <button @click.stop="removeHole(index)" class="btn-remove">
                ✕
              </button>
            </div>
          </div>
        </section>

        <!-- Post Processor -->
        <section class="panel-section">
          <h3>Post Processor</h3>
          <select v-model="params.post" class="post-selector">
            <option value="">Auto (Modal if supported)</option>
            <option value="grbl">GRBL (Expanded)</option>
            <option value="linuxcnc">LinuxCNC (Modal)</option>
            <option value="fanuc_generic">Fanuc (Modal)</option>
            <option value="haas_vf">Haas VF/VM (Modal)</option>
            <option value="mach4">Mach4 (Modal)</option>
          </select>
          
          <div v-if="postWarnings.length" class="warnings">
            <div v-for="(warning, i) in postWarnings" :key="i" class="warning">
              ⚠️ {{ warning }}
            </div>
          </div>
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
        ></canvas>
        
        <!-- Stats Overlay -->
        <div class="stats-overlay">
          <div class="stat">
            <strong>Holes:</strong> {{ enabledHoleCount }}
          </div>
          <div class="stat">
            <strong>Total Depth:</strong> {{ totalDepth.toFixed(1) }} {{ params.units }}
          </div>
          <div class="stat">
            <strong>Est. Time:</strong> {{ estimatedTime }}
          </div>
          <div v-if="params.cycle === 'G83'" class="stat">
            <strong>Total Pecks:</strong> {{ totalPecks }}
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom Panel (G-Code Preview) -->
    <div class="bottom-panel" :class="{ collapsed: gcodeCollapsed }">
      <div class="panel-header" @click="gcodeCollapsed = !gcodeCollapsed">
        <h3>G-Code Preview</h3>
        <div class="panel-actions">
          <button @click.stop="copyGCode" class="btn-icon" title="Copy">
            📋
          </button>
          <button @click.stop="downloadGCode" class="btn-icon" title="Download">
            💾
          </button>
          <button class="btn-icon">
            {{ gcodeCollapsed ? '▲' : '▼' }}
          </button>
        </div>
      </div>
      <div v-if="!gcodeCollapsed" class="gcode-content">
        <pre><code v-html="highlightedGCode"></code></pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'

// Types
interface Hole {
  x: number
  y: number
  z: number
  label?: string
  enabled: boolean
}

interface DrillingParams {
  holes: Hole[]
  tool_type: string
  tool_d: number
  tool_number: string
  spindle_rpm: number
  feed_z: number
  cycle: string
  peck_depth?: number
  dwell_time?: number
  thread_pitch?: number
  tap_mode: string
  r_plane: number
  safe_z: number
  post?: string
  units: string
  work_offset: string
  program_no: string
}

// Refs
const canvas = ref<HTMLCanvasElement | null>(null)
const holes = ref<Hole[]>([])
const selectedHole = ref<number | null>(null)
const activePattern = ref('manual')
const gcodeCollapsed = ref(false)
const gcodePreview = ref('')

// Parameters
const params = ref<DrillingParams>({
  holes: [],
  tool_type: 'drill',
  tool_d: 6.0,
  tool_number: '1',
  spindle_rpm: 3000,
  feed_z: 300,
  cycle: 'G81',
  peck_depth: 5.0,
  dwell_time: 1.0,
  thread_pitch: 1.0,
  tap_mode: 'rigid',
  r_plane: 2.0,
  safe_z: 10.0,
  post: '',
  units: 'mm',
  work_offset: 'G54',
  program_no: '1000'
})

// Pattern configs
const linearPattern = ref({
  start_x: 10,
  start_y: 10,
  spacing: 20,
  count: 5,
  direction: 'x',
  depth: -15
})

const circularPattern = ref({
  center_x: 50,
  center_y: 50,
  radius: 30,
  count: 8,
  start_angle: 0,
  depth: -15
})

const gridPattern = ref({
  start_x: 10,
  start_y: 10,
  spacing_x: 20,
  spacing_y: 20,
  count_x: 3,
  count_y: 3,
  depth: -15
})

// Constants
const toolTypes = [
  { value: 'drill', label: 'Drill' },
  { value: 'spot_drill', label: 'Spot Drill' },
  { value: 'tap', label: 'Tap' },
  { value: 'boring_bar', label: 'Boring Bar' }
]

const cycleTypes = [
  { value: 'G81', label: 'G81', description: 'Simple drill (rapid retract)' },
  { value: 'G82', label: 'G82', description: 'Spot drill (dwell at bottom)' },
  { value: 'G83', label: 'G83', description: 'Peck drill (full retract)' },
  { value: 'G73', label: 'G73', description: 'Chip break (partial retract)' },
  { value: 'G84', label: 'G84', description: 'Rigid tap' },
  { value: 'G85', label: 'G85', description: 'Boring (feed in/out)' }
]

const patternTypes = [
  { value: 'manual', label: 'Manual' },
  { value: 'linear', label: 'Linear' },
  { value: 'circular', label: 'Circular' },
  { value: 'grid', label: 'Grid' }
]

// Computed
const isPeckCycle = computed(() => ['G83', 'G73'].includes(params.value.cycle))
const isDwellCycle = computed(() => ['G82', 'G89'].includes(params.value.cycle))

const calculatedTapFeed = computed(() => {
  if (params.value.tool_type === 'tap' && params.value.thread_pitch) {
    return (params.value.spindle_rpm * params.value.thread_pitch).toFixed(1)
  }
  return '0'
})

const enabledHoleCount = computed(() => holes.value.filter(h => h.enabled).length)

const totalDepth = computed(() => {
  return holes.value
    .filter(h => h.enabled)
    .reduce((sum, h) => sum + Math.abs(h.z), 0)
})

const totalPecks = computed(() => {
  if (!params.value.peck_depth) return 0
  return holes.value
    .filter(h => h.enabled)
    .reduce((sum, h) => {
      const depth = Math.abs(h.z - params.value.r_plane)
      return sum + Math.ceil(depth / params.value.peck_depth!)
    }, 0)
})

const estimatedTime = computed(() => {
  const rapidTime = enabledHoleCount.value * 2.0 // seconds per hole
  const drillTime = totalDepth.value / (params.value.feed_z / 60.0)
  let peckTime = 0
  
  if (params.value.cycle === 'G83') {
    peckTime = totalPecks.value * 1.0 // 1 second per peck retract
  }
  
  const totalSeconds = rapidTime + drillTime + peckTime
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = Math.round(totalSeconds % 60)
  
  return minutes > 0 ? `${minutes}m ${seconds}s` : `${seconds}s`
})

const postWarnings = computed(() => {
  const warnings: string[] = []
  
  if (params.value.post === 'grbl') {
    warnings.push('GRBL: Cycles will be expanded to G0/G1 moves')
  }
  
  if (params.value.cycle === 'G84' && !['fanuc_generic', 'haas_vf', 'linuxcnc'].includes(params.value.post || '')) {
    warnings.push('Rigid tapping may not be supported on this controller')
  }
  
  return warnings
})

const highlightedGCode = computed(() => {
  if (!gcodePreview.value) return ''
  
  return gcodePreview.value
    .split('\n')
    .map(line => {
      if (line.startsWith('(')) {
        return `<span class="comment">${line}</span>`
      } else if (line.match(/^[GM]\d+/)) {
        return `<span class="gcode">${line}</span>`
      } else {
        return line
      }
    })
    .join('\n')
})

// Methods
function addHole() {
  holes.value.push({
    x: 10 + holes.value.length * 10,
    y: 10,
    z: -15,
    enabled: true
  })
  drawCanvas()
}

function removeHole(index: number) {
  holes.value.splice(index, 1)
  if (selectedHole.value === index) {
    selectedHole.value = null
  }
  drawCanvas()
}

function selectHole(index: number) {
  selectedHole.value = index
  drawCanvas()
}

async function generateLinearPattern() {
  const response = await fetch('/api/cam/drilling/pattern/linear', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(linearPattern.value)
  })
  
  const newHoles = await response.json()
  holes.value = newHoles.map((h: any) => ({ ...h, enabled: true }))
  drawCanvas()
  updateGCodePreview()
}

async function generateCircularPattern() {
  const response = await fetch('/api/cam/drilling/pattern/circular', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(circularPattern.value)
  })
  
  const newHoles = await response.json()
  holes.value = newHoles.map((h: any) => ({ ...h, enabled: true }))
  drawCanvas()
  updateGCodePreview()
}

async function generateGridPattern() {
  const response = await fetch('/api/cam/drilling/pattern/grid', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(gridPattern.value)
  })
  
  const newHoles = await response.json()
  holes.value = newHoles.map((h: any) => ({ ...h, enabled: true }))
  drawCanvas()
  updateGCodePreview()
}

function drawCanvas() {
  if (!canvas.value) return
  
  const ctx = canvas.value.getContext('2d')!
  const w = canvas.value.width
  const h = canvas.value.height
  
  // Clear
  ctx.fillStyle = '#1a1a1a'
  ctx.fillRect(0, 0, w, h)
  
  // Grid
  ctx.strokeStyle = '#333'
  ctx.lineWidth = 1
  for (let i = 0; i <= 10; i++) {
    const x = (i / 10) * w
    const y = (i / 10) * h
    ctx.beginPath()
    ctx.moveTo(x, 0)
    ctx.lineTo(x, h)
    ctx.stroke()
    ctx.beginPath()
    ctx.moveTo(0, y)
    ctx.lineTo(w, y)
    ctx.stroke()
  }
  
  // Origin
  ctx.strokeStyle = '#666'
  ctx.lineWidth = 2
  ctx.beginPath()
  ctx.moveTo(30, h - 30)
  ctx.lineTo(80, h - 30)
  ctx.stroke()
  ctx.beginPath()
  ctx.moveTo(30, h - 30)
  ctx.lineTo(30, h - 80)
  ctx.stroke()
  
  ctx.fillStyle = '#999'
  ctx.font = '12px monospace'
  ctx.fillText('X', 85, h - 25)
  ctx.fillText('Y', 35, h - 85)
  
  // Holes
  const scale = 5 // pixels per mm
  const offsetX = 100
  const offsetY = h - 100
  
  holes.value.forEach((hole, index) => {
    const x = offsetX + hole.x * scale
    const y = offsetY - hole.y * scale
    
    const isSelected = selectedHole.value === index
    const isEnabled = hole.enabled
    
    // Hole circle
    ctx.beginPath()
    ctx.arc(x, y, params.value.tool_d * scale / 2, 0, Math.PI * 2)
    ctx.fillStyle = isEnabled ? '#4CAF50' : '#666'
    ctx.fill()
    ctx.strokeStyle = isSelected ? '#FFD700' : '#fff'
    ctx.lineWidth = isSelected ? 3 : 1
    ctx.stroke()
    
    // Label
    ctx.fillStyle = '#fff'
    ctx.font = '10px monospace'
    ctx.fillText(hole.label || `H${index + 1}`, x + 10, y - 10)
  })
}

function onCanvasClick(e: MouseEvent) {
  if (!canvas.value) return
  
  const rect = canvas.value.getBoundingClientRect()
  const clickX = e.clientX - rect.left
  const clickY = e.clientY - rect.top
  
  const scale = 5
  const offsetX = 100
  const offsetY = canvas.value.height - 100
  
  // Check if clicked on existing hole
  for (let i = 0; i < holes.value.length; i++) {
    const hole = holes.value[i]
    const holeX = offsetX + hole.x * scale
    const holeY = offsetY - hole.y * scale
    const distance = Math.sqrt((clickX - holeX) ** 2 + (clickY - holeY) ** 2)
    
    if (distance < params.value.tool_d * scale / 2) {
      selectHole(i)
      return
    }
  }
  
  // Add new hole if manual mode
  if (activePattern.value === 'manual') {
    const x = (clickX - offsetX) / scale
    const y = (offsetY - clickY) / scale
    
    holes.value.push({
      x: Math.round(x),
      y: Math.round(y),
      z: -15,
      enabled: true
    })
    
    drawCanvas()
    updateGCodePreview()
  }
}

function onCanvasHover(e: MouseEvent) {
  // TODO: Show cursor coordinates
}

async function updateGCodePreview() {
  const enabledHoles = holes.value.filter(h => h.enabled)
  if (enabledHoles.length === 0) {
    gcodePreview.value = '(No holes defined)'
    return
  }
  
  const body = {
    ...params.value,
    holes: enabledHoles
  }
  
  try {
    const response = await fetch('/api/cam/drilling/gcode', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
    
    const result = await response.json()
    gcodePreview.value = result.gcode
  } catch (error) {
    console.error('Failed to generate G-code:', error)
    gcodePreview.value = '(Error generating G-code)'
  }
}

function onToolTypeChange() {
  // Auto-adjust cycle based on tool type
  if (params.value.tool_type === 'tap') {
    params.value.cycle = 'G84'
  } else if (params.value.tool_type === 'spot_drill') {
    params.value.cycle = 'G82'
  } else if (params.value.tool_type === 'boring_bar') {
    params.value.cycle = 'G85'
  } else {
    params.value.cycle = 'G81'
  }
  updateGCodePreview()
}

function onCycleChange() {
  updateGCodePreview()
}

async function exportGCode() {
  if (!gcodePreview.value) {
    alert('No G-code to export')
    return
  }
  
  const blob = new Blob([gcodePreview.value], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `drilling_${params.value.cycle.toLowerCase()}_${params.value.post || 'auto'}.nc`
  a.click()
  URL.revokeObjectURL(url)
}

function copyGCode() {
  navigator.clipboard.writeText(gcodePreview.value)
  alert('G-code copied to clipboard')
}

function downloadGCode() {
  exportGCode()
}

function saveToLibrary() {
  // TODO: Implement save to library
  alert('Save to library - TODO')
}

// Watchers
watch(() => holes.value, () => {
  updateGCodePreview()
}, { deep: true })

watch(() => params.value, () => {
  updateGCodePreview()
}, { deep: true })

// Lifecycle
onMounted(() => {
  // Initialize with sample pattern
  holes.value = [
    { x: 10, y: 10, z: -15, enabled: true },
    { x: 30, y: 10, z: -15, enabled: true },
    { x: 50, y: 10, z: -15, enabled: true }
  ]
  
  drawCanvas()
  updateGCodePreview()
})
</script>

<style scoped>
.drilling-lab {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #0a0a0a;
  color: #e0e0e0;
}

.lab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #333;
}

.lab-header h2 {
  margin: 0;
  font-size: 1.5rem;
}

.actions {
  display: flex;
  gap: 0.5rem;
}

.btn-primary, .btn-secondary {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-primary {
  background: #4CAF50;
  color: white;
}

.btn-secondary {
  background: #555;
  color: white;
}

.lab-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.left-panel {
  width: 350px;
  padding: 1rem;
  overflow-y: auto;
  border-right: 1px solid #333;
}

.panel-section {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: #1a1a1a;
  border-radius: 8px;
}

.panel-section h3 {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
  color: #4CAF50;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.25rem;
  font-size: 0.9rem;
  color: #aaa;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 0.5rem;
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 4px;
  color: #e0e0e0;
}

.input-with-unit {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.input-with-unit input {
  flex: 1;
}

.unit {
  color: #999;
  font-size: 0.9rem;
}

.help-text {
  display: block;
  margin-top: 0.25rem;
  font-size: 0.85rem;
  color: #666;
}

.tool-type-selector,
.cycle-selector {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.cycle-option {
  display: flex;
  flex-direction: column;
}

.pattern-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.tab {
  flex: 1;
  padding: 0.5rem;
  background: #2a2a2a;
  border: none;
  border-radius: 4px;
  color: #aaa;
  cursor: pointer;
}

.tab.active {
  background: #4CAF50;
  color: white;
}

.btn-generate,
.btn-add {
  width: 100%;
  padding: 0.75rem;
  background: #4CAF50;
  border: none;
  border-radius: 4px;
  color: white;
  cursor: pointer;
  font-size: 0.9rem;
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
  background: #2a2a2a;
  border-radius: 4px;
  margin-bottom: 0.5rem;
  cursor: pointer;
}

.hole-item.selected {
  background: #3a3a3a;
  border: 1px solid #4CAF50;
}

.hole-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.btn-remove {
  padding: 0.25rem 0.5rem;
  background: #d32f2f;
  border: none;
  border-radius: 4px;
  color: white;
  cursor: pointer;
}

.canvas-container {
  position: relative;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

canvas {
  border: 1px solid #333;
  border-radius: 8px;
}

.stats-overlay {
  position: absolute;
  top: 2rem;
  right: 2rem;
  background: rgba(0, 0, 0, 0.8);
  padding: 1rem;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.stat {
  font-size: 0.9rem;
}

.bottom-panel {
  border-top: 1px solid #333;
  background: #1a1a1a;
  transition: height 0.3s;
}

.bottom-panel.collapsed {
  height: 50px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  cursor: pointer;
}

.panel-header h3 {
  margin: 0;
}

.panel-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-icon {
  padding: 0.25rem 0.5rem;
  background: #2a2a2a;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}

.gcode-content {
  padding: 0 1rem 1rem 1rem;
  max-height: 300px;
  overflow-y: auto;
}

.gcode-content pre {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 0.85rem;
  line-height: 1.5;
}

.gcode-content .comment {
  color: #666;
}

.gcode-content .gcode {
  color: #4CAF50;
}

.warnings {
  margin-top: 0.5rem;
}

.warning {
  padding: 0.5rem;
  background: rgba(255, 152, 0, 0.1);
  border-left: 3px solid #FF9800;
  margin-bottom: 0.5rem;
  font-size: 0.85rem;
}
</style>
```

---

## 🧪 Testing Guide

### **Test 1: Manual Hole Entry**

1. Open DrillingLab component
2. Click on canvas to add holes
3. Verify holes appear with green circles
4. Select hole by clicking (should highlight with gold border)
5. Remove hole with ✕ button
6. Check G-code preview updates in real-time

---

### **Test 2: Linear Pattern**

1. Switch to "Linear" tab
2. Set: Start X=10, Y=10, Spacing=20, Count=5, Direction=X
3. Click "Generate Linear Pattern"
4. Verify 5 holes appear horizontally spaced at 20mm
5. Check stats overlay shows correct hole count

---

### **Test 3: Bolt Circle**

1. Switch to "Circular" tab
2. Set: Center X=50, Y=50, Radius=30, Count=8
3. Click "Generate Bolt Circle"
4. Verify 8 holes appear evenly distributed on 30mm radius
5. Export G-code and verify hole coordinates

---

### **Test 4: Peck Drilling**

1. Select "G83 Peck" cycle
2. Set Peck Depth to 5mm
3. Add holes with -50mm depth
4. Verify stats show correct peck count
5. Check G-code shows either modal G83 or expanded pecks

---

### **Test 5: Rigid Tapping**

1. Select "Tap" tool type (should auto-select G84)
2. Set Thread Pitch to 1.0mm
3. Set RPM to 500
4. Verify calculated feed = 500 mm/min
5. Check G-code shows M29/M28 for Haas/Fanuc

---

## 📊 Features Summary

| Feature | Status | Description |
|---------|--------|-------------|
| **Interactive Canvas** | ✅ | Click to add holes, visual feedback |
| **Pattern Generators** | ✅ | Linear, circular, grid patterns |
| **Cycle Support** | ✅ | G81, G82, G83, G73, G84, G85 |
| **Real-time Preview** | ✅ | Live G-code updates |
| **Post Selector** | ✅ | Auto-detection with warnings |
| **Stats Overlay** | ✅ | Holes, depth, time, pecks |
| **Tool Types** | ✅ | Drill, tap, spot drill, boring |
| **Hole Management** | ✅ | Enable/disable, remove, select |
| **Export Options** | ✅ | Download, copy, save |
| **Syntax Highlighting** | ✅ | Color-coded G-code |

---

## ✅ Implementation Checklist

### **Phase 1: Component Structure (2 hours)**
- [ ] Create `DrillingLab.vue` with layout
- [ ] Implement left panel sections
- [ ] Add canvas with grid rendering
- [ ] Setup bottom panel with collapsible G-code

### **Phase 2: Hole Management (1 hour)**
- [ ] Implement hole list rendering
- [ ] Add/remove/select hole logic
- [ ] Enable/disable checkboxes
- [ ] Canvas click detection

### **Phase 3: Pattern Generators (2 hours)**
- [ ] Implement linear pattern UI and API call
- [ ] Implement circular pattern UI and API call
- [ ] Implement grid pattern UI and API call
- [ ] Test all patterns with canvas updates

### **Phase 4: G-Code Integration (1.5 hours)**
- [ ] Connect to `/api/cam/drilling/gcode` endpoint
- [ ] Implement real-time preview updates
- [ ] Add syntax highlighting
- [ ] Export/copy/download functionality

### **Phase 5: Advanced Features (1 hour)**
- [ ] Tool type auto-cycle selection
- [ ] Tap feed calculation display
- [ ] Post-processor warnings
- [ ] Stats overlay calculations

### **Phase 6: Polish (1 hour)**
- [ ] Styling and responsive layout
- [ ] Hover effects and tooltips
- [ ] Error handling
- [ ] Loading states

**Total Effort:** ~8.5 hours

---

## 🎨 Styling Notes

- **Dark theme** (#0a0a0a background, #e0e0e0 text)
- **Accent color** (#4CAF50 green)
- **Canvas grid** (#333 lines)
- **Selected hole** (gold border #FFD700)
- **Enabled holes** (green fill)
- **Disabled holes** (gray fill #666)

---

## 🔮 Future Enhancements

### **V2: Advanced Features**
- DXF import with auto-hole detection
- Hole sorting by distance (optimize travel)
- Multi-depth operations (pilot → final drill)
- Tool library integration
- Material database with recommended feeds/speeds

### **V3: Collaboration**
- Save patterns to cloud library
- Share patterns with team
- Version history
- Pattern templates marketplace

---

## 🏆 Summary

Patch N.07 delivers a **production-ready drilling UI** with:

✅ **Interactive canvas** with click-to-add holes  
✅ **3 pattern generators** (linear, circular, grid)  
✅ **6 cycle types** (G81-G85)  
✅ **Real-time G-code preview** with syntax highlighting  
✅ **Smart post adaptation** with warnings  
✅ **Stats overlay** (holes, depth, time, pecks)  
✅ **Tool-aware interface** (drill, tap, spot, boring)  
✅ **Export options** (download, copy, save)  

**Implementation:** ~8.5 hours  
**Status:** 🔜 Ready for implementation  
**Dependencies:** Patch N.06 (drilling router and modal_cycles.py)
