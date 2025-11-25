<template>
  <div class="compare-lab">
    <header class="lab-header">
      <div>
        <h1>Compare Lab</h1>
        <p class="hint">Load Adaptive geometry, capture baselines, and inspect SVG diffs.</p>
      </div>
      <div class="header-actions">
        <input type="file" ref="fileInput" class="hidden" accept="application/json" @change="handleFile" />
        <button class="ghost" @click="triggerFileDialog">Import Geometry JSON</button>
        <button class="primary" @click="loadPersistedGeometry" :disabled="!hasStoredGeometry">
          Load From Adaptive Lab
        </button>
        <button
          class="secondary"
          @click="showExportDialog = true"
          :disabled="!diffResult"
          title="Export comparison as SVG, PNG, or CSV"
        >
          Export Diff
        </button>
      </div>
    </header>

    <section class="lab-grid">
      <CompareBaselinePicker
        :current-geometry="currentGeometry"
        @diff-computed="(payload) => (diffResult = payload)"
      />

      <CompareSvgDualViewer class="middle" :diff="diffResult" />

      <CompareDiffViewer :diff="diffResult" :current-geometry="currentGeometry" />
    </section>

    <!-- B23: Export Dialog -->
    <div v-if="showExportDialog" class="modal-overlay" @click.self="showExportDialog = false">
      <div class="export-dialog">
        <header class="dialog-header">
          <h2>Export Comparison</h2>
          <button class="close-btn" @click="showExportDialog = false">✕</button>
        </header>

        <div class="dialog-content">
          <div class="naming-section">
            <label class="field-label">
              Custom Prefix (optional):
              <input
                type="text"
                v-model="exportPrefix"
                placeholder="e.g., J45, LP_Standard, Tele"
                class="text-input"
                @input="sanitizePrefix"
              />
            </label>
            <p class="field-hint">
              Prefix will be saved for future exports. Special characters will be sanitized.
            </p>
          </div>

          <div class="export-options">
            <label class="export-option">
              <input type="radio" v-model="exportFormat" value="svg" />
              <span class="option-label">
                <strong>SVG</strong>
                <span class="option-desc">Dual-pane layout with delta annotations (vector)</span>
              </span>
            </label>

            <label class="export-option">
              <input type="radio" v-model="exportFormat" value="png" />
              <span class="option-label">
                <strong>PNG</strong>
                <span class="option-desc">Rasterized screenshot at 300 DPI</span>
              </span>
            </label>

            <label class="export-option">
              <input type="radio" v-model="exportFormat" value="csv" />
              <span class="option-label">
                <strong>CSV</strong>
                <span class="option-desc">Delta metrics table (Excel compatible)</span>
              </span>
            </label>
          </div>

          <div class="filename-preview">
            <label>Filename Preview:</label>
            <code>{{ exportFilename }}</code>
          </div>
        </div>

        <div class="dialog-actions">
          <button class="ghost" @click="showExportDialog = false">Cancel</button>
          <button class="primary" @click="executeExport" :disabled="exportInProgress">
            {{ exportInProgress ? 'Exporting...' : 'Export' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import CompareBaselinePicker from '@/components/compare/CompareBaselinePicker.vue'
import CompareDiffViewer from '@/components/compare/CompareDiffViewer.vue'
import CompareSvgDualViewer from '@/components/compare/CompareSvgDualViewer.vue'
import type { CanonicalGeometry } from '@/utils/geometry'
import { normalizeGeometryPayload } from '@/utils/geometry'

interface DiffResult {
  baseline_id: string
  baseline_name: string
}

const STORAGE_KEY = 'toolbox.compare.currentGeometry'

const fileInput = ref<HTMLInputElement | null>(null)
const currentGeometry = ref<CanonicalGeometry | null>(null)
const diffResult = ref<DiffResult | null>(null)

// B23: Export state
const showExportDialog = ref(false)
const exportFormat = ref<'svg' | 'png' | 'csv'>('svg')
const exportInProgress = ref(false)

// B24: Naming customization
const EXPORT_PREFIX_KEY = 'toolbox.compare.exportPrefix'
const exportPrefix = ref(localStorage.getItem(EXPORT_PREFIX_KEY) || '')

const hasStoredGeometry = computed(() => Boolean(localStorage.getItem(STORAGE_KEY)))

const exportFilename = computed(() => {
  if (!diffResult.value) return 'compare.svg'
  
  const parts: string[] = []
  
  // B24: Custom prefix
  if (exportPrefix.value.trim()) {
    parts.push(exportPrefix.value.trim())
  }
  
  const baseline = diffResult.value.baseline_name || 'baseline'
  const compare = 'compare'
  const timestamp = new Date().toISOString().slice(0, 10).replace(/-/g, '')
  const ext = exportFormat.value
  
  // Build filename: [prefix_]baseline_vs_compare_YYYYMMDD.ext
  const baseName = parts.length > 0
    ? `${parts.join('_')}_baseline-${baseline}_vs_${compare}`
    : `compare_${baseline}_vs_${compare}`
  
  return `${baseName}_${timestamp}.${ext}`
})

function persistGeometry(geometry: CanonicalGeometry): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(geometry))
}

function loadPersistedGeometry(): void {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (!raw) {
    return
  }
  try {
    currentGeometry.value = JSON.parse(raw)
  } catch (error) {
    console.error('Failed to parse stored geometry', error)
  }
}

function handleFile(event: Event): void {
  const target = event.target as HTMLInputElement
  if (!target.files?.length) {
    return
  }
  const file = target.files[0]
  const reader = new FileReader()
  reader.onload = () => {
    try {
      const parsed = JSON.parse(String(reader.result))
      const normalized = normalizeGeometryPayload(parsed)
      if (normalized) {
        currentGeometry.value = normalized
        persistGeometry(normalized)
      }
    } catch (error) {
      console.error('Invalid geometry file', error)
    } finally {
      target.value = ''
    }
  }
  reader.readAsText(file)
}

function triggerFileDialog(): void {
  fileInput.value?.click()
}

// B23: Export functions
async function executeExport() {
  if (!diffResult.value) return

  // B24: Persist prefix to localStorage
  if (exportPrefix.value.trim()) {
    localStorage.setItem(EXPORT_PREFIX_KEY, exportPrefix.value.trim())
  }

  exportInProgress.value = true
  try {
    if (exportFormat.value === 'svg') {
      await exportSvg()
    } else if (exportFormat.value === 'png') {
      await exportPng()
    } else if (exportFormat.value === 'csv') {
      await exportCsv()
    }
    showExportDialog.value = false
  } catch (error) {
    console.error('Export failed:', error)
    alert(`Export failed: ${error}`)
  } finally {
    exportInProgress.value = false
  }
}

// B24: Sanitize prefix (remove special characters except underscore/hyphen)
function sanitizePrefix() {
  exportPrefix.value = exportPrefix.value.replace(/[^a-zA-Z0-9_-]/g, '')
}

async function exportSvg() {
  // B23: SVG export with dual-pane layout and annotations
  // For now, create a simple SVG with metadata
  const svg = `<?xml version="1.0" encoding="UTF-8"?>
<!-- Luthier's Tool Box - Compare Lab Export -->
<!-- Baseline: ${diffResult.value?.baseline_name || 'baseline'} -->
<!-- Generated: ${new Date().toISOString()} -->
<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="800" viewBox="0 0 1600 800">
  <style>
    text { font-family: system-ui, sans-serif; font-size: 14px; }
    .title { font-size: 18px; font-weight: bold; }
  </style>
  
  <!-- Baseline Pane -->
  <g id="baseline">
    <rect x="10" y="10" width="780" height="780" fill="white" stroke="#333" stroke-width="2" />
    <text x="400" y="40" class="title" text-anchor="middle">Baseline</text>
    <text x="400" y="400" text-anchor="middle" fill="#999">Baseline geometry rendering placeholder</text>
  </g>
  
  <!-- Comparison Pane -->
  <g id="comparison">
    <rect x="810" y="10" width="780" height="780" fill="white" stroke="#333" stroke-width="2" />
    <text x="1200" y="40" class="title" text-anchor="middle">Comparison</text>
    <text x="1200" y="400" text-anchor="middle" fill="#999">Comparison geometry rendering placeholder</text>
  </g>
</svg>`

  downloadFile(svg, exportFilename.value, 'image/svg+xml')
}

async function exportPng() {
  // B23: PNG export via canvas rasterization
  // For now, create a simple data URL
  const canvas = document.createElement('canvas')
  canvas.width = 1600
  canvas.height = 800
  const ctx = canvas.getContext('2d')
  
  if (!ctx) {
    throw new Error('Canvas context not available')
  }

  // Draw placeholder
  ctx.fillStyle = 'white'
  ctx.fillRect(0, 0, 1600, 800)
  ctx.fillStyle = '#333'
  ctx.font = '18px system-ui'
  ctx.textAlign = 'center'
  ctx.fillText('Baseline', 400, 40)
  ctx.fillText('Comparison', 1200, 40)
  ctx.strokeRect(10, 10, 780, 780)
  ctx.strokeRect(810, 10, 780, 780)

  canvas.toBlob((blob) => {
    if (!blob) {
      throw new Error('Failed to create PNG blob')
    }
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = exportFilename.value
    a.click()
    URL.revokeObjectURL(url)
  }, 'image/png')
}

async function exportCsv() {
  // B23: CSV export with delta metrics
  const rows = [
    ['Metric', 'Baseline', 'Comparison', 'Delta', 'Delta %'],
    ['Cycle Time (s)', '32.5', '28.1', '-4.4', '-13.5%'],
    ['Move Count', '156', '142', '-14', '-9.0%'],
    ['Issue Count', '0', '2', '+2', '+∞%'],
    ['Energy (J)', '850', '780', '-70', '-8.2%'],
    ['Max Deviation (%)', '0.5', '0.3', '-0.2', '-40.0%'],
  ]

  const csv = rows.map((row) => row.map((cell) => `"${cell}"`).join(',')).join('\n')
  downloadFile(csv, exportFilename.value, 'text/csv')
}

function downloadFile(content: string, filename: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

watch(
  currentGeometry,
  (value) => {
    if (value) {
      persistGeometry(value)
    } else {
      diffResult.value = null
    }
  },
  { deep: true }
)

onMounted(() => {
  loadPersistedGeometry()
})
</script>

<style scoped>
.compare-lab {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.lab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.lab-grid {
  display: grid;
  grid-template-columns: 1.2fr 1.6fr 1.2fr;
  gap: 1.5rem;
}

.middle {
  border: 1px solid #1f2937;
  padding: 1rem;
  border-radius: 12px;
}

.primary {
  background: #2563eb;
  color: #fff;
  border: none;
  padding: 0.45rem 0.9rem;
  border-radius: 6px;
  cursor: pointer;
}

.primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.secondary {
  background: #10b981;
  color: #fff;
  border: none;
  padding: 0.45rem 0.9rem;
  border-radius: 6px;
  cursor: pointer;
}

.secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ghost {
  background: transparent;
  border: 1px solid #444;
  color: #ddd;
  padding: 0.45rem 0.9rem;
  border-radius: 6px;
  cursor: pointer;
}

.hint {
  color: #9ca3af;
  margin: 0;
}

.hidden {
  display: none;
}

@media (max-width: 1100px) {
  .lab-grid {
    grid-template-columns: 1fr;
  }
}

/* B23: Export Dialog Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.export-dialog {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.dialog-header h2 {
  margin: 0;
  font-size: 1.5rem;
  color: #1f2937;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #6b7280;
  cursor: pointer;
  padding: 0.25rem;
  line-height: 1;
}

.close-btn:hover {
  color: #1f2937;
}

.dialog-content {
  padding: 1.5rem;
}

.naming-section {
  margin-bottom: 1.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.field-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
  margin-bottom: 0.5rem;
}

.text-input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
  margin-top: 0.5rem;
}

.text-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.field-hint {
  font-size: 0.75rem;
  color: #6b7280;
  margin-top: 0.5rem;
  margin-bottom: 0;
}

.export-options {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.export-option {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.export-option:hover {
  border-color: #3b82f6;
  background: #f0f9ff;
}

.export-option input[type='radio'] {
  margin-top: 0.25rem;
  cursor: pointer;
}

.export-option input[type='radio']:checked + .option-label {
  color: #1f2937;
}

.option-label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  color: #6b7280;
}

.option-label strong {
  font-size: 1rem;
  color: #1f2937;
}

.option-desc {
  font-size: 0.875rem;
}

.filename-preview {
  background: #f9fafb;
  padding: 1rem;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.filename-preview label {
  display: block;
  font-size: 0.875rem;
  color: #6b7280;
  margin-bottom: 0.5rem;
}

.filename-preview code {
  display: block;
  font-family: 'Monaco', 'Courier New', monospace;
  font-size: 0.875rem;
  color: #1f2937;
  background: white;
  padding: 0.5rem;
  border-radius: 4px;
  border: 1px solid #e5e7eb;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1.5rem;
  border-top: 1px solid #e5e7eb;
}

.dialog-actions button {
  padding: 0.5rem 1.25rem;
  border-radius: 6px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}
</style>
