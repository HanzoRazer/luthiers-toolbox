<template>
  <div class="cam-bridge-preflight-panel">
    <div class="panel-header">
      <h3>Bridge DXF Preflight</h3>
      <p class="text-sm text-gray-600">Validate DXF geometry before CAM processing</p>
    </div>

    <!-- File Upload Section -->
    <div class="upload-section">
      <div 
        class="drop-zone"
        :class="{ 'dragging': isDragging, 'has-file': file }"
        @drop.prevent="onDrop"
        @dragover.prevent="isDragging = true"
        @dragleave="isDragging = false"
      >
        <div v-if="!file" class="upload-prompt">
          <div class="icon">📄</div>
          <p>Drag & drop DXF file here</p>
          <p class="or-text">or</p>
          <label class="upload-button">
            Browse Files
            <input type="file" accept=".dxf" @change="onFileChange" hidden>
          </label>
        </div>
        
        <div v-else class="file-info">
          <div class="icon">✅</div>
          <div class="file-details">
            <h4>{{ file.name }}</h4>
            <p class="text-sm text-gray-600">{{ formatFileSize(file.size) }}</p>
          </div>
          <button @click="clearFile" class="clear-btn" title="Remove file">✕</button>
        </div>
      </div>

      <button 
        v-if="file && !preflightResult"
        @click="runPreflight" 
        class="btn-primary"
        :disabled="preflightRunning"
      >
        {{ preflightRunning ? 'Validating...' : 'Run Preflight Check' }}
      </button>
    </div>

    <!-- Preflight Results -->
    <div v-if="preflightResult" class="preflight-results">
      <div class="results-header">
        <h4>Validation Results</h4>
        <div class="status-badge" :class="preflightResult.passed ? 'passed' : 'failed'">
          {{ preflightResult.passed ? '✅ PASSED' : '❌ FAILED' }}
        </div>
      </div>

      <div class="results-summary">
        <div class="summary-item">
          <span class="label">File:</span>
          <span class="value">{{ preflightResult.filename }}</span>
        </div>
        <div class="summary-item">
          <span class="label">DXF Version:</span>
          <span class="value">{{ preflightResult.dxf_version }}</span>
        </div>
        <div class="summary-item">
          <span class="label">Entities:</span>
          <span class="value">{{ preflightResult.total_entities }}</span>
        </div>
        <div class="summary-item">
          <span class="label">Layers:</span>
          <span class="value">{{ preflightResult.layers?.length || 0 }}</span>
        </div>
      </div>

      <!-- Issue Summary -->
      <div v-if="preflightResult.summary" class="issue-summary">
        <div class="issue-count error" v-if="preflightResult.summary.errors > 0">
          <span class="badge">{{ preflightResult.summary.errors }}</span>
          <span class="label">Errors</span>
        </div>
        <div class="issue-count warning" v-if="preflightResult.summary.warnings > 0">
          <span class="badge">{{ preflightResult.summary.warnings }}</span>
          <span class="label">Warnings</span>
        </div>
        <div class="issue-count info" v-if="preflightResult.summary.info > 0">
          <span class="badge">{{ preflightResult.summary.info }}</span>
          <span class="label">Info</span>
        </div>
      </div>

      <!-- Issues List -->
      <div v-if="preflightResult.issues && preflightResult.issues.length > 0" class="issues-list">
        <h5>Issues Found</h5>
        <div 
          v-for="(issue, idx) in preflightResult.issues" 
          :key="idx"
          class="issue-item"
          :class="issue.severity.toLowerCase()"
        >
          <div class="issue-header">
            <span class="severity-badge">{{ issue.severity }}</span>
            <span class="category">{{ issue.category }}</span>
          </div>
          <p class="issue-message">{{ issue.message }}</p>
          <p v-if="issue.layer" class="issue-detail">Layer: {{ issue.layer }}</p>
          <p v-if="issue.suggestion" class="issue-suggestion">💡 {{ issue.suggestion }}</p>
        </div>
      </div>

      <!-- Actions -->
      <div class="results-actions">
        <button @click="downloadHTMLReport" class="btn-secondary">
          📄 Download HTML Report
        </button>
        <button @click="clearResults" class="btn-secondary">
          🔄 Check Another File
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

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
    
    const response = await fetch('/api/cam/blueprint/preflight', {
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
    
    const response = await fetch('/api/cam/blueprint/preflight', {
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

<style scoped>
.cam-bridge-preflight-panel {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1.5rem;
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.panel-header h3 {
  margin: 0 0 0.25rem 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
}

.upload-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.drop-zone {
  border: 2px dashed #d1d5db;
  border-radius: 0.5rem;
  padding: 2rem;
  text-align: center;
  transition: all 0.2s;
  background: #f9fafb;
}

.drop-zone.dragging {
  border-color: #3b82f6;
  background: #eff6ff;
}

.drop-zone.has-file {
  border-color: #10b981;
  background: #f0fdf4;
}

.upload-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}

.upload-prompt .icon {
  font-size: 3rem;
}

.upload-prompt p {
  margin: 0;
  color: #6b7280;
}

.or-text {
  font-size: 0.875rem;
  color: #9ca3af;
}

.upload-button {
  display: inline-block;
  padding: 0.5rem 1rem;
  background: #3b82f6;
  color: white;
  border-radius: 0.375rem;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s;
}

.upload-button:hover {
  background: #2563eb;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.file-info .icon {
  font-size: 2rem;
}

.file-details {
  flex: 1;
  text-align: left;
}

.file-details h4 {
  margin: 0;
  font-size: 1rem;
  font-weight: 500;
  color: #1f2937;
}

.clear-btn {
  padding: 0.25rem 0.5rem;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  font-size: 1.25rem;
  line-height: 1;
}

.clear-btn:hover {
  background: #dc2626;
}

.btn-primary, .btn-secondary {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.375rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-primary:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.btn-secondary {
  background: #e5e7eb;
  color: #1f2937;
}

.btn-secondary:hover {
  background: #d1d5db;
}

/* Results */
.preflight-results {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
  background: #f9fafb;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.results-header h4 {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 0.25rem;
  font-weight: 600;
  font-size: 0.875rem;
}

.status-badge.passed {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.failed {
  background: #fee2e2;
  color: #991b1b;
}

.results-summary {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.5rem;
}

.summary-item {
  display: flex;
  gap: 0.5rem;
  font-size: 0.875rem;
}

.summary-item .label {
  font-weight: 500;
  color: #6b7280;
}

.summary-item .value {
  color: #1f2937;
}

.issue-summary {
  display: flex;
  gap: 1rem;
  padding: 0.75rem;
  background: white;
  border-radius: 0.375rem;
}

.issue-count {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.issue-count .badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.5rem;
  height: 1.5rem;
  padding: 0 0.5rem;
  border-radius: 9999px;
  font-weight: 600;
  font-size: 0.875rem;
}

.issue-count.error .badge {
  background: #fecaca;
  color: #991b1b;
}

.issue-count.warning .badge {
  background: #fef3c7;
  color: #92400e;
}

.issue-count.info .badge {
  background: #dbeafe;
  color: #1e40af;
}

.issue-count .label {
  font-size: 0.875rem;
  color: #6b7280;
}

.issues-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.issues-list h5 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
}

.issue-item {
  padding: 0.75rem;
  background: white;
  border-left: 4px solid #d1d5db;
  border-radius: 0.375rem;
}

.issue-item.error {
  border-left-color: #ef4444;
}

.issue-item.warning {
  border-left-color: #f59e0b;
}

.issue-item.info {
  border-left-color: #3b82f6;
}

.issue-header {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.severity-badge {
  padding: 0.125rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.issue-item.error .severity-badge {
  background: #fee2e2;
  color: #991b1b;
}

.issue-item.warning .severity-badge {
  background: #fef3c7;
  color: #92400e;
}

.issue-item.info .severity-badge {
  background: #dbeafe;
  color: #1e40af;
}

.category {
  padding: 0.125rem 0.5rem;
  background: #f3f4f6;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  color: #6b7280;
}

.issue-message {
  margin: 0 0 0.5rem 0;
  font-size: 0.875rem;
  color: #1f2937;
}

.issue-detail {
  margin: 0 0 0.25rem 0;
  font-size: 0.75rem;
  color: #6b7280;
}

.issue-suggestion {
  margin: 0.5rem 0 0 0;
  padding: 0.5rem;
  background: #fffbeb;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  color: #92400e;
}

.results-actions {
  display: flex;
  gap: 0.75rem;
  padding-top: 0.5rem;
  border-top: 1px solid #e5e7eb;
}

.results-actions button {
  flex: 1;
}
</style>
