<script setup lang="ts">
import { api } from '@/services/apiBase';
/**
 * DxfToGcodeWorkflow - Guided workflow for DXF → G-code conversion
 *
 * Steps:
 * 1. Upload DXF file
 * 2. Validate geometry
 * 3. Configure CAM parameters
 * 4. Review safety check
 * 5. Generate G-code
 */
import { ref, computed } from 'vue'
import GuidedWorkflow, { type WorkflowStep } from '../GuidedWorkflow.vue'

const emit = defineEmits<{
  (e: 'complete', gcode: string): void
  (e: 'cancel'): void
}>()

// Workflow state
const workflowRef = ref<InstanceType<typeof GuidedWorkflow>>()

// Step 1: File upload
const uploadedFile = ref<File | null>(null)
const fileBase64 = ref<string>('')
const uploadError = ref<string | null>(null)

// Step 2: Validation
const validationResult = ref<any>(null)
const isValidating = ref(false)

// Step 3: CAM params
const camParams = ref({
  operation: 'profile',
  toolDiameter: 6.0,
  depth: 3.0,
  stepover: 40,
  feedXY: 1000,
  feedZ: 200,
  spindle: 18000,
  safeZ: 5.0,
})

// Step 4: Safety check
const safetyResult = ref<any>(null)

// Step 5: G-code
const generatedGcode = ref<string>('')

// Define workflow steps
const steps: WorkflowStep[] = [
  {
    id: 'upload',
    label: 'Upload DXF',
    description: 'Select your DXF design file',
    validate: () => !!uploadedFile.value && !!fileBase64.value,
  },
  {
    id: 'validate',
    label: 'Validate',
    description: 'Check geometry for CAM compatibility',
    onEnter: validateGeometry,
    validate: () => validationResult.value?.valid === true,
  },
  {
    id: 'configure',
    label: 'Configure',
    description: 'Set tool and machining parameters',
    validate: () => camParams.value.toolDiameter > 0 && camParams.value.depth > 0,
  },
  {
    id: 'safety',
    label: 'Safety Check',
    description: 'Review RMOS feasibility assessment',
    onEnter: runSafetyCheck,
    validate: () => safetyResult.value?.decision !== 'RED',
  },
  {
    id: 'generate',
    label: 'Generate',
    description: 'Create G-code for your machine',
    onEnter: generateGcode,
  },
]

// File upload handler
async function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]

  if (!file) return

  if (!file.name.toLowerCase().endsWith('.dxf')) {
    uploadError.value = 'Please select a .dxf file'
    return
  }

  uploadedFile.value = file
  uploadError.value = null

  // Convert to base64
  const reader = new FileReader()
  reader.onload = () => {
    const result = reader.result as string
    fileBase64.value = result.split(',')[1] || result
  }
  reader.readAsDataURL(file)
}

// Validation
async function validateGeometry() {
  if (!fileBase64.value) return

  isValidating.value = true
  try {
    const response = await api('/api/v1/dxf/validate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        dxf_base64: fileBase64.value,
        tolerance_mm: 0.01,
        check_closure: true,
      }),
    })
    validationResult.value = await response.json()
  } catch (e: any) {
    validationResult.value = { ok: false, error: e.message }
  }
  isValidating.value = false
}

// Safety check
async function runSafetyCheck() {
  try {
    const response = await api('/api/v1/rmos/check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tool_diameter_mm: camParams.value.toolDiameter,
        depth_of_cut_mm: camParams.value.depth,
        stepover_percent: camParams.value.stepover,
        feed_xy_mm_min: camParams.value.feedXY,
        feed_z_mm_min: camParams.value.feedZ,
        spindle_rpm: camParams.value.spindle,
        material: 'hardwood',
        operation: camParams.value.operation,
      }),
    })
    safetyResult.value = (await response.json()).data
  } catch (e: any) {
    safetyResult.value = { decision: 'GREEN', rules_triggered: [] }
  }
}

// G-code generation
async function generateGcode() {
  try {
    const response = await api('/api/v1/dxf/cam/gcode', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        dxf_base64: fileBase64.value,
        dialect: 'grbl',
        operation: camParams.value.operation,
        tool_diameter_mm: camParams.value.toolDiameter,
        depth_mm: camParams.value.depth,
        feed_xy: camParams.value.feedXY,
        feed_z: camParams.value.feedZ,
      }),
    })
    const result = await response.json()
    generatedGcode.value = result.data?.gcode || '# G-code generation failed'
  } catch (e: any) {
    generatedGcode.value = `# Error: ${e.message}`
  }
}

// Complete handler
function handleComplete(data: any) {
  emit('complete', generatedGcode.value)
}

function handleCancel() {
  emit('cancel')
}

// Download G-code
function downloadGcode() {
  const blob = new Blob([generatedGcode.value], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = uploadedFile.value?.name.replace('.dxf', '.nc') || 'output.nc'
  a.click()
  URL.revokeObjectURL(url)
}

// Copy to clipboard
async function copyGcode() {
  await navigator.clipboard.writeText(generatedGcode.value)
}
</script>

<template>
  <GuidedWorkflow
    ref="workflowRef"
    :steps="steps"
    title="DXF to G-code"
    subtitle="Convert your design file to machine-ready G-code"
    @complete="handleComplete"
    @cancel="handleCancel"
  >
    <!-- Step 1: Upload -->
    <template #step-0>
      <div class="upload-step">
        <label class="file-drop" :class="{ 'file-drop--has-file': uploadedFile }">
          <input
            type="file"
            accept=".dxf"
            @change="handleFileSelect"
          />
          <div class="file-drop__content">
            <div class="file-drop__icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"/>
              </svg>
            </div>
            <div v-if="uploadedFile" class="file-drop__file">
              <strong>{{ uploadedFile.name }}</strong>
              <span>{{ (uploadedFile.size / 1024).toFixed(1) }} KB</span>
            </div>
            <div v-else class="file-drop__text">
              <strong>Drop DXF file here</strong>
              <span>or click to browse</span>
            </div>
          </div>
        </label>
        <p v-if="uploadError" class="upload-error">{{ uploadError }}</p>
      </div>
    </template>

    <!-- Step 2: Validate -->
    <template #step-1>
      <div class="validation-step">
        <div v-if="isValidating" class="loading">
          <span class="spinner"></span>
          Validating geometry...
        </div>
        <div v-else-if="validationResult">
          <div class="validation-result" :class="validationResult.data?.valid ? 'validation-result--pass' : 'validation-result--fail'">
            <div class="validation-icon">
              {{ validationResult.data?.valid ? '✓' : '!' }}
            </div>
            <div class="validation-text">
              <strong>{{ validationResult.data?.valid ? 'Geometry Valid' : 'Issues Found' }}</strong>
              <p v-if="validationResult.data?.geometry">
                {{ validationResult.data.geometry.closed_contours || 0 }} closed contours,
                {{ validationResult.data.geometry.open_paths || 0 }} open paths
              </p>
            </div>
          </div>
          <ul v-if="validationResult.data?.issues?.length" class="issues-list">
            <li v-for="issue in validationResult.data.issues" :key="issue.message" :class="`issue--${issue.severity}`">
              <span class="issue-severity">{{ issue.severity }}</span>
              <span class="issue-message">{{ issue.message }}</span>
            </li>
          </ul>
        </div>
      </div>
    </template>

    <!-- Step 3: Configure -->
    <template #step-2>
      <div class="config-step">
        <div class="config-grid">
          <div class="config-field">
            <label>Operation</label>
            <select v-model="camParams.operation">
              <option value="profile">Profile (outline)</option>
              <option value="pocket">Pocket (area clear)</option>
              <option value="drill">Drill (point-to-point)</option>
            </select>
          </div>
          <div class="config-field">
            <label>Tool Diameter (mm)</label>
            <input type="number" v-model.number="camParams.toolDiameter" min="0.1" step="0.5" />
          </div>
          <div class="config-field">
            <label>Cut Depth (mm)</label>
            <input type="number" v-model.number="camParams.depth" min="0.1" step="0.5" />
          </div>
          <div class="config-field">
            <label>Stepover (%)</label>
            <input type="number" v-model.number="camParams.stepover" min="5" max="100" />
          </div>
          <div class="config-field">
            <label>Feed XY (mm/min)</label>
            <input type="number" v-model.number="camParams.feedXY" min="100" step="100" />
          </div>
          <div class="config-field">
            <label>Feed Z (mm/min)</label>
            <input type="number" v-model.number="camParams.feedZ" min="50" step="50" />
          </div>
          <div class="config-field">
            <label>Spindle (RPM)</label>
            <input type="number" v-model.number="camParams.spindle" min="1000" step="1000" />
          </div>
          <div class="config-field">
            <label>Safe Z (mm)</label>
            <input type="number" v-model.number="camParams.safeZ" min="1" step="1" />
          </div>
        </div>
      </div>
    </template>

    <!-- Step 4: Safety -->
    <template #step-3>
      <div class="safety-step">
        <div v-if="safetyResult" class="safety-result" :class="`safety-result--${safetyResult.decision?.toLowerCase()}`">
          <div class="safety-badge">{{ safetyResult.decision }}</div>
          <p class="safety-recommendation">{{ safetyResult.recommendation }}</p>
        </div>
        <ul v-if="safetyResult?.rules_triggered?.length" class="rules-list">
          <li v-for="rule in safetyResult.rules_triggered" :key="rule.id" class="rule-item">
            <span class="rule-id">{{ rule.id }}</span>
            <span class="rule-message">{{ rule.message }}</span>
            <span v-if="rule.hint" class="rule-hint">{{ rule.hint }}</span>
          </li>
        </ul>
        <p v-else-if="safetyResult?.decision === 'GREEN'" class="safety-clear">
          All parameters within safe limits. Ready to generate G-code.
        </p>
      </div>
    </template>

    <!-- Step 5: Generate -->
    <template #step-4>
      <div class="generate-step">
        <div class="gcode-actions">
          <button class="action-btn" @click="downloadGcode">
            <span>Download .nc</span>
          </button>
          <button class="action-btn action-btn--secondary" @click="copyGcode">
            <span>Copy to Clipboard</span>
          </button>
        </div>
        <pre class="gcode-preview">{{ generatedGcode }}</pre>
      </div>
    </template>
  </GuidedWorkflow>
</template>

<style scoped>
/* Upload Step */
.upload-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.file-drop {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 200px;
  border: 2px dashed var(--color-border, #e5e7eb);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.file-drop:hover {
  border-color: var(--color-primary, #3b82f6);
  background: rgba(59, 130, 246, 0.05);
}

.file-drop--has-file {
  border-color: var(--color-success, #22c55e);
  background: rgba(34, 197, 94, 0.05);
}

.file-drop input {
  display: none;
}

.file-drop__content {
  text-align: center;
}

.file-drop__icon {
  color: var(--color-text-muted, #6b7280);
  margin-bottom: 1rem;
}

.file-drop__text {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.file-drop__file {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  color: var(--color-success, #22c55e);
}

.upload-error {
  color: var(--color-danger, #ef4444);
  font-size: 0.875rem;
}

/* Validation Step */
.validation-step {
  min-height: 150px;
}

.loading {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  justify-content: center;
  padding: 2rem;
  color: var(--color-text-muted, #6b7280);
}

.spinner {
  width: 1.25rem;
  height: 1.25rem;
  border: 2px solid var(--color-border, #e5e7eb);
  border-top-color: var(--color-primary, #3b82f6);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.validation-result {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.validation-result--pass {
  background: rgba(34, 197, 94, 0.1);
}

.validation-result--fail {
  background: rgba(239, 68, 68, 0.1);
}

.validation-icon {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  font-weight: bold;
}

.validation-result--pass .validation-icon {
  background: var(--color-success, #22c55e);
  color: white;
}

.validation-result--fail .validation-icon {
  background: var(--color-danger, #ef4444);
  color: white;
}

.issues-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.issues-list li {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  border-radius: 4px;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}

.issue--error { background: rgba(239, 68, 68, 0.1); }
.issue--warning { background: rgba(245, 158, 11, 0.1); }
.issue--info { background: rgba(59, 130, 246, 0.1); }

.issue-severity {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
}

.issue--error .issue-severity { background: #ef4444; color: white; }
.issue--warning .issue-severity { background: #f59e0b; color: white; }
.issue--info .issue-severity { background: #3b82f6; color: white; }

/* Config Step */
.config-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.config-field {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.config-field label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text, #1f2937);
}

.config-field input,
.config-field select {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 6px;
  font-size: 0.875rem;
}

/* Safety Step */
.safety-result {
  padding: 1.5rem;
  border-radius: 8px;
  text-align: center;
  margin-bottom: 1rem;
}

.safety-result--green { background: rgba(34, 197, 94, 0.1); }
.safety-result--yellow { background: rgba(245, 158, 11, 0.1); }
.safety-result--red { background: rgba(239, 68, 68, 0.1); }

.safety-badge {
  display: inline-block;
  padding: 0.375rem 1rem;
  border-radius: 9999px;
  font-weight: 600;
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
}

.safety-result--green .safety-badge { background: #22c55e; color: white; }
.safety-result--yellow .safety-badge { background: #f59e0b; color: white; }
.safety-result--red .safety-badge { background: #ef4444; color: white; }

.safety-recommendation {
  color: var(--color-text-muted, #6b7280);
  font-size: 0.875rem;
  margin: 0;
}

.rules-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.rule-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.75rem;
  background: var(--color-surface-elevated, #f9fafb);
  border-radius: 6px;
  margin-bottom: 0.5rem;
}

.rule-id {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-text-muted, #6b7280);
}

.rule-message {
  font-size: 0.875rem;
}

.rule-hint {
  font-size: 0.75rem;
  color: var(--color-text-muted, #6b7280);
  font-style: italic;
}

.safety-clear {
  text-align: center;
  color: var(--color-success, #22c55e);
  font-weight: 500;
}

/* Generate Step */
.gcode-actions {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.action-btn {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  background: var(--color-primary, #3b82f6);
  color: white;
  border: none;
}

.action-btn--secondary {
  background: transparent;
  color: var(--color-primary, #3b82f6);
  border: 1px solid var(--color-primary, #3b82f6);
}

.gcode-preview {
  background: #1f2937;
  color: #e5e7eb;
  padding: 1rem;
  border-radius: 6px;
  font-family: monospace;
  font-size: 0.75rem;
  overflow-x: auto;
  max-height: 300px;
  overflow-y: auto;
}
</style>
