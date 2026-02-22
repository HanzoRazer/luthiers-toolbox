<template>
  <div :class="styles.blueprintImporter">
    <!-- Header -->
    <div :class="styles.header">
      <h2>Blueprint Importer</h2>
      <span :class="styles.phaseBadge">Phase 1</span>
    </div>

    <!-- Upload Zone -->
    <div
      :class="isDragOver ? styles.uploadZoneDragOver : isUploading ? styles.uploadZoneUploading : styles.uploadZone"
      @drop.prevent="handleDrop"
      @dragover.prevent="isDragOver = true"
      @dragleave="isDragOver = false"
    >
      <input
        ref="fileInput"
        type="file"
        accept=".pdf,.png,.jpg,.jpeg"
        style="display: none"
        @change="handleFileSelect"
      >

      <div
        v-if="!isUploading && !analysis"
        :class="styles.uploadPrompt"
      >
        <svg
          :class="styles.uploadIcon"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
          />
        </svg>
        <p :class="styles.uploadText">
          <strong>Drop blueprint here</strong> or <button
            :class="styles.browseBtn"
            @click="($refs.fileInput as HTMLInputElement)?.click()"
          >
            browse
          </button>
        </p>
        <p :class="styles.uploadHint">
          Supports PDF, PNG, JPG (max 20MB)
        </p>
      </div>

      <div
        v-if="isUploading"
        :class="styles.uploadProgress"
      >
        <div :class="styles.spinner" />
        <p>Analyzing with Claude Sonnet 4...</p>
        <p :class="styles.progressTime">
          {{ uploadProgress }}s elapsed
        </p>
      </div>
    </div>

    <!-- Analysis Results -->
    <div
      v-if="analysis && !isUploading"
      :class="styles.analysisResults"
    >
      <div :class="styles.resultsHeader">
        <h3>Analysis Results</h3>
        <button
          :class="styles.btnSecondary"
          @click="reset"
        >
          New Blueprint
        </button>
      </div>

      <!-- Scale Info -->
      <div :class="styles.scaleInfo">
        <div :class="styles.infoCard">
          <span :class="styles.infoLabel">Detected Scale:</span>
          <span :class="styles.infoValue">{{ analysis.scale || 'Unknown' }}</span>
          <span :class="analysis.scale_confidence === 'high' ? styles.confidenceHigh : analysis.scale_confidence === 'medium' ? styles.confidenceMedium : styles.confidenceLow">
            {{ analysis.scale_confidence || 'unknown' }}
          </span>
        </div>
        <div
          v-if="analysis.blueprint_type"
          :class="styles.infoCard"
        >
          <span :class="styles.infoLabel">Type:</span>
          <span :class="styles.infoValue">{{ analysis.blueprint_type }}</span>
        </div>
        <div
          v-if="analysis.detected_model"
          :class="styles.infoCard"
        >
          <span :class="styles.infoLabel">Model:</span>
          <span :class="styles.infoValue">{{ analysis.detected_model }}</span>
        </div>
      </div>

      <!-- Dimensions Table -->
      <div :class="styles.dimensionsSection">
        <h4>Detected Dimensions ({{ analysis.dimensions?.length || 0 }})</h4>
        <div :class="styles.dimensionsTable">
          <div :class="styles.tableHeader">
            <span>Label</span>
            <span>Value</span>
            <span>Type</span>
            <span>Confidence</span>
          </div>
          <div
            v-for="(dim, idx) in analysis.dimensions?.slice(0, 20)"
            :key="idx"
            :class="dim.type === 'detected' ? styles.tableRowDetected : dim.type === 'estimated' ? styles.tableRowEstimated : styles.tableRow"
          >
            <span :class="styles.dimLabel">{{ dim.label }}</span>
            <span :class="styles.dimValue">{{ dim.value }}</span>
            <span :class="dim.type === 'detected' ? styles.dimTypeDetected : styles.dimTypeEstimated">{{ dim.type }}</span>
            <span :class="dim.confidence === 'high' ? styles.confidenceHigh : dim.confidence === 'medium' ? styles.confidenceMedium : styles.confidenceLow">
              {{ dim.confidence }}
            </span>
          </div>
        </div>
      </div>

      <!-- Export Actions -->
      <div :class="styles.exportActions">
        <button
          :class="styles.btnPrimary"
          :disabled="isExporting"
          @click="exportSVG"
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
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
            />
          </svg>
          {{ isExporting ? 'Exporting...' : 'Export SVG' }}
        </button>
        <button
          :class="styles.btnSecondary"
          disabled
          title="Coming in Phase 2"
          @click="exportDXF"
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
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
            />
          </svg>
          Export DXF (Phase 2)
        </button>
      </div>

      <!-- Notes -->
      <div
        v-if="analysis.notes"
        :class="styles.analysisNotes"
      >
        <h4>Analysis Notes</h4>
        <p>{{ analysis.notes }}</p>
      </div>
    </div>

    <!-- Error Display -->
    <div
      v-if="error"
      :class="styles.errorMessage"
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
        :class="styles.btnClose"
        @click="error = null"
      >
        ×
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { api } from '@/services/apiBase';
import { ref, onMounted, onUnmounted } from 'vue'
import styles from './BlueprintImporter.module.css'

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
    const response = await api('/api/blueprint/analyze', {
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

    const response = await api('/api/blueprint/to-svg', {
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

