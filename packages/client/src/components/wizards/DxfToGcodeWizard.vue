<template>
  <div class="wizard-container">
    <div class="wizard-header">
      <h2>DXF to G-code Wizard</h2>
      <div class="step-indicator">
        <div
          v-for="(step, idx) in steps"
          :key="idx"
          :class="['step', { active: currentStep === idx, completed: currentStep > idx }]"
        >
          <span class="step-number">{{ idx + 1 }}</span>
          <span class="step-label">{{ step.label }}</span>
        </div>
      </div>
    </div>

    <div class="wizard-content">
      <!-- Step 1: Upload DXF -->
      <div v-if="currentStep === 0" class="step-content">
        <h3>Upload DXF File</h3>
        <p>Select a DXF file containing your design geometry.</p>

        <div
          class="drop-zone"
          :class="{ dragover: isDragging }"
          @dragover.prevent="isDragging = true"
          @dragleave="isDragging = false"
          @drop.prevent="handleDrop"
        >
          <input
            type="file"
            ref="fileInput"
            accept=".dxf"
            @change="handleFileSelect"
            style="display: none"
          />
          <div v-if="!file" class="drop-prompt">
            <span class="icon">📁</span>
            <p>Drag and drop DXF file here</p>
            <button @click="$refs.fileInput.click()" class="btn btn-secondary">
              Or click to browse
            </button>
          </div>
          <div v-else class="file-selected">
            <span class="icon">✓</span>
            <p><strong>{{ file.name }}</strong></p>
            <p class="file-size">{{ formatSize(file.size) }}</p>
          </div>
        </div>
      </div>

      <!-- Step 2: Validate -->
      <div v-if="currentStep === 1" class="step-content">
        <h3>Validate Geometry</h3>
        <p>Checking your DXF file for CAM compatibility...</p>

        <div v-if="validating" class="loading">
          <div class="spinner"></div>
          <p>Validating...</p>
        </div>

        <div v-else-if="validation" class="validation-results">
          <div :class="['status-badge', validation.ok ? 'success' : 'error']">
            {{ validation.ok ? 'Valid' : 'Issues Found' }}
          </div>

          <div class="stats">
            <div class="stat">
              <span class="label">Layers</span>
              <span class="value">{{ validation.data?.layers?.length || 0 }}</span>
            </div>
            <div class="stat">
              <span class="label">Entities</span>
              <span class="value">{{ validation.data?.entity_count || 0 }}</span>
            </div>
          </div>

          <div v-if="validation.data?.issues?.length" class="issues">
            <h4>Issues:</h4>
            <ul>
              <li v-for="(issue, idx) in validation.data.issues" :key="idx">
                {{ issue.message }}
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Step 3: Configure -->
      <div v-if="currentStep === 2" class="step-content">
        <h3>Configure CAM Parameters</h3>

        <div class="form-grid">
          <div class="form-group">
            <label>Operation Type</label>
            <select v-model="params.operation">
              <option value="profile">Profile (Outline)</option>
              <option value="pocket">Pocket (Clear Area)</option>
              <option value="drill">Drilling</option>
            </select>
          </div>

          <div class="form-group">
            <label>Tool Diameter (mm)</label>
            <input type="number" v-model.number="params.toolDiameter" step="0.5" min="0.5" max="25" />
          </div>

          <div class="form-group">
            <label>Depth (mm)</label>
            <input type="number" v-model.number="params.depth" step="0.5" min="0.5" max="50" />
          </div>

          <div class="form-group">
            <label>Feed Rate XY (mm/min)</label>
            <input type="number" v-model.number="params.feedXY" step="100" min="100" max="5000" />
          </div>

          <div class="form-group">
            <label>Feed Rate Z (mm/min)</label>
            <input type="number" v-model.number="params.feedZ" step="50" min="50" max="2000" />
          </div>

          <div class="form-group">
            <label>G-code Dialect</label>
            <select v-model="params.dialect">
              <option value="grbl">GRBL (Arduino/Hobby)</option>
              <option value="linuxcnc">LinuxCNC</option>
              <option value="mach3">Mach3/Mach4</option>
              <option value="haas">Haas</option>
              <option value="fanuc">FANUC</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Step 4: Generate -->
      <div v-if="currentStep === 3" class="step-content">
        <h3>Generate G-code</h3>

        <div v-if="generating" class="loading">
          <div class="spinner"></div>
          <p>Generating toolpath...</p>
        </div>

        <div v-else-if="gcode" class="gcode-result">
          <div class="status-badge success">G-code Ready</div>

          <div class="stats">
            <div class="stat">
              <span class="label">Lines</span>
              <span class="value">{{ gcode.data?.line_count || 0 }}</span>
            </div>
            <div class="stat">
              <span class="label">Est. Time</span>
              <span class="value">{{ gcode.data?.estimated_time_min?.toFixed(1) || 0 }} min</span>
            </div>
          </div>

          <div class="gcode-preview">
            <pre>{{ gcode.data?.gcode?.slice(0, 500) }}...</pre>
          </div>

          <button @click="downloadGcode" class="btn btn-primary">
            Download G-code
          </button>
        </div>
      </div>
    </div>

    <div class="wizard-footer">
      <button
        @click="prevStep"
        :disabled="currentStep === 0"
        class="btn btn-secondary"
      >
        Back
      </button>

      <button
        @click="nextStep"
        :disabled="!canProceed"
        class="btn btn-primary"
      >
        {{ currentStep === steps.length - 1 ? 'Finish' : 'Next' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const steps = [
  { label: 'Upload' },
  { label: 'Validate' },
  { label: 'Configure' },
  { label: 'Generate' },
]

const currentStep = ref(0)
const file = ref<File | null>(null)
const isDragging = ref(false)
const validating = ref(false)
const generating = ref(false)
const validation = ref<any>(null)
const gcode = ref<any>(null)

const params = ref({
  operation: 'profile',
  toolDiameter: 6.0,
  depth: 3.0,
  feedXY: 1200,
  feedZ: 300,
  dialect: 'grbl',
})

const canProceed = computed(() => {
  if (currentStep.value === 0) return !!file.value
  if (currentStep.value === 1) return validation.value?.ok
  if (currentStep.value === 2) return params.value.toolDiameter > 0
  return true
})

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function handleDrop(e: DragEvent) {
  isDragging.value = false
  const files = e.dataTransfer?.files
  if (files?.[0]?.name.endsWith('.dxf')) {
    file.value = files[0]
  }
}

function handleFileSelect(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files?.[0]) {
    file.value = target.files[0]
  }
}

async function validateFile() {
  if (!file.value) return

  validating.value = true
  try {
    const formData = new FormData()
    formData.append('file', file.value)

    const response = await fetch('/api/v1/dxf/upload', {
      method: 'POST',
      body: formData,
    })
    validation.value = await response.json()
  } catch (error) {
    validation.value = { ok: false, error: 'Validation failed' }
  } finally {
    validating.value = false
  }
}

async function generateGcode() {
  generating.value = true
  try {
    const response = await fetch('/api/v1/dxf/cam/gcode', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        dxf_base64: await fileToBase64(file.value!),
        dialect: params.value.dialect,
        operation: params.value.operation,
        tool_diameter_mm: params.value.toolDiameter,
        depth_mm: params.value.depth,
        feed_xy: params.value.feedXY,
        feed_z: params.value.feedZ,
      }),
    })
    gcode.value = await response.json()
  } catch (error) {
    gcode.value = { ok: false, error: 'Generation failed' }
  } finally {
    generating.value = false
  }
}

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const base64 = (reader.result as string).split(',')[1]
      resolve(base64)
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

function downloadGcode() {
  if (!gcode.value?.data?.gcode) return

  const blob = new Blob([gcode.value.data.gcode], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${file.value?.name?.replace('.dxf', '')}_${params.value.dialect}.nc`
  a.click()
  URL.revokeObjectURL(url)
}

async function nextStep() {
  if (currentStep.value === 0 && file.value) {
    currentStep.value++
    await validateFile()
  } else if (currentStep.value === 2) {
    currentStep.value++
    await generateGcode()
  } else if (currentStep.value < steps.length - 1) {
    currentStep.value++
  }
}

function prevStep() {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}
</script>

<style scoped>
.wizard-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
  background: var(--color-bg-secondary, #f5f5f5);
  border-radius: 8px;
}

.wizard-header h2 {
  margin: 0 0 1.5rem;
  text-align: center;
}

.step-indicator {
  display: flex;
  justify-content: space-between;
  margin-bottom: 2rem;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  position: relative;
}

.step::after {
  content: '';
  position: absolute;
  top: 15px;
  left: 50%;
  width: 100%;
  height: 2px;
  background: var(--color-border, #ddd);
}

.step:last-child::after {
  display: none;
}

.step.completed::after {
  background: var(--color-success, #22c55e);
}

.step-number {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--color-border, #ddd);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  z-index: 1;
}

.step.active .step-number {
  background: var(--color-primary, #3b82f6);
  color: white;
}

.step.completed .step-number {
  background: var(--color-success, #22c55e);
  color: white;
}

.step-label {
  margin-top: 0.5rem;
  font-size: 0.875rem;
  color: var(--color-text-secondary, #666);
}

.wizard-content {
  min-height: 300px;
  padding: 1.5rem;
  background: white;
  border-radius: 8px;
  margin-bottom: 1.5rem;
}

.step-content h3 {
  margin: 0 0 0.5rem;
}

.drop-zone {
  border: 2px dashed var(--color-border, #ddd);
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.drop-zone:hover,
.drop-zone.dragover {
  border-color: var(--color-primary, #3b82f6);
  background: var(--color-bg-secondary, #f0f9ff);
}

.drop-prompt .icon,
.file-selected .icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.file-size {
  color: var(--color-text-secondary, #666);
  font-size: 0.875rem;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-border, #ddd);
  border-top-color: var(--color-primary, #3b82f6);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-weight: 600;
  margin-bottom: 1rem;
}

.status-badge.success {
  background: var(--color-success-bg, #dcfce7);
  color: var(--color-success, #22c55e);
}

.status-badge.error {
  background: var(--color-error-bg, #fee2e2);
  color: var(--color-error, #ef4444);
}

.stats {
  display: flex;
  gap: 2rem;
  margin: 1rem 0;
}

.stat {
  display: flex;
  flex-direction: column;
}

.stat .label {
  font-size: 0.875rem;
  color: var(--color-text-secondary, #666);
}

.stat .value {
  font-size: 1.5rem;
  font-weight: bold;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  margin-bottom: 0.25rem;
  font-weight: 500;
}

.form-group input,
.form-group select {
  padding: 0.5rem;
  border: 1px solid var(--color-border, #ddd);
  border-radius: 4px;
}

.gcode-preview {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 1rem;
  border-radius: 4px;
  overflow: auto;
  max-height: 200px;
  margin: 1rem 0;
}

.gcode-preview pre {
  margin: 0;
  font-family: monospace;
  font-size: 0.875rem;
}

.wizard-footer {
  display: flex;
  justify-content: space-between;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--color-primary, #3b82f6);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-primary-dark, #2563eb);
}

.btn-secondary {
  background: var(--color-bg-secondary, #e5e7eb);
  color: var(--color-text, #374151);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--color-bg-tertiary, #d1d5db);
}
</style>
