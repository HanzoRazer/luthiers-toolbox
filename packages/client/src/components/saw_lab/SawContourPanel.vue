<template>
  <div :class="styles.sawContourPanel">
    <div :class="styles.panelHeader">
      <h2>Saw Contour Operation</h2>
      <p :class="styles.subtitle">
        Curved paths for rosettes and binding with radius validation
      </p>
    </div>

    <div :class="styles.panelContent">
      <!-- Left Column: Parameters -->
      <div :class="styles.parametersSection">
        <h3>Contour Parameters</h3>

        <!-- Blade Selection -->
        <div :class="styles.formGroup">
          <label>Saw Blade</label>
          <select
            v-model="selectedBladeId"
            @change="onBladeChange"
          >
            <option value="">
              Select blade...
            </option>
            <option
              v-for="blade in blades"
              :key="blade.blade_id"
              :value="blade.blade_id"
            >
              {{ blade.vendor }} {{ blade.model_code }} ({{ blade.diameter_mm }}mm)
            </option>
          </select>
          <div
            v-if="selectedBlade"
            :class="styles.bladeInfo"
          >
            Min radius: {{ (selectedBlade.diameter_mm / 2).toFixed(1) }}mm | Kerf: {{ selectedBlade.kerf_mm }}mm
          </div>
        </div>

        <!-- Machine & Material -->
        <div :class="styles.formGroup">
          <label>Machine Profile</label>
          <select v-model="machineProfile">
            <option value="bcam_router_2030">
              BCAM Router 2030
            </option>
            <option value="syil_x7">
              SYIL X7
            </option>
            <option value="tormach_1100mx">
              Tormach 1100MX
            </option>
          </select>
        </div>

        <div :class="styles.formGroup">
          <label>Material Family</label>
          <select v-model="materialFamily">
            <option value="hardwood">
              Hardwood
            </option>
            <option value="softwood">
              Softwood
            </option>
            <option value="plywood">
              Plywood
            </option>
            <option value="mdf">
              MDF
            </option>
          </select>
        </div>

        <!-- Contour Type -->
        <div :class="styles.formGroup">
          <label>Contour Type</label>
          <select
            v-model="contourType"
            @change="updateContourPath"
          >
            <option value="arc">
              Arc Segment
            </option>
            <option value="circle">
              Full Circle
            </option>
            <option value="rosette">
              Rosette Pattern
            </option>
          </select>
        </div>

        <!-- Arc Parameters -->
        <div v-if="contourType === 'arc'">
          <div :class="styles.formGroup">
            <label>Center X (mm)</label>
            <input
              v-model.number="centerX"
              type="number"
              step="0.1"
              @input="updateContourPath"
            >
          </div>

          <div :class="styles.formGroup">
            <label>Center Y (mm)</label>
            <input
              v-model.number="centerY"
              type="number"
              step="0.1"
              @input="updateContourPath"
            >
          </div>

          <div :class="styles.formGroup">
            <label>Radius (mm)</label>
            <input
              v-model.number="radius"
              type="number"
              step="1"
              min="1"
              @input="updateContourPath"
            >
            <div
              v-if="radiusValidation"
              :class="[styles.validationHint, styles[`validationHint${radiusValidation.status.charAt(0).toUpperCase()}${radiusValidation.status.slice(1)}`]]"
            >
              {{ radiusValidation.message }}
            </div>
          </div>

          <div :class="styles.formGroup">
            <label>Start Angle (degrees)</label>
            <input
              v-model.number="startAngle"
              type="number"
              step="15"
              min="0"
              max="360"
              @input="updateContourPath"
            >
          </div>

          <div :class="styles.formGroup">
            <label>End Angle (degrees)</label>
            <input
              v-model.number="endAngle"
              type="number"
              step="15"
              min="0"
              max="360"
              @input="updateContourPath"
            >
          </div>
        </div>

        <!-- Circle Parameters -->
        <div v-if="contourType === 'circle'">
          <div :class="styles.formGroup">
            <label>Center X (mm)</label>
            <input
              v-model.number="centerX"
              type="number"
              step="0.1"
              @input="updateContourPath"
            >
          </div>

          <div :class="styles.formGroup">
            <label>Center Y (mm)</label>
            <input
              v-model.number="centerY"
              type="number"
              step="0.1"
              @input="updateContourPath"
            >
          </div>

          <div :class="styles.formGroup">
            <label>Radius (mm)</label>
            <input
              v-model.number="radius"
              type="number"
              step="1"
              min="1"
              @input="updateContourPath"
            >
            <div
              v-if="radiusValidation"
              :class="[styles.validationHint, styles[`validationHint${radiusValidation.status.charAt(0).toUpperCase()}${radiusValidation.status.slice(1)}`]]"
            >
              {{ radiusValidation.message }}
            </div>
          </div>
        </div>

        <!-- Rosette Parameters -->
        <div v-if="contourType === 'rosette'">
          <div :class="styles.formGroup">
            <label>Center X (mm)</label>
            <input
              v-model.number="centerX"
              type="number"
              step="0.1"
              @input="updateContourPath"
            >
          </div>

          <div :class="styles.formGroup">
            <label>Center Y (mm)</label>
            <input
              v-model.number="centerY"
              type="number"
              step="0.1"
              @input="updateContourPath"
            >
          </div>

          <div :class="styles.formGroup">
            <label>Outer Radius (mm)</label>
            <input
              v-model.number="outerRadius"
              type="number"
              step="1"
              min="1"
              @input="updateContourPath"
            >
          </div>

          <div :class="styles.formGroup">
            <label>Inner Radius (mm)</label>
            <input
              v-model.number="innerRadius"
              type="number"
              step="1"
              min="1"
              @input="updateContourPath"
            >
            <div
              v-if="radiusValidation"
              :class="[styles.validationHint, styles[`validationHint${radiusValidation.status.charAt(0).toUpperCase()}${radiusValidation.status.slice(1)}`]]"
            >
              {{ radiusValidation.message }}
            </div>
          </div>

          <div :class="styles.formGroup">
            <label>Number of Petals</label>
            <input
              v-model.number="petalCount"
              type="number"
              step="1"
              min="3"
              max="24"
              @input="updateContourPath"
            >
          </div>
        </div>

        <!-- Depth Parameters -->
        <div :class="styles.formGroup">
          <label>Total Depth (mm)</label>
          <input
            v-model.number="totalDepth"
            type="number"
            step="0.5"
            min="0.5"
          >
        </div>

        <div :class="styles.formGroup">
          <label>Depth Per Pass (mm)</label>
          <input
            v-model.number="depthPerPass"
            type="number"
            step="0.5"
            min="0.5"
          >
        </div>

        <!-- Feeds & Speeds -->
        <div :class="styles.formGroup">
          <label>RPM</label>
          <input
            v-model.number="rpm"
            type="number"
            step="100"
            min="2000"
            max="6000"
          >
        </div>

        <div :class="styles.formGroup">
          <label>Feed Rate (IPM)</label>
          <input
            v-model.number="feedIpm"
            type="number"
            step="5"
            min="10"
            max="300"
          >
        </div>

        <div :class="styles.formGroup">
          <label>Safe Z (mm)</label>
          <input
            v-model.number="safeZ"
            type="number"
            step="0.5"
            min="1"
          >
        </div>

        <!-- Actions -->
        <div :class="styles.actions">
          <button
            :disabled="!canValidate"
            :class="styles.btnPrimary"
            @click="validateContour"
          >
            Validate Contour
          </button>
          <button
            :disabled="!canMerge"
            :class="styles.btnSecondary"
            @click="mergeLearnedParams"
          >
            Apply Learned Overrides
          </button>
          <button
            :disabled="!isValid"
            :class="styles.btnPrimary"
            @click="generateGcode"
          >
            Generate G-code
          </button>
          <button
            :disabled="!hasGcode"
            :class="styles.btnSuccess"
            @click="sendToJobLog"
          >
            Send to JobLog
          </button>
        </div>
      </div>

      <!-- Right Column: Preview & Validation -->
      <div :class="styles.previewSection">
        <!-- Radius Validation -->
        <div
          v-if="radiusValidation"
          :class="styles.radiusValidation"
        >
          <h3>Radius Validation</h3>
          <div :class="[styles.validationBadge, styles[`validationBadge${radiusValidation.status.charAt(0).toUpperCase()}${radiusValidation.status.slice(1)}`]]">
            {{ radiusValidation.status.toUpperCase() }}
          </div>
          <div :class="styles.validationDetails">
            <div :class="styles.detailRow">
              <span :class="styles.label">Minimum radius:</span>
              <span :class="styles.value">{{ radiusValidation.min_radius?.toFixed(1) || 'N/A' }} mm</span>
            </div>
            <div :class="styles.detailRow">
              <span :class="styles.label">Requested radius:</span>
              <span :class="styles.value">{{ radiusValidation.requested_radius?.toFixed(1) || 'N/A' }} mm</span>
            </div>
            <div :class="styles.detailRow">
              <span :class="styles.label">Safety margin:</span>
              <span :class="styles.value">{{ radiusValidation.safety_margin?.toFixed(1) || 'N/A' }}%</span>
            </div>
          </div>
          <div :class="styles.validationMessage">
            {{ radiusValidation.message }}
          </div>
        </div>

        <!-- Validation Results -->
        <div
          v-if="validationResult"
          :class="styles.validationResults"
        >
          <h3>Full Validation Results</h3>
          <div :class="[styles.validationBadge, styles[`validationBadge${validationResult.overall_result.charAt(0).toUpperCase()}${validationResult.overall_result.slice(1).toLowerCase()}`]]">
            {{ validationResult.overall_result }}
          </div>
          <div :class="styles.validationChecks">
            <div
              v-for="(check, key) in validationResult.checks"
              :key="key"
              :class="[styles.checkItem, styles[`checkItem${check.result.charAt(0).toUpperCase()}${check.result.slice(1).toLowerCase()}`]]"
            >
              <span :class="styles.checkIcon">{{ check.result === 'OK' ? '✓' : check.result === 'WARN' ? '⚠' : '✗' }}</span>
              <span :class="styles.checkName">{{ formatCheckName(String(key)) }}</span>
              <span :class="styles.checkMessage">{{ check.message }}</span>
            </div>
          </div>
        </div>

        <!-- Learned Parameters -->
        <div
          v-if="mergedParams"
          :class="styles.learnedParams"
        >
          <h3>Learned Parameters Applied</h3>
          <div :class="styles.paramComparison">
            <div :class="styles.paramRow">
              <span :class="styles.label">RPM:</span>
              <span :class="styles.baseline">{{ rpm }}</span>
              <span :class="styles.arrow">→</span>
              <span :class="styles.merged">{{ mergedParams.rpm?.toFixed(0) || rpm }}</span>
            </div>
            <div :class="styles.paramRow">
              <span :class="styles.label">Feed:</span>
              <span :class="styles.baseline">{{ feedIpm }}</span>
              <span :class="styles.arrow">→</span>
              <span :class="styles.merged">{{ mergedParams.feed_ipm?.toFixed(1) || feedIpm }}</span>
            </div>
            <div :class="styles.paramRow">
              <span :class="styles.label">DOC:</span>
              <span :class="styles.baseline">{{ depthPerPass }}</span>
              <span :class="styles.arrow">→</span>
              <span :class="styles.merged">{{ mergedParams.doc_mm?.toFixed(1) || depthPerPass }}</span>
            </div>
          </div>
        </div>

        <!-- Path Statistics -->
        <div
          v-if="pathStats"
          :class="styles.pathStats"
        >
          <h3>Path Statistics</h3>
          <div :class="styles.statsGrid">
            <div :class="styles.statItem">
              <span :class="styles.statLabel">Path Length:</span>
              <span :class="styles.statValue">{{ pathStats.length_mm.toFixed(1) }} mm</span>
            </div>
            <div :class="styles.statItem">
              <span :class="styles.statLabel">Depth Passes:</span>
              <span :class="styles.statValue">{{ depthPasses }}</span>
            </div>
            <div :class="styles.statItem">
              <span :class="styles.statLabel">Total Length:</span>
              <span :class="styles.statValue">{{ totalLengthMm.toFixed(1) }} mm</span>
            </div>
            <div :class="styles.statItem">
              <span :class="styles.statLabel">Est. Time:</span>
              <span :class="styles.statValue">{{ estimatedTimeSec.toFixed(0) }}s</span>
            </div>
          </div>
        </div>

        <!-- SVG Preview -->
        <div :class="styles.svgPreview">
          <h3>Contour Preview</h3>
          <svg
            :viewBox="svgViewBox"
            width="100%"
            height="400"
            :class="styles.previewCanvas"
          >
            <!-- Grid -->
            <defs>
              <pattern
                id="contour-grid"
                width="20"
                height="20"
                patternUnits="userSpaceOnUse"
              >
                <path
                  d="M 20 0 L 0 0 0 20"
                  fill="none"
                  stroke="#e0e0e0"
                  stroke-width="0.5"
                />
              </pattern>
            </defs>
            <rect
              width="100%"
              height="100%"
              fill="url(#contour-grid)"
            />
            
            <!-- Contour path -->
            <path
              v-if="contourPath"
              :d="contourPath"
              fill="none"
              stroke="#2196F3"
              stroke-width="3"
            />
            
            <!-- Center marker -->
            <circle
              :cx="centerX"
              :cy="centerY"
              r="3"
              fill="#F44336"
            />
            <text
              :x="centerX + 8"
              :y="centerY + 5"
              font-size="12"
              fill="#666"
            >Center</text>
            
            <!-- Radius indicator -->
            <line
              v-if="contourType !== 'rosette'"
              :x1="centerX"
              :y1="centerY"
              :x2="centerX + (radius || 0)"
              :y2="centerY"
              stroke="#9C27B0"
              stroke-width="1"
              stroke-dasharray="5,5"
            />
            <text
              v-if="contourType !== 'rosette'"
              :x="centerX + (radius || 0) / 2"
              :y="centerY - 8"
              font-size="11"
              fill="#9C27B0"
              text-anchor="middle"
            >R={{ radius }}</text>
          </svg>
          <div :class="styles.legend">
            <span><span
              :class="styles.colorBox"
              style="background: #2196F3;"
            /> Cut path</span>
            <span><span
              :class="styles.colorBox"
              style="background: #F44336;"
            /> Center</span>
            <span><span
              :class="styles.colorBox"
              style="background: #9C27B0;"
            /> Radius</span>
          </div>
        </div>

        <!-- G-code Preview -->
        <div
          v-if="gcode"
          :class="styles.gcodePreview"
        >
          <h3>G-code Preview</h3>
          <pre :class="styles.gcodeText">{{ gcodePreview }}</pre>
          <button
            :class="styles.btnSecondary"
            @click="downloadGcode"
          >
            Download G-code
          </button>
        </div>

        <!-- Run Artifact Link -->
        <div
          v-if="runId"
          :class="styles.runArtifactLink"
        >
          <h3>Run Artifact</h3>
          <p>Job logged with Run ID: <code>{{ runId }}</code></p>
          <router-link
            :to="`/rmos/runs?run_id=${runId}`"
            :class="styles.btnPrimary"
          >
            View Run Artifact
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { api } from '@/services/apiBase';
import { ref, computed, onMounted } from 'vue'
import styles from './SawContourPanel.module.css'

// ============================================================================
// State
// ============================================================================

const blades = ref<any[]>([])
const selectedBladeId = ref<string>('')
const selectedBlade = ref<any>(null)

const machineProfile = ref<string>('bcam_router_2030')
const materialFamily = ref<string>('hardwood')

const contourType = ref<string>('arc')
const centerX = ref<number>(100)
const centerY = ref<number>(100)
const radius = ref<number>(50)
const startAngle = ref<number>(0)
const endAngle = ref<number>(180)

const outerRadius = ref<number>(80)
const innerRadius = ref<number>(40)
const petalCount = ref<number>(6)

const totalDepth = ref<number>(6)
const depthPerPass = ref<number>(2)

const rpm = ref<number>(3600)
const feedIpm = ref<number>(100)
const safeZ = ref<number>(5)

const radiusValidation = ref<any>(null)
const validationResult = ref<any>(null)
const mergedParams = ref<any>(null)
const gcode = ref<string>('')
const contourPath = ref<string>('')
const runId = ref<string>('')

// ============================================================================
// Computed
// ============================================================================

const canValidate = computed(() => {
  return selectedBladeId.value && radius.value > 0
})

const canMerge = computed(() => {
  return selectedBladeId.value && machineProfile.value && materialFamily.value
})

const isValid = computed(() => {
  return validationResult.value && validationResult.value.overall_result !== 'ERROR'
})

const hasGcode = computed(() => {
  return gcode.value.length > 0
})

const depthPasses = computed(() => {
  return Math.ceil(totalDepth.value / depthPerPass.value)
})

const pathStats = computed(() => {
  let length = 0
  
  if (contourType.value === 'arc') {
    const angleRad = ((endAngle.value - startAngle.value) * Math.PI) / 180
    length = radius.value * angleRad
  } else if (contourType.value === 'circle') {
    length = 2 * Math.PI * radius.value
  } else if (contourType.value === 'rosette') {
    // Approximate rosette length
    const avgRadius = (outerRadius.value + innerRadius.value) / 2
    length = 2 * Math.PI * avgRadius * petalCount.value
  }
  
  return { length_mm: length }
})

const totalLengthMm = computed(() => {
  return pathStats.value.length_mm * depthPasses.value
})

const estimatedTimeSec = computed(() => {
  const feedMmMin = feedIpm.value * 25.4
  return (totalLengthMm.value / feedMmMin) * 60
})

const gcodePreview = computed(() => {
  if (!gcode.value) return ''
  const lines = gcode.value.split('\n')
  return lines.slice(0, 20).join('\n') + '\n...\n' + lines.slice(-5).join('\n')
})

const svgViewBox = computed(() => {
  const maxRadius = contourType.value === 'rosette' ? outerRadius.value : radius.value
  const padding = 40
  const minX = centerX.value - maxRadius - padding
  const minY = centerY.value - maxRadius - padding
  const width = (maxRadius + padding) * 2
  const height = (maxRadius + padding) * 2
  return `${minX} ${minY} ${width} ${height}`
})

// ============================================================================
// Functions
// ============================================================================

function updateContourPath() {
  if (contourType.value === 'arc') {
    const startRad = (startAngle.value * Math.PI) / 180
    const endRad = (endAngle.value * Math.PI) / 180
    
    const x1 = centerX.value + radius.value * Math.cos(startRad)
    const y1 = centerY.value + radius.value * Math.sin(startRad)
    const x2 = centerX.value + radius.value * Math.cos(endRad)
    const y2 = centerY.value + radius.value * Math.sin(endRad)
    
    const largeArc = Math.abs(endAngle.value - startAngle.value) > 180 ? 1 : 0
    
    contourPath.value = `M ${x1} ${y1} A ${radius.value} ${radius.value} 0 ${largeArc} 1 ${x2} ${y2}`
  } else if (contourType.value === 'circle') {
    const x1 = centerX.value + radius.value
    const y1 = centerY.value
    const x2 = centerX.value - radius.value
    const y2 = centerY.value
    
    contourPath.value = `M ${x1} ${y1} A ${radius.value} ${radius.value} 0 1 1 ${x2} ${y2} A ${radius.value} ${radius.value} 0 1 1 ${x1} ${y1}`
  } else if (contourType.value === 'rosette') {
    const points: { x: number; y: number }[] = []
    const angleStep = (2 * Math.PI) / (petalCount.value * 2)
    
    for (let i = 0; i <= petalCount.value * 2; i++) {
      const angle = i * angleStep
      const r = i % 2 === 0 ? outerRadius.value : innerRadius.value
      const x = centerX.value + r * Math.cos(angle)
      const y = centerY.value + r * Math.sin(angle)
      points.push({ x, y })
    }
    
    contourPath.value = points.map((p, i) => 
      i === 0 ? `M ${p.x} ${p.y}` : `L ${p.x} ${p.y}`
    ).join(' ') + ' Z'
  }
  
  validateRadius()
}

async function validateRadius() {
  if (!selectedBlade.value) return
  
  const minRadius = contourType.value === 'rosette' ? innerRadius.value : radius.value
  
  const payload = {
    blade_diameter_mm: selectedBlade.value.diameter_mm,
    requested_radius_mm: minRadius
  }
  
  try {
    const response = await api('/api/saw/validate/contour', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    radiusValidation.value = await response.json()
  } catch (err) {
    console.error('Radius validation failed:', err)
  }
}

async function loadBlades() {
  try {
    const response = await api('/api/saw/blades')
    blades.value = await response.json()
  } catch (err) {
    console.error('Failed to load blades:', err)
  }
}

async function onBladeChange() {
  const blade = blades.value.find(b => b.blade_id === selectedBladeId.value)
  selectedBlade.value = blade
  
  validationResult.value = null
  mergedParams.value = null
  updateContourPath()
}

async function validateContour() {
  if (!selectedBlade.value) return
  
  const payload = {
    blade: selectedBlade.value,
    op_type: 'contour',
    material_family: materialFamily.value,
    planned_rpm: rpm.value,
    planned_feed_ipm: feedIpm.value,
    planned_doc_mm: depthPerPass.value
  }
  
  try {
    const response = await api('/api/saw/validate/operation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    validationResult.value = await response.json()
  } catch (err) {
    console.error('Validation failed:', err)
  }
}

async function mergeLearnedParams() {
  const laneKey = {
    tool_id: selectedBladeId.value,
    material: materialFamily.value,
    mode: 'contour',
    machine_profile: machineProfile.value
  }
  
  const baseline = {
    rpm: rpm.value,
    feed_ipm: feedIpm.value,
    doc_mm: depthPerPass.value,
    safe_z: safeZ.value
  }
  
  try {
    const response = await api('/api/feeds/learned/merge', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lane_key: laneKey, baseline })
    })
    const result = await response.json()
    mergedParams.value = result.merged
    
    rpm.value = result.merged.rpm
    feedIpm.value = result.merged.feed_ipm
    depthPerPass.value = result.merged.doc_mm
  } catch (err) {
    console.error('Failed to merge learned params:', err)
  }
}

async function generateGcode() {
  const lines: string[] = []
  
  // Header
  lines.push('G21  ; Metric units')
  lines.push('G90  ; Absolute positioning')
  lines.push('G17  ; XY plane')
  lines.push(`(Saw Contour: ${contourType.value})`)
  lines.push(`(Blade: ${selectedBlade.value.vendor} ${selectedBlade.value.model_code})`)
  lines.push('')
  
  lines.push(`G0 Z${safeZ.value.toFixed(3)}  ; Safe Z`)
  
  // Generate contour moves (simplified - real implementation would need arc conversion)
  for (let pass = 1; pass <= depthPasses.value; pass++) {
    const depth = Math.min(pass * depthPerPass.value, totalDepth.value)
    lines.push(`; Pass ${pass} of ${depthPasses.value} (depth: ${depth}mm)`)
    
    if (contourType.value === 'circle') {
      const startX = centerX.value + radius.value
      const startY = centerY.value
      
      lines.push(`G0 X${startX.toFixed(3)} Y${startY.toFixed(3)}  ; Move to start`)
      lines.push(`G1 Z${-depth.toFixed(3)} F${(feedIpm.value * 25.4 / 5).toFixed(1)}  ; Plunge`)
      lines.push(`G2 I${(-radius.value).toFixed(3)} J0 F${(feedIpm.value * 25.4).toFixed(1)}  ; Cut circle`)
      lines.push(`G0 Z${safeZ.value.toFixed(3)}  ; Retract`)
    } else {
      lines.push(`; Contour path - simplified`)
      lines.push(`G0 X${centerX.value.toFixed(3)} Y${centerY.value.toFixed(3)}`)
      lines.push(`G1 Z${-depth.toFixed(3)} F${(feedIpm.value * 25.4 / 5).toFixed(1)}`)
      lines.push(`; (Arc/rosette moves would be generated here)`)
      lines.push(`G0 Z${safeZ.value.toFixed(3)}`)
    }
    lines.push('')
  }
  
  lines.push('M30  ; Program end')
  
  gcode.value = lines.join('\n')
}

async function sendToJobLog() {
  const payload = {
    op_type: 'contour',
    machine_profile: machineProfile.value,
    material_family: materialFamily.value,
    blade_id: selectedBladeId.value,
    safe_z: safeZ.value,
    depth_passes: depthPasses.value,
    total_length_mm: totalLengthMm.value,
    planned_rpm: rpm.value,
    planned_feed_ipm: feedIpm.value,
    planned_doc_mm: depthPerPass.value,
    operator_notes: `Contour: ${contourType.value}, radius ${radius.value}mm`
  }
  
  try {
    const response = await api('/api/saw/joblog/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    const run = await response.json()
    runId.value = run.run_id

    alert(`Contour sent to job log! Run ID: ${run.run_id}`)
  } catch (err) {
    console.error('Failed to send to job log:', err)
    alert('Failed to send to job log')
  }
}

function downloadGcode() {
  const blob = new Blob([gcode.value], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `saw_contour_${contourType.value}_${selectedBlade.value?.model_code || 'unknown'}.nc`
  a.click()
  URL.revokeObjectURL(url)
}

function formatCheckName(key: string): string {
  return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

// ============================================================================
// Lifecycle
// ============================================================================

onMounted(() => {
  loadBlades()
  updateContourPath()
})
</script>
