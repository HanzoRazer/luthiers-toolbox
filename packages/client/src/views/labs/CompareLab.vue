<template>
  <div class="compare-lab">
    <div class="flex items-center gap-3 mb-2">
      <h2 id="compare-lab-title">
        Compare Lab (Dual Toolpath Diff)
      </h2>
      <CompareModeButton
        :baseline-id="baseline?.id || 'baseline'"
        :candidate-id="compare?.id || 'candidate'"
        aria-label="Back to Adaptive Lab"
      >
        Back to Adaptive Lab
      </CompareModeButton>
    </div>
    <DualSvgDisplay
      :baseline="baseline"
      :candidate="compare"
      :diff="delta"
      :opacity-a="0.85"
      :opacity-b="0.85"
      :diff-mode="diffMode"
      :sync-viewports="true"
    />
    <DiffModeToggle
      v-model="diffMode"
      :delta="delta"
    />
    <ExportToolbar
      v-if="delta"
      @export-dxf="exportDXF"
      @export-svg="exportSVG"
      @export-gcode="exportGcode"
    />
    <div v-if="loading">
      Loading...
    </div>
    <div
      v-if="error"
      class="error"
    >
      {{ error }}
    </div>
    <MetricsDisplay :delta="delta" />
  </div>
</template>

<script setup lang="ts">
import { api } from '@/services/apiBase';

import CompareModeButton from '@/components/compare/CompareModeButton.vue'
import { ref, onMounted, watch } from 'vue'
import DualSvgDisplay from '@/components/compare/DualSvgDisplay.vue'
import DiffModeToggle from '@/components/compare/DiffModeToggle.vue'
import ExportToolbar from '@/components/compare/ExportToolbar.vue'
import MetricsDisplay from '@/components/compare/MetricsDisplay.vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const baseline = ref<any>(null)
const compare = ref<any>(null)
const delta = ref<any>(null)
const loading = ref(true)
const error = ref('')
const diffMode = ref(localStorage.getItem('compare.diffMode') || 'overlay')

// Sync diffMode to localStorage and querystring
watch(diffMode, (v) => {
  localStorage.setItem('compare.diffMode', v)
  const q = { ...route.query, diff_mode: v }
  router.replace({ query: q })
})

onMounted(async () => {
  // Restore from querystring/localStorage
  if (route.query.diff_mode) diffMode.value = String(route.query.diff_mode)
  // TODO: expand for overlays, selected jobs, etc.
  const baseId = route.query.baseline_id || localStorage.getItem('compare.baseline_id')
  const compId = route.query.compare_id || localStorage.getItem('compare.candidate_id')
  if (baseId) localStorage.setItem('compare.baseline_id', baseId as string)
  if (compId) localStorage.setItem('compare.candidate_id', compId as string)
  if (!baseId || !compId) {
    error.value = 'Missing baseline or compare job ID.'
    loading.value = false
    return
  }
  try {
    const resp = await api(`/api/cam/compare/diff?baseline=${baseId}&compare=${compId}`)
    if (!resp.ok) throw new Error('API error')
    const data = await resp.json()
    baseline.value = data.baseline
    compare.value = data.compare
    delta.value = data.delta
  } catch (e: any) {
    error.value = e.message || 'Failed to load diff.'
  } finally {
    loading.value = false
  }
})
// --- Export logic ---
function downloadBlob(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  setTimeout(() => {
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  }, 100)
}

async function exportDXF() {
  if (!delta.value) return
  const r = await api('/api/geometry/export?fmt=dxf', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ geometry: delta.value })
  })
  const blob = await r.blob()
  downloadBlob(blob, 'compare_diff.dxf')
}
async function exportSVG() {
  if (!delta.value) return
  const r = await api('/api/geometry/export?fmt=svg', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ geometry: delta.value })
  })
  const blob = await r.blob()
  downloadBlob(blob, 'compare_diff.svg')
}
async function exportGcode() {
  if (!compare.value || !compare.value.gcode) return
  const r = await api('/api/geometry/export_gcode', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ gcode: compare.value.gcode, units: 'mm', post_id: 'GRBL' })
  })
  const blob = await r.blob()
  downloadBlob(blob, 'compare_candidate.nc')
}
</script>

<style scoped>
.compare-lab { padding: 2rem; }
.metrics { margin-top: 2rem; }
.error { color: red; }
 .export-toolbar { margin: 1.5rem 0; display: flex; gap: 1rem; }
</style>
