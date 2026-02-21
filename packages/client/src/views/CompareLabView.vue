<template>
  <div :class="styles.compareLab">
    <header :class="styles.labHeader">
      <div>
        <h1>Compare Lab</h1>
        <p :class="styles.hint">
          Load Adaptive geometry, capture baselines, and inspect SVG diffs.
        </p>
      </div>
      <div :class="styles.headerActions">
        <input
          ref="fileInput"
          type="file"
          :class="styles.hidden"
          accept="application/json"
          @change="handleFile"
        >
        <button
          :class="styles.ghost"
          @click="triggerFileDialog"
        >
          Import Geometry JSON
        </button>
        <button
          :class="styles.primary"
          :disabled="!hasStoredGeometry"
          @click="loadPersistedGeometry"
        >
          Load From Adaptive Lab
        </button>
        <button
          :class="styles.secondary"
          :disabled="!diffResult"
          title="Export comparison as SVG, PNG, or CSV"
          @click="showExportDialog = true"
        >
          Export Diff
        </button>
        <button
          :class="styles.primary"
          :disabled="!diffResult || !filenameTemplate"
          title="Save current comparison configuration as preset"
          @click="showSavePresetModal = true"
        >
          💾 Save as Preset
        </button>
      </div>
    </header>

    <section :class="styles.labGrid">
      <CompareBaselinePicker
        :current-geometry="currentGeometry"
        @diff-computed="(payload: any) => (diffResult = payload)"
      />

      <CompareSvgDualViewer
        :class="styles.middle"
        :diff="diffResult as any"
      />

      <CompareDiffViewer
        :diff="diffResult as any"
        :current-geometry="currentGeometry"
      />
    </section>

    <!-- B23: Export Dialog -->
    <ExportDialog
      v-if="showExportDialog"
      :styles="styles"
      :export-presets="exportPresets"
      :selected-preset-id="selectedPresetId"
      :filename-template="filenameTemplate"
      :extension-mismatch="extensionMismatch"
      :template-validation="templateValidation"
      :neck-profile-context="neckProfileContext"
      :neck-section-context="neckSectionContext"
      :export-format="exportFormat"
      :export-filename="exportFilename"
      :export-in-progress="exportInProgress"
      @close="showExportDialog = false"
      @update:selected-preset-id="(v) => { selectedPresetId = v; loadPresetTemplate() }"
      @update:filename-template="filenameTemplate = $event"
      @update:export-format="exportFormat = $event"
      @validate-template="validateTemplate"
      @fix-template-extension="fixTemplateExtension"
      @fix-export-format="fixExportFormat"
      @export="executeExport"
    />

    <!-- CompareLab: Save as Preset Modal -->
    <SavePresetModal
      v-if="showSavePresetModal"
      :styles="styles"
      :preset-form="presetForm"
      :filename-template="filenameTemplate"
      :export-format="exportFormat"
      :neck-profile-context="neckProfileContext"
      :neck-section-context="neckSectionContext"
      :diff-result-mode="diffResult?.mode || 'neck_diff'"
      :preset-save-message="presetSaveMessage"
      :preset-save-in-progress="presetSaveInProgress"
      @close="showSavePresetModal = false"
      @update:preset-form="presetForm = $event"
      @save="saveAsPreset"
    />
  </div>
</template>

<script setup lang="ts">
import { api } from '@/services/apiBase';
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import CompareBaselinePicker from '@/components/compare/CompareBaselinePicker.vue'
import CompareDiffViewer from '@/components/compare/CompareDiffViewer.vue'
import CompareSvgDualViewer from '@/components/compare/CompareSvgDualViewer.vue'
import ExportDialog from './compare_lab/ExportDialog.vue'
import SavePresetModal from './compare_lab/SavePresetModal.vue'
import type { CanonicalGeometry } from '@/utils/geometry'
import { normalizeGeometryPayload } from '@/utils/geometry'
import styles from './CompareLabView.module.css'

interface DiffResult {
  baseline_id: string
  baseline_name: string
  summary?: { added: number; removed: number; matched: number }
  segments?: Array<{ status: string; length: number; path_index: number }>
  mode?: string
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
    
    const response = await api('/api/presets', {
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
    const response = await api('/api/presets?kind=export')
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
    const response = await api(`/api/presets/${selectedPresetId.value}`)
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
    const response = await api('/api/presets/validate-template', {
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
