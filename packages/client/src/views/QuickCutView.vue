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
  <div class="quick-cut-view">
    <header class="qc-header">
      <h1>Quick Cut</h1>
      <p class="subtitle">DXF to G-code in 3 steps</p>
    </header>

    <!-- Step Indicator -->
    <div class="steps-indicator">
      <div :class="['step', { active: currentStep === 1, done: currentStep > 1 }]">
        <span class="step-num">1</span>
        <span class="step-label">Upload</span>
      </div>
      <div class="step-line" :class="{ done: currentStep > 1 }"></div>
      <div :class="['step', { active: currentStep === 2, done: currentStep > 2 }]">
        <span class="step-num">2</span>
        <span class="step-label">Configure</span>
      </div>
      <div class="step-line" :class="{ done: currentStep > 2 }"></div>
      <div :class="['step', { active: currentStep === 3 }]">
        <span class="step-num">3</span>
        <span class="step-label">Export</span>
      </div>
    </div>

    <!-- Step 1: Upload DXF -->
    <div v-if="currentStep === 1" class="step-content">
      <div
        class="upload-zone"
        :class="{ 'has-file': !!dxfFile }"
        @drop="handleDrop"
        @dragover.prevent
      >
        <input
          type="file"
          accept=".dxf"
          @change="handleFileUpload"
          :style="{ display: dxfFile ? 'none' : 'block' }"
        />
        <div v-if="!dxfFile" class="upload-prompt">
          <p class="upload-icon">📄</p>
          <p><strong>Drop DXF here</strong> or click to browse</p>
          <p class="hint">DXF R12/R2000 format • Closed polylines for pockets</p>
        </div>
        <div v-else class="file-selected">
          <span class="filename">{{ dxfFile.name }}</span>
          <span class="filesize">({{ (dxfFile.size / 1024).toFixed(1) }} KB)</span>
          <button class="clear-btn" @click="dxfFile = null">×</button>
        </div>
      </div>

      <p v-if="uploadError" class="error">{{ uploadError }}</p>

      <div class="step-actions">
        <button
          class="btn primary"
          :disabled="!dxfFile"
          @click="currentStep = 2"
        >
          Next: Configure
        </button>
      </div>
    </div>

    <!-- Step 2: Configure Machine & Parameters -->
    <div v-if="currentStep === 2" class="step-content">
      <div class="config-grid">
        <div class="config-section">
          <h3>Machine</h3>
          <select v-model="selectedMachine" class="select-input">
            <option v-for="m in machines" :key="m.id" :value="m.id">
              {{ m.name }}
            </option>
          </select>
          <p class="hint">{{ machines.find(m => m.id === selectedMachine)?.desc }}</p>
        </div>

        <div class="config-section">
          <h3>Material</h3>
          <select v-model="selectedMaterial" class="select-input">
            <option v-for="m in materials" :key="m.id" :value="m.id">
              {{ m.name }}
            </option>
          </select>
          <p class="hint">Feed: {{ selectedMaterialData?.feed }} mm/min</p>
        </div>

        <div class="config-section">
          <h3>Tool Diameter (mm)</h3>
          <input
            type="number"
            v-model.number="toolDiameter"
            min="0.5"
            max="25"
            step="0.5"
            class="number-input"
          />
        </div>

        <div class="config-section">
          <h3>Stepdown (mm)</h3>
          <input
            type="number"
            v-model.number="stepdown"
            min="0.5"
            max="10"
            step="0.5"
            class="number-input"
          />
        </div>

        <div class="config-section full-width">
          <h3>Target Depth (mm)</h3>
          <input
            type="number"
            v-model.number="targetDepth"
            max="0"
            step="0.5"
            class="number-input"
          />
          <p class="hint">Negative value (e.g., -6 for 6mm deep pocket)</p>
        </div>
      </div>

      <p v-if="generateError" class="error">{{ generateError }}</p>

      <div class="step-actions">
        <button class="btn secondary" @click="currentStep = 1">Back</button>
        <button
          class="btn primary"
          :disabled="isGenerating"
          @click="generateGcode"
        >
          {{ isGenerating ? 'Generating...' : 'Generate G-code' }}
        </button>
      </div>
    </div>

    <!-- Step 3: Review & Export -->
    <div v-if="currentStep === 3" class="step-content">
      <!-- Safety Summary -->
      <div class="safety-summary" :class="riskClass">
        <div class="safety-header">
          <span class="safety-icon">{{ riskIcon }}</span>
          <span class="safety-level">{{ riskLevel || 'UNKNOWN' }}</span>
          <span class="safety-label">Safety Check</span>
        </div>

        <div v-if="riskLevel === 'GREEN'" class="safety-message">
          All checks passed. Safe to run on machine.
        </div>
        <div v-else-if="riskLevel === 'YELLOW'" class="safety-message">
          Review warnings before proceeding. Download available.
        </div>
        <div v-else-if="riskLevel === 'RED'" class="safety-message">
          Blocked for safety. Review parameters and try again.
        </div>

        <ul v-if="warnings.length > 0" class="warnings-list">
          <li v-for="(w, i) in warnings" :key="i">{{ w }}</li>
        </ul>
      </div>

      <!-- G-code Preview -->
      <div class="gcode-preview">
        <h3>G-code Preview</h3>
        <pre class="gcode-block">{{ gcodePreview }}</pre>
      </div>

      <!-- Export Info -->
      <div class="export-info">
        <p><strong>File:</strong> {{ dxfFile?.name }}</p>
        <p><strong>Machine:</strong> {{ machines.find(m => m.id === selectedMachine)?.name }}</p>
        <p><strong>Material:</strong> {{ materials.find(m => m.id === selectedMaterial)?.name }}</p>
        <p><strong>Tool:</strong> {{ toolDiameter }}mm, {{ stepdown }}mm stepdown</p>
        <p v-if="result?.run_id" class="run-id"><strong>Run ID:</strong> {{ result.run_id }}</p>
      </div>

      <div class="step-actions">
        <button class="btn secondary" @click="currentStep = 2">Back</button>
        <button
          class="btn primary"
          :disabled="!canDownload"
          @click="downloadGcode"
        >
          {{ riskLevel === 'RED' ? 'Blocked' : 'Download G-code' }}
        </button>
        <button class="btn secondary" @click="reset">Start Over</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.quick-cut-view {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
}

.qc-header {
  text-align: center;
  margin-bottom: 2rem;
}

.qc-header h1 {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #666;
}

/* Step Indicator */
.steps-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 2rem;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  opacity: 0.5;
}

.step.active,
.step.done {
  opacity: 1;
}

.step-num {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
}

.step.active .step-num {
  background: #2196f3;
  color: white;
}

.step.done .step-num {
  background: #4caf50;
  color: white;
}

.step-label {
  margin-top: 0.5rem;
  font-size: 0.875rem;
}

.step-line {
  width: 60px;
  height: 2px;
  background: #e0e0e0;
  margin: 0 1rem;
}

.step-line.done {
  background: #4caf50;
}

/* Step Content */
.step-content {
  background: #f9f9f9;
  border-radius: 8px;
  padding: 2rem;
}

/* Upload Zone */
.upload-zone {
  border: 2px dashed #ccc;
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  transition: border-color 0.2s;
}

.upload-zone:hover {
  border-color: #2196f3;
}

.upload-zone.has-file {
  border-style: solid;
  border-color: #4caf50;
  background: #f0fff0;
}

.upload-prompt {
  color: #666;
}

.upload-icon {
  font-size: 3rem;
  margin-bottom: 0.5rem;
}

.file-selected {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.filename {
  font-weight: bold;
  color: #4caf50;
}

.filesize {
  color: #666;
}

.clear-btn {
  background: #ff5252;
  color: white;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  cursor: pointer;
  font-size: 1rem;
}

/* Config Grid */
.config-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.config-section h3 {
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
  color: #666;
}

.config-section.full-width {
  grid-column: 1 / -1;
}

.select-input,
.number-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.hint {
  font-size: 0.75rem;
  color: #888;
  margin-top: 0.25rem;
}

/* Safety Summary */
.safety-summary {
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.safety-summary.risk-green {
  background: #e8f5e9;
  border: 2px solid #4caf50;
}

.safety-summary.risk-yellow {
  background: #fff8e1;
  border: 2px solid #ffc107;
}

.safety-summary.risk-red {
  background: #ffebee;
  border: 2px solid #f44336;
}

.safety-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.safety-icon {
  font-size: 1.5rem;
}

.safety-level {
  font-weight: bold;
  font-size: 1.25rem;
}

.safety-label {
  color: #666;
  margin-left: auto;
}

.safety-message {
  font-size: 0.875rem;
}

.warnings-list {
  margin-top: 0.75rem;
  padding-left: 1.25rem;
  font-size: 0.875rem;
}

.warnings-list li {
  margin: 0.25rem 0;
}

/* G-code Preview */
.gcode-preview {
  margin-bottom: 1.5rem;
}

.gcode-preview h3 {
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
  color: #666;
}

.gcode-block {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 1rem;
  border-radius: 4px;
  overflow-x: auto;
  max-height: 250px;
  font-family: monospace;
  font-size: 0.8rem;
}

/* Export Info */
.export-info {
  background: white;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1.5rem;
}

.export-info p {
  margin: 0.25rem 0;
  font-size: 0.875rem;
}

.run-id {
  font-family: monospace;
  font-size: 0.75rem;
  color: #666;
}

/* Actions */
.step-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 2rem;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  font-size: 1rem;
}

.btn.primary {
  background: #2196f3;
  color: white;
}

.btn.primary:hover:not(:disabled) {
  background: #1976d2;
}

.btn.primary:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.btn.secondary {
  background: #e0e0e0;
}

.btn.secondary:hover {
  background: #d0d0d0;
}

.error {
  color: #f44336;
  font-size: 0.875rem;
  margin-top: 0.5rem;
}
</style>
