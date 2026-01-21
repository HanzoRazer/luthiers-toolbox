<template>
  <div class="guitar-dimensions-form">
    <div class="form-header">
      <h2>🎸 Guitar Body Dimensions</h2>
      <p class="description">
        Enter measurements for acoustic or electric guitar bodies. All dimensions stored in millimeters.
      </p>
    </div>

    <!-- Guitar Type Selection -->
    <section class="form-section">
      <h3>Guitar Type</h3>
      <div class="button-group">
        <button 
          v-for="type in guitarTypes" 
          :key="type.id"
          :class="{ active: selectedType === type.id }"
          @click="selectType(type.id)"
        >
          {{ type.icon }} {{ type.name }}
        </button>
      </div>
    </section>

    <!-- Body Dimensions -->
    <section class="form-section">
      <h3>Body Dimensions</h3>
      <div class="form-grid">
        <div class="form-field">
          <label for="bodyLength">Body Length</label>
          <div class="input-with-unit">
            <input 
              id="bodyLength" 
              v-model.number="dimensions.bodyLength" 
              type="number" 
              step="0.1"
              @input="handleChange"
            >
            <span class="unit">{{ currentUnit }}</span>
          </div>
          <span class="hint">Tip to tail along centerline</span>
        </div>

        <div class="form-field">
          <label for="bodyWidthUpper">Upper Bout Width</label>
          <div class="input-with-unit">
            <input 
              id="bodyWidthUpper" 
              v-model.number="dimensions.bodyWidthUpper" 
              type="number" 
              step="0.1"
              @input="handleChange"
            >
            <span class="unit">{{ currentUnit }}</span>
          </div>
          <span class="hint">Widest point above waist</span>
        </div>

        <div class="form-field">
          <label for="bodyWidthLower">Lower Bout Width</label>
          <div class="input-with-unit">
            <input 
              id="bodyWidthLower" 
              v-model.number="dimensions.bodyWidthLower" 
              type="number" 
              step="0.1"
              @input="handleChange"
            >
            <span class="unit">{{ currentUnit }}</span>
          </div>
          <span class="hint">Widest point below waist</span>
        </div>

        <div class="form-field">
          <label for="waistWidth">Waist Width</label>
          <div class="input-with-unit">
            <input 
              id="waistWidth" 
              v-model.number="dimensions.waistWidth" 
              type="number" 
              step="0.1"
              @input="handleChange"
            >
            <span class="unit">{{ currentUnit }}</span>
          </div>
          <span class="hint">Narrowest point (C-curves)</span>
        </div>

        <div class="form-field">
          <label for="bodyDepth">Body Depth</label>
          <div class="input-with-unit">
            <input 
              id="bodyDepth" 
              v-model.number="dimensions.bodyDepth" 
              type="number" 
              step="0.1"
              @input="handleChange"
            >
            <span class="unit">{{ currentUnit }}</span>
          </div>
          <span class="hint">Including top and back arch (if any)</span>
        </div>

        <div class="form-field">
          <label for="scaleLength">Scale Length</label>
          <div class="input-with-unit">
            <input 
              id="scaleLength" 
              v-model.number="dimensions.scaleLength" 
              type="number" 
              step="0.1"
              @input="handleChange"
            >
            <span class="unit">{{ currentUnit }}</span>
          </div>
          <span class="hint">Nut to bridge saddle</span>
        </div>
      </div>
    </section>

    <!-- Neck Dimensions -->
    <section class="form-section">
      <h3>Neck Dimensions</h3>
      <div class="form-grid">
        <div class="form-field">
          <label for="nutWidth">Nut Width</label>
          <div class="input-with-unit">
            <input 
              id="nutWidth" 
              v-model.number="dimensions.nutWidth" 
              type="number" 
              step="0.1"
              @input="handleChange"
            >
            <span class="unit">{{ currentUnit }}</span>
          </div>
        </div>

        <div class="form-field">
          <label for="bridgeSpacing">Bridge String Spacing</label>
          <div class="input-with-unit">
            <input 
              id="bridgeSpacing" 
              v-model.number="dimensions.bridgeSpacing" 
              type="number" 
              step="0.1"
              @input="handleChange"
            >
            <span class="unit">{{ currentUnit }}</span>
          </div>
        </div>

        <div class="form-field">
          <label for="fretCount">Fret Count</label>
          <div class="input-with-unit">
            <input 
              id="fretCount" 
              v-model.number="dimensions.fretCount" 
              type="number" 
              step="1"
              @input="handleChange"
            >
            <span class="unit">frets</span>
          </div>
        </div>

        <div class="form-field">
          <label for="neckAngle">Neck Angle</label>
          <div class="input-with-unit">
            <input 
              id="neckAngle" 
              v-model.number="dimensions.neckAngle" 
              type="number" 
              step="0.1"
              @input="handleChange"
            >
            <span class="unit">degrees</span>
          </div>
          <span class="hint">Set-neck tilt (0° for bolt-on)</span>
        </div>
      </div>
    </section>

    <!-- Presets -->
    <section class="form-section">
      <h3>Load Preset</h3>
      <div class="preset-buttons">
        <button 
          v-for="preset in presets" 
          :key="preset.id"
          class="preset-btn"
          @click="loadPreset(preset.id)"
        >
          {{ preset.name }}
        </button>
      </div>
    </section>

    <!-- Units Toggle -->
    <section class="form-section">
      <h3>Units</h3>
      <div class="button-group">
        <button 
          :class="{ active: units === 'mm' }"
          @click="toggleUnits('mm')"
        >
          Millimeters (mm)
        </button>
        <button 
          :class="{ active: units === 'inch' }"
          @click="toggleUnits('inch')"
        >
          Inches (in)
        </button>
      </div>
    </section>

    <!-- Actions -->
    <section class="form-section actions">
      <button
        class="btn-primary"
        :disabled="!hasValidDimensions || isGenerating"
        @click="generateAndExportDXF"
      >
        {{ isGenerating ? '⏳ Generating...' : '🎨 Generate Body Outline (DXF)' }}
      </button>
      <button
        class="btn-primary"
        :disabled="!hasValidDimensions || isGenerating"
        @click="generateAndExportSVG"
      >
        {{ isGenerating ? '⏳ Generating...' : '🖼️ Generate Body Outline (SVG)' }}
      </button>
      <button
        class="btn-success"
        :disabled="!hasValidDimensions || isGenerating"
        style="margin-top: 8px;"
        @click="generateAndSendToCAM"
      >
        {{ isGenerating ? '⏳ Planning...' : '⚙️ Send to CAM (Generate Toolpath)' }}
      </button>
      <button
        class="btn-secondary"
        @click="exportJSON"
      >
        💾 Save as JSON
      </button>
      <button
        class="btn-secondary"
        @click="exportCSV"
      >
        📊 Export CSV
      </button>
      <button
        class="btn-secondary"
        @click="copyToClipboard"
      >
        📋 Copy to Clipboard
      </button>
      <button
        class="btn-danger"
        @click="clearAll"
      >
        🗑️ Clear All
      </button>
    </section>

    <!-- CAM Toolpath Statistics -->
    <section
      v-if="camResults"
      class="form-section cam-results"
    >
      <h3>🔧 CAM Toolpath Statistics</h3>
      <div class="stats-grid">
        <div class="stat-item">
          <span class="stat-label">Total Length:</span>
          <span class="stat-value">{{ camResults.stats.length_mm.toFixed(2) }} mm</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Pocket Area:</span>
          <span class="stat-value">{{ camResults.stats.area_mm2.toFixed(2) }} mm²</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Machining Time:</span>
          <span class="stat-value">{{ camResults.stats.time_min.toFixed(2) }} min ({{ camResults.stats.time_s.toFixed(1) }}s)</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Material Volume:</span>
          <span class="stat-value">{{ camResults.stats.volume_mm3.toFixed(2) }} mm³</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Move Count:</span>
          <span class="stat-value">{{ camResults.stats.move_count }}</span>
        </div>
      </div>
      
      <div class="cam-params">
        <h4>CAM Parameters Used:</h4>
        <ul>
          <li><strong>Tool Diameter:</strong> {{ camResults.cam_params.tool_d }} mm</li>
          <li><strong>Stepover:</strong> {{ (camResults.cam_params.stepover * 100).toFixed(0) }}% ({{ (camResults.cam_params.tool_d * camResults.cam_params.stepover).toFixed(2) }} mm)</li>
          <li><strong>Strategy:</strong> {{ camResults.cam_params.strategy }}</li>
        </ul>
      </div>

      <div class="cam-actions">
        <button
          class="btn-primary"
          @click="downloadGCode"
        >
          💾 Download G-code ({{ selectedPost }})
        </button>
        <select
          v-model="selectedPost"
          class="post-selector"
        >
          <option value="GRBL">
            GRBL
          </option>
          <option value="Mach3">
            Mach3
          </option>
          <option value="Mach4">
            Mach4
          </option>
          <option value="LinuxCNC">
            LinuxCNC
          </option>
          <option value="PathPilot">
            PathPilot
          </option>
        </select>
      </div>

      <details class="move-preview">
        <summary>Preview First 20 Moves</summary>
        <pre class="gcode-preview">{{ formatMoves(camResults.moves) }}</pre>
      </details>
    </section>

    <!-- Status -->
    <div
      v-if="status"
      :class="['status-message', statusType]"
    >
      {{ status }}
    </div>

    <!-- Visual Preview (Simple SVG) -->
    <section class="form-section preview">
      <h3>Preview (Top View)</h3>
      <svg
        :viewBox="viewBox"
        class="body-preview"
      >
        <!-- Background -->
        <rect
          x="0"
          y="0"
          :width="svgWidth"
          :height="svgHeight"
          fill="#fafafa"
        />
        
        <!-- Simplified body outline (based on dimensions) -->
        <g
          v-if="hasValidDimensions"
          transform="translate(250, 50)"
        >
          <!-- Upper bout -->
          <ellipse 
            :cx="0" 
            :cy="scaledBodyLength * 0.3" 
            :rx="scaledBodyWidthUpper / 2" 
            :ry="scaledBodyLength * 0.15"
            fill="none"
            stroke="#333"
            stroke-width="2"
          />
          
          <!-- Lower bout -->
          <ellipse 
            :cx="0" 
            :cy="scaledBodyLength * 0.7" 
            :rx="scaledBodyWidthLower / 2" 
            :ry="scaledBodyLength * 0.2"
            fill="none"
            stroke="#333"
            stroke-width="2"
          />
          
          <!-- Waist indicators -->
          <line 
            :x1="-scaledWaistWidth / 2" 
            :y1="scaledBodyLength * 0.5"
            :x2="scaledWaistWidth / 2" 
            :y2="scaledBodyLength * 0.5"
            stroke="#666"
            stroke-width="1"
            stroke-dasharray="3,3"
          />
          
          <!-- Centerline -->
          <line 
            x1="0" 
            y1="0"
            x2="0" 
            :y2="scaledBodyLength"
            stroke="#94a3b8"
            stroke-width="1"
            stroke-dasharray="5,5"
          />
          
          <!-- Dimension labels -->
          <text
            x="10"
            :y="scaledBodyLength / 2"
            font-size="10"
            fill="#666"
          >
            {{ dimensions.bodyLength }} {{ currentUnit }}
          </text>
        </g>
        
        <!-- Placeholder if no dimensions -->
        <text
          v-else
          x="250"
          y="250"
          text-anchor="middle"
          font-size="14"
          fill="#999"
        >
          Enter dimensions to see preview
        </text>
      </svg>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

interface GuitarDimensions {
  bodyLength: number
  bodyWidthUpper: number
  bodyWidthLower: number
  waistWidth: number
  bodyDepth: number
  scaleLength: number
  nutWidth: number
  bridgeSpacing: number
  fretCount: number
  neckAngle: number
}

const guitarTypes = [
  { id: 'acoustic', name: 'Acoustic', icon: '🎻' },
  { id: 'electric', name: 'Electric', icon: '🎸' },
  { id: 'classical', name: 'Classical', icon: '🎼' },
  { id: 'bass', name: 'Bass', icon: '🎵' }
]

const presets = [
  { id: 'dreadnought', name: 'Dreadnought' },
  { id: 'om', name: 'OM / 000' },
  { id: 'les_paul', name: 'Les Paul' },
  { id: 'stratocaster', name: 'Stratocaster' },
  { id: 'telecaster', name: 'Telecaster' },
  { id: 'jazz_bass', name: 'Jazz Bass' }
]

const selectedType = ref('acoustic')
const units = ref<'mm' | 'inch'>('mm')
const status = ref('')
const statusType = ref<'success' | 'error' | 'info'>('info')

const dimensions = ref<GuitarDimensions>({
  bodyLength: 0,
  bodyWidthUpper: 0,
  bodyWidthLower: 0,
  waistWidth: 0,
  bodyDepth: 0,
  scaleLength: 0,
  nutWidth: 0,
  bridgeSpacing: 0,
  fretCount: 22,
  neckAngle: 0
})

// Load dimensions from query parameters (AI-extracted from Blueprint Lab)
onMounted(() => {
  if (route.query.preset === 'ai-extracted') {
    // Parse numeric dimensions from query params
    const parseQueryNumber = (key: string): number => {
      const value = route.query[key]
      if (typeof value === 'string') {
        const parsed = parseFloat(value)
        return isNaN(parsed) ? 0 : parsed
      }
      return 0
    }

    dimensions.value = {
      bodyLength: parseQueryNumber('bodyLength'),
      bodyWidthUpper: parseQueryNumber('bodyWidthUpper'),
      bodyWidthLower: parseQueryNumber('bodyWidthLower'),
      waistWidth: parseQueryNumber('bodyWidthWaist'),
      bodyDepth: parseQueryNumber('bodyDepth'),
      scaleLength: parseQueryNumber('scaleLength'),
      nutWidth: parseQueryNumber('neckWidth'),
      bridgeSpacing: parseQueryNumber('bridgeSpacing'),
      fretCount: parseQueryNumber('fretCount') || 22,
      neckAngle: parseQueryNumber('neckAngle')
    }

    status.value = '✅ Dimensions loaded from Blueprint AI analysis'
    statusType.value = 'success'
  }
})

const currentUnit = computed(() => units.value === 'mm' ? 'mm' : 'in')

const hasValidDimensions = computed(() => {
  return dimensions.value.bodyLength > 0 && 
         dimensions.value.bodyWidthLower > 0
})

// SVG preview scaling
const svgWidth = 500
const svgHeight = 600
const viewBox = `0 0 ${svgWidth} ${svgHeight}`

const scaledBodyLength = computed(() => {
  if (!dimensions.value.bodyLength) return 0
  return Math.min(dimensions.value.bodyLength * 0.8, 400)
})

const scaledBodyWidthUpper = computed(() => {
  if (!dimensions.value.bodyWidthUpper) return 0
  return Math.min(dimensions.value.bodyWidthUpper * 0.8, 300)
})

const scaledBodyWidthLower = computed(() => {
  if (!dimensions.value.bodyWidthLower) return 0
  return Math.min(dimensions.value.bodyWidthLower * 0.8, 300)
})

const scaledWaistWidth = computed(() => {
  if (!dimensions.value.waistWidth) return 0
  return Math.min(dimensions.value.waistWidth * 0.8, 200)
})

const isGenerating = ref(false)
const camResults = ref<any>(null)
const selectedPost = ref('GRBL')

function selectType(typeId: string) {
  selectedType.value = typeId
  status.value = `✅ Selected ${guitarTypes.find(t => t.id === typeId)?.name} guitar type`
  statusType.value = 'success'
}

function handleChange() {
  // Dimensions changed, clear status
  if (status.value) {
    status.value = ''
  }
}

function toggleUnits(newUnit: 'mm' | 'inch') {
  if (units.value === newUnit) return
  
  const conversionFactor = newUnit === 'inch' ? 0.03937007874015748 : 25.4
  
  // Convert all dimension values
  const keys: (keyof GuitarDimensions)[] = [
    'bodyLength', 'bodyWidthUpper', 'bodyWidthLower', 'waistWidth',
    'bodyDepth', 'scaleLength', 'nutWidth', 'bridgeSpacing'
  ]
  
  keys.forEach(key => {
    if (dimensions.value[key]) {
      dimensions.value[key] = parseFloat((dimensions.value[key] * conversionFactor).toFixed(3))
    }
  })
  
  units.value = newUnit
  status.value = `✅ Converted to ${newUnit === 'mm' ? 'millimeters' : 'inches'}`
  statusType.value = 'success'
}

function loadPreset(presetId: string) {
  const presetData: Record<string, Partial<GuitarDimensions>> = {
    dreadnought: {
      bodyLength: 505,
      bodyWidthUpper: 280,
      bodyWidthLower: 390,
      waistWidth: 270,
      bodyDepth: 120,
      scaleLength: 648,
      nutWidth: 43,
      bridgeSpacing: 56,
      fretCount: 20,
      neckAngle: 0
    },
    om: {
      bodyLength: 495,
      bodyWidthUpper: 280,
      bodyWidthLower: 380,
      waistWidth: 260,
      bodyDepth: 110,
      scaleLength: 648,
      nutWidth: 43,
      bridgeSpacing: 54,
      fretCount: 20,
      neckAngle: 0
    },
    les_paul: {
      bodyLength: 475,
      bodyWidthUpper: 330,
      bodyWidthLower: 330,
      waistWidth: 280,
      bodyDepth: 55,
      scaleLength: 628,
      nutWidth: 43,
      bridgeSpacing: 52,
      fretCount: 22,
      neckAngle: 4
    },
    stratocaster: {
      bodyLength: 460,
      bodyWidthUpper: 320,
      bodyWidthLower: 320,
      waistWidth: 280,
      bodyDepth: 45,
      scaleLength: 648,
      nutWidth: 42,
      bridgeSpacing: 52,
      fretCount: 22,
      neckAngle: 0
    },
    telecaster: {
      bodyLength: 470,
      bodyWidthUpper: 325,
      bodyWidthLower: 325,
      waistWidth: 320,
      bodyDepth: 45,
      scaleLength: 648,
      nutWidth: 42,
      bridgeSpacing: 54,
      fretCount: 22,
      neckAngle: 0
    },
    jazz_bass: {
      bodyLength: 490,
      bodyWidthUpper: 330,
      bodyWidthLower: 355,
      waistWidth: 280,
      bodyDepth: 46,
      scaleLength: 864,
      nutWidth: 38,
      bridgeSpacing: 62,
      fretCount: 20,
      neckAngle: 0
    }
  }
  
  const preset = presetData[presetId]
  if (preset) {
    Object.assign(dimensions.value, preset)
    status.value = `✅ Loaded ${presets.find(p => p.id === presetId)?.name} preset`
    statusType.value = 'success'
    
    // Auto-select guitar type based on preset
    if (presetId.includes('bass')) {
      selectedType.value = 'bass'
    } else if (['dreadnought', 'om'].includes(presetId)) {
      selectedType.value = 'acoustic'
    } else {
      selectedType.value = 'electric'
    }
  }
}

function exportJSON() {
  const data = {
    type: selectedType.value,
    units: units.value,
    dimensions: dimensions.value,
    timestamp: new Date().toISOString()
  }
  
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `guitar-dimensions-${Date.now()}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  
  status.value = '✅ JSON file downloaded'
  statusType.value = 'success'
}

function exportCSV() {
  const headers = ['Dimension', 'Value', 'Unit']
  const rows = [
    ['Body Length', dimensions.value.bodyLength, currentUnit.value],
    ['Upper Bout Width', dimensions.value.bodyWidthUpper, currentUnit.value],
    ['Lower Bout Width', dimensions.value.bodyWidthLower, currentUnit.value],
    ['Waist Width', dimensions.value.waistWidth, currentUnit.value],
    ['Body Depth', dimensions.value.bodyDepth, currentUnit.value],
    ['Scale Length', dimensions.value.scaleLength, currentUnit.value],
    ['Nut Width', dimensions.value.nutWidth, currentUnit.value],
    ['Bridge Spacing', dimensions.value.bridgeSpacing, currentUnit.value],
    ['Fret Count', dimensions.value.fretCount, 'frets'],
    ['Neck Angle', dimensions.value.neckAngle, 'degrees']
  ]
  
  const csv = [headers, ...rows].map(row => row.join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `guitar-dimensions-${Date.now()}.csv`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  
  status.value = '✅ CSV file downloaded'
  statusType.value = 'success'
}

function copyToClipboard() {
  const text = Object.entries(dimensions.value)
    .map(([key, value]) => `${key}: ${value}${key.includes('Angle') ? '°' : key === 'fretCount' ? '' : currentUnit.value}`)
    .join('\n')
  
  navigator.clipboard.writeText(text).then(() => {
    status.value = '✅ Copied to clipboard'
    statusType.value = 'success'
  }).catch(() => {
    status.value = '❌ Failed to copy to clipboard'
    statusType.value = 'error'
  })
}

async function generateAndExportDXF() {
  if (!hasValidDimensions.value) {
    status.value = '❌ Please enter at least body length and lower bout width'
    statusType.value = 'error'
    return
  }

  isGenerating.value = true
  status.value = '⏳ Generating parametric body outline...'
  statusType.value = 'info'

  try {
    const response = await fetch('/api/guitar/design/parametric/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        dimensions: dimensions.value,
        guitarType: selectedType.value.charAt(0).toUpperCase() + selectedType.value.slice(1),
        units: units.value,
        format: 'dxf',
        resolution: 48
      })
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`HTTP ${response.status}: ${errorText}`)
    }

    // Download file
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    const filename = response.headers.get('content-disposition')?.split('filename=')[1]?.replace(/"/g, '') || 
                     `guitar_body_${Date.now()}.dxf`
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

    status.value = '✅ DXF body outline downloaded! Import into CAM software.'
    statusType.value = 'success'
  } catch (error) {
    console.error('DXF generation failed:', error)
    status.value = `❌ Generation failed: ${error instanceof Error ? error.message : 'Unknown error'}`
    statusType.value = 'error'
  } finally {
    isGenerating.value = false
  }
}

async function generateAndExportSVG() {
  if (!hasValidDimensions.value) {
    status.value = '❌ Please enter at least body length and lower bout width'
    statusType.value = 'error'
    return
  }

  isGenerating.value = true
  status.value = '⏳ Generating parametric body outline...'
  statusType.value = 'info'

  try {
    const response = await fetch('/api/guitar/design/parametric/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        dimensions: dimensions.value,
        guitarType: selectedType.value.charAt(0).toUpperCase() + selectedType.value.slice(1),
        units: units.value,
        format: 'svg',
        resolution: 48
      })
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`HTTP ${response.status}: ${errorText}`)
    }

    // Download file
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    const filename = response.headers.get('content-disposition')?.split('filename=')[1]?.replace(/"/g, '') || 
                     `guitar_body_${Date.now()}.svg`
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

    status.value = '✅ SVG body outline downloaded!'
    statusType.value = 'success'
  } catch (error) {
    console.error('SVG generation failed:', error)
    status.value = `❌ Generation failed: ${error instanceof Error ? error.message : 'Unknown error'}`
    statusType.value = 'error'
  } finally {
    isGenerating.value = false
  }
}

// Generate CAM toolpath from dimensions
async function generateAndSendToCAM() {
  if (!hasValidDimensions.value) {
    status.value = '❌ Please enter valid body dimensions first'
    statusType.value = 'error'
    return
  }

  try {
    isGenerating.value = true
    camResults.value = null
    status.value = '⏳ Planning adaptive toolpath with Module L.2...'
    statusType.value = 'info'

    const response = await fetch('/api/guitar/design/parametric/to-cam', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        dimensions: dimensions.value,
        guitarType: selectedType.value,
        resolution: 48
      })
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`CAM planning failed: ${response.status} ${errorText}`)
    }

    const result = await response.json()
    camResults.value = result

    status.value = `✅ Toolpath generated: ${result.stats.move_count} moves, ${result.stats.length_mm.toFixed(2)}mm path, ${result.stats.time_min.toFixed(2)} min machining time`
    statusType.value = 'success'
  } catch (error) {
    console.error('CAM generation failed:', error)
    status.value = `❌ CAM planning failed: ${error instanceof Error ? error.message : 'Unknown error'}`
    statusType.value = 'error'
  } finally {
    isGenerating.value = false
  }
}

// Download G-code with selected post-processor
async function downloadGCode() {
  if (!camResults.value) {
    status.value = '❌ Generate toolpath first'
    statusType.value = 'error'
    return
  }

  try {
    status.value = `⏳ Generating G-code for ${selectedPost.value}...`
    statusType.value = 'info'

    // For now, generate basic G-code with post headers
    // TODO: Integrate with /api/geometry/export_gcode endpoint
    const gcode = generateGCodeWithPost(camResults.value.moves, selectedPost.value)
    
    const blob = new Blob([gcode], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `guitar_body_${selectedType.value}_${selectedPost.value.toLowerCase()}.nc`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

    status.value = `✅ G-code downloaded: ${link.download}`
    statusType.value = 'success'
  } catch (error) {
    console.error('G-code download failed:', error)
    status.value = `❌ G-code download failed: ${error instanceof Error ? error.message : 'Unknown error'}`
    statusType.value = 'error'
  }
}

// Generate G-code with post-processor headers
function generateGCodeWithPost(moves: any[], postId: string): string {
  const headers: Record<string, string[]> = {
    'GRBL': ['G21', 'G90', 'G17', '(POST=GRBL;UNITS=mm)'],
    'Mach3': ['G21', 'G90', 'G17', 'G40', 'G49', '(POST=Mach3;UNITS=mm)'],
    'Mach4': ['G21', 'G90', 'G17', 'G40', 'G49', 'G80', '(POST=Mach4;UNITS=mm)'],
    'LinuxCNC': ['G21', 'G90', 'G17', 'G40', 'G49', '(POST=LinuxCNC;UNITS=mm)'],
    'PathPilot': ['G21', 'G90', 'G17', 'G40', 'G49', '(POST=PathPilot;UNITS=mm)']
  }

  const footers: Record<string, string[]> = {
    'GRBL': ['M30', '(End of program)'],
    'Mach3': ['M30', '(End of program)'],
    'Mach4': ['M30', '(End of program)'],
    'LinuxCNC': ['M2', '(End of program)'],
    'PathPilot': ['M30', '(End of program)']
  }

  const lines: string[] = []
  
  // Add headers
  lines.push(...(headers[postId] || headers['GRBL']))
  lines.push('')
  
  // Add moves
  moves.forEach(move => {
    const parts: string[] = [move.code]
    if (move.x !== undefined) parts.push(`X${move.x.toFixed(4)}`)
    if (move.y !== undefined) parts.push(`Y${move.y.toFixed(4)}`)
    if (move.z !== undefined) parts.push(`Z${move.z.toFixed(4)}`)
    if (move.f !== undefined) parts.push(`F${move.f.toFixed(1)}`)
    lines.push(parts.join(' '))
  })
  
  lines.push('')
  
  // Add footers
  lines.push(...(footers[postId] || footers['GRBL']))
  
  return lines.join('\n')
}

// Format moves for preview
function formatMoves(moves: any[]): string {
  return moves.map((move, i) => {
    const parts: string[] = [`N${i + 1}`, move.code]
    if (move.x !== undefined) parts.push(`X${move.x.toFixed(4)}`)
    if (move.y !== undefined) parts.push(`Y${move.y.toFixed(4)}`)
    if (move.z !== undefined) parts.push(`Z${move.z.toFixed(4)}`)
    if (move.f !== undefined) parts.push(`F${move.f.toFixed(1)}`)
    return parts.join(' ')
  }).join('\n')
}

function clearAll() {
  if (confirm('Clear all dimensions? This cannot be undone.')) {
    Object.keys(dimensions.value).forEach(key => {
      if (key === 'fretCount') {
        dimensions.value[key as keyof GuitarDimensions] = 22
      } else {
        dimensions.value[key as keyof GuitarDimensions] = 0
      }
    })
    status.value = '🗑️ All dimensions cleared'
    statusType.value = 'info'
  }
}
</script>

<style scoped>
.guitar-dimensions-form {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1.5rem;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.form-header {
  margin-bottom: 2rem;
  text-align: center;
}

.form-header h2 {
  font-size: 2rem;
  margin-bottom: 0.5rem;
  color: #333;
}

.description {
  color: #666;
  font-size: 0.95rem;
}

.form-section {
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid #eee;
}

.form-section:last-of-type {
  border-bottom: none;
}

.form-section h3 {
  font-size: 1.25rem;
  margin-bottom: 1rem;
  color: #444;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-field label {
  font-weight: 600;
  color: #555;
  font-size: 0.9rem;
}

.input-with-unit {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.form-field input {
  flex: 1;
  padding: 0.6rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-field input:focus {
  outline: none;
  border-color: #667eea;
}

.unit {
  font-size: 0.85rem;
  color: #666;
  min-width: 40px;
}

.hint {
  font-size: 0.8rem;
  color: #999;
  font-style: italic;
}

.button-group {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.button-group button {
  padding: 0.75rem 1.5rem;
  border: 2px solid #ddd;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.button-group button:hover {
  border-color: #667eea;
  color: #667eea;
}

.button-group button.active {
  background: #667eea;
  border-color: #667eea;
  color: white;
}

.preset-buttons {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.preset-btn {
  padding: 0.65rem 1.25rem;
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9rem;
}

.preset-btn:hover {
  background: #667eea;
  border-color: #667eea;
  color: white;
}

.actions {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.actions button {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #667eea;
  color: white;
}

.btn-primary:hover {
  background: #5568d3;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.btn-secondary {
  background: #f5f5f5;
  color: #333;
  border: 1px solid #ddd;
}

.btn-secondary:hover {
  background: #e8e8e8;
}

.btn-danger {
  background: #ef4444;
  color: white;
}

.btn-danger:hover {
  background: #dc2626;
}

.status-message {
  padding: 1rem;
  border-radius: 6px;
  margin-top: 1rem;
  font-weight: 500;
}

.status-message.success {
  background: #d1fae5;
  color: #065f46;
}

.status-message.error {
  background: #fee2e2;
  color: #991b1b;
}

.status-message.info {
  background: #dbeafe;
  color: #1e40af;
}

.preview {
  background: #fafafa;
  padding: 1.5rem;
  border-radius: 8px;
}

.body-preview {
  width: 100%;
  height: 600px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
}

/* CAM Results Styles */
.cam-results {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.5rem;
  border-radius: 8px;
  margin-top: 1.5rem;
}

.cam-results h3 {
  margin-top: 0;
  font-size: 1.4rem;
  margin-bottom: 1rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-item {
  background: rgba(255, 255, 255, 0.15);
  padding: 1rem;
  border-radius: 6px;
  backdrop-filter: blur(10px);
}

.stat-label {
  display: block;
  font-size: 0.85rem;
  opacity: 0.9;
  margin-bottom: 0.25rem;
  font-weight: 500;
}

.stat-value {
  display: block;
  font-size: 1.4rem;
  font-weight: 700;
}

.cam-params {
  background: rgba(255, 255, 255, 0.1);
  padding: 1rem;
  border-radius: 6px;
  margin-bottom: 1rem;
}

.cam-params h4 {
  margin-top: 0;
  margin-bottom: 0.75rem;
  font-size: 1.1rem;
}

.cam-params ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.cam-params li {
  padding: 0.5rem 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.cam-params li:last-child {
  border-bottom: none;
}

.cam-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
  margin-bottom: 1rem;
}

.post-selector {
  padding: 0.6rem 1rem;
  border: 2px solid rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.post-selector:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
}

.post-selector option {
  background: #764ba2;
  color: white;
}

.move-preview {
  background: rgba(0, 0, 0, 0.2);
  padding: 0.75rem;
  border-radius: 6px;
  margin-top: 1rem;
}

.move-preview summary {
  cursor: pointer;
  font-weight: 600;
  padding: 0.5rem;
  user-select: none;
}

.move-preview summary:hover {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

.gcode-preview {
  background: rgba(0, 0, 0, 0.3);
  padding: 1rem;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 0.85rem;
  line-height: 1.5;
  overflow-x: auto;
  margin-top: 0.75rem;
  white-space: pre;
}

.btn-success {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  font-weight: 600;
  box-shadow: 0 4px 6px rgba(16, 185, 129, 0.3);
}

.btn-success:hover:not(:disabled) {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  box-shadow: 0 6px 8px rgba(16, 185, 129, 0.4);
  transform: translateY(-2px);
}

.btn-success:disabled {
  background: #d1d5db;
  box-shadow: none;
  cursor: not-allowed;
}
</style>
