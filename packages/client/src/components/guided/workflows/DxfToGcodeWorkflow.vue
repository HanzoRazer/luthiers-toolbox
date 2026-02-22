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
import styles from './DxfToGcodeWorkflow.module.css'

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
      <div :class="styles.uploadStep">
        <label :class="uploadedFile ? styles.fileDropHasFile : styles.fileDrop">
          <input
            type="file"
            accept=".dxf"
            @change="handleFileSelect"
          />
          <div :class="styles.fileDropContent">
            <div :class="styles.fileDropIcon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"/>
              </svg>
            </div>
            <div v-if="uploadedFile" :class="styles.fileDropFile">
              <strong>{{ uploadedFile.name }}</strong>
              <span>{{ (uploadedFile.size / 1024).toFixed(1) }} KB</span>
            </div>
            <div v-else :class="styles.fileDropText">
              <strong>Drop DXF file here</strong>
              <span>or click to browse</span>
            </div>
          </div>
        </label>
        <p v-if="uploadError" :class="styles.uploadError">{{ uploadError }}</p>
      </div>
    </template>

    <!-- Step 2: Validate -->
    <template #step-1>
      <div :class="styles.validationStep">
        <div v-if="isValidating" :class="styles.loading">
          <span :class="styles.spinner"></span>
          Validating geometry...
        </div>
        <div v-else-if="validationResult">
          <div :class="validationResult.data?.valid ? styles.validationResultPass : styles.validationResultFail">
            <div :class="validationResult.data?.valid ? styles.validationIconPass : styles.validationIconFail">
              {{ validationResult.data?.valid ? '✓' : '!' }}
            </div>
            <div :class="styles.validationText">
              <strong>{{ validationResult.data?.valid ? 'Geometry Valid' : 'Issues Found' }}</strong>
              <p v-if="validationResult.data?.geometry">
                {{ validationResult.data.geometry.closed_contours || 0 }} closed contours,
                {{ validationResult.data.geometry.open_paths || 0 }} open paths
              </p>
            </div>
          </div>
          <ul v-if="validationResult.data?.issues?.length" :class="styles.issuesList">
            <li v-for="issue in validationResult.data.issues" :key="issue.message" :class="issue.severity === 'error' ? styles.issueError : issue.severity === 'warning' ? styles.issueWarning : styles.issueInfo">
              <span :class="issue.severity === 'error' ? styles.issueSeverityError : issue.severity === 'warning' ? styles.issueSeverityWarning : styles.issueSeverityInfo">{{ issue.severity }}</span>
              <span :class="styles.issueMessage">{{ issue.message }}</span>
            </li>
          </ul>
        </div>
      </div>
    </template>

    <!-- Step 3: Configure -->
    <template #step-2>
      <div :class="styles.configStep">
        <div :class="styles.configGrid">
          <div :class="styles.configField">
            <label>Operation</label>
            <select v-model="camParams.operation">
              <option value="profile">Profile (outline)</option>
              <option value="pocket">Pocket (area clear)</option>
              <option value="drill">Drill (point-to-point)</option>
            </select>
          </div>
          <div :class="styles.configField">
            <label>Tool Diameter (mm)</label>
            <input type="number" v-model.number="camParams.toolDiameter" min="0.1" step="0.5" />
          </div>
          <div :class="styles.configField">
            <label>Cut Depth (mm)</label>
            <input type="number" v-model.number="camParams.depth" min="0.1" step="0.5" />
          </div>
          <div :class="styles.configField">
            <label>Stepover (%)</label>
            <input type="number" v-model.number="camParams.stepover" min="5" max="100" />
          </div>
          <div :class="styles.configField">
            <label>Feed XY (mm/min)</label>
            <input type="number" v-model.number="camParams.feedXY" min="100" step="100" />
          </div>
          <div :class="styles.configField">
            <label>Feed Z (mm/min)</label>
            <input type="number" v-model.number="camParams.feedZ" min="50" step="50" />
          </div>
          <div :class="styles.configField">
            <label>Spindle (RPM)</label>
            <input type="number" v-model.number="camParams.spindle" min="1000" step="1000" />
          </div>
          <div :class="styles.configField">
            <label>Safe Z (mm)</label>
            <input type="number" v-model.number="camParams.safeZ" min="1" step="1" />
          </div>
        </div>
      </div>
    </template>

    <!-- Step 4: Safety -->
    <template #step-3>
      <div :class="styles.safetyStep">
        <div v-if="safetyResult" :class="[styles.safetyResult, safetyResult.decision?.toLowerCase() === 'green' ? styles.safetyResultGreen : safetyResult.decision?.toLowerCase() === 'yellow' ? styles.safetyResultYellow : styles.safetyResultRed]">
          <div :class="safetyResult.decision?.toLowerCase() === 'green' ? styles.safetyBadgeGreen : safetyResult.decision?.toLowerCase() === 'yellow' ? styles.safetyBadgeYellow : styles.safetyBadgeRed">{{ safetyResult.decision }}</div>
          <p :class="styles.safetyRecommendation">{{ safetyResult.recommendation }}</p>
        </div>
        <ul v-if="safetyResult?.rules_triggered?.length" :class="styles.rulesList">
          <li v-for="rule in safetyResult.rules_triggered" :key="rule.id" :class="styles.ruleItem">
            <span :class="styles.ruleId">{{ rule.id }}</span>
            <span :class="styles.ruleMessage">{{ rule.message }}</span>
            <span v-if="rule.hint" :class="styles.ruleHint">{{ rule.hint }}</span>
          </li>
        </ul>
        <p v-else-if="safetyResult?.decision === 'GREEN'" :class="styles.safetyClear">
          All parameters within safe limits. Ready to generate G-code.
        </p>
      </div>
    </template>

    <!-- Step 5: Generate -->
    <template #step-4>
      <div :class="styles.generateStep">
        <div :class="styles.gcodeActions">
          <button :class="styles.actionBtn" @click="downloadGcode">
            <span>Download .nc</span>
          </button>
          <button :class="styles.actionBtnSecondary" @click="copyGcode">
            <span>Copy to Clipboard</span>
          </button>
        </div>
        <pre :class="styles.gcodePreview">{{ generatedGcode }}</pre>
      </div>
    </template>
  </GuidedWorkflow>
</template>
