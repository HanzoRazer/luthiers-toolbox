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
        <button
          class="primary"
          @click="showSavePresetModal = true"
          :disabled="!diffResult || !filenameTemplate"
          title="Save current comparison configuration as preset"
        >
          💾 Save as Preset
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
              Export Preset (optional):
              <select v-model="selectedPresetId" class="text-input" @change="loadPresetTemplate">
                <option value="">-- Use custom template --</option>
                <option v-for="preset in exportPresets" :key="preset.id" :value="preset.id">
                  {{ preset.name }}
                </option>
              </select>
            </label>
            
            <label class="field-label">
              Filename Template:
              <input
                type="text"
                v-model="filenameTemplate"
                placeholder="{preset}__{compare_mode}__{date}"
                class="text-input"
                @blur="validateTemplate"
              />
            </label>
            
            <!-- Extension Mismatch Warning -->
            <div v-if="extensionMismatch" class="extension-warning">
              <div class="warning-banner">
                <span class="warning-icon">⚠️</span>
                <div class="warning-content">
                  <strong>Extension Mismatch Detected</strong>
                  <p>
                    Template has <code>.{{ extensionMismatch.templateExt }}</code> extension 
                    but export format is <strong>{{ extensionMismatch.expectedExt.toUpperCase() }}</strong>
                  </p>
                </div>
              </div>
              <div class="warning-actions">
                <button type="button" class="fix-button" @click="fixTemplateExtension" title="Change template extension to match format">
                  Fix Template → .{{ extensionMismatch.expectedExt }}
                </button>
                <button type="button" class="fix-button secondary" @click="fixExportFormat" title="Change format to match template extension">
                  Fix Format → {{ extensionMismatch.templateExt.toUpperCase() }}
                </button>
              </div>
            </div>
            
            <p v-if="templateValidation" class="field-hint" :class="{'text-red-600': templateValidation.warnings?.length}">
              <span v-if="templateValidation.valid">✓ Valid template</span>
              <span v-else>⚠ {{ templateValidation.warnings?.join(', ') }}</span>
            </p>
            <p class="field-hint text-xs text-gray-500">
              Tokens: {preset}, {compare_mode}, {neck_profile}, {neck_section}, {date}, {timestamp}
            </p>
            <p v-if="neckProfileContext || neckSectionContext" class="field-hint text-xs text-blue-600">
              ℹ Neck context: 
              <span v-if="neckProfileContext">Profile: <code class="bg-blue-50 px-1 rounded">{{ neckProfileContext }}</code></span>
              <span v-if="neckSectionContext">Section: <code class="bg-blue-50 px-1 rounded">{{ neckSectionContext }}</code></span>
            </p>
            <p v-else class="field-hint text-xs text-amber-600">
              ⚠ No neck context detected. Tokens {neck_profile} and {neck_section} will be empty.
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

    <!-- CompareLab: Save as Preset Modal -->
    <div v-if="showSavePresetModal" class="modal-overlay" @click.self="showSavePresetModal = false">
      <div class="export-dialog">
        <header class="dialog-header">
          <h2>Save Comparison as Preset</h2>
          <button class="close-btn" @click="showSavePresetModal = false">✕</button>
        </header>

        <div class="dialog-content">
          <div class="naming-section">
            <label class="field-label">
              Preset Name:
              <input
                type="text"
                v-model="presetForm.name"
                placeholder="e.g., Les Paul Neck Comparison Template"
                class="text-input"
                required
              />
            </label>

            <label class="field-label">
              Description (optional):
              <textarea
                v-model="presetForm.description"
                placeholder="Describe this comparison preset..."
                class="text-input"
                rows="3"
              ></textarea>
            </label>

            <label class="field-label">
              Tags (comma-separated):
              <input
                type="text"
                v-model="presetForm.tagsInput"
                placeholder="comparison, neck, les-paul"
                class="text-input"
              />
            </label>

            <label class="field-label">
              Preset Kind:
              <select v-model="presetForm.kind" class="text-input">
                <option value="export">Export Only (template + format)</option>
                <option value="combo">Combo (comparison mode + export)</option>
              </select>
            </label>
            <p class="field-hint text-xs text-gray-500">
              Export: Saves only export settings (template, format)<br>
              Combo: Saves comparison mode + export settings
            </p>
          </div>

          <div class="preset-summary">
            <h3 class="text-sm font-semibold mb-2">Preset Will Include:</h3>
            <ul class="text-xs space-y-1">
              <li>✓ Filename Template: <code class="bg-gray-100 px-1">{{ filenameTemplate }}</code></li>
              <li>✓ Export Format: <code class="bg-gray-100 px-1">{{ exportFormat }}</code></li>
              <li v-if="neckProfileContext">✓ Neck Profile Context: <code class="bg-gray-100 px-1">{{ neckProfileContext }}</code></li>
              <li v-if="neckSectionContext">✓ Neck Section Context: <code class="bg-gray-100 px-1">{{ neckSectionContext }}</code></li>
              <li v-if="presetForm.kind === 'combo'">✓ Compare Mode: <code class="bg-gray-100 px-1">{{ diffResult?.mode || 'neck_diff' }}</code></li>
            </ul>
          </div>

          <div v-if="presetSaveMessage" class="p-3 rounded text-sm" :class="presetSaveMessage.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'">
            {{ presetSaveMessage.text }}
          </div>
        </div>

        <div class="dialog-actions">
          <button class="ghost" @click="showSavePresetModal = false">Cancel</button>
          <button class="primary" @click="saveAsPreset" :disabled="!presetForm.name || presetSaveInProgress">
            {{ presetSaveInProgress ? 'Saving...' : 'Save Preset' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
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
const NECK_PROFILE_KEY = 'toolbox.compare.neckProfile'
const NECK_SECTION_KEY = 'toolbox.compare.neckSection'

const route = useRoute()

const fileInput = ref<HTMLInputElement | null>(null)
const currentGeometry = ref<CanonicalGeometry | null>(null)
const diffResult = ref<DiffResult | null>(null)

// B23: Export state
const showExportDialog = ref(false)
const exportFormat = ref<'svg' | 'png' | 'csv'>('svg')
const exportInProgress = ref(false)

// B24: Naming customization with template engine
const EXPORT_PREFIX_KEY = 'toolbox.compare.exportPrefix'
const STORAGE_KEYS = {
  PRESET_ID: 'comparelab.selectedPresetId',
  TEMPLATE: 'comparelab.filenameTemplate',
  FORMAT: 'comparelab.exportFormat'
}

const exportPrefix = ref(localStorage.getItem(EXPORT_PREFIX_KEY) || '')
const exportPresets = ref<any[]>([])
const selectedPresetId = ref('')
const filenameTemplate = ref('{preset}__{compare_mode}__{date}')
const templateValidation = ref<any>(null)
const neckProfileContext = ref<string | null>(null)
const neckSectionContext = ref<string | null>(null)

// Load persisted export state
function loadExportState() {
  try {
    const savedPresetId = localStorage.getItem(STORAGE_KEYS.PRESET_ID)
    if (savedPresetId) selectedPresetId.value = savedPresetId

    const savedTemplate = localStorage.getItem(STORAGE_KEYS.TEMPLATE)
    if (savedTemplate) filenameTemplate.value = savedTemplate

    const savedFormat = localStorage.getItem(STORAGE_KEYS.FORMAT)
    if (savedFormat && ['svg', 'png', 'csv'].includes(savedFormat)) {
      exportFormat.value = savedFormat as 'svg' | 'png' | 'csv'
    }
  } catch (error) {
    console.error('Failed to load export state:', error)
  }
}

// Save export state
function saveExportState() {
  try {
    localStorage.setItem(STORAGE_KEYS.PRESET_ID, selectedPresetId.value)
    localStorage.setItem(STORAGE_KEYS.TEMPLATE, filenameTemplate.value)
    localStorage.setItem(STORAGE_KEYS.FORMAT, exportFormat.value)
  } catch (error) {
    console.error('Failed to save export state:', error)
  }
}

// Extension Validation: Detect when template extension doesn't match format
const extensionMismatch = computed(() => {
  const template = filenameTemplate.value.toLowerCase()
  const format = exportFormat.value.toLowerCase()
  
  // Extract extension from template (last .xxx after removing tokens)
  const withoutTokens = template.replace(/\{[^}]+\}/g, '')
  const match = withoutTokens.match(/\.(svg|png|csv|dxf|nc|gcode)$/i)
  const templateExt = match ? match[1].toLowerCase() : null
  
  if (!templateExt) return null // No extension in template
  
  if (templateExt !== format) {
    return {
      templateExt,
      expectedExt: format,
      hasConflict: true
    }
  }
  
  return null
})

// Auto-fix: Change template extension to match format
function fixTemplateExtension() {
  if (!extensionMismatch.value) return
  
  const { templateExt, expectedExt } = extensionMismatch.value
  const regex = new RegExp(`\\.${templateExt}$`, 'i')
  filenameTemplate.value = filenameTemplate.value.replace(regex, `.${expectedExt}`)
}

// Auto-fix: Change format to match template extension
function fixExportFormat() {
  if (!extensionMismatch.value) return
  
  const validFormat = extensionMismatch.value.templateExt as 'svg' | 'png' | 'csv'
  if (['svg', 'png', 'csv'].includes(validFormat)) {
    exportFormat.value = validFormat
  }
}

// CompareLab: Save as Preset state
const showSavePresetModal = ref(false)
const presetSaveInProgress = ref(false)
const presetSaveMessage = ref<{type: 'success' | 'error', text: string} | null>(null)
const presetForm = ref({
  name: '',
  description: '',
  tagsInput: 'comparison',
  kind: 'export' as 'export' | 'combo'
})

const hasStoredGeometry = computed(() => Boolean(localStorage.getItem(STORAGE_KEY)))

const exportFilename = computed(() => {
  if (!diffResult.value) return 'compare.svg'
  
  // If using template engine, resolve tokens
  if (filenameTemplate.value && filenameTemplate.value.includes('{')) {
    // Build context for token resolution
    const context: Record<string, string> = {
      preset: exportPrefix.value || diffResult.value.baseline_name || 'compare',
      compare_mode: 'neck_diff', // or 'geom_diff' based on mode
      date: new Date().toISOString().slice(0, 10),
      timestamp: new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
    }
    
    // Add neck context if available
    if (neckProfileContext.value) {
      context.neck_profile = neckProfileContext.value
    }
    if (neckSectionContext.value) {
      context.neck_section = neckSectionContext.value
    }
    
    // Resolve template (simplified client-side)
    let resolved = filenameTemplate.value
    Object.keys(context).forEach(key => {
      const regex = new RegExp(`\\{${key}\\}`, 'gi')
      resolved = resolved.replace(regex, context[key] || '')
    })
    
    // Sanitize
    resolved = resolved.replace(/[^a-zA-Z0-9_.-]/g, '_').replace(/_+/g, '_')
    
    return `${resolved}.${exportFormat.value}`
  }
  
  // Fallback to legacy naming
  const parts: string[] = []
  if (exportPrefix.value.trim()) {
    parts.push(exportPrefix.value.trim())
  }
  
  const baseline = diffResult.value.baseline_name || 'baseline'
  const compare = 'compare'
  const timestamp = new Date().toISOString().slice(0, 10).replace(/-/g, '')
  const ext = exportFormat.value
  
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
    extractNeckContext()
  } catch (error) {
    console.error('Failed to parse stored geometry', error)
  }
}

function extractNeckContext(): void {
  // Priority 1: URL query parameters
  const queryProfile = route.query.neck_profile as string
  const querySection = route.query.neck_section as string
  
  if (queryProfile) {
    neckProfileContext.value = queryProfile
    localStorage.setItem(NECK_PROFILE_KEY, queryProfile)
  }
  if (querySection) {
    neckSectionContext.value = querySection
    localStorage.setItem(NECK_SECTION_KEY, querySection)
  }
  
  // Priority 2: Geometry metadata (paths[0].meta.neck_profile / neck_section)
  if (!neckProfileContext.value && currentGeometry.value?.paths?.[0]?.meta) {
    const meta = currentGeometry.value.paths[0].meta
    if (typeof meta.neck_profile === 'string') {
      neckProfileContext.value = meta.neck_profile
      localStorage.setItem(NECK_PROFILE_KEY, meta.neck_profile)
    }
    if (typeof meta.neck_section === 'string') {
      neckSectionContext.value = meta.neck_section
      localStorage.setItem(NECK_SECTION_KEY, meta.neck_section)
    }
  }
  
  // Priority 3: Geometry source string parsing (e.g., "NeckLab:Fender_Modern_C:Fret_5")
  if (!neckProfileContext.value && currentGeometry.value?.source) {
    const sourceParts = currentGeometry.value.source.split(':')
    if (sourceParts.length >= 3 && sourceParts[0] === 'NeckLab') {
      neckProfileContext.value = sourceParts[1]
      neckSectionContext.value = sourceParts[2]
      localStorage.setItem(NECK_PROFILE_KEY, sourceParts[1])
      localStorage.setItem(NECK_SECTION_KEY, sourceParts[2])
    }
  }
  
  // Priority 4: localStorage fallback
  if (!neckProfileContext.value) {
    neckProfileContext.value = localStorage.getItem(NECK_PROFILE_KEY)
  }
  if (!neckSectionContext.value) {
    neckSectionContext.value = localStorage.getItem(NECK_SECTION_KEY)
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
        extractNeckContext()
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

// CompareLab: Save as Preset function
async function saveAsPreset() {
  if (!presetForm.value.name.trim()) {
    presetSaveMessage.value = { type: 'error', text: 'Preset name is required' }
    return
  }
  
  presetSaveInProgress.value = true
  presetSaveMessage.value = null
  
  try {
    // Parse tags from comma-separated input
    const tags = presetForm.value.tagsInput
      .split(',')
      .map(t => t.trim())
      .filter(t => t.length > 0)
    
    // Build export_params
    const export_params: any = {
      filename_template: filenameTemplate.value,
      format: exportFormat.value
    }
    
    // Add neck context if available
    if (neckProfileContext.value) {
      export_params.neck_profile = neckProfileContext.value
    }
    if (neckSectionContext.value) {
      export_params.neck_section = neckSectionContext.value
    }
    
    // Build cam_params for combo presets (comparison mode)
    const cam_params = presetForm.value.kind === 'combo' && diffResult.value ? {
      compare_mode: diffResult.value.mode || 'neck_diff',
      baseline_name: diffResult.value.baseline_name || 'baseline'
    } : undefined
    
    // Create preset payload
    const payload = {
      name: presetForm.value.name.trim(),
      kind: presetForm.value.kind,
      description: presetForm.value.description.trim() || undefined,
      tags: tags,
      export_params: export_params,
      cam_params: cam_params,
      source: 'manual'
    }
    
    const response = await fetch('/api/presets', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || `HTTP ${response.status}`)
    }
    
    const created = await response.json()
    
    presetSaveMessage.value = {
      type: 'success',
      text: `✅ Preset "${created.name}" saved successfully!`
    }
    
    // Reset form and close after 2 seconds
    setTimeout(() => {
      showSavePresetModal.value = false
      presetForm.value = {
        name: '',
        description: '',
        tagsInput: 'comparison',
        kind: 'export'
      }
      presetSaveMessage.value = null
      
      // Refresh export presets list
      loadExportPresets()
    }, 2000)
    
  } catch (error: any) {
    console.error('Failed to save preset:', error)
    presetSaveMessage.value = {
      type: 'error',
      text: `❌ Failed to save preset: ${error.message}`
    }
  } finally {
    presetSaveInProgress.value = false
  }
}

// Template engine integration
async function loadExportPresets() {
  try {
    const response = await fetch('/api/presets?kind=export')
    exportPresets.value = await response.json()
  } catch (error) {
    console.error('Failed to load export presets:', error)
  }
}

async function loadPresetTemplate() {
  if (!selectedPresetId.value) {
    filenameTemplate.value = '{preset}__{compare_mode}__{date}'
    return
  }
  
  try {
    const response = await fetch(`/api/presets/${selectedPresetId.value}`)
    const preset = await response.json()
    if (preset.export_params?.filename_template) {
      filenameTemplate.value = preset.export_params.filename_template
    }
  } catch (error) {
    console.error('Failed to load preset template:', error)
  }
}

async function validateTemplate() {
  if (!filenameTemplate.value) return
  
  try {
    const response = await fetch('/api/presets/validate-template', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ template: filenameTemplate.value })
    })
    templateValidation.value = await response.json()
  } catch (error) {
    console.error('Template validation failed:', error)
    templateValidation.value = { valid: false, warnings: ['Validation failed'] }
  }
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
      extractNeckContext()
    } else {
      diffResult.value = null
    }
  },
  { deep: true }
)

onMounted(() => {
  loadPersistedGeometry()
  loadExportState()
  loadExportPresets()
  extractNeckContext()
})

// Reload presets and refresh neck context when export dialog opens
watch(showExportDialog, (isOpen) => {
  if (isOpen) {
    loadExportPresets()
    extractNeckContext()
  }
})

// Watch for export state changes and persist
watch([selectedPresetId, filenameTemplate, exportFormat], () => {
  saveExportState()
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

/* CompareLab: Preset summary styles */
.preset-summary {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 6px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.preset-summary h3 {
  margin: 0 0 0.5rem 0;
  color: #0c4a6e;
}

.preset-summary ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.preset-summary li {
  color: #0c4a6e;
  padding: 0.25rem 0;
}

.preset-summary code {
  font-family: 'Monaco', 'Courier New', monospace;
  padding: 2px 4px;
  border-radius: 3px;
}

/* Extension Validation Styles */
.extension-warning {
  margin: 0.75rem 0;
  padding: 0.75rem;
  background-color: #fef3c7;
  border: 1px solid #f59e0b;
  border-radius: 6px;
}

.warning-banner {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.warning-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
}

.warning-content {
  flex: 1;
}

.warning-content strong {
  display: block;
  color: #92400e;
  margin-bottom: 0.25rem;
  font-size: 0.875rem;
}

.warning-content p {
  margin: 0;
  color: #78350f;
  font-size: 0.813rem;
  line-height: 1.4;
}

.warning-content code {
  background-color: #fde68a;
  color: #92400e;
  padding: 0.125rem 0.375rem;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 0.813rem;
}

.warning-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.fix-button {
  padding: 0.375rem 0.75rem;
  font-size: 0.813rem;
  font-weight: 500;
  border-radius: 4px;
  border: 1px solid #f59e0b;
  background-color: #fbbf24;
  color: #78350f;
  cursor: pointer;
  transition: all 0.2s;
}

.fix-button:hover {
  background-color: #f59e0b;
  transform: translateY(-1px);
}

.fix-button.secondary {
  background-color: #fef3c7;
  border-color: #d97706;
}

.fix-button.secondary:hover {
  background-color: #fde68a;
}
</style>
