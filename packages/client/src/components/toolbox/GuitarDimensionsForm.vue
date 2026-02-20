<template>
  <div class="guitar-dimensions-form">
    <div class="form-header">
      <h2>Guitar Body Dimensions</h2>
      <p class="description">
        Enter measurements for acoustic or electric guitar bodies. All dimensions stored in millimeters.
      </p>
    </div>

    <!-- Guitar Type Selection -->
    <GuitarTypeSelector
      v-model="selectedType"
      :guitar-types="guitarTypes"
    />

    <!-- Dimension Inputs -->
    <DimensionInputGrid
      v-model:dimensions="dimensions"
      :current-unit="currentUnit"
      @change="handleChange"
    />

    <!-- Presets -->
    <PresetSelector
      :presets="presets"
      @load="loadPreset"
    />

    <!-- Units Toggle -->
    <section class="form-section">
      <h3>Units</h3>
      <div class="button-group">
        <button
          :class="{ active: units === 'mm' }"
          @click="toggleUnits('mm')"
        >
          Millimeters (mm)
        </button>
        <button
          :class="{ active: units === 'inch' }"
          @click="toggleUnits('inch')"
        >
          Inches (in)
        </button>
      </div>
    </section>

    <!-- Actions -->
    <section class="form-section actions">
      <button
        class="btn-primary"
        :disabled="!hasValidDimensions || isExporting || isGenerating"
        @click="handleGenerateDXF"
      >
        {{ isExporting ? 'Generating...' : 'Generate Body Outline (DXF)' }}
      </button>
      <button
        class="btn-primary"
        :disabled="!hasValidDimensions || isExporting || isGenerating"
        @click="handleGenerateSVG"
      >
        {{ isExporting ? 'Generating...' : 'Generate Body Outline (SVG)' }}
      </button>
      <button
        class="btn-success"
        :disabled="!hasValidDimensions || isGenerating"
        @click="handleGenerateCAM"
      >
        {{ isGenerating ? 'Planning...' : 'Send to CAM (Generate Toolpath)' }}
      </button>
      <button
        class="btn-secondary"
        @click="handleExportJSON"
      >
        Save as JSON
      </button>
      <button
        class="btn-secondary"
        @click="handleExportCSV"
      >
        Export CSV
      </button>
      <button
        class="btn-secondary"
        @click="handleCopyToClipboard"
      >
        Copy to Clipboard
      </button>
      <button
        class="btn-danger"
        @click="clearAll"
      >
        Clear All
      </button>
    </section>

    <!-- CAM Results -->
    <CamResultsPanel
      :cam-results="camResults"
      :selected-post="selectedPost"
      :moves-preview="movesPreview"
      @download="handleDownloadGCode"
      @update:selected-post="selectedPost = $event as PostProcessor"
    />

    <!-- Status -->
    <div
      v-if="status"
      :class="['status-message', statusType]"
    >
      {{ status }}
    </div>

    <!-- Visual Preview -->
    <GuitarBodyPreview
      :dimensions="dimensions"
      :current-unit="currentUnit"
      :has-valid-dimensions="hasValidDimensions"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useGuitarDimensions } from './composables/useGuitarDimensions'
import { useGuitarExport } from './composables/useGuitarExport'
import { useGuitarCAM, type PostProcessor } from './composables/useGuitarCAM'
import {
  GuitarTypeSelector,
  PresetSelector,
  DimensionInputGrid,
  CamResultsPanel,
  GuitarBodyPreview,
} from './guitar-dimensions'

// Composables
const {
  guitarTypes,
  presets,
  dimensions,
  selectedType,
  units,
  status,
  statusType,
  currentUnit,
  hasValidDimensions,
  toggleUnits,
  loadPreset,
  handleChange,
  clearAll,
  setStatus,
} = useGuitarDimensions()

const { isExporting, exportJSON, exportCSV, copyToClipboard, generateDXF, generateSVG } =
  useGuitarExport()

const { isGenerating, camResults, selectedPost, generateToolpath, formatMoves, downloadGCode } =
  useGuitarCAM()

// Computed
const movesPreview = computed(() => {
  if (!camResults.value?.moves) return ''
  return formatMoves(camResults.value.moves)
})

// Export handlers
function handleExportJSON() {
  const success = exportJSON({
    dimensions: dimensions.value,
    guitarType: selectedType.value,
    units: units.value,
    currentUnit: currentUnit.value,
  })
  setStatus(success ? '✅ JSON file downloaded' : '❌ Export failed', success ? 'success' : 'error')
}

function handleExportCSV() {
  const success = exportCSV({
    dimensions: dimensions.value,
    guitarType: selectedType.value,
    units: units.value,
    currentUnit: currentUnit.value,
  })
  setStatus(success ? '✅ CSV file downloaded' : '❌ Export failed', success ? 'success' : 'error')
}

async function handleCopyToClipboard() {
  const success = await copyToClipboard({
    dimensions: dimensions.value,
    guitarType: selectedType.value,
    units: units.value,
    currentUnit: currentUnit.value,
  })
  setStatus(
    success ? '✅ Copied to clipboard' : '❌ Failed to copy to clipboard',
    success ? 'success' : 'error'
  )
}

async function handleGenerateDXF() {
  if (!hasValidDimensions.value) {
    setStatus('❌ Please enter at least body length and lower bout width', 'error')
    return
  }

  setStatus('⏳ Generating parametric body outline...', 'info')
  const result = await generateDXF({
    dimensions: dimensions.value,
    guitarType: selectedType.value,
    units: units.value,
    currentUnit: currentUnit.value,
  })

  if (result.success) {
    setStatus('✅ DXF body outline downloaded! Import into CAM software.', 'success')
  } else {
    setStatus(`❌ Generation failed: ${result.error}`, 'error')
  }
}

async function handleGenerateSVG() {
  if (!hasValidDimensions.value) {
    setStatus('❌ Please enter at least body length and lower bout width', 'error')
    return
  }

  setStatus('⏳ Generating parametric body outline...', 'info')
  const result = await generateSVG({
    dimensions: dimensions.value,
    guitarType: selectedType.value,
    units: units.value,
    currentUnit: currentUnit.value,
  })

  if (result.success) {
    setStatus('✅ SVG body outline downloaded!', 'success')
  } else {
    setStatus(`❌ Generation failed: ${result.error}`, 'error')
  }
}

async function handleGenerateCAM() {
  if (!hasValidDimensions.value) {
    setStatus('❌ Please enter valid body dimensions first', 'error')
    return
  }

  setStatus('⏳ Planning adaptive toolpath...', 'info')
  const result = await generateToolpath(dimensions.value, selectedType.value)

  if (result.success && camResults.value) {
    const stats = camResults.value.stats
    setStatus(
      `✅ Toolpath generated: ${stats.move_count} moves, ${stats.length_mm.toFixed(2)}mm path, ${stats.time_min.toFixed(2)} min`,
      'success'
    )
  } else {
    setStatus(`❌ CAM planning failed: ${result.error}`, 'error')
  }
}

function handleDownloadGCode() {
  setStatus(`⏳ Generating G-code for ${selectedPost.value}...`, 'info')
  const success = downloadGCode(selectedType.value)

  if (success) {
    setStatus(`✅ G-code downloaded`, 'success')
  } else {
    setStatus('❌ Generate toolpath first', 'error')
  }
}
</script>

<style scoped>
.guitar-dimensions-form {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1.5rem;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.form-header {
  margin-bottom: 2rem;
  text-align: center;
}

.form-header h2 {
  font-size: 2rem;
  margin-bottom: 0.5rem;
  color: #333;
}

.description {
  color: #666;
  font-size: 0.95rem;
}

.form-section {
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid #eee;
}

.form-section h3 {
  font-size: 1.25rem;
  margin-bottom: 1rem;
  color: #444;
}

.button-group {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.button-group button {
  padding: 0.75rem 1.5rem;
  border: 2px solid #ddd;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.button-group button:hover {
  border-color: #667eea;
  color: #667eea;
}

.button-group button.active {
  background: #667eea;
  border-color: #667eea;
  color: white;
}

.actions {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.actions button {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #667eea;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #5568d3;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f5f5f5;
  color: #333;
  border: 1px solid #ddd;
}

.btn-secondary:hover {
  background: #e8e8e8;
}

.btn-success {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  font-weight: 600;
  box-shadow: 0 4px 6px rgba(16, 185, 129, 0.3);
}

.btn-success:hover:not(:disabled) {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  box-shadow: 0 6px 8px rgba(16, 185, 129, 0.4);
  transform: translateY(-2px);
}

.btn-success:disabled {
  background: #d1d5db;
  box-shadow: none;
  cursor: not-allowed;
}

.btn-danger {
  background: #ef4444;
  color: white;
}

.btn-danger:hover {
  background: #dc2626;
}

.status-message {
  padding: 1rem;
  border-radius: 6px;
  margin-top: 1rem;
  font-weight: 500;
}

.status-message.success {
  background: #d1fae5;
  color: #065f46;
}

.status-message.error {
  background: #fee2e2;
  color: #991b1b;
}

.status-message.info {
  background: #dbeafe;
  color: #1e40af;
}
</style>
