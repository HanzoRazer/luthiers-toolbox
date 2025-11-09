<template>
  <div class="blueprint-importer">
    <!-- Header -->
    <div class="header">
      <h2>Blueprint Importer</h2>
      <span class="phase-badge">Phase 1</span>
    </div>

    <!-- Upload Zone -->
    <div
      class="upload-zone"
      :class="{ 'drag-over': isDragOver, 'uploading': isUploading }"
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
      
      <div v-if="!isUploading && !analysis" class="upload-prompt">
        <svg class="upload-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
        <p class="upload-text">
          <strong>Drop blueprint here</strong> or <button @click="$refs.fileInput.click()" class="browse-btn">browse</button>
        </p>
        <p class="upload-hint">Supports PDF, PNG, JPG (max 20MB)</p>
      </div>

      <div v-if="isUploading" class="upload-progress">
        <div class="spinner"></div>
        <p>Analyzing with Claude Sonnet 4...</p>
        <p class="progress-time">{{ uploadProgress }}s elapsed</p>
      </div>
    </div>

    <!-- Analysis Results -->
    <div v-if="analysis && !isUploading" class="analysis-results">
      <div class="results-header">
        <h3>Analysis Results</h3>
        <button @click="reset" class="btn-secondary">New Blueprint</button>
      </div>

      <!-- Scale Info -->
      <div class="scale-info">
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

      <!-- Dimensions Table -->
      <div class="dimensions-section">
        <h4>Detected Dimensions ({{ analysis.dimensions?.length || 0 }})</h4>
        <div class="dimensions-table">
          <div class="table-header">
            <span>Label</span>
            <span>Value</span>
            <span>Type</span>
            <span>Confidence</span>
          </div>
          <div
            v-for="(dim, idx) in analysis.dimensions?.slice(0, 20)"
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
      </div>

      <!-- Export Actions -->
      <div class="export-actions">
        <button @click="exportSVG" class="btn-primary" :disabled="isExporting">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          {{ isExporting ? 'Exporting...' : 'Export SVG' }}
        </button>
        <button @click="exportDXF" class="btn-secondary" disabled title="Coming in Phase 2">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Export DXF (Phase 2)
        </button>
      </div>

      <!-- Notes -->
      <div v-if="analysis.notes" class="analysis-notes">
        <h4>Analysis Notes</h4>
        <p>{{ analysis.notes }}</p>
      </div>
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
import { ref, onMounted, onUnmounted } from 'vue'

// State
const fileInput = ref<HTMLInputElement | null>(null)
const isDragOver = ref(false)
const isUploading = ref(false)
const isExporting = ref(false)
const analysis = ref<any>(null)
const error = ref<string | null>(null)
const uploadProgress = ref(0)
let progressInterval: any = null

// File handling
const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files[0]) {
    uploadBlueprint(target.files[0])
  }
}

const handleDrop = (event: DragEvent) => {
  isDragOver.value = false
  if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
    uploadBlueprint(event.dataTransfer.files[0])
  }
}

// Upload and analyze
const uploadBlueprint = async (file: File) => {
  // Validate file
  const allowedTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg']
  if (!allowedTypes.includes(file.type)) {
    error.value = `Unsupported file type: ${file.type}. Use PDF, PNG, or JPG.`
    return
  }

  if (file.size > 20 * 1024 * 1024) {
    error.value = 'File too large. Maximum size: 20MB'
    return
  }

  try {
    isUploading.value = true
    error.value = null
    uploadProgress.value = 0

    // Start progress timer
    progressInterval = setInterval(() => {
      uploadProgress.value++
    }, 1000)

    // Create form data
    const formData = new FormData()
    formData.append('file', file)

    // Call API
    const response = await fetch('/api/blueprint/analyze', {
      method: 'POST',
      body: formData
    })

    clearInterval(progressInterval)

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
    console.error('Upload error:', err)
    error.value = err.message || 'Failed to analyze blueprint'
  } finally {
    isUploading.value = false
    clearInterval(progressInterval)
  }
}

// Export functions
const exportSVG = async () => {
  if (!analysis.value) return

  try {
    isExporting.value = true
    error.value = null

    const response = await fetch('/api/blueprint/to-svg', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        analysis_data: analysis.value,
        format: 'svg',
        scale_correction: 1.0,
        width_mm: 300,
        height_mm: 200
      })
    })

    if (!response.ok) {
      throw new Error('SVG export failed')
    }

    // Download file
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'blueprint.svg'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  } catch (err: any) {
    console.error('Export error:', err)
    error.value = err.message || 'Failed to export SVG'
  } finally {
    isExporting.value = false
  }
}

const exportDXF = () => {
  error.value = 'DXF export coming in Phase 2. Use SVG export for now.'
}

// Reset
const reset = () => {
  analysis.value = null
  error.value = null
  uploadProgress.value = 0
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

// Cleanup
onUnmounted(() => {
  if (progressInterval) {
    clearInterval(progressInterval)
  }
})
</script>

<style scoped>
.blueprint-importer {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
}

.phase-badge {
  background: #3b82f6;
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 600;
}

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

.upload-progress {
  text-align: center;
}

.spinner {
  border: 4px solid #e5e7eb;
  border-top: 4px solid #3b82f6;
  border-radius: 50%;
  width: 48px;
  height: 48px;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.progress-time {
  color: #6b7280;
  font-size: 0.875rem;
  margin-top: 0.5rem;
}

.analysis-results {
  margin-top: 2rem;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.scale-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.info-card {
  background: white;
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

.dimensions-section {
  margin-bottom: 2rem;
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

.export-actions {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
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

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-secondary:hover:not(:disabled) {
  background: #f9fafb;
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary svg,
.btn-secondary svg {
  width: 20px;
  height: 20px;
}

.analysis-notes {
  background: #f0f9ff;
  border-left: 4px solid #3b82f6;
  padding: 1rem;
  border-radius: 0.5rem;
}

.analysis-notes h4 {
  margin-top: 0;
  margin-bottom: 0.5rem;
  color: #1e40af;
}

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
</style>
