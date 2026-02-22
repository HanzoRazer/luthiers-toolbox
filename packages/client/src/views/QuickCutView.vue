<script setup lang="ts">
/**
 * Quick Cut View - Simplified DXF to G-code workflow
 *
 * 3-step onboarding flow for newcomers:
 * 1. Upload DXF file
 * 2. Select machine and basic parameters
 * 3. Review safety summary and download G-code
 *
 * Uses real RMOS API for safety gating.
 */
import { ref, computed } from 'vue'
import RiskBadge from '@/components/ui/RiskBadge.vue'
import RmosTooltip from '@/components/rmos/RmosTooltip.vue'
import styles from './QuickCutView.module.css'

const API_BASE = (import.meta as any).env?.VITE_API_BASE || ''

const currentStep = ref<1 | 2 | 3>(1)

// Step 1: Upload
const dxfFile = ref<File | null>(null)
const uploadError = ref<string | null>(null)

// Step 2: Configure
const machines = [
  { id: 'GRBL', name: 'GRBL 1.1', desc: 'Hobby CNC, Arduino-based' },
  { id: 'Mach4', name: 'Mach4', desc: 'Windows CNC control' },
  { id: 'LinuxCNC', name: 'LinuxCNC', desc: 'Open source CNC' },
  { id: 'PathPilot', name: 'PathPilot', desc: 'Tormach machines' },
  { id: 'MASSO', name: 'MASSO G3', desc: 'Standalone controller' }
]

const materials = [
  { id: 'softwood', name: 'Softwood (Pine, Cedar)', feed: 1500, plunge: 500 },
  { id: 'hardwood', name: 'Hardwood (Maple, Walnut)', feed: 1000, plunge: 300 },
  { id: 'plywood', name: 'Plywood / MDF', feed: 1200, plunge: 400 }
]

const selectedMachine = ref('GRBL')
const selectedMaterial = ref('softwood')
const toolDiameter = ref(6.0)
const stepdown = ref(3.0)
const targetDepth = ref(-6.0)

// Step 3: Result
const isGenerating = ref(false)
const result = ref<any>(null)
const generateError = ref<string | null>(null)

const selectedMaterialData = computed(() =>
  materials.find(m => m.id === selectedMaterial.value)
)

const riskLevel = computed(() =>
  String(result.value?.decision?.risk_level || '').toUpperCase()
)

const riskClass = computed(() => {
  const rl = riskLevel.value
  if (rl === 'GREEN') return 'risk-green'
  if (rl === 'YELLOW') return 'risk-yellow'
  if (rl === 'RED') return 'risk-red'
  return ''
})

const riskIcon = computed(() => {
  const rl = riskLevel.value
  if (rl === 'GREEN') return '✓'
  if (rl === 'YELLOW') return '⚠'
  if (rl === 'RED') return '⛔'
  return '?'
})

const warnings = computed(() =>
  result.value?.decision?.warnings || []
)

const canDownload = computed(() =>
  result.value?.gcode?.text && riskLevel.value !== 'RED'
)

const gcodeText = computed(() =>
  result.value?.gcode?.text || ''
)

const gcodePreview = computed(() => {
  const text = gcodeText.value
  if (!text) return ''
  const lines = text.split('\n')
  if (lines.length <= 20) return text
  return lines.slice(0, 15).join('\n') + '\n\n... (' + (lines.length - 15) + ' more lines) ...'
})

function handleFileUpload(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  uploadError.value = null

  if (!file) return

  if (!file.name.toLowerCase().endsWith('.dxf')) {
    uploadError.value = 'Please select a DXF file (.dxf)'
    return
  }

  dxfFile.value = file
}

function handleDrop(event: DragEvent) {
  event.preventDefault()
  const file = event.dataTransfer?.files?.[0]
  uploadError.value = null

  if (!file) return

  if (!file.name.toLowerCase().endsWith('.dxf')) {
    uploadError.value = 'Please select a DXF file (.dxf)'
    return
  }

  dxfFile.value = file
}

async function generateGcode() {
  if (!dxfFile.value) return

  isGenerating.value = true
  generateError.value = null
  result.value = null

  try {
    const mat = selectedMaterialData.value
    const fd = new FormData()
    fd.append('file', dxfFile.value)
    fd.append('tool_d', String(toolDiameter.value))
    fd.append('stepdown', String(stepdown.value))
    fd.append('z_rough', String(targetDepth.value))
    fd.append('feed_xy', String(mat?.feed || 1200))
    fd.append('feed_z', String(mat?.plunge || 300))
    fd.append('safe_z', '5.0')
    fd.append('stepover', '0.45')
    fd.append('strategy', 'Spiral')
    fd.append('post_id', selectedMachine.value)

    const response = await fetch(`${API_BASE}/api/rmos/wrap/mvp/dxf-to-grbl`, {
      method: 'POST',
      body: fd
    })

    if (!response.ok) {
      const data = await response.json().catch(() => ({}))
      throw new Error(data.detail || `HTTP ${response.status}`)
    }

    result.value = await response.json()
    currentStep.value = 3

  } catch (err: any) {
    generateError.value = err.message || 'Failed to generate G-code'
  } finally {
    isGenerating.value = false
  }
}

function downloadGcode() {
  if (!canDownload.value) return

  const blob = new Blob([gcodeText.value], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  const baseName = (dxfFile.value?.name || 'output').replace(/\.dxf$/i, '')
  a.download = `${baseName}_${selectedMachine.value}.nc`
  a.click()
  URL.revokeObjectURL(url)
}

function reset() {
  currentStep.value = 1
  dxfFile.value = null
  uploadError.value = null
  result.value = null
  generateError.value = null
}
</script>

<template>
  <div :class="styles.quickCutView">
    <header :class="styles.qcHeader">
      <h1>Quick Cut</h1>
      <p :class="styles.subtitle">DXF to G-code in 3 steps</p>
    </header>

    <!-- Step Indicator -->
    <div :class="styles.stepsIndicator">
      <div :class="currentStep === 1 ? styles.stepActive : currentStep > 1 ? styles.stepDone : styles.step">
        <span :class="currentStep === 1 ? styles.stepNumActive : currentStep > 1 ? styles.stepNumDone : styles.stepNum">1</span>
        <span :class="styles.stepLabel">Upload</span>
      </div>
      <div :class="currentStep > 1 ? styles.stepLineDone : styles.stepLine"></div>
      <div :class="currentStep === 2 ? styles.stepActive : currentStep > 2 ? styles.stepDone : styles.step">
        <span :class="currentStep === 2 ? styles.stepNumActive : currentStep > 2 ? styles.stepNumDone : styles.stepNum">2</span>
        <span :class="styles.stepLabel">Configure</span>
      </div>
      <div :class="currentStep > 2 ? styles.stepLineDone : styles.stepLine"></div>
      <div :class="currentStep === 3 ? styles.stepActive : styles.step">
        <span :class="currentStep === 3 ? styles.stepNumActive : styles.stepNum">3</span>
        <span :class="styles.stepLabel">Export</span>
      </div>
    </div>

    <!-- Step 1: Upload DXF -->
    <div v-if="currentStep === 1" :class="styles.stepContent">
      <div
        :class="dxfFile ? styles.uploadZoneHasFile : styles.uploadZone"
        @drop="handleDrop"
        @dragover.prevent
      >
        <input
          type="file"
          accept=".dxf"
          @change="handleFileUpload"
          :style="{ display: dxfFile ? 'none' : 'block' }"
        />
        <div v-if="!dxfFile" :class="styles.uploadPrompt">
          <p :class="styles.uploadIcon">📄</p>
          <p><strong>Drop DXF here</strong> or click to browse</p>
          <p :class="styles.hint">DXF R12/R2000 format • Closed polylines for pockets</p>
        </div>
        <div v-else :class="styles.fileSelected">
          <span :class="styles.filename">{{ dxfFile.name }}</span>
          <span :class="styles.filesize">({{ (dxfFile.size / 1024).toFixed(1) }} KB)</span>
          <button :class="styles.clearBtn" @click="dxfFile = null">×</button>
        </div>
      </div>

      <p v-if="uploadError" :class="styles.error">{{ uploadError }}</p>

      <div :class="styles.stepActions">
        <button
          :class="styles.btnPrimary"
          :disabled="!dxfFile"
          @click="currentStep = 2"
        >
          Next: Configure
        </button>
      </div>
    </div>

    <!-- Step 2: Configure Machine & Parameters -->
    <div v-if="currentStep === 2" :class="styles.stepContent">
      <div :class="styles.configGrid">
        <div :class="styles.configSection">
          <h3>Machine</h3>
          <select v-model="selectedMachine" :class="styles.selectInput">
            <option v-for="m in machines" :key="m.id" :value="m.id">
              {{ m.name }}
            </option>
          </select>
          <p :class="styles.hint">{{ machines.find(m => m.id === selectedMachine)?.desc }}</p>
        </div>

        <div :class="styles.configSection">
          <h3>Material</h3>
          <select v-model="selectedMaterial" :class="styles.selectInput">
            <option v-for="m in materials" :key="m.id" :value="m.id">
              {{ m.name }}
            </option>
          </select>
          <p :class="styles.hint">Feed: {{ selectedMaterialData?.feed }} mm/min</p>
        </div>

        <div :class="styles.configSection">
          <h3>Tool Diameter (mm)</h3>
          <input
            type="number"
            v-model.number="toolDiameter"
            min="0.5"
            max="25"
            step="0.5"
            :class="styles.numberInput"
          />
        </div>

        <div :class="styles.configSection">
          <h3>Stepdown (mm)</h3>
          <input
            type="number"
            v-model.number="stepdown"
            min="0.5"
            max="10"
            step="0.5"
            :class="styles.numberInput"
          />
        </div>

        <div :class="styles.configSectionFullWidth">
          <h3>Target Depth (mm)</h3>
          <input
            type="number"
            v-model.number="targetDepth"
            max="0"
            step="0.5"
            :class="styles.numberInput"
          />
          <p :class="styles.hint">Negative value (e.g., -6 for 6mm deep pocket)</p>
        </div>
      </div>

      <p v-if="generateError" :class="styles.error">{{ generateError }}</p>

      <div :class="styles.stepActions">
        <button :class="styles.btnSecondary" @click="currentStep = 1">Back</button>
        <button
          :class="styles.btnPrimary"
          :disabled="isGenerating"
          @click="generateGcode"
        >
          {{ isGenerating ? 'Generating...' : 'Generate G-code' }}
        </button>
      </div>
    </div>

    <!-- Step 3: Review & Export -->
    <div v-if="currentStep === 3" :class="styles.stepContent">
      <!-- Safety Summary -->
      <div :class="riskLevel === 'GREEN' ? styles.safetySummaryGreen : riskLevel === 'YELLOW' ? styles.safetySummaryYellow : riskLevel === 'RED' ? styles.safetySummaryRed : styles.safetySummary">
        <div :class="styles.safetyHeader">
          <RiskBadge :level="riskLevel" size="lg" />
          <span :class="styles.safetyLabel">
            Safety Check
            <RmosTooltip concept="feasibility" :inline="true" />
          </span>
        </div>

        <div v-if="riskLevel === 'GREEN'" :class="styles.safetyMessage">
          All checks passed. Safe to run on machine.
          <RmosTooltip concept="risk-green" :inline="true" />
        </div>
        <div v-else-if="riskLevel === 'YELLOW'" :class="styles.safetyMessage">
          Review warnings before proceeding. Download available.
          <RmosTooltip concept="risk-yellow" :inline="true" />
        </div>
        <div v-else-if="riskLevel === 'RED'" :class="styles.safetyMessage">
          Blocked for safety. Review parameters and try again.
          <RmosTooltip concept="risk-red" :inline="true" />
        </div>

        <ul v-if="warnings.length > 0" :class="styles.warningsList">
          <li v-for="(w, i) in warnings" :key="i">{{ w }}</li>
        </ul>
      </div>

      <!-- G-code Preview -->
      <div :class="styles.gcodePreview">
        <h3>G-code Preview</h3>
        <pre :class="styles.gcodeBlock">{{ gcodePreview }}</pre>
      </div>

      <!-- Export Info -->
      <div :class="styles.exportInfo">
        <p><strong>File:</strong> {{ dxfFile?.name }}</p>
        <p><strong>Machine:</strong> {{ machines.find(m => m.id === selectedMachine)?.name }}</p>
        <p><strong>Material:</strong> {{ materials.find(m => m.id === selectedMaterial)?.name }}</p>
        <p><strong>Tool:</strong> {{ toolDiameter }}mm, {{ stepdown }}mm stepdown</p>
        <p v-if="result?.run_id" :class="styles.runId">
          <strong>Run ID:</strong> {{ result.run_id }}
          <RmosTooltip concept="run-id" :inline="true" />
        </p>
      </div>

      <div :class="styles.stepActions">
        <button :class="styles.btnSecondary" @click="currentStep = 2">Back</button>
        <button
          :class="styles.btnPrimary"
          :disabled="!canDownload"
          @click="downloadGcode"
        >
          {{ riskLevel === 'RED' ? 'Blocked' : 'Download G-code' }}
        </button>
        <button :class="styles.btnSecondary" @click="reset">Start Over</button>
      </div>
    </div>
  </div>
</template>

