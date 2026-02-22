<template>
  <div class="spectrum-chart-renderer">
    <div class="header">
      <span class="label">{{ entry.kind }}</span>
      <span class="path">{{ entry.relpath }}</span>
      <div class="controls">
        <label class="toggle">
          <input
            v-model="showCoherence"
            type="checkbox"
          >
          <span>Coherence</span>
        </label>
        <label class="toggle">
          <input
            v-model="logScale"
            type="checkbox"
          >
          <span>Log Scale</span>
        </label>
        <label
          v-if="parsedPeaks.length > 0"
          class="toggle"
        >
          <input
            v-model="showPeaks"
            type="checkbox"
          >
          <span>Peaks ({{ parsedPeaks.length }})</span>
        </label>
        <button
          class="btn"
          @click="downloadChart"
        >
          📷 PNG
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
      v-else
      class="chart-container"
    >
      <canvas ref="chartCanvas" />
    </div>

    <div class="stats">
      <span v-if="peakFreq !== null">
        <strong>Peak:</strong> {{ peakFreq.toFixed(1) }} Hz @ {{ peakMag.toFixed(4) }}
      </span>
      <span><strong>Points:</strong> {{ dataPoints }}</span>
      <span
        v-if="isDecimated"
        class="decimation-warning"
      >
        ⚠️ Decimated from {{ originalRowCount }} points
      </span>
      <span v-if="freqRange"><strong>Range:</strong> {{ freqRange }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { watch, onMounted, onUnmounted, nextTick } from 'vue'
import {
  Chart,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  LogarithmicScale,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import type { RendererProps } from './types'
import type { PeakSelectedPayload } from './spectrum_chart/composables'
import {
  useSpectrumChartState,
  useSpectrumChartParsing,
  useSpectrumChartStats,
  useSpectrumChartRender
} from './spectrum_chart/composables'

// Register Chart.js components
Chart.register(
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  LogarithmicScale,
  Title,
  Tooltip,
  Legend,
  Filler
)

const props = defineProps<RendererProps & { selectedFreqHz?: number | null }>()
const emit = defineEmits<{
  (e: 'peak-selected', payload: PeakSelectedPayload): void
}>()

// State
const {
  chartCanvas,
  showCoherence,
  logScale,
  showPeaks,
  parseError,
  originalRowCount,
  chartInstance
} = useSpectrumChartState()

// Parsing
const { parsedData, parsedPeaks, isDecimated } = useSpectrumChartParsing(
  () => props.bytes,
  () => props.peaksBytes,
  parseError,
  originalRowCount
)

// Stats
const { dataPoints, peakFreq, peakMag, freqRange, nearestMagAtFreq } =
  useSpectrumChartStats(parsedData)

// Rendering
const { createChart, downloadChart, destroyChart } = useSpectrumChartRender({
  chartCanvas,
  chartInstance,
  parsedData,
  parsedPeaks,
  showCoherence,
  showPeaks,
  logScale,
  selectedFreqHz: () => props.selectedFreqHz ?? null,
  entryRelpath: () => props.entry.relpath,
  nearestMagAtFreq,
  emitPeakSelected: (payload) => emit('peak-selected', payload)
})

// Lifecycle
onMounted(() => {
  nextTick(() => createChart())
})

onUnmounted(() => {
  destroyChart()
})

// Watch for changes
watch(
  [showCoherence, logScale, showPeaks, () => props.bytes, () => props.peaksBytes, () => props.selectedFreqHz],
  () => {
    nextTick(() => createChart())
  }
)
</script>

<style scoped>
.spectrum-chart-renderer {
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
  background: rgba(66, 184, 131, 0.2);
  color: #42b883;
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
  accent-color: #42b883;
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
}

.stats strong {
  color: var(--vt-c-text-1, #ddd);
}

.decimation-warning {
  color: #f59e0b;
  background: rgba(245, 158, 11, 0.15);
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
</style>
