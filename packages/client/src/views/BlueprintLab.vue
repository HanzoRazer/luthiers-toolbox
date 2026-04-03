<template>
  <div class="blueprint-lab">
    <!-- Header -->
    <div class="header">
      <h1>Blueprint Lab</h1>
      <div class="phase-badges">
        <span class="phase-badge phase-1">Phase 1: AI Analysis</span>
        <span class="phase-badge phase-cal">Calibration</span>
        <span class="phase-badge phase-2">Phase 2: OpenCV Vectorization</span>
      </div>
    </div>

    <!-- Tab Bar -->
    <div class="tab-bar">
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'blueprint' }"
        @click="activeTab = 'blueprint'"
      >
        Blueprint Reader (Legacy)
      </button>
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'vectorizer' }"
        @click="activeTab = 'vectorizer'"
      >
        Photo Vectorizer V2
      </button>
    </div>

    <!-- TAB 1: Blueprint Reader (Legacy) -->
    <div v-if="activeTab === 'blueprint'">
      <!-- Upload Zone -->
      <BlueprintUploadZone
      v-if="!uploadedFile"
      @file-selected="onFileSelected"
      @error="setError"
    />

    <!-- Main Workflow (After Upload) -->
    <div
      v-if="uploadedFile"
      class="workflow"
    >
      <!-- Phase 1: AI Analysis -->
      <Phase1AnalysisPanel
        :analysis="analysis"
        :is-analyzing="isAnalyzing"
        :is-exporting="isExporting"
        :analysis-progress="analysisProgress"
        @analyze="analyzeBlueprint"
        @reset="resetWorkflow"
        @export-svg="handleExportSVG"
        @edit-dimensions="editDimensions"
      />

      <!-- Calibration Panel (after analysis, before vectorization) -->
      <CalibrationPanel
        v-if="analysis"
        :calibration="calibration"
        :is-calibrating="isCalibrating"
        :accepted="calibrationAccepted"
        @calibrate="handleCalibrate"
        @manual-calibrate="handleManualCalibrate"
        @accept="acceptCalibration"
        @recalibrate="resetCalibration"
      />

      <!-- Phase 2 / Phase 3: Geometry Vectorization -->
      <Phase2VectorizationPanel
        v-if="analysis && calibrationAccepted"
        :vectorized-geometry="vectorizedGeometry"
        :vector-params="vectorParams"
        :is-vectorizing="isVectorizing"
        :use-phase3="usePhase3Vectorization"
        :phase3-available="phase3Available"
        @vectorize="vectorizeGeometry"
        @download-svg="handleDownloadVectorizedSVG"
        @download-dxf="handleDownloadVectorizedDXF"
        @re-vectorize="resetVectorization"
        @update:vector-params="vectorParams = $event"
        @update:use-phase3="usePhase3Vectorization = $event"
        @check-phase3="checkPhase3Availability"
      />

      <!-- Phase 3: CAM Integration -->
      <Phase3CamPanel
        v-if="vectorizedGeometry"
        :cam-params="camParams"
        :rmos-result="rmosResult"
        :is-sending-to-c-a-m="isSendingToCAM"
        :gcode-ready="gcodeReady"
        @send-to-cam="sendToCAM"
        @download-gcode="downloadGcode"
        @update:cam-params="camParams = $event"
      />
    </div>
    </div>

    <!-- TAB 2: Photo Vectorizer V2 -->
    <div v-if="activeTab === 'vectorizer'" class="v2-panel">
      <div class="v2-upload-zone"
        :class="{ dragover: v2DragOver }"
        @dragover.prevent="v2DragOver = true"
        @dragleave="v2DragOver = false"
        @drop.prevent="onV2Drop"
        @click="v2FileInput?.click()"
      >
        <input
          ref="v2FileInput"
          type="file"
          accept="image/*"
          style="display: none"
          @change="onV2FileChange"
        />
        <div v-if="!v2PreviewUrl" class="v2-placeholder">
          <p>Drop a guitar photo here or click to browse</p>
          <p class="hint">PNG, JPG - direct silhouette extraction</p>
        </div>
        <img v-else :src="v2PreviewUrl" class="v2-preview" />
      </div>

      <div class="v2-options">
        <label>
          <span>Known Width (mm):</span>
          <input v-model.number="v2KnownWidth" type="number" placeholder="Optional" />
        </label>
        <label class="checkbox-label">
          <input v-model="v2CorrectPerspective" type="checkbox" />
          <span>Correct perspective</span>
        </label>
        <label class="checkbox-label">
          <input v-model="v2ExportDxf" type="checkbox" />
          <span>Export DXF</span>
        </label>
      </div>

      <button
        class="btn-extract"
        :disabled="!v2File || v2Extracting"
        @click="extractV2"
      >
        {{ v2Extracting ? 'Extracting...' : 'Extract Silhouette' }}
      </button>

      <div v-if="v2Result" class="v2-result">
        <h3>Extraction Result</h3>
        <p v-if="v2Result.body_width_mm">Width: {{ v2Result.body_width_mm.toFixed(1) }} mm</p>
        <p v-if="v2Result.body_height_mm">Height: {{ v2Result.body_height_mm.toFixed(1) }} mm</p>
        <p>Processing: {{ v2Result.processing_ms }} ms</p>
        <div class="v2-downloads">
          <button v-if="v2Result.svg_path" @click="downloadV2Svg">Download SVG</button>
          <button v-if="v2Result.dxf_path" @click="downloadV2Dxf">Download DXF</button>
        </div>
        <div v-if="v2Result.warnings?.length" class="v2-warnings">
          <p v-for="w in v2Result.warnings" :key="w">{{ w }}</p>
        </div>
      </div>
    </div>

    <!-- Error Display -->
    <div
      v-if="error"
      class="error-message"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <div>
        <strong>Error:</strong> {{ error }}
      </div>
      <button
        class="btn-close"
        @click="clearError"
      >
        x
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useBlueprintWorkflow } from '@/composables/useBlueprintWorkflow'
import { useAgenticEvents } from '@/composables/useAgenticEvents'
import BlueprintUploadZone from '@/components/blueprint/BlueprintUploadZone.vue'
import Phase1AnalysisPanel from '@/components/blueprint/Phase1AnalysisPanel.vue'
import CalibrationPanel from '@/components/blueprint/CalibrationPanel.vue'
import Phase2VectorizationPanel from '@/components/blueprint/Phase2VectorizationPanel.vue'
import Phase3CamPanel from '@/components/blueprint/Phase3CamPanel.vue'

const router = useRouter()
// E-1: Agentic Spine event emission
const { emitViewRendered, emitAnalysisCompleted, emitAnalysisFailed } = useAgenticEvents()

// Tab state
const activeTab = ref<'blueprint' | 'vectorizer'>('blueprint')

// Photo Vectorizer V2 State
const v2FileInput = ref<HTMLInputElement | null>(null)
const v2File = ref<File | null>(null)
const v2PreviewUrl = ref('')
const v2DragOver = ref(false)
const v2Extracting = ref(false)
const v2KnownWidth = ref<number | null>(null)
const v2CorrectPerspective = ref(false)
const v2ExportDxf = ref(true)
const v2Result = ref<{
  ok: boolean
  svg_path?: string
  dxf_path?: string
  body_width_mm?: number
  body_height_mm?: number
  warnings?: string[]
  processing_ms?: number
} | null>(null)

// Use composable for workflow state and actions
const {
  // State
  uploadedFile,
  error,
  // Phase 1
  isAnalyzing,
  analysis,
  analysisProgress,
  // Calibration
  isCalibrating,
  calibration,
  calibrationAccepted,
  // Phase 2 / Phase 3 vectorization
  isVectorizing,
  vectorizedGeometry,
  vectorParams,
  usePhase3Vectorization,
  phase3Available,
  checkPhase3Availability,
  // Phase 3 CAM
  isSendingToCAM,
  rmosResult,
  camParams,
  // Export
  isExporting,
  // Computed
  gcodeReady,
  // Actions
  validateAndSetFile,
  analyzeBlueprint,
  calibrateBlueprint,
  manualCalibrate,
  acceptCalibration,
  resetCalibration,
  vectorizeGeometry,
  sendToCAM,
  exportSVGBasic,
  downloadVectorizedSVG,
  downloadVectorizedDXF,
  getGcodeText,
  resetWorkflow,
  resetVectorization,
  clearError,
} = useBlueprintWorkflow({
  onError: (msg) => console.error('Workflow error:', msg),
})

// Check for pending image from AI Images (sessionStorage handoff)
onMounted(async () => {
  // E-1: Emit view rendered event for agentic spine
  emitViewRendered('blueprint-lab')

  const pendingImageJson = sessionStorage.getItem('blueprintLab.pendingImage')
  if (!pendingImageJson) return

  try {
    const pendingImage = JSON.parse(pendingImageJson)
    sessionStorage.removeItem('blueprintLab.pendingImage') // Clear immediately

    if (!pendingImage.url) {
      console.warn('Pending image has no URL')
      return
    }

    // Fetch the image from the URL
    const response = await fetch(pendingImage.url)
    if (!response.ok) {
      throw new Error(`Failed to fetch image: ${response.status}`)
    }

    const blob = await response.blob()
    const filename = pendingImage.filename || 'ai-generated.png'
    const file = new File([blob], filename, { type: blob.type || 'image/png' })

    // Load into workflow
    validateAndSetFile(file)
    console.log('Loaded pending image from AI Images:', filename)
  } catch (e) {
    console.error('Failed to load pending image:', e)
    sessionStorage.removeItem('blueprintLab.pendingImage')
  }
})

// E-1: Watch for CAM result (Phase 3 completion) to emit analysis_completed
watch(rmosResult, (newResult) => {
  if (newResult && newResult.run_id) {
    emitAnalysisCompleted([
      'blueprint_vectorized',
      'cam_toolpaths_generated',
      newResult.run_id,
    ])
  }
})

// E-1: Watch for analysis errors
watch(error, (newError) => {
  if (newError) {
    emitAnalysisFailed(newError, 'BLUEPRINT_WORKFLOW_ERROR')
  }
})

// File selection handler
function onFileSelected(file: File) {
  validateAndSetFile(file)
}

// Error setter (from child component)
function setError(msg: string) {
  error.value = msg
}

// Calibration handlers
function handleCalibrate(opts: { knownScaleLength: number | null; paperSize: string }) {
  calibrateBlueprint({
    knownScaleLength: opts.knownScaleLength ?? undefined,
    paperSize: opts.paperSize,
  })
}

// Transform CalibrationPanel's emitted format to composable's expected format
interface ManualCalibrationData {
  point1_x: number
  point1_y: number
  point2_x: number
  point2_y: number
  real_dimension: number
  dimension_name: string
}

function handleManualCalibrate(data: ManualCalibrationData) {
  manualCalibrate({
    point1: { x: data.point1_x, y: data.point1_y },
    point2: { x: data.point2_x, y: data.point2_y },
    realDimension: data.real_dimension,
    dimensionName: data.dimension_name,
  })
}

// Export handlers with blob download
async function handleExportSVG() {
  const blob = await exportSVGBasic()
  if (blob) downloadBlob(blob, 'blueprint_dimensions.svg')
}

async function handleDownloadVectorizedSVG() {
  const blob = await downloadVectorizedSVG()
  if (blob) downloadBlob(blob, 'blueprint_vectorized.svg')
}

async function handleDownloadVectorizedDXF() {
  const blob = await downloadVectorizedDXF()
  if (blob) downloadBlob(blob, 'blueprint_vectorized.dxf')
}

// G-code download
function downloadGcode() {
  const text = getGcodeText()
  if (!text) return

  const blob = new Blob([text], { type: 'text/plain' })
  const baseName = (uploadedFile.value?.name || 'blueprint').replace(/\.[^.]+$/, '')
  downloadBlob(blob, `${baseName}_GRBL.nc`)
}

// Navigate to Parametric Designer with extracted dimensions
function editDimensions() {
  if (!analysis.value?.dimensions) return

  const parseDimension = (label: string): number | undefined => {
    const dim = analysis.value?.dimensions?.find((d) =>
      d.label.toLowerCase().includes(label.toLowerCase())
    )
    if (!dim?.value) return undefined

    const match = dim.value.match(/([\d.]+)\s*(mm|inch|in|"|cm)?/i)
    if (!match) return undefined

    let value = parseFloat(match[1])
    const unit = match[2]?.toLowerCase()

    if (unit === 'inch' || unit === 'in' || unit === '"') {
      value = value * 25.4
    } else if (unit === 'cm') {
      value = value * 10
    }

    return value
  }

  const extractedDims: Record<string, string | number> = {
    preset: 'ai-extracted',
  }

  const bodyLength =
    parseDimension('body length') || parseDimension('total length') || parseDimension('length')
  const bodyWidthLower =
    parseDimension('lower bout') || parseDimension('body width') || parseDimension('width')
  const bodyWidthUpper = parseDimension('upper bout')
  const bodyWidthWaist = parseDimension('waist')

  if (bodyLength) extractedDims.bodyLength = bodyLength
  if (bodyWidthLower) extractedDims.bodyWidthLower = bodyWidthLower
  if (bodyWidthUpper) extractedDims.bodyWidthUpper = bodyWidthUpper
  if (bodyWidthWaist) extractedDims.bodyWidthWaist = bodyWidthWaist

  const neckLength = parseDimension('neck length')
  const neckWidth = parseDimension('neck width') || parseDimension('nut width')
  const scaleLength = parseDimension('scale length') || parseDimension('scale')

  if (neckLength) extractedDims.neckLength = neckLength
  if (neckWidth) extractedDims.neckWidth = neckWidth
  if (scaleLength) extractedDims.scaleLength = scaleLength

  router.push({
    path: '/guitar-dimensions',
    query: extractedDims as Record<string, string>,
  })
}

// Utility: download blob
function downloadBlob(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  window.URL.revokeObjectURL(url)
}

// ============================================================================
// Photo Vectorizer V2 Functions
// ============================================================================

function onV2FileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files && input.files[0]) {
    setV2File(input.files[0])
  }
}

function onV2Drop(e: DragEvent) {
  v2DragOver.value = false
  if (e.dataTransfer?.files && e.dataTransfer.files[0]) {
    setV2File(e.dataTransfer.files[0])
  }
}

function setV2File(file: File) {
  v2File.value = file
  v2PreviewUrl.value = URL.createObjectURL(file)
  v2Result.value = null
}

async function extractV2() {
  if (!v2File.value) return
  
  v2Extracting.value = true
  v2Result.value = null
  
  try {
    // Convert file to base64
    const arrayBuffer = await v2File.value.arrayBuffer()
    const base64 = btoa(
      new Uint8Array(arrayBuffer).reduce((data, byte) => data + String.fromCharCode(byte), '')
    )
    
    const payload = {
      image_b64: base64,
      media_type: v2File.value.type || 'image/png',
      known_width_mm: v2KnownWidth.value ?? undefined,
      correct_perspective: v2CorrectPerspective.value,
      export_svg: true,
      export_dxf: v2ExportDxf.value,
      label: v2File.value.name.replace(/\.[^.]+$/, ''),
      source_type: 'photo',
    }
    
    const resp = await fetch('/api/vectorizer/extract', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    
    if (!resp.ok) {
      const errText = await resp.text()
      throw new Error(errText || resp.statusText)
    }
    
    v2Result.value = await resp.json()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e)
    error.value = 'V2 extraction failed: ' + msg
  } finally {
    v2Extracting.value = false
  }
}

function downloadV2Svg() {
  if (v2Result.value?.svg_path) {
    // Extract filename from path (handles both / and \ separators)
    const filename = v2Result.value.svg_path.split(/[/\\]/).pop()
    window.open(`/api/blueprint/static/${filename}?t=${Date.now()}`, '_blank')
  }
}

function downloadV2Dxf() {
  if (v2Result.value?.dxf_path) {
    // Extract filename from path (handles both / and \ separators)
    const filename = v2Result.value.dxf_path.split(/[/\\]/).pop()
    window.open(`/api/blueprint/static/${filename}?t=${Date.now()}`, '_blank')
  }
}
</script>

<style scoped>
.blueprint-lab {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.phase-badges {
  display: flex;
  gap: 0.5rem;
}

.phase-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 600;
}

.phase-1 {
  background: #3b82f6;
  color: white;
}

.phase-cal {
  background: #f59e0b;
  color: white;
}

.phase-2 {
  background: #10b981;
  color: white;
}

/* Workflow Sections */
.workflow {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

/* Error Message */
.error-message {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  margin-top: 1.5rem;
  background: #fee2e2;
  border: 1px solid #fca5a5;
  border-radius: 0.5rem;
  color: #991b1b;
}

.error-message svg {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
}

.error-message div {
  flex: 1;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  color: #991b1b;
  padding: 0.25rem 0.5rem;
}

.btn-close:hover {
  opacity: 0.7;
}

/* Tab Bar */
.tab-bar {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  border-bottom: 2px solid #e5e7eb;
  padding-bottom: 0.5rem;
}

.tab-btn {
  padding: 0.75rem 1.5rem;
  border: none;
  background: transparent;
  font-size: 1rem;
  font-weight: 600;
  color: #6b7280;
  cursor: pointer;
  border-radius: 0.5rem 0.5rem 0 0;
  transition: all 0.2s;
}

.tab-btn:hover {
  background: #f3f4f6;
  color: #374151;
}

.tab-btn.active {
  background: #3b82f6;
  color: white;
}

/* V2 Panel */
.v2-panel {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.v2-upload-zone {
  border: 2px dashed #d1d5db;
  border-radius: 0.75rem;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.v2-upload-zone:hover,
.v2-upload-zone.dragover {
  border-color: #3b82f6;
  background: #eff6ff;
}

.v2-placeholder {
  color: #6b7280;
}

.v2-placeholder .hint {
  font-size: 0.875rem;
  margin-top: 0.5rem;
  color: #9ca3af;
}

.v2-preview {
  max-width: 100%;
  max-height: 300px;
  object-fit: contain;
}

.v2-options {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  align-items: center;
}

.v2-options label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.v2-options input[type="number"] {
  width: 100px;
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
}

.checkbox-label {
  cursor: pointer;
}

.btn-extract {
  padding: 0.75rem 1.5rem;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-extract:hover:not(:disabled) {
  background: #059669;
}

.btn-extract:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.v2-result {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1.5rem;
}

.v2-result h3 {
  margin: 0 0 1rem 0;
  font-size: 1.125rem;
}

.v2-downloads {
  display: flex;
  gap: 0.75rem;
  margin-top: 1rem;
}

.v2-downloads button {
  padding: 0.5rem 1rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
}

.v2-downloads button:hover {
  background: #2563eb;
}

.v2-warnings {
  margin-top: 1rem;
  padding: 0.75rem;
  background: #fef3c7;
  border-radius: 0.375rem;
  color: #92400e;
  font-size: 0.875rem;
}
</style>
