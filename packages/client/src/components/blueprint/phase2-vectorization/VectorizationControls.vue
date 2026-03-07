<script setup lang="ts">
/**
 * VectorizationControls.vue - Pre-vectorization controls and action button
 *
 * Controls:
 * - Scale Factor: Manual override if calibration was incorrect
 * - Instrument Type: Electric vs Acoustic (affects contour scoring)
 * - Dark Threshold: Line extraction sensitivity (auto or 0-255)
 * - Gap Close Size: Morphological closing to connect broken lines
 */
import { computed } from "vue";
import type { VectorParams, ExtractionMode } from "@/composables/useBlueprintWorkflow";

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

// Handle dark threshold mode (auto vs manual)
const darkThresholdMode = computed(() =>
  props.vectorParams.darkThreshold === 'auto' ? 'auto' : 'manual'
);

function setDarkThresholdMode(mode: 'auto' | 'manual') {
  if (mode === 'auto') {
    updateParam('darkThreshold', 'auto');
  } else {
    updateParam('darkThreshold', 128); // Default manual value
  }
}

function setDarkThresholdValue(value: number) {
  updateParam('darkThreshold', value);
}
</script>

<template>
  <div class="action-card">
    <p class="hint">
      Detect edges, extract contours, and export CAM-ready DXF with closed polylines
    </p>

    <!-- Vectorization Controls -->
    <div class="controls-grid">
      <!-- Scale Factor -->
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
        <span class="control-hint">Override if calibration was incorrect</span>
      </div>

      <!-- Instrument Type -->
      <div class="control-group">
        <label>Instrument Type:</label>
        <select
          :value="vectorParams.instrumentType"
          @change="updateParam('instrumentType', ($event.target as HTMLSelectElement).value as 'electric' | 'acoustic')"
        >
          <option value="electric">Electric Guitar</option>
          <option value="acoustic">Acoustic Guitar</option>
        </select>
        <span class="control-hint">Affects contour scoring heuristics</span>
      </div>

      <!-- Extraction Mode -->
      <div class="control-group">
        <label>Extraction Mode:</label>
        <select
          :value="vectorParams.extractionMode"
          @change="updateParam('extractionMode', ($event.target as HTMLSelectElement).value as ExtractionMode)"
        >
          <option value="smart">Smart (ML-filtered)</option>
          <option value="simple">Simple (All contours)</option>
        </select>
        <span class="control-hint">Simple mode works for non-guitar instruments</span>
      </div>

      <!-- Dark Threshold -->
      <div class="control-group">
        <label>Line Detection:</label>
        <div class="threshold-controls">
          <label class="radio-label">
            <input
              type="radio"
              name="darkThreshold"
              value="auto"
              :checked="darkThresholdMode === 'auto'"
              @change="setDarkThresholdMode('auto')"
            >
            Auto
          </label>
          <label class="radio-label">
            <input
              type="radio"
              name="darkThreshold"
              value="manual"
              :checked="darkThresholdMode === 'manual'"
              @change="setDarkThresholdMode('manual')"
            >
            Manual
          </label>
          <input
            v-if="darkThresholdMode === 'manual'"
            :value="typeof vectorParams.darkThreshold === 'number' ? vectorParams.darkThreshold : 128"
            type="range"
            min="0"
            max="255"
            class="threshold-slider"
            @input="setDarkThresholdValue(parseInt(($event.target as HTMLInputElement).value))"
          >
          <span v-if="darkThresholdMode === 'manual'" class="threshold-value">
            {{ vectorParams.darkThreshold }}
          </span>
        </div>
        <span class="control-hint">Lower = detect lighter lines</span>
      </div>

      <!-- Gap Close Size -->
      <div class="control-group">
        <label>Gap Closing:</label>
        <div class="gap-controls">
          <input
            :value="vectorParams.gapCloseSize"
            type="range"
            min="0"
            max="10"
            @input="updateParam('gapCloseSize', parseInt(($event.target as HTMLInputElement).value))"
          >
          <span class="gap-value">{{ vectorParams.gapCloseSize || 'Off' }}</span>
        </div>
        <span class="control-hint">Connect broken lines (5 recommended)</span>
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

.control-group input[type="number"],
.control-group select {
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 1rem;
}

.control-hint {
  color: #9ca3af;
  font-size: 0.75rem;
}

/* Threshold controls */
.threshold-controls {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-weight: normal;
  font-size: 0.875rem;
  cursor: pointer;
}

.threshold-slider {
  flex: 1;
  min-width: 80px;
}

.threshold-value {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
  min-width: 30px;
}

/* Gap controls */
.gap-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.gap-controls input[type="range"] {
  flex: 1;
}

.gap-value {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
  min-width: 30px;
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
