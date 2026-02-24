<script setup lang="ts">
/**
 * VectorizationControls.vue - Pre-vectorization controls and action button
 * Extracted from Phase2VectorizationPanel.vue
 */
import type { VectorParams } from "@/composables/useBlueprintWorkflow";

const props = defineProps<{
  vectorParams: VectorParams;
  isVectorizing: boolean;
}>();

const emit = defineEmits<{
  vectorize: [];
  "update:vectorParams": [params: VectorParams];
}>();

function updateParam<K extends keyof VectorParams>(key: K, value: VectorParams[K]) {
  emit("update:vectorParams", { ...props.vectorParams, [key]: value });
}
</script>

<template>
  <div class="action-card">
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
</template>

<style scoped>
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

.btn-primary {
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
  background: #10b981;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #059669;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary svg {
  width: 20px;
  height: 20px;
}
</style>
