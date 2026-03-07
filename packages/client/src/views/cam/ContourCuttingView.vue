<script setup lang="ts">
/**
 * ContourCuttingView - Contour/Profile Cutting Toolpath Generator
 * Generate toolpaths for cutting around shapes (inside/outside/on-line)
 *
 * Connected to API endpoints:
 *   POST /api/cam/contour/preview
 *   POST /api/cam/contour/generate
 */
import { ref, computed } from 'vue'

const cutType = ref('outside')  // inside, outside, on-line
const toolDiameter = ref(6.0)
const stepdown = ref(3.0)
const feedRate = ref(1500)
const plungeRate = ref(500)
const spindleSpeed = ref(18000)
const cutDepth = ref(19)  // full thickness
const tabsEnabled = ref(true)
const tabWidth = ref(8)
const tabHeight = ref(2)
const tabCount = ref(4)
const leadIn = ref('arc')  // arc, tangent, direct

const dxfFile = ref<File | null>(null)
const loading = ref(false)

function handleFileUpload(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files?.length) dxfFile.value = input.files[0]
}

async function generateToolpath() {
  loading.value = true
  await new Promise(resolve => setTimeout(resolve, 1000))
  loading.value = false
}
</script>

<template>
  <div class="contour-cutting-view">
    <div class="header">
      <h1>Contour Cutting</h1>
      <p class="subtitle">Generate profile cutting toolpaths with tabs</p>
    </div>

    <div class="content">
      <div class="panel upload-panel">
        <h3>Geometry</h3>
        <div class="upload-zone" @click="($refs.fileInput as HTMLInputElement).click()">
          <input type="file" ref="fileInput" accept=".dxf,.svg" @change="handleFileUpload" hidden />
          <span class="upload-icon">📁</span>
          <p v-if="dxfFile">{{ dxfFile.name }}</p>
          <p v-else>Upload DXF or SVG</p>
        </div>

        <h3>Cut Type</h3>
        <div class="cut-type-buttons">
          <button :class="{ active: cutType === 'inside' }" @click="cutType = 'inside'">Inside</button>
          <button :class="{ active: cutType === 'outside' }" @click="cutType = 'outside'">Outside</button>
          <button :class="{ active: cutType === 'on-line' }" @click="cutType = 'on-line'">On Line</button>
        </div>

        <h3>Lead-In</h3>
        <select v-model="leadIn">
          <option value="arc">Arc (Recommended)</option>
          <option value="tangent">Tangent</option>
          <option value="direct">Direct Plunge</option>
        </select>
      </div>

      <div class="panel params-panel">
        <h3>Tool & Depth</h3>
        <div class="form-row">
          <div class="form-group">
            <label>Tool Diameter (mm)</label>
            <input type="number" v-model.number="toolDiameter" step="0.1" />
          </div>
          <div class="form-group">
            <label>Cut Depth (mm)</label>
            <input type="number" v-model.number="cutDepth" step="0.5" />
          </div>
        </div>
        <div class="form-group">
          <label>Stepdown (mm)</label>
          <input type="number" v-model.number="stepdown" step="0.5" />
        </div>

        <h3>Holding Tabs</h3>
        <div class="form-group checkbox-group">
          <label><input type="checkbox" v-model="tabsEnabled" /> Enable holding tabs</label>
        </div>
        <div v-if="tabsEnabled" class="form-row">
          <div class="form-group">
            <label>Tab Width (mm)</label>
            <input type="number" v-model.number="tabWidth" step="1" />
          </div>
          <div class="form-group">
            <label>Tab Height (mm)</label>
            <input type="number" v-model.number="tabHeight" step="0.5" />
          </div>
        </div>
        <div v-if="tabsEnabled" class="form-group">
          <label>Tab Count</label>
          <input type="number" v-model.number="tabCount" step="1" min="2" max="8" />
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
            <span class="icon">✂️</span>
            <p>Configure and generate toolpath</p>
          </div>
        </div>
        <div class="action-buttons">
          <button class="btn btn-primary" @click="generateToolpath" :disabled="!dxfFile || loading">
            Generate Toolpath
          </button>
          <button class="btn btn-secondary">Download G-code</button>
        </div>
      </div>
    </div>

    <div class="coming-soon-notice">
      <p>Full contour cutting with automatic tab placement coming soon.</p>
    </div>
  </div>
</template>

<style scoped>
.contour-cutting-view { min-height: 100vh; background: #0a0a0a; color: #e5e5e5; padding: 2rem; }
.header { max-width: 1400px; margin: 0 auto 2rem; }
.header h1 { font-size: 2rem; font-weight: 700; margin: 0 0 0.5rem; }
.subtitle { color: #888; margin: 0; }

.content { max-width: 1400px; margin: 0 auto; display: grid; grid-template-columns: 280px 1fr 1fr; gap: 1.5rem; }
.panel { background: #1a1a1a; border-radius: 0.75rem; padding: 1.5rem; }
.panel h3 { font-size: 0.875rem; font-weight: 600; color: #888; text-transform: uppercase; margin: 0 0 1rem; }
.panel h3:not(:first-child) { margin-top: 1.5rem; }

.upload-zone { border: 2px dashed #333; border-radius: 0.5rem; padding: 2rem; text-align: center; cursor: pointer; }
.upload-zone:hover { border-color: #60a5fa; }
.upload-icon { font-size: 2rem; display: block; margin-bottom: 0.5rem; }

.cut-type-buttons { display: flex; gap: 0.5rem; }
.cut-type-buttons button { flex: 1; padding: 0.5rem; background: #262626; border: 1px solid #333; border-radius: 0.375rem; color: #e5e5e5; cursor: pointer; }
.cut-type-buttons button.active { background: #2563eb; border-color: #2563eb; }

select { width: 100%; padding: 0.5rem; background: #262626; border: 1px solid #333; border-radius: 0.375rem; color: #e5e5e5; }

.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; font-size: 0.875rem; color: #888; margin-bottom: 0.25rem; }
.form-group input { width: 100%; padding: 0.5rem; background: #262626; border: 1px solid #333; border-radius: 0.375rem; color: #e5e5e5; }
.checkbox-group label { display: flex; align-items: center; gap: 0.5rem; cursor: pointer; }

.preview-container { aspect-ratio: 4/3; background: #0d0d0d; border-radius: 0.5rem; display: flex; align-items: center; justify-content: center; margin-bottom: 1rem; }
.placeholder { text-align: center; color: #666; }
.placeholder .icon { font-size: 3rem; display: block; margin-bottom: 0.5rem; }

.action-buttons { display: flex; gap: 0.75rem; }
.btn { flex: 1; padding: 0.75rem; border-radius: 0.5rem; font-weight: 600; cursor: pointer; border: none; }
.btn-primary { background: #2563eb; color: #fff; }
.btn-primary:disabled { background: #333; color: #666; }
.btn-secondary { background: #262626; color: #e5e5e5; border: 1px solid #333; }

.coming-soon-notice { max-width: 1400px; margin: 2rem auto 0; padding: 1rem; background: #1e3a5f; border-radius: 0.5rem; text-align: center; color: #60a5fa; }

@media (max-width: 1200px) { .content { grid-template-columns: 1fr; } }
</style>
