<template>
  <div class="transfer-function-renderer">
    <div class="header">
      <span class="label">{{ entry.kind }}</span>
      <span class="path">{{ entry.relpath }}</span>
      <div class="controls">
        <label class="toggle">
          <input
            v-model="showPhase"
            type="checkbox"
          >
          <span>Phase</span>
        </label>
        <label class="toggle">
          <input
            v-model="logFreq"
            type="checkbox"
          >
          <span>Log Freq</span>
        </label>
        <label class="toggle">
          <input
            v-model="dbScale"
            type="checkbox"
          >
          <span>dB</span>
        </label>
        <button
          class="btn"
          @click="downloadChart"
        >
          PNG
        </button>
      </div>
    </div>

    <div
      v-if="parseError"
      class="error"
    >
      <strong>Parse Error:</strong> {{ parseError }}
    </div>

    <div
      v-else-if="!hasData"
      class="empty"
    >
      No transfer function data found in JSON.
    </div>

    <div
      v-else
      class="chart-container"
    >
      <canvas ref="chartCanvas" />
    </div>

    <div class="stats">
      <span v-if="peakInfo">
        <strong>Peak:</strong> {{ peakInfo.freq.toFixed(1) }} Hz @ {{ peakInfo.mag.toFixed(2) }} {{ dbScale ? 'dB' : '' }}
      </span>
      <span><strong>Points:</strong> {{ dataPoints }}</span>
      <span v-if="freqRange"><strong>Range:</strong> {{ freqRange }}</span>
      <span
        v-if="odsMetadata"
        class="metadata-badge"
      >
        {{ odsMetadata }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * TransferFunctionRenderer - Bode plot for transfer function data.
 *
 * REFACTORED: Uses composables for cleaner separation of concerns.
 */
import { ref } from 'vue'
import type { RendererProps } from './types'
import {
  useTransferFunctionParsing,
  useTransferFunctionStats,
  useTransferFunctionChart
} from './transfer_function/composables'

// =============================================================================
// PROPS
// =============================================================================

const props = defineProps<RendererProps>()

// =============================================================================
// LOCAL STATE
// =============================================================================

const chartCanvas = ref<HTMLCanvasElement | null>(null)
const showPhase = ref(true)
const logFreq = ref(true)   // Default to log frequency for Bode plot
const dbScale = ref(true)   // Default to dB scale for Bode plot

// =============================================================================
// COMPOSABLES
// =============================================================================

// Parsing
const { parsedData, parseError } = useTransferFunctionParsing(() => props.bytes)

// Stats
const {
  hasData,
  dataPoints,
  chartData,
  peakInfo,
  freqRange,
  odsMetadata
} = useTransferFunctionStats(parsedData, dbScale)

// Chart (handles lifecycle internally)
const { downloadChart } = useTransferFunctionChart(
  chartCanvas,
  chartData,
  showPhase,
  logFreq,
  dbScale,
  () => props.bytes
)
</script>

<style scoped>
.transfer-function-renderer {
  background: var(--vt-c-bg-soft, #1e1e1e);
  border-radius: 8px;
  overflow: hidden;
}

.header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--vt-c-divider-light, #333);
  flex-wrap: wrap;
}

.label {
  font-family: monospace;
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  font-size: 0.85rem;
}

.path {
  font-family: monospace;
  font-size: 0.8rem;
  color: var(--vt-c-text-2, #aaa);
}

.controls {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-left: auto;
}

.toggle {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.85rem;
  color: var(--vt-c-text-2, #ccc);
  cursor: pointer;
}

.toggle input {
  accent-color: #3b82f6;
}

.btn {
  padding: 0.35rem 0.6rem;
  font-size: 0.8rem;
  background: var(--vt-c-bg-mute, #2a2a2a);
  border: 1px solid var(--vt-c-divider-light, #444);
  border-radius: 4px;
  cursor: pointer;
  color: inherit;
}

.btn:hover {
  background: var(--vt-c-bg, #333);
}

.chart-container {
  position: relative;
  height: 400px;
  padding: 1rem;
}

.stats {
  display: flex;
  gap: 1.5rem;
  padding: 0.75rem 1rem;
  border-top: 1px solid var(--vt-c-divider-light, #333);
  font-size: 0.85rem;
  color: var(--vt-c-text-2, #aaa);
  flex-wrap: wrap;
}

.stats strong {
  color: var(--vt-c-text-1, #ddd);
}

.metadata-badge {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
}

.error {
  padding: 1rem;
  color: var(--vt-c-red, #f44);
  background: rgba(255, 68, 68, 0.1);
  margin: 1rem;
  border-radius: 6px;
}

.empty {
  padding: 2rem;
  text-align: center;
  color: var(--vt-c-text-2, #888);
}
</style>
