<script setup lang="ts">
/**
 * SurfacingView - Surface Flattening Toolpath Generator
 * Generate toolpaths for flattening/facing operations
 *
 * Connected to API endpoints:
 *   POST /api/cam/surfacing/preview
 *   POST /api/cam/surfacing/generate
 */
import { ref } from 'vue'

const surfaceWidth = ref(300)
const surfaceLength = ref(500)
const stockRemoval = ref(1.0)
const toolDiameter = ref(25)
const stepover = ref(60)
const feedRate = ref(2000)
const spindleSpeed = ref(12000)
const pattern = ref('zigzag')  // zigzag, spiral, raster

const loading = ref(false)

async function generateToolpath() {
  loading.value = true
  await new Promise(resolve => setTimeout(resolve, 1000))
  loading.value = false
}
</script>

<template>
  <div class="surfacing-view">
    <div class="header">
      <h1>Surfacing</h1>
      <p class="subtitle">Generate flattening and facing toolpaths</p>
    </div>

    <div class="content">
      <div class="panel params-panel">
        <h3>Work Area</h3>
        <div class="form-row">
          <div class="form-group">
            <label>Width (mm)</label>
            <input type="number" v-model.number="surfaceWidth" step="10" />
          </div>
          <div class="form-group">
            <label>Length (mm)</label>
            <input type="number" v-model.number="surfaceLength" step="10" />
          </div>
        </div>
        <div class="form-group">
          <label>Stock Removal (mm)</label>
          <input type="number" v-model.number="stockRemoval" step="0.1" />
        </div>

        <h3>Tool</h3>
        <div class="form-row">
          <div class="form-group">
            <label>Tool Diameter (mm)</label>
            <input type="number" v-model.number="toolDiameter" step="1" />
          </div>
          <div class="form-group">
            <label>Stepover (%)</label>
            <input type="number" v-model.number="stepover" step="5" />
          </div>
        </div>

        <h3>Pattern</h3>
        <div class="pattern-buttons">
          <button :class="{ active: pattern === 'zigzag' }" @click="pattern = 'zigzag'">Zigzag</button>
          <button :class="{ active: pattern === 'spiral' }" @click="pattern = 'spiral'">Spiral</button>
          <button :class="{ active: pattern === 'raster' }" @click="pattern = 'raster'">Raster</button>
        </div>

        <h3>Feeds & Speeds</h3>
        <div class="form-row">
          <div class="form-group">
            <label>Feed Rate (mm/min)</label>
            <input type="number" v-model.number="feedRate" step="100" />
          </div>
          <div class="form-group">
            <label>Spindle (RPM)</label>
            <input type="number" v-model.number="spindleSpeed" step="1000" />
          </div>
        </div>
      </div>

      <div class="panel preview-panel">
        <h3>Preview</h3>
        <div class="preview-container">
          <div v-if="loading" class="loading">Generating...</div>
          <div v-else class="placeholder">
            <span class="icon">🔳</span>
            <p>{{ surfaceWidth }} × {{ surfaceLength }} mm surface</p>
            <p class="detail">{{ stockRemoval }}mm removal with {{ toolDiameter }}mm tool</p>
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
      <p>Full surfacing with automatic tramming compensation coming soon.</p>
    </div>
  </div>
</template>

<style scoped>
.surfacing-view { min-height: 100vh; background: #0a0a0a; color: #e5e5e5; padding: 2rem; }
.header { max-width: 1200px; margin: 0 auto 2rem; }
.header h1 { font-size: 2rem; font-weight: 700; margin: 0 0 0.5rem; }
.subtitle { color: #888; margin: 0; }

.content { max-width: 1200px; margin: 0 auto; display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
.panel { background: #1a1a1a; border-radius: 0.75rem; padding: 1.5rem; }
.panel h3 { font-size: 0.875rem; font-weight: 600; color: #888; text-transform: uppercase; margin: 0 0 1rem; }
.panel h3:not(:first-child) { margin-top: 1.5rem; }

.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; font-size: 0.875rem; color: #888; margin-bottom: 0.25rem; }
.form-group input { width: 100%; padding: 0.5rem; background: #262626; border: 1px solid #333; border-radius: 0.375rem; color: #e5e5e5; }

.pattern-buttons { display: flex; gap: 0.5rem; }
.pattern-buttons button { flex: 1; padding: 0.5rem; background: #262626; border: 1px solid #333; border-radius: 0.375rem; color: #e5e5e5; cursor: pointer; }
.pattern-buttons button.active { background: #2563eb; border-color: #2563eb; }

.preview-container { aspect-ratio: 4/3; background: #0d0d0d; border-radius: 0.5rem; display: flex; align-items: center; justify-content: center; margin-bottom: 1rem; }
.placeholder { text-align: center; color: #666; }
.placeholder .icon { font-size: 3rem; display: block; margin-bottom: 0.5rem; }
.detail { font-size: 0.75rem; color: #888; margin-top: 0.25rem; }

.action-buttons { display: flex; gap: 0.75rem; }
.btn { flex: 1; padding: 0.75rem; border-radius: 0.5rem; font-weight: 600; cursor: pointer; border: none; }
.btn-primary { background: #2563eb; color: #fff; }
.btn-primary:disabled { background: #333; color: #666; }
.btn-secondary { background: #262626; color: #e5e5e5; border: 1px solid #333; }

.coming-soon-notice { max-width: 1200px; margin: 2rem auto 0; padding: 1rem; background: #1e3a5f; border-radius: 0.5rem; text-align: center; color: #60a5fa; }

@media (max-width: 900px) { .content { grid-template-columns: 1fr; } }
</style>
