<template>
  <div class="wsi-curve-renderer">
    <div class="header">
      <span class="label">{{ entry.kind }}</span>
      <span class="path">{{ entry.relpath }}</span>
      <div class="controls">
        <label class="toggle">
          <input
            v-model="showCohMean"
            type="checkbox"
          >
          <span>coh_mean</span>
        </label>
        <label class="toggle">
          <input
            v-model="showPhaseDisorder"
            type="checkbox"
          >
          <span>phase_disorder</span>
        </label>
        <label class="toggle">
          <input
            v-model="shadeAdmissible"
            type="checkbox"
          >
          <span>Admissible shading</span>
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
      <span v-if="rows.length > 0"><strong>Rows:</strong> {{ rows.length }}</span>
      <span v-if="freqRange"><strong>Range:</strong> {{ freqRange }}</span>
      <span v-if="maxWsiHz !== null"><strong>Max WSI:</strong> {{ maxWsi.toFixed(3) }} @ {{ maxWsiHz.toFixed(1) }} Hz</span>
      <span
        v-if="selectedNearest !== null"
        class="selected"
      >
        <strong>Nearest:</strong> {{ selectedNearest.freq_hz.toFixed(2) }} Hz → wsi {{ selectedNearest.wsi.toFixed(3) }}
      </span>
      <span
        v-if="selectedNearest !== null"
        class="selected muted"
      >
        (exporter fields; nearest sample)
      </span>
    </div>

    <details
      v-if="rows.length > 0"
      class="raw"
    >
      <summary class="raw-summary">
        Raw rows (first 25)
      </summary>
      <pre class="raw-pre">{{ rawPreview }}</pre>
    </details>
  </div>
</template>


<script setup lang="ts">
/**
 * GOVERNANCE NOTE — WSI CURVE RENDERER
 *
 * This renderer displays the exported Wolf Stress Index (WSI) curve exactly
 * as provided by tap-tone-pi. Its role is visual correlation only.
 *
 * REFACTORED: Uses composables for cleaner separation of concerns.
 */
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import type { RendererProps } from './types'
import {
  useWsiCurveState,
  useWsiCurveParsing,
  useWsiCurveStats,
  useWsiCurveSelection,
  useWsiCurveChart,
  type PeakSelectedPayload
} from './wsi_curve/composables'

// =============================================================================
// PROPS & EMITS
// =============================================================================

const props = defineProps<RendererProps & { selectedFreqHz?: number | null }>()
const emit = defineEmits<{
  (e: 'peak-selected', payload: PeakSelectedPayload): void
}>()

// =============================================================================
// REFS
// =============================================================================

const chartCanvas = ref<HTMLCanvasElement | null>(null)

// =============================================================================
// COMPOSABLES
// =============================================================================

// State
const {
  showCohMean,
  showPhaseDisorder,
  shadeAdmissible,
  parseError,
  emphasizeSelectionPoint
} = useWsiCurveState()

// Parsing
const { rows } = useWsiCurveParsing(
  () => props.bytes,
  parseError
)

// Stats
const { freqRange, maxWsiHz, maxWsi, rawPreview } = useWsiCurveStats(rows)

// Selection
const { nearestRowByFreq, nearestRowByLabel, selectedNearest, boolText } =
  useWsiCurveSelection(rows, () => props.selectedFreqHz)

// Chart
const { createChart, destroyChart, downloadChart } = useWsiCurveChart(
  chartCanvas,
  rows,
  showCohMean,
  showPhaseDisorder,
  shadeAdmissible,
  emphasizeSelectionPoint,
  selectedNearest,
  () => props.selectedFreqHz,
  nearestRowByFreq,
  nearestRowByLabel,
  boolText,
  () => props.entry.relpath,
  emit
)

// =============================================================================
// LIFECYCLE
// =============================================================================

onMounted(() => nextTick(createChart))
onUnmounted(destroyChart)

watch(
  [showCohMean, showPhaseDisorder, shadeAdmissible, emphasizeSelectionPoint, () => props.bytes, () => props.selectedFreqHz],
  () => nextTick(createChart)
)
</script>

<style scoped>
.wsi-curve-renderer {
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
  background: rgba(34, 197, 94, 0.18);
  color: #22c55e;
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
  accent-color: #22c55e;
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
  gap: 1.25rem;
  padding: 0.75rem 1rem;
  border-top: 1px solid var(--vt-c-divider-light, #333);
  font-size: 0.85rem;
  color: var(--vt-c-text-2, #aaa);
  flex-wrap: wrap;
}
.stats strong {
  color: var(--vt-c-text-1, #ddd);
}
.selected {
  color: #93c5fd;
}
.muted {
  opacity: 0.7;
}
.error {
  padding: 1rem;
  color: var(--vt-c-red, #f44);
  background: rgba(255, 68, 68, 0.1);
  margin: 1rem;
  border-radius: 6px;
}
.raw {
  margin: 10px 0 0 0;
  padding: 0 1rem 1rem 1rem;
}
.raw-summary {
  cursor: pointer;
  user-select: none;
  opacity: 0.85;
  padding: 0.35rem 0;
}
.raw-pre {
  max-height: 240px;
  overflow: auto;
  font-size: 0.8rem;
  line-height: 1.35;
  margin: 0;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 10px;
}
</style>
