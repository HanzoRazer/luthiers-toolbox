<script setup lang="ts">
/**
 * @deprecated Use InlayWorkspaceShell at /art-studio/inlay-workspace (Stage 2 uses ArtStudioInlay).
 * InlayDesignerView - Fretboard Inlay Pattern Designer
 * Connected to API endpoints:
 *   GET  /api/art-studio/inlay/presets
 *   GET  /api/art-studio/inlay/presets/{preset_name}
 *   GET  /api/art-studio/inlay/pattern-types
 *   POST /api/art-studio/inlay/preview
 *   POST /api/art-studio/inlay/export-dxf
 */
import { ref, computed, onMounted, watch } from 'vue'

// API base
const API_BASE = '/api/art-studio/inlay'

// Pattern types
interface PatternType {
  value: string
  label: string
}

interface PresetInfo {
  name: string
  description: string
  pattern_type: string
  fret_count: number
}

interface InlayShape {
  fret_number: number
  x_mm: number
  y_mm: number
  width_mm: number
  height_mm: number
  pattern_type: string
  is_double: boolean
}

interface InlayResult {
  shapes: InlayShape[]
  total_shapes: number
  pattern_type: string
  pocket_depth_mm: number
  bounds_mm: { min_x: number; max_x: number; min_y: number; max_y: number }
}

// Form state
const patternType = ref('dot')
const scaleLength = ref(648)
const markerDiameter = ref(6.0)
const blockWidth = ref(40.0)
const blockHeight = ref(8.0)
const pocketDepth = ref(1.5)
const doubleAt12 = ref(true)
const includeSideDots = ref(false)
const selectedFrets = ref([3, 5, 7, 9, 12, 15, 17, 19, 21, 24])
const dxfVersion = ref('R12')

// Data from API
const patternTypes = ref<string[]>([])
const presets = ref<PresetInfo[]>([])
const dxfVersions = ref<string[]>(['R12'])
const previewSvg = ref('')
const result = ref<InlayResult | null>(null)

// UI state
const selectedPreset = ref('')
const isLoading = ref(false)
const isExporting = ref(false)
const error = ref('')

// Standard fret positions for selection
const availableFrets = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 24]

// Computed
const hasPreview = computed(() => previewSvg.value.length > 0)
const isBlockType = computed(() => patternType.value === 'block' || patternType.value === 'parallelogram')

// Pattern type display names
const patternLabels: Record<string, string> = {
  dot: 'Dot',
  diamond: 'Diamond',
  block: 'Block',
  parallelogram: 'Trapezoid',
  split_block: 'Split Block',
  crown: 'Crown',
  snowflake: 'Snowflake',
  custom: 'Custom',
}

// Load initial data
onMounted(async () => {
  await Promise.all([
    loadPatternTypes(),
    loadPresets(),
    loadDxfVersions(),
  ])
})

// Watch for preset changes
watch(selectedPreset, async (presetName) => {
  if (presetName) {
    await loadPreset(presetName)
  }
})

// API calls
async function loadPatternTypes() {
  try {
    const response = await fetch(`${API_BASE}/pattern-types`)
    if (response.ok) {
      patternTypes.value = await response.json()
    }
  } catch (e) {
    console.error('Failed to load pattern types:', e)
  }
}

async function loadPresets() {
  try {
    const response = await fetch(`${API_BASE}/presets`)
    if (response.ok) {
      presets.value = await response.json()
    }
  } catch (e) {
    console.error('Failed to load presets:', e)
  }
}

async function loadDxfVersions() {
  try {
    const response = await fetch(`${API_BASE}/dxf-versions`)
    if (response.ok) {
      dxfVersions.value = await response.json()
    }
  } catch (e) {
    console.error('Failed to load DXF versions:', e)
  }
}

async function loadPreset(presetName: string) {
  try {
    const response = await fetch(`${API_BASE}/presets/${presetName}`)
    if (response.ok) {
      const preset = await response.json()
      patternType.value = preset.pattern_type
      selectedFrets.value = preset.fret_positions
      doubleAt12.value = preset.double_at_12
      markerDiameter.value = preset.marker_diameter_mm
      blockWidth.value = preset.block_width_mm
      blockHeight.value = preset.block_height_mm
      scaleLength.value = preset.scale_length_mm
      pocketDepth.value = preset.pocket_depth_mm
      includeSideDots.value = preset.include_side_dots

      // Auto-generate preview
      await generatePreview()
    }
  } catch (e) {
    console.error('Failed to load preset:', e)
  }
}

async function generatePreview() {
  isLoading.value = true
  error.value = ''

  try {
    const response = await fetch(`${API_BASE}/preview`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pattern_type: patternType.value,
        fret_positions: selectedFrets.value,
        double_at_12: doubleAt12.value,
        marker_diameter_mm: markerDiameter.value,
        block_width_mm: blockWidth.value,
        block_height_mm: blockHeight.value,
        scale_length_mm: scaleLength.value,
        pocket_depth_mm: pocketDepth.value,
        include_side_dots: includeSideDots.value,
      }),
    })

    if (!response.ok) {
      const err = await response.json()
      throw new Error(err.detail || 'Failed to generate preview')
    }

    const data = await response.json()
    result.value = data.result
    previewSvg.value = data.preview_svg || ''
  } catch (e: any) {
    error.value = e.message || 'Failed to generate preview'
  } finally {
    isLoading.value = false
  }
}

async function exportDxf() {
  isExporting.value = true
  error.value = ''

  try {
    const response = await fetch(`${API_BASE}/export-dxf`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pattern_type: patternType.value,
        fret_positions: selectedFrets.value,
        double_at_12: doubleAt12.value,
        marker_diameter_mm: markerDiameter.value,
        block_width_mm: blockWidth.value,
        block_height_mm: blockHeight.value,
        scale_length_mm: scaleLength.value,
        pocket_depth_mm: pocketDepth.value,
        include_side_dots: includeSideDots.value,
        dxf_version: dxfVersion.value,
      }),
    })

    if (!response.ok) {
      const err = await response.json()
      throw new Error(err.detail || 'Failed to export DXF')
    }

    // Download the file
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `inlay_${patternType.value}_${selectedFrets.value.length}frets.dxf`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  } catch (e: any) {
    error.value = e.message || 'Failed to export DXF'
  } finally {
    isExporting.value = false
  }
}

function toggleFret(fret: number) {
  const index = selectedFrets.value.indexOf(fret)
  if (index === -1) {
    selectedFrets.value = [...selectedFrets.value, fret].sort((a, b) => a - b)
  } else {
    selectedFrets.value = selectedFrets.value.filter(f => f !== fret)
  }
}

function selectStandardFrets() {
  selectedFrets.value = [3, 5, 7, 9, 12, 15, 17, 19, 21, 24]
}

function selectClassicalFrets() {
  selectedFrets.value = [5, 7, 9, 12]
}

function selectAllFrets() {
  selectedFrets.value = [...availableFrets]
}

function clearFrets() {
  selectedFrets.value = []
}
</script>

<template>
  <div class="inlay-designer-view">
    <header class="view-header">
      <h1>Inlay Designer</h1>
      <p class="subtitle">Design fretboard inlay patterns with precise positioning using 12-TET fret calculations</p>
    </header>

    <div v-if="error" class="error-banner">
      {{ error }}
      <button @click="error = ''" class="dismiss-btn">&times;</button>
    </div>

    <div class="content-grid">
      <!-- Preset Selection -->
      <section class="panel preset-panel">
        <h2>Presets</h2>
        <div class="preset-grid">
          <button
            v-for="preset in presets"
            :key="preset.name"
            class="preset-btn"
            :class="{ active: selectedPreset === preset.name }"
            @click="selectedPreset = preset.name"
          >
            <span class="preset-icon">
              {{ preset.pattern_type === 'dot' ? '●' : preset.pattern_type === 'diamond' ? '◆' : preset.pattern_type === 'block' ? '▬' : '◇' }}
            </span>
            <span class="preset-name">{{ preset.name }}</span>
            <span class="preset-desc">{{ preset.fret_count }} frets</span>
          </button>
        </div>
      </section>

      <!-- Parameters -->
      <section class="panel params-panel">
        <h2>Inlay Parameters</h2>
        <div class="param-group">
          <label>
            Pattern Type
            <select v-model="patternType">
              <option v-for="pt in patternTypes" :key="pt" :value="pt">
                {{ patternLabels[pt] || pt }}
              </option>
            </select>
          </label>

          <label>
            Scale Length (mm)
            <input v-model.number="scaleLength" type="number" step="1" min="400" max="900" />
          </label>

          <label v-if="!isBlockType">
            Marker Diameter (mm)
            <input v-model.number="markerDiameter" type="number" step="0.5" min="2" max="20" />
          </label>

          <template v-if="isBlockType">
            <label>
              Block Width (mm)
              <input v-model.number="blockWidth" type="number" step="1" min="10" max="60" />
            </label>
            <label>
              Block Height (mm)
              <input v-model.number="blockHeight" type="number" step="0.5" min="4" max="20" />
            </label>
          </template>

          <label>
            Pocket Depth (mm)
            <input v-model.number="pocketDepth" type="number" step="0.1" min="0.5" max="5" />
          </label>

          <div class="checkbox-group">
            <label class="checkbox">
              <input type="checkbox" v-model="doubleAt12" />
              Double marker at 12th fret
            </label>
            <label class="checkbox">
              <input type="checkbox" v-model="includeSideDots" />
              Include side dot positions
            </label>
          </div>
        </div>

        <button
          class="btn-primary"
          :disabled="isLoading || selectedFrets.length === 0"
          @click="generatePreview"
        >
          {{ isLoading ? 'Generating...' : 'Generate Preview' }}
        </button>
      </section>

      <!-- Fret Selection -->
      <section class="panel frets-panel">
        <h2>Fret Positions</h2>
        <div class="fret-presets">
          <button @click="selectStandardFrets" class="fret-preset-btn">Standard</button>
          <button @click="selectClassicalFrets" class="fret-preset-btn">Classical</button>
          <button @click="selectAllFrets" class="fret-preset-btn">All</button>
          <button @click="clearFrets" class="fret-preset-btn">Clear</button>
        </div>
        <div class="fret-grid">
          <button
            v-for="fret in availableFrets"
            :key="fret"
            class="fret-btn"
            :class="{ selected: selectedFrets.includes(fret), octave: fret === 12 }"
            @click="toggleFret(fret)"
          >
            {{ fret }}
          </button>
        </div>
        <p class="fret-count">{{ selectedFrets.length }} frets selected</p>
      </section>

      <!-- Preview -->
      <section class="panel preview-panel">
        <h2>Preview</h2>
        <div class="preview-container">
          <div v-if="!hasPreview" class="preview-placeholder">
            <span class="icon">💎</span>
            <p>Configure parameters and click Generate Preview</p>
          </div>
          <div v-else class="svg-preview" v-html="previewSvg"></div>
        </div>

        <div v-if="result" class="result-stats">
          <div class="stat">
            <span class="stat-value">{{ result.total_shapes }}</span>
            <span class="stat-label">Inlays</span>
          </div>
          <div class="stat">
            <span class="stat-value">{{ patternLabels[result.pattern_type] || result.pattern_type }}</span>
            <span class="stat-label">Pattern</span>
          </div>
          <div class="stat">
            <span class="stat-value">{{ result.pocket_depth_mm }}</span>
            <span class="stat-label">Depth (mm)</span>
          </div>
          <div class="stat">
            <span class="stat-value">{{ (result.bounds_mm.max_x - result.bounds_mm.min_x).toFixed(1) }}</span>
            <span class="stat-label">Span (mm)</span>
          </div>
        </div>

        <div class="export-section">
          <label class="export-version">
            DXF Version
            <select v-model="dxfVersion">
              <option v-for="v in dxfVersions" :key="v" :value="v">{{ v }}</option>
            </select>
          </label>
          <button
            class="btn-export"
            :disabled="!hasPreview || isExporting"
            @click="exportDxf"
          >
            {{ isExporting ? 'Exporting...' : 'Export DXF' }}
          </button>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.inlay-designer-view {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.view-header {
  margin-bottom: 2rem;
}

.view-header h1 {
  font-size: 1.75rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #64748b;
}

.error-banner {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  margin-bottom: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dismiss-btn {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  color: #dc2626;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.panel {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  padding: 1.5rem;
}

.panel h2 {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #1e293b;
}

/* Presets */
.preset-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
}

.preset-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  background: #fff;
  cursor: pointer;
  transition: all 0.2s;
}

.preset-btn:hover {
  border-color: #2563eb;
  background: #f8fafc;
}

.preset-btn.active {
  border-color: #2563eb;
  background: #eff6ff;
}

.preset-icon {
  font-size: 1.5rem;
  margin-bottom: 0.25rem;
}

.preset-name {
  font-weight: 600;
  font-size: 0.875rem;
  color: #1e293b;
}

.preset-desc {
  font-size: 0.75rem;
  color: #64748b;
}

/* Parameters */
.param-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.param-group label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.875rem;
  color: #475569;
}

.param-group input,
.param-group select {
  padding: 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.75rem;
  background: #f8fafc;
  border-radius: 0.375rem;
}

.checkbox {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  flex-direction: row;
}

.checkbox input {
  width: auto;
}

/* Fret selection */
.fret-presets {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.fret-preset-btn {
  padding: 0.375rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  background: #fff;
  cursor: pointer;
  font-size: 0.75rem;
  transition: all 0.2s;
}

.fret-preset-btn:hover {
  border-color: #2563eb;
  background: #f8fafc;
}

.fret-grid {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 0.375rem;
  margin-bottom: 0.75rem;
}

.fret-btn {
  aspect-ratio: 1;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  background: #fff;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.2s;
}

.fret-btn:hover {
  border-color: #2563eb;
}

.fret-btn.selected {
  background: #2563eb;
  color: white;
  border-color: #2563eb;
}

.fret-btn.octave {
  font-weight: 700;
}

.fret-btn.octave.selected {
  background: #7c3aed;
  border-color: #7c3aed;
}

.fret-count {
  font-size: 0.875rem;
  color: #64748b;
  text-align: center;
}

/* Preview */
.preview-container {
  background: #f8fafc;
  border-radius: 0.375rem;
  min-height: 150px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
  overflow: hidden;
}

.preview-placeholder {
  text-align: center;
  color: #94a3b8;
  padding: 2rem;
}

.preview-placeholder .icon {
  font-size: 2rem;
  display: block;
  margin-bottom: 0.5rem;
}

.svg-preview {
  width: 100%;
  padding: 1rem;
}

.svg-preview :deep(svg) {
  width: 100%;
  height: auto;
}

.result-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.stat {
  text-align: center;
  padding: 0.75rem;
  background: #f8fafc;
  border-radius: 0.375rem;
}

.stat-value {
  display: block;
  font-size: 1.25rem;
  font-weight: 700;
  color: #1e293b;
}

.stat-label {
  font-size: 0.75rem;
  color: #64748b;
}

.export-section {
  display: flex;
  gap: 1rem;
  align-items: flex-end;
}

.export-version {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.875rem;
  color: #475569;
}

.export-version select {
  padding: 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
}

/* Buttons */
.btn-primary,
.btn-export {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  width: 100%;
  background: #2563eb;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-export {
  background: #10b981;
  color: white;
  flex-shrink: 0;
}

.btn-export:hover:not(:disabled) {
  background: #059669;
}

.btn-export:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
