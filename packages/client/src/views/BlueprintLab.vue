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
    <div
      v-if="!uploadedFile"
      class="upload-zone"
      :class="{ 'drag-over': isDragOver }"
      @drop.prevent="handleDrop"
      @dragover.prevent="isDragOver = true"
      @dragleave="isDragOver = false"
    >
      <input
        ref="fileInput"
        type="file"
        accept=".pdf,.png,.jpg,.jpeg"
        @change="handleFileSelect"
        style="display: none"
      />
      
      <div class="upload-prompt">
        <svg class="upload-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
        <p class="upload-text">
          <strong>Drop blueprint here</strong> or <button @click="$refs.fileInput.click()" class="browse-btn">browse</button>
        </p>
        <p class="upload-hint">Supports PDF, PNG, JPG (max 20MB)</p>
      </div>
    </div>

    <!-- Main Workflow (After Upload) -->
    <div v-if="uploadedFile" class="workflow">
      <!-- Phase 1: AI Analysis -->
      <section class="workflow-section">
        <div class="section-header">
          <h2>
            <span class="step-number">1</span>
            AI Analysis (Claude Sonnet 4)
          </h2>
          <button v-if="analysis && !isAnalyzing" @click="resetWorkflow" class="btn-secondary">
            Upload New Blueprint
          </button>
        </div>

        <div v-if="!analysis" class="action-card">
          <p class="hint">Analyze blueprint to detect scale, dimensions, and blueprint type</p>
          <button @click="analyzeBlueprint" :disabled="isAnalyzing" class="btn-primary">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            {{ isAnalyzing ? 'Analyzing...' : 'Start Analysis' }}
          </button>
          <div v-if="isAnalyzing" class="progress-timer">{{ analysisProgress }}s elapsed</div>
        </div>

        <div v-if="analysis" class="results-card">
          <!-- Scale Info -->
          <div class="scale-grid">
            <div class="info-card">
              <span class="label">Detected Scale:</span>
              <span class="value">{{ analysis.scale || 'Unknown' }}</span>
              <span :class="['confidence', `confidence-${analysis.scale_confidence}`]">
                {{ analysis.scale_confidence || 'unknown' }}
              </span>
            </div>
            <div v-if="analysis.blueprint_type" class="info-card">
              <span class="label">Type:</span>
              <span class="value">{{ analysis.blueprint_type }}</span>
            </div>
            <div v-if="analysis.detected_model" class="info-card">
              <span class="label">Model:</span>
              <span class="value">{{ analysis.detected_model }}</span>
            </div>
          </div>

          <!-- Dimensions Table (Collapsible) -->
          <details class="dimensions-details" :open="analysis.dimensions?.length <= 10">
            <summary>
              <strong>Detected Dimensions ({{ analysis.dimensions?.length || 0 }})</strong>
            </summary>
            <div class="dimensions-table">
              <div class="table-header">
                <span>Label</span>
                <span>Value</span>
                <span>Type</span>
                <span>Confidence</span>
              </div>
              <div
                v-for="(dim, idx) in analysis.dimensions?.slice(0, 50)"
                :key="idx"
                class="table-row"
                :class="dim.type"
              >
                <span class="dim-label">{{ dim.label }}</span>
                <span class="dim-value">{{ dim.value }}</span>
                <span :class="['dim-type', dim.type]">{{ dim.type }}</span>
                <span :class="['dim-confidence', `confidence-${dim.confidence}`]">
                  {{ dim.confidence }}
                </span>
              </div>
            </div>
          </details>

          <!-- Phase 1 Export -->
          <div class="export-row">
            <button @click="exportSVGBasic" :disabled="isExporting" class="btn-secondary">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Export SVG (Dimensions Only)
            </button>
            <button @click="editDimensions" class="btn-primary" style="margin-left: 12px;">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              📐 Edit Dimensions in Parametric Designer
            </button>
          </div>
        </div>
      </section>

      <!-- Phase 2: Geometry Vectorization -->
      <section v-if="analysis" class="workflow-section phase-2">
        <div class="section-header">
          <h2>
            <span class="step-number">2</span>
            Geometry Vectorization (OpenCV)
          </h2>
        </div>

        <div v-if="!vectorizedGeometry" class="action-card">
          <p class="hint">Detect edges, extract contours, and export CAM-ready DXF with closed polylines</p>
          
          <!-- Vectorization Controls -->
          <div class="controls-grid">
            <div class="control-group">
              <label>Scale Factor:</label>
              <input v-model.number="vectorParams.scaleFactor" type="number" step="0.1" min="0.1" max="10" />
              <span class="control-hint">Adjust if scale detection was incorrect</span>
            </div>
            <div class="control-group">
              <label>Edge Threshold (Low):</label>
              <input v-model.number="vectorParams.lowThreshold" type="number" min="10" max="200" />
              <span class="control-hint">Lower = more edges detected</span>
            </div>
            <div class="control-group">
              <label>Edge Threshold (High):</label>
              <input v-model.number="vectorParams.highThreshold" type="number" min="50" max="300" />
              <span class="control-hint">Higher = stricter edge detection</span>
            </div>
            <div class="control-group">
              <label>Min Contour Area (px²):</label>
              <input v-model.number="vectorParams.minArea" type="number" min="10" max="1000" />
              <span class="control-hint">Filter small noise</span>
            </div>
          </div>

          <button @click="vectorizeGeometry" :disabled="isVectorizing" class="btn-primary">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
            </svg>
            {{ isVectorizing ? 'Vectorizing...' : 'Vectorize Geometry' }}
          </button>
        </div>

        <div v-if="vectorizedGeometry" class="results-card">
          <!-- Vectorization Stats -->
          <div class="stats-grid">
            <div class="stat-card">
              <span class="stat-value">{{ vectorizedGeometry.contours_detected }}</span>
              <span class="stat-label">Contours Detected</span>
            </div>
            <div class="stat-card">
              <span class="stat-value">{{ vectorizedGeometry.lines_detected }}</span>
              <span class="stat-label">Lines Detected</span>
            </div>
            <div class="stat-card">
              <span class="stat-value">{{ vectorizedGeometry.processing_time_ms }}ms</span>
              <span class="stat-label">Processing Time</span>
            </div>
          </div>

          <!-- Preview Canvas -->
          <div class="preview-section">
            <h4>Geometry Preview:</h4>
            <div class="preview-placeholder">
              <p>SVG Preview: <a :href="`/api/blueprint/static/${vectorizedGeometry.svg_path.split('/').pop()}`" target="_blank">View SVG</a></p>
              <p class="hint-small">Detected contours shown in blue, lines in red</p>
            </div>
          </div>

          <!-- Phase 2 Exports -->
          <div class="export-row">
            <button @click="downloadVectorizedSVG" class="btn-primary">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Download SVG (Vectorized)
            </button>
            <button @click="downloadVectorizedDXF" class="btn-primary">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Download DXF R2000 (CAM-Ready)
            </button>
            <button @click="vectorizedGeometry = null" class="btn-secondary">
              Re-vectorize with New Settings
            </button>
          </div>
        </div>
      </section>

      <!-- Phase 3: CAM Integration (MVP Wrapper) -->
      <section v-if="vectorizedGeometry" class="workflow-section phase-3">
        <div class="section-header">
          <h2>
            <span class="step-number">3</span>
            Send to CAM Pipeline (GRBL)
          </h2>
        </div>

        <!-- CAM Parameters -->
        <div class="action-card">
          <p class="hint">Generate G-code from vectorized DXF using adaptive pocketing</p>

          <div class="controls-grid">
            <div class="control-group">
              <label>Tool Diameter (mm):</label>
              <input v-model.number="camParams.tool_d" type="number" step="0.5" min="0.5" max="25" />
            </div>
            <div class="control-group">
              <label>Stepover (0-1):</label>
              <input v-model.number="camParams.stepover" type="number" step="0.05" min="0.1" max="0.9" />
            </div>
            <div class="control-group">
              <label>Stepdown (mm):</label>
              <input v-model.number="camParams.stepdown" type="number" step="0.5" min="0.5" max="10" />
            </div>
            <div class="control-group">
              <label>Target Depth (mm):</label>
              <input v-model.number="camParams.z_rough" type="number" step="0.5" max="0" />
            </div>
            <div class="control-group">
              <label>Feed XY (mm/min):</label>
              <input v-model.number="camParams.feed_xy" type="number" step="100" min="100" max="5000" />
            </div>
            <div class="control-group">
              <label>Feed Z (mm/min):</label>
              <input v-model.number="camParams.feed_z" type="number" step="50" min="50" max="1000" />
            </div>
          </div>

          <button @click="sendToCAM" :disabled="isSendingToCAM" class="btn-primary">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            {{ isSendingToCAM ? 'Generating G-code...' : 'Generate G-code (GRBL)' }}
          </button>
        </div>

        <!-- RMOS Result -->
        <div v-if="rmosResult" class="results-card">
          <div class="stats-grid">
            <div class="stat-card">
              <span class="stat-value">{{ rmosResult.decision?.risk_level || 'N/A' }}</span>
              <span class="stat-label">Risk Level</span>
            </div>
            <div class="stat-card">
              <span class="stat-value" style="font-size: 0.875rem; word-break: break-all;">{{ rmosResult.run_id || 'N/A' }}</span>
              <span class="stat-label">RMOS Run ID</span>
            </div>
            <div class="stat-card">
              <span class="stat-value">{{ rmosResult.rmos_persisted ? '✓' : '✗' }}</span>
              <span class="stat-label">RMOS Persisted</span>
            </div>
          </div>

          <!-- Warnings -->
          <div v-if="rmosResult.decision?.warnings?.length" class="warning-list">
            <strong>Warnings:</strong>
            <ul>
              <li v-for="(w, i) in rmosResult.decision.warnings" :key="i">{{ w }}</li>
            </ul>
          </div>

          <!-- RMOS Error -->
          <div v-if="!rmosResult.rmos_persisted && rmosResult.rmos_error" class="rmos-error">
            <strong>RMOS Error:</strong> {{ rmosResult.rmos_error }}
          </div>

          <!-- Download Button -->
          <div class="export-row">
            <button
              @click="downloadGcode"
              :disabled="!gcodeReady"
              class="btn-primary"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Download G-code (.nc)
            </button>
            <span v-if="rmosResult && !rmosResult.gcode?.inline" class="hint-small">
              G-code too large for inline delivery. Use RMOS attachments.
            </span>
          </div>
        </div>
      </section>
    </div>

    <!-- Error Display -->
    <div v-if="error" class="error-message">
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <div>
        <strong>Error:</strong> {{ error }}
      </div>
      <button @click="error = null" class="btn-close">×</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// File handling
const fileInput = ref<HTMLInputElement | null>(null)
const isDragOver = ref(false)
const uploadedFile = ref<File | null>(null)

// Phase 1: Analysis state
const isAnalyzing = ref(false)
const analysis = ref<any>(null)
const analysisProgress = ref(0)
let analysisInterval: any = null

// Phase 2: Vectorization state
const isVectorizing = ref(false)
const vectorizedGeometry = ref<any>(null)
const vectorParams = ref({
  scaleFactor: 1.0,
  lowThreshold: 50,
  highThreshold: 150,
  minArea: 100
})

// Export state
const isExporting = ref(false)

// Phase 3: CAM state
const isSendingToCAM = ref(false)
const rmosResult = ref<any>(null)
const camParams = ref({
  tool_d: 6.0,
  stepover: 0.45,
  stepdown: 1.5,
  z_rough: -3.0,
  feed_xy: 1200,
  feed_z: 300,
  rapid: 3000,
  safe_z: 5.0,
  strategy: 'Spiral',
  layer_name: 'GEOMETRY',
  climb: true,
  smoothing: 0.1,
  margin: 0.0
})

// Computed: G-code ready for download
const gcodeReady = computed(() => rmosResult.value?.gcode?.inline && !!rmosResult.value?.gcode?.text)

// Error state
const error = ref<string | null>(null)

// File selection
const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files[0]) {
    validateAndSetFile(target.files[0])
  }
}

const handleDrop = (event: DragEvent) => {
  isDragOver.value = false
  if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
    validateAndSetFile(event.dataTransfer.files[0])
  }
}

const validateAndSetFile = (file: File) => {
  const allowedTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg']
  if (!allowedTypes.includes(file.type)) {
    error.value = `Unsupported file type: ${file.type}. Use PDF, PNG, or JPG.`
    return
  }

  if (file.size > 20 * 1024 * 1024) {
    error.value = 'File too large. Maximum size: 20MB'
    return
  }

  uploadedFile.value = file
  error.value = null
}

// Phase 1: AI Analysis
const analyzeBlueprint = async () => {
  if (!uploadedFile.value) return

  try {
    isAnalyzing.value = true
    error.value = null
    analysisProgress.value = 0

    // Start progress timer
    analysisInterval = setInterval(() => {
      analysisProgress.value++
    }, 1000)

    const formData = new FormData()
    formData.append('file', uploadedFile.value)

    const response = await fetch('/api/blueprint/analyze', {
      method: 'POST',
      body: formData
    })

    clearInterval(analysisInterval)

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || 'Analysis failed')
    }

    const result = await response.json()

    if (!result.success) {
      error.value = result.message || 'Analysis failed'
      return
    }

    analysis.value = result.analysis
  } catch (err: any) {
    console.error('Analysis error:', err)
    error.value = err.message || 'Failed to analyze blueprint'
  } finally {
    isAnalyzing.value = false
    clearInterval(analysisInterval)
  }
}

// Phase 2: Vectorization
const vectorizeGeometry = async () => {
  if (!uploadedFile.value || !analysis.value) return

  try {
    isVectorizing.value = true
    error.value = null

    const formData = new FormData()
    formData.append('file', uploadedFile.value)
    formData.append('analysis_data', JSON.stringify(analysis.value))
    formData.append('scale_factor', vectorParams.value.scaleFactor.toString())
    formData.append('low_threshold', vectorParams.value.lowThreshold.toString())
    formData.append('high_threshold', vectorParams.value.highThreshold.toString())
    formData.append('min_area', vectorParams.value.minArea.toString())

    const response = await fetch('/api/blueprint/vectorize-geometry', {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || 'Vectorization failed')
    }

    const result = await response.json()
    vectorizedGeometry.value = result

  } catch (err: any) {
    console.error('Vectorization error:', err)
    error.value = err.message || 'Failed to vectorize geometry'
  } finally {
    isVectorizing.value = false
  }
}

// Export functions
const exportSVGBasic = async () => {
  if (!analysis.value) return

  try {
    isExporting.value = true
    error.value = null

    const response = await fetch('/api/blueprint/to-svg', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        analysis_data: analysis.value,
        format: 'svg',
        scale_correction: 1.0,
        width_mm: 300,
        height_mm: 200
      })
    })

    if (!response.ok) throw new Error('SVG export failed')

    const blob = await response.blob()
    downloadBlob(blob, 'blueprint_dimensions.svg')
  } catch (err: any) {
    console.error('Export error:', err)
    error.value = err.message || 'Failed to export SVG'
  } finally {
    isExporting.value = false
  }
}

// Navigate to Parametric Designer with extracted dimensions
const editDimensions = () => {
  if (!analysis.value?.dimensions) return

  // Helper function to parse dimension value (handles "475mm", "18.7 inches", etc.)
  const parseDimension = (label: string): number | undefined => {
    const dim = analysis.value.dimensions.find((d: any) => 
      d.label.toLowerCase().includes(label.toLowerCase())
    )
    if (!dim?.value) return undefined
    
    // Extract numeric value and unit
    const match = dim.value.match(/([\d.]+)\s*(mm|inch|in|"|cm)?/i)
    if (!match) return undefined
    
    let value = parseFloat(match[1])
    const unit = match[2]?.toLowerCase()
    
    // Convert to mm if needed
    if (unit === 'inch' || unit === 'in' || unit === '"') {
      value = value * 25.4
    } else if (unit === 'cm') {
      value = value * 10
    }
    
    return value
  }

  // Extract dimensions (try common guitar dimension labels)
  const extractedDims: any = {
    preset: 'ai-extracted'
  }

  // Body dimensions
  const bodyLength = parseDimension('body length') || parseDimension('total length') || parseDimension('length')
  const bodyWidthLower = parseDimension('lower bout') || parseDimension('body width') || parseDimension('width')
  const bodyWidthUpper = parseDimension('upper bout')
  const bodyWidthWaist = parseDimension('waist')

  if (bodyLength) extractedDims.bodyLength = bodyLength
  if (bodyWidthLower) extractedDims.bodyWidthLower = bodyWidthLower
  if (bodyWidthUpper) extractedDims.bodyWidthUpper = bodyWidthUpper
  if (bodyWidthWaist) extractedDims.bodyWidthWaist = bodyWidthWaist

  // Neck dimensions (optional)
  const neckLength = parseDimension('neck length')
  const neckWidth = parseDimension('neck width') || parseDimension('nut width')
  const scaleLength = parseDimension('scale length') || parseDimension('scale')

  if (neckLength) extractedDims.neckLength = neckLength
  if (neckWidth) extractedDims.neckWidth = neckWidth
  if (scaleLength) extractedDims.scaleLength = scaleLength

  // Navigate to GuitarDimensionsForm with query params
  router.push({
    path: '/guitar-dimensions',
    query: extractedDims
  })
}

const downloadVectorizedSVG = async () => {
  if (!vectorizedGeometry.value?.svg_path) return
  
  try {
    const response = await fetch(`/api/blueprint/static/${vectorizedGeometry.value.svg_path.split('/').pop()}`)
    const blob = await response.blob()
    downloadBlob(blob, 'blueprint_vectorized.svg')
  } catch (err: any) {
    error.value = 'Failed to download SVG: ' + err.message
  }
}

const downloadVectorizedDXF = async () => {
  if (!vectorizedGeometry.value?.dxf_path) return
  
  try {
    const response = await fetch(`/api/blueprint/static/${vectorizedGeometry.value.dxf_path.split('/').pop()}`)
    const blob = await response.blob()
    downloadBlob(blob, 'blueprint_vectorized.dxf')
  } catch (err: any) {
    error.value = 'Failed to download DXF: ' + err.message
  }
}

const downloadBlob = (blob: Blob, filename: string) => {
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  window.URL.revokeObjectURL(url)
}

// Phase 3: Send to CAM (MVP Wrapper)
const sendToCAM = async () => {
  if (\!vectorizedGeometry.value?.dxf_path) return

  try {
    isSendingToCAM.value = true
    error.value = null
    rmosResult.value = null

    // Fetch the DXF file from server
    const dxfResponse = await fetch(\)
    if (\!dxfResponse.ok) throw new Error('Failed to fetch DXF file')
    const dxfBlob = await dxfResponse.blob()

    // Build form data for MVP wrapper
    const fd = new FormData()
    fd.append('file', dxfBlob, 'blueprint.dxf')

    // Add all CAM parameters
    for (const [k, v] of Object.entries(camParams.value)) {
      if (typeof v === 'boolean') {
        fd.append(k, v ? 'true' : 'false')
      } else {
        fd.append(k, String(v))
      }
    }

    // Call MVP wrapper endpoint
    const response = await fetch('/api/rmos/wrap/mvp/dxf-to-grbl', {
      method: 'POST',
      body: fd
    })

    if (\!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || \)
    }

    rmosResult.value = await response.json()

  } catch (err: any) {
    console.error('CAM error:', err)
    error.value = err.message || 'Failed to generate G-code'
  } finally {
    isSendingToCAM.value = false
  }
}

// Download G-code from inline response
const downloadGcode = () => {
  if (\!rmosResult.value?.gcode?.inline || \!rmosResult.value?.gcode?.text) return

  const blob = new Blob([rmosResult.value.gcode.text], { type: 'text/plain' })
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  const baseName = (uploadedFile.value?.name || 'blueprint').replace(/\.[^.]+$/, '')
  a.download =   document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  window.URL.revokeObjectURL(url)
}

// Reset workflow
const resetWorkflow = () => {
  uploadedFile.value = null
  analysis.value = null
  vectorizedGeometry.value = null
  error.value = null
  analysisProgress.value = 0
  if (fileInput.value) fileInput.value.value = ''
}

// Cleanup
onUnmounted(() => {
  if (analysisInterval) clearInterval(analysisInterval)
})
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

.phase-3 {
  background: #f59e0b;
  color: white;
}

/* Upload Zone */
.upload-zone {
  border: 3px dashed #d1d5db;
  border-radius: 1rem;
  padding: 3rem;
  text-align: center;
  background: #f9fafb;
  transition: all 0.3s;
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.upload-zone.drag-over {
  border-color: #3b82f6;
  background: #eff6ff;
}

.upload-icon {
  width: 64px;
  height: 64px;
  color: #9ca3af;
  margin-bottom: 1rem;
}

.upload-text {
  font-size: 1.125rem;
  color: #374151;
  margin-bottom: 0.5rem;
}

.browse-btn {
  color: #3b82f6;
  text-decoration: underline;
  background: none;
  border: none;
  cursor: pointer;
  font-size: inherit;
}

.upload-hint {
  color: #6b7280;
  font-size: 0.875rem;
}

/* Workflow Sections */
.workflow {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.workflow-section {
  border: 2px solid #e5e7eb;
  border-radius: 1rem;
  padding: 1.5rem;
  background: white;
}

.workflow-section.phase-2 {
  border-color: #10b981;
}

.workflow-section.phase-3 {
  border-color: #f59e0b;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.section-header h2 {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin: 0;
}

.step-number {
  background: #3b82f6;
  color: white;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
}

.workflow-section.phase-2 .step-number {
  background: #10b981;
}

.workflow-section.phase-3 .step-number {
  background: #f59e0b;
}

/* Action Cards */
.action-card {
  background: #f9fafb;
  border-radius: 0.5rem;
  padding: 1.5rem;
  text-align: center;
}

.hint {
  color: #6b7280;
  margin-bottom: 1rem;
}

.hint-small {
  color: #9ca3af;
  font-size: 0.875rem;
  margin-top: 0.5rem;
}

.progress-timer {
  color: #6b7280;
  font-size: 0.875rem;
  margin-top: 0.5rem;
}

/* Results Cards */
.results-card {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.scale-grid,
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.info-card {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.info-card .label {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 600;
}

.info-card .value {
  font-size: 1.125rem;
  color: #111827;
}

.stat-card {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 0.5rem;
  padding: 1rem;
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 1.5rem;
  font-weight: bold;
  color: #0c4a6e;
}

.stat-label {
  display: block;
  font-size: 0.875rem;
  color: #0369a1;
  margin-top: 0.25rem;
}

.confidence {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.confidence-high {
  background: #d1fae5;
  color: #065f46;
}

.confidence-medium {
  background: #fef3c7;
  color: #92400e;
}

.confidence-low {
  background: #fee2e2;
  color: #991b1b;
}

/* Dimensions Table */
.dimensions-details {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1rem;
}

.dimensions-details summary {
  cursor: pointer;
  user-select: none;
  margin-bottom: 1rem;
}

.dimensions-table {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  overflow: hidden;
}

.table-header {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 1rem;
  padding: 0.75rem 1rem;
  background: #f3f4f6;
  font-weight: 600;
  font-size: 0.875rem;
  color: #374151;
}

.table-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 1rem;
  padding: 0.75rem 1rem;
  border-top: 1px solid #e5e7eb;
  align-items: center;
}

.table-row.detected {
  background: #f0fdf4;
}

.table-row.estimated {
  background: #fffbeb;
}

.dim-type {
  text-transform: capitalize;
  font-size: 0.875rem;
}

.dim-type.detected {
  color: #059669;
}

.dim-type.estimated {
  color: #d97706;
}

/* Controls */
.controls-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
  text-align: left;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.control-group label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
}

.control-group input {
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 1rem;
}

.control-hint {
  font-size: 0.75rem;
  color: #6b7280;
}

/* Preview */
.preview-section {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1rem;
}

.preview-placeholder {
  text-align: center;
  padding: 2rem;
  border: 2px dashed #d1d5db;
  border-radius: 0.5rem;
}

.preview-placeholder a {
  color: #3b82f6;
  text-decoration: underline;
}

/* Buttons */
.export-row {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.btn-primary,
.btn-secondary {
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s;
}

.btn-primary {
  background: #3b82f6;
  color: white;
  border: none;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-secondary {
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-secondary:hover:not(:disabled) {
  background: #f9fafb;
}

.btn-primary:disabled,
.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary svg,
.btn-secondary svg {
  width: 20px;
  height: 20px;
}

/* Error */
.error-message {
  background: #fee2e2;
  border-left: 4px solid #dc2626;
  padding: 1rem;
  border-radius: 0.5rem;
  display: flex;
  align-items: start;
  gap: 1rem;
  margin-top: 1rem;
}

.error-message svg {
  width: 24px;
  height: 24px;
  color: #dc2626;
  flex-shrink: 0;
}

.btn-close {
  margin-left: auto;
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #991b1b;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}
/* Warning list */
.warning-list {
  background: #fffbeb;
  border: 1px solid #fcd34d;
  border-radius: 0.5rem;
  padding: 1rem;
}

.warning-list ul {
  margin: 0.5rem 0 0 1.5rem;
  padding: 0;
}

.warning-list li {
  color: #92400e;
  font-size: 0.875rem;
}

/* RMOS Error */
.rmos-error {
  background: #fef2f2;
  border: 1px solid #fca5a5;
  border-radius: 0.5rem;
  padding: 1rem;
  color: #991b1b;
  font-size: 0.875rem;
}
</style>
