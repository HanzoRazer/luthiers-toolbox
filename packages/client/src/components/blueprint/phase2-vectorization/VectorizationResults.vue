<script setup lang="ts">
/**
 * VectorizationResults.vue - Vectorization results display with stats and exports
 * Extracted from Phase2VectorizationPanel.vue
 */
import { computed } from "vue";
import type { VectorizedGeometry } from "@/composables/useBlueprintWorkflow";

const props = defineProps<{
  vectorizedGeometry: VectorizedGeometry;
}>();

const emit = defineEmits<{
  "download-svg": [];
  "download-dxf": [];
  "re-vectorize": [];
}>();

const svgPreviewUrl = computed(() => {
  if (!props.vectorizedGeometry?.svg_path) return "#";
  return `/api/blueprint/static/${props.vectorizedGeometry.svg_path.split("/").pop()}`;
});
</script>

<template>
  <div class="results-card">
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
</template>

<style scoped>
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
