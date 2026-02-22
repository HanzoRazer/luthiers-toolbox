<template>
  <div :class="styles.camBridgePreflightPanel">
    <div :class="styles.panelHeader">
      <h3>Bridge DXF Preflight</h3>
      <p :class="[styles.textSm, styles.textGray600]">
        Validate DXF geometry before CAM processing
      </p>
    </div>

    <!-- File Upload Section -->
    <div :class="styles.uploadSection">
      <div 
        :class="dropZoneClass"
        @drop.prevent="onDrop"
        @dragover.prevent="isDragging = true"
        @dragleave="isDragging = false"
      >
        <div
          v-if="!file"
          :class="styles.uploadPrompt"
        >
          <div :class="styles.uploadPromptIcon">
            📄
          </div>
          <p>Drag & drop DXF file here</p>
          <p :class="styles.orText">
            or
          </p>
          <label :class="styles.uploadButton">
            Browse Files
            <input
              type="file"
              accept=".dxf"
              hidden
              @change="onFileChange"
            >
          </label>
        </div>
        
        <div
          v-else
          :class="styles.fileInfo"
        >
          <div :class="styles.uploadPromptIcon">
            ✅
          </div>
          <div :class="styles.fileDetails">
            <h4>{{ file.name }}</h4>
            <p :class="[styles.textSm, styles.textGray600]">
              {{ formatFileSize(file.size) }}
            </p>
          </div>
          <button
            :class="styles.clearBtn"
            title="Remove file"
            @click="clearFile"
          >
            ✕
          </button>
        </div>
      </div>

      <button 
        v-if="file && !preflightResult"
        :class="styles.btnPrimary" 
        :disabled="preflightRunning"
        @click="runPreflight"
      >
        {{ preflightRunning ? 'Validating...' : 'Run Preflight Check' }}
      </button>
    </div>

    <!-- Preflight Results -->
    <div
      v-if="preflightResult"
      :class="styles.preflightResults"
    >
      <div :class="styles.resultsHeader">
        <h4>Validation Results</h4>
        <div
          :class="preflightResult.passed ? styles.statusBadgePassed : styles.statusBadgeFailed"
        >
          {{ preflightResult.passed ? '✅ PASSED' : '❌ FAILED' }}
        </div>
      </div>

      <div :class="styles.resultsSummary">
        <div :class="styles.summaryItem">
          <span :class="styles.summaryItemLabel">File:</span>
          <span :class="styles.summaryItemValue">{{ preflightResult.filename }}</span>
        </div>
        <div :class="styles.summaryItem">
          <span :class="styles.summaryItemLabel">DXF Version:</span>
          <span :class="styles.summaryItemValue">{{ preflightResult.dxf_version }}</span>
        </div>
        <div :class="styles.summaryItem">
          <span :class="styles.summaryItemLabel">Entities:</span>
          <span :class="styles.summaryItemValue">{{ preflightResult.total_entities }}</span>
        </div>
        <div :class="styles.summaryItem">
          <span :class="styles.summaryItemLabel">Layers:</span>
          <span :class="styles.summaryItemValue">{{ preflightResult.layers?.length || 0 }}</span>
        </div>
      </div>

      <!-- Issue Summary -->
      <div
        v-if="preflightResult.summary"
        :class="styles.issueSummary"
      >
        <div
          v-if="preflightResult.summary.errors > 0"
          :class="[styles.issueCount, styles.issueCountError]"
        >
          <span :class="styles.issueCountBadge">{{ preflightResult.summary.errors }}</span>
          <span :class="styles.issueCountLabel">Errors</span>
        </div>
        <div
          v-if="preflightResult.summary.warnings > 0"
          :class="[styles.issueCount, styles.issueCountWarning]"
        >
          <span :class="styles.issueCountBadge">{{ preflightResult.summary.warnings }}</span>
          <span :class="styles.issueCountLabel">Warnings</span>
        </div>
        <div
          v-if="preflightResult.summary.info > 0"
          :class="[styles.issueCount, styles.issueCountInfo]"
        >
          <span :class="styles.issueCountBadge">{{ preflightResult.summary.info }}</span>
          <span :class="styles.issueCountLabel">Info</span>
        </div>
      </div>

      <!-- Issues List -->
      <div
        v-if="preflightResult.issues && preflightResult.issues.length > 0"
        :class="styles.issuesList"
      >
        <h5>Issues Found</h5>
        <div 
          v-for="(issue, idx) in preflightResult.issues" 
          :key="idx"
          :class="issueItemClass(issue.severity)"
        >
          <div :class="styles.issueHeader">
            <span :class="styles.severityBadge">{{ issue.severity }}</span>
            <span :class="styles.category">{{ issue.category }}</span>
          </div>
          <p :class="styles.issueMessage">
            {{ issue.message }}
          </p>
          <p
            v-if="issue.layer"
            :class="styles.issueDetail"
          >
            Layer: {{ issue.layer }}
          </p>
          <p
            v-if="issue.suggestion"
            :class="styles.issueSuggestion"
          >
            💡 {{ issue.suggestion }}
          </p>
        </div>
      </div>

      <!-- Actions -->
      <div :class="styles.resultsActions">
        <button
          :class="styles.btnSecondary"
          @click="downloadHTMLReport"
        >
          📄 Download HTML Report
        </button>
        <button
          :class="styles.btnSecondary"
          @click="clearResults"
        >
          🔄 Check Another File
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { api } from '@/services/apiBase';
import { ref, computed } from 'vue'
import styles from './CamBridgePreflightPanel.module.css'

// Component events
const emit = defineEmits<{
  (e: 'preflight-result', result: any): void
  (e: 'dxf-file-changed', file: File | null): void
}>()

// State
const file = ref<File | null>(null)
const isDragging = ref(false)
const preflightRunning = ref(false)
const preflightResult = ref<any>(null)

// Computed classes
const dropZoneClass = computed(() => {
  if (file.value) return styles.dropZoneHasFile
  if (isDragging.value) return styles.dropZoneDragging
  return styles.dropZone
})

function issueItemClass(severity: string) {
  const level = severity.toLowerCase()
  if (level === 'error') return styles.issueItemError
  if (level === 'warning') return styles.issueItemWarning
  if (level === 'info') return styles.issueItemInfo
  return styles.issueItem
}

// File handling
function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const f = input.files?.[0] ?? null
  
  if (f && !f.name.toLowerCase().endsWith('.dxf')) {
    alert('Please select a DXF file')
    return
  }
  
  file.value = f
  preflightResult.value = null
  emit('dxf-file-changed', f)
}

function onDrop(event: DragEvent) {
  isDragging.value = false
  const f = event.dataTransfer?.files[0]
  
  if (!f) return
  
  if (!f.name.toLowerCase().endsWith('.dxf')) {
    alert('Please drop a DXF file')
    return
  }
  
  file.value = f
  preflightResult.value = null
  emit('dxf-file-changed', f)
}

function clearFile() {
  file.value = null
  preflightResult.value = null
  emit('dxf-file-changed', null)
}

function clearResults() {
  preflightResult.value = null
}

function loadExternalFile(external: File | null) {
  file.value = external
  preflightResult.value = null
  emit('dxf-file-changed', external)
}

defineExpose({ loadExternalFile })

// Preflight validation
async function runPreflight() {
  if (!file.value) return
  
  preflightRunning.value = true
  
  try {
    const formData = new FormData()
    formData.append('file', file.value)
    formData.append('format', 'json')
    
    const response = await api('/api/cam/blueprint/preflight', {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) {
      throw new Error(`Preflight failed: ${response.statusText}`)
    }
    
    const result = await response.json()
    preflightResult.value = result
    emit('preflight-result', result)
  } catch (error) {
    console.error('Preflight error:', error)
    alert(`Preflight check failed: ${error}`)
  } finally {
    preflightRunning.value = false
  }
}

async function downloadHTMLReport() {
  if (!file.value) return
  
  try {
    const formData = new FormData()
    formData.append('file', file.value)
    formData.append('format', 'html')
    
    const response = await api('/api/cam/blueprint/preflight', {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) throw new Error('Failed to generate HTML report')
    
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `bridge_preflight_${Date.now()}.html`
    a.click()
    URL.revokeObjectURL(url)
  } catch (error) {
    console.error('HTML report error:', error)
    alert(`Failed to download HTML report: ${error}`)
  }
}

// Utilities
function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
</script>

