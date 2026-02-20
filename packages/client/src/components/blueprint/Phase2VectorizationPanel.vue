<template>
  <section class="workflow-section phase-2">
    <div class="section-header">
      <h2>
        <span class="step-number">2</span>
        Geometry Vectorization (OpenCV)
      </h2>
    </div>

    <!-- Pre-Vectorization Action Card -->
    <div
      v-if="!vectorizedGeometry"
      class="action-card"
    >
      <p class="hint">
        Detect edges, extract contours, and export CAM-ready DXF with closed polylines
      </p>

      <!-- Vectorization Controls -->
      <div class="controls-grid">
        <div class="control-group">
          <label>Scale Factor:</label>
          <input
            :value="vectorParams.scaleFactor"
            type="number"
            step="0.1"
            min="0.1"
            max="10"
            @input="updateParam('scaleFactor', parseFloat(($event.target as HTMLInputElement).value))"
          >
          <span class="control-hint">Adjust if scale detection was incorrect</span>
        </div>
        <div class="control-group">
          <label>Edge Threshold (Low):</label>
          <input
            :value="vectorParams.lowThreshold"
            type="number"
            min="10"
            max="200"
            @input="updateParam('lowThreshold', parseInt(($event.target as HTMLInputElement).value))"
          >
          <span class="control-hint">Lower = more edges detected</span>
        </div>
        <div class="control-group">
          <label>Edge Threshold (High):</label>
          <input
            :value="vectorParams.highThreshold"
            type="number"
            min="50"
            max="300"
            @input="updateParam('highThreshold', parseInt(($event.target as HTMLInputElement).value))"
          >
          <span class="control-hint">Higher = stricter edge detection</span>
        </div>
        <div class="control-group">
          <label>Min Contour Area (px):</label>
          <input
            :value="vectorParams.minArea"
            type="number"
            min="10"
            max="1000"
            @input="updateParam('minArea', parseInt(($event.target as HTMLInputElement).value))"
          >
          <span class="control-hint">Filter small noise</span>
        </div>
      </div>

      <button
        :disabled="isVectorizing"
        class="btn-primary"
        @click="emit('vectorize')"
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
            d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z"
          />
        </svg>
        {{ isVectorizing ? 'Vectorizing...' : 'Vectorize Geometry' }}
      </button>
    </div>

    <!-- Vectorization Results -->
    <div
      v-if="vectorizedGeometry"
      class="results-card"
    >
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
          <p>
            SVG Preview: <a
              :href="svgPreviewUrl"
              target="_blank"
            >View SVG</a>
          </p>
          <p class="hint-small">
            Detected contours shown in blue, lines in red
          </p>
        </div>
      </div>

      <!-- Phase 2 Exports -->
      <div class="export-row">
        <button
          class="btn-primary"
          @click="emit('download-svg')"
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
          Download SVG (Vectorized)
        </button>
        <button
          class="btn-primary"
          @click="emit('download-dxf')"
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
          Download DXF R2000 (CAM-Ready)
        </button>
        <button
          class="btn-secondary"
          @click="emit('re-vectorize')"
        >
          Re-vectorize with New Settings
        </button>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { VectorParams, VectorizedGeometry } from '@/composables/useBlueprintWorkflow'

// Props
interface Props {
  vectorizedGeometry: VectorizedGeometry | null
  vectorParams: VectorParams
  isVectorizing: boolean
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  'vectorize': []
  'download-svg': []
  'download-dxf': []
  're-vectorize': []
  'update:vectorParams': [params: VectorParams]
}>()

// Computed
const svgPreviewUrl = computed(() => {
  if (!props.vectorizedGeometry?.svg_path) return '#'
  return `/api/blueprint/static/${props.vectorizedGeometry.svg_path.split('/').pop()}`
})

// Helpers
function updateParam<K extends keyof VectorParams>(key: K, value: VectorParams[K]) {
  emit('update:vectorParams', { ...props.vectorParams, [key]: value })
}
</script>

<style scoped>
.workflow-section {
  border: 2px solid #e5e7eb;
  border-radius: 1rem;
  padding: 1.5rem;
  background: white;
}

.workflow-section.phase-2 {
  border-color: #10b981;
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
  font-size: 1.25rem;
}

.step-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #10b981;
  color: white;
  font-weight: bold;
  font-size: 1rem;
}

.action-card {
  background: #f9fafb;
  border-radius: 0.75rem;
  padding: 1.5rem;
}

.hint {
  color: #6b7280;
  margin-bottom: 1rem;
}

.controls-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.control-group label {
  font-weight: 500;
  color: #374151;
  font-size: 0.875rem;
}

.control-group input {
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 1rem;
}

.control-hint {
  color: #9ca3af;
  font-size: 0.75rem;
}

.results-card {
  background: #f9fafb;
  border-radius: 0.75rem;
  padding: 1.5rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: white;
  padding: 1rem;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 1.5rem;
  font-weight: 700;
  color: #10b981;
}

.stat-label {
  display: block;
  color: #6b7280;
  font-size: 0.875rem;
  margin-top: 0.25rem;
}

.preview-section h4 {
  margin: 0 0 0.5rem 0;
  color: #374151;
}

.preview-placeholder {
  background: white;
  padding: 1rem;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
  margin-bottom: 1.5rem;
}

.preview-placeholder a {
  color: #3b82f6;
  text-decoration: underline;
}

.hint-small {
  color: #9ca3af;
  font-size: 0.875rem;
  margin-top: 0.5rem;
}

.export-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

/* Buttons */
.btn-primary,
.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.5rem;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #10b981;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #059669;
}

.btn-secondary {
  background: #e5e7eb;
  color: #374151;
}

.btn-secondary:hover:not(:disabled) {
  background: #d1d5db;
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
</style>
