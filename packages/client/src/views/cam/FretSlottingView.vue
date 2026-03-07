<script setup lang="ts">
/**
 * FretSlottingView - Fret Slot Cutting Toolpath Generator
 * Generate precision fret slot cutting toolpaths based on scale length
 *
 * Connected to API endpoints:
 *   POST /api/cam/fret-slots/preview
 *   POST /api/cam/fret-slots/generate
 *   GET  /api/calculators/fret-positions
 */
import { ref, computed } from 'vue'

const scaleLength = ref(648)  // mm
const fretCount = ref(22)
const slotWidth = ref(0.6)  // mm (for standard fretwire)
const slotDepth = ref(3.0)  // mm
const fretboardWidth = ref(43)  // mm at nut
const fretboardTaper = ref(56)  // mm at last fret

const bladeDiameter = ref(0.6)  // mm slitting saw
const feedRate = ref(200)
const spindleSpeed = ref(8000)
const multiPass = ref(false)
const passDepth = ref(1.5)

const loading = ref(false)

// Computed fret positions (simplified calculation)
const fretPositions = computed(() => {
  const positions: number[] = []
  for (let i = 1; i <= fretCount.value; i++) {
    positions.push(scaleLength.value - (scaleLength.value / Math.pow(2, i / 12)))
  }
  return positions
})

async function generateToolpath() {
  loading.value = true
  await new Promise(resolve => setTimeout(resolve, 500))
  loading.value = false
}

async function exportDxf() {
  alert('DXF export coming soon')
}
</script>

<template>
  <div class="fret-slotting-view">
    <div class="header">
      <h1>Fret Slotting</h1>
      <p class="subtitle">Generate precision fret slot cutting toolpaths</p>
    </div>

    <div class="content">
      <div class="panel params-panel">
        <h3>Scale & Frets</h3>
        <div class="form-row">
          <div class="form-group">
            <label>Scale Length (mm)</label>
            <input type="number" v-model.number="scaleLength" step="0.5" />
          </div>
          <div class="form-group">
            <label>Fret Count</label>
            <input type="number" v-model.number="fretCount" step="1" min="12" max="27" />
          </div>
        </div>

        <h3>Slot Dimensions</h3>
        <div class="form-row">
          <div class="form-group">
            <label>Slot Width (mm)</label>
            <input type="number" v-model.number="slotWidth" step="0.05" />
          </div>
          <div class="form-group">
            <label>Slot Depth (mm)</label>
            <input type="number" v-model.number="slotDepth" step="0.1" />
          </div>
        </div>

        <h3>Fretboard</h3>
        <div class="form-row">
          <div class="form-group">
            <label>Width at Nut (mm)</label>
            <input type="number" v-model.number="fretboardWidth" step="0.5" />
          </div>
          <div class="form-group">
            <label>Width at Last Fret (mm)</label>
            <input type="number" v-model.number="fretboardTaper" step="0.5" />
          </div>
        </div>

        <h3>Cutting</h3>
        <div class="form-row">
          <div class="form-group">
            <label>Feed Rate (mm/min)</label>
            <input type="number" v-model.number="feedRate" step="50" />
          </div>
          <div class="form-group">
            <label>Spindle (RPM)</label>
            <input type="number" v-model.number="spindleSpeed" step="1000" />
          </div>
        </div>
        <div class="form-group checkbox-group">
          <label><input type="checkbox" v-model="multiPass" /> Multi-pass cutting</label>
        </div>
      </div>

      <div class="panel positions-panel">
        <h3>Fret Positions</h3>
        <div class="positions-table">
          <div v-for="(pos, index) in fretPositions" :key="index" class="position-row">
            <span class="fret-num">{{ index + 1 }}</span>
            <span class="fret-pos">{{ pos.toFixed(3) }} mm</span>
          </div>
        </div>
        <p class="info">12-TET equal temperament</p>
      </div>

      <div class="panel preview-panel">
        <h3>Preview</h3>
        <div class="preview-container">
          <div v-if="loading" class="loading">Generating...</div>
          <div v-else class="placeholder">
            <span class="icon">🎸</span>
            <p>{{ fretCount }} fret slots</p>
            <p class="detail">Scale: {{ scaleLength }}mm • {{ slotWidth }}mm × {{ slotDepth }}mm</p>
          </div>
        </div>
        <div class="action-buttons">
          <button class="btn btn-primary" @click="generateToolpath" :disabled="loading">
            Generate Toolpath
          </button>
          <button class="btn btn-secondary" @click="exportDxf">Export DXF</button>
        </div>
      </div>
    </div>

    <div class="coming-soon-notice">
      <p>Full fret slotting with multi-scale and custom temperament support coming soon.</p>
    </div>
  </div>
</template>

<style scoped>
.fret-slotting-view { min-height: 100vh; background: #0a0a0a; color: #e5e5e5; padding: 2rem; }
.header { max-width: 1400px; margin: 0 auto 2rem; }
.header h1 { font-size: 2rem; font-weight: 700; margin: 0 0 0.5rem; }
.subtitle { color: #888; margin: 0; }

.content { max-width: 1400px; margin: 0 auto; display: grid; grid-template-columns: 1fr 200px 1fr; gap: 1.5rem; }
.panel { background: #1a1a1a; border-radius: 0.75rem; padding: 1.5rem; }
.panel h3 { font-size: 0.875rem; font-weight: 600; color: #888; text-transform: uppercase; margin: 0 0 1rem; }
.panel h3:not(:first-child) { margin-top: 1.5rem; }

.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; font-size: 0.875rem; color: #888; margin-bottom: 0.25rem; }
.form-group input { width: 100%; padding: 0.5rem; background: #262626; border: 1px solid #333; border-radius: 0.375rem; color: #e5e5e5; }
.checkbox-group label { display: flex; align-items: center; gap: 0.5rem; cursor: pointer; }

.positions-table { max-height: 400px; overflow-y: auto; }
.position-row { display: flex; justify-content: space-between; padding: 0.25rem 0; border-bottom: 1px solid #262626; font-size: 0.875rem; }
.fret-num { color: #888; }
.fret-pos { font-family: monospace; color: #e5e5e5; }
.info { font-size: 0.75rem; color: #60a5fa; margin-top: 0.5rem; }

.preview-container { aspect-ratio: 3/1; background: #0d0d0d; border-radius: 0.5rem; display: flex; align-items: center; justify-content: center; margin-bottom: 1rem; }
.placeholder { text-align: center; color: #666; }
.placeholder .icon { font-size: 3rem; display: block; margin-bottom: 0.5rem; }
.detail { font-size: 0.75rem; color: #888; }

.action-buttons { display: flex; gap: 0.75rem; }
.btn { flex: 1; padding: 0.75rem; border-radius: 0.5rem; font-weight: 600; cursor: pointer; border: none; }
.btn-primary { background: #2563eb; color: #fff; }
.btn-primary:disabled { background: #333; color: #666; }
.btn-secondary { background: #262626; color: #e5e5e5; border: 1px solid #333; }

.coming-soon-notice { max-width: 1400px; margin: 2rem auto 0; padding: 1rem; background: #1e3a5f; border-radius: 0.5rem; text-align: center; color: #60a5fa; }

@media (max-width: 1200px) { .content { grid-template-columns: 1fr; } }
</style>
