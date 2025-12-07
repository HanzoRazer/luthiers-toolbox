<!-- Patch N14.1 / N10 - CNC Export Panel for RMOS Studio -->

<template>
  <div class="cnc-export-panel">
    <h2>CNC Export (Per-Ring)</h2>

    <div class="config-grid">
      <div class="config-group">
        <h3>Material</h3>
        <div class="material-options">
          <label>
            <input
              type="radio"
              value="hardwood"
              v-model="material"
            />
            Hardwood
          </label>
          <label>
            <input
              type="radio"
              value="softwood"
              v-model="material"
            />
            Softwood
          </label>
          <label>
            <input
              type="radio"
              value="composite"
              v-model="material"
            />
            Composite
          </label>
        </div>
      </div>

      <div class="config-group">
        <h3>Jig Origin</h3>
        <label>
          Origin X (mm)
          <input type="number" v-model.number="jigOriginX" />
        </label>
        <label>
          Origin Y (mm)
          <input type="number" v-model.number="jigOriginY" />
        </label>
        <label>
          Rotation (deg)
          <input type="number" v-model.number="jigRotation" />
        </label>
      </div>
    </div>

    <div class="actions">
      <button
        :disabled="!canExport || loading"
        @click="onExport"
      >
        Export CNC for Selected Ring
      </button>
      <span v-if="loading">Exporting...</span>

      <!-- Bundle #12: Download Operator PDF button -->
      <button
        v-if="cncExport && cncExport.job_id"
        type="button"
        @click="onDownloadReport"
        class="download-pdf-btn"
      >
        Download Operator PDF
      </button>
    </div>

    <div v-if="cncExport" class="results">
      <h3>Export Summary</h3>
      <p>
        <strong>Job ID:</strong> {{ cncExport.job_id }}<br />
        <strong>Ring ID:</strong> {{ cncExport.ring_id }}<br />
        <strong>Toolpath segments:</strong> {{ cncExport.toolpaths.length }}<br />
        <strong>Estimated runtime:</strong>
        {{ cncExport.simulation.estimated_runtime_sec.toFixed(1) }} s
        ({{ cncExport.simulation.passes }} pass<span v-if="cncExport.simulation.passes !== 1">es</span>)
      </p>

      <h3>Safety</h3>
      <p>
        <strong>Decision:</strong> {{ cncExport.safety.decision }}<br />
        <strong>Risk level:</strong> {{ cncExport.safety.risk_level }}<br />
        <strong>Override required:</strong>
        {{ cncExport.safety.requires_override ? 'Yes' : 'No' }}
      </p>
      <ul v-if="cncExport.safety.reasons && cncExport.safety.reasons.length">
        <li v-for="(reason, idx) in cncExport.safety.reasons" :key="idx">
          {{ reason }}
        </li>
      </ul>

      <h3>Toolpath Ladder (Stub View)</h3>
      <div class="toolpath-ladder">
        <div
          v-for="seg in cncExport.toolpaths"
          :key="segKey(seg)"
          class="toolpath-row"
        >
          <span class="index">
            {{ segIndex(seg) }}
          </span>
          <span class="coords">
            ({{ seg.x_start_mm.toFixed(1) }}, {{ seg.y_start_mm.toFixed(1) }})
            →
            ({{ seg.x_end_mm.toFixed(1) }}, {{ seg.y_end_mm.toFixed(1) }})
          </span>
          <span class="feed">
            {{ seg.feed_mm_per_min.toFixed(0) }} mm/min
          </span>
        </div>
      </div>
    </div>

    <p v-else class="no-export">
      No CNC export yet. Generate slices for a ring, configure material & jig,
      then click "Export CNC".
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRosetteDesignerStore } from '@/stores/useRosetteDesignerStore'

const store = useRosetteDesignerStore()

const loading = computed(() => store.loading)
const cncExport = computed(() => store.cncExport)
const material = computed({
  get: () => store.cncMaterial,
  set: (val: 'hardwood' | 'softwood' | 'composite') => {
    store.cncMaterial = val
  },
})

const jigOriginX = computed({
  get: () => store.cncJigOriginX,
  set: (val: number) => {
    store.cncJigOriginX = val
  },
})

const jigOriginY = computed({
  get: () => store.cncJigOriginY,
  set: (val: number) => {
    store.cncJigOriginY = val
  },
})

const jigRotation = computed({
  get: () => store.cncJigRotationDeg,
  set: (val: number) => {
    store.cncJigRotationDeg = val
  },
})

const canExport = computed(() => !!store.sliceBatch && store.rings.length > 0)

function onExport() {
  store.exportCncForSelectedRing()
}

function onDownloadReport() {
  const exportResult = cncExport.value
  if (!exportResult || !exportResult.job_id) return

  // Simple browser download: open the PDF endpoint in a new tab/window.
  const url = `/api/rmos/rosette/operator-report-pdf/${encodeURIComponent(
    exportResult.job_id,
  )}`
  window.open(url, '_blank')
}

function segIndex(seg: any): number {
  // just derive from position, since the segment doesn't carry an index
  return Math.floor(seg.x_start_mm / 2)
}

function segKey(seg: any): string {
  return `${seg.x_start_mm}_${seg.y_start_mm}_${seg.x_end_mm}_${seg.y_end_mm}`
}
</script>

<style scoped>
.cnc-export-panel {
  font-size: 0.9rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.config-grid {
  display: grid;
  grid-template-columns: 1.2fr 1.2fr;
  gap: 1rem;
}

.config-group {
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 0.5rem 0.75rem;
}

.config-group h3 {
  margin-top: 0;
  margin-bottom: 0.5rem;
  font-size: 0.95rem;
}

.material-options {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.config-group label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-bottom: 0.35rem;
}

.config-group input {
  padding: 0.25rem 0.4rem;
  font-size: 0.9rem;
}

.actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.download-pdf-btn {
  background-color: #0066cc;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
}

.download-pdf-btn:hover {
  background-color: #0052a3;
}

.download-pdf-btn:active {
  background-color: #004080;
}

.results {
  border-top: 1px solid #ddd;
  padding-top: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.toolpath-ladder {
  max-height: 260px;
  overflow: auto;
  border: 1px solid #eee;
  border-radius: 4px;
}

.toolpath-row {
  display: grid;
  grid-template-columns: 40px 1fr 100px;
  gap: 0.5rem;
  padding: 0.2rem 0.4rem;
  border-bottom: 1px solid #f1f1f1;
  font-size: 0.8rem;
}

.toolpath-row:last-child {
  border-bottom: none;
}

.toolpath-row .index {
  text-align: right;
  font-weight: 600;
}

.toolpath-row .coords {
  font-family: monospace;
}

.toolpath-row .feed {
  text-align: right;
}

.no-export {
  font-style: italic;
  color: #777;
}
</style>
