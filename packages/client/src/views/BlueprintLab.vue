<template>
  <div class="blueprint-lab">
    <!-- Header -->
    <div class="header">
      <h1>Blueprint Lab</h1>
      <div class="phase-badges">
        <span class="phase-badge phase-1">Phase 1: AI Analysis</span>
        <span class="phase-badge phase-2">Phase 2: OpenCV Vectorization</span>
      </div>
    </div>

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

      <!-- Phase 2: Geometry Vectorization -->
      <Phase2VectorizationPanel
        v-if="analysis"
        :vectorized-geometry="vectorizedGeometry"
        :vector-params="vectorParams"
        :is-vectorizing="isVectorizing"
        @vectorize="vectorizeGeometry"
        @download-svg="handleDownloadVectorizedSVG"
        @download-dxf="handleDownloadVectorizedDXF"
        @re-vectorize="resetVectorization"
        @update:vector-params="vectorParams = $event"
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
import { useRouter } from 'vue-router'
import { useBlueprintWorkflow } from '@/composables/useBlueprintWorkflow'
import BlueprintUploadZone from '@/components/blueprint/BlueprintUploadZone.vue'
import Phase1AnalysisPanel from '@/components/blueprint/Phase1AnalysisPanel.vue'
import Phase2VectorizationPanel from '@/components/blueprint/Phase2VectorizationPanel.vue'
import Phase3CamPanel from '@/components/blueprint/Phase3CamPanel.vue'

const router = useRouter()

// Use composable for workflow state and actions
const {
  // State
  uploadedFile,
  error,
  // Phase 1
  isAnalyzing,
  analysis,
  analysisProgress,
  // Phase 2
  isVectorizing,
  vectorizedGeometry,
  vectorParams,
  // Phase 3
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

// File selection handler
function onFileSelected(file: File) {
  validateAndSetFile(file)
}

// Error setter (from child component)
function setError(msg: string) {
  error.value = msg
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
</style>
