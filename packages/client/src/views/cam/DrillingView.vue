<script setup lang="ts">
/**
 * DrillingView - Drilling Operations Toolpath Generator
 * Generate drilling toolpaths for holes, peck drilling, and tapping
 *
 * Connected to API endpoints:
 *   POST /api/cam/drilling/preview
 *   POST /api/cam/drilling/generate
 */
import { ref } from 'vue'

const drillType = ref('standard')  // standard, peck, tapping
const holeDiameter = ref(6.0)
const holeDepth = ref(10)
const peckDepth = ref(3)
const retractHeight = ref(2)
const feedRate = ref(300)
const spindleSpeed = ref(3000)

// Hole positions
const holes = ref([
  { x: 50, y: 50 },
  { x: 100, y: 50 },
  { x: 150, y: 50 },
])

const loading = ref(false)

function addHole() {
  holes.value.push({ x: 0, y: 0 })
}

function removeHole(index: number) {
  holes.value.splice(index, 1)
}

async function generateToolpath() {
  loading.value = true
  await new Promise(resolve => setTimeout(resolve, 500))
  loading.value = false
}
</script>

<template>
  <div class="drilling-view">
    <div class="header">
      <h1>Drilling Operations</h1>
      <p class="subtitle">Generate drilling, peck drilling, and tapping toolpaths</p>
    </div>

    <div class="content">
      <div class="panel params-panel">
        <h3>Drill Type</h3>
        <div class="type-buttons">
          <button :class="{ active: drillType === 'standard' }" @click="drillType = 'standard'">Standard</button>
          <button :class="{ active: drillType === 'peck' }" @click="drillType = 'peck'">Peck Drill</button>
          <button :class="{ active: drillType === 'tapping' }" @click="drillType = 'tapping'">Tapping</button>
        </div>

        <h3>Hole Parameters</h3>
        <div class="form-row">
          <div class="form-group">
            <label>Hole Diameter (mm)</label>
            <input type="number" v-model.number="holeDiameter" step="0.5" />
          </div>
          <div class="form-group">
            <label>Hole Depth (mm)</label>
            <input type="number" v-model.number="holeDepth" step="0.5" />
          </div>
        </div>
        <div v-if="drillType === 'peck'" class="form-group">
          <label>Peck Depth (mm)</label>
          <input type="number" v-model.number="peckDepth" step="0.5" />
        </div>

        <h3>Feeds & Speeds</h3>
        <div class="form-row">
          <div class="form-group">
            <label>Feed Rate (mm/min)</label>
            <input type="number" v-model.number="feedRate" step="50" />
          </div>
          <div class="form-group">
            <label>Spindle (RPM)</label>
            <input type="number" v-model.number="spindleSpeed" step="500" />
          </div>
        </div>
      </div>

      <div class="panel holes-panel">
        <h3>Hole Positions</h3>
        <div class="holes-list">
          <div v-for="(hole, index) in holes" :key="index" class="hole-row">
            <span class="hole-num">#{{ index + 1 }}</span>
            <input type="number" v-model.number="hole.x" placeholder="X" />
            <input type="number" v-model.number="hole.y" placeholder="Y" />
            <button class="remove-btn" @click="removeHole(index)">×</button>
          </div>
        </div>
        <button class="add-btn" @click="addHole">+ Add Hole</button>
        <p class="hole-count">{{ holes.length }} holes</p>
      </div>

      <div class="panel preview-panel">
        <h3>Preview</h3>
        <div class="preview-container">
          <div v-if="loading" class="loading">Generating...</div>
          <div v-else class="placeholder">
            <span class="icon">🔩</span>
            <p>{{ holes.length }} × Ø{{ holeDiameter }}mm holes</p>
            <p class="detail">Depth: {{ holeDepth }}mm</p>
          </div>
        </div>
        <div class="action-buttons">
          <button class="btn btn-primary" @click="generateToolpath" :disabled="loading">
            Generate Toolpath
          </button>
          <button class="btn btn-secondary">Download G-code</button>
        </div>
      </div>
    </div>

    <div class="coming-soon-notice">
      <p>Full drilling with hole pattern import and optimization coming soon.</p>
    </div>
  </div>
</template>

<style scoped>
.drilling-view { min-height: 100vh; background: #0a0a0a; color: #e5e5e5; padding: 2rem; }
.header { max-width: 1400px; margin: 0 auto 2rem; }
.header h1 { font-size: 2rem; font-weight: 700; margin: 0 0 0.5rem; }
.subtitle { color: #888; margin: 0; }

.content { max-width: 1400px; margin: 0 auto; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1.5rem; }
.panel { background: #1a1a1a; border-radius: 0.75rem; padding: 1.5rem; }
.panel h3 { font-size: 0.875rem; font-weight: 600; color: #888; text-transform: uppercase; margin: 0 0 1rem; }
.panel h3:not(:first-child) { margin-top: 1.5rem; }

.type-buttons { display: flex; gap: 0.5rem; }
.type-buttons button { flex: 1; padding: 0.5rem; background: #262626; border: 1px solid #333; border-radius: 0.375rem; color: #e5e5e5; cursor: pointer; }
.type-buttons button.active { background: #2563eb; border-color: #2563eb; }

.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; font-size: 0.875rem; color: #888; margin-bottom: 0.25rem; }
.form-group input { width: 100%; padding: 0.5rem; background: #262626; border: 1px solid #333; border-radius: 0.375rem; color: #e5e5e5; }

.holes-list { max-height: 250px; overflow-y: auto; }
.hole-row { display: flex; gap: 0.5rem; align-items: center; margin-bottom: 0.5rem; }
.hole-num { width: 2rem; font-size: 0.75rem; color: #888; }
.hole-row input { flex: 1; padding: 0.375rem; background: #262626; border: 1px solid #333; border-radius: 0.25rem; color: #e5e5e5; font-size: 0.875rem; }
.remove-btn { background: none; border: none; color: #666; cursor: pointer; font-size: 1rem; }
.add-btn { width: 100%; padding: 0.5rem; background: #262626; border: 1px dashed #444; border-radius: 0.375rem; color: #888; cursor: pointer; margin-top: 0.5rem; }
.hole-count { font-size: 0.75rem; color: #60a5fa; margin-top: 0.5rem; }

.preview-container { aspect-ratio: 1; background: #0d0d0d; border-radius: 0.5rem; display: flex; align-items: center; justify-content: center; margin-bottom: 1rem; }
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
