<template>
  <div class="compare-lab-view">
    <div class="toolbar">
      <label>Opacity A <input
        v-model.number="opacityA"
        type="range"
        min="0"
        max="1"
        step="0.01"
      ></label>
      <label>Opacity B <input
        v-model.number="opacityB"
        type="range"
        min="0"
        max="1"
        step="0.01"
      ></label>
      <label>Diff Mode
        <select v-model="diffMode">
          <option value="none">None</option>
          <option value="overlay">Overlay</option>
          <option value="delta">Delta Only</option>
        </select>
      </label>
      <label><input
        v-model="syncViewports"
        type="checkbox"
      > Sync Viewports</label>
      <span class="legend">
        <span
          class="legend-item"
          style="color:blue"
        >■ Baseline</span>
        <span
          class="legend-item"
          style="color:green"
        >■ Candidate</span>
        <span
          class="legend-item"
          style="color:red"
        >■ Removed</span>
        <span
          class="legend-item"
          style="color:orange"
        >■ Changed</span>
      </span>
    </div>
    <div
      v-if="error"
      class="error"
    >
      {{ error }}
    </div>
    <DualSvgDisplay
      :baseline="baseline"
      :candidate="candidate"
      :diff="diff"
      :opacity-a="opacityA"
      :opacity-b="opacityB"
      :diff-mode="diffMode"
      :sync-viewports="syncViewports"
      @render-error="onRenderError"
    />
    <div
      v-if="renderError"
      class="render-error"
    >
      {{ renderError }}
    </div>
    <div
      v-if="diff"
      class="metrics"
    >
      <h3>Delta Metrics</h3>
      <ul>
        <li>Time Δ: {{ diff.time?.toFixed(2) }} s</li>
        <li>Length Δ: {{ diff.length?.toFixed(2) }} mm</li>
        <li>Retracts Δ: {{ diff.retracts }}</li>
      </ul>
    </div>
    <div class="export-drawer">
      <button disabled>
        Export (coming soon)
      </button>
      <div class="export-options">
        <label><input
          type="checkbox"
          checked
          disabled
        > Baseline</label>
        <label><input
          type="checkbox"
          checked
          disabled
        > Candidate</label>
        <label><input
          type="checkbox"
          disabled
        > Diff/Overlays</label>
        <select disabled>
          <option>SVG</option>
          <option>DXF</option>
          <option>GCODE</option>
        </select>
        <input
          type="text"
          disabled
          placeholder="Filename template preview..."
        >
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import DualSvgDisplay from '@/components/compare/DualSvgDisplay.vue'
import { parseBaseline, parseCandidate, parseDiffResult } from '@/cam/compare/compare_types'
import { loadLastBaseline, loadLastCandidate } from '@/cam/compare/compare_storage'

const route = useRoute()
const baseline = ref<any>(null)
const candidate = ref<any>(null)
const diff = ref<any>(null)
const error = ref('')
const renderError = ref('')
const opacityA = ref(1)
const opacityB = ref(1)
const diffMode = ref('none')
const syncViewports = ref(true)

function onRenderError(e: string) {
  renderError.value = e
}

onMounted(async () => {
  let baseId = route.query.baseline_id as string | undefined
  let candId = route.query.candidate_id as string | undefined
  // Fallback to localStorage if not in query
  if (!baseId) baseId = loadLastBaseline()?.id
  if (!candId) candId = loadLastCandidate()?.id
  if (!baseId || !candId) {
    error.value = 'Missing baseline or candidate job ID.'
    return
  }
  try {
    const resp = await fetch(`/api/cam/compare/diff?baseline=${baseId}&compare=${candId}`)
    if (!resp.ok) throw new Error('API error')
    const data = await resp.json()
    baseline.value = parseBaseline(data.baseline)
    candidate.value = parseCandidate(data.compare)
    diff.value = data.delta ? parseDiffResult(data.delta) : null
  } catch (e: any) {
    error.value = e.message || 'Failed to load diff.'
  }
})
</script>
<style scoped>
.compare-lab-view { padding: 2rem; }
.toolbar { display: flex; gap: 1.5rem; align-items: center; margin-bottom: 1rem; }
.legend { margin-left: 2rem; }
.legend-item { margin-right: 1rem; font-weight: bold; }
.error { color: red; margin-bottom: 1rem; }
.render-error { color: orange; margin-top: 1rem; }
.metrics { margin-top: 2rem; }
.export-drawer { margin-top: 2rem; background: #f5f5f5; padding: 1rem; border-radius: 6px; }
.export-options { display: flex; gap: 1rem; align-items: center; margin-top: 0.5rem; }
</style>
